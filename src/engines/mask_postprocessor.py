# -*- coding: utf-8 -*-
"""
Single Responsibility: Ham Alpha maskesi üzerinde morfolojik iyileştirme
(Choke/Spread, Feather, Threshold, Temporal EMA) ve önizleme kompozisyonu yapar.
"""

from typing import Optional
import cv2
import numpy as np
from src.core.contracts import ExportMode, MattingConfig, PreviewMode
from src.engines.text_compositor import TextDepthCompositor


class MaskPostProcessor:
    """Alpha maskesini sinematik kalitede yumuşatan ve önizleme üreten sınıf."""

    def __init__(self) -> None:
        self._prev_alpha: Optional[np.ndarray] = None
        self._checker_cache: Optional[np.ndarray] = None

    def reset(self) -> None:
        self._prev_alpha = None

    def refine(self, raw_alpha: np.ndarray, cfg: MattingConfig) -> np.ndarray:
        """Ham uint8 alpha maskesine eşikleme, daraltma/genişletme, feather ve EMA uygular."""
        alpha = raw_alpha.astype(np.float32)

        # 1. Alt ve üst eşik (Contrast / Clean Matte)
        lo = float(min(cfg.threshold_low, cfg.threshold_high - 1))
        hi = float(max(cfg.threshold_high, lo + 1))
        alpha = np.clip((alpha - lo) * (255.0 / (hi - lo)), 0.0, 255.0).astype(np.uint8)

        # 2. Choke (-) / Spread (+) morfolojik işlem
        if cfg.choke_px != 0:
            r = abs(int(cfg.choke_px))
            ksize = 2 * r + 1
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
            if cfg.choke_px < 0:
                alpha = cv2.erode(alpha, kernel, iterations=1)
            else:
                alpha = cv2.dilate(alpha, kernel, iterations=1)

        # 3. Kenar yumuşatma (Feather / Gaussian Blur)
        if cfg.feather_px > 0:
            k = int(cfg.feather_px) * 2 + 1
            alpha = cv2.GaussianBlur(alpha, (k, k), 0)

        # 4. Kareler arası zamansal EMA yumuşatma (Flicker önleyici)
        if cfg.temporal_smooth > 0.01 and self._prev_alpha is not None and self._prev_alpha.shape == alpha.shape:
            w = float(np.clip(cfg.temporal_smooth, 0.0, 0.75))
            alpha = cv2.addWeighted(alpha, 1.0 - w, self._prev_alpha, w, 0)

        self._prev_alpha = alpha.copy()
        return alpha

    @staticmethod
    def resolve_effective_preview_mode(cfg: MattingConfig) -> PreviewMode:
        """AUTO_EXPORT seçiliyse, seçilen çıktı formatının gerçek karşılığını döner."""
        if cfg.preview_mode != PreviewMode.AUTO_EXPORT:
            return cfg.preview_mode

        mapping = {
            ExportMode.LUMA_MATTE_MP4: PreviewMode.LUMA_MATTE,
            ExportMode.PRORES_ALPHA_MOV: PreviewMode.CHECKERBOARD,
            ExportMode.VP9_ALPHA_WEBM: PreviewMode.CHECKERBOARD,
            ExportMode.GREENSCREEN_MP4: PreviewMode.GREENSCREEN,
            ExportMode.DEPTH_TEXT_MP4: PreviewMode.DEPTH_TEXT_DEMO,
        }
        return mapping.get(cfg.export_mode, PreviewMode.CHECKERBOARD)

    def build_preview(
        self,
        frame_bgr: np.ndarray,
        alpha_u8: np.ndarray,
        cfg_or_mode: MattingConfig | PreviewMode,
    ) -> np.ndarray:
        """Seçilen önizleme veya çıktı moduna göre BGR önizleme görüntüsü üretir."""
        if isinstance(cfg_or_mode, MattingConfig):
            cfg = cfg_or_mode
            mode = self.resolve_effective_preview_mode(cfg)
        else:
            cfg = MattingConfig(preview_mode=cfg_or_mode)
            mode = cfg_or_mode

        h, w = alpha_u8.shape[:2]
        if mode == PreviewMode.LUMA_MATTE:
            return cv2.cvtColor(alpha_u8, cv2.COLOR_GRAY2BGR)

        if mode == PreviewMode.DEPTH_TEXT_DEMO:
            return TextDepthCompositor.render_behind_subject(frame_bgr, alpha_u8, cfg)

        a_norm = (alpha_u8.astype(np.float32) / 255.0)[..., None]

        if mode == PreviewMode.GREENSCREEN:
            green_bg = np.zeros_like(frame_bgr)
            green_bg[:, :] = (0, 215, 0)
            return (frame_bgr * a_norm + green_bg * (1.0 - a_norm)).astype(np.uint8)

        # Varsayılan: Damalı (Checkerboard) Gerçek Şeffaf Kesim Önizlemesi
        checker = self._get_checkerboard(h, w)
        return (frame_bgr * a_norm + checker * (1.0 - a_norm)).astype(np.uint8)

    def _get_checkerboard(self, h: int, w: int, tile: int = 20) -> np.ndarray:
        if self._checker_cache is None or self._checker_cache.shape[:2] != (h, w):
            yy, xx = np.indices((h, w))
            grid = ((yy // tile) + (xx // tile)) % 2
            c = np.where(grid[..., None] == 0, 52, 84).astype(np.uint8)
            self._checker_cache = np.repeat(c, 3, axis=2)
        return self._checker_cache
