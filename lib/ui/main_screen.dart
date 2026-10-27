import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import '../core/localization.dart';
import '../core/models.dart';
import '../core/theme.dart';
import '../services/engine_bridge_service.dart';
import 'widgets/control_panel.dart';
import 'widgets/frameless_title_bar.dart';
import 'widgets/glass_box.dart';
import 'widgets/preview_canvas.dart';
import 'widgets/studio_player_dialog.dart';

class AlphaFlowMainScreen extends StatefulWidget {
  final ThemeMode themeMode;
  final ValueChanged<ThemeMode> onThemeModeChanged;
  final String langCode;
  final ValueChanged<String> onLangCodeChanged;

  const AlphaFlowMainScreen({
    super.key,
    required this.themeMode,
    required this.onThemeModeChanged,
    required this.langCode,
    required this.onLangCodeChanged,
  });

  @override
  State<AlphaFlowMainScreen> createState() => _AlphaFlowMainScreenState();
}

class _AlphaFlowMainScreenState extends State<AlphaFlowMainScreen> {
  final EngineBridgeService _bridge = EngineBridgeService();
  StreamSubscription<Map<String, dynamic>>? _sub;

  MattingConfig _config = const MattingConfig();
  SystemDiagnostics _diagnostics = const SystemDiagnostics();
  VideoMetadata? _videoMeta;
  Uint8List? _origFrameBytes;
  Uint8List? _previewFrameBytes;

  int _currentFrameIdx = 0;
  bool _isConverting = false;
  int _progressPct = 0;
  String _statusKey = 'status_starting_engine';
  Map<String, String> _statusParams = const {};
  String _lastOutputVideo = '';

  @override
  void initState() {
    super.initState();
    _sub = _bridge.events.listen(_handleBridgeEvent);
    _bridge.start();
  }

  @override
  void reassemble() {
    super.reassemble();
    // Hot Reload (r) yapıldığında Python AI alt sürecini yeni motor kodlarıyla yeniden başlat
    if (!_isConverting) {
      _bridge.restartAndRefresh(
        videoPath: _videoMeta?.path,
        frameIdx: _currentFrameIdx,
        config: _config,
      );
    }
  }

