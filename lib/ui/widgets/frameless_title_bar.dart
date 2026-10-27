import 'package:flutter/material.dart';
import '../../core/localization.dart';
import '../../core/theme.dart';
import '../../services/window_control_service.dart';
import 'glass_box.dart';

class FramelessTitleBar extends StatefulWidget {
  final ThemeMode themeMode;
  final ValueChanged<ThemeMode> onThemeModeChanged;
  final String langCode;
  final ValueChanged<String> onLangCodeChanged;

  const FramelessTitleBar({
    super.key,
    required this.themeMode,
    required this.onThemeModeChanged,
    required this.langCode,
    required this.onLangCodeChanged,
  });

  @override
  State<FramelessTitleBar> createState() => _FramelessTitleBarState();
}

class _FramelessTitleBarState extends State<FramelessTitleBar> {
  bool _isMaximized = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      WindowControlService.ensureFrameless();
    });
  }

  Future<void> _toggleMax() async {
    final max = await WindowControlService.toggleMaximize();
    if (mounted) {
      setState(() => _isMaximized = max);
    }
  }

  @override
  Widget build(BuildContext context) {
    final p = AlphaFlowPalette.of(context);
    final i18n = AppI18n.of(context);
    final isDark = p.isDark;

    return GlassCard(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      borderRadius: 12,
      blurSigma: 24,
      child: Row(
        children: [
          // Sürüklenebilir Başlık Alanı (Büyütülmüş Apple HIG Logo + Başlık)
          Expanded(
            child: GestureDetector(
              behavior: HitTestBehavior.opaque,
              onPanStart: (_) => WindowControlService.beginDrag(),
              onPanUpdate: (_) => WindowControlService.updateDrag(),
              onPanEnd: (_) => WindowControlService.endDrag(),
              onPanCancel: WindowControlService.endDrag,
              onDoubleTap: _toggleMax,
              child: Row(
                children: [
                  Image.asset(
                    'assets/icons/alphaflow_logo_transparent.png',
                    width: 38,
                    height: 38,
                    fit: BoxFit.contain,
                  ),
                  const SizedBox(width: 10),
                  Text(
                    i18n.t('app_title'),
                    style: TextStyle(
                      fontSize: 15.5,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 0.25,
                      color: p.textPrimary,
                    ),
                  ),
                ],
              ),
            ),
          ),

          // TR / EN Dil Seçici Glass Toggle
          Container(
            padding: const EdgeInsets.all(2),
            decoration: BoxDecoration(
              color: p.glassElevatedFill,
              borderRadius: BorderRadius.circular(18),
              border: Border.all(color: p.glassBorder),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                _PillSwitchChip(
                  icon: Icons.language_rounded,
                  label: 'TR',
                  active: widget.langCode == 'tr',
                  onTap: () => widget.onLangCodeChanged('tr'),
                ),
                _PillSwitchChip(
                  icon: null,
                  label: 'EN',
                  active: widget.langCode == 'en',
                  onTap: () => widget.onLangCodeChanged('en'),
                ),
              ],
            ),
          ),
          const SizedBox(width: 6),

          // Dark / Light Mode Segmented Glass Toggle
          Container(
            padding: const EdgeInsets.all(2),
            decoration: BoxDecoration(
              color: p.glassElevatedFill,
              borderRadius: BorderRadius.circular(18),
              border: Border.all(color: p.glassBorder),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                _PillSwitchChip(
                  icon: Icons.dark_mode_rounded,
                  label: i18n.t('theme_dark'),
                  active: isDark,
                  onTap: () => widget.onThemeModeChanged(ThemeMode.dark),
                ),
                _PillSwitchChip(
                  icon: Icons.light_mode_rounded,
                  label: i18n.t('theme_light'),
                  active: !isDark,
                  onTap: () => widget.onThemeModeChanged(ThemeMode.light),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),

          // Pencere Kontrol Butonları
          _WindowControlBtn(
            icon: Icons.remove_rounded,
            tooltip: i18n.t('tooltip_minimize'),
            onTap: WindowControlService.minimize,
          ),
          const SizedBox(width: 2),
          _WindowControlBtn(
            icon: _isMaximized
                ? Icons.filter_none_rounded
                : Icons.crop_square_rounded,
            tooltip: _isMaximized
                ? i18n.t('tooltip_restore')
                : i18n.t('tooltip_maximize'),
            onTap: _toggleMax,
          ),
          const SizedBox(width: 2),
          _WindowControlBtn(
            icon: Icons.close_rounded,
            tooltip: i18n.t('tooltip_close'),
            isClose: true,
            onTap: WindowControlService.close,
          ),
        ],
      ),
    );
  }
}

class _PillSwitchChip extends StatelessWidget {
  final IconData? icon;
  final String label;
  final bool active;
  final VoidCallback onTap;

