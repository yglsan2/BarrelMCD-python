import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// Association MCD : **ovale** (ellipse) — forme ovale, plus ronde qu’un rectangle.
/// Les bras (points de connexion) sont sur le bord de l’ovale.
class AssociationOval extends StatelessWidget {
  const AssociationOval({
    super.key,
    required this.name,
    this.selected = false,
    this.onSecondaryTap,
    this.onSize,
    this.fixedDiameter,
    this.armAngles,
  });

  /// Diamètre minimum du cercle visible (association) — bien lisible, taille confortable.
  static const double minDiameter = 220;
  /// Diamètre maximum autorisé pour le redimensionnement.
  static const double maxDiameter = 550;
  static const double padding = 16;
  /// Cercle invisible : même taille que le visible (rayon identique). Bras = point sur le bord du cercle.
  static const double armExtensionLength = 0;

  final String name;
  final bool selected;
  final VoidCallback? onSecondaryTap;
  /// Appelé avec (diameter, diameter) pour un cercle.
  final void Function(double width, double height)? onSize;
  /// Si défini, le cercle a cette taille (pour aligner avec les bras).
  final double? fixedDiameter;
  /// Angles des bras en degrés (0 = droite, 180 = gauche). Dessinés comme radii centrés sur le cercle.
  final List<double>? armAngles;

  @override
  Widget build(BuildContext context) {
    final displayName = name.isEmpty ? 'Association' : name;
    return LayoutBuilder(
      builder: (ctx, constraints) {
        final textPainter = TextPainter(
          text: TextSpan(
            text: displayName,
            style: const TextStyle(
              color: AppTheme.textPrimary,
              fontSize: 12,
              fontWeight: FontWeight.bold,
            ),
          ),
          textDirection: TextDirection.ltr,
          maxLines: 3,
        )..layout(maxWidth: 220);

        final contentW = textPainter.width + padding * 2;
        final contentH = textPainter.height + padding * 2;
        final computedDiameter = math.max(minDiameter, math.max(contentW, contentH)).clamp(minDiameter, maxDiameter);
        final diameter = fixedDiameter != null && fixedDiameter! >= minDiameter
            ? fixedDiameter!.clamp(minDiameter, maxDiameter)
            : computedDiameter;

        if (fixedDiameter == null) {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            onSize?.call(computedDiameter, computedDiameter);
          });
        }

        return GestureDetector(
          onSecondaryTap: onSecondaryTap,
          child: CustomPaint(
            size: Size(diameter, diameter),
            painter: _AssociationCircleAndArmsPainter(
              selected: selected,
              armAngles: armAngles ?? const [0.0, 90.0, 180.0, 270.0],
            ),
            child: Center(
              child: Padding(
                padding: const EdgeInsets.all(padding),
                child: Text(
                  displayName,
                  textAlign: TextAlign.center,
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: AppTheme.textPrimary,
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}

/// Ovale (ellipse) + bras : forme OVALE allongée (moins ronde, plus ovale).
class _AssociationCircleAndArmsPainter extends CustomPainter {
  _AssociationCircleAndArmsPainter({this.selected = false, this.armAngles = const [0.0, 90.0, 180.0, 270.0]});
  final bool selected;
  final List<double> armAngles;

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    // Ovale Barrel : ellipse bien allongée horizontalement (largeur > hauteur, ratio ~0.68).
    final radiusX = size.width / 2;
    final radiusY = size.height / 2 * _ovalRadiusYRatio;
    final rect = Rect.fromCenter(center: center, width: radiusX * 2, height: radiusY * 2);
    canvas.drawOval(
      rect,
      Paint()
        ..color = AppTheme.associationBg
        ..style = PaintingStyle.fill,
    );
    canvas.drawOval(
      rect,
      Paint()
        ..color = selected ? AppTheme.associationSelected : AppTheme.associationBorder
        ..style = PaintingStyle.stroke
        ..strokeWidth = selected ? 2.5 : 1.5,
    );
    // Bras : du centre vers le bord de l'ellipse (point à l'angle donné).
    final armPaint = Paint()
      ..color = AppTheme.primary
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round
      ..style = PaintingStyle.stroke;
    for (final angleDeg in armAngles) {
      final rad = angleDeg * math.pi / 180;
      final to = Offset(
        center.dx + radiusX * math.cos(rad),
        center.dy + radiusY * math.sin(rad),
      );
      canvas.drawLine(center, to, armPaint);
    }
  }

  @override
  bool shouldRepaint(covariant _AssociationCircleAndArmsPainter oldDelegate) =>
      oldDelegate.selected != selected || oldDelegate.armAngles != armAngles;
}

/// Rapport hauteur/largeur de l'ovale (OVALE allongé, moins rond).
const double _ovalRadiusYRatio = 0.68;

/// Position de la pointe d'un bras sur l'**ellipse** (ovale type Barrel) ou le cercle.
Offset armPositionFromCenter(Offset center, double angleDegrees, double circleDiameter, double unusedHeight) {
  final radiusX = circleDiameter / 2 + AssociationOval.armExtensionLength;
  final radiusY = radiusX * _ovalRadiusYRatio;
  final rad = angleDegrees * math.pi / 180;
  return Offset(
    center.dx + radiusX * math.cos(rad),
    center.dy + radiusY * math.sin(rad),
  );
}
