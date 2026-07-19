"""Build BSpeak95 with PyInstaller.

Usage:
    uv run python build.py

Produces dist/BSpeak95.zip containing the one-folder bundle.
"""

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
DIST = ROOT / "dist"
BUILD = ROOT / "build"
APP_NAME = "BSpeak95"


def find_upx():
    """Try to find UPX on PATH or common locations."""
    for candidate in ["upx", r"C:\upx\upx.exe", r"C:\tools\upx\upx.exe"]:
        if shutil.which(candidate):
            return str(Path(shutil.which(candidate)).parent)
    return None


def build_hidden_imports():
    """Return --hidden-import arguments for modules PyInstaller can miss."""
    return [
        "--hidden-import", "prism",
        "--hidden-import", "prism.common",
        "--hidden-import", "prism.core",
        "--hidden-import", "prism.custom",
        "--hidden-import", "prism._native",
        # Prism's compiled module is a cffi extension; it needs the cffi runtime
        # backend, which nothing imports directly so PyInstaller misses it.
        "--hidden-import", "_cffi_backend",
        "--hidden-import", "cffi",
    ]


def espeak_data():
    """Bundle the eSpeak DLLs and voice data next to the frozen app.

    _espeak.py loads the DLL and its espeak-ng-data directory from the bundle
    root (sys._MEIPASS) at run time; PyInstaller cannot see these dynamic ctypes
    loads, so we add them explicitly.
    """
    src = ROOT / "src"
    args = []
    for dll in ("espeak.dll", "espeak64.dll"):
        f = src / dll
        if f.exists():
            args += ["--add-binary", f"{f}{os.pathsep}."]
        else:
            print(f"WARNING: expected eSpeak DLL not found: {f}", file=sys.stderr)
    data = src / "espeak-ng-data"
    if data.is_dir():
        args += ["--add-data", f"{data}{os.pathsep}espeak-ng-data"]
    else:
        print(f"WARNING: espeak-ng-data not found: {data}", file=sys.stderr)
    return args


def prism_native_binaries():
    """Return --add-binary arguments for Prism's compiled cffi module and its
    native library.

    Prism keeps ``_prism_cffi.pyd`` and ``prism.dll`` in ``prism/_native`` and
    only exposes ``prism._prism_cffi`` at runtime, by appending that directory
    to ``prism.__path__`` (see prism/_native.py). PyInstaller's analysis never
    sees the extension module, so ``--collect-all`` misses the .pyd. We add both
    files back into ``prism/_native`` so that runtime __path__ hack finds them,
    exactly as it does in the virtualenv.
    """
    import prism

    native = Path(prism.__file__).parent / "_native"
    args = []
    for name in ("_prism_cffi.pyd", "prism.dll"):
        f = native / name
        if f.exists():
            args += ["--add-binary", f"{f}{os.pathsep}prism/_native"]
        else:
            print(f"WARNING: expected Prism native file not found: {f}",
                  file=sys.stderr)
    return args

def make_zip(folder, zip_path):
    """Create a zip archive of the given folder."""
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for root, _, files in os.walk(folder):
            for f in files:
                full = Path(root) / f
                arcname = Path(APP_NAME) / full.relative_to(folder)
                zf.write(full, arcname)
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"Created {zip_path} ({size_mb:.1f} MB)")


def main():
    # Clean previous builds
    for d in [BUILD, DIST]:
        if d.exists():
            try:
                shutil.rmtree(d)
            except PermissionError:
                print(
                    f"Could not remove {d}: it is in use by another process.\n"
                    f"Close any running {APP_NAME}.exe and make sure no terminal "
                    f"is inside {d}, then run the build again.",
                    file=sys.stderr,
                )
                sys.exit(1)

    # Ensure Prism is available in the build environment.
    try:
        __import__("prism")
    except Exception as e:
        print(
            "Prism is not installed in this environment. "
            "Install prismatoid in .venv before building.",
            file=sys.stderr,
        )
        print(f"Import error: {e}", file=sys.stderr)
        sys.exit(1)

    cmd1 = [
        sys.executable,
        "versionfile.py",
    ]
    cmd2 = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--onedir",
        "--noupx" if not find_upx() else f"--upx-dir={find_upx()}",
        "--version-file=vdata.txt",
        # Speed optimisations
        "--optimize", "2",
        "--noconfirm",
        "--clean",
        # Entry point
        str(ROOT / "src/emu.py"),
    ]
    subprocess.run(cmd1, cwd=str(ROOT), check=True)
    cmd2 += build_hidden_imports()

    # Collect Prism package modules and native assets.
    cmd2 += ["--collect-all", "prism"]
    # ...and add the compiled cffi module + native lib that --collect-all misses.
    cmd2 += prism_native_binaries()

    # Bundle the eSpeak engine (DLLs + voice data) for the --espeak-voice path.
    cmd2 += espeak_data()

    # Exclude unnecessary large modules
    for mod in ["tkinter", "_tkinter", "unittest", "test", "setuptools",
                "pip", "wheel"]:
        cmd2 += ["--exclude-module", mod]

    print("Running PyInstaller...")
    print(" ".join(cmd2))
    result = subprocess.run(cmd2, cwd=str(ROOT))
    if result.returncode != 0:
        print("PyInstaller failed!", file=sys.stderr)
        sys.exit(1)

    output_dir = DIST / APP_NAME
    if not output_dir.exists():
        print(f"Expected output dir {output_dir} not found!", file=sys.stderr)
        sys.exit(1)

    # Create zip
    zip_path = DIST / f"{APP_NAME}.zip"
    print("Creating zip archive...")
    make_zip(output_dir, zip_path)

    print("Build complete!")
    print(f"  Folder: {output_dir}")
    print(f"  Archive: {zip_path}")


if __name__ == "__main__":
    main()
