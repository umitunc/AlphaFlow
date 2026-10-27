# -*- coding: utf-8 -*-
"""
Single Responsibility: Hibrit AI Video Foreground Matting Motoru.
1. İnsan / Portre videolarında ConvGRU zamansal hafızalı Robust Video Matting (RVM) çalıştırır.
2. Tüm sahnelerde (insan, origami, heykel, kelebek, hayvan, araç, ürün, VFX vb.) RVM ile birlikte
   çok-ölçekli (multi-scale logit) U2NetP Salient Object Segmentation ve CIE-LAB / Odak (Focus)
   sahne ön plan analizini hibrit olarak birleştirir.
"""

from pathlib import Path
from typing import List, Optional
import cv2
import numpy as np
from src.core.contracts import IMattingEngine
from src.core.platform_utils import get_preferred_ort_providers
from src.engines.model_downloader import ensure_rvm_model


class RVMOnnxEngine(IMattingEngine):
    """RVM + Çok-Ölçekli U2NetP + Sahne Odak/Renk Analizli Hibrit ONNX Çıkarım Motoru."""

    def __init__(self, model_path: Optional[str] = None) -> None:
        import onnxruntime as ort

        default_models_dir = Path(__file__).resolve().parents[2] / "models"
        if not model_path:
            model_path = ensure_rvm_model(str(default_models_dir))
        else:
            ensure_rvm_model(str(Path(model_path).parent))

        u2netp_path = str(Path(model_path).parent / "u2netp.onnx")
        active_providers = get_preferred_ort_providers()

        sess_opts = ort.SessionOptions()
        sess_opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self._session = ort.InferenceSession(
            model_path, sess_options=sess_opts, providers=active_providers
        )
        self._u2_session = (
            ort.InferenceSession(
                u2netp_path, sess_options=sess_opts, providers=active_providers
            )
            if Path(u2netp_path).exists()
            else None
        )
        self._rec: List[np.ndarray] = [
            np.zeros((1, 1, 1, 1), dtype=np.float32) for _ in range(4)
        ]

    def reset_state(self) -> None:
        """Yeni video başladığında ConvGRU hafıza durumlarını sıfırlar."""
        self._rec = [np.zeros((1, 1, 1, 1), dtype=np.float32) for _ in range(4)]

    def _extract_u2net_multiscale(self, rgb_norm: np.ndarray, h: int, w: int) -> np.ndarray:
        """
        U2NetP'nin 6 farklı ölçekteki (d0..d5) yan çıktılarını logit (log-odds) uzayında
        birleştirerek hem tam opak gövdeyi hem de Tolerans sürgüsü için sürekli olasılık
        gradyanını üretir.
        """
        if self._u2_session is None:
            return np.zeros((h, w), dtype=np.float32)

        inp = cv2.resize(rgb_norm, (320, 320), interpolation=cv2.INTER_AREA)
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        inp = (inp - mean) / std
        tensor = np.transpose(inp, (2, 0, 1))[None, ...].astype(np.float32)

        in_name = self._u2_session.get_inputs()[0].name
        outs = self._u2_session.run(None, {in_name: tensor})

        weights = [0.42, 0.22, 0.14, 0.10, 0.07, 0.05]
        logit_sum = np.zeros((320, 320), dtype=np.float32)
        for w_i, out_i in zip(weights, outs[:6]):
            p = np.clip(out_i[0, 0], 1e-5, 1.0 - 1e-5)
            logit_sum += w_i * np.log(p / (1.0 - p))

        # Yumuşatılmış sıcaklık (temperature=2.6) ile ikili (0/1) doygunluğu önle
        u2_soft = 1.0 / (1.0 + np.exp(-logit_sum / 2.6))
        p_min, p_max = float(u2_soft.min()), float(u2_soft.max())
        if p_max - p_min > 1e-5:
            u2_soft = (u2_soft - p_min) / (p_max - p_min)
        else:
            return np.zeros((h, w), dtype=np.float32)

        return cv2.resize(u2_soft, (w, h), interpolation=cv2.INTER_CUBIC)

    def extract_alpha(self, frame_bgr: np.ndarray, downsample_ratio: float = 0.35) -> np.ndarray:
        """
        Tek bir BGR kareden [H, W] uint8 (0..255) hibrit ham Alpha olasılık haritası döner.
        RVM (insan/saç) + Çok-Ölçekli U2NetP (genel nesne/origami/hayvan/VFX) +
        Sahne Renk/Odak (LAB & Sobel) önsel bilgisini her karede birleştirir.
        """
        h, w = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        src = rgb.astype(np.float32) / 255.0
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
        rvm_pha = outputs[1][0, 0]
        self._rec = outputs[2:6]

        # Her karede U2NetP çok-ölçekli genel nesne maskesini çalıştır ve RVM ile birleştir
        u2_pha = self._extract_u2net_multiscale(src, h, w)
        ai_pha = np.maximum(u2_pha, rvm_pha * 0.92)

        # Sahne Odak (Netlik) ve CIE-LAB Arka Plan Renk Farkı Analizi
        sigma = max(10.0, min(h, w) * 0.075)
        ai_halo = np.clip(
            cv2.GaussianBlur(ai_pha, (0, 0), sigmaX=sigma) * 2.4, 0.06, 1.0
        )

        lab = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
        bg_mask = (ai_pha < 0.12).astype(np.float32)
        if bg_mask.mean() < 0.05:
            bg_mask = np.zeros((h, w), dtype=np.float32)
            bg_mask[: max(4, h // 12), :] = 1.0

        k_bg = (45, 45)
        bg_w = cv2.boxFilter(bg_mask, cv2.CV_32F, k_bg) + 1e-5
        bg_lab = np.zeros_like(lab)
        for c in range(3):
            bg_lab[..., c] = (
                cv2.boxFilter(lab[..., c] * bg_mask, cv2.CV_32F, k_bg) / bg_w
            )
        color_diff = np.clip(
            np.linalg.norm(lab - bg_lab, axis=2) / 40.0, 0.0, 1.0
        )

        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        grad = np.hypot(gx, gy)
        grad[:3, :] = 0.0
        grad[-3:, :] = 0.0
        grad[:, :3] = 0.0
        grad[:, -3:] = 0.0
        grad_blur = cv2.GaussianBlur(grad, (15, 15), 0)
        g_max = (
            float(np.percentile(grad_blur, 98))
            if grad_blur.max() > 1e-5
            else 1.0
        )
        focus_sal = np.clip(grad_blur / max(0.05, g_max * 0.72), 0.0, 1.0)

        scene_prior = np.clip(0.55 * color_diff + 0.45 * focus_sal, 0.0, 1.0) * ai_halo
        flat_bg_penalty = np.clip((0.78 - ai_pha) / 0.55, 0.0, 1.0) * (
            1.0 - np.maximum(color_diff, focus_sal)
        )
        combined = np.clip(
            ai_pha * (1.0 - 0.58 * flat_bg_penalty) + 0.28 * scene_prior,
            0.0,
            1.0,
        )

        alpha_u8 = np.clip(combined * 255.0, 0, 255).astype(np.uint8)
        return alpha_u8
