import 'package:flutter_test/flutter_test.dart';
import 'package:alphaflow_studio/core/localization.dart';
import 'package:alphaflow_studio/core/models.dart';
import 'package:alphaflow_studio/services/window_control_service.dart';

void main() {
  test('MattingConfig default backdropText & PreviewMode resolution test', () {
    const cfg = MattingConfig();
    expect(cfg.backdropText, 'SAMPLE TEXT');
    expect(cfg.exportMode, ExportMode.lumaMatteMp4);
    expect(
      cfg.previewMode.resolveEffective(ExportMode.proresAlphaMov),
      PreviewMode.checkerboard,
    );
    expect(
      cfg.previewMode.resolveEffective(ExportMode.depthTextMp4),
      PreviewMode.depthTextDemo,
    );
  });

  test('AppI18n JSON interpolation test', () {
    const i18n = AppI18n(
      langCode: 'tr',
      strings: {'label_feather': 'Kenar Yumuşatma (Feather): {px} px'},
    );
    expect(
      i18n.t('label_feather', {'px': '3'}),
      'Kenar Yumuşatma (Feather): 3 px',
    );
  });

  test('WindowControlService Win32 FFI bindings resolve cleanly', () {
    final hwnd = WindowControlService.getWindowHandle();
    expect(hwnd, isA<int>());
    WindowControlService.ensureFrameless();
  });
}
