#!/usr/bin/env python3
"""Build helper: compile frontend, run PyInstaller, stage binary for Tauri."""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DESKTOP = ROOT / "desktop"
FRONTEND = ROOT / "frontend"
TAURI_BINS = DESKTOP / "src-tauri" / "binaries"


def _target_triple() -> str:
    """Return the Rust-style target triple for the current platform."""
    machine = platform.machine().lower()
    system = platform.system()

    if system == "Darwin":
        arch = "aarch64" if machine == "arm64" else "x86_64"
        return f"{arch}-apple-darwin"
    elif system == "Windows":
        return "x86_64-pc-windows-msvc"
    else:
        arch = "x86_64" if machine == "x86_64" else machine
        return f"{arch}-unknown-linux-gnu"


def build_frontend() -> None:
    """Build the React frontend for desktop mode."""
    print("==> Building frontend...")
    subprocess.run(
        ["npm", "run", "build:desktop"],
        cwd=FRONTEND,
        check=True,
    )
    print("==> Frontend built.")


def build_pyinstaller() -> None:
    """Run PyInstaller to freeze the Python backend."""
    print("==> Running PyInstaller...")
    subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--clean", "foundrai.spec"],
        cwd=DESKTOP,
        check=True,
    )
    print("==> PyInstaller done.")


def stage_binary() -> None:
    """Copy the frozen binary to the Tauri binaries directory."""
    triple = _target_triple()
    ext = ".exe" if platform.system() == "Windows" else ""
    binary_name = f"foundrai-server-{triple}{ext}"

    # PyInstaller output
    dist_dir = DESKTOP / "dist" / "foundrai-server"
    if not dist_dir.exists():
        print(f"ERROR: PyInstaller output not found at {dist_dir}")
        sys.exit(1)

    TAURI_BINS.mkdir(parents=True, exist_ok=True)

    # For --onedir mode, copy the entire directory
    dest = TAURI_BINS / f"foundrai-server-{triple}"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(dist_dir, dest)

    # Also create the expected entry-point binary name
    src_exe = dist_dir / f"foundrai-server{ext}"
    dest_exe = TAURI_BINS / binary_name
    if src_exe.exists():
        shutil.copy2(src_exe, dest_exe)
        print(f"==> Staged {dest_exe}")

    print(f"==> Binary staged for target: {triple}")


def main() -> None:
    build_frontend()
    build_pyinstaller()
    stage_binary()
    print("==> Build complete! Run 'cargo tauri build' from desktop/ to create installer.")


if __name__ == "__main__":
    main()
