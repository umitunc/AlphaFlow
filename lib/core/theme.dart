import 'package:flutter/material.dart';

class AlphaFlowPalette {
  final bool isDark;
  final Color canvasBaseTop;
  final Color canvasBaseBottom;
  final Color orbCyan;
  final Color orbIndigo;
  final Color orbGold;

  final Color glassFillStart;
  final Color glassFillEnd;
  final Color glassElevatedFill;
  final Color glassBorder;
  final Color glassInnerHighlight;
  final Color glassShadow;

  final Color textPrimary;
  final Color textSecondary;
  final Color textMuted;

  final Color accentCyan;
  final Color accentIndigo;
  final Color accentGold;
  final Color accentGoldBright;
  final Color viewportBackground;

  const AlphaFlowPalette({
    required this.isDark,
    required this.canvasBaseTop,
    required this.canvasBaseBottom,
    required this.orbCyan,
    required this.orbIndigo,
    required this.orbGold,
    required this.glassFillStart,
    required this.glassFillEnd,
    required this.glassElevatedFill,
    required this.glassBorder,
    required this.glassInnerHighlight,
    required this.glassShadow,
    required this.textPrimary,
    required this.textSecondary,
    required this.textMuted,
    required this.accentCyan,
    required this.accentIndigo,
    required this.accentGold,
    required this.accentGoldBright,
    required this.viewportBackground,
  });

  static const AlphaFlowPalette dark = AlphaFlowPalette(
    isDark: true,
    canvasBaseTop: Color(0xFF080B12),
    canvasBaseBottom: Color(0xFF0E1320),
    orbCyan: Color(0x3306B6D4),
    orbIndigo: Color(0x2E6366F1),
    orbGold: Color(0x22D5A853),
    glassFillStart: Color(0xA6192030),
    glassFillEnd: Color(0x80121724),
    glassElevatedFill: Color(0xB81E2638),
    glassBorder: Color(0x26FFFFFF),
    glassInnerHighlight: Color(0x18FFFFFF),
    glassShadow: Color(0x55000000),
    textPrimary: Color(0xFFF8FAFC),
    textSecondary: Color(0xFF94A3B8),
    textMuted: Color(0xFF64748B),
    accentCyan: Color(0xFF22D3EE),
    accentIndigo: Color(0xFF6366F1),
    accentGold: Color(0xFFE2B45A),
    accentGoldBright: Color(0xFFF7CE74),
    viewportBackground: Color(0xCC07090E),
  );

  static const AlphaFlowPalette light = AlphaFlowPalette(
    isDark: false,
    canvasBaseTop: Color(0xFFEEF3FB),
    canvasBaseBottom: Color(0xFFE0E8F6),
    orbCyan: Color(0x4038BDF8),
    orbIndigo: Color(0x33818CF8),
    orbGold: Color(0x2BF59E0B),
    glassFillStart: Color(0xCCFFFFFF),
    glassFillEnd: Color(0x99F8FAFC),
    glassElevatedFill: Color(0xD9FFFFFF),
    glassBorder: Color(0xB3FFFFFF),
    glassInnerHighlight: Color(0xCCFFFFFF),
    glassShadow: Color(0x180F172A),
    textPrimary: Color(0xFF0F172A),
    textSecondary: Color(0xFF475569),
    textMuted: Color(0xFF64748B),
    accentCyan: Color(0xFF0284C7),
    accentIndigo: Color(0xFF4F46E5),
    accentGold: Color(0xFFB47814),
    accentGoldBright: Color(0xFFD99B26),
    viewportBackground: Color(0xE6111622),
  );

  static AlphaFlowPalette of(BuildContext context) {
    final brightness = Theme.of(context).brightness;
    return brightness == Brightness.dark ? dark : light;
  }
}

class AlphaFlowTheme {
  static ThemeData buildTheme(Brightness brightness) {
    final isDark = brightness == Brightness.dark;
    final p = isDark ? AlphaFlowPalette.dark : AlphaFlowPalette.light;

    return ThemeData(
      useMaterial3: true,
      brightness: brightness,
      scaffoldBackgroundColor: Colors.transparent,
      colorScheme: ColorScheme(
        brightness: brightness,
        primary: p.accentCyan,
        onPrimary: isDark ? const Color(0xFF080B12) : Colors.white,
        secondary: p.accentGold,
        onSecondary: isDark ? const Color(0xFF080B12) : Colors.white,
        error: const Color(0xFFEF4444),
        onError: Colors.white,
        surface: p.glassElevatedFill,
        onSurface: p.textPrimary,
      ),
      sliderTheme: SliderThemeData(
        activeTrackColor: p.accentCyan,
        inactiveTrackColor: isDark
            ? const Color(0x55334155)
            : const Color(0x5594A3B8),
        thumbColor: p.accentCyan,
        overlayColor: p.accentCyan.withValues(alpha: 0.16),
        trackHeight: 4.5,
        thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 7.0),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: p.glassElevatedFill,
        isDense: true,
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        hintStyle: TextStyle(color: p.textMuted, fontSize: 12.5),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: BorderSide(color: p.glassBorder),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: BorderSide(color: p.glassBorder),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: BorderSide(color: p.accentCyan, width: 1.5),
        ),
      ),
    );
  }

  static Color hexToColor(String hex) {
    final clean = hex.replaceAll('#', '').trim();
    if (clean.length == 6) {
      return Color(int.parse('FF$clean', radix: 16));
    }
    return const Color(0xFFF0C05A);
  }
}
