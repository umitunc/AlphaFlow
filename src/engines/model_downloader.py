# -*- coding: utf-8 -*-
"""
Single Responsibility: RVM (Robust Video Matting) ONNX model dosyasını
kontrol eder ve yoksa resmi GitHub sürümlerinden otomatik indirir.
"""

import os
import urllib.request
from typing import Callable, Optional

RVM_ONNX_URL = (
    "https://github.com/PeterL1n/RobustVideoMatting/releases/download/"
    "v1.0.0/rvm_mobilenetv3_fp32.onnx"
)


def ensure_rvm_model(
    models_dir: str,
    progress_callback: Optional[Callable[[int], None]] = None,
) -> str:
    """
    Model dosyasının yerel yolunu döner; dosya mevcut değilse indirir.
    """
    os.makedirs(models_dir, exist_ok=True)
    model_path = os.path.join(models_dir, "rvm_mobilenetv3_fp32.onnx")
    if os.path.exists(model_path) and os.path.getsize(model_path) > 5_000_000:
        return model_path

    tmp_path = model_path + ".part"

    def _reporthook(block_num: int, block_size: int, total_size: int) -> None:
        if progress_callback and total_size > 0:
            pct = int(min(100, (block_num * block_size * 100) // total_size))
            progress_callback(pct)

    urllib.request.urlretrieve(RVM_ONNX_URL, tmp_path, reporthook=_reporthook)
    if os.path.exists(model_path):
        os.remove(model_path)
    os.replace(tmp_path, model_path)
    return model_path
