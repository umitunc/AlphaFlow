# -*- coding: utf-8 -*-
"""
Single Responsibility: Windows Media Player'ın açamadığı profesyonel
Apple ProRes 4444 (.mov / ap4h), WebM VP9 Alpha (.webm) ve MP4 videoları
kodek gerektirmeden doğrudan uygulama içinde oynatan dahili stüdyo oynatıcısı.
"""

from pathlib import Path
import cv2
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
)
from src.core.platform_utils import reveal_in_file_manager
from src.ui.theme import STUDIO_DARK_QSS


class StudioVideoPlayerDialog(QDialog):
    """ProRes 4444 (ap4h), WebM Alpha ve MP4 destekli dahili video oynatıcı penceresi."""

    def __init__(self, video_path: str, parent=None) -> None:
        super().__init__(parent)
        self._video_path = video_path
        self._cap = cv2.VideoCapture(video_path)
        self._fps = self._cap.get(cv2.CAP_PROP_FPS) or 24.0
        self._total_frames = max(1, int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT)))
        self._current_idx = 0
        self._playing = True

        self.setWindowTitle(f"AlphaFlow Dahili Stüdyo Oynatıcı — {Path(video_path).name}")
        self.resize(900, 620)
        self.setStyleSheet(STUDIO_DARK_QSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        info_lbl = QLabel(
            f"🎬  {Path(video_path).name}   |   Dahili FFmpeg/ProRes 4444 (ap4h) & Alpha Kodek Motoru Aktif"
        )
        info_lbl.setStyleSheet("color: #D5A853; font-weight: 700; font-size: 13px;")
        layout.addWidget(info_lbl)

        self._screen = QLabel("Video yükleniyor...")
        self._screen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._screen.setMinimumSize(640, 420)
        self._screen.setStyleSheet(
            "background-color: #0D0F14; border: 1px solid #2A303D; border-radius: 8px;"
        )
        layout.addWidget(self._screen, stretch=1)

        ctrl_row = QHBoxLayout()
        self._play_btn = QPushButton("⏸ Duraklat")
        self._play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._play_btn.clicked.connect(self._toggle_play)

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, max(0, self._total_frames - 1))
        self._slider.sliderMoved.connect(self._on_seek)

        self._frame_lbl = QLabel(f"1 / {self._total_frames}")
        self._frame_lbl.setStyleSheet("color: #B8C0D0; font-weight: 600;")

        self._reveal_btn = QPushButton("📂 Dosyayı Klasörde Göster")
        self._reveal_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._reveal_btn.clicked.connect(lambda: reveal_in_file_manager(self._video_path))

        ctrl_row.addWidget(self._play_btn)
        ctrl_row.addWidget(self._slider, stretch=1)
        ctrl_row.addWidget(self._frame_lbl)
        ctrl_row.addWidget(self._reveal_btn)
        layout.addLayout(ctrl_row)

        self._timer = QTimer(self)
        self._timer.setInterval(max(15, int(1000.0 / self._fps)))
        self._timer.timeout.connect(self._next_frame)
        self._timer.start()

    def _toggle_play(self) -> None:
        self._playing = not self._playing
        if self._playing:
            self._play_btn.setText("⏸ Duraklat")
            self._timer.start()
        else:
            self._play_btn.setText("▶️ Oynat")
            self._timer.stop()

    def _on_seek(self, frame_idx: int) -> None:
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        self._current_idx = frame_idx
        self._read_and_display()

    def _next_frame(self) -> None:
        if not self._read_and_display():
            # Video bittiğinde başa sar (Loop)
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self._current_idx = 0
            self._read_and_display()

    def _read_and_display(self) -> bool:
        if not self._cap.isOpened():
            return False
        ret, frame_bgr = self._cap.read()
        if not ret:
            return False

        self._current_idx = int(self._cap.get(cv2.CAP_PROP_POS_FRAMES))
        self._slider.blockSignals(True)
        self._slider.setValue(max(0, self._current_idx - 1))
        self._slider.blockSignals(False)
        self._frame_lbl.setText(f"{self._current_idx} / {self._total_frames}")

        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(qimg).scaled(
            self._screen.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._screen.setPixmap(pix)
        return True

    def closeEvent(self, event) -> None:
        self._timer.stop()
        if self._cap.isOpened():
            self._cap.release()
        super().closeEvent(event)
