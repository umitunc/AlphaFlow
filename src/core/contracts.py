# -*- coding: utf-8 -*-
"""
SOLID Contracts & Domain Value Objects (DIP / ISP / LSP).
Hiçbir somut kütüphaneye (OpenCV, PySide6, ONNX) bağımlı olmayan saf kontrat katmanı.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import numpy as np


class ExportMode(str, Enum):
    """Desteklenen çıktı formatları."""
    LUMA_MATTE_MP4 = "luma_mp4"        # Siyah-Beyaz Track Matte (.mp4) - Premiere Pro V4 Kanalı İçin
    PRORES_ALPHA_MOV = "prores_mov"    # Apple ProRes 4444 Gerçek Şeffaf (.mov)
    VP9_ALPHA_WEBM = "vp9_webm"        # WebM VP9 Gerçek Şeffaf (.webm)
    GREENSCREEN_MP4 = "green_mp4"      # Yeşil Perde Chroma Key (.mp4)
    DEPTH_TEXT_MP4 = "depth_text_mp4"  # Karakter Arkası 3D Yazı Gömülü (.mp4)


class PreviewMode(str, Enum):
    """Önizleme ekranında sağ panelin görünüm modu."""
    AUTO_EXPORT = "auto_export"        # Seçilen Çıktı Formatına Göre Otomatik Göster
    LUMA_MATTE = "luma"                # Sadece Siyah-Beyaz Alpha Maske
    CHECKERBOARD = "checkerboard"      # Gerçek Şeffaf Kesim (Damalı RGBA)
    GREENSCREEN = "greenscreen"        # Yeşil Perde (Chroma Key)
    DEPTH_TEXT_DEMO = "depth_text"     # Karakter Arkası 3D Yazı Kompozisyonu


@dataclass
class MattingConfig:
    """Kullanıcının arayüzden ayarladığı maskeleme, 3D yazı ve çıktı parametreleri."""
    export_mode: ExportMode = ExportMode.LUMA_MATTE_MP4
    preview_mode: PreviewMode = PreviewMode.AUTO_EXPORT
    downsample_ratio: float = 0.35     # RVM iç çözünürlük oranı (0.25 - 0.50 arası hız/kalite dengesi)
    feather_px: int = 3                # Kenar yumuşatma (Gaussian yarıçapı)
    choke_px: int = 0                  # Kenar daraltma (-) veya genişletme (+)
    threshold_low: int = 12            # Gürültü alt eşiği (0-255)
    threshold_high: int = 242          # Tam opak üst eşik (0-255)
    temporal_smooth: float = 0.20      # Kareler arası EMA titreşim sönümleme (0.0 - 0.7)
    backdrop_text: str = "VAZGEÇTİN ACİZSİN"  # Karakterin arkasına yerleştirilecek 3D yazı
    text_y_pct: int = 40               # Yazının dikey konumu (%10 üst - %90 alt)
    text_scale_pct: int = 100          # Yazı boyutu ölçeği (%40 - %220)
    text_color_hex: str = "#F0C05A"    # Yazı rengi (Kehribar / Altın varsayılan)
    output_dir: str = ""               # Boş ise kaynak videonun klasörü kullanılır


class IMattingEngine(ABC):
    """
    Tüm AI video maskeleme motorlarının uyması gereken soyut arayüz (LSP & DIP).
    """

    @abstractmethod
    def reset_state(self) -> None:
        """Yeni bir videoya geçildiğinde zamansal hafızayı (RNN/GRU state) sıfırlar."""

    @abstractmethod
    def extract_alpha(self, frame_bgr: np.ndarray, downsample_ratio: float = 0.35) -> np.ndarray:
        """
        BGR formatındaki tek bir video karesinden [H, W] boyutunda
        uint8 (0..255) ham Alpha maskesi üretir.
        """


class IVideoExporter(ABC):
    """Video karelerini ve alpha kanalını hedef dosyaya yazan soyut arayüz."""

    @abstractmethod
    def open(self, output_path: str, width: int, height: int, fps: float, source_audio_path: str) -> None:
        """Kodlayıcı borusunu (pipe) başlatır."""

    @abstractmethod
    def write_frame(self, frame_bgr: np.ndarray, alpha_u8: np.ndarray) -> None:
        """Tek bir kareyi ve alpha maskesini kodlayıcıya yazar."""

    @abstractmethod
    def close(self) -> None:
        """Kodlayıcıyı kapatır ve dosyayı tamamlar."""