  const _PillSwitchChip({
    required this.icon,
    required this.label,
    required this.active,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final p = AlphaFlowPalette.of(context);
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
        decoration: BoxDecoration(
          color: active
              ? p.accentCyan.withValues(alpha: 0.22)
              : Colors.transparent,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: active
                ? p.accentCyan.withValues(alpha: 0.55)
                : Colors.transparent,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (icon != null) ...[
              Icon(
                icon,
                size: 12.5,
                color: active ? p.accentCyan : p.textSecondary,
              ),
              const SizedBox(width: 3),
            ],
            Text(
              label,
              style: TextStyle(
                fontSize: 11,
                fontWeight: active ? FontWeight.w700 : FontWeight.w500,
                color: active ? p.textPrimary : p.textSecondary,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _WindowControlBtn extends StatefulWidget {
  final IconData icon;
  final String tooltip;
  final bool isClose;
  final VoidCallback onTap;

  const _WindowControlBtn({
    required this.icon,
    required this.tooltip,
    required this.onTap,
    this.isClose = false,
  });

  @override
  State<_WindowControlBtn> createState() => _WindowControlBtnState();
}

class _WindowControlBtnState extends State<_WindowControlBtn> {
  bool _hover = false;

  @override
  Widget build(BuildContext context) {
    final p = AlphaFlowPalette.of(context);
    final bgColor = _hover
        ? (widget.isClose
            ? const Color(0xFFEF4444)
            : p.textPrimary.withValues(alpha: 0.12))
        : Colors.transparent;
    final iconColor = _hover && widget.isClose ? Colors.white : p.textPrimary;

    return Tooltip(
      message: widget.tooltip,
      waitDuration: const Duration(milliseconds: 450),
      child: MouseRegion(
        cursor: SystemMouseCursors.click,
        onEnter: (_) => setState(() => _hover = true),
        onExit: (_) => setState(() => _hover = false),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: widget.onTap,
            borderRadius: BorderRadius.circular(7),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 120),
              width: 32,
              height: 28,
              decoration: BoxDecoration(
                color: bgColor,
                borderRadius: BorderRadius.circular(7),
              ),
              child: Icon(widget.icon, size: 16, color: iconColor),
            ),
          ),
        ),
      ),
    );
  }
}

/// Çerçevesiz (Frameless) pencerenin 4 kenarından ve 4 köşesinden
/// fare ile tutulup yeniden boyutlandırılmasını (8-yönlü resize) sağlayan sarmalayıcı.
class FramelessResizeWrapper extends StatelessWidget {
  final Widget child;
  static const double _edgeThickness = 6.0;
  static const double _cornerSize = 14.0;

  const FramelessResizeWrapper({
    super.key,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    return Stack(
      fit: StackFit.expand,
      children: [
        child,
        // Sol Kenar
        const Positioned(
          left: 0,
          top: _cornerSize,
          bottom: _cornerSize,
          width: _edgeThickness,
          child: _ResizeHandleZone(
            edge: ResizeEdge.left,
            cursor: SystemMouseCursors.resizeLeftRight,
          ),
        ),
        // Sağ Kenar
        const Positioned(
          right: 0,
          top: _cornerSize,
          bottom: _cornerSize,
          width: _edgeThickness,
          child: _ResizeHandleZone(
            edge: ResizeEdge.right,
            cursor: SystemMouseCursors.resizeLeftRight,
          ),
        ),
        // Üst Kenar
        const Positioned(
          top: 0,
          left: _cornerSize,
          right: _cornerSize,
          height: _edgeThickness,
          child: _ResizeHandleZone(
            edge: ResizeEdge.top,
            cursor: SystemMouseCursors.resizeUpDown,
          ),
        ),
        // Alt Kenar
        const Positioned(
          bottom: 0,
          left: _cornerSize,
          right: _cornerSize,
          height: _edgeThickness,
          child: _ResizeHandleZone(
            edge: ResizeEdge.bottom,
            cursor: SystemMouseCursors.resizeUpDown,
          ),
        ),
        // Sol-Üst Köşe
        const Positioned(
          top: 0,
          left: 0,
          width: _cornerSize,
          height: _cornerSize,
          child: _ResizeHandleZone(
            edge: ResizeEdge.topLeft,
            cursor: SystemMouseCursors.resizeUpLeftDownRight,
          ),
        ),
        // Sağ-Üst Köşe
        const Positioned(
          top: 0,
          right: 0,
          width: _cornerSize,
          height: _cornerSize,
          child: _ResizeHandleZone(
            edge: ResizeEdge.topRight,
            cursor: SystemMouseCursors.resizeUpRightDownLeft,
          ),
        ),
        // Sol-Alt Köşe
        const Positioned(
          bottom: 0,
          left: 0,
          width: _cornerSize,
          height: _cornerSize,
          child: _ResizeHandleZone(
            edge: ResizeEdge.bottomLeft,
            cursor: SystemMouseCursors.resizeUpRightDownLeft,
          ),
        ),
        // Sağ-Alt Köşe
        const Positioned(
          bottom: 0,
          right: 0,
          width: _cornerSize + 2,
          height: _cornerSize + 2,
          child: _ResizeHandleZone(
            edge: ResizeEdge.bottomRight,
            cursor: SystemMouseCursors.resizeUpLeftDownRight,
          ),
        ),
      ],
    );
  }
}

class _ResizeHandleZone extends StatelessWidget {
  final ResizeEdge edge;
  final MouseCursor cursor;

  const _ResizeHandleZone({
    required this.edge,
    required this.cursor,
  });

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      cursor: cursor,
      child: GestureDetector(
        behavior: HitTestBehavior.translucent,
        onPanStart: (_) => WindowControlService.beginResize(edge),
        onPanUpdate: (_) => WindowControlService.updateResize(),
        onPanEnd: (_) => WindowControlService.endResize(),
        onPanCancel: WindowControlService.endResize,
        child: const SizedBox.expand(),
      ),
    );
  }
}
