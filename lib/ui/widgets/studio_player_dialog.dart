import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import '../../core/localization.dart';
import '../../core/theme.dart';
import '../../services/engine_bridge_service.dart';
import 'glass_box.dart';

class StudioPlayerDialog extends StatefulWidget {
  final String videoPath;
  final EngineBridgeService bridge;

  const StudioPlayerDialog({
    super.key,
    required this.videoPath,
    required this.bridge,
  });

  @override
  State<StudioPlayerDialog> createState() => _StudioPlayerDialogState();
}

class _StudioPlayerDialogState extends State<StudioPlayerDialog> {
  StreamSubscription<Map<String, dynamic>>? _sub;
  Timer? _playTimer;
  String _fileName = '';
  double _fps = 24.0;
  int _totalFrames = 1;
  int _currentIdx = 0;
  bool _playing = true;
  bool _waitingFrame = false;
  Uint8List? _frameBytes;

  @override
  void initState() {
    super.initState();
    _fileName = widget.videoPath.split(RegExp(r'[\\/]')).last;
    _sub = widget.bridge.events.listen(_onBridgeEvent);
    widget.bridge.openPlayer(widget.videoPath);
  }

  void _onBridgeEvent(Map<String, dynamic> ev) {
    final type = ev['type'];
    if (type == 'player_opened') {
      final fps = (ev['fps'] as num?)?.toDouble() ?? 24.0;
      final total = (ev['total_frames'] as num?)?.toInt() ?? 1;
      final idx = (ev['frame_idx'] as num?)?.toInt() ?? 0;
      final bytes = EngineBridgeService.decodeBase64Frame(ev['frame_b64']);
      if (!mounted) return;
      setState(() {
        _fps = fps;
        _totalFrames = total > 0 ? total : 1;
        _currentIdx = idx;
        _frameBytes = bytes;
        _waitingFrame = false;
      });
      _startTimer();
    } else if (type == 'player_frame') {
      final idx = (ev['frame_idx'] as num?)?.toInt() ?? 0;
      final bytes = EngineBridgeService.decodeBase64Frame(ev['frame_b64']);
      if (!mounted) return;
      setState(() {
        _currentIdx = idx;
        if (bytes != null) _frameBytes = bytes;
        _waitingFrame = false;
      });
    }
  }

  void _startTimer() {
    _playTimer?.cancel();
    final intervalMs =
        (1000.0 / (_fps > 1.0 ? _fps : 24.0)).round().clamp(16, 200);
    _playTimer = Timer.periodic(Duration(milliseconds: intervalMs), (_) {
      if (!_playing || _waitingFrame) return;
      _waitingFrame = true;
      widget.bridge.requestPlayerFrame();
    });
  }

  void _togglePlay() {
    setState(() {
      _playing = !_playing;
    });
  }

  void _seekTo(int idx) {
    setState(() {
      _currentIdx = idx;
      _waitingFrame = true;
    });
    widget.bridge.requestPlayerFrame(frameIdx: idx);
  }

  @override
  void dispose() {
    _playTimer?.cancel();
    _sub?.cancel();
    widget.bridge.closePlayer();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final p = AlphaFlowPalette.of(context);
    final i18n = AppI18n.of(context);
    final sliderMax = (_totalFrames > 1 ? _totalFrames - 1 : 1).toDouble();
    final sliderVal = _currentIdx.clamp(0, sliderMax.toInt()).toDouble();

    return Dialog(
      backgroundColor: Colors.transparent,
      elevation: 0,
      child: SizedBox(
        width: 920,
        height: 620,
        child: GlassCard(
          padding: const EdgeInsets.all(16),
          borderRadius: 18,
          blurSigma: 28,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                children: [
                  Image.asset(
                    'assets/icons/alphaflow_logo_transparent.png',
                    width: 26,
                    height: 26,
                    fit: BoxFit.contain,
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      i18n.t('player_header_info', {'file': _fileName}),
                      style: TextStyle(
                        color: p.accentGold,
                        fontWeight: FontWeight.w700,
                        fontSize: 13.5,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  IconButton(
                    onPressed: () => Navigator.of(context).pop(),
                    icon: Icon(Icons.close_rounded, color: p.textPrimary),
                    tooltip: i18n.t('tooltip_close'),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Expanded(
                child: Container(
                  decoration: BoxDecoration(
                    color: p.viewportBackground,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: p.glassBorder),
                  ),
                  clipBehavior: Clip.antiAlias,
                  child: _frameBytes != null
                      ? Center(
                          child: Image.memory(
                            _frameBytes!,
                            fit: BoxFit.contain,
                            gaplessPlayback: true,
                          ),
                        )
                      : const Center(
                          child: CircularProgressIndicator(),
                        ),
                ),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  FilledButton.tonalIcon(
                    onPressed: _togglePlay,
                    icon: Icon(
                      _playing
                          ? Icons.pause_rounded
                          : Icons.play_arrow_rounded,
                    ),
                    label: Text(
                      _playing ? i18n.t('btn_pause') : i18n.t('btn_play'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Slider(
                      value: sliderVal,
                      min: 0,
                      max: sliderMax,
                      onChanged: (v) => _seekTo(v.round()),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    '${_currentIdx + 1} / $_totalFrames',
                    style: TextStyle(
                      color: p.textSecondary,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(width: 12),
                  OutlinedButton.icon(
                    onPressed: () =>
                        widget.bridge.revealFileInExplorer(widget.videoPath),
                    icon: const Icon(Icons.folder_open_rounded, size: 18),
                    label: Text(i18n.t('btn_reveal_file')),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
