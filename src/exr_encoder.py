"""Native Python OpenEXR encoder for 16-bit Rec.2020 PQ HDR PNG images.

Converts SMPTE ST 2084 (PQ) 16-bit PNGs into linear 16-bit half-float OpenEXR
files with full Rec.2020 ``chromaticities``, ITU-R BT.2408 ``whiteLuminance``
(203 cd/m^2), and all 14 official OpenEXR 3.5 compression methods without any
external CLI dependency.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple

from src.models import EXR_COMPRESSIONS

# CIE 1931 xy chromaticities for ITU-R BT.709 / sRGB and ITU-R BT.2020 (Rec.2020)
REC709_CHROMATICITIES: Tuple[float, ...] = (
    0.640,
    0.330,
    0.300,
    0.600,
    0.150,
    0.060,
    0.3127,
    0.3290,
)
REC2020_CHROMATICITIES: Tuple[float, ...] = (
    0.708,
    0.292,
    0.170,
    0.797,
    0.131,
    0.046,
    0.3127,
    0.3290,
)

# ITU-R BT.2408 / Lightroom / ISO 21496-1 diffuse SDR reference white (cd/m^2)
SDR_WHITE_NITS: float = 203.0
SDR_SRGB_WHITE_NITS: float = 80.0
DEFAULT_DWA_COMPRESSION_LEVEL: float = 45.0

_PQ_LUT_CACHE: Dict[float, object] = {}
_SRGB_U8_LUT = None
_SRGB_U16_LUT = None


def is_openexr_available() -> bool:
    """Return ``True`` when ``OpenEXR``, ``numpy``, and ``imagecodecs`` can be imported."""
    try:
        import OpenEXR  # noqa: F401
        import imagecodecs  # noqa: F401
        import numpy  # noqa: F401
        return bool(getattr(imagecodecs.PNG, "available", False))
    except ImportError:
        return False


def _compression_constant(compression: str):
    """Map a normalized compression name (e.g. ``'piz'``, ``'dwab'``) to an OpenEXR constant."""
    import OpenEXR

    key = compression.strip().lower()
    mapping = {
        "none": OpenEXR.NO_COMPRESSION,
        "rle": OpenEXR.RLE_COMPRESSION,
        "zips": OpenEXR.ZIPS_COMPRESSION,
        "zip": OpenEXR.ZIP_COMPRESSION,
        "piz": OpenEXR.PIZ_COMPRESSION,
        "pxr24": OpenEXR.PXR24_COMPRESSION,
        "b44": OpenEXR.B44_COMPRESSION,
        "b44a": OpenEXR.B44A_COMPRESSION,
        "dwaa": OpenEXR.DWAA_COMPRESSION,
        "dwab": OpenEXR.DWAB_COMPRESSION,
        "htj2k256": OpenEXR.HTJ2K256_COMPRESSION,
        "htj2k32": OpenEXR.HTJ2K32_COMPRESSION,
        "lj2k": OpenEXR.LJ2K_COMPRESSION,
        "zstd": OpenEXR.ZSTD_COMPRESSION,
    }
    if key not in mapping:
        raise ValueError(
            f"Unsupported EXR compression '{compression}'. "
            f"Valid options: {', '.join(EXR_COMPRESSIONS)}"
        )
    return mapping[key]


def _get_pq_eotf_lut(white_nits: float):
    """Build and cache a 65536-entry float16 LUT mapping uint16 PQ -> linear EXR."""
    cached = _PQ_LUT_CACHE.get(white_nits)
    if cached is not None:
        return cached

    import numpy as np

    v = np.arange(65536, dtype=np.float64) / 65535.0
    m1 = 2610.0 / 16384.0
    m2 = 2523.0 / 32.0
    c1 = 3424.0 / 4096.0
    c2 = 2413.0 / 128.0
    c3 = 2392.0 / 128.0

    vp = np.power(v, 1.0 / m2)
    linear_01 = np.power(np.maximum(vp - c1, 0.0) / (c2 - c3 * vp), 1.0 / m1)
    linear_scaled = (linear_01 * (10000.0 / white_nits)).astype(np.float16)
    _PQ_LUT_CACHE[white_nits] = linear_scaled
    return linear_scaled


def _get_srgb_eotf_lut(bits: int):
    """Build and cache an IEC 61966-2-1 sRGB EOTF LUT (8-bit or 16-bit -> float16 linear)."""
    global _SRGB_U8_LUT, _SRGB_U16_LUT
    if bits == 8 and _SRGB_U8_LUT is not None:
        return _SRGB_U8_LUT
    if bits == 16 and _SRGB_U16_LUT is not None:
        return _SRGB_U16_LUT

    import numpy as np

    max_val = 255.0 if bits == 8 else 65535.0
    v = np.arange(int(max_val) + 1, dtype=np.float64) / max_val
    linear = np.where(
        v <= 0.04045,
        v / 12.92,
        np.power((v + 0.055) / 1.055, 2.4),
    ).astype(np.float16)

    if bits == 8:
        _SRGB_U8_LUT = linear
    else:
        _SRGB_U16_LUT = linear
    return linear


def _read_png_rgb(png_file: Path):
    """Decode PNG into an RGB numpy array (uint8 or uint16) via ``imagecodecs.png_decode``."""
    import imagecodecs
    import numpy as np

    img = imagecodecs.png_decode(png_file.read_bytes())
    if img is None:
        raise ValueError(f"Failed to decode PNG image: {png_file}")

    if img.ndim == 2:
        return np.stack([img, img, img], axis=-1)
    if img.shape[2] >= 3:
        return img[:, :, :3]
    raise ValueError(f"Unsupported channel count {img.shape} in {png_file}")


def encode_sdr_png_to_exr(
    png_file: Path,
    output_path: Path,
    *,
    compression: str = "lj2k",
    dwa_compression_level: float = DEFAULT_DWA_COMPRESSION_LEVEL,
    chromaticities: Tuple[float, ...] = REC709_CHROMATICITIES,
    white_nits: float = SDR_SRGB_WHITE_NITS,
) -> None:
    """Convert an SDR sRGB PNG directly into a linear 16-bit half-float Rec.709 EXR."""
    import OpenEXR
    import numpy as np

    rgb = _read_png_rgb(png_file)
    if rgb.dtype == np.uint8:
        lut = _get_srgb_eotf_lut(8)
    elif rgb.dtype == np.uint16:
        lut = _get_srgb_eotf_lut(16)
    else:
        raise ValueError(f"Unsupported PNG pixel dtype {rgb.dtype} in {png_file}")

    rgb_half = np.ascontiguousarray(lut[rgb], dtype=np.float16)

    comp_key = compression.strip().lower()
    header = {
        "compression": _compression_constant(comp_key),
        "type": OpenEXR.scanlineimage,
        "chromaticities": tuple(float(x) for x in chromaticities),
        "whiteLuminance": float(white_nits),
    }
    if comp_key in {"dwaa", "dwab"}:
        header["dwaCompressionLevel"] = float(dwa_compression_level)

    with OpenEXR.File(header, {"RGB": rgb_half}) as exr_file:
        exr_file.write(str(output_path))


def encode_hdr_rgb16_to_exr(
    rgb_u16,
    output_path: Path,
    *,
    compression: str = "lj2k",
    dwa_compression_level: float = DEFAULT_DWA_COMPRESSION_LEVEL,
    chromaticities: Tuple[float, ...] = REC2020_CHROMATICITIES,
    white_nits: float = SDR_WHITE_NITS,
) -> None:
    """Convert an in-memory 16-bit Rec.2020 PQ RGB array to linear half-float EXR."""
    import OpenEXR
    import numpy as np

    lut = _get_pq_eotf_lut(white_nits)
    rgb_half = np.ascontiguousarray(lut[rgb_u16], dtype=np.float16)

    comp_key = compression.strip().lower()
    header = {
        "compression": _compression_constant(comp_key),
        "type": OpenEXR.scanlineimage,
        "chromaticities": tuple(float(x) for x in chromaticities),
        "whiteLuminance": float(white_nits),
    }
    if comp_key in {"dwaa", "dwab"}:
        header["dwaCompressionLevel"] = float(dwa_compression_level)

    with OpenEXR.File(header, {"RGB": rgb_half}) as exr_file:
        exr_file.write(str(output_path))


def encode_hdr_png_to_exr(
    png_file: Path,
    output_path: Path,
    *,
    compression: str = "lj2k",
    dwa_compression_level: float = DEFAULT_DWA_COMPRESSION_LEVEL,
    chromaticities: Tuple[float, ...] = REC2020_CHROMATICITIES,
    white_nits: float = SDR_WHITE_NITS,
) -> None:
    """Convert a 16-bit Rec.2020 PQ HDR PNG directly into a linear 16-bit half-float EXR."""
    import numpy as np

    rgb = _read_png_rgb(png_file)

    # Convert to uint16 PQ scale and map through cached SMPTE ST 2084 EOTF LUT
    if rgb.dtype == np.uint8:
        rgb_u16 = rgb.astype(np.uint16) * 257
    elif rgb.dtype == np.uint16:
        rgb_u16 = rgb
    else:
        raise ValueError(f"Unsupported PNG pixel dtype {rgb.dtype} in {png_file}")

    encode_hdr_rgb16_to_exr(
        rgb_u16,
        output_path,
        compression=compression,
        dwa_compression_level=dwa_compression_level,
        chromaticities=chromaticities,
        white_nits=white_nits,
    )


def recompress_exr(
    input_exr: Path,
    output_exr: Path,
    *,
    compression: str = "piz",
    dwa_compression_level: Optional[float] = None,
) -> None:
    """Decode an existing EXR file and write it back with a new compression method.

    Preserves pixel data, ``chromaticities``, and ``whiteLuminance`` metadata.
    """
    import OpenEXR
    import numpy as np

    with OpenEXR.File(str(input_exr)) as src:
        src_header = dict(src.header())
        chrom = src_header.get("chromaticities")
        white_lum = src_header.get("whiteLuminance")
        src_channels = src.channels()
        if "RGB" in src_channels:
            rgb_pixels = np.ascontiguousarray(src_channels["RGB"].pixels, dtype=np.float16)
        else:
            rgb_pixels = np.ascontiguousarray(
                np.stack(
                    [
                        src_channels["R"].pixels,
                        src_channels["G"].pixels,
                        src_channels["B"].pixels,
                    ],
                    axis=-1,
                ),
                dtype=np.float16,
            )

    comp_key = compression.strip().lower()
    dst_header = {
        "compression": _compression_constant(comp_key),
        "type": OpenEXR.scanlineimage,
    }
    if chrom is not None:
        dst_header["chromaticities"] = tuple(float(x) for x in chrom)
    if white_lum is not None:
        dst_header["whiteLuminance"] = float(white_lum)
    if comp_key in {"dwaa", "dwab"}:
        dst_header["dwaCompressionLevel"] = float(
            dwa_compression_level
            if dwa_compression_level is not None
            else DEFAULT_DWA_COMPRESSION_LEVEL
        )

    with OpenEXR.File(dst_header, {"RGB": rgb_pixels}) as dst:
        dst.write(str(output_exr))
