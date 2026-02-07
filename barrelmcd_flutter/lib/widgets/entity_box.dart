import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// Rectangle représentant une entité MCD (style Python : coins arrondis, dégradé).
class EntityBox extends StatelessWidget {
  const EntityBox({
    super.key,
    required this.name,
    this.attributes = const [],
    this.selected = false,
    this.onTap,
  });

  final String name;
  final List<Map<String, dynamic>> attributes;
  final bool selected;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 200,
        constraints: const BoxConstraints(minHeight: 80),
        decoration: BoxDecoration(
          color: AppTheme.entityBg,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: selected ? AppTheme.entitySelected : AppTheme.entityBorder,
            width: selected ? 2.5 : 1.5,
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.3),
              blurRadius: 8,
              offset: const Offset(2, 2),
            ),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: AppTheme.entityBorder.withValues(alpha: 0.5),
                borderRadius: const BorderRadius.vertical(top: Radius.circular(6)),
              ),
              child: Text(
                name,
                style: const TextStyle(
                  color: AppTheme.textPrimary,
                  fontWeight: FontWeight.bold,
                  fontSize: 12,
                ),
              ),
            ),
            const Divider(height: 1, color: AppTheme.entityBorder),
            ...attributes.take(5).map((a) => Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  child: Row(
                    children: [
                      if (a['is_primary_key'] == true)
                        const Padding(
                          padding: EdgeInsets.only(right: 4),
                          child: Icon(Icons.key, size: 12, color: AppTheme.secondary),
                        ),
                      Expanded(
                        child: Text(
                          '${a['name']} (${a['type'] ?? 'varchar'})',
                          style: const TextStyle(color: AppTheme.textSecondary, fontSize: 11),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                )),
            if (attributes.length > 5)
              Padding(
                padding: const EdgeInsets.all(4),
                child: Text(
                  '+${attributes.length - 5} autres',
                  style: TextStyle(color: AppTheme.textTertiary, fontSize: 10),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
