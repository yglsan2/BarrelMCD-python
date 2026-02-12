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
    this.width,
    this.onTap,
    this.onAttributesAreaTap,
  });

  final String name;
  final List<Map<String, dynamic>> attributes;
  final bool selected;
  /// Largeur du rectangle (défaut 200). Permet le redimensionnement.
  final double? width;
  final bool isWeak;
  final bool isFictive;
  final VoidCallback? onTap;
  /// Clic droit sur la zone sous le nom (attributs) → ouvre la fenêtre d'attributs (créer, modifier, typages, quantités, etc.).
  final VoidCallback? onAttributesAreaTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: width ?? 200,
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
            GestureDetector(
              onSecondaryTap: onAttributesAreaTap,
              behavior: HitTestBehavior.opaque,
              child: Tooltip(
                message: 'Clic droit pour ajouter ou modifier les attributs',
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
            if (attributes.isEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                child: Text(
                  'Clic droit pour ajouter ou modifier les attributs',
                  style: const TextStyle(
                    color: AppTheme.textTertiary,
                    fontSize: 10,
                    fontStyle: FontStyle.italic,
                  ),
                ),
              )
            else ...[
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                child: Row(
                  children: [
                    const SizedBox(
                      width: 36,
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Tooltip(
                            message: 'Clé primaire. Voir Aide → Lexique.',
                            child: SizedBox(width: 8, child: Text('PK', style: TextStyle(color: AppTheme.textTertiary, fontSize: 9), textAlign: TextAlign.center)),
                          ),
                          Tooltip(
                            message: 'Clé secondaire / Unique. Voir Aide → Lexique.',
                            child: SizedBox(width: 10, child: Text('U', style: TextStyle(color: AppTheme.textTertiary, fontSize: 9), textAlign: TextAlign.center)),
                          ),
                        ],
                      ),
                    ),
                    const Expanded(child: Text('Attributs', style: TextStyle(color: AppTheme.textTertiary, fontSize: 9))),
                  ],
                ),
              ),
              const Divider(height: 8),
              ...attributes.map((a) {
                final attrName = a['name']?.toString() ?? '';
                final type = a['type']?.toString() ?? 'varchar';
                final oblig = a['nullable'] == false;
                final isPk = a['is_primary_key'] == true;
                final isUnique = a['is_unique'] == true;
                return Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      SizedBox(
                        width: 36,
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            SizedBox(
                              width: 16,
                              height: 16,
                              child: Checkbox(
                                value: isPk,
                                onChanged: null,
                                materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                                fillColor: WidgetStateProperty.resolveWith((_) => AppTheme.secondary),
                                checkColor: Colors.white,
                                tristate: false,
                              ),
                            ),
                            const SizedBox(width: 2),
                            SizedBox(
                              width: 16,
                              height: 16,
                              child: Checkbox(
                                value: isUnique,
                                onChanged: null,
                                materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                                fillColor: WidgetStateProperty.resolveWith((_) => AppTheme.primary),
                                checkColor: Colors.white,
                                tristate: false,
                              ),
                            ),
                          ],
                        ),
                      ),
                      Expanded(
                        child: Tooltip(
                          message: (a['description']?.toString() ?? '').trim().isEmpty
                              ? '${isPk ? 'Clé primaire. ' : ''}${isUnique ? 'Clé sec. / Unique. ' : ''}$attrName — $type${oblig ? ' (obligatoire)' : ''}. Voir Aide → Lexique pour les définitions.'
                              : '${a['description']}. Voir Aide → Lexique pour clé primaire, clé secondaire, etc.',
                          child: Text(
                            attrName.isEmpty ? '(sans nom)' : '$attrName ($type)${oblig ? ' *' : ''}',
                            style: const TextStyle(color: AppTheme.textSecondary, fontSize: 11),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ),
                    ],
                  ),
                );
              }),
            ],
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
