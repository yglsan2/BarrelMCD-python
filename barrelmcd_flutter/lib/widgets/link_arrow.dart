import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../utils/link_geometry.dart';

/// Dessine un lien entre deux points (association ↔ entité).
/// Deux styles : Barrel (mode simple, ligne/polyline) et Barrel mode courbe (courbe Bézier).
class LinkArrow {
  static const double _capsuleWidth = 44;
  static const double _capsuleHeight = 24;
  static const double _capsuleOffset = 28;

  /// Boîtes cardinalités : le long du segment (marge de sécurité) puis décalées perpendiculairement.
  /// Rattachement des textes de part et d'autre de l'arc.
  static const double cardinalityBoxWidth = 40.0;
  static const double cardinalityBoxHeight = 22.0;
  /// Distance le long du lien depuis chaque extrémité (évite que la cardinalité rentre dans la forme).
  static const double cardinalityAlongOffset = 44.0;
  /// Décalage perpendiculaire : cardinalité assoc d'un côté (+norm), cardinalité entité de l'autre (-norm).
  static const double cardinalityPerpOffset = 24.0;

  /// Centres des boîtes cardinalités : sur le segment à [cardinalityAlongOffset] px de chaque bout, puis décal perp.
  static ({Offset assocCenter, Offset entityCenter}) cardinalityBoxCenters(Offset from, Offset to) {
    final dx = to.dx - from.dx;
    final dy = to.dy - from.dy;
    final dist = math.sqrt(dx * dx + dy * dy);
    if (dist < 1) return (assocCenter: from, entityCenter: to);
    final ux = dx / dist;
    final uy = dy / dist;
    final normX = uy;
    final normY = -ux;
    return (
      assocCenter: Offset(from.dx + cardinalityAlongOffset * ux + cardinalityPerpOffset * normX, from.dy + cardinalityAlongOffset * uy + cardinalityPerpOffset * normY),
      entityCenter: Offset(to.dx - cardinalityAlongOffset * ux - cardinalityPerpOffset * normX, to.dy - cardinalityAlongOffset * uy - cardinalityPerpOffset * normY),
    );
  }

  static void paint(Canvas canvas, {required Offset from, required Offset to, required String cardinality, bool selected = false}) {
    paintWithStyle(
      canvas,
      from: from,
      to: to,
      cardinalityEntity: cardinality,
      cardinalityAssoc: cardinality,
      associationArmAngleDeg: 0,
      selected: selected,
      barrelStyle: true,
    );
  }

  /// [barrelStyle] true = style Barrel (ligne droite ou polyline, cardinalités en texte simple).
  /// [barrelStyle] false = style Barrel courbe (courbe Bézier).
  /// [controlPoints] points intermédiaires pour déformer le trait (polyline from → cp1 → … → to).
  /// [arrowReversed] true = flèche au départ au lieu de l'arrivée (sens inverse).
  /// [strokeWidth] épaisseur du trait (1–6).
  /// [arrowHead] forme de la pointe : 'arrow', 'diamond', 'block', 'none'.
  /// [startCap] forme du départ : 'dot', 'diamond', 'square', 'none'.
  /// [arrowStartMargin] marge au début du trait (px). Défaut [kArrowStartMargin].
  static void paintWithCapsules(Canvas canvas, {
    required Offset from,
    required Offset to,
    required String cardinalityEntity,
    required String cardinalityAssoc,
    required double associationArmAngleDeg,
    bool selected = false,
    bool curved = false,
    List<Offset> controlPoints = const [],
    bool arrowReversed = false,
    double strokeWidth = 2.5,
    String arrowHead = 'arrow',
    String startCap = 'dot',
    double? arrowStartMargin,
  }) {
    paintWithStyle(
      canvas,
      from: from,
      to: to,
      cardinalityEntity: cardinalityEntity,
      cardinalityAssoc: cardinalityAssoc,
      associationArmAngleDeg: associationArmAngleDeg,
      selected: selected,
      barrelStyle: !curved,
      controlPoints: controlPoints,
      arrowReversed: arrowReversed,
      strokeWidth: strokeWidth,
      arrowHead: arrowHead,
      startCap: startCap,
      arrowStartMargin: arrowStartMargin,
    );
  }

