import 'dart:typed_data';
import 'package:desktop_drop/desktop_drop.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import '../../core/localization.dart';
import '../../core/models.dart';
import '../../core/theme.dart';
import 'glass_box.dart';
import 'header_drop_zone.dart';

class PreviewCanvas extends StatefulWidget {
  final MattingConfig config;
  final SystemDiagnostics diagnostics;
  final VideoMetadata? videoMeta;
  final Uint8List? originalFrameBytes;
  final Uint8List? previewFrameBytes;
  final int currentFrameIdx;
  final bool scrubEnabled;
  final ValueChanged<PreviewMode> onPreviewModeSelected;
  final ValueChanged<int> onScrubFrame;
  final ValueChanged<String> onVideoDropped;

  const PreviewCanvas({
    super.key,
    required this.config,
    required this.diagnostics,
    required this.videoMeta,
    required this.originalFrameBytes,
    required this.previewFrameBytes,
    required this.currentFrameIdx,
    required this.scrubEnabled,
    required this.onPreviewModeSelected,
    required this.onScrubFrame,
    required this.onVideoDropped,
  });

  @override
  State<PreviewCanvas> createState() => _PreviewCanvasState();
}

class _PreviewCanvasState extends State<PreviewCanvas> {
  bool _leftHighlight = false;

  Future<void> _pickVideoFile() async {
    if (!widget.scrubEnabled) return;
    final i18n = AppI18n.of(context);
    final res = await FilePicker.platform.pickFiles(
      dialogTitle: i18n.t('dialog_pick_video_title'),
      type: FileType.custom,
      allowedExtensions: HeaderDropZone.supportedExtensions.toList(),
    );
    final path = res?.files.singleOrNull?.path;
    if (path != null && path.isNotEmpty) {
      widget.onVideoDropped(path);
    }
  }

