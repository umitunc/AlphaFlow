# -*- coding: utf-8 -*-
"""
Single Responsibility: Windows ve macOS işletim sistemleri arasındaki farkları
(Dosya gezgininde gösterme, sistem fontları, GPU sağlayıcıları, FFmpeg doğrulaması)
soyutlayan çapraz platform (Cross-Platform) yardımcı katmanı.
"""

import os
import platform
import subprocess
from pathlib import Path
from typing import Dict, List


def is_windows() -> bool:
    return platform.system().lower() == "windows"


def is_macos() -> bool:
    return platform.system().lower() == "darwin"


def reveal_in_file_manager(file_path: str) -> None:
    """Çıktı dosyasını Windows Explorer veya macOS Finder içinde seçili olarak açar."""
    target = Path(file_path).resolve()
    if not target.exists():
        target = target.parent

    if is_windows():
        if target.is_file():
            subprocess.Popen(["explorer", f"/select,{str(target)}"])
        else:
            os.startfile(str(target))  # type: ignore[attr-defined]
    elif is_macos():
        if target.is_file():
            subprocess.Popen(["open", "-R", str(target)])
        else:
            subprocess.Popen(["open", str(target)])
    else:
        subprocess.Popen(["xdg-open", str(target.parent if target.is_file() else target)])


def get_platform_font_candidates() -> List[str]:
    """Windows ve macOS için kalın/sinematik TrueType font yollarını döner."""
    if is_windows():
        windir = os.environ.get("WINDIR", r"C:\Windows")
        fdir = os.path.join(windir, "Fonts")
        return [
            os.path.join(fdir, "impact.ttf"),
            os.path.join(fdir, "segoeuib.ttf"),
            os.path.join(fdir, "arialbd.ttf"),
            os.path.join(fdir, "georgiab.ttf"),
        ]
    if is_macos():
        return [
            "/System/Library/Fonts/Supplemental/Impact.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/HelveticaNeue.ttc",
            "/Library/Fonts/Arial Bold.ttf",
        ]
    return [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    ]


def get_preferred_ort_providers() -> List[str]:
    """
    Windows (CUDA / DirectML) ve macOS Apple Silicon (CoreML) için
    en hızlı donanım hızlandırma sağlayıcı listesini döner.
    """
    import onnxruntime as ort

    available = ort.get_available_providers()
    preferred = [
        "CUDAExecutionProvider",
        "CoreMLExecutionProvider",
        "DmlExecutionProvider",
        "CPUExecutionProvider",
    ]
    active = [p for p in preferred if p in available]
    return active if active else available


def get_system_diagnostics() -> Dict[str, str]:
    """Sistemin OS, Python, FFmpeg ve ONNX donanım durumunu raporlar."""
    import imageio_ffmpeg
    import onnxruntime as ort

    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
    providers = get_preferred_ort_providers()
    return {
        "os": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "python": platform.python_version(),
        "accelerator": providers[0].replace("ExecutionProvider", ""),
        "ffmpeg": Path(ffmpeg_path).name if ffmpeg_path else "Bulunamadı",
    }
