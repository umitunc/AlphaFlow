import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import '../core/models.dart';

class EngineBridgeService {
  Process? _process;
  final StreamController<Map<String, dynamic>> _eventsController =
      StreamController<Map<String, dynamic>>.broadcast();
  Timer? _debounceTimer;

  Stream<Map<String, dynamic>> get events => _eventsController.stream;

  Future<void> start() async {
    if (_process != null) return;

    final rootDir = _resolveWorkspaceRoot();
    final sidecarExe = _findBundledSidecar(rootDir);

    try {
      if (sidecarExe != null) {
        _process = await Process.start(
          sidecarExe.path,
          const [],
          workingDirectory: rootDir.path,
          environment: {'PYTHONIOENCODING': 'utf-8'},
        );
      } else {
        final pythonExe = await _findPythonExecutable(rootDir);
        final scriptFile = File(
          '${rootDir.path}${Platform.pathSeparator}src${Platform.pathSeparator}bridge${Platform.pathSeparator}headless_worker.py',
        );
        _process = await Process.start(
          pythonExe,
          [scriptFile.path],
          workingDirectory: rootDir.path,
          environment: {'PYTHONIOENCODING': 'utf-8'},
        );
      }

      _process!.stdout
          .transform(utf8.decoder)
          .transform(const LineSplitter())
          .listen((line) {
        if (line.trim().isEmpty) return;
        try {
          final decoded = jsonDecode(line) as Map<String, dynamic>;
          _eventsController.add(decoded);
        } catch (e) {
          debugPrint('Bridge JSON parse error: $e');
        }
      });

      _process!.stderr
          .transform(utf8.decoder)
          .transform(const LineSplitter())
          .listen((errLine) {
        debugPrint('[AI Engine Stderr] $errLine');
      });

      sendCommand({'cmd': 'init'});
    } catch (e) {
      _eventsController.add({
        'type': 'error',
        'message': 'AI Motoru başlatılamadı: $e',
      });
    }
  }

  Directory _resolveWorkspaceRoot() {
    var current = Directory.current;
    for (int i = 0; i < 6; i++) {
      final checkScript = File(
        '${current.path}${Platform.pathSeparator}src${Platform.pathSeparator}bridge${Platform.pathSeparator}headless_worker.py',
      );
      if (checkScript.existsSync()) {
        return current;
      }
      final parent = current.parent;
      if (parent.path == current.path) break;
      current = parent;
    }

    // Derlenmiş uygulama paketi (Release / MSIX / macOS .app) dizini kontrolü
    final exeDir = File(Platform.resolvedExecutable).parent;
    final bundledRoot = File(
      '${exeDir.path}${Platform.pathSeparator}src${Platform.pathSeparator}bridge${Platform.pathSeparator}headless_worker.py',
    );
    if (bundledRoot.existsSync()) {
      return exeDir;
    }
    return Directory.current;
  }

  File? _findBundledSidecar(Directory rootDir) {
    final exeDir = File(Platform.resolvedExecutable).parent;
    final binName = Platform.isWindows ? 'alphaflow_engine.exe' : 'alphaflow_engine';
    final candidates = [
      File('${exeDir.path}${Platform.pathSeparator}$binName'),
      File('${exeDir.path}${Platform.pathSeparator}engine${Platform.pathSeparator}$binName'),
      File('${rootDir.path}${Platform.pathSeparator}dist${Platform.pathSeparator}alphaflow_engine${Platform.pathSeparator}$binName'),
    ];
    for (final c in candidates) {
      if (c.existsSync()) return c;
    }
    return null;
  }

  Future<String> _findPythonExecutable(Directory rootDir) async {
    final sep = Platform.pathSeparator;
    final venvCandidates = Platform.isWindows
        ? [
            '${rootDir.path}$sep.venv${sep}Scripts${sep}python.exe',
            '${rootDir.path}${sep}venv${sep}Scripts${sep}python.exe',
          ]
        : [
            '${rootDir.path}$sep.venv${sep}bin${sep}python3',
            '${rootDir.path}$sep.venv${sep}bin${sep}python',
          ];

    for (final path in venvCandidates) {
      if (File(path).existsSync()) return path;
    }
    return Platform.isWindows ? 'python' : 'python3';
  }

  void sendCommand(Map<String, dynamic> payload) {
    final proc = _process;
    if (proc == null) return;
    try {
      proc.stdin.writeln(jsonEncode(payload));
    } catch (e) {
      debugPrint('Bridge sendCommand error: $e');
    }
  }

  void loadVideo(String path, MattingConfig config) {
    sendCommand({
      'cmd': 'load_video',
      'path': path,
      'config': config.toJson(),
    });
  }

  void scrubFrameDebounced(int frameIdx, MattingConfig config) {
    _debounceTimer?.cancel();
    _debounceTimer = Timer(const Duration(milliseconds: 45), () {
      sendCommand({
        'cmd': 'scrub',
        'frame_idx': frameIdx,
        'config': config.toJson(),
      });
    });
  }

  void updateConfigDebounced(MattingConfig config) {
    _debounceTimer?.cancel();
    _debounceTimer = Timer(const Duration(milliseconds: 45), () {
      sendCommand({
        'cmd': 'update_config',
        'config': config.toJson(),
      });
    });
  }

  void startConversion(MattingConfig config) {
    sendCommand({
      'cmd': 'convert',
      'config': config.toJson(),
    });
  }

  void cancelConversion() {
    sendCommand({'cmd': 'cancel'});
  }

  void openPlayer(String path) {
    sendCommand({'cmd': 'player_open', 'path': path});
  }

  void requestPlayerFrame({int? frameIdx}) {
    sendCommand({'cmd': 'player_frame', 'frame_idx': frameIdx});
  }

  void closePlayer() {
    sendCommand({'cmd': 'player_close'});
  }

  void revealFileInExplorer(String path) {
    sendCommand({'cmd': 'reveal', 'path': path});
  }

  static Uint8List? decodeBase64Frame(dynamic rawB64) {
    if (rawB64 is! String || rawB64.isEmpty) return null;
    try {
      return base64Decode(rawB64);
    } catch (_) {
      return null;
    }
  }

  Future<void> restartAndRefresh({
    String? videoPath,
    int frameIdx = 0,
    required MattingConfig config,
  }) async {
    _debounceTimer?.cancel();
    try {
      sendCommand({'cmd': 'quit'});
      _process?.kill();
    } catch (_) {}
    _process = null;
    await start();
    if (videoPath != null && videoPath.isNotEmpty) {
      loadVideo(videoPath, config);
      if (frameIdx > 0) {
        scrubFrameDebounced(frameIdx, config);
      }
    }
  }

  void dispose() {
    _debounceTimer?.cancel();
    sendCommand({'cmd': 'quit'});
    _process?.kill();
    _process = null;
    _eventsController.close();
  }
}