  /// Style Barrel : ligne droite (ou polyline si controlPoints) ; cardinalités à côté.
  /// Style Barrel courbe : courbe Bézier.
  /// [arrowReversed] flèche au départ (sens inverse). [strokeWidth] épaisseur du trait.
  /// [arrowHead] 'arrow' | 'diamond' | 'block' | 'none'. [startCap] 'dot' | 'diamond' | 'square' | 'none'.
  /// [arrowStartMargin] marge au début du trait (px). Défaut [kArrowStartMargin].
  static void paintWithStyle(Canvas canvas, {
    required Offset from,
    required Offset to,
    required String cardinalityEntity,
    required String cardinalityAssoc,
    required double associationArmAngleDeg,
    bool selected = false,
    bool barrelStyle = false,
    List<Offset> controlPoints = const [],
    bool arrowReversed = false,
    double strokeWidth = 2.5,
    String arrowHead = 'arrow',
    String startCap = 'dot',
    double? arrowStartMargin,
  }) {
    final marginStart = arrowStartMargin ?? kArrowStartMargin;
    final dx = to.dx - from.dx;
    final dy = to.dy - from.dy;
    final dist = math.sqrt(dx * dx + dy * dy);
    if (dist < 1 && controlPoints.isEmpty) return;

    final ux = dist >= 1 ? dx / dist : 1.0;
    final uy = dist >= 1 ? dy / dist : 0.0;
    // Si le segment est plus court que la marge de départ, partir de [from] pour ne pas inverser le trait.
    final startOffset = dist >= marginStart ? marginStart : 0.0;
    final start = Offset(from.dx + ux * startOffset, from.dy + uy * startOffset);
    final end = to;

    if (barrelStyle) {
      _paintBarrelStyle(canvas, start: start, end: end, from: from, to: to, ux: ux, uy: uy, dist: dist,
          cardinalityEntity: cardinalityEntity, cardinalityAssoc: cardinalityAssoc, selected: selected,
          controlPoints: controlPoints, arrowReversed: arrowReversed, strokeWidth: strokeWidth,
          arrowHead: arrowHead, startCap: startCap);
    } else {
      _paintBarrelCurvedStyle(canvas, start: start, end: end, from: from, to: to, ux: ux, uy: uy, dist: dist,
          cardinalityEntity: cardinalityEntity, cardinalityAssoc: cardinalityAssoc,
          associationArmAngleDeg: associationArmAngleDeg, selected: selected);
    }
  }

