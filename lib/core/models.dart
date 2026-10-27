import 'dart:typed_data';
import 'localization.dart';

enum ExportMode {
  lumaMatteMp4('luma_mp4', 'export_luma_mp4', '_luma_matte.mp4'),
  proresAlphaMov('prores_mov', 'export_prores_mov', '_alpha_prores4444.mov'),
  vp9AlphaWebm('vp9_webm', 'export_vp9_webm', '_alpha_vp9.webm'),
  greenScreenMp4('green_mp4', 'export_green_mp4', '_greenscreen.mp4'),
  depthTextMp4('depth_text_mp4', 'export_depth_text_mp4', '_3d_text.mp4');

  final String value;
  final String labelKey;
  final String suffix;
  const ExportMode(this.value, this.labelKey, this.suffix);

  String localizedLabel(AppI18n i18n) => i18n.t(labelKey);
}

enum PreviewMode {
  autoExport('auto_export', 'pill_auto_export', 'drop_preview_auto_export'),
  lumaMatte('luma', 'pill_luma_matte', 'drop_preview_luma_matte'),
  checkerboard('checkerboard', 'pill_checkerboard', 'drop_preview_checkerboard'),
  greenScreen('greenscreen', 'pill_greenscreen', 'drop_preview_greenscreen'),
  depthTextDemo('depth_text', 'pill_depth_text', 'drop_preview_depth_text');

  final String value;
  final String pillKey;
  final String dropdownKey;
  const PreviewMode(this.value, this.pillKey, this.dropdownKey);

  String localizedPill(AppI18n i18n) => i18n.t(pillKey);
  String localizedDropdown(AppI18n i18n) => i18n.t(dropdownKey);

  PreviewMode resolveEffective(ExportMode exportMode) {
    if (this != PreviewMode.autoExport) return this;
    switch (exportMode) {
      case ExportMode.lumaMatteMp4:
        return PreviewMode.lumaMatte;
      case ExportMode.proresAlphaMov:
      case ExportMode.vp9AlphaWebm:
        return PreviewMode.checkerboard;
      case ExportMode.greenScreenMp4:
        return PreviewMode.greenScreen;
      case ExportMode.depthTextMp4:
        return PreviewMode.depthTextDemo;
    }
  }

  String localizedRightPanelHeader(AppI18n i18n) {
    switch (this) {
      case PreviewMode.lumaMatte:
        return i18n.t('right_title_luma');
      case PreviewMode.checkerboard:
        return i18n.t('right_title_checkerboard');
      case PreviewMode.greenScreen:
        return i18n.t('right_title_greenscreen');
      case PreviewMode.depthTextDemo:
        return i18n.t('right_title_depth_text');
      case PreviewMode.autoExport:
        return i18n.t('right_title_checkerboard');
    }
  }
}

class MattingConfig {
  final ExportMode exportMode;
  final PreviewMode previewMode;
  final double downsampleRatio;
  final int tolerancePct;
  final int featherPx;
  final int chokePx;
  final int thresholdLow;
  final int thresholdHigh;
  final double temporalSmooth;
  final String backdropText;
  final int textYPct;
  final int textScalePct;
  final String textColorHex;
  final String outputDir;

  const MattingConfig({
    this.exportMode = ExportMode.lumaMatteMp4,
    this.previewMode = PreviewMode.autoExport,
    this.downsampleRatio = 0.35,
    this.tolerancePct = 50,
    this.featherPx = 3,
    this.chokePx = 0,
    this.thresholdLow = 12,
    this.thresholdHigh = 242,
    this.temporalSmooth = 0.20,
    this.backdropText = 'SAMPLE TEXT',
    this.textYPct = 40,
    this.textScalePct = 100,
    this.textColorHex = '#F0C05A',
    this.outputDir = '',
  });

  MattingConfig copyWith({
    ExportMode? exportMode,
    PreviewMode? previewMode,
    double? downsampleRatio,
    int? tolerancePct,
    int? featherPx,
    int? chokePx,
    int? thresholdLow,
    int? thresholdHigh,
    double? temporalSmooth,
    String? backdropText,
    int? textYPct,
    int? textScalePct,
    String? textColorHex,
    String? outputDir,
  }) {
    return MattingConfig(
      exportMode: exportMode ?? this.exportMode,
      previewMode: previewMode ?? this.previewMode,
      downsampleRatio: downsampleRatio ?? this.downsampleRatio,
      tolerancePct: tolerancePct ?? this.tolerancePct,
      featherPx: featherPx ?? this.featherPx,
      chokePx: chokePx ?? this.chokePx,
      thresholdLow: thresholdLow ?? this.thresholdLow,
      thresholdHigh: thresholdHigh ?? this.thresholdHigh,
      temporalSmooth: temporalSmooth ?? this.temporalSmooth,
      backdropText: backdropText ?? this.backdropText,
      textYPct: textYPct ?? this.textYPct,
      textScalePct: textScalePct ?? this.textScalePct,
      textColorHex: textColorHex ?? this.textColorHex,
      outputDir: outputDir ?? this.outputDir,
    );
  }

  Map<String, dynamic> toJson() => {
        'export_mode': exportMode.value,
        'preview_mode': previewMode.value,
        'downsample_ratio': downsampleRatio,
        'tolerance_pct': tolerancePct,
        'feather_px': featherPx,
        'choke_px': chokePx,
        'threshold_low': thresholdLow,
        'threshold_high': thresholdHigh,
        'temporal_smooth': temporalSmooth,
        'backdrop_text': backdropText,
        'text_y_pct': textYPct,
        'text_scale_pct': textScalePct,
        'text_color_hex': textColorHex,
        'output_dir': outputDir,
      };
}

class VideoMetadata {
  final String path;
  final String name;
  final String parentDir;
  final int width;
  final int height;
  final double fps;
  final int totalFrames;
  final double durationSec;
  final int sampleIdx;

  const VideoMetadata({
    required this.path,
    required this.name,
    required this.parentDir,
    required this.width,
    required this.height,
    required this.fps,
    required this.totalFrames,
    required this.durationSec,
    required this.sampleIdx,
  });
}

class SystemDiagnostics {
  final String os;
  final String accelerator;
  final String ffmpeg;
  final bool ready;

  const SystemDiagnostics({
    this.os = '...',
    this.accelerator = 'ONNX Runtime',
    this.ffmpeg = 'FFmpeg Pipe',
    this.ready = false,
  });
}

class FramePair {
  final Uint8List? originalBytes;
  final Uint8List? previewBytes;

  const FramePair({this.originalBytes, this.previewBytes});
}
