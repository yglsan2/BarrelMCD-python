import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/mcd_state.dart';
import '../theme/app_theme.dart';
import '../widgets/mcd_canvas.dart';

/// Panneau Explorateur : liste des entités, associations et liens pour sélection / suppression. Recherche et filtre.
class ElementsPanel extends StatefulWidget {
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
  State<ElementsPanel> createState() => _ElementsPanelState();
}

class _ElementsPanelState extends State<ElementsPanel> {
  final _searchController = TextEditingController();
  String _searchQuery = '';

  @override
  void initState() {
    super.initState();
    _searchController.addListener(() => setState(() => _searchQuery = _searchController.text.trim().toLowerCase()));
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  bool _matches(String? name) {
    if (_searchQuery.isEmpty) return true;
    return (name ?? '').toLowerCase().contains(_searchQuery);
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<McdState>(
      builder: (context, state, _) {
        final entitiesFiltered = state.entities.asMap().entries.where((e) => _matches(e.value['name'] as String?)).toList();
        final associationsFiltered = state.associations.asMap().entries.where((a) => _matches(a.value['name'] as String?)).toList();
        final linksFiltered = state.associationLinks.asMap().entries.where((l) {
          final assoc = l.value['association'] as String? ?? '';
          final entity = l.value['entity'] as String? ?? '';
          return _matches(assoc) || _matches(entity);
        }).toList();
        final inheritanceFiltered = state.inheritanceLinks.asMap().entries.where((l) {
          final p = l.value['parent'] as String? ?? '';
          final c = l.value['child'] as String? ?? '';
          return _matches(p) || _matches(c);
        }).toList();
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
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              child: TextField(
                controller: _searchController,
                decoration: InputDecoration(
                  hintText: 'Rechercher entité, association…',
                  prefixIcon: const Icon(Icons.search, size: 20),
                  border: const OutlineInputBorder(),
                  isDense: true,
                  contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
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
                    child: Text('Entités', style: TextStyle(fontWeight: FontWeight.w600, color: AppTheme.primary)),
                  ),
                  ...entitiesFiltered.map((e) => ListTile(
                        leading: Icon(Icons.table_chart, color: state.isEntitySelected(e.key) ? AppTheme.primary : AppTheme.textSecondary, size: 22),
                        title: Text(e.value['name'] as String? ?? 'Sans nom', style: TextStyle(fontWeight: state.isEntitySelected(e.key) ? FontWeight.bold : FontWeight.normal)),
                        subtitle: Text('${(e.value['attributes'] as List?)?.length ?? 0} attributs', style: const TextStyle(fontSize: 12)),
                        selected: state.isEntitySelected(e.key),
                        selectedTileColor: AppTheme.primary.withValues(alpha: 0.2),
                        onTap: () {
                          state.selectEntity(e.key);
                          Navigator.pop(context);
                        },
                        trailing: IconButton(
                          icon: const Icon(Icons.tune, size: 20),
                          tooltip: 'Modifier les attributs',
                          onPressed: () => showEntityAttributesFor(context, e.key),
                        ),
                      )),
                  const Padding(
                    padding: EdgeInsets.only(top: 16, bottom: 4),
                    child: Text('Associations', style: TextStyle(fontWeight: FontWeight.w600, color: AppTheme.primary)),
                  ),
                  ...associationsFiltered.map((a) => ListTile(
                        leading: Icon(Icons.link, color: state.isAssociationSelected(a.key) ? AppTheme.primary : AppTheme.textSecondary),
                        title: Text(a.value['name'] as String? ?? 'Sans nom'),
                        subtitle: Text('${(a.value['attributes'] as List?)?.length ?? 0} attributs'),
                        selected: state.isAssociationSelected(a.key),
                        onTap: () {
                          state.selectAssociation(a.key);
                          Navigator.pop(context);
                        },
                        trailing: IconButton(
                          icon: const Icon(Icons.tune, size: 20),
                          tooltip: 'Modifier les attributs',
                          onPressed: () => showAssociationAttributesFor(context, a.key),
                        ),
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
                  const Padding(
                    padding: EdgeInsets.only(top: 16, bottom: 4),
                    child: Text('Héritage', style: TextStyle(fontWeight: FontWeight.w600, color: AppTheme.primary)),
                  ),
                  ...inheritanceFiltered.map((l) {
                    final parent = l.value['parent'] as String? ?? '';
                    final child = l.value['child'] as String? ?? '';
                    return _ListTile(
                      title: '$child → $parent',
                      subtitle: 'hérite de',
                      icon: Icons.account_tree_outlined,
                      selected: state.isInheritanceSelected(l.key),
                      onTap: () {
                        state.selectInheritance(l.key);
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