  /// Style Barrel : trait droit ou polyline. Début du trait à [start] (marge), fin à [end] (marge) — comme ça la pointe ne rentre jamais dans la forme.
  static void _paintBarrelStyle(Canvas canvas, {
    required Offset start,
    required Offset end,
    required Offset from,
    required Offset to,
    required double ux,
    required double uy,
    required String cardinalityEntity,
    required String cardinalityAssoc,
    required bool selected,
    List<Offset> controlPoints = const [],
    bool arrowReversed = false,
    double strokeWidth = 2.5,
    double dist = 1.0,
    String arrowHead = 'arrow',
    String startCap = 'dot',
  }) {
    final effectiveStroke = selected ? 3.0 : strokeWidth.clamp(1.0, 6.0);
    final paint = Paint()
      ..color = selected ? AppTheme.primary : AppTheme.primary.withValues(alpha: 0.9)
      ..strokeWidth = effectiveStroke
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round;

    if (controlPoints.isEmpty) {
      canvas.drawLine(start, end, paint);
    } else {
      final path = Path()..moveTo(start.dx, start.dy);
      for (final p in controlPoints) path.lineTo(p.dx, p.dy);
      path.lineTo(end.dx, end.dy);
      canvas.drawPath(path, paint);
    }

    final size = selected ? 10.0 : 8.0;
    final tipPoint = arrowReversed ? start : end;
    final tipDirX = arrowReversed ? -ux : ux;
    final tipDirY = arrowReversed ? -uy : uy;
    if (arrowHead == 'arrow') {
      _drawChevronAt(canvas, tipPoint, tipDirX, tipDirY, paint.color, size);
    } else if (arrowHead == 'diamond') {
      _drawDiamondAt(canvas, tipPoint, tipDirX, tipDirY, paint.color, size);
    } else if (arrowHead == 'block') {
      _drawBlockAt(canvas, tipPoint, tipDirX, tipDirY, paint.color, size);
    }

    final startCapPoint = arrowReversed ? end : start;
    final startCapDirX = arrowReversed ? ux : -ux;
    final startCapDirY = arrowReversed ? uy : -uy;
    if (startCap == 'dot') {
      final dotRadius = selected ? 10.0 : 4.0;
      final dotPaint = Paint()
        ..color = selected ? AppTheme.primary : AppTheme.textSecondary
        ..style = PaintingStyle.fill;
      canvas.drawCircle(startCapPoint, dotRadius, dotPaint);
      canvas.drawCircle(startCapPoint, dotRadius, Paint()..color = paint.color..style = PaintingStyle.stroke..strokeWidth = selected ? 2 : 1);
    } else if (startCap == 'diamond') {
      _drawDiamondAt(canvas, startCapPoint, startCapDirX, startCapDirY, paint.color, size);
    } else if (startCap == 'square') {
      _drawSquareAt(canvas, startCapPoint, startCapDirX, startCapDirY, paint.color, size);
    }

    final normX = uy;
    final normY = -ux;
    final assocBoxCenter = Offset(from.dx + cardinalityAlongOffset * ux + cardinalityPerpOffset * normX, from.dy + cardinalityAlongOffset * uy + cardinalityPerpOffset * normY);
    final entityBoxCenter = Offset(end.dx - cardinalityAlongOffset * ux - cardinalityPerpOffset * normX, end.dy - cardinalityAlongOffset * uy - cardinalityPerpOffset * normY);
    _drawCardinalityBox(canvas, assocBoxCenter, cardinalityAssoc, selected);
    _drawCardinalityBox(canvas, entityBoxCenter, cardinalityEntity, selected);
  }

  /// Dessine un chevron (flèche) à [point], dans la direction (ux, uy) — pointe à l'arrivée du lien.
  static void _drawChevronAt(Canvas canvas, Offset point, double ux, double uy, Color color, double size) {
    final angle = math.atan2(uy, ux);
    final tip = point;
    final left = Offset(
      tip.dx - size * math.cos(angle) + size * 0.6 * math.sin(angle),
      tip.dy - size * math.sin(angle) - size * 0.6 * math.cos(angle),
    );
    final right = Offset(
      tip.dx - size * math.cos(angle) - size * 0.6 * math.sin(angle),
      tip.dy - size * math.sin(angle) + size * 0.6 * math.cos(angle),
    );
    final path = Path()..moveTo(tip.dx, tip.dy)..lineTo(left.dx, left.dy)..lineTo(right.dx, right.dy)..close();
    canvas.drawPath(path, Paint()..color = color..style = PaintingStyle.fill);
    canvas.drawPath(path, Paint()..color = color..style = PaintingStyle.stroke..strokeWidth = 1.5);
  }

  /// Losange centré sur [point], une pointe dans la direction (ux, uy).
  static void _drawDiamondAt(Canvas canvas, Offset point, double ux, double uy, Color color, double size) {
    final angle = math.atan2(uy, ux);
    final tip = Offset(point.dx + size * math.cos(angle), point.dy + size * math.sin(angle));
    final left = Offset(point.dx + size * math.cos(angle + math.pi / 2), point.dy + size * math.sin(angle + math.pi / 2));
    final tail = Offset(point.dx - size * math.cos(angle), point.dy - size * math.sin(angle));
    final right = Offset(point.dx + size * math.cos(angle - math.pi / 2), point.dy + size * math.sin(angle - math.pi / 2));
    final path = Path()
      ..moveTo(tip.dx, tip.dy)
      ..lineTo(left.dx, left.dy)
      ..lineTo(tail.dx, tail.dy)
      ..lineTo(right.dx, right.dy)
      ..close();
    canvas.drawPath(path, Paint()..color = color..style = PaintingStyle.fill);
    canvas.drawPath(path, Paint()..color = color..style = PaintingStyle.stroke..strokeWidth = 1.5);
  }

