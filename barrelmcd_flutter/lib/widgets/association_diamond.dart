import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// Losange représentant une association MCD (style Python).
class AssociationDiamond extends StatelessWidget {
  const AssociationDiamond({super.key, required this.name, this.selected = false});

  final String name;
  final bool selected;

  @override
  Widget build(BuildContext context) {
    const double size = 60;
    return CustomPaint(
      size: const Size(size * 1.6, size * 1.6),
      painter: _DiamondPainter(selected: selected),
      child: Center(
        child: Padding(
          padding: const EdgeInsets.all(8),
          child: Text(
            name,
            textAlign: TextAlign.center,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              color: AppTheme.textPrimary,
              fontSize: 10,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
      ),
    );
  }
}

class _DiamondPainter extends CustomPainter {
  _DiamondPainter({this.selected = false});
  final bool selected;

  @override
  void paint(Canvas canvas, Size size) {
    const double diamondSize = 60;
    final center = Offset(size.width / 2, size.height / 2);
    final path = Path()
      ..moveTo(center.dx, center.dy - diamondSize / 2)
      ..lineTo(center.dx + diamondSize / 2, center.dy)
      ..lineTo(center.dx, center.dy + diamondSize / 2)
      ..lineTo(center.dx - diamondSize / 2, center.dy)
      ..close();
    canvas.drawPath(
      path,
      Paint()
        ..color = AppTheme.associationBg
        ..style = PaintingStyle.fill,
    );
    canvas.drawPath(
      path,
      Paint()
        ..color = selected ? AppTheme.associationSelected : AppTheme.associationBorder
        ..style = PaintingStyle.stroke
        ..strokeWidth = selected ? 2.5 : 1.5,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
