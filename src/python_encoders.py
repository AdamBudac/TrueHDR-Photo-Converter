"""Native Python image encoders backed by ``imagecodecs``, ``pillow-heif``, and ``Pillow``.

Eliminates external CLI binary dependencies (``cjpeg``, ``cjxl``, ``heif-enc``,
``avifenc``, ``ffmpeg``, ``ultrahdr_app``) by encoding directly from in-memory
NumPy arrays loaded once per image.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Tuple

from src.exr_encoder import SDR_WHITE_NITS, _get_pq_eotf_lut


def _num_threads() -> int:
    """Return all available logical CPU cores for multi-threaded native codecs."""
    return max(1, os.cpu_count() or 1)


# ---------------------------------------------------------------------------
# Runtime availability checks
# ---------------------------------------------------------------------------

def is_imagecodecs_available() -> bool:
    """Return ``True`` when ``imagecodecs``, ``numpy``, and ``PIL`` are importable."""
    try:
        import imagecodecs  # noqa: F401
        import numpy  # noqa: F401
        from PIL import Image  # noqa: F401

        return bool(
            getattr(imagecodecs.PNG, "available", False)
            and getattr(imagecodecs.JPEG8, "available", False)
            and getattr(imagecodecs.AVIF, "available", False)
            and getattr(imagecodecs.ULTRAHDR, "available", False)
        )
    except ImportError:
        return False


def is_pillow_heif_available() -> bool:
    """Return ``True`` when ``pillow_heif``, ``imagecodecs``, ``numpy``, and ``PIL`` are importable."""
    try:
        import imagecodecs  # noqa: F401
        import numpy  # noqa: F401
        import pillow_heif  # noqa: F401
        from PIL import Image  # noqa: F401

        return bool(getattr(imagecodecs.PNG, "available", False))
    except ImportError:
        return False


# ---------------------------------------------------------------------------
# PNG loaders (read pixel data + embedded ICC profile once per image)
# ---------------------------------------------------------------------------

def _read_icc_profile(png_file: Path) -> Optional[bytes]:
    """Extract raw ICC profile bytes from *png_file* if present."""
    from PIL import Image

    with Image.open(png_file) as img:
        icc = img.info.get("icc_profile")
        return bytes(icc) if icc else None


def _decode_png_rgb(png_file: Path):
    """Decode PNG into an RGB numpy array (uint8 or uint16) via ``imagecodecs.png_decode``."""
    import imagecodecs
    import numpy as np

    raw = imagecodecs.png_decode(png_file.read_bytes())
    if raw is None:
        raise ValueError(f"Failed to decode PNG image: {png_file}")

    if raw.ndim == 2:
        return np.stack([raw, raw, raw], axis=-1)
    if raw.shape[2] >= 3:
        return raw[:, :, :3]
    raise ValueError(f"Unsupported channel count in PNG: {raw.shape}")


def load_sdr_png(png_file: Path) -> Tuple[object, Optional[bytes]]:
    """Load an SDR PNG as contiguous 8-bit RGB ``(H, W, 3)`` and optional ICC bytes."""
    import numpy as np

    rgb = _decode_png_rgb(png_file)

    if rgb.dtype == np.uint16:
        rgb = ((rgb.astype(np.uint32) * 255 + 32767) // 65535).astype(np.uint8)
    elif rgb.dtype != np.uint8:
        rgb = np.clip(rgb, 0, 255).astype(np.uint8)

    icc = _read_icc_profile(png_file)
    return np.ascontiguousarray(rgb, dtype=np.uint8), icc


def load_hdr_png(png_file: Path) -> Tuple[object, Optional[bytes]]:
    """Load an HDR PNG as contiguous 16-bit RGB ``(H, W, 3)`` and optional ICC bytes."""
    import numpy as np

    rgb = _decode_png_rgb(png_file)

    if rgb.dtype == np.uint8:
        rgb = (rgb.astype(np.uint16) * 257)
    elif rgb.dtype != np.uint16:
        rgb = np.clip(rgb, 0, 65535).astype(np.uint16)

    icc = _read_icc_profile(png_file)
    return np.ascontiguousarray(rgb, dtype=np.uint16), icc


# ---------------------------------------------------------------------------
# SDR encoders (8-bit sRGB / BT.709)
# ---------------------------------------------------------------------------

def encode_sdr_jpeg(
    rgb8,
    icc_profile: Optional[bytes],
    output_path: Path,
    quality: int,
) -> Path:
    """Encode 8-bit RGB to 4:2:0 JPEG via ``imagecodecs.jpeg8_encode`` (libjpeg-turbo)."""
    import imagecodecs

    data = imagecodecs.jpeg8_encode(
        rgb8,
        level=int(quality),
        subsampling="420",
        optimize=True,
        iccprofile=icc_profile,
    )
    output_path.write_bytes(data)
    return output_path


def encode_sdr_jxl(
    rgb8,
    output_path: Path,
    quality: int,
) -> Path:
    """Encode 8-bit RGB to JPEG XL via ``imagecodecs.jpegxl_encode`` (libjxl 0.13)."""
    import imagecodecs

    lossless = int(quality) >= 100
    data = imagecodecs.jpegxl_encode(
        rgb8,
        level=int(quality),
        lossless=lossless,
        effort=7,
        primaries=imagecodecs.JPEGXL.PRIMARIES.SRGB,
        transfer=imagecodecs.JPEGXL.TRANSFER_FUNCTION.SRGB,
        whitepoint=imagecodecs.JPEGXL.WHITE_POINT.D65,
        numthreads=_num_threads(),
    )
    output_path.write_bytes(data)
    return output_path


def encode_sdr_heic(
    rgb8,
    icc_profile: Optional[bytes],
    output_path: Path,
    quality: int,
) -> Path:
    """Encode 8-bit RGB to 4:2:0 sRGB HEIC via ``pillow-heif`` (libheif + x265)."""
    import pillow_heif

    h, w = rgb8.shape[:2]
    heif_img = pillow_heif.from_bytes("RGB", (w, h), rgb8.tobytes())
    save_kwargs = {
        "quality": int(quality),
        "chroma": 420,
        "matrix_coefficients": 1,
        "color_primaries": 1,
        "transfer_characteristics": 13,
        "full_range_flag": 1,
        "enc_params": {"preset": "slow", "tune": "ssim", "complexity": "80"},
    }
    if icc_profile:
        save_kwargs["icc_profile"] = icc_profile
    heif_img.save(str(output_path), **save_kwargs)
    return output_path


def encode_sdr_avif(
    rgb8,
    icc_profile: Optional[bytes],
    output_path: Path,
    quality: int,
) -> Path:
    """Encode 8-bit RGB to 4:2:0 BT.709/sRGB AVIF via ``imagecodecs.avif_encode`` (libavif)."""
    import imagecodecs

    data = imagecodecs.avif_encode(
        rgb8,
        level=int(quality),
        speed=6,
        tilelog2=(2, 2),
        bitspersample=8,
        pixelformat=imagecodecs.AVIF.PIXEL_FORMAT.YUV420,
        codec=imagecodecs.AVIF.CODEC_CHOICE.AOM,
        primaries=imagecodecs.AVIF.COLOR_PRIMARIES.BT709,
        transfer=imagecodecs.AVIF.TRANSFER_CHARACTERISTICS.SRGB,
        matrix=imagecodecs.AVIF.MATRIX_COEFFICIENTS.BT709,
        iccprofile=icc_profile,
        numthreads=_num_threads(),
    )
    output_path.write_bytes(data)
    return output_path


# ---------------------------------------------------------------------------
# HDR/PQ encoders (16-bit Rec.2020 SMPTE ST 2084 PQ input)
# ---------------------------------------------------------------------------

def encode_hdr_pq_jxl(
    rgb16,
    output_path: Path,
    quality: int,
) -> Path:
    """Encode 16-bit Rec.2020 PQ RGB to HDR JPEG XL via ``imagecodecs.jpegxl_encode``."""
    import imagecodecs

    lossless = int(quality) >= 100
    data = imagecodecs.jpegxl_encode(
        rgb16,
        level=int(quality),
        lossless=lossless,
        effort=7,
        bitspersample=16,
        primaries=imagecodecs.JPEGXL.PRIMARIES.BT2100,
        transfer=imagecodecs.JPEGXL.TRANSFER_FUNCTION.PQ,
        whitepoint=imagecodecs.JPEGXL.WHITE_POINT.D65,
        numthreads=_num_threads(),
    )
    output_path.write_bytes(data)
    return output_path


def encode_hdr_pq_heic(
    rgb16,
    icc_profile: Optional[bytes],
    output_path: Path,
    quality: int,
) -> Path:
    """Encode 16-bit Rec.2020 PQ RGB to 10-bit 4:2:0 HDR HEIC via ``pillow-heif``."""
    import pillow_heif

    pillow_heif.options.SAVE_HDR_TO_12_BIT = False
    h, w = rgb16.shape[:2]
    heif_img = pillow_heif.from_bytes("RGB;16", (w, h), rgb16.tobytes())
    save_kwargs = {
        "quality": int(quality),
        "chroma": 420,
        "matrix_coefficients": 9,
        "color_primaries": 9,
        "transfer_characteristics": 16,
        "full_range_flag": 1,
        "enc_params": {"preset": "slow", "tune": "ssim", "complexity": "80"},
    }
    if icc_profile:
        save_kwargs["icc_profile"] = icc_profile
    heif_img.save(str(output_path), **save_kwargs)
    return output_path


def encode_hdr_pq_avif(
    rgb16,
    icc_profile: Optional[bytes],
    output_path: Path,
    quality: int,
) -> Path:
    """Encode 16-bit Rec.2020 PQ RGB to 10-bit 4:2:0 HDR AVIF via ``imagecodecs.avif_encode``."""
    import imagecodecs
    import numpy as np

    rgb10 = np.ascontiguousarray(
        ((rgb16.astype(np.uint32) * 1023 + 32767) // 65535).astype(np.uint16)
    )
    data = imagecodecs.avif_encode(
        rgb10,
        level=int(quality),
        speed=6,
        tilelog2=(2, 2),
        bitspersample=10,
        pixelformat=imagecodecs.AVIF.PIXEL_FORMAT.YUV420,
        codec=imagecodecs.AVIF.CODEC_CHOICE.AOM,
        primaries=imagecodecs.AVIF.COLOR_PRIMARIES.BT2020,
        transfer=imagecodecs.AVIF.TRANSFER_CHARACTERISTICS.PQ,
        matrix=imagecodecs.AVIF.MATRIX_COEFFICIENTS.BT2020_NCL,
        iccprofile=icc_profile,
        numthreads=_num_threads(),
    )
    output_path.write_bytes(data)
    return output_path


# ---------------------------------------------------------------------------
# HDR/GainMap JPEG encoder (ISO 21496-1 Ultra HDR via libultrahdr 2.0.2)
# ---------------------------------------------------------------------------

def encode_hdr_gm_jpeg(
    rgb16,
    sdr_rgb8,
    output_path: Path,
    quality: int,
    sdr_icc: Optional[bytes] = None,
) -> Path:
    """Encode Rec.2020 PQ HDR RGB (+ optional paired 8-bit SDR RGB) to 4:2:0 Ultra HDR JPEG.

    Converts 16-bit PQ to linear 16-bit half-float RGBA normalized so ``1.0 == 203 nits``
    (ITU-R BT.2408 diffuse SDR white, matching ``libultrahdr`` ``UHDR_CT_LINEAR``).
    Pre-encodes the SDR base as an optimized 4:2:0 JPEG (preserving *sdr_icc*), computes
    the gain map against the decoded 4:2:0 SDR pixels (Scenario 3 equivalent), and packs
    both streams via ``ultrahdr_encode_jpeg`` so the primary image stays 4:2:0.
    """
    import imagecodecs
    import numpy as np

    h, w = rgb16.shape[:2]
    q = int(quality)
    lut = _get_pq_eotf_lut(SDR_WHITE_NITS)
    hdr_rgba16f = np.ones((h, w, 4), dtype=np.float16)
    hdr_rgba16f[..., :3] = lut[rgb16]

    if sdr_rgb8 is not None and sdr_rgb8.shape[:2] == (h, w):
        base_420 = imagecodecs.jpeg8_encode(
            sdr_rgb8,
            level=q,
            subsampling="420",
            optimize=True,
            iccprofile=sdr_icc,
        )
        sdr_decoded = imagecodecs.jpeg8_decode(base_420)
        sdr_rgba8 = np.full((h, w, 4), 255, dtype=np.uint8)
        sdr_rgba8[..., :3] = sdr_decoded
        raw_uhdr = imagecodecs.ultrahdr_encode(
            hdr_rgba16f,
            level=q,
            sdr=sdr_rgba8,
            gamut=imagecodecs.ULTRAHDR.CG.BT_2100,
            transfer=imagecodecs.ULTRAHDR.CT.LINEAR,
            crange=imagecodecs.ULTRAHDR.CR.FULL_RANGE,
            usage=imagecodecs.ULTRAHDR.USAGE.QUALITY,
            gainmap_level=q,
            multichannel=True,
            scale=1,
        )
        _, gm_jpg, meta = imagecodecs.ultrahdr_decode_jpeg(raw_uhdr)
        data = imagecodecs.ultrahdr_encode_jpeg(
            base_420,
            gm_jpg,
            gamut=imagecodecs.ULTRAHDR.CG.BT_2100,
            gainmap_gamma=meta["gainmap_gamma"],
            boostmin=meta["boostmin"],
            boostmax=meta["boostmax"],
            offset_sdr=meta["offset_sdr"],
            offset_hdr=meta["offset_hdr"],
            hdr_capacity_min=meta["hdr_capacity_min"],
            hdr_capacity_max=meta["hdr_capacity_max"],
            use_base_cg=meta["use_base_cg"],
        )
    else:
        raw_uhdr = imagecodecs.ultrahdr_encode(
            hdr_rgba16f,
            level=q,
            gamut=imagecodecs.ULTRAHDR.CG.BT_2100,
            transfer=imagecodecs.ULTRAHDR.CT.LINEAR,
            crange=imagecodecs.ULTRAHDR.CR.FULL_RANGE,
            usage=imagecodecs.ULTRAHDR.USAGE.QUALITY,
            gainmap_level=q,
            multichannel=True,
            scale=1,
        )
        base_raw, gm_jpg, meta = imagecodecs.ultrahdr_decode_jpeg(raw_uhdr)
        base_rgb = imagecodecs.jpeg8_decode(base_raw)
        base_420 = imagecodecs.jpeg8_encode(
            base_rgb,
            level=q,
            subsampling="420",
            optimize=True,
        )
        data = imagecodecs.ultrahdr_encode_jpeg(
            base_420,
            gm_jpg,
            gamut=imagecodecs.ULTRAHDR.CG.BT_2100,
            gainmap_gamma=meta["gainmap_gamma"],
            boostmin=meta["boostmin"],
            boostmax=meta["boostmax"],
            offset_sdr=meta["offset_sdr"],
            offset_hdr=meta["offset_hdr"],
            hdr_capacity_min=meta["hdr_capacity_min"],
            hdr_capacity_max=meta["hdr_capacity_max"],
            use_base_cg=meta["use_base_cg"],
        )

    output_path.write_bytes(data)
    return output_path