  /// Bloc (rectangle perpendiculaire au trait) centré sur [point], direction (ux, uy).
  static void _drawBlockAt(Canvas canvas, Offset point, double ux, double uy, Color color, double size) {
    final halfW = size * 0.8;
    final halfH = size * 0.4;
    final perpX = -uy;
    final perpY = ux;
    final c1 = Offset(point.dx + halfH * ux + halfW * perpX, point.dy + halfH * uy + halfW * perpY);
    final c2 = Offset(point.dx + halfH * ux - halfW * perpX, point.dy + halfH * uy - halfW * perpY);
    final c3 = Offset(point.dx - halfH * ux - halfW * perpX, point.dy - halfH * uy - halfW * perpY);
    final c4 = Offset(point.dx - halfH * ux + halfW * perpX, point.dy - halfH * uy + halfW * perpY);
    final path = Path()..moveTo(c1.dx, c1.dy)..lineTo(c2.dx, c2.dy)..lineTo(c3.dx, c3.dy)..lineTo(c4.dx, c4.dy)..close();
    canvas.drawPath(path, Paint()..color = color..style = PaintingStyle.fill);
    canvas.drawPath(path, Paint()..color = color..style = PaintingStyle.stroke..strokeWidth = 1.5);
  }

  /// Carré centré sur [point], un côté perpendiculaire à la direction (ux, uy).
  static void _drawSquareAt(Canvas canvas, Offset point, double ux, double uy, Color color, double size) {
    final angle = math.atan2(uy, ux);
    final half = size * 0.7;
    final c = math.cos(angle);
    final s = math.sin(angle);
    final path = Path()
      ..moveTo(point.dx + half * c + half * s, point.dy + half * s - half * c)
      ..lineTo(point.dx - half * c + half * s, point.dy - half * s - half * c)
      ..lineTo(point.dx - half * c - half * s, point.dy - half * s + half * c)
      ..lineTo(point.dx + half * c - half * s, point.dy + half * s + half * c)
      ..close();
    canvas.drawPath(path, Paint()..color = color..style = PaintingStyle.fill);
    canvas.drawPath(path, Paint()..color = color..style = PaintingStyle.stroke..strokeWidth = 1.5);
  }

