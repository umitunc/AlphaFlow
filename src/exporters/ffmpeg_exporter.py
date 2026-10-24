# -*- coding: utf-8 -*-
"""
Single Responsibility: İşlenen kareleri diskte geçici PNG biriktirmeden
doğrudan FFmpeg stdin borusuna (pipe) aktararak Luma Matte (.mp4),
Apple ProRes 4444 Alpha (.mov), VP9 Alpha (.webm), GreenScreen (.mp4)
veya 3D Karakter Arkası Yazılı (.mp4) üretir.
"""

import subprocess
from typing import Optional
import cv2
import numpy as np
import imageio_ffmpeg
from src.core.contracts import ExportMode, IVideoExporter, MattingConfig
from src.engines.text_compositor import TextDepthCompositor


class FFmpegPipeExporter(IVideoExporter):
    """FFmpeg subprocess pipe tabanlı çoklu format video kodlayıcı."""

    def __init__(self, mode: ExportMode, config: Optional[MattingConfig] = None) -> None:
        self._mode = mode
        self._config = config or MattingConfig(export_mode=mode)
        self._proc: Optional[subprocess.Popen] = None

    @staticmethod
    def build_output_path(source_path: str, output_dir: str, mode: ExportMode) -> str:
        import os

        base = os.path.splitext(os.path.basename(source_path))[0]
        target_dir = output_dir.strip() if output_dir.strip() else os.path.dirname(source_path)
        os.makedirs(target_dir, exist_ok=True)

        suffix_map = {
            ExportMode.LUMA_MATTE_MP4: f"{base}_luma_matte.mp4",
            ExportMode.PRORES_ALPHA_MOV: f"{base}_alpha_prores4444.mov",
            ExportMode.VP9_ALPHA_WEBM: f"{base}_alpha_vp9.webm",
            ExportMode.GREENSCREEN_MP4: f"{base}_greenscreen.mp4",
            ExportMode.DEPTH_TEXT_MP4: f"{base}_3d_text.mp4",
        }
        return os.path.join(target_dir, suffix_map[mode])

    def open(self, output_path: str, width: int, height: int, fps: float, source_audio_path: str) -> None:
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        is_alpha_stream = self._mode in (ExportMode.PRORES_ALPHA_MOV, ExportMode.VP9_ALPHA_WEBM)
        pix_fmt_in = "bgra" if is_alpha_stream else "bgr24"

        cmd = [
            ffmpeg_exe,
            "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-pix_fmt", pix_fmt_in,
            "-s", f"{width}x{height}",
            "-r", f"{fps:.4f}",
            "-i", "-",
            "-i", source_audio_path,
            "-map", "0:v:0",
            "-map", "1:a:0?",
            "-shortest",
        ]

        if self._mode == ExportMode.PRORES_ALPHA_MOV:
            cmd += [
                "-c:v", "prores_ks",
                "-profile:v", "4444",
                "-pix_fmt", "yuva444p10le",
                "-c:a", "aac", "-b:a", "256k",
                output_path,
            ]
        elif self._mode == ExportMode.VP9_ALPHA_WEBM:
            cmd += [
                "-c:v", "libvpx-vp9",
                "-pix_fmt", "yuva420p",
                "-b:v", "0", "-crf", "24",
                "-deadline", "realtime", "-cpu-used", "4",
                "-c:a", "libopus",
                output_path,
            ]
        else:
            # Luma Matte MP4, GreenScreen MP4 veya 3D Text MP4 (H.264)
            cmd += [
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "17",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "256k",
                "-movflags", "+faststart",
                output_path,
            ]

        self._proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def write_frame(self, frame_bgr: np.ndarray, alpha_u8: np.ndarray) -> None:
        if self._proc is None or self._proc.stdin is None:
            return

        if self._mode == ExportMode.LUMA_MATTE_MP4:
            out_bgr = cv2.cvtColor(alpha_u8, cv2.COLOR_GRAY2BGR)
            self._proc.stdin.write(out_bgr.tobytes())
        elif self._mode == ExportMode.GREENSCREEN_MP4:
            a_norm = (alpha_u8.astype(np.float32) / 255.0)[..., None]
            green = np.zeros_like(frame_bgr)
            green[:, :] = (0, 215, 0)
            comp = (frame_bgr * a_norm + green * (1.0 - a_norm)).astype(np.uint8)
            self._proc.stdin.write(comp.tobytes())
        elif self._mode == ExportMode.DEPTH_TEXT_MP4:
            comp = TextDepthCompositor.render_behind_subject(frame_bgr, alpha_u8, self._config)
            self._proc.stdin.write(comp.tobytes())
        else:
            # BGRA (Gerçek Şeffaf Alpha Kanalı)
            bgra = np.dstack([frame_bgr, alpha_u8])
            self._proc.stdin.write(bgra.tobytes())

    def close(self) -> None:
        if self._proc is not None:
            if self._proc.stdin:
                self._proc.stdin.close()
            self._proc.wait()
            self._proc = None
