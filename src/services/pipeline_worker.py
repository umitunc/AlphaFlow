# -*- coding: utf-8 -*-
"""
Single Responsibility: Video okuma, AI Alpha çıkarımı, MaskPostProcessor
ve FFmpegPipeExporter adımlarını QThread üzerinde asenkron yöneten orkestratör.
"""

import time
import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal
from src.core.contracts import IMattingEngine, MattingConfig
from src.engines.mask_postprocessor import MaskPostProcessor
from src.exporters.ffmpeg_exporter import FFmpegPipeExporter


class VideoMattingWorker(QThread):
    """Arka planda videoyu kare kare işleyip UI'a sinyal gönderen QThread sınıfı."""

    progress_changed = Signal(int, str)                 # (yüzde, durum_metni)
    preview_ready = Signal(np.ndarray, np.ndarray)      # (orijinal_bgr, onizleme_bgr)
    conversion_finished = Signal(str)                   # (cikti_dosya_yolu)
    conversion_failed = Signal(str)                     # (hata_mesaji)

    def __init__(
        self,
        video_path: str,
        engine: IMattingEngine,
        config: MattingConfig,
    ) -> None:
        super().__init__()
        self._video_path = video_path
        self._engine = engine
        self._config = config
        self._post = MaskPostProcessor()
        self._cancel_requested = False

    def request_cancel(self) -> None:
        self._cancel_requested = True

    def run(self) -> None:
        cap = cv2.VideoCapture(self._video_path)
        if not cap.isOpened():
            self.conversion_failed.emit("Video dosyası açılamadı.")
            return

        fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
        total_frames = max(1, int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        out_path = FFmpegPipeExporter.build_output_path(
            self._video_path, self._config.output_dir, self._config.export_mode
        )
        exporter = FFmpegPipeExporter(self._config.export_mode, self._config)

        try:
            self._engine.reset_state()
            self._post.reset()
            exporter.open(out_path, width, height, fps, self._video_path)

            t0 = time.perf_counter()
            frame_idx = 0

            while not self._cancel_requested:
                ret, frame_bgr = cap.read()
                if not ret:
                    break

                raw_alpha = self._engine.extract_alpha(frame_bgr, self._config.downsample_ratio)
                clean_alpha = self._post.refine(raw_alpha, self._config)
                exporter.write_frame(frame_bgr, clean_alpha)

                frame_idx += 1
                # Her 3 karede bir canlı önizleme ve ilerleme güncelle
                if frame_idx % 3 == 0 or frame_idx == total_frames:
                    elapsed = max(0.001, time.perf_counter() - t0)
                    cur_fps = frame_idx / elapsed
                    pct = int(min(100, (frame_idx * 100) // total_frames))
                    eta_sec = max(0.0, (total_frames - frame_idx) / max(0.1, cur_fps))
                    status = f"İşleniyor: Kare {frame_idx}/{total_frames}  |  {cur_fps:.1f} FPS  |  Kalan: {eta_sec:.1f} sn"
                    self.progress_changed.emit(pct, status)

                    prev_bgr = self._post.build_preview(frame_bgr, clean_alpha, self._config)
                    self.preview_ready.emit(frame_bgr, prev_bgr)

            exporter.close()
            cap.release()

            if self._cancel_requested:
                self.conversion_failed.emit("İşlem kullanıcı tarafından iptal edildi.")
            else:
                self.conversion_finished.emit(out_path)

        except Exception as exc:
            exporter.close()
            cap.release()
            self.conversion_failed.emit(str(exc))
