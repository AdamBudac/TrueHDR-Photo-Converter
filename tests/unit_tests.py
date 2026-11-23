import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.models import AppSettings, ImageType, compute_zero_fill  # noqa: E402
from src.config import settings_from_dict  # noqa: E402
from src.classifier import normalize_base, classify_files  # noqa: E402
from src.worker import copy_source_files  # noqa: E402


# ---------------------------------------------------------------------------
# Existing tests (updated imports)
# ---------------------------------------------------------------------------

def test_compute_zero_fill_raises_manual_to_auto():
    logger = logging.getLogger("test_zero_fill")
    logger.addHandler(logging.NullHandler())
    digits = compute_zero_fill(start=8, count=4, mode="manual", manual_digits=1, logger=logger)
    assert digits == 2


def test_settings_from_dict_clamps_quality():
    logger = logging.getLogger("test_settings")
    logger.addHandler(logging.NullHandler())
    settings = settings_from_dict({"codec_quality": {"jpeg": 150}, "start_counter": 0}, logger)
    assert settings.codec_quality["jpeg"] == 100
    assert settings.start_counter == 0


def test_copy_source_files(tmp_path: Path):
    (tmp_path / "image.png").write_bytes(b"fake")
    (tmp_path / "image_HDR.exr").write_bytes(b"fakeexr")
    (tmp_path / "image_HDR.jpg").write_bytes(b"fakejpg")
    (tmp_path / "ignore.txt").write_text("x")
    (tmp_path / "sdr_photo.jpg").write_bytes(b"sdrjpg")  # non-HDR JPEG – should be ignored
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    logger = logging.getLogger("test_copy")
    logger.addHandler(logging.NullHandler())

    png_files, exr_files, jpg_hdr_files = copy_source_files(tmp_path, output_dir, logger)

    assert len(png_files) == 1
    assert len(exr_files) == 1
    assert len(jpg_hdr_files) == 1
    assert (output_dir / "image.png").exists()
    assert (output_dir / "image_HDR.exr").exists()
    assert (output_dir / "image_HDR.jpg").exists()
    assert not (output_dir / "sdr_photo.jpg").exists()  # non-HDR JPEG not copied


# ---------------------------------------------------------------------------
# New tests – classifier (BW / HDR detection)
# ---------------------------------------------------------------------------

def test_normalize_base_sdr_color():
    base, img_type = normalize_base("photo")
    assert base == "photo"
    assert img_type == ImageType.SDR_COLOR


def test_normalize_base_sdr_bw_dash2_treated_as_color():
    # Suffix -2 is no longer treated as BW; regular numbered files stay color
    base, img_type = normalize_base("photo-2")
    assert base == "photo-2"
    assert img_type == ImageType.SDR_COLOR


def test_normalize_base_sdr_bw_suffix():
    base, img_type = normalize_base("photo_BW")
    assert base == "photo"
    assert img_type == ImageType.SDR_BW


def test_normalize_base_sdr_bw_suffix_lowercase():
    base, img_type = normalize_base("photo_bw")
    assert base == "photo"
    assert img_type == ImageType.SDR_BW


def test_normalize_base_hdr_color():
    base, img_type = normalize_base("photo_HDR")
    assert base == "photo"
    assert img_type == ImageType.HDR_COLOR


def test_normalize_base_hdr_color_lowercase():
    base, img_type = normalize_base("photo_hdr")
    assert base == "photo"
    assert img_type == ImageType.HDR_COLOR


def test_normalize_base_hdr_dash2_treated_as_color():
    # photo-2_HDR has HDR suffix stripped, leaving photo-2 as HDR color (not BW)
    base, img_type = normalize_base("photo-2_HDR")
    assert base == "photo-2"
    assert img_type == ImageType.HDR_COLOR


def test_normalize_base_hdr_bw_suffix():
    base, img_type = normalize_base("photo_BW_HDR")
    assert base == "photo"
    assert img_type == ImageType.HDR_BW


