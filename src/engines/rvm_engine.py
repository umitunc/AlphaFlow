# -*- coding: utf-8 -*-
"""
Single Responsibility: Robust Video Matting (RVM) ONNX çıkarım motoru.
ConvGRU zamansal hafıza durumlarını (r1, r2, r3, r4) koruyarak kareler arası
titreme (flicker) olmadan yüksek hızlı video alpha maskesi üretir.
"""

from pathlib import Path
from typing import List, Optional
import cv2
import numpy as np
from src.core.contracts import IMattingEngine
from src.core.platform_utils import get_preferred_ort_providers
from src.engines.model_downloader import ensure_rvm_model


class RVMOnnxEngine(IMattingEngine):
    """ONNX Runtime tabanlı Robust Video Matting motoru."""

    def __init__(self, model_path: Optional[str] = None) -> None:
        import onnxruntime as ort

        if not model_path:
            default_models_dir = str(Path(__file__).resolve().parents[2] / "models")
            model_path = ensure_rvm_model(default_models_dir)

        active_providers = get_preferred_ort_providers()

        sess_opts = ort.SessionOptions()
        sess_opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self._session = ort.InferenceSession(model_path, sess_options=sess_opts, providers=active_providers)
        self._rec: List[np.ndarray] = [np.zeros((1, 1, 1, 1), dtype=np.float32) for _ in range(4)]

    def reset_state(self) -> None:
        """Yeni video başladığında ConvGRU hafıza durumlarını sıfırlar."""
        self._rec = [np.zeros((1, 1, 1, 1), dtype=np.float32) for _ in range(4)]

    def extract_alpha(self, frame_bgr: np.ndarray, downsample_ratio: float = 0.35) -> np.ndarray:
        """
        Tek bir BGR kareden [H, W] uint8 (0..255) Alpha maskesi döner.
        """
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        src = rgb.astype(np.float32) / 255.0
        # [1, 3, H, W]
        src_tensor = np.transpose(src, (2, 0, 1))[None, ...]
        ds = np.array([downsample_ratio], dtype=np.float32)

        outputs = self._session.run(
            None,
            {
                "src": src_tensor,
                "r1i": self._rec[0],
                "r2i": self._rec[1],
                "r3i": self._rec[2],
                "r4i": self._rec[3],
                "downsample_ratio": ds,
            },
        )
        # outputs: fgr, pha, r1o, r2o, r3o, r4o
        pha = outputs[1][0, 0]
        self._rec = outputs[2:6]
        alpha_u8 = np.clip(pha * 255.0, 0, 255).astype(np.uint8)
        return alpha_u8
