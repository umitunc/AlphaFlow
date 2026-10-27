import 'package:desktop_drop/desktop_drop.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import '../../core/localization.dart';
import '../../core/models.dart';
import '../../core/theme.dart';
import 'glass_box.dart';

class HeaderDropZone extends StatefulWidget {
  final VideoMetadata? videoMeta;
  final bool enabled;
  final ValueChanged<String> onVideoSelected;

  const HeaderDropZone({
    super.key,
    required this.videoMeta,
    required this.enabled,
    required this.onVideoSelected,
  });

  static const Set<String> supportedExtensions = {
    'mp4',
    'mov',
    'mkv',
    'avi',
    'webm',
  };

  static bool isSupportedVideoPath(String path) {
    final dot = path.lastIndexOf('.');
    if (dot < 0) return false;
    final ext = path.substring(dot + 1).toLowerCase();
    return supportedExtensions.contains(ext);
  }

  @override
  State<HeaderDropZone> createState() => _HeaderDropZoneState();
}

class _HeaderDropZoneState extends State<HeaderDropZone> {
  bool _isDragging = false;

  Future<void> _pickFile() async {
    if (!widget.enabled) return;
    final i18n = AppI18n.of(context);
    final res = await FilePicker.platform.pickFiles(
      dialogTitle: i18n.t('dialog_pick_video_title'),
      type: FileType.custom,
      allowedExtensions: HeaderDropZone.supportedExtensions.toList(),
    );
    final path = res?.files.singleOrNull?.path;
    if (path != null && path.isNotEmpty) {
      widget.onVideoSelected(path);
    }
  }

  @override
  Widget build(BuildContext context) {
    final p = AlphaFlowPalette.of(context);
    final i18n = AppI18n.of(context);
    final meta = widget.videoMeta;

    return DropTarget(
      onDragEntered: (_) {
        if (widget.enabled) setState(() => _isDragging = true);
      },
      onDragExited: (_) {
        if (_isDragging) setState(() => _isDragging = false);
      },
      onDragDone: (detail) {
        setState(() => _isDragging = false);
        if (!widget.enabled) return;
        for (final file in detail.files) {
          if (HeaderDropZone.isSupportedVideoPath(file.path)) {
            widget.onVideoSelected(file.path);
            break;
          }
        }
      },
      child: GlassCard(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 9),
        borderRadius: 13,
        borderColor: _isDragging ? p.accentCyan : p.glassBorder,
        borderWidth: _isDragging ? 2.0 : 1.1,
        child: Row(
          children: [
            Image.asset(
              'assets/icons/alphaflow_logo_transparent.png',
              width: 34,
              height: 34,
              fit: BoxFit.contain,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                meta == null
                    ? i18n.t('dropzone_empty')
                    : i18n.t('dropzone_loaded', {
                        'name': meta.name,
                        'width': meta.width.toString(),
                        'height': meta.height.toString(),
                        'fps': meta.fps.toStringAsFixed(1),
                        'frames': meta.totalFrames.toString(),
                        'duration': meta.durationSec.toStringAsFixed(1),
                      }),
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: meta == null
                      ? p.textPrimary
                      : (p.isDark
                          ? const Color(0xFF4ADE80)
                          : const Color(0xFF15803D)),
                ),
                overflow: TextOverflow.ellipsis,
              ),
            ),
            const SizedBox(width: 12),
            FilledButton.tonalIcon(
              onPressed: widget.enabled ? _pickFile : null,
              icon: const Icon(Icons.video_library_rounded, size: 17),
              label: Text(i18n.t('btn_browse_video')),
              style: FilledButton.styleFrom(
                backgroundColor: p.accentCyan.withValues(alpha: 0.16),
                foregroundColor: p.textPrimary,
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 12,
                ),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(9),
                  side: BorderSide(color: p.accentCyan.withValues(alpha: 0.4)),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