def test_normalize_base_hdr_bw_all_lowercase():
    base, img_type = normalize_base("photo_bw_hdr")
    assert base == "photo"
    assert img_type == ImageType.HDR_BW


def test_normalize_base_hdr_mixed_case():
    base, img_type = normalize_base("photo_Bw_Hdr")
    assert base == "photo"
    assert img_type == ImageType.HDR_BW


def test_classify_files_groups():
    """Verify that classify_files sorts files into the right groups."""
    files = [
        Path("photo.png"),
        Path("photo_BW.png"),
        Path("photo_HDR.png"),
        Path("photo_BW_HDR.png"),
        Path("photo_bw_hdr.png"),
    ]
    exr = [Path("photo_HDR.exr")]

    result = classify_files(files, exr)

    assert "photo" in result.sdr_color_groups
    assert "photo" in result.sdr_bw_groups
    assert "photo" in result.hdr_color_groups
    assert "photo" in result.hdr_bw_groups
    assert len(result.sdr_color_groups["photo"]) == 1
    assert len(result.sdr_bw_groups["photo"]) == 1   # _BW
    assert len(result.hdr_color_groups["photo"]) == 1  # _HDR
    assert len(result.hdr_bw_groups["photo"]) == 2   # _BW_HDR and _bw_hdr


# ---------------------------------------------------------------------------
# New tests – JPG HDR classification
# ---------------------------------------------------------------------------

def test_classify_files_jpg_hdr():
    """Verify that classify_files groups JPG HDR files by base name."""
    files = [Path("photo_HDR.png")]
    exr = [Path("photo_HDR.exr")]
    jpg_hdr = [Path("photo_HDR.jpg")]

    result = classify_files(files, exr, jpg_hdr)

    assert "photo" in result.jpg_hdr_groups
    assert len(result.jpg_hdr_groups["photo"]) == 1
    assert "photo" in result.exr_groups
    assert len(result.exr_groups["photo"]) == 1


def test_classify_files_jpg_hdr_bw():
    """JPG HDR files with _BW suffix are grouped under the correct base."""
    files = [Path("photo_BW_HDR.png")]
    jpg_hdr = [Path("photo_BW_HDR.jpg"), Path("photo_bw_hdr.jpeg"), Path("photo-2_HDR.jpeg")]

    result = classify_files(files, [], jpg_hdr)

    assert "photo" in result.jpg_hdr_groups
    assert len(result.jpg_hdr_groups["photo"]) == 2
    # photo-2 is a separate base now that -2 is not treated as BW
    assert "photo-2" in result.jpg_hdr_groups
    assert len(result.jpg_hdr_groups["photo-2"]) == 1


def test_classify_files_jpg_hdr_case_insensitive():
    """JPG HDR classification is case-insensitive for _HDR suffix."""
    files = [Path("photo_hdr.png")]
    jpg_hdr = [Path("photo_hdr.jpg")]

    result = classify_files(files, [], jpg_hdr)

    assert "photo" in result.jpg_hdr_groups
    assert len(result.jpg_hdr_groups["photo"]) == 1


def test_copy_source_files_ignores_non_hdr_jpeg(tmp_path: Path):
    """Non-HDR JPEG files are not copied to the output directory."""
    (tmp_path / "photo.png").write_bytes(b"fake")
    (tmp_path / "normal.jpg").write_bytes(b"notHDR")
    (tmp_path / "normal.jpeg").write_bytes(b"notHDR2")
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    logger = logging.getLogger("test_ignore_sdr_jpeg")
    logger.addHandler(logging.NullHandler())

    _, _, jpg_hdr_files = copy_source_files(tmp_path, output_dir, logger)

    assert len(jpg_hdr_files) == 0
    assert not (output_dir / "normal.jpg").exists()
    assert not (output_dir / "normal.jpeg").exists()


