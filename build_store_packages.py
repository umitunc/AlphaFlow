# -*- coding: utf-8 -*-
"""
AlphaFlow Studio Pro — Microsoft Store (MSIX) & Mac App Store (.app) Paketleyici.
1. AI/Codec motorunu (`src/bridge/headless_worker.py`) bağımsız `alphaflow_engine`
   sidecar ikilisi olarak derler (hedef sistemde Python gerektirmez).
2. Flutter Windows veya macOS Release derlemesini çalıştırır ve AI motorunu pakete gömer.
3. Windows üzerinde Microsoft Store uyumlu `.msix` paketini üretir.
"""

import platform
import shutil
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent


def build_headless_engine_sidecar() -> Path:
    from src.core.bootstrap import ensure_dependencies
    from src.engines.model_downloader import ensure_rvm_model

    ensure_dependencies(auto_install=True)
    models_dir = ROOT_DIR / "models"
    model_path = ensure_rvm_model(str(models_dir))

    sep = ";" if platform.system().lower() == "windows" else ":"
    add_data_arg = f"{model_path}{sep}models"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--noconsole",
        "--name",
        "alphaflow_engine",
        "--add-data",
        add_data_arg,
        "--collect-binaries",
        "imageio_ffmpeg",
        "--collect-binaries",
        "onnxruntime",
        str(ROOT_DIR / "src" / "bridge" / "headless_worker.py"),
    ]
    print("[1/3] AI & FFmpeg Sidecar Motoru derleniyor...")
    subprocess.run(cmd, cwd=str(ROOT_DIR), check=True)
    return ROOT_DIR / "dist" / "alphaflow_engine"


def build_flutter_platform(sidecar_dir: Path) -> None:
    is_win = platform.system().lower() == "windows"
    flutter_cmd = "flutter.bat" if is_win else "flutter"

    if is_win:
        print("[2/3] Flutter Windows Release derleniyor...")
        subprocess.run([flutter_cmd, "build", "windows", "--release"], cwd=str(ROOT_DIR), check=True)
        release_dir = ROOT_DIR / "build" / "windows" / "x64" / "runner" / "Release"
        target_engine_dir = release_dir / "engine"
        if target_engine_dir.exists():
            shutil.rmtree(target_engine_dir)
        shutil.copytree(sidecar_dir, target_engine_dir)
        print("[3/3] Microsoft Store MSIX paketi oluşturuluyor...")
        subprocess.run(
            ["dart", "run", "msix:create", "--build-windows=false"],
            cwd=str(ROOT_DIR),
            check=False,
        )
        print(f"Tamamlandı! Windows Release & MSIX dizini: {release_dir}")
    else:
        print("[2/3] Flutter macOS Release derleniyor...")
        subprocess.run([flutter_cmd, "build", "macos", "--release"], cwd=str(ROOT_DIR), check=True)
        app_bundle = (
            ROOT_DIR / "build" / "macos" / "Build" / "Products" / "Release" / "AlphaFlow Studio Pro.app"
        )
        macos_exec_dir = app_bundle / "Contents" / "MacOS" / "engine"
        if macos_exec_dir.exists():
            shutil.rmtree(macos_exec_dir)
        shutil.copytree(sidecar_dir, macos_exec_dir)
        print(f"[3/3] Tamamlandı! Mac App Store uygulama paketi: {app_bundle}")


if __name__ == "__main__":
    engine_out = build_headless_engine_sidecar()
    build_flutter_platform(engine_out)