  @override
  Widget build(BuildContext context) {
    final p = AlphaFlowPalette.of(context);
    final i18n = AppI18n.of(context);
    final totalFrames = widget.videoMeta?.totalFrames ?? 0;
    final sliderMax = (totalFrames > 1 ? totalFrames - 1 : 1).toDouble();
    final sliderVal =
        widget.currentFrameIdx.clamp(0, sliderMax.toInt()).toDouble();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Sol ve Sağ Kompakt Glassmorphic Önizleme Panelleri
        Expanded(
          child: Row(
            children: [
              // SOL PANEL: Orijinal Video + Dahili Dosya Seçici & Sürükle-Bırak
              Expanded(
                child: DropTarget(
                  onDragEntered: (_) {
                    if (widget.scrubEnabled) {
                      setState(() => _leftHighlight = true);
                    }
                  },
                  onDragExited: (_) {
                    if (_leftHighlight) {
                      setState(() => _leftHighlight = false);
                    }
                  },
                  onDragDone: (detail) {
                    setState(() => _leftHighlight = false);
                    if (!widget.scrubEnabled) return;
                    for (final file in detail.files) {
                      if (HeaderDropZone.isSupportedVideoPath(file.path)) {
                        widget.onVideoDropped(file.path);
                        break;
                      }
                    }
                  },
                  child: GlassCard(
                    padding: const EdgeInsets.all(8),
                    borderRadius: 13,
                    borderColor: _leftHighlight ? p.accentCyan : p.glassBorder,
                    borderWidth: _leftHighlight ? 2.0 : 1.1,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        // Sol Panel Üst Barı: Başlık + Yüklü Video Rozeti + Kompakt Dosya Seç Butonu
                        Row(
                          children: [
                            const SizedBox(width: 4),
                            Icon(
                              Icons.movie_creation_rounded,
                              size: 14,
                              color: p.accentGold,
                            ),
                            const SizedBox(width: 5),
                            Text(
                              i18n.t('left_panel_title'),
                              style: TextStyle(
                                color: p.accentGold,
                                fontWeight: FontWeight.w700,
                                fontSize: 11.5,
                                letterSpacing: 0.25,
                              ),
                            ),
                            const SizedBox(width: 8),
                            if (widget.videoMeta != null)
                              Expanded(
                                child: Align(
                                  alignment: Alignment.centerLeft,
                                  child: Container(
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 8,
                                      vertical: 2.5,
                                    ),
                                    decoration: BoxDecoration(
                                      color: const Color(0xFF22C55E)
                                          .withValues(alpha: 0.14),
                                      borderRadius: BorderRadius.circular(14),
                                      border: Border.all(
                                        color: const Color(0xFF22C55E)
                                            .withValues(alpha: 0.35),
                                      ),
                                    ),
                                    child: Text(
                                      '✅ ${i18n.t('dropzone_loaded', {
                                        'name': widget.videoMeta!.name,
                                        'width': '${widget.videoMeta!.width}',
                                        'height': '${widget.videoMeta!.height}',
                                        'fps': widget.videoMeta!.fps
                                            .toStringAsFixed(0),
                                        'frames':
                                            '${widget.videoMeta!.totalFrames}',
                                      })}',
                                      style: TextStyle(
                                        fontSize: 10.5,
                                        fontWeight: FontWeight.w600,
                                        color: p.isDark
                                            ? const Color(0xFF4ADE80)
                                            : const Color(0xFF15803D),
                                      ),
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                ),
                              )
                            else
                              const Spacer(),
                            const SizedBox(width: 6),
                            SizedBox(
                              height: 26,
                              child: FilledButton.tonalIcon(
                                onPressed: widget.scrubEnabled
                                    ? _pickVideoFile
                                    : null,
                                icon: const Icon(
                                  Icons.folder_open_rounded,
                                  size: 14,
                                ),
                                label: Text(
                                  i18n.t('btn_browse_video'),
                                  style: const TextStyle(
                                    fontSize: 11.5,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                                style: FilledButton.styleFrom(
                                  backgroundColor:
                                      p.accentCyan.withValues(alpha: 0.16),
                                  foregroundColor: p.textPrimary,
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 10,
                                  ),
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(7),
                                    side: BorderSide(
                                      color:
                                          p.accentCyan.withValues(alpha: 0.4),
                                    ),
                                  ),
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 6),
                        // Görüntü veya Tıklanabilir Video Seçim Alanı
                        Expanded(
                          child: InkWell(
                            onTap: widget.originalFrameBytes == null
                                ? _pickVideoFile
                                : null,
                            borderRadius: BorderRadius.circular(9),
                            child: Container(
                              decoration: BoxDecoration(
                                color: p.viewportBackground,
                                borderRadius: BorderRadius.circular(9),
                                border: Border.all(
                                  color: Colors.white.withValues(alpha: 0.08),
                                ),
                              ),
                              clipBehavior: Clip.antiAlias,
                              child: widget.originalFrameBytes != null
                                  ? Center(
                                      child: Image.memory(
                                        widget.originalFrameBytes!,
                                        fit: BoxFit.contain,
                                        gaplessPlayback: true,
                                      ),
                                    )
                                  : Center(
                                      child: Column(
                                        mainAxisSize: MainAxisSize.min,
                                        children: [
                                          Image.asset(
                                            'assets/icons/alphaflow_logo_transparent.png',
                                            width: 52,
                                            height: 52,
                                            fit: BoxFit.contain,
                                          ),
                                          const SizedBox(height: 10),
                                          Text(
                                            i18n.t('left_panel_placeholder'),
                                            textAlign: TextAlign.center,
                                            style: const TextStyle(
                                              color: Color(0xFF94A3B8),
                                              fontSize: 12.5,
                                              height: 1.35,
                                            ),
                                          ),
                                          const SizedBox(height: 12),
                                          FilledButton.tonalIcon(
                                            onPressed: widget.scrubEnabled
                                                ? _pickVideoFile
                                                : null,
                                            icon: const Icon(
                                              Icons.video_library_rounded,
                                              size: 16,
                                            ),
                                            label: Text(
                                              i18n.t('btn_browse_video'),
                                            ),
                                            style: FilledButton.styleFrom(
                                              backgroundColor: p.accentCyan
                                                  .withValues(alpha: 0.2),
                                              foregroundColor: Colors.white,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 10),

              // SAĞ PANEL: Canlı Çıktı Önizlemesi + Entegre Mod Hapları
              Expanded(
                child: GlassCard(
                  padding: const EdgeInsets.all(8),
                  borderRadius: 13,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      // Sağ Panel Üst Barı: AI/Codec Rozeti + Entegre Hızlı Görünüm Seçici Haplar
                      SizedBox(
                        height: 26,
                        child: Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 8,
                                vertical: 3,
                              ),
                              decoration: BoxDecoration(
                                color: p.accentCyan.withValues(alpha: 0.14),
                                borderRadius: BorderRadius.circular(14),
                                border: Border.all(
                                  color: p.accentCyan.withValues(alpha: 0.35),
                                ),
                              ),
                              child: Text(
                                i18n.t('badge_ai_codec', {
                                  'accelerator': widget.diagnostics.accelerator,
                                }),
                                style: TextStyle(
                                  fontSize: 10.5,
                                  fontWeight: FontWeight.w700,
                                  color: p.accentCyan,
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: SingleChildScrollView(
                                scrollDirection: Axis.horizontal,
                                child: Row(
                                  children: [
                                    for (final mode in PreviewMode.values)
                                      Padding(
                                        padding:
                                            const EdgeInsets.only(right: 5),
                                        child: _ModePillButton(
                                          label: mode.localizedPill(i18n),
                                          selected:
                                              widget.config.previewMode == mode,
                                          onTap: () => widget
                                              .onPreviewModeSelected(mode),
                                        ),
                                      ),
                                  ],
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 6),
                      Expanded(
                        child: Container(
                          decoration: BoxDecoration(
                            color: p.viewportBackground,
                            borderRadius: BorderRadius.circular(9),
                            border: Border.all(
                              color: Colors.white.withValues(alpha: 0.08),
                            ),
                          ),
                          clipBehavior: Clip.antiAlias,
                          child: widget.previewFrameBytes != null
                              ? Center(
                                  child: Image.memory(
                                    widget.previewFrameBytes!,
                                    fit: BoxFit.contain,
                                    gaplessPlayback: true,
                                  ),
                                )
                              : Center(
                                  child: Column(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Opacity(
                                        opacity: 0.55,
                                        child: Image.asset(
                                          'assets/icons/alphaflow_logo_transparent.png',
                                          width: 52,
                                          height: 52,
                                          fit: BoxFit.contain,
                                        ),
                                      ),
                                      const SizedBox(height: 10),
                                      Text(
                                        i18n.t('right_panel_placeholder'),
                                        textAlign: TextAlign.center,
                                        style: const TextStyle(
                                          color: Color(0xFF94A3B8),
                                          fontSize: 12.5,
                                          height: 1.35,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 6),

        // Kompakt Timeline Kare Kaydırıcı (Scrubber)
        GlassCard(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 2),
          borderRadius: 10,
          child: SizedBox(
            height: 28,
            child: Row(
              children: [
                Icon(
                  Icons.linear_scale_rounded,
                  size: 15,
                  color: p.accentCyan,
                ),
                const SizedBox(width: 6),
                Text(
                  i18n.t('scrubber_label', {
                    'current': totalFrames > 0
                        ? '${widget.currentFrameIdx + 1}'
                        : '0',
                    'total': '$totalFrames',
                  }),
                  style: TextStyle(
                    color: p.textSecondary,
                    fontWeight: FontWeight.w600,
                    fontSize: 12,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Slider(
                    value: sliderVal,
                    min: 0,
                    max: sliderMax,
                    onChanged: (widget.scrubEnabled && totalFrames > 1)
                        ? (v) => widget.onScrubFrame(v.round())
                        : null,
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _ModePillButton extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _ModePillButton({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final p = AlphaFlowPalette.of(context);

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 140),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(
          color: selected
              ? p.accentCyan.withValues(alpha: p.isDark ? 0.25 : 0.18)
              : p.glassElevatedFill,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: selected ? p.accentCyan : p.glassBorder,
            width: selected ? 1.3 : 1.0,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 11.5,
            fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
            color: selected ? p.textPrimary : p.textSecondary,
          ),
        ),
      ),
    );
  }
}
