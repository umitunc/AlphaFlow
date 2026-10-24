# -*- coding: utf-8 -*-
"""
Single Responsibility: Sol (Orijinal Video — Drag & Drop destekli) ve
Sağ (Otomatik Çıktı / Sadece Maske / Gerçek Şeffaf Kesim / 3D Arkadaki Yazı)
ekranlarını yan yana gösteren ve timeline üzerinden anlık kare önizlemesi sağlayan bileşen.
"""

from pathlib import Path
import cv2
import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QImage, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)
from src.core.contracts import ExportMode, MattingConfig, PreviewMode
from src.engines.mask_postprocessor import MaskPostProcessor
from src.ui.drop_zone import SUPPORTED_EXTS


class PreviewCanvasWidget(QWidget):
    """Yan yana (Before / After) canlı video önizleme, Drag & Drop ve görünüm seçici bileşen."""

    scrub_requested = Signal(int)             # Kullanıcının seçtiği kare indeksi
    video_dropped = Signal(str)               # Orijinal video karesine sürüklenen dosya
    preview_mode_selected = Signal(object)    # Sağ panel üstündeki hızlı görünüm sekmesi

    _MODE_TITLES = {
        PreviewMode.LUMA_MATTE: "SAĞ ÖNİZLEME: SADECE MASKE (SİYAH-BEYAZ LUMA MATTE)",
        PreviewMode.CHECKERBOARD: "SAĞ ÖNİZLEME: GERÇEK ŞEFFAF KESİM (RGBA ALPHA)",
        PreviewMode.GREENSCREEN: "SAĞ ÖNİZLEME: YEŞİL PERDE (CHROMA KEY ÇIKTISI)",
        PreviewMode.DEPTH_TEXT_DEMO: "SAĞ ÖNİZLEME: 3D KARAKTER ARKASI YAZI (SANDVİÇ KATMANI)",
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 2, 0, 2)
        root.setSpacing(6)

        # Hızlı Görünüm Seçici Bar (Sağ Ekran Modları)
        mode_bar = QHBoxLayout()
        mode_bar.setSpacing(6)
        bar_lbl = QLabel("👁️ Önizleme Görünümü:")
        bar_lbl.setStyleSheet("color: #D5A853; font-weight: 700;")
        mode_bar.addWidget(bar_lbl)

        self._btn_group = QButtonGroup(self)
        self._btn_group.setExclusive(True)
        self._mode_buttons: dict[PreviewMode, QPushButton] = {}

        modes = [
            (PreviewMode.AUTO_EXPORT, "🔄 Çıktı Formatına Göre (Otomatik)"),
            (PreviewMode.LUMA_MATTE, "⬛ Sadece Maske (S/B)"),
            (PreviewMode.CHECKERBOARD, "🏁 Gerçek Kesim (Şeffaf)"),
            (PreviewMode.GREENSCREEN, "🟩 Yeşil Perde"),
            (PreviewMode.DEPTH_TEXT_DEMO, "✨ 3D Arkadaki Yazı"),
        ]
        for idx, (m_enum, label) in enumerate(modes):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if idx == 0:
                btn.setChecked(True)
            btn.clicked.connect(lambda _checked, m=m_enum: self.preview_mode_selected.emit(m))
            self._btn_group.addButton(btn)
            self._mode_buttons[m_enum] = btn
            mode_bar.addWidget(btn)

        mode_bar.addStretch(1)
        self._apply_pill_styles()
        root.addLayout(mode_bar)

        # Sol ve Sağ Önizleme Panelleri
        screens_layout = QHBoxLayout()
        screens_layout.setSpacing(12)

        self._left_box, self._left_header, self._left_img = self._create_panel(
            "ORİJİNAL VİDEO KARESİ (Videoyu Buraya Sürükleyebilirsiniz)",
            "🎬 Videoyu doğrudan bu kareye sürükleyip bırakın\nveya üstten Dosya Seç'e tıklayın",
        )
        self._right_box, self._right_header, self._right_img = self._create_panel(
            "SAĞ ÖNİZLEME: ÇIKTI FORMATINA GÖRE OTOMATİK",
            "Maske / Gerçek Çıktı / 3D Yazı önizlemesi burada görünecek",
        )

        screens_layout.addWidget(self._left_box, stretch=1)
        screens_layout.addWidget(self._right_box, stretch=1)
        root.addLayout(screens_layout, stretch=1)

        # Timeline Kare Kaydırıcı (Scrubber)
        scrub_row = QHBoxLayout()
        self._scrub_label = QLabel("Kare Önizleme: 0 / 0")
        self._scrub_label.setStyleSheet("color: #9DA5B4; font-weight: 600;")
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setEnabled(False)
        self._slider.valueChanged.connect(self._on_slider_moved)

        scrub_row.addWidget(self._scrub_label)
        scrub_row.addWidget(self._slider, stretch=1)
        root.addLayout(scrub_row)

    def _apply_pill_styles(self) -> None:
        qss = (
            "QPushButton { padding: 5px 12px; font-size: 12px; border-radius: 13px; "
            "background-color: #1D212A; border: 1px solid #303646; color: #B8C0D0; }"
            "QPushButton:checked { background-color: #C89B3C; border-color: #F0C869; "
            "color: #111318; font-weight: 700; }"
            "QPushButton:hover:!checked { border-color: #D5A853; color: #FFFFFF; }"
        )
        for btn in self._mode_buttons.values():
            btn.setStyleSheet(qss)

    def _create_panel(self, title: str, placeholder: str) -> tuple[QWidget, QLabel, QLabel]:
        container = QWidget()
        container.setStyleSheet(
            "background-color: #161920; border: 1px solid #282D3A; border-radius: 8px;"
        )
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(8, 8, 8, 8)

        header = QLabel(title)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #D5A853; font-weight: 700; font-size: 12px; border: none;")

        img_label = QLabel(placeholder)
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_label.setMinimumSize(360, 240)
        img_label.setStyleSheet(
            "color: #788092; font-size: 13px; border: none; background-color: #0E1015; border-radius: 6px;"
        )

        vbox.addWidget(header)
        vbox.addWidget(img_label, stretch=1)
        return container, header, img_label

    def sync_active_mode_badge(self, cfg: MattingConfig) -> None:
        if cfg.preview_mode in self._mode_buttons:
            self._mode_buttons[cfg.preview_mode].blockSignals(True)
            self._mode_buttons[cfg.preview_mode].setChecked(True)
            self._mode_buttons[cfg.preview_mode].blockSignals(False)

        effective = MaskPostProcessor.resolve_effective_preview_mode(cfg)
        base_title = self._MODE_TITLES.get(effective, "SAĞ ÖNİZLEME")
        if cfg.preview_mode == PreviewMode.AUTO_EXPORT:
            self._right_header.setText(f"🔄 {base_title} [Seçilen Çıktı Formatı]")
        else:
            self._right_header.setText(f"👁️ {base_title}")

    def configure_timeline(self, total_frames: int, sample_idx: int = 0) -> None:
        self._slider.blockSignals(True)
        self._slider.setRange(0, max(0, total_frames - 1))
        self._slider.setValue(sample_idx)
        self._slider.setEnabled(total_frames > 1)
        self._scrub_label.setText(f"Kare Önizleme: {sample_idx + 1} / {total_frames}")
        self._slider.blockSignals(False)

    def set_scrub_enabled(self, enabled: bool) -> None:
        self._slider.setEnabled(enabled)

    def _on_slider_moved(self, frame_idx: int) -> None:
        total = self._slider.maximum() + 1
        self._scrub_label.setText(f"Kare Önizleme: {frame_idx + 1} / {total}")
        self.scrub_requested.emit(frame_idx)

    def update_frames(self, orig_bgr: np.ndarray, masked_bgr: np.ndarray) -> None:
        self._set_pixmap(self._left_img, orig_bgr)
        self._set_pixmap(self._right_img, masked_bgr)

    def _set_pixmap(self, label: QLabel, frame_bgr: np.ndarray) -> None:
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(qimg).scaled(
            label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        label.setPixmap(pix)

    # --- Orijinal Video Karesi Üzerine Sürükle-Bırak (Drag & Drop) Desteği ---
    def _highlight_left_drop(self, active: bool) -> None:
        if active:
            self._left_box.setStyleSheet(
                "background-color: #1F2430; border: 2px dashed #E5B95C; border-radius: 8px;"
            )
        else:
            self._left_box.setStyleSheet(
                "background-color: #161920; border: 1px solid #282D3A; border-radius: 8px;"
            )

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if Path(url.toLocalFile()).suffix.lower() in SUPPORTED_EXTS:
                    self._highlight_left_drop(True)
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self._highlight_left_drop(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        self._highlight_left_drop(False)
        for url in event.mimeData().urls():
            local_path = url.toLocalFile()
            if Path(local_path).suffix.lower() in SUPPORTED_EXTS:
                self.video_dropped.emit(local_path)
                event.acceptProposedAction()
                return