def test_copy_source_files_copies_hdr_jpeg(tmp_path: Path):
    """HDR JPEG files (with _HDR in stem) are copied to the output directory."""
    (tmp_path / "photo.png").write_bytes(b"fake")
    (tmp_path / "photo_HDR.jpg").write_bytes(b"hdrjpg")
    (tmp_path / "photo_hdr.jpeg").write_bytes(b"hdrjpeg")
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    logger = logging.getLogger("test_copy_hdr_jpeg")
    logger.addHandler(logging.NullHandler())

    _, _, jpg_hdr_files = copy_source_files(tmp_path, output_dir, logger)

    assert len(jpg_hdr_files) == 2
    assert (output_dir / "photo_HDR.jpg").exists()
    assert (output_dir / "photo_hdr.jpeg").exists()


def test_settings_from_dict_accepts_zerofill_up_to_99():
    logger = logging.getLogger("test_zerofill_range")
    logger.addHandler(logging.NullHandler())
    settings = settings_from_dict({"zero_fill_digits": 50}, logger)
    assert settings.zero_fill_digits == 50


def test_logs_dir_creates_and_returns_path():
    from src.config import logs_dir
    p = logs_dir()
    assert p.is_dir()
    assert p.name == "logs"


def test_hdr_output_stem_variants():
    from src.converter import hdr_output_stem
    assert hdr_output_stem(Path("Image_01_HDR.png"), "HDR-PQ").name == "Image_01_HDR-PQ"
    assert hdr_output_stem(Path("Image_01_BW_HDR.png"), "HDR-PQ").name == "Image_01_BW_HDR-PQ"
    assert hdr_output_stem(Path("Image_01_HDR.png"), "HDR-GM").name == "Image_01_HDR-GM"
    assert hdr_output_stem(Path("Image_01_BW_HDR.png"), "HDR-GM").name == "Image_01_BW_HDR-GM"
    assert hdr_output_stem(Path("Image_01_HDR_Duplicate1.png"), "HDR-GM").name == "Image_01_HDR-GM_Duplicate1"


def test_settings_from_dict_migrates_legacy_hdr_enabled():
    logger = logging.getLogger("test_legacy_hdr")
    logger.addHandler(logging.NullHandler())
    s_off = settings_from_dict({"hdr_enabled": False}, logger)
    assert s_off.hdr_pq_enabled is False
    assert s_off.hdr_gm_enabled is False
    s_split = settings_from_dict({"hdr_pq_enabled": True, "hdr_gm_enabled": False}, logger)
    assert s_split.hdr_pq_enabled is True
    assert s_split.hdr_gm_enabled is False