  void _handleBridgeEvent(Map<String, dynamic> event) {
    if (!mounted) return;
    final type = event['type'];

    switch (type) {
      case 'model_download':
        final pct = (event['pct'] as num?)?.toInt() ?? 0;
        setState(() {
          _progressPct = pct;
          _statusKey = 'status_downloading_model';
          _statusParams = {'pct': '$pct'};
        });
        break;

      case 'ready':
        setState(() {
          _diagnostics = SystemDiagnostics(
            os: (event['os'] as String?) ?? 'OS',
            accelerator: (event['accelerator'] as String?) ?? 'CPU / GPU',
            ffmpeg: (event['ffmpeg'] as String?) ?? 'FFmpeg',
            ready: true,
          );
          _progressPct = 0;
          if (_videoMeta == null) {
            _statusKey = 'status_ready_idle';
            _statusParams = const {};
          }
        });
        break;

      case 'video_loaded':
        final parentDir = (event['parent_dir'] as String?) ?? '';
        final sampleIdx = (event['sample_idx'] as num?)?.toInt() ?? 0;
        final meta = VideoMetadata(
          path: (event['path'] as String?) ?? '',
          name: (event['name'] as String?) ?? '',
          parentDir: parentDir,
          width: (event['width'] as num?)?.toInt() ?? 0,
          height: (event['height'] as num?)?.toInt() ?? 0,
          fps: (event['fps'] as num?)?.toDouble() ?? 24.0,
          totalFrames: (event['total_frames'] as num?)?.toInt() ?? 1,
          durationSec: (event['duration_sec'] as num?)?.toDouble() ?? 0.0,
          sampleIdx: sampleIdx,
        );
        final orig = EngineBridgeService.decodeBase64Frame(event['orig_b64']);
        final prev =
            EngineBridgeService.decodeBase64Frame(event['preview_b64']);
        setState(() {
          _videoMeta = meta;
          if (_config.outputDir.isEmpty && parentDir.isNotEmpty) {
            _config = _config.copyWith(outputDir: parentDir);
          }
          _currentFrameIdx = sampleIdx;
          _origFrameBytes = orig;
          _previewFrameBytes = prev;
          _progressPct = 0;
          _statusKey = 'status_video_loaded';
          _statusParams = const {};
        });
        break;

      case 'preview_updated':
        final orig = EngineBridgeService.decodeBase64Frame(event['orig_b64']);
        final prev =
            EngineBridgeService.decodeBase64Frame(event['preview_b64']);
        final frameIdx = (event['frame_idx'] as num?)?.toInt();
        setState(() {
          if (frameIdx != null) _currentFrameIdx = frameIdx;
          if (orig != null) _origFrameBytes = orig;
          if (prev != null) _previewFrameBytes = prev;
        });
        break;

      case 'progress':
        final pct = (event['pct'] as num?)?.toInt() ?? 0;
        final curFrame = (event['frame_idx'] as num?)?.toInt() ?? 0;
        final totFrames = (event['total_frames'] as num?)?.toInt() ?? 1;
        final fps = (event['fps'] as num?)?.toDouble() ?? 0.0;
        final eta = (event['eta_sec'] as num?)?.toDouble() ?? 0.0;
        final orig = EngineBridgeService.decodeBase64Frame(event['orig_b64']);
        final prev =
            EngineBridgeService.decodeBase64Frame(event['preview_b64']);
        setState(() {
          _progressPct = pct;
          _currentFrameIdx = curFrame;
          _statusKey = 'status_processing_progress';
          _statusParams = {
            'current': '$curFrame',
            'total': '$totFrames',
            'fps': fps.toStringAsFixed(1),
            'eta': eta.toStringAsFixed(1),
          };
          if (orig != null) _origFrameBytes = orig;
          if (prev != null) _previewFrameBytes = prev;
        });
        break;

      case 'conversion_finished':
        final outPath = (event['output_path'] as String?) ?? '';
        final fileName = (event['file_name'] as String?) ?? outPath;
        setState(() {
          _isConverting = false;
          _lastOutputVideo = outPath;
          _progressPct = 100;
          _statusKey = 'status_completed';
          _statusParams = {'file': fileName};
        });
        _showCompletionDialog(outPath);
        break;

      case 'conversion_failed':
        final err = (event['error'] as String?) ?? 'Error';
        setState(() {
          _isConverting = false;
          _progressPct = 0;
          _statusKey = 'status_stopped';
          _statusParams = {'error': err};
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(err),
            backgroundColor: const Color(0xFFB91C1C),
          ),
        );
        break;

      case 'error':
        final msg = (event['message'] as String?) ?? 'Error';
        setState(() {
          _statusKey = 'status_stopped';
          _statusParams = {'error': msg};
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(msg),
            backgroundColor: const Color(0xFFB91C1C),
          ),
        );
        break;
    }
  }

  void _onVideoSelected(String path) {
    if (_isConverting) return;
    setState(() {
      _statusKey = 'status_analyzing_video';
      _statusParams = const {};
    });
    _bridge.loadVideo(path, _config);
  }

  void _onScrubFrame(int frameIdx) {
    if (_isConverting || _videoMeta == null) return;
    setState(() {
      _currentFrameIdx = frameIdx;
    });
    _bridge.scrubFrameDebounced(frameIdx, _config);
  }

  void _onConfigChanged(MattingConfig newConfig) {
    setState(() {
      _config = newConfig;
    });
    if (_videoMeta != null && !_isConverting) {
      _bridge.updateConfigDebounced(newConfig);
    }
  }

  void _onPreviewModeSelected(PreviewMode mode) {
    _onConfigChanged(_config.copyWith(previewMode: mode));
  }

  void _startConversion() {
    if (_videoMeta == null || _isConverting) return;
    setState(() {
      _isConverting = true;
      _progressPct = 0;
      _statusKey = 'status_starting_conversion';
      _statusParams = const {};
    });
    _bridge.startConversion(_config);
  }

