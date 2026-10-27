# -*- coding: utf-8 -*-
"""
Single Responsibility: Ham Alpha maskesi üzerinde Tolerans (Hassasiyet),
bağlı bileşen (Connected Component) gürültü temizliği, iç boşluk doldurma,
morfolojik iyileştirme (Choke/Spread, Feather, Temporal EMA) ve önizleme kompozisyonu yapar.
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
        """
        Ham uint8 alpha maskesine Tolerans (Hassasiyet), bağlı bileşen filtreleme,
        daraltma/genişletme (Choke), kenar yumuşatma (Feather) ve zamansal EMA uygular.
        """
        alpha = raw_alpha.astype(np.float32)

        # 1. Tolerans / Hassasiyet (%1 - %100, varsayılan %50) tabanlı dinamik eşikleme ve gama
        t = float(np.clip(cfg.tolerance_pct, 1, 100)) / 100.0
        lo = 195.0 * ((1.0 - t) ** 1.35) + 3.0
        hi = max(lo + 16.0, 232.0 - 165.0 * t)
        norm_a = np.clip((alpha - lo) / (hi - lo), 0.0, 1.0)
        gamma = float(np.clip(1.45 - 1.02 * t, 0.35, 1.55))
        alpha_u8 = (np.power(norm_a, gamma) * 255.0).astype(np.uint8)

        # 2. Toleransa duyarlı bağlı bileşen (Connected Component) gürültü temizliği
        # Düşük/orta toleransta kopuk küçük arka plan parlamalarını bastırır,
        # yüksek toleransta (%75+) sahnedeki ikincil nesneleri korur.
        if t < 0.78:
            bin_m = (alpha_u8 > 32).astype(np.uint8)
            num_l, labels, stats, _ = cv2.connectedComponentsWithStats(bin_m)
            if num_l > 2:
                areas = stats[1:, cv2.CC_STAT_AREA]
                max_area = int(areas.max())
                min_ratio = 0.12 * ((0.80 - t) ** 1.4)
                keep = np.zeros_like(alpha_u8, dtype=np.float32)
                for idx in range(1, num_l):
                    if stats[idx, cv2.CC_STAT_AREA] >= max_area * min_ratio:
                        keep[labels == idx] = 1.0
                keep_soft = cv2.GaussianBlur(keep, (21, 21), 0)
                alpha_u8 = (alpha_u8.astype(np.float32) * keep_soft).astype(np.uint8)

        # 3. Öznenin iç gövdesindeki mikro boşlukları kapat (Morphological Close)
        if t >= 0.35:
            close_r = max(1, int(round(1.0 + 3.0 * t)))
            k_close = cv2.getStructuringElement(
                cv2.MORPH_ELLIPSE, (2 * close_r + 1, 2 * close_r + 1)
            )
            closed = cv2.morphologyEx(alpha_u8, cv2.MORPH_CLOSE, k_close)
            core_weight = (alpha_u8.astype(np.float32) / 255.0) ** 0.5
            alpha_u8 = np.clip(
                alpha_u8.astype(np.float32) * (1.0 - 0.65 * core_weight)
                + closed.astype(np.float32) * (0.65 * core_weight),
                0,
                255,
            ).astype(np.uint8)

        # 4. Choke (-) / Spread (+) morfolojik işlem
        if cfg.choke_px != 0:
            r = abs(int(cfg.choke_px))
            ksize = 2 * r + 1
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
            if cfg.choke_px < 0:
                alpha_u8 = cv2.erode(alpha_u8, kernel, iterations=1)
            else:
                alpha_u8 = cv2.dilate(alpha_u8, kernel, iterations=1)

        # 5. Kenar yumuşatma (Feather / Gaussian Blur)
        if cfg.feather_px > 0:
            k = int(cfg.feather_px) * 2 + 1
            alpha_u8 = cv2.GaussianBlur(alpha_u8, (k, k), 0)

        # 6. Kareler arası zamansal EMA yumuşatma (Flicker önleyici)
        if (
            cfg.temporal_smooth > 0.01
            and self._prev_alpha is not None
            and self._prev_alpha.shape == alpha_u8.shape
        ):
            w = float(np.clip(cfg.temporal_smooth, 0.0, 0.75))
            alpha_u8 = cv2.addWeighted(alpha_u8, 1.0 - w, self._prev_alpha, w, 0)

        self._prev_alpha = alpha_u8.copy()
        return alpha_u8

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
