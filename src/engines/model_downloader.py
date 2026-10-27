# -*- coding: utf-8 -*-
"""
Single Responsibility: RVM (İnsan/Portre Video Matting) ve U2NetP (Genel Nesne / Hayvan /
Efekt Salient Foreground) ONNX model dosyalarını kontrol eder ve eksikse otomatik indirir.
"""

import os
import urllib.request
from typing import Callable, Optional

RVM_ONNX_URL = (
    "https://github.com/PeterL1n/RobustVideoMatting/releases/download/"
    "v1.0.0/rvm_mobilenetv3_fp32.onnx"
)

U2NETP_ONNX_URL = (
    "https://github.com/danielgatis/rembg/releases/download/"
    "v0.0.0/u2netp.onnx"
)


def _download_if_missing(
    url: str,
    target_path: str,
    min_bytes: int,
    progress_callback: Optional[Callable[[int], None]] = None,
) -> str:
    if os.path.exists(target_path) and os.path.getsize(target_path) > min_bytes:
        return target_path

    tmp_path = target_path + ".part"

    def _reporthook(block_num: int, block_size: int, total_size: int) -> None:
        if progress_callback and total_size > 0:
            pct = int(min(100, (block_num * block_size * 100) // total_size))
            progress_callback(pct)

    urllib.request.urlretrieve(url, tmp_path, reporthook=_reporthook)
    if os.path.exists(target_path):
        os.remove(target_path)
    os.replace(tmp_path, target_path)
    return target_path


def ensure_rvm_model(
    models_dir: str,
    progress_callback: Optional[Callable[[int], None]] = None,
) -> str:
    """RVM ve U2NetP (Genel Nesne) ONNX modellerinin hazır olmasını sağlar."""
    os.makedirs(models_dir, exist_ok=True)
    rvm_path = os.path.join(models_dir, "rvm_mobilenetv3_fp32.onnx")
    u2netp_path = os.path.join(models_dir, "u2netp.onnx")

    _download_if_missing(RVM_ONNX_URL, rvm_path, 5_000_000, progress_callback)
    _download_if_missing(U2NETP_ONNX_URL, u2netp_path, 2_000_000, progress_callback)
    return rvm_path