def test_convert_hdr_pq_and_gm_scenarios(tmp_path: Path):
    import imagecodecs
    import numpy as np
    import OpenEXR
    import pillow_heif
    from src.converter import convert_hdr, convert_sdr
    from src.models import EXR_COMPRESSIONS
    from src.results import OutputStatus

    # Real tiny 16-bit HDR PNG & 8-bit SDR PNG so ALL native Python encoders run for real
    hdr_arr = np.full((16, 24, 3), 38000, dtype=np.uint16)
    sdr_arr = np.full((16, 24, 3), 128, dtype=np.uint8)
    hdr_png = tmp_path / "Img_01_HDR.png"
    sdr_png = tmp_path / "Img_01.png"
    hdr_png.write_bytes(imagecodecs.png_encode(hdr_arr))
    sdr_png.write_bytes(imagecodecs.png_encode(sdr_arr))

    class FakeRunner:
        def __init__(self):
            self.commands = []

        def run_cmd(self, cmd, logger):
            self.commands.append(list(cmd))
            tool = cmd[0]
            if tool == "avifgainmaputil":
                out = Path(cmd[4])
            elif tool == "cjxl":
                out = Path(cmd[2])
            else:
                raise AssertionError(f"Unexpected external CLI cmd: {cmd}")
            out.write_bytes(b"ok")

    tool_map = {
        "imagecodecs_python": True,
        "pillow_heif_python": True,
        "openexr_python": True,
        "cjxl": True,
        "avifgainmaputil": True,
    }
    logger = logging.getLogger("test_hdr_gm")
    logger.addHandler(logging.NullHandler())

    # 1. Both HDR/PQ and HDR/GM with paired SDR PNG -> native Python encoders run for real;
    #    ONLY cjxl and avifgainmaputil use FakeRunner!
    settings = AppSettings(hdr_pq_enabled=True, hdr_gm_enabled=True, exr_compression="dwab")
    runner = FakeRunner()
    res = convert_hdr(hdr_png, settings, tool_map, runner, logger, sdr_file=sdr_png)
    assert all(o.status == OutputStatus.SUCCESS for o in res.outputs)
    assert (tmp_path / "Img_01_HDR-PQ.jxl").exists()
    assert (tmp_path / "Img_01_HDR-PQ.heic").exists()
    assert (tmp_path / "Img_01_HDR-PQ.avif").exists()
    assert (tmp_path / "Img_01_HDR.exr").exists()
    assert (tmp_path / "Img_01_HDR-GM.jpg").exists()
    assert (tmp_path / "Img_01_HDR-GM.avif").exists()

    # Verify real binary outputs decoded cleanly
    assert imagecodecs.avif_decode((tmp_path / "Img_01_HDR-PQ.avif").read_bytes()).shape == (16, 24, 3)
    heif_hdr = pillow_heif.open_heif(str(tmp_path / "Img_01_HDR-PQ.heic"), convert_hdr_to_8bit=False)
    assert heif_hdr.size == (24, 16)
    assert imagecodecs.ultrahdr_decode((tmp_path / "Img_01_HDR-GM.jpg").read_bytes()).shape[:2] == (16, 24)
    with OpenEXR.File(str(tmp_path / "Img_01_HDR.exr")) as exr_f:
        h = exr_f.header()
        assert h["compression"] == OpenEXR.DWAB_COMPRESSION
        assert abs(h["chromaticities"][0] - 0.708) < 1e-3
        assert abs(h["whiteLuminance"] - 203.0) < 1e-3

    # Only cjxl (with gaborish/brotli_effort) and avifgainmaputil use subprocess runner
    assert [c[0] for c in runner.commands] == ["cjxl", "avifgainmaputil"]
    assert "--gaborish" in runner.commands[0]
    assert "--brotli_effort" in runner.commands[0]
    assert "--ignore-profile" in runner.commands[1]

    # 2. HDR/GM ONLY (no HDR/PQ) and WITHOUT paired SDR PNG (Scenario 0 auto-SDR fallback)
    #    JXL and HEIC must still be emitted once as *_HDR-PQ.{jxl,heic} and EXR as *_HDR.exr!
    hdr_only = tmp_path / "Solo_02_HDR.png"
    hdr_only.write_bytes(imagecodecs.png_encode(hdr_arr))
    settings_gm_only = AppSettings(hdr_pq_enabled=False, hdr_gm_enabled=True, exr_compression="piz")
    runner2 = FakeRunner()
    res2 = convert_hdr(hdr_only, settings_gm_only, tool_map, runner2, logger, sdr_file=None)
    assert all(o.status == OutputStatus.SUCCESS for o in res2.outputs)
    assert (tmp_path / "Solo_02_HDR-PQ.jxl").exists()
    assert (tmp_path / "Solo_02_HDR-PQ.heic").exists()
    assert (tmp_path / "Solo_02_HDR.exr").exists()
    assert (tmp_path / "Solo_02_HDR-GM.jpg").exists()
    assert (tmp_path / "Solo_02_HDR-GM.avif").exists()
    assert not (tmp_path / "Solo_02_HDR-PQ.avif").exists()
    # Scenario 0 fallback uses native Python libultrahdr (no ffmpeg / ultrahdr_app CLI)
    assert [c[0] for c in runner2.commands] == ["cjxl", "avifgainmaputil"]

    # 3. Verify recompress_exr preserves chromaticities and whiteLuminance
    from src.exr_encoder import recompress_exr
    recomp = tmp_path / "Img_01_recomp.exr"
    recompress_exr(tmp_path / "Img_01_HDR.exr", recomp, compression="piz")
    with OpenEXR.File(str(recomp)) as rf:
        rh = rf.header()
        assert rh["compression"] == OpenEXR.PIZ_COMPRESSION
        assert abs(rh["chromaticities"][0] - 0.708) < 1e-3
        assert abs(rh["whiteLuminance"] - 203.0) < 1e-3

    # 4. Verify all SDR codecs run cleanly (Python JPEG/HEIC/AVIF + cjxl) and EXR is HDR-only
    assert AppSettings().exr_compression == "lj2k"
    assert EXR_COMPRESSIONS[0] == "none"
    assert EXR_COMPRESSIONS[-1] == "lj2k"
    assert EXR_COMPRESSIONS.index("rle") < EXR_COMPRESSIONS.index("piz") < EXR_COMPRESSIONS.index("b44") < EXR_COMPRESSIONS.index("lj2k")

    sdr_all_settings = AppSettings(
        codec_enabled={"jpeg": True, "jpegxl": True, "heic": True, "avif": True, "exr": True}
    )
    sdr_runner = FakeRunner()
    sdr_res = convert_sdr(sdr_png, sdr_all_settings, tool_map, sdr_runner, logger)
    assert len(sdr_res.outputs) == 4  # EXR skipped for SDR
    assert all(o.status == OutputStatus.SUCCESS for o in sdr_res.outputs)
    assert [c[0] for c in sdr_runner.commands] == ["cjxl"]
    assert (tmp_path / "Img_01.jpg").exists()
    assert (tmp_path / "Img_01.jxl").exists()
    assert (tmp_path / "Img_01.heic").exists()
    assert (tmp_path / "Img_01.avif").exists()
    assert not (tmp_path / "Img_01.exr").exists()

    # 5. EXR-only HDR run: hdr_pq_enabled=False AND hdr_gm_enabled=False must still emit *_HDR.exr
    exr_indep_png = tmp_path / "Indep_03_HDR.png"
    exr_indep_png.write_bytes(imagecodecs.png_encode(hdr_arr))
    exr_indep_settings = AppSettings(
        hdr_pq_enabled=False,
        hdr_gm_enabled=False,
        exr_compression="lj2k",
        codec_enabled={"jpeg": True, "jpegxl": True, "heic": True, "avif": True, "exr": True},
    )
    exr_indep_runner = FakeRunner()
    exr_indep_res = convert_hdr(exr_indep_png, exr_indep_settings, tool_map, exr_indep_runner, logger)
    assert len(exr_indep_res.outputs) == 1
    assert exr_indep_res.outputs[0].status == OutputStatus.SUCCESS
    assert (tmp_path / "Indep_03_HDR.exr").exists()
    assert exr_indep_runner.commands == []
    with OpenEXR.File(str(tmp_path / "Indep_03_HDR.exr")) as ef:
        eh = ef.header()
        assert eh["compression"] == OpenEXR.LJ2K_COMPRESSION
        assert abs(eh["chromaticities"][0] - 0.708) < 1e-3
        assert abs(eh["whiteLuminance"] - 203.0) < 1e-3


def test_rename_plan_space_after_prefix():
    from src.renamer import build_rename_plan

    classified = classify_files([Path("shot.png")], [])

    # Default space_after_prefix=True inserts space for plain word prefix
    s_on = AppSettings(prefix="Auto", start_counter=23, space_after_prefix=True)
    plan_on = build_rename_plan(classified, s_on, None)
    assert plan_on[0].target.name == "Auto 23.png"

    # Disabled space_after_prefix=False concatenates directly
    s_off = AppSettings(prefix="Auto", start_counter=23, space_after_prefix=False)
    plan_off = build_rename_plan(classified, s_off, None)
    assert plan_off[0].target.name == "Auto23.png"

    # Prefix already ending with '_' / '-' / ' ' does not get an extra space
    s_under = AppSettings(prefix="Image_", start_counter=23, space_after_prefix=True)
    plan_under = build_rename_plan(classified, s_under, None)
    assert plan_under[0].target.name == "Image_23.png"
