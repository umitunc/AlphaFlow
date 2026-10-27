import 'dart:ui';
import 'package:flutter/material.dart';
import '../../core/theme.dart';

/// Apple HIG Frosted Glassmorphic Konteyner Bileşeni
class GlassCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final double borderRadius;
  final double blurSigma;
  final Color? borderColor;
  final double borderWidth;

  const GlassCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(12),
    this.borderRadius = 14,
    this.blurSigma = 22,
    this.borderColor,
    this.borderWidth = 1.1,
  });

  @override
  Widget build(BuildContext context) {
    final p = AlphaFlowPalette.of(context);

    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(borderRadius),
        boxShadow: [
          BoxShadow(
            color: p.glassShadow,
            blurRadius: 18,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(borderRadius),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: blurSigma, sigmaY: blurSigma),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            padding: padding,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [p.glassFillStart, p.glassFillEnd],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(borderRadius),
              border: Border.all(
                color: borderColor ?? p.glassBorder,
                width: borderWidth,
              ),
            ),
            child: child,
          ),
        ),
      ),
    );
  }
}

/// Uygulama arka planında cam panellerin kıracağı (refract edeceği) ambiyans ışık küreleri
class GlassmorphicAmbientCanvas extends StatelessWidget {
  final Widget child;

  const GlassmorphicAmbientCanvas({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    final p = AlphaFlowPalette.of(context);

    return AnimatedContainer(
      duration: const Duration(milliseconds: 260),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [p.canvasBaseTop, p.canvasBaseBottom],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      ),
      child: Stack(
        fit: StackFit.expand,
        children: [
          // Sol-Üst Siber Camgöbeği Işık Küresi
          Positioned(
            top: -110,
            left: -90,
            child: _AmbientGlowOrb(color: p.orbCyan, size: 420),
          ),
          // Sağ-Üst İndigo/Mor Işık Küresi
          Positioned(
            top: -80,
            right: -100,
            child: _AmbientGlowOrb(color: p.orbIndigo, size: 460),
          ),
          // Alt-Merkez Kehribar/Altın Işık Küresi
          Positioned(
            bottom: -140,
            left: 280,
            child: _AmbientGlowOrb(color: p.orbGold, size: 440),
          ),
          child,
        ],
      ),
    );
  }
}

class _AmbientGlowOrb extends StatelessWidget {
  final Color color;
  final double size;

  const _AmbientGlowOrb({required this.color, required this.size});

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          gradient: RadialGradient(
            colors: [
              color,
              color.withValues(alpha: 0.0),
            ],
          ),
        ),
      ),
    );
  }
}

