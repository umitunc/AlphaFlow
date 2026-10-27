import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import '../../core/localization.dart';
import '../../core/models.dart';
import '../../core/theme.dart';
import 'glass_box.dart';

class ControlPanel extends StatefulWidget {
  final MattingConfig config;
  final bool readyToConvert;
  final bool isConverting;
  final bool hasPlayableOutput;
  final int progressPct;
  final String statusText;
  final ValueChanged<MattingConfig> onConfigChanged;
  final VoidCallback onConvertClicked;
  final VoidCallback onCancelClicked;
  final VoidCallback onPlayOutputClicked;

  const ControlPanel({
    super.key,
    required this.config,
    required this.readyToConvert,
    required this.isConverting,
    required this.hasPlayableOutput,
    required this.progressPct,
    required this.statusText,
    required this.onConfigChanged,
    required this.onConvertClicked,
    required this.onCancelClicked,
    required this.onPlayOutputClicked,
  });

  @override
  State<ControlPanel> createState() => _ControlPanelState();
}

class _ControlPanelState extends State<ControlPanel> {
  late final TextEditingController _textCtrl;

  static const List<MapEntry<String, String>> _studioColorSwatches = [
    MapEntry('color_amber', '#F0C05A'),
    MapEntry('color_white', '#FFFFFF'),
    MapEntry('color_cyan', '#22D3EE'),
    MapEntry('color_red', '#EF4444'),
    MapEntry('color_emerald', '#10B981'),
    MapEntry('color_purple', '#A855F7'),
    MapEntry('color_orange', '#F97316'),
    MapEntry('color_blue', '#3B82F6'),
  ];

  @override
  void initState() {
    super.initState();
    _textCtrl = TextEditingController(text: widget.config.backdropText);
  }

