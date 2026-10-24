# -*- coding: utf-8 -*-
"""
Single Responsibility: Sürükle-Bırak (Drag & Drop) ve dosya seçici video yükleme alanı.
"""

from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QPushButton

SUPPORTED_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}


class DropZoneWidget(QFrame):
    """Kullanıcının videoyu sürükleyip bırakabileceği veya seçebileceği üst bar bileşeni."""

    video_Dropped = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFixedHeight(74)
        self._apply_style(False)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 10, 18, 10)

        self._info_label = QLabel(
            "🎬  Videoyu buraya sürükleyip bırakın  (.mp4, .mov, .webm)  veya sağdan seçin"
        )
        self._info_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #D5A853;")

        self._browse_btn = QPushButton("Dosya Seç...")
        self._browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._browse_btn.clicked.connect(self._open_dialog)

        layout.addWidget(self._info_label, stretch=1)
        layout.addWidget(self._browse_btn)

    def _apply_style(self, highlight: bool) -> None:
        border_color = "#E5B95C" if highlight else "#383F52"
        bg_color = "#1F2430" if highlight else "#171A22"
        self.setStyleSheet(
            f"DropZoneWidget {{ background-color: {bg_color}; "
            f"border: 2px dashed {border_color}; border-radius: 10px; }}"
        )

    def set_loaded_file(self, path: str, width: int, height: int, fps: float, frames: int) -> None:
        name = Path(path).name
        dur = frames / max(1.0, fps)
        self._info_label.setText(
            f"✅  {name}   |   {width}x{height} px   |   {fps:.1f} FPS   |   {frames} Kare ({dur:.1f} sn)"
        )

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if Path(url.toLocalFile()).suffix.lower() in SUPPORTED_EXTS:
                    self._apply_style(True)
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self._apply_style(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        self._apply_style(False)
        for url in event.mimeData().urls():
            local_path = url.toLocalFile()
            if Path(local_path).suffix.lower() in SUPPORTED_EXTS:
                self.video_Dropped.emit(local_path)
                event.acceptProposedAction()
                return

    def _open_dialog(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Maskelenecek Videoyu Seçin",
            "",
            "Video Dosyaları (*.mp4 *.mov *.mkv *.avi *.webm)",
        )
        if file_path:
            self.video_Dropped.emit(file_path)
