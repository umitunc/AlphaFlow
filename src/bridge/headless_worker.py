# -*- coding: utf-8 -*-
"""
AlphaFlow Studio Pro — Headless JSON-RPC AI & Codec Engine Bridge.
Flutter Masaüstü (Windows & macOS) arayüzü ile RVM ONNX / OpenCV / FFmpeg
çekirdeği arasında yüksek hızlı stdin/stdout JSON protokolü sağlar.
"""

import base64
import importlib
import json
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

# Proje kök dizinini sys.path'e ekle
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import cv2
import numpy as np

from src.core.contracts import ExportMode, MattingConfig, PreviewMode
from src.core.platform_utils import get_system_diagnostics, reveal_in_file_manager
import src.engines.mask_postprocessor as mask_post_mod
import src.engines.rvm_engine as rvm_engine_mod
from src.engines.mask_postprocessor import MaskPostProcessor
from src.engines.model_downloader import ensure_rvm_model
from src.engines.rvm_engine import RVMOnnxEngine
from src.exporters.ffmpeg_exporter import FFmpegPipeExporter


class HeadlessBridgeServer:
    """Flutter uygulaması tarafından alt süreç (subprocess) olarak yönetilen AI motoru."""

    def __init__(self) -> None:
        self._stdout_lock = threading.Lock()
        self._engine: Optional[RVMOnnxEngine] = None
        self._post = MaskPostProcessor()
        self._current_video: str = ""
        self._cached_frame_bgr: Optional[np.ndarray] = None
        self._cached_raw_alpha: Optional[np.ndarray] = None
        self._cached_downsample: float = 0.35
        self._cancel_requested = False
        self._converting = False

        # Dahili oynatıcı (ProRes 4444 / VP9 / MP4) durumu
        self._player_cap: Optional[cv2.VideoCapture] = None
        self._player_path: str = ""
        self._player_lock = threading.Lock()
        self._last_engine_mtime: float = self._get_engine_files_mtime()

    @staticmethod
    def _get_engine_files_mtime() -> float:
        try:
            p1 = ROOT_DIR / "src" / "engines" / "rvm_engine.py"
            p2 = ROOT_DIR / "src" / "engines" / "mask_postprocessor.py"
            return max(p1.stat().st_mtime, p2.stat().st_mtime)
        except Exception:
            return 0.0

    def _reload_if_changed(self) -> bool:
        """Motor dosyaları diskte güncellendiyse sıcak yeniden yükleme (hot-reload) yapar."""
        cur_mtime = self._get_engine_files_mtime()
        if cur_mtime > self._last_engine_mtime:
            self._last_engine_mtime = cur_mtime
            try:
                importlib.reload(rvm_engine_mod)
                importlib.reload(mask_post_mod)
                models_dir = str(ROOT_DIR / "models")
                model_path = ensure_rvm_model(models_dir)
                self._engine = rvm_engine_mod.RVMOnnxEngine(model_path=model_path)
                self._post = mask_post_mod.MaskPostProcessor()
                self._cached_raw_alpha = None
                return True
            except Exception:
                return False
        return False

    def send_event(self, payload: Dict[str, Any]) -> None:
        """Thread-safe JSON satırı çıktısı üretir."""
        line = json.dumps(payload, ensure_ascii=False)
        with self._stdout_lock:
            sys.stdout.write(line + "\n")
            sys.stdout.flush()

    @staticmethod
    def _encode_bgr_b64(frame_bgr: np.ndarray, max_width: int = 960, quality: int = 88) -> str:
        """BGR görüntüyü hızlı UI aktarımı için JPEG base64 dizgesine dönüştürür."""
        h, w = frame_bgr.shape[:2]
        if w > max_width:
            scale = max_width / float(w)
            new_w = max_width
            new_h = max(1, int(h * scale))
            frame_bgr = cv2.resize(frame_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)
        ok, buf = cv2.imencode(".jpg", frame_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        if not ok:
            return ""
        return base64.b64encode(buf.tobytes()).decode("ascii")

    @staticmethod
    def _parse_config(raw: Optional[Dict[str, Any]]) -> MattingConfig:
        if not raw:
            return MattingConfig()
        export_str = raw.get("export_mode", ExportMode.LUMA_MATTE_MP4.value)
        preview_str = raw.get("preview_mode", PreviewMode.AUTO_EXPORT.value)
        try:
            export_mode = ExportMode(export_str)
        except ValueError:
            export_mode = ExportMode.LUMA_MATTE_MP4
        try:
            preview_mode = PreviewMode(preview_str)
        except ValueError:
            preview_mode = PreviewMode.AUTO_EXPORT

        return MattingConfig(
            export_mode=export_mode,
            preview_mode=preview_mode,
            downsample_ratio=float(raw.get("downsample_ratio", 0.35)),
            tolerance_pct=int(raw.get("tolerance_pct", 50)),
            feather_px=int(raw.get("feather_px", 3)),
            choke_px=int(raw.get("choke_px", 0)),
            threshold_low=int(raw.get("threshold_low", 12)),
            threshold_high=int(raw.get("threshold_high", 242)),
            temporal_smooth=float(raw.get("temporal_smooth", 0.20)),
            backdrop_text=str(raw.get("backdrop_text", "SAMPLE TEXT")),
            text_y_pct=int(raw.get("text_y_pct", 40)),
            text_scale_pct=int(raw.get("text_scale_pct", 100)),
            text_color_hex=str(raw.get("text_color_hex", "#F0C05A")),
            output_dir=str(raw.get("output_dir", "")),
        )

    def handle_init(self) -> None:
        try:
            models_dir = str(ROOT_DIR / "models")
            model_path = ensure_rvm_model(
                models_dir,
                progress_callback=lambda pct: self.send_event(
                    {"type": "model_download", "pct": pct}
                ),
            )
            if self._engine is None:
                self._engine = RVMOnnxEngine(model_path=model_path)
            diag = get_system_diagnostics()
            self.send_event(
                {
                    "type": "ready",
                    "os": diag["os"],
                    "python": diag["python"],
                    "accelerator": diag["accelerator"],
                    "ffmpeg": diag["ffmpeg"],
                    "model_path": model_path,
                }
            )
        except Exception as exc:
            self.send_event({"type": "error", "message": f"Motor başlatılamadı: {exc}"})

    def _ensure_engine(self) -> RVMOnnxEngine:
        self._reload_if_changed()
        if self._engine is None:
            models_dir = str(ROOT_DIR / "models")
            model_path = ensure_rvm_model(models_dir)
            self._engine = rvm_engine_mod.RVMOnnxEngine(model_path=model_path)
        return self._engine

    def handle_load_video(self, path: str, raw_cfg: Optional[Dict[str, Any]]) -> None:
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            self.send_event({"type": "error", "message": "Seçilen video dosyası açılamadı!"})
            return

        fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
        frames = max(1, int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        sample_idx = min(frames - 1, max(0, frames // 5))
        cap.set(cv2.CAP_PROP_POS_FRAMES, sample_idx)
        ret, frame_bgr = cap.read()
        cap.release()

        if not ret or frame_bgr is None:
            self.send_event({"type": "error", "message": "Video karesi okunamadı!"})
            return

        self._current_video = path
        cfg = self._parse_config(raw_cfg)
        engine = self._ensure_engine()
        engine.reset_state()
        self._cached_frame_bgr = frame_bgr
        self._cached_downsample = cfg.downsample_ratio
        self._cached_raw_alpha = engine.extract_alpha(frame_bgr, cfg.downsample_ratio)

        self._post.reset()
        clean_alpha = self._post.refine(self._cached_raw_alpha, cfg)
        preview_bgr = self._post.build_preview(frame_bgr, clean_alpha, cfg)

        self.send_event(
            {
                "type": "video_loaded",
                "path": path,
                "name": Path(path).name,
                "parent_dir": str(Path(path).parent),
                "width": w,
                "height": h,
                "fps": round(fps, 2),
                "total_frames": frames,
                "duration_sec": round(frames / max(1.0, fps), 2),
                "sample_idx": sample_idx,
                "orig_b64": self._encode_bgr_b64(frame_bgr),
                "preview_b64": self._encode_bgr_b64(preview_bgr),
            }
        )

    def handle_scrub(self, frame_idx: int, raw_cfg: Optional[Dict[str, Any]]) -> None:
        if not self._current_video or self._converting:
            return
        cap = cv2.VideoCapture(self._current_video)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame_bgr = cap.read()
        cap.release()
        if not ret or frame_bgr is None:
            return

        cfg = self._parse_config(raw_cfg)
        engine = self._ensure_engine()
        engine.reset_state()
        self._cached_frame_bgr = frame_bgr
        self._cached_downsample = cfg.downsample_ratio
        self._cached_raw_alpha = engine.extract_alpha(frame_bgr, cfg.downsample_ratio)

        self._post.reset()
        clean_alpha = self._post.refine(self._cached_raw_alpha, cfg)
        preview_bgr = self._post.build_preview(frame_bgr, clean_alpha, cfg)

        self.send_event(
            {
                "type": "preview_updated",
                "frame_idx": frame_idx,
                "orig_b64": self._encode_bgr_b64(frame_bgr),
                "preview_b64": self._encode_bgr_b64(preview_bgr),
            }
        )

    def handle_update_config(self, raw_cfg: Optional[Dict[str, Any]]) -> None:
        if self._cached_frame_bgr is None or self._converting:
            return
        cfg = self._parse_config(raw_cfg)
        engine = self._ensure_engine()
        if (
            self._cached_raw_alpha is None
            or abs(cfg.downsample_ratio - self._cached_downsample) > 0.005
        ):
            engine.reset_state()
            self._cached_downsample = cfg.downsample_ratio
            self._cached_raw_alpha = engine.extract_alpha(
                self._cached_frame_bgr, cfg.downsample_ratio
            )

        self._post.reset()
        clean_alpha = self._post.refine(self._cached_raw_alpha, cfg)
        preview_bgr = self._post.build_preview(self._cached_frame_bgr, clean_alpha, cfg)

        self.send_event(
            {
                "type": "preview_updated",
                "orig_b64": self._encode_bgr_b64(self._cached_frame_bgr),
                "preview_b64": self._encode_bgr_b64(preview_bgr),
            }
        )

    def handle_convert(self, raw_cfg: Optional[Dict[str, Any]]) -> None:
        if not self._current_video or self._converting:
            return
        cfg = self._parse_config(raw_cfg)
        self._cancel_requested = False
        self._converting = True
        worker_thread = threading.Thread(
            target=self._run_conversion_worker,
            args=(self._current_video, cfg),
            daemon=True,
        )
        worker_thread.start()

    def _run_conversion_worker(self, video_path: str, cfg: MattingConfig) -> None:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            self._converting = False
            self.send_event(
                {"type": "conversion_failed", "error": "Video dosyası açılamadı.", "cancelled": False}
            )
            return

        fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
        total_frames = max(1, int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        out_path = FFmpegPipeExporter.build_output_path(
            video_path, cfg.output_dir, cfg.export_mode
        )
        exporter = FFmpegPipeExporter(cfg.export_mode, cfg)
        post = MaskPostProcessor()
        engine = self._ensure_engine()

        try:
            engine.reset_state()
            post.reset()
            exporter.open(out_path, width, height, fps, video_path)

            t0 = time.perf_counter()
            frame_idx = 0

            while not self._cancel_requested:
                ret, frame_bgr = cap.read()
                if not ret:
                    break

                raw_alpha = engine.extract_alpha(frame_bgr, cfg.downsample_ratio)
                clean_alpha = post.refine(raw_alpha, cfg)
                exporter.write_frame(frame_bgr, clean_alpha)

                frame_idx += 1
                if frame_idx % 3 == 0 or frame_idx == total_frames:
                    elapsed = max(0.001, time.perf_counter() - t0)
                    cur_fps = frame_idx / elapsed
                    pct = int(min(100, (frame_idx * 100) // total_frames))
                    eta_sec = max(0.0, (total_frames - frame_idx) / max(0.1, cur_fps))
                    status = (
                        f"İşleniyor: Kare {frame_idx}/{total_frames}  •  "
                        f"{cur_fps:.1f} FPS  •  Kalan: {eta_sec:.1f} sn"
                    )
                    prev_bgr = post.build_preview(frame_bgr, clean_alpha, cfg)
                    self.send_event(
                        {
                            "type": "progress",
                            "pct": pct,
                            "frame_idx": frame_idx,
                            "total_frames": total_frames,
                            "fps": round(cur_fps, 1),
                            "eta_sec": round(eta_sec, 1),
                            "status": status,
                            "orig_b64": self._encode_bgr_b64(frame_bgr, max_width=760, quality=82),
                            "preview_b64": self._encode_bgr_b64(prev_bgr, max_width=760, quality=82),
                        }
                    )

            exporter.close()
            cap.release()
            self._converting = False

            if self._cancel_requested:
                self.send_event(
                    {
                        "type": "conversion_failed",
                        "error": "İşlem kullanıcı tarafından iptal edildi.",
                        "cancelled": True,
                    }
                )
            else:
                self.send_event(
                    {
                        "type": "conversion_finished",
                        "output_path": out_path,
                        "file_name": Path(out_path).name,
                    }
                )
        except Exception as exc:
            exporter.close()
            cap.release()
            self._converting = False
            self.send_event(
                {"type": "conversion_failed", "error": str(exc), "cancelled": False}
            )

    def handle_player_open(self, path: str) -> None:
        with self._player_lock:
            if self._player_cap is not None:
                self._player_cap.release()
            cap = cv2.VideoCapture(path)
            if not cap.isOpened():
                self.send_event({"type": "error", "message": "Çıktı videosu açılamadı."})
                return
            self._player_cap = cap
            self._player_path = path
            fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
            total_frames = max(1, int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            ret, frame_bgr = cap.read()
            b64 = self._encode_bgr_b64(frame_bgr, max_width=960) if ret and frame_bgr is not None else ""
            self.send_event(
                {
                    "type": "player_opened",
                    "path": path,
                    "name": Path(path).name,
                    "fps": round(fps, 2),
                    "total_frames": total_frames,
                    "width": w,
                    "height": h,
                    "frame_idx": 0,
                    "frame_b64": b64,
                }
            )

    def handle_player_frame(self, frame_idx: Optional[int]) -> None:
        with self._player_lock:
            if self._player_cap is None or not self._player_cap.isOpened():
                return
            if frame_idx is not None:
                self._player_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame_bgr = self._player_cap.read()
            if not ret or frame_bgr is None:
                self._player_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame_bgr = self._player_cap.read()
                if not ret or frame_bgr is None:
                    return
            cur_idx = max(0, int(self._player_cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1)
            self.send_event(
                {
                    "type": "player_frame",
                    "frame_idx": cur_idx,
                    "frame_b64": self._encode_bgr_b64(frame_bgr, max_width=960, quality=85),
                }
            )

    def handle_player_close(self) -> None:
        with self._player_lock:
            if self._player_cap is not None:
                self._player_cap.release()
                self._player_cap = None

    def serve_forever(self) -> None:
        """Stdin üzerinden gelen JSON komutlarını dinler."""
        for raw_line in sys.stdin:
            line = raw_line.lstrip("\ufeff").strip()
            if not line:
                continue
            try:
                req = json.loads(line)
            except Exception as exc:
                self.send_event({"type": "error", "message": f"Geçersiz JSON: {exc}"})
                continue

            cmd = req.get("cmd")
            if cmd == "init":
                self.handle_init()
            elif cmd == "load_video":
                self.handle_load_video(req.get("path", ""), req.get("config"))
            elif cmd == "scrub":
                self.handle_scrub(int(req.get("frame_idx", 0)), req.get("config"))
            elif cmd == "update_config":
                self.handle_update_config(req.get("config"))
            elif cmd == "convert":
                self.handle_convert(req.get("config"))
            elif cmd == "cancel":
                self._cancel_requested = True
            elif cmd == "player_open":
                self.handle_player_open(req.get("path", ""))
            elif cmd == "player_frame":
                idx = req.get("frame_idx")
                self.handle_player_frame(int(idx) if idx is not None else None)
            elif cmd == "player_close":
                self.handle_player_close()
            elif cmd == "reveal":
                reveal_in_file_manager(req.get("path", ""))
            elif cmd == "quit":
                self.handle_player_close()
                break


if __name__ == "__main__":
    # UTF-8 stdin/stdout zorla (Windows Türkçe karakter uyumu için kritik)
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    server = HeadlessBridgeServer()
    server.serve_forever()
