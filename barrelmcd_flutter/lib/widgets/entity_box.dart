import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// Rectangle représentant une entité MCD (style Python : coins arrondis, dégradé).
/// Entité faible : double bordure (style Merise).
class EntityBox extends StatelessWidget {
  const EntityBox({
    super.key,
    required this.name,
    this.attributes = const [],
    this.selected = false,
    this.isWeak = false,
    this.isFictive = false,
    this.onTap,
  });

  final String name;
  final List<Map<String, dynamic>> attributes;
  final bool selected;
  final bool isWeak;
  final bool isFictive;
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
          boxShadow: isWeak
              ? [
                  BoxShadow(
                    color: AppTheme.secondary.withValues(alpha: 0.4),
                    blurRadius: 0,
                    spreadRadius: 1,
                    offset: const Offset(2, 2),
                  ),
                ]
              : [
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
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      name,
                      style: const TextStyle(
                        color: AppTheme.textPrimary,
                        fontWeight: FontWeight.bold,
                        fontSize: 12,
                      ),
                    ),
                  ),
                  if (isWeak)
                    const Text(
                      'faible',
                      style: TextStyle(
                        color: AppTheme.secondary,
                        fontSize: 9,
                        fontStyle: FontStyle.italic,
                      ),
                    ),
                  if (isFictive)
                    const Padding(
                      padding: EdgeInsets.only(left: 4),
                      child: Text(
                        'fictive',
                        style: TextStyle(
                          color: AppTheme.warning,
                          fontSize: 9,
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                    ),
                ],
              ),
            ),
            const Divider(height: 1, color: AppTheme.entityBorder),
            ...attributes.take(5).map((a) {
              final name = a['name']?.toString() ?? '';
              final type = a['type']?.toString() ?? 'varchar';
              final oblig = a['nullable'] == false;
              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                child: Row(
                  children: [
                    if (a['is_primary_key'] == true)
                      const Padding(
                        padding: EdgeInsets.only(right: 4),
                        child: Icon(Icons.key, size: 12, color: AppTheme.secondary),
                      ),
                    Expanded(
                      child: Tooltip(
                        message: (a['description']?.toString() ?? '').trim().isEmpty ? '$name — $type' : '${a['description']}',
                        child: Text(
                          name.isEmpty ? '(sans nom)' : '$name ($type)${oblig ? ' *' : ''}',
                          style: const TextStyle(color: AppTheme.textSecondary, fontSize: 11),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ),
                  ],
                ),
              );
            }),
            if (attributes.length > 5)
              Padding(
                padding: const EdgeInsets.all(4),
                child: Text(
                  '+${attributes.length - 5} autres',
                  style: const TextStyle(color: AppTheme.textTertiary, fontSize: 10),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
