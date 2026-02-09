import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// Losange représentant une association MCD (style Python). Peut afficher des attributs d'association.
/// Dimensions : [diamondSize] = 60, affichage width = [diamondDisplayWidth] = 96 (aligné avec _LinksPainter dans mcd_canvas).
class AssociationDiamond extends StatelessWidget {
  const AssociationDiamond({
    super.key,
    required this.name,
    this.selected = false,
    this.attributes = const [],
  });

  static const double diamondSize = 60;
  static const double diamondDisplayWidth = 96; // diamondSize * 1.6

  final String name;
  final bool selected;
  final List<Map<String, dynamic>> attributes;

  @override
  Widget build(BuildContext context) {
    final hasAttrs = attributes.isNotEmpty;
    final height = hasAttrs ? diamondDisplayWidth + attributes.length * 14.0 : diamondDisplayWidth;
    return CustomPaint(
      size: Size(diamondDisplayWidth, height),
      painter: _DiamondPainter(selected: selected),
      child: Padding(
        padding: const EdgeInsets.all(8),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
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
            if (hasAttrs) ...[
              const SizedBox(height: 4),
              ...attributes.take(3).map((a) => Padding(
                    padding: const EdgeInsets.only(top: 2),
                    child: Text(
                      '${a['name']} (${a['type'] ?? ''})',
                      style: const TextStyle(color: AppTheme.textSecondary, fontSize: 8),
                      overflow: TextOverflow.ellipsis,
                      maxLines: 1,
                    ),
                  )),
              if (attributes.length > 3)
                Text(
                  '+${attributes.length - 3}',
                  style: const TextStyle(color: AppTheme.textTertiary, fontSize: 8),
                ),
            ],
          ],
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
    final center = Offset(size.width / 2, size.height / 2);
    const double halfDiamond = AssociationDiamond.diamondSize / 2;
    final path = Path()
      ..moveTo(center.dx, center.dy - halfDiamond)
      ..lineTo(center.dx + halfDiamond, center.dy)
      ..lineTo(center.dx, center.dy + halfDiamond)
      ..lineTo(center.dx - halfDiamond, center.dy)
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