  /// Style Barrel courbe : courbe de Bézier lisse, flèche, capsules pour les cardinalités.
  static void _paintBarrelCurvedStyle(Canvas canvas, {
    required Offset start,
    required Offset end,
    required Offset from,
    required Offset to,
    required double ux,
    required double uy,
    required double dist,
    required String cardinalityEntity,
    required String cardinalityAssoc,
    required double associationArmAngleDeg,
    required bool selected,
  }) {
    const strokeWidth = 2.2;
    final paint = Paint()
      ..color = selected ? AppTheme.primary : AppTheme.primary.withValues(alpha: 0.85)
      ..strokeWidth = selected ? 2.8 : strokeWidth
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    final mid = Offset((start.dx + end.dx) / 2, (start.dy + end.dy) / 2);
    final perpX = -uy;
    final perpY = ux;
    final bulge = dist * 0.18;
    final control = Offset(mid.dx + perpX * bulge, mid.dy + perpY * bulge);
    final path = Path()
      ..moveTo(start.dx, start.dy)
      ..quadraticBezierTo(control.dx, control.dy, end.dx, end.dy);
    canvas.drawPath(path, paint);

    const arrowSize = 9.0;
    final angle = math.atan2(end.dy - control.dy, end.dx - control.dx);
    final arrowTip = Offset(end.dx - arrowSize * math.cos(angle), end.dy - arrowSize * math.sin(angle));
    final arrowLeft = Offset(
      arrowTip.dx + arrowSize * math.cos(angle - 2.5) - arrowSize * 0.5 * math.sin(angle - 2.5),
      arrowTip.dy + arrowSize * math.sin(angle - 2.5) + arrowSize * 0.5 * math.cos(angle - 2.5),
    );
    final arrowRight = Offset(
      arrowTip.dx + arrowSize * math.cos(angle + 2.5) + arrowSize * 0.5 * math.sin(angle + 2.5),
      arrowTip.dy + arrowSize * math.sin(angle + 2.5) - arrowSize * 0.5 * math.cos(angle + 2.5),
    );
    canvas.drawPath(
      Path()..moveTo(end.dx, end.dy)..lineTo(arrowLeft.dx, arrowLeft.dy)..lineTo(arrowRight.dx, arrowRight.dy)..close(),
      Paint()..color = paint.color..style = PaintingStyle.fill,
    );
    canvas.drawPath(
      Path()..moveTo(end.dx, end.dy)..lineTo(arrowLeft.dx, arrowLeft.dy)..lineTo(arrowRight.dx, arrowRight.dy)..close(),
      Paint()..color = paint.color..style = PaintingStyle.stroke..strokeWidth = strokeWidth,
    );

    final normX = uy;
    final normY = -ux;
    final assocBoxCenter = Offset(from.dx + cardinalityAlongOffset * ux + cardinalityPerpOffset * normX, from.dy + cardinalityAlongOffset * uy + cardinalityPerpOffset * normY);
    final entityBoxCenter = Offset(to.dx - cardinalityAlongOffset * ux - cardinalityPerpOffset * normX, to.dy - cardinalityAlongOffset * uy - cardinalityPerpOffset * normY);
    _drawCardinalityBox(canvas, assocBoxCenter, cardinalityAssoc, selected);
    _drawCardinalityBox(canvas, entityBoxCenter, cardinalityEntity, selected);
  }

  /// Boîte à cardinalité bleue (couleur des bras), texte blanc, toujours lisible.
  static void _drawCardinalityBox(Canvas canvas, Offset center, String text, bool selected) {
    final w = cardinalityBoxWidth;
    final h = cardinalityBoxHeight;
    final rect = RRect.fromRectAndRadius(
      Rect.fromCenter(center: center, width: w, height: h),
      const Radius.circular(6),
    );
    canvas.drawRRect(
      rect,
      Paint()
        ..color = selected ? AppTheme.primary : AppTheme.primary.withValues(alpha: 0.95)
        ..style = PaintingStyle.fill,
    );
    canvas.drawRRect(
      rect,
      Paint()
        ..color = AppTheme.textPrimary.withValues(alpha: 0.5)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1,
    );
    final textPainter = TextPainter(
      text: TextSpan(
        text: text,
        style: const TextStyle(
          color: AppTheme.textPrimary,
          fontSize: 11,
          fontWeight: FontWeight.w600,
        ),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    textPainter.paint(
      canvas,
      Offset(center.dx - textPainter.width / 2, center.dy - textPainter.height / 2),
    );
  }

  static void _drawCapsule(Canvas canvas, Offset center, String text, bool selected) {
    _drawCapsuleShape(canvas, center, selected);
    _drawCapsuleText(canvas, center, text);
  }

  static void _drawCapsuleShape(Canvas canvas, Offset center, bool selected) {
    final rect = RRect.fromRectAndRadius(
      Rect.fromCenter(center: center, width: _capsuleWidth, height: _capsuleHeight),
      const Radius.circular(_capsuleHeight / 2),
    );
    canvas.drawRRect(
      rect,
      Paint()..color = AppTheme.primary.withValues(alpha: 0.5)..style = PaintingStyle.fill,
    );
    canvas.drawRRect(
      rect,
      Paint()
        ..color = selected ? AppTheme.primary : AppTheme.primary.withValues(alpha: 0.8)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.5,
    );
  }

  static void _drawCapsuleText(Canvas canvas, Offset center, String text) {
    final textPainter = TextPainter(
      text: TextSpan(
        text: text,
        style: const TextStyle(color: AppTheme.textPrimary, fontSize: 12, fontWeight: FontWeight.w600),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    textPainter.paint(
      canvas,
      Offset(center.dx - textPainter.width / 2, center.dy - textPainter.height / 2),
    );
  }
}
