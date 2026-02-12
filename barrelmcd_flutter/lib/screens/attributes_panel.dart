import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/mcd_state.dart';
import '../theme/app_theme.dart';
import '../widgets/mcd_canvas.dart';

/// Panneau Attributs : liste des entités et associations pour ouvrir la fenêtre
/// d'édition des attributs (typages, quantités, clé primaire, etc.) — même fenêtre
/// que le clic sur la zone attributs d'une entité.
class AttributesPanel extends StatelessWidget {
  const AttributesPanel({super.key});

  static void show(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppTheme.surface,
      builder: (ctx) => DraggableScrollableSheet(
        initialChildSize: 0.5,
        minChildSize: 0.25,
        maxChildSize: 0.9,
        expand: false,
        builder: (_, scrollController) => const AttributesPanel(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<McdState>(
      builder: (context, state, _) {
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  const Icon(Icons.tune, size: 24, color: AppTheme.primary),
                  const SizedBox(width: 8),
                  const Text(
                    'Attributs',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  const Spacer(),
                  IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
            ),
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 12),
              child: Text(
                'Choisissez une entité ou une association pour modifier ses attributs (types, clé primaire, obligatoire, etc.).',
                style: TextStyle(
                  color: AppTheme.textSecondary,
                  fontSize: 12,
                  height: 1.3,
                ),
              ),
            ),
            const Divider(height: 1),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.all(8),
                children: [
                  const Padding(
                    padding: EdgeInsets.only(top: 8, bottom: 4),
                    child: Text(
                      'Entités',
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        color: AppTheme.primary,
                      ),
                    ),
                  ),
                  ...state.entities.asMap().entries.map((e) {
                    final name = e.value['name'] as String? ?? 'Sans nom';
                    final count = (e.value['attributes'] as List?)?.length ?? 0;
                    return ListTile(
                      leading: const Icon(
                        Icons.table_chart,
                        color: AppTheme.textSecondary,
                        size: 22,
                      ),
                      title: Text(name),
                      subtitle: Text(
                        '$count attribut${count > 1 ? 's' : ''}',
                        style: const TextStyle(fontSize: 12),
                      ),
                      trailing: const Icon(Icons.edit, size: 20, color: AppTheme.primary),
                      onTap: () async {
                        await showEntityAttributesFor(context, e.key);
                        if (context.mounted) {}
                      },
                    );
                  }),
                  const Padding(
                    padding: EdgeInsets.only(top: 16, bottom: 4),
                    child: Text(
                      'Associations',
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        color: AppTheme.primary,
                      ),
                    ),
                  ),
                  ...state.associations.asMap().entries.map((a) {
                    final name = a.value['name'] as String? ?? 'Sans nom';
                    final count = (a.value['attributes'] as List?)?.length ?? 0;
                    return ListTile(
                      leading: const Icon(
                        Icons.link,
                        color: AppTheme.textSecondary,
                        size: 22,
                      ),
                      title: Text(name),
                      subtitle: Text(
                        '$count attribut${count > 1 ? 's' : ''}',
                        style: const TextStyle(fontSize: 12),
                      ),
                      trailing: const Icon(Icons.edit, size: 20, color: AppTheme.primary),
                      onTap: () async {
                        await showAssociationAttributesFor(context, a.key);
                        if (context.mounted) {}
                      },
                    );
                  }),
                  if (state.entities.isEmpty && state.associations.isEmpty)
                    const Padding(
                      padding: EdgeInsets.all(24),
                      child: Center(
                        child: Text(
                          'Aucune entité ni association.\nCréez-en sur le canvas puis revenez ici.',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            color: AppTheme.textTertiary,
                            fontSize: 12,
                          ),
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ],
        );
      },
    );
  }
}