  @override
  void dispose() {
    _textCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickOutputDirectory() async {
    final i18n = AppI18n.of(context);
    final folder = await FilePicker.platform.getDirectoryPath(
      dialogTitle: i18n.t('dialog_pick_dir_title'),
    );
    if (folder != null && folder.isNotEmpty) {
      widget.onConfigChanged(widget.config.copyWith(outputDir: folder));
    }
  }

  Future<void> _openColorPickerDialog() async {
    final p = AlphaFlowPalette.of(context);
    final i18n = AppI18n.of(context);
    final hexCtrl = TextEditingController(text: widget.config.textColorHex);
    final chosen = await showDialog<String>(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          backgroundColor: p.isDark
              ? const Color(0xFF151B28)
              : const Color(0xFFF8FAFC),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: BorderSide(color: p.glassBorder),
          ),
          title: Text(
            i18n.t('color_dialog_title'),
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w700,
              color: p.textPrimary,
            ),
          ),
          content: SizedBox(
            width: 380,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  i18n.t('color_dialog_subtitle'),
                  style: TextStyle(color: p.textSecondary, fontSize: 12.5),
                ),
                const SizedBox(height: 10),
                Wrap(
                  spacing: 10,
                  runSpacing: 10,
                  children: [
                    for (final entry in _studioColorSwatches)
                      InkWell(
                        onTap: () => Navigator.of(ctx).pop(entry.value),
                        borderRadius: BorderRadius.circular(10),
                        child: Container(
                          width: 84,
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 8,
                          ),
                          decoration: BoxDecoration(
                            color: p.glassElevatedFill,
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(
                              color: widget.config.textColorHex.toUpperCase() ==
                                      entry.value
                                  ? p.accentCyan
                                  : p.glassBorder,
                            ),
                          ),
                          child: Column(
                            children: [
                              Container(
                                width: 28,
                                height: 28,
                                decoration: BoxDecoration(
                                  color: AlphaFlowTheme.hexToColor(entry.value),
                                  shape: BoxShape.circle,
                                  border: Border.all(color: Colors.black26),
                                ),
                              ),
                              const SizedBox(height: 6),
                              Text(
                                i18n.t(entry.key),
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                  fontSize: 10.5,
                                  color: p.textPrimary,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ],
                          ),
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: hexCtrl,
                  style: TextStyle(color: p.textPrimary),
                  decoration: InputDecoration(
                    labelText: i18n.t('color_dialog_custom_hex'),
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(),
              child: Text(i18n.t('btn_cancel')),
            ),
            FilledButton(
              onPressed: () => Navigator.of(ctx).pop(hexCtrl.text.trim()),
              child: Text(i18n.t('btn_apply')),
            ),
          ],
        );
      },
    );

    if (chosen != null && chosen.isNotEmpty) {
      final previewMode = widget.config.exportMode == ExportMode.depthTextMp4
          ? widget.config.previewMode
          : PreviewMode.depthTextDemo;
      widget.onConfigChanged(
        widget.config.copyWith(
          textColorHex: chosen,
          previewMode: previewMode,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final p = AlphaFlowPalette.of(context);
    final i18n = AppI18n.of(context);
    final cfg = widget.config;
    final textBtnColor = AlphaFlowTheme.hexToColor(cfg.textColorHex);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // YAN YANA KOMPAKT 2 SÜTUNLU KONTROL DOCK'U
        IntrinsicHeight(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // SOL KART: 1. MASKE & ÇIKTI AYARLARI
              Expanded(
                flex: 11,
                child: _GroupGlassCard(
                  title: i18n.t('group1_title'),
                  child: Column(
                    children: [
                      // Satır 1: Çıktı Formatı + Kayıt Klasörü Butonu
                      Row(
                        children: [
                          Text(
                            i18n.t('label_export_format'),
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                              color: p.textPrimary,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: _StyledGlassDropdown<ExportMode>(
                              value: cfg.exportMode,
                              enabled: !widget.isConverting,
                              items: [
                                for (final m in ExportMode.values)
                                  DropdownMenuItem(
                                    value: m,
                                    child: Text(
                                      m.localizedLabel(i18n),
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                              ],
                              onChanged: (val) {
                                if (val == null) return;
                                widget.onConfigChanged(
                                  cfg.copyWith(
                                    exportMode: val,
                                    previewMode: PreviewMode.autoExport,
                                  ),
                                );
                              },
                            ),
                          ),
                          const SizedBox(width: 8),
                          Tooltip(
                            message: cfg.outputDir.isEmpty
                                ? i18n.t('dialog_pick_dir_title')
                                : cfg.outputDir,
                            child: OutlinedButton(
                              onPressed: _pickOutputDirectory,
                              style: OutlinedButton.styleFrom(
                                foregroundColor: p.textPrimary,
                                backgroundColor: p.glassElevatedFill,
                                side: BorderSide(color: p.glassBorder),
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 10,
                                  vertical: 8,
                                ),
                                minimumSize: const Size(0, 32),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(8),
                                ),
                              ),
                              child: Text(
                                i18n.t('btn_choose_dir'),
                                style: const TextStyle(fontSize: 11.5),
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      // Satır 2: Tolerans + Feather + Choke Kaydırıcıları
                      Row(
                        children: [
                          _CompactSliderItem(
                            label: i18n.t(
                              'label_tolerance',
                              {'pct': '${cfg.tolerancePct}'},
                            ),
                            value: cfg.tolerancePct.toDouble(),
                            min: 5,
                            max: 95,
                            highlight: true,
                            onChanged: (v) => widget.onConfigChanged(
                              cfg.copyWith(tolerancePct: v.round()),
                            ),
                          ),
                          const SizedBox(width: 8),
                          _CompactSliderItem(
                            label: i18n.t(
                              'label_feather',
                              {'px': '${cfg.featherPx}'},
                            ),
                            value: cfg.featherPx.toDouble(),
                            min: 0,
                            max: 15,
                            onChanged: (v) => widget.onConfigChanged(
                              cfg.copyWith(featherPx: v.round()),
                            ),
                          ),
                          const SizedBox(width: 8),
                          _CompactSliderItem(
                            label: i18n.t(
                              'label_choke',
                              {'px': '${cfg.chokePx}'},
                            ),
                            value: cfg.chokePx.toDouble(),
                            min: -8,
                            max: 8,
                            onChanged: (v) => widget.onConfigChanged(
                              cfg.copyWith(chokePx: v.round()),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 10),

              // SAĞ KART: 2. 3D ARKADAKİ YAZI
              Expanded(
                flex: 9,
                child: _GroupGlassCard(
                  title: i18n.t('group2_title'),
                  child: Column(
                    children: [
                      // Satır 1: Metin Kutusu + Renk Seçici
                      Row(
                        children: [
                          Text(
                            i18n.t('label_backdrop_text'),
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                              color: p.textPrimary,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: SizedBox(
                              height: 32,
                              child: TextField(
                                controller: _textCtrl,
                                style: TextStyle(
                                  fontSize: 12.5,
                                  color: p.textPrimary,
                                ),
                                decoration: InputDecoration(
                                  hintText: i18n.t('hint_backdrop_text'),
                                  contentPadding: const EdgeInsets.symmetric(
                                    horizontal: 10,
                                    vertical: 6,
                                  ),
                                ),
                                onChanged: (txt) {
                                  final previewMode = cfg.exportMode ==
                                          ExportMode.depthTextMp4
                                      ? cfg.previewMode
                                      : PreviewMode.depthTextDemo;
                                  widget.onConfigChanged(
                                    cfg.copyWith(
                                      backdropText: txt,
                                      previewMode: previewMode,
                                    ),
                                  );
                                },
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          SizedBox(
                            height: 32,
                            child: ElevatedButton(
                              onPressed: _openColorPickerDialog,
                              style: ElevatedButton.styleFrom(
                                backgroundColor: textBtnColor,
                                foregroundColor: const Color(0xFF111318),
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 10,
                                ),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(8),
                                ),
                              ),
                              child: Text(
                                i18n.t('btn_text_color'),
                                style: const TextStyle(
                                  fontWeight: FontWeight.w700,
                                  fontSize: 11.5,
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      // Satır 2: Yazı Boyutu + Dikey Hiza Kaydırıcıları
                      Row(
                        children: [
                          _CompactSliderItem(
                            label: i18n.t(
                              'label_text_scale',
                              {'pct': '${cfg.textScalePct}'},
                            ),
                            value: cfg.textScalePct.toDouble(),
                            min: 40,
                            max: 220,
                            onChanged: (v) {
                              final previewMode =
                                  cfg.exportMode == ExportMode.depthTextMp4
                                      ? cfg.previewMode
                                      : PreviewMode.depthTextDemo;
                              widget.onConfigChanged(
                                cfg.copyWith(
                                  textScalePct: v.round(),
                                  previewMode: previewMode,
                                ),
                              );
                            },
                          ),
                          const SizedBox(width: 10),
                          _CompactSliderItem(
                            label: i18n.t(
                              'label_text_ypos',
                              {'pct': '${cfg.textYPct}'},
                            ),
                            value: cfg.textYPct.toDouble(),
                            min: 10,
                            max: 90,
                            onChanged: (v) {
                              final previewMode =
                                  cfg.exportMode == ExportMode.depthTextMp4
                                      ? cfg.previewMode
                                      : PreviewMode.depthTextDemo;
                              widget.onConfigChanged(
                                cfg.copyWith(
                                  textYPct: v.round(),
                                  previewMode: previewMode,
                                ),
                              );
                            },
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 6),

        // TEK SATIRLI KOMPAKT AKSİYON VE İLERLEME ÇUBUĞU
        SizedBox(
          height: 36,
          child: Row(
            children: [
              Expanded(
                child: GlassCard(
                  padding: EdgeInsets.zero,
                  borderRadius: 9,
                  child: Stack(
                    fit: StackFit.expand,
                    children: [
                      FractionallySizedBox(
                        alignment: Alignment.centerLeft,
                        widthFactor:
                            (widget.progressPct.clamp(0, 100)) / 100.0,
                        child: Container(
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              colors: [p.accentCyan, p.accentIndigo],
                            ),
                          ),
                        ),
                      ),
                      Center(
                        child: Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 12),
                          child: Text(
                            widget.statusText,
                            style: TextStyle(
                              color: p.textPrimary,
                              fontWeight: FontWeight.w700,
                              fontSize: 12,
                            ),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 8),
              OutlinedButton(
                onPressed: widget.isConverting ? widget.onCancelClicked : null,
                style: OutlinedButton.styleFrom(
                  foregroundColor: p.textPrimary,
                  backgroundColor: p.glassElevatedFill,
                  side: BorderSide(color: p.glassBorder),
                  padding: const EdgeInsets.symmetric(horizontal: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(9),
                  ),
                ),
                child: Text(
                  i18n.t('btn_cancel'),
                  style: const TextStyle(fontSize: 12),
                ),
              ),
              const SizedBox(width: 6),
              OutlinedButton.icon(
                onPressed: widget.hasPlayableOutput
                    ? widget.onPlayOutputClicked
                    : null,
                icon: const Icon(Icons.play_circle_fill_rounded, size: 16),
                label: Text(
                  i18n.t('btn_play_output'),
                  style: const TextStyle(fontSize: 12),
                ),
                style: OutlinedButton.styleFrom(
                  foregroundColor: p.textPrimary,
                  backgroundColor: p.glassElevatedFill,
                  side: BorderSide(color: p.glassBorder),
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(9),
                  ),
                ),
              ),
              const SizedBox(width: 6),
              ElevatedButton(
                onPressed: (widget.readyToConvert && !widget.isConverting)
                    ? widget.onConvertClicked
                    : null,
                style: ElevatedButton.styleFrom(
                  backgroundColor: p.accentCyan,
                  disabledBackgroundColor: p.glassElevatedFill,
                  foregroundColor: const Color(0xFF080B12),
                  disabledForegroundColor: p.textMuted,
                  padding: const EdgeInsets.symmetric(horizontal: 18),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(9),
                  ),
                ),
                child: Text(
                  i18n.t('btn_convert_save'),
                  style: const TextStyle(
                    fontWeight: FontWeight.w800,
                    fontSize: 12.5,
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _CompactSliderItem extends StatelessWidget {
  final String label;
  final double value;
  final double min;
  final double max;
  final bool highlight;
  final ValueChanged<double> onChanged;

  const _CompactSliderItem({
    required this.label,
    required this.value,
    required this.min,
    required this.max,
    required this.onChanged,
    this.highlight = false,
  });

  @override
  Widget build(BuildContext context) {
    final p = AlphaFlowPalette.of(context);
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            label,
            style: TextStyle(
              fontSize: 11,
              fontWeight: highlight ? FontWeight.w700 : FontWeight.w500,
              color: highlight ? p.accentCyan : p.textSecondary,
            ),
            overflow: TextOverflow.ellipsis,
          ),
          SizedBox(
            height: 22,
            child: SliderTheme(
              data: SliderTheme.of(context).copyWith(
                trackHeight: 3.5,
                thumbShape:
                    const RoundSliderThumbShape(enabledThumbRadius: 6.0),
                overlayShape:
                    const RoundSliderOverlayShape(overlayRadius: 11.0),
              ),
              child: Slider(
                value: value.clamp(min, max),
                min: min,
                max: max,
                onChanged: onChanged,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _GroupGlassCard extends StatelessWidget {
  final String title;
  final Widget child;

  const _GroupGlassCard({required this.title, required this.child});

  @override
  Widget build(BuildContext context) {
    final p = AlphaFlowPalette.of(context);
    return GlassCard(
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 6),
      borderRadius: 12,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: TextStyle(
              color: p.accentGold,
              fontWeight: FontWeight.w700,
              fontSize: 11,
              letterSpacing: 0.3,
            ),
          ),
          const SizedBox(height: 5),
          child,
        ],
      ),
    );
  }
}

class _StyledGlassDropdown<T> extends StatelessWidget {
  final T value;
  final bool enabled;
  final List<DropdownMenuItem<T>> items;
  final ValueChanged<T?> onChanged;

  const _StyledGlassDropdown({
    required this.value,
    required this.enabled,
    required this.items,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    final p = AlphaFlowPalette.of(context);
    return Container(
      height: 32,
      padding: const EdgeInsets.symmetric(horizontal: 10),
      decoration: BoxDecoration(
        color: p.glassElevatedFill,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: p.glassBorder),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<T>(
          value: value,
          isExpanded: true,
          dropdownColor: p.isDark
              ? const Color(0xFF181F2E)
              : const Color(0xFFF8FAFC),
          style: TextStyle(
            color: p.textPrimary,
            fontSize: 12,
            fontWeight: FontWeight.w500,
          ),
          items: items,
          onChanged: enabled ? onChanged : null,
        ),
      ),
    );
  }
}

