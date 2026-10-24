# -*- coding: utf-8 -*-
"""
Single Responsibility: Alpha kenar yumuşatma (Feather/Choke), çıktı formatı,
önizleme modu, 3D Karakter Arkası Yazı özelleştirme (metin, boyut, konum, renk),
kayıt dizini ve Dönüştür / İptal kontrollerini barındıran alt panel.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)
from src.core.contracts import ExportMode, MattingConfig, PreviewMode


class ControlPanelWidget(QWidget):
    """Kullanıcı parametrelerini MattingConfig olarak üreten ve aksiyon sinyalleri yayan panel."""

    config_changed = Signal()
    convert_clicked = Signal()
    cancel_clicked = Signal()
    play_output_clicked = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._text_color_hex = "#F0C05A"
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        # GRUP 1: Maske, Çıktı Formatı ve Görünüm Ayarları
        settings_group = QGroupBox("1. ALPHA MASKE & ÇIKTI FORMATI AYARLARI")
        grid = QGridLayout(settings_group)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(8)

        grid.addWidget(QLabel("Çıktı Formatı:"), 0, 0)
        self._export_combo = QComboBox()
        self._export_combo.addItem(
            "⬛ Luma Matte MP4 (Siyah/Beyaz Maske — Premiere V4 Track Matte İçin)",
            ExportMode.LUMA_MATTE_MP4,
        )
        self._export_combo.addItem(
            "🏁 Apple ProRes 4444 MOV (Gerçek Şeffaf RGBA Kesim — Efektsiz Kullanım)",
            ExportMode.PRORES_ALPHA_MOV,
        )
        self._export_combo.addItem(
            "🏁 WebM VP9 Alpha (Hafif Gerçek Şeffaf Kesim — Web & OBS)",
            ExportMode.VP9_ALPHA_WEBM,
        )
        self._export_combo.addItem(
            "🟩 Green Screen MP4 (Chroma Key Yeşil Perde Çıktısı)",
            ExportMode.GREENSCREEN_MP4,
        )
        self._export_combo.addItem(
            "✨ 3D Karakter Arkası Yazılı MP4 (Yazı Karakterin Arkasına Gömülü Çıktı)",
            ExportMode.DEPTH_TEXT_MP4,
        )
        self._export_combo.currentIndexChanged.connect(self._on_export_format_changed)
        grid.addWidget(self._export_combo, 0, 1)

        grid.addWidget(QLabel("Sağ Önizleme Modu:"), 0, 2)
        self._preview_combo = QComboBox()
        self._preview_combo.addItem("🔄 Seçilen Çıktı Formatına Göre Otomatik Göster", PreviewMode.AUTO_EXPORT)
        self._preview_combo.addItem("⬛ Sadece Maskeyi Göster (Siyah-Beyaz Luma)", PreviewMode.LUMA_MATTE)
        self._preview_combo.addItem("🏁 Gerçek Şeffaf Çıktıyı Göster (RGBA Kesim)", PreviewMode.CHECKERBOARD)
        self._preview_combo.addItem("🟩 Yeşil Perde Çıktısını Göster (Green Screen)", PreviewMode.GREENSCREEN)
        self._preview_combo.addItem("✨ 3D Karakter Arkası Yazıyı Göster (Canlı Test)", PreviewMode.DEPTH_TEXT_DEMO)
        self._preview_combo.currentIndexChanged.connect(self.config_changed.emit)
        grid.addWidget(self._preview_combo, 0, 3)

        # Feather & Choke
        self._feather_lbl = QLabel("Kenar Yumuşatma (Feather): 3 px")
        grid.addWidget(self._feather_lbl, 1, 0)
        self._feather_slider = QSlider(Qt.Orientation.Horizontal)
        self._feather_slider.setRange(0, 15)
        self._feather_slider.setValue(3)
        self._feather_slider.valueChanged.connect(self._on_mask_slider_change)
        grid.addWidget(self._feather_slider, 1, 1)

        self._choke_lbl = QLabel("Kenar Daralt / Genişlet (Choke): 0 px")
        grid.addWidget(self._choke_lbl, 1, 2)
        self._choke_slider = QSlider(Qt.Orientation.Horizontal)
        self._choke_slider.setRange(-8, 8)
        self._choke_slider.setValue(0)
        self._choke_slider.valueChanged.connect(self._on_mask_slider_change)
        grid.addWidget(self._choke_slider, 1, 3)

        root.addWidget(settings_group)

        # GRUP 2: Karakter Arkası 3D Yazı (Depth Typography) Özelleştirme
        text_group = QGroupBox("2. KARAKTER ARKASI 3D YAZI (DEPTH TYPOGRAPHY) & KAYIT DİZİNİ")
        tgrid = QGridLayout(text_group)
        tgrid.setHorizontalSpacing(14)
        tgrid.setVerticalSpacing(8)

        tgrid.addWidget(QLabel("Arkadaki Yazı:"), 0, 0)
        self._text_edit = QLineEdit("VAZGEÇTİN ACİZSİN")
        self._text_edit.setPlaceholderText("Karakterin arkasına gelecek metni yazın...")
        self._text_edit.textChanged.connect(self._on_text_custom_changed)
        tgrid.addWidget(self._text_edit, 0, 1)

        self._size_lbl = QLabel("Yazı Boyutu: %100")
        tgrid.addWidget(self._size_lbl, 0, 2)
        size_color_row = QHBoxLayout()
        self._size_slider = QSlider(Qt.Orientation.Horizontal)
        self._size_slider.setRange(40, 220)
        self._size_slider.setValue(100)
        self._size_slider.valueChanged.connect(self._on_text_custom_changed)

        self._color_btn = QPushButton("🎨 Yazı Rengi")
        self._color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._color_btn.clicked.connect(self._pick_text_color)
        self._update_color_btn_style()

        size_color_row.addWidget(self._size_slider, stretch=1)
        size_color_row.addWidget(self._color_btn)
        tgrid.addLayout(size_color_row, 0, 3)

        self._ypos_lbl = QLabel("Dikey Hiza (Baş/Omuz): %40")
        tgrid.addWidget(self._ypos_lbl, 1, 0)
        self._ypos_slider = QSlider(Qt.Orientation.Horizontal)
        self._ypos_slider.setRange(10, 90)
        self._ypos_slider.setValue(40)
        self._ypos_slider.valueChanged.connect(self._on_text_custom_changed)
        tgrid.addWidget(self._ypos_slider, 1, 1)

        tgrid.addWidget(QLabel("Kayıt Dizini:"), 1, 2)
        dir_row = QHBoxLayout()
        self._dir_edit = QLineEdit()
        self._dir_edit.setPlaceholderText("Varsayılan: Kaynak videonun klasörü")
        self._dir_btn = QPushButton("Klasör Seç...")
        self._dir_btn.clicked.connect(self._select_output_dir)
        dir_row.addWidget(self._dir_edit, stretch=1)
        dir_row.addWidget(self._dir_btn)
        tgrid.addLayout(dir_row, 1, 3)

        root.addWidget(text_group)

        # İlerleme Çubuğu ve Aksiyon Butonları
        bottom_row = QHBoxLayout()
        self._progress = QProgressBar()
        self._progress.setValue(0)
        self._progress.setFormat("Hazır — Videoyu sol kareye veya üst bara sürükleyin")

        self._cancel_btn = QPushButton("İptal Et")
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.clicked.connect(self.cancel_clicked.emit)

        self._play_last_btn = QPushButton("▶️ Çıktıyı Oynat (ProRes/MOV/MP4)")
        self._play_last_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._play_last_btn.setEnabled(False)
        self._play_last_btn.clicked.connect(self.play_output_clicked.emit)

        self._convert_btn = QPushButton("⚡  SEÇİLEN FORMATTA DÖNÜŞTÜR & KAYDET")
        self._convert_btn.setObjectName("PrimaryConvertBtn")
        self._convert_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._convert_btn.setEnabled(False)
        self._convert_btn.clicked.connect(self.convert_clicked.emit)

        bottom_row.addWidget(self._progress, stretch=1)
        bottom_row.addWidget(self._cancel_btn)
        bottom_row.addWidget(self._play_last_btn)
        bottom_row.addWidget(self._convert_btn)
        root.addLayout(bottom_row)

    def _on_export_format_changed(self) -> None:
        # Çıktı formatı değiştiğinde sağ önizlemeyi otomatik olarak o çıktı formatına senkronize et
        self.set_preview_mode(PreviewMode.AUTO_EXPORT, emit_signal=False)
        self.config_changed.emit()

    def _on_mask_slider_change(self) -> None:
        self._feather_lbl.setText(f"Kenar Yumuşatma (Feather): {self._feather_slider.value()} px")
        self._choke_lbl.setText(f"Kenar Daralt / Genişlet (Choke): {self._choke_slider.value()} px")
        self.config_changed.emit()

    def _on_text_custom_changed(self) -> None:
        self._size_lbl.setText(f"Yazı Boyutu: %{self._size_slider.value()}")
        self._ypos_lbl.setText(f"Dikey Hiza (Baş/Omuz): %{self._ypos_slider.value()}")
        # Kullanıcı yazıyı düzenlediğinde önizlemede hemen 3D yazıyı görebilmesi için 3D Yazı moduna geçir
        if self._export_combo.currentData() != ExportMode.DEPTH_TEXT_MP4:
            self.set_preview_mode(PreviewMode.DEPTH_TEXT_DEMO, emit_signal=False)
        self.config_changed.emit()

    def _pick_text_color(self) -> None:
        col = QColorDialog.getColor(QColor(self._text_color_hex), self, "Arkadaki 3D Yazı Rengini Seçin")
        if col.isValid():
            self._text_color_hex = col.name()
            self._update_color_btn_style()
            self._on_text_custom_changed()

    def _update_color_btn_style(self) -> None:
        self._color_btn.setStyleSheet(
            f"background-color: {self._text_color_hex}; color: #111318; font-weight: 700; border-radius: 5px;"
        )

    def set_preview_mode(self, mode: PreviewMode, emit_signal: bool = True) -> None:
        idx = self._preview_combo.findData(mode)
        if idx >= 0:
            self._preview_combo.blockSignals(not emit_signal)
            self._preview_combo.setCurrentIndex(idx)
            self._preview_combo.blockSignals(False)

    def _select_output_dir(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Çıktı Klasörünü Seçin")
        if folder:
            self._dir_edit.setText(folder)
            self.config_changed.emit()

    def set_output_dir_default(self, folder_path: str) -> None:
        if not self._dir_edit.text().strip():
            self._dir_edit.setText(folder_path)

    def build_config(self) -> MattingConfig:
        return MattingConfig(
            export_mode=self._export_combo.currentData(),
            preview_mode=self._preview_combo.currentData(),
            feather_px=self._feather_slider.value(),
            choke_px=self._choke_slider.value(),
            backdrop_text=self._text_edit.text(),
            text_y_pct=self._ypos_slider.value(),
            text_scale_pct=self._size_slider.value(),
            text_color_hex=self._text_color_hex,
            output_dir=self._dir_edit.text().strip(),
        )

    def set_ready_state(self, ready: bool) -> None:
        self._convert_btn.setEnabled(ready)
        self._cancel_btn.setEnabled(False)

    def set_running_state(self, running: bool) -> None:
        self._convert_btn.setEnabled(not running)
        self._cancel_btn.setEnabled(running)
        self._export_combo.setEnabled(not running)

    def update_progress(self, pct: int, status_text: str) -> None:
        self._progress.setValue(pct)
        self._progress.setFormat(status_text)

    def set_playable_output(self, enabled: bool) -> None:
        self._play_last_btn.setEnabled(enabled)
