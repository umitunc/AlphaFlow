# -*- coding: utf-8 -*-
"""
AlphaFlow Studio Pro — Uygulama Başlatıcı (Composition Root & Self-Bootstrapper).
Hem Windows hem de macOS üzerinde eksik kütüphaneleri ve AI modelini otomatik kurar.
"""

from pathlib import Path
import sys
from src.core.bootstrap import ensure_dependencies


def main() -> int:
    # 1. Eksik Python paketlerini (PySide6, onnxruntime, opencv-python, Pillow, imageio-ffmpeg) kontrol et ve otomatik kur
    if not ensure_dependencies(auto_install=True):
        print("Gerekli kütüphaneler kurulamadı. Lütfen internet bağlantınızı kontrol edin.", file=sys.stderr)
        return 1

    from PySide6.QtWidgets import QApplication
    from src.engines.model_downloader import ensure_rvm_model
    from src.engines.rvm_engine import RVMOnnxEngine
    from src.ui.main_window import AlphaFlowMainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("AlphaFlow Studio Pro")

    # 2. RVM ONNX Model dosyasını kontrol et / eksikse otomatik indir
    models_dir = str(Path(__file__).resolve().parent / "models")
    model_path = ensure_rvm_model(models_dir)

    # 3. Dependency Injection ile motoru başlat ve ana pencereye enjekte et
    engine = RVMOnnxEngine(model_path=model_path)
    window = AlphaFlowMainWindow(engine=engine)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
