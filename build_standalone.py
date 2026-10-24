# -*- coding: utf-8 -*-
"""
AlphaFlow Studio Pro — Bağımsız (Standalone) Uygulama Paketleyici.
Windows üzerinde `dist/AlphaFlowStudio.exe`,
macOS üzerinde `dist/AlphaFlowStudio.app` üretir.
"""

import importlib.util
import os
import platform
import subprocess
import sys
from pathlib import Path


def ensure_pyinstaller() -> None:
    if importlib.util.find_spec("PyInstaller") is None:
        print("[Build] PyInstaller bulunamadı, otomatik kuruluyor...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)


def build() -> None:
    from src.core.bootstrap import ensure_dependencies
    from src.engines.model_downloader import ensure_rvm_model

    ensure_dependencies(auto_install=True)
    ensure_pyinstaller()

    root_dir = Path(__file__).resolve().parent
    models_dir = root_dir / "models"
    model_path = ensure_rvm_model(str(models_dir))

    sep = ";" if platform.system().lower() == "windows" else ":"
    add_data_arg = f"{model_path}{sep}models"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        "AlphaFlowStudio",
        "--add-data",
        add_data_arg,
        "--collect-binaries",
        "imageio_ffmpeg",
        "--collect-binaries",
        "onnxruntime",
        str(root_dir / "main.py"),
    ]

    print(f"[Build] {platform.system()} için bağımsız uygulama derleniyor...")
    subprocess.run(cmd, cwd=str(root_dir), check=True)
    print(f"[Build] Tamamlandı! Çıktı dizini: {root_dir / 'dist'}")


if __name__ == "__main__":
    build()
