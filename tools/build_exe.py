"""Build standalone Windows release artifacts via PyInstaller.

Produces both GitHub Release variants in ``dist/`` by default:
1. **Portable ZIP (`--onedir`):**
   - Builds ``dist/TrueHDRPhotoConverter/`` (``TrueHDRPhotoConverter.exe``, ``_internal/``, ``bin/``),
     compresses it into ``dist/TrueHDRPhotoConverter.zip``, and removes the temporary
     unpacked folder so ``dist/`` stays clean.
   - Portable settings (``data/settings.json``) and logs (``data/logs/``) are
     created automatically at runtime when the portable build runs.
2. **Single-file EXE (`--onefile`):**
   - ``dist/TrueHDRPhotoConverter.exe`` (embeds ``bin/`` inside ``_MEIPASS/bin``).

Usage
-----
    python tools/build_exe.py             # build BOTH portable ZIP and onefile EXE
    python tools/build_exe.py --onefile   # build only dist/TrueHDRPhotoConverter.exe
    python tools/build_exe.py --onedir    # build only dist/TrueHDRPhotoConverter.zip
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (relative to project root)
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENTRY_POINT = PROJECT_ROOT / "src" / "main.py"
STYLES_QSS = PROJECT_ROOT / "src" / "styles.qss"
BIN_DIR = PROJECT_ROOT / "bin"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
EXE_NAME = "TrueHDRPhotoConverter"

# Dynamic Cython / native submodules used by our Python encoders.
# Listing only the imagecodecs submodules we actually call avoids bundling ~50
# unused codecs and keeps executables smaller and faster to start.
HIDDEN_IMPORTS = [
    "imagecodecs._shared",
    "imagecodecs._shared_cython",
    "imagecodecs._imcd",
    "imagecodecs._png",
    "imagecodecs._jpeg",
    "imagecodecs._avif",
    "imagecodecs._ultrahdr",
    "pillow_heif",
    "OpenEXR",
    "Imath",
]


def _base_pyinstaller_cmd(*, onefile: bool) -> list[str]:
    sep = ";" if sys.platform == "win32" else ":"
    workpath = BUILD_DIR / ("onefile" if onefile else "onedir")

    cmd: list[str] = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--noconsole",
        "--onefile" if onefile else "--onedir",
        "--name", EXE_NAME,
        "--distpath", str(DIST_DIR),
        "--workpath", str(workpath),
        "--specpath", str(workpath),
        "--add-data", f"{STYLES_QSS}{sep}src",
        "--collect-binaries", "pillow_heif",
        "--exclude-module", "cv2",
    ]

    for mod in HIDDEN_IMPORTS:
        cmd.extend(["--hidden-import", mod])

    # In --onefile mode, embed bin/ directly into _MEIPASS/bin/.
    # In --onedir mode, bin/ is copied cleanly next to TrueHDRPhotoConverter.exe.
    if onefile and BIN_DIR.is_dir():
        bundled_files = sorted(p for p in BIN_DIR.iterdir() if p.is_file())
        for bin_file in bundled_files:
            cmd.extend(["--add-data", f"{bin_file}{sep}bin"])
        print(f"[onefile] Embedding {len(bundled_files)} file(s) from {BIN_DIR} -> _MEIPASS/bin/")

    cmd.append(str(ENTRY_POINT))
    return cmd


def _copy_bin_into_portable_dir(portable_dir: Path) -> None:
    """Copy ``bin/`` right next to ``TrueHDRPhotoConverter.exe`` inside *portable_dir*."""
    if BIN_DIR.is_dir():
        target_bin = portable_dir / "bin"
        if target_bin.exists():
            shutil.rmtree(target_bin)
        target_bin.mkdir(parents=True, exist_ok=True)
        bundled_files = sorted(p for p in BIN_DIR.iterdir() if p.is_file())
        for bin_file in bundled_files:
            shutil.copy2(bin_file, target_bin / bin_file.name)
        print(f"[onedir] Copied {len(bundled_files)} file(s) -> {target_bin}")
    else:
        print(f"WARNING: {BIN_DIR} not found; portable archive will lack bundled CLI tools.")


def _zip_portable_dir(portable_dir: Path, zip_path: Path) -> None:
    """Compress *portable_dir* into *zip_path* with top-level ``TrueHDRPhotoConverter/``."""
    if zip_path.exists():
        zip_path.unlink()

    files = sorted(p for p in portable_dir.rglob("*") if p.is_file())
    with zipfile.ZipFile(
        zip_path, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as zf:
        for file_path in files:
            arcname = file_path.relative_to(portable_dir.parent)
            zf.write(file_path, arcname=str(arcname))

    size_mib = zip_path.stat().st_size / (1024 * 1024)
    print(f"[onedir] Created portable archive: {zip_path} ({size_mib:.2f} MiB, {len(files)} files)")


def build_onedir() -> int:
    portable_dir = DIST_DIR / EXE_NAME
    if portable_dir.exists():
        shutil.rmtree(portable_dir)

    cmd = _base_pyinstaller_cmd(onefile=False)
    print("[onedir] Running:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if result.returncode != 0:
        print(f"[onedir] Build failed (exit code {result.returncode})", file=sys.stderr)
        return result.returncode

    _copy_bin_into_portable_dir(portable_dir)
    zip_path = DIST_DIR / f"{EXE_NAME}.zip"
    _zip_portable_dir(portable_dir, zip_path)

    # Remove unpacked folder after zipping so dist/ contains only release artifacts
    shutil.rmtree(portable_dir)
    print(f"[onedir] Cleaned temporary folder: {portable_dir}")
    return 0


def build_onefile() -> int:
    exe_path = DIST_DIR / f"{EXE_NAME}.exe"
    if exe_path.exists():
        exe_path.unlink()

    cmd = _base_pyinstaller_cmd(onefile=True)
    print("[onefile] Running:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if result.returncode != 0:
        print(f"[onefile] Build failed (exit code {result.returncode})", file=sys.stderr)
        return result.returncode

    size_mib = exe_path.stat().st_size / (1024 * 1024) if exe_path.exists() else 0.0
    print(f"[onefile] Build successful: {exe_path} ({size_mib:.2f} MiB)")
    return 0


def main(argv: list[str] | None = None) -> int:
    if not ENTRY_POINT.exists():
        print(f"ERROR: entry point not found: {ENTRY_POINT}", file=sys.stderr)
        return 1

    parser = argparse.ArgumentParser(
        description="Build TrueHDRPhotoConverter Windows onefile EXE and/or portable onedir ZIP."
    )
    parser.add_argument("--onefile", action="store_true", help="Build only single-file EXE.")
    parser.add_argument("--onedir", action="store_true", help="Build only portable ZIP.")
    args = parser.parse_args(argv)

    run_onedir = args.onedir or not args.onefile
    run_onefile = args.onefile or not args.onedir

    if run_onedir:
        rc = build_onedir()
        if rc != 0:
            return rc

    if run_onefile:
        rc = build_onefile()
        if rc != 0:
            return rc

    print("\nAll requested build artifacts completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
