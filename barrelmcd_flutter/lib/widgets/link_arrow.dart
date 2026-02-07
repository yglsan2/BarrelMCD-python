import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// Dessine une flèche entre deux points avec label de cardinalité (style MCD Merise).
class LinkArrow {
  static void paint(Canvas canvas, {required Offset from, required Offset to, required String cardinality, bool selected = false}) {
    const strokeWidth = 2.0;
    final paint = Paint()
      ..color = selected ? AppTheme.primary : AppTheme.textSecondary
      ..strokeWidth = selected ? 3.0 : strokeWidth
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    final dx = to.dx - from.dx;
    final dy = to.dy - from.dy;
    final dist = math.sqrt(dx * dx + dy * dy);
    if (dist < 1) return;

    const arrowSize = 10.0;
    const entityMargin = 30.0;
    const assocMargin = 25.0;

    final ux = dx / dist;
    final uy = dy / dist;
    final start = Offset(from.dx + ux * assocMargin, from.dy + uy * assocMargin);
    final end = Offset(to.dx - ux * entityMargin, to.dy - uy * entityMargin);

    canvas.drawLine(start, end, paint);

    final angle = math.atan2(dy, dx);
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

    final mid = Offset((start.dx + end.dx) / 2, (start.dy + end.dy) / 2);
    final textPainter = TextPainter(
      text: TextSpan(text: cardinality, style: TextStyle(color: AppTheme.textPrimary, fontSize: 11, fontWeight: FontWeight.w500)),
      textDirection: TextDirection.ltr,
    )..layout();
    textPainter.paint(
      canvas,
      Offset(mid.dx - textPainter.width / 2, mid.dy - textPainter.height / 2),
    );
  }
}
