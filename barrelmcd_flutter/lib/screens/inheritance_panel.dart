import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/mcd_state.dart';
import '../theme/app_theme.dart';

/// Panneau Héritage (généralisation / spécialisation).
/// Liste des liens parent→enfant et ajout/suppression.
class InheritancePanel extends StatelessWidget {
  const InheritancePanel({super.key});

  static void show(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppTheme.surface,
      builder: (ctx) => DraggableScrollableSheet(
        initialChildSize: 0.45,
        minChildSize: 0.25,
        maxChildSize: 0.7,
        expand: false,
        builder: (_, scrollController) => const InheritancePanel(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<McdState>(
      builder: (context, state, _) {
        final links = state.inheritanceLinks;
        final entityNames = state.entities.map((e) => e['name'] as String? ?? '').where((n) => n.isNotEmpty).toList();
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  const Icon(Icons.account_tree, color: AppTheme.primary, size: 24),
                  const SizedBox(width: 8),
                  const Text('Héritage (généralisation)', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const Spacer(),
                  IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(context)),
                ],
              ),
            ),
            const Divider(height: 1),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              child: Text(
                'Placez le symbole héritage où vous voulez sur le canvas (glissez-le) et tracez des liens/flèches comme vous le souhaitez. Ces éléments sont affichés à titre indicatif et ne sont pas utilisés pour la transposition MLD/MPD.',
                style: TextStyle(fontSize: 12, color: AppTheme.textSecondary),
              ),
            ),
            if (entityNames.length < 2)
              Padding(
                padding: const EdgeInsets.all(16),
                child: Text(
                  'Créez au moins deux entités pour définir un héritage.',
                  style: TextStyle(color: AppTheme.textSecondary),
                ),
              )
            else
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                child: OutlinedButton.icon(
                  icon: const Icon(Icons.add, size: 18),
                  label: const Text('Ajouter un lien d\'héritage'),
                  onPressed: () => _showAddInheritanceDialog(context, state, entityNames),
                ),
              ),
            const SizedBox(height: 8),
            Expanded(
              child: links.isEmpty
                  ? Center(
                      child: Text(
                        'Aucun lien d\'héritage.',
                        style: TextStyle(color: AppTheme.textTertiary),
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      itemCount: links.length,
                      itemBuilder: (context, i) {
                        final parent = links[i]['parent'] as String? ?? '';
                        final child = links[i]['child'] as String? ?? '';
                        return Card(
                          margin: const EdgeInsets.only(bottom: 6),
                          color: AppTheme.surfaceLight,
                          child: ListTile(
                            leading: const Icon(Icons.account_tree_outlined, color: AppTheme.primary),
                            title: Text('$child → $parent'),
                            subtitle: const Text('hérite de'),
                            trailing: IconButton(
                              icon: const Icon(Icons.delete_outline, color: AppTheme.error, size: 20),
                              onPressed: () {
                                state.removeInheritanceLinkAt(i);
                              },
                            ),
                          ),
                        );
                      },
                    ),
            ),
          ],
        );
      },
    );
  }

  static Future<void> _showAddInheritanceDialog(BuildContext context, McdState state, List<String> entityNames) async {
    String? parent = entityNames.isNotEmpty ? entityNames.first : null;
    String? child = entityNames.length > 1 ? entityNames[1] : entityNames.first;
    await showDialog<void>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setState) {
          final childrenAvailable = entityNames.where((n) => n != parent).toList();
          final parentsAvailable = entityNames.where((n) => n != child).toList();
          if (parent != null && !parentsAvailable.contains(parent)) parent = parentsAvailable.isNotEmpty ? parentsAvailable.first : null;
          if (child != null && !childrenAvailable.contains(child)) child = childrenAvailable.isNotEmpty ? childrenAvailable.first : null;
          return AlertDialog(
            backgroundColor: AppTheme.surface,
            title: const Text('Ajouter un lien d\'héritage'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                DropdownButtonFormField<String>(
                  value: child,
                  decoration: const InputDecoration(labelText: 'Enfant (spécialisation)'),
                  items: childrenAvailable.map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
                  onChanged: (v) => setState(() => child = v),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  value: parent,
                  decoration: const InputDecoration(labelText: 'Parent (généralisation)'),
                  items: parentsAvailable.map((p) => DropdownMenuItem(value: p, child: Text(p))).toList(),
                  onChanged: (v) => setState(() => parent = v),
                ),
              ],
            ),
            actions: [
              TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler')),
              FilledButton(
                onPressed: (parent != null && child != null && parent != child)
                    ? () {
                        state.addInheritanceLink(parent!, child!);
                        Navigator.pop(ctx);
                        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$child hérite de $parent')));
                      }
                    : null,
                child: const Text('Ajouter'),
              ),
            ],
          );
        },
      ),
    );
  }
}
