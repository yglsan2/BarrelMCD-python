import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/mcd_state.dart';
import '../theme/app_theme.dart';

/// Panneau Explorateur : liste des entités, associations et liens pour sélection / suppression.
class ElementsPanel extends StatelessWidget {
  const ElementsPanel({super.key});

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
        builder: (_, scrollController) => const ElementsPanel(),
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
                  const Text('Explorateur', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const Spacer(),
                  IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(context)),
                ],
              ),
            ),
            const Divider(height: 1),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.all(8),
                children: [
                  const Padding(
                    padding: EdgeInsets.only(top: 8, bottom: 4),
                    child: Text('Entités', style: TextStyle(fontWeight: FontWeight.w600, color: AppTheme.primary)),
                  ),
                  ...state.entities.asMap().entries.map((e) => _ListTile(
                        title: e.value['name'] as String? ?? 'Sans nom',
                        subtitle: '${(e.value['attributes'] as List?)?.length ?? 0} attributs',
                        icon: Icons.table_chart,
                        selected: state.isEntitySelected(e.key),
                        onTap: () {
                          state.selectEntity(e.key);
                          Navigator.pop(context);
                        },
                      )),
                  const Padding(
                    padding: EdgeInsets.only(top: 16, bottom: 4),
                    child: Text('Associations', style: TextStyle(fontWeight: FontWeight.w600, color: AppTheme.primary)),
                  ),
                  ...state.associations.asMap().entries.map((a) => _ListTile(
                        title: a.value['name'] as String? ?? 'Sans nom',
                        subtitle: '',
                        icon: Icons.link,
                        selected: state.isAssociationSelected(a.key),
                        onTap: () {
                          state.selectAssociation(a.key);
                          Navigator.pop(context);
                        },
                      )),
                  const Padding(
                    padding: EdgeInsets.only(top: 16, bottom: 4),
                    child: Text('Liens', style: TextStyle(fontWeight: FontWeight.w600, color: AppTheme.primary)),
                  ),
                  ...state.associationLinks.asMap().entries.map((l) {
                    final assoc = l.value['association'] as String? ?? '';
                    final entity = l.value['entity'] as String? ?? '';
                    final card = l.value['cardinality'] as String? ?? '';
                    return _ListTile(
                      title: '$assoc — $entity',
                      subtitle: card,
                      icon: Icons.account_tree,
                      selected: state.isLinkSelected(l.key),
                      onTap: () {
                        state.selectLink(l.key);
                        Navigator.pop(context);
                      },
                    );
                  }),
                ],
              ),
            ),
          ],
        );
      },
    );
  }
}

class _ListTile extends StatelessWidget {
  const _ListTile({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.selected,
    required this.onTap,
  });

  final String title;
  final String subtitle;
  final IconData icon;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icon, color: selected ? AppTheme.primary : AppTheme.textSecondary, size: 22),
      title: Text(title, style: TextStyle(fontWeight: selected ? FontWeight.bold : FontWeight.normal)),
      subtitle: subtitle.isEmpty ? null : Text(subtitle, style: const TextStyle(fontSize: 12)),
      selected: selected,
      selectedTileColor: AppTheme.primary.withValues(alpha: 0.2),
      onTap: onTap,
    );
  }
}
