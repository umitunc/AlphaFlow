# -*- coding: utf-8 -*-
"""
Single Responsibility: Alt bileşenleri (DropZone, PreviewCanvas, ControlPanel, StudioVideoPlayerDialog)
ve iş mantığını (IMattingEngine, VideoMattingWorker) birbirine bağlayan çapraz platform (Windows & macOS) ana pencere.
"""

from pathlib import Path
import cv2
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QLabel, QMainWindow, QMessageBox, QVBoxLayout, QWidget
from src.core.contracts import IMattingEngine, PreviewMode
from src.core.platform_utils import get_system_diagnostics, reveal_in_file_manager
from src.engines.mask_postprocessor import MaskPostProcessor
from src.services.pipeline_worker import VideoMattingWorker
from src.ui.control_panel import ControlPanelWidget
from src.ui.drop_zone import DropZoneWidget, SUPPORTED_EXTS
from src.ui.player_dialog import StudioVideoPlayerDialog
from src.ui.preview_canvas import PreviewCanvasWidget
from src.ui.theme import STUDIO_DARK_QSS


class AlphaFlowMainWindow(QMainWindow):
    """SOLID prensiplerine uygun modüler Alpha Video Maskeleme Masaüstü Uygulaması (Windows & macOS)."""

    def __init__(self, engine: IMattingEngine) -> None:
        super().__init__()
        self._engine = engine
        self._post = MaskPostProcessor()
        self._current_video: str = ""
        self._last_output_video: str = ""
        self._cached_frame_bgr = None
        self._cached_raw_alpha = None
        self._worker: VideoMattingWorker | None = None

        self.setAcceptDrops(True)
        self.setWindowTitle("AlphaFlow Studio Pro — AI Video Alpha & 3D Depth Masking (Windows & macOS)")
        self.resize(1260, 840)
        self.setStyleSheet(STUDIO_DARK_QSS)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 12, 16, 10)
        layout.setSpacing(10)

        self._drop_zone = DropZoneWidget()
        self._preview_canvas = PreviewCanvasWidget()
        self._controls = ControlPanelWidget()

        # Sistem & Kodek Durum Çubuğu (Windows & macOS Donanım ve FFmpeg Doğrulaması)
        diag = get_system_diagnostics()
        self._sys_bar = QLabel(
            f"🟢 Sistem Hazır: {diag['os']}   |   AI Hızlandırıcı: {diag['accelerator']}   |   "
            f"Dahili Kodek Motoru: {diag['ffmpeg']} (ProRes 4444 ap4h, VP9 Alpha, H.264 Yüklü)"
        )
        self._sys_bar.setStyleSheet(
            "color: #8E98AA; font-size: 11px; padding: 3px 6px; background-color: #151820; border-radius: 4px;"
        )

        layout.addWidget(self._drop_zone)
        layout.addWidget(self._preview_canvas, stretch=1)
        layout.addWidget(self._controls)
        layout.addWidget(self._sys_bar)

        # Sinyal bağlantıları
        self._drop_zone.video_Dropped.connect(self._on_video_selected)
        self._preview_canvas.video_dropped.connect(self._on_video_selected)
        self._preview_canvas.scrub_requested.connect(self._on_scrub_frame)
        self._preview_canvas.preview_mode_selected.connect(self._on_canvas_mode_pill_clicked)
        self._controls.config_changed.connect(self._refresh_single_frame_preview)
        self._controls.convert_clicked.connect(self._start_conversion)
        self._controls.cancel_clicked.connect(self._cancel_conversion)
        self._controls.play_output_clicked.connect(self._open_builtin_player)

    def _on_canvas_mode_pill_clicked(self, mode: PreviewMode) -> None:
        self._controls.set_preview_mode(mode, emit_signal=True)

    def _on_video_selected(self, video_path: str) -> None:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            QMessageBox.critical(self, "Hata", "Seçilen video dosyası açılamadı!")
            return

        fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
        frames = max(1, int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        self._current_video = video_path
        self._drop_zone.set_loaded_file(video_path, w, h, fps, frames)
        self._controls.set_output_dir_default(str(Path(video_path).parent))

        sample_idx = min(frames - 1, max(0, frames // 5))
        self._preview_canvas.configure_timeline(frames, sample_idx=sample_idx)
        self._controls.set_ready_state(True)
        self._controls.update_progress(0, "Video yüklendi — Önizleme hazır, dönüştürmeyi başlatabilirsiniz")

        self._on_scrub_frame(sample_idx)

    def _on_scrub_frame(self, frame_idx: int) -> None:
        if not self._current_video:
            return
        cap = cv2.VideoCapture(self._current_video)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame_bgr = cap.read()
        cap.release()
        if not ret:
            return

        self._cached_frame_bgr = frame_bgr
        cfg = self._controls.build_config()
        self._engine.reset_state()
        self._cached_raw_alpha = self._engine.extract_alpha(frame_bgr, cfg.downsample_ratio)
        self._refresh_single_frame_preview()

    def _refresh_single_frame_preview(self) -> None:
        cfg = self._controls.build_config()
        self._preview_canvas.sync_active_mode_badge(cfg)
        if self._cached_frame_bgr is None or self._cached_raw_alpha is None:
            return
        self._post.reset()
        clean_alpha = self._post.refine(self._cached_raw_alpha, cfg)
        preview_bgr = self._post.build_preview(self._cached_frame_bgr, clean_alpha, cfg)
        self._preview_canvas.update_frames(self._cached_frame_bgr, preview_bgr)

    def _start_conversion(self) -> None:
        if not self._current_video:
            return
        cfg = self._controls.build_config()
        self._preview_canvas.sync_active_mode_badge(cfg)
        self._controls.set_running_state(True)
        self._preview_canvas.set_scrub_enabled(False)

        self._worker = VideoMattingWorker(self._current_video, self._engine, cfg)
        self._worker.progress_changed.connect(self._controls.update_progress)
        self._worker.preview_ready.connect(self._preview_canvas.update_frames)
        self._worker.conversion_finished.connect(self._on_conversion_done)
        self._worker.conversion_failed.connect(self._on_conversion_error)
        self._worker.start()

    def _cancel_conversion(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.request_cancel()

    def _on_conversion_done(self, out_path: str) -> None:
        self._last_output_video = out_path
        self._controls.set_running_state(False)
        self._controls.set_playable_output(True)
        self._preview_canvas.set_scrub_enabled(True)
        self._controls.update_progress(100, f"Tamamlandı: {Path(out_path).name}")

        msg = QMessageBox(self)
        msg.setWindowTitle("Maskeleme Tamamlandı")
        msg.setText(
            f"Video başarıyla oluşturuldu:\n{out_path}\n\n"
            "Not: Apple ProRes 4444 (.mov / ap4h) dosyalarını Windows Media Player açamaz; "
            "ancak Adobe Premiere Pro doğrudan tanır veya hemen şimdi AlphaFlow Dahili Oynatıcıda izleyebilirsiniz."
        )
        play_btn = msg.addButton("▶️ Dahili Oynatıcıda İzle", QMessageBox.ButtonRole.AcceptRole)
        folder_btn = msg.addButton("📂 Klasörde Göster", QMessageBox.ButtonRole.ActionRole)
        msg.addButton("Kapat", QMessageBox.ButtonRole.RejectRole)
        msg.exec()

        clicked = msg.clickedButton()
        if clicked == play_btn:
            self._open_builtin_player()
        elif clicked == folder_btn:
            reveal_in_file_manager(out_path)

    def _open_builtin_player(self) -> None:
        target = self._last_output_video or self._current_video
        if not target or not Path(target).exists():
            return
        dlg = StudioVideoPlayerDialog(target, self)
        dlg.exec()

    def _on_conversion_error(self, err_msg: str) -> None:
        self._controls.set_running_state(False)
        self._preview_canvas.set_scrub_enabled(True)
        self._controls.update_progress(0, f"Durduruldu: {err_msg}")
        QMessageBox.warning(self, "Bilgi / Hata", err_msg)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if Path(url.toLocalFile()).suffix.lower() in SUPPORTED_EXTS:
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        for url in event.mimeData().urls():
            local_path = url.toLocalFile()
            if Path(local_path).suffix.lower() in SUPPORTED_EXTS:
                self._on_video_selected(local_path)
                event.acceptProposedAction()
                return
