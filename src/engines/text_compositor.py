# -*- coding: utf-8 -*-
"""
Single Responsibility: Karakterin arkasına Türkçe karakter destekli (UTF-8),
gölgeli, boyutu/konumu/rengi özelleştirilebilir 3D Depth Typography (Sandviç Katmanı) işler.
"""

import os
import cv2
import numpy as np
from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageFont
from src.core.contracts import MattingConfig
from src.core.platform_utils import get_platform_font_candidates


class TextDepthCompositor:
    """Video karesi ile karakter alpha maskesi arasına sinematik metin katmanı yerleştirir."""

    @classmethod
    def _load_font(cls, pixel_size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        for path in get_platform_font_candidates():
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size=max(14, pixel_size))
                except Exception:
                    continue
        return ImageFont.load_default()

    @classmethod
    def render_behind_subject(
        cls,
        frame_bgr: np.ndarray,
        alpha_u8: np.ndarray,
        cfg: MattingConfig,
    ) -> np.ndarray:
        """
        1. Arka plan (frame_bgr) üzerine seçilen metni gölgeli olarak çizer.
        2. Karakteri (alpha_u8 maskesiyle) metnin ÜSTÜNE bindirir (Yazı karakterin arkasında kalır).
        """
        text = cfg.backdrop_text.strip()
        if not text:
            return frame_bgr.copy()

        h, w = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        base_img = Image.fromarray(rgb).convert("RGBA")

        base_font_px = int((w / 13.5) * (cfg.text_scale_pct / 100.0))
        font = cls._load_font(base_font_px)

        txt_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(txt_layer)

        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = (w - tw) // 2
        ty = int((h - th) * (np.clip(cfg.text_y_pct, 5, 95) / 100.0))

        # Yumuşak sinematik arka gölge (Drop Shadow)
        shadow_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        s_draw = ImageDraw.Draw(shadow_layer)
        offset = max(3, base_font_px // 18)
        s_draw.text((tx + offset, ty + offset), text, font=font, fill=(0, 0, 0, 210))
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=max(3, base_font_px // 16)))

        # Ana metin rengi
        try:
            rgb_color = ImageColor.getrgb(cfg.text_color_hex)
        except Exception:
            rgb_color = (240, 192, 90)

        draw.text((tx, ty), text, font=font, fill=(*rgb_color, 240))

        # Arka plan + Gölge + Metin birleşimi
        bg_with_text = Image.alpha_composite(base_img, shadow_layer)
        bg_with_text = Image.alpha_composite(bg_with_text, txt_layer)
        bg_with_text_bgr = cv2.cvtColor(np.array(bg_with_text.convert("RGB")), cv2.COLOR_RGB2BGR)

        # Sandviç Birleştirme: Karakter (Ön Plan) > Yazılı Arka Plan
        a_norm = (alpha_u8.astype(np.float32) / 255.0)[..., None]
        composite = (frame_bgr.astype(np.float32) * a_norm + bg_with_text_bgr.astype(np.float32) * (1.0 - a_norm))
        return np.clip(composite, 0, 255).astype(np.uint8)
