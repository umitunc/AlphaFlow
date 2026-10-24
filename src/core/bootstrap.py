# -*- coding: utf-8 -*-
"""
Single Responsibility: Uygulama ilk kez yeni bir Windows veya macOS bilgisayarda
çalıştırıldığında eksik Python kütüphanelerini (PySide6, onnxruntime, opencv-python,
numpy, Pillow, imageio-ffmpeg) tespit eder ve otomatik olarak kurar.
Sadece Python standart kütüphanesini (stdlib) kullanır.
"""

import importlib.util
import subprocess
import sys
from typing import List, Tuple

REQUIRED_PACKAGES: List[Tuple[str, str]] = [
    ("PySide6", "PySide6>=6.6.0"),
    ("onnxruntime", "onnxruntime>=1.17.0"),
    ("cv2", "opencv-python>=4.9.0"),
    ("numpy", "numpy>=1.26.0"),
    ("PIL", "Pillow>=10.0.0"),
    ("imageio_ffmpeg", "imageio-ffmpeg>=0.5.1"),
]


def find_missing_packages() -> List[str]:
    """Sistemde kurulu olmayan paketlerin pip kurulum isimlerini döner."""
    missing: List[str] = []
    for import_name, pip_spec in REQUIRED_PACKAGES:
        if importlib.util.find_spec(import_name) is None:
            missing.append(pip_spec)
    return missing


def ensure_dependencies(auto_install: bool = True) -> bool:
    """
    Eksik kütüphaneleri kontrol eder; auto_install=True ise pip ile otomatik kurar.
    Tüm bağımlılıklar hazırsa True döner.
    """
    missing = find_missing_packages()
    if not missing:
        return True

    if not auto_install:
        return False

    print(f"[AlphaFlow Bootstrap] Eksik kütüphaneler tespit edildi: {', '.join(missing)}")
    print("[AlphaFlow Bootstrap] Otomatik kurulum başlatılıyor, lütfen bekleyin...")

    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", *missing]
    res = subprocess.run(cmd, check=False)
    if res.returncode != 0:
        print("[AlphaFlow Bootstrap] HATA: Kütüphane kurulumu başarısız oldu.", file=sys.stderr)
        return False

    print("[AlphaFlow Bootstrap] Tüm kütüphaneler başarıyla kuruldu!")
    return len(find_missing_packages()) == 0