  void _cancelConversion() {
    if (!_isConverting) return;
    _bridge.cancelConversion();
  }

  void _openBuiltinPlayer([String? specificPath]) {
    final target = specificPath ??
        (_lastOutputVideo.isNotEmpty
            ? _lastOutputVideo
            : (_videoMeta?.path ?? ''));
    if (target.isEmpty) return;
    showDialog<void>(
      context: context,
      builder: (_) => StudioPlayerDialog(
        videoPath: target,
        bridge: _bridge,
      ),
    );
  }

  void _showCompletionDialog(String outPath) {
    final p = AlphaFlowPalette.of(context);
    final i18n = AppI18n.of(context);
    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor:
            p.isDark ? const Color(0xFF151B28) : const Color(0xFFF8FAFC),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: BorderSide(color: p.glassBorder),
        ),
        title: Row(
          children: [
            const Icon(Icons.check_circle_rounded, color: Color(0xFF4ADE80)),
            const SizedBox(width: 10),
            Text(
              i18n.t('done_dialog_title'),
              style: TextStyle(
                fontSize: 17,
                fontWeight: FontWeight.w700,
                color: p.textPrimary,
              ),
            ),
          ],
        ),
        content: SizedBox(
          width: 480,
          child: Text(
            i18n.t('done_dialog_body', {'path': outPath}),
            style: TextStyle(
              color: p.textSecondary,
              height: 1.45,
              fontSize: 13,
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: Text(i18n.t('btn_close')),
          ),
          OutlinedButton.icon(
            onPressed: () {
              Navigator.of(ctx).pop();
              _bridge.revealFileInExplorer(outPath);
            },
            icon: const Icon(Icons.folder_open_rounded, size: 18),
            label: Text(i18n.t('btn_reveal_folder')),
          ),
          FilledButton.icon(
            onPressed: () {
              Navigator.of(ctx).pop();
              _openBuiltinPlayer(outPath);
            },
            icon: const Icon(Icons.play_arrow_rounded, size: 18),
            label: Text(i18n.t('btn_watch_builtin')),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _sub?.cancel();
    _bridge.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final i18n = AppI18n.of(context);

    return Scaffold(
      backgroundColor: Colors.transparent,
      body: FramelessResizeWrapper(
        child: GlassmorphicAmbientCanvas(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(10, 8, 10, 8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // 1. Kompakt Çerçevesiz (Frameless) Başlık Çubuğu
                FramelessTitleBar(
                  themeMode: widget.themeMode,
                  onThemeModeChanged: widget.onThemeModeChanged,
                  langCode: widget.langCode,
                  onLangCodeChanged: widget.onLangCodeChanged,
                ),
                const SizedBox(height: 6),

                // 2. Yan Yana Canlı Önizleme Tuvali (Sol Panelde Video Rozeti + Dosya Seçici, Sağ Panelde AI Rozeti + Görünüm Hapları)
                Expanded(
                  child: PreviewCanvas(
                    config: _config,
                    diagnostics: _diagnostics,
                    videoMeta: _videoMeta,
                    originalFrameBytes: _origFrameBytes,
                    previewFrameBytes: _previewFrameBytes,
                    currentFrameIdx: _currentFrameIdx,
                    scrubEnabled: !_isConverting,
                    onPreviewModeSelected: _onPreviewModeSelected,
                    onScrubFrame: _onScrubFrame,
                    onVideoDropped: _onVideoSelected,
                  ),
                ),
                const SizedBox(height: 6),

                // 3. Yan Yana Kompakt Kontrol Dock'u & Tek Satır Aksiyon Barı
                ControlPanel(
                  config: _config,
                  readyToConvert: _videoMeta != null,
                  isConverting: _isConverting,
                  hasPlayableOutput:
                      _lastOutputVideo.isNotEmpty || _videoMeta != null,
                  progressPct: _progressPct,
                  statusText: i18n.t(_statusKey, _statusParams),
                  onConfigChanged: _onConfigChanged,
                  onConvertClicked: _startConversion,
                  onCancelClicked: _cancelConversion,
                  onPlayOutputClicked: () => _openBuiltinPlayer(),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
