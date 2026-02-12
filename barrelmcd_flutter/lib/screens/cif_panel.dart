import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/mcd_state.dart';
import '../theme/app_theme.dart';

/// Types CIF/CIFF (alignés backend).
const List<String> cifTypes = ['functional', 'inter_association', 'unique', 'exclusion'];

String cifTypeLabel(String type) {
  switch (type) {
    case 'functional': return 'Fonctionnelle';
    case 'inter_association': return 'Inter-associations';
    case 'unique': return 'Unicité';
    case 'exclusion': return 'Exclusion';
    default: return type;
  }
}

/// Panneau CIF / CIFF — Contraintes d'intégrité fonctionnelle.
class CifPanel extends StatelessWidget {
  const CifPanel({super.key});

  /// Ouvre le dialogue d'édition d'une CIF à l'index donné (depuis le canvas ou ailleurs).
  static void showEditDialogForIndex(BuildContext context, McdState state, int index) {
    if (index < 0 || index >= state.cifConstraints.length) return;
    _showCifEditDialog(context, state, index);
  }

  static void show(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppTheme.surface,
      builder: (ctx) => DraggableScrollableSheet(
        initialChildSize: 0.5,
        minChildSize: 0.3,
        maxChildSize: 0.85,
        expand: false,
        builder: (_, scrollController) => const CifPanel(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<McdState>(
      builder: (context, state, _) {
        final constraints = state.cifConstraints;
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  const Icon(Icons.rule, color: AppTheme.primary, size: 24),
                  const SizedBox(width: 8),
                  const Text('CIF / CIFF', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const Spacer(),
                  IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(context)),
                ],
              ),
            ),
            const Divider(height: 1),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              child: Text(
                'Placez les symboles CIF/CIFF où vous voulez sur le canvas et tracez des liens/flèches comme vous le souhaitez. Ces éléments sont affichés à titre indicatif et ne sont pas utilisés pour la transposition MLD/MPD.',
                style: TextStyle(fontSize: 12, color: AppTheme.textSecondary),
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: OutlinedButton.icon(
                icon: const Icon(Icons.add, size: 18),
                label: const Text('Ajouter une CIF'),
                onPressed: () => _showCifEditDialog(context, state, null),
              ),
            ),
            const SizedBox(height: 8),
            Expanded(
              child: constraints.isEmpty
                  ? Center(
                      child: Text(
                        'Aucune contrainte CIF.',
                        style: TextStyle(color: AppTheme.textTertiary),
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      itemCount: constraints.length,
                      itemBuilder: (context, i) {
                        final c = constraints[i];
                        final name = c['name'] as String? ?? 'CIF';
                        final type = c['type'] as String? ?? 'functional';
                        final enabled = c['is_enabled'] != false;
                        return Card(
                          margin: const EdgeInsets.only(bottom: 6),
                          color: AppTheme.surfaceLight,
                          child: ListTile(
                            leading: Icon(
                              enabled ? Icons.rule : Icons.rule_outlined,
                              color: enabled ? AppTheme.primary : AppTheme.textTertiary,
                            ),
                            title: Text(name),
                            subtitle: Text('${cifTypeLabel(type)}${(c['associations'] as List?)?.isNotEmpty == true ? ' · ${(c['associations'] as List).length} assoc.' : ''}'),
                            trailing: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                IconButton(
                                  icon: const Icon(Icons.edit_outlined, size: 20),
                                  onPressed: () => _showCifEditDialog(context, state, i),
                                ),
                                IconButton(
                                  icon: const Icon(Icons.delete_outline, color: AppTheme.error, size: 20),
                                  onPressed: () => state.removeCifConstraintAt(i),
                                ),
                              ],
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

  static Future<void> _showCifEditDialog(BuildContext context, McdState state, int? index) async {
    final isEdit = index != null;
    final existing = isEdit && index < state.cifConstraints.length ? state.cifConstraints[index] : null;
    final entityNames = state.entities.map((e) => e['name'] as String? ?? '').where((n) => n.isNotEmpty).toList();
    final assocNames = state.associations.map((a) => a['name'] as String? ?? '').where((n) => n.isNotEmpty).toList();

    final result = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (ctx) => _CifEditDialog(
        isEdit: isEdit,
        initialName: (existing?['name'] as String?) ?? 'CIF',
        initialType: (existing?['type'] as String?) ?? 'functional',
        initialDescription: (existing?['description'] as String?) ?? '',
        initialEntities: List<String>.from(existing?['entities'] as List? ?? []),
        initialAssociations: List<String>.from(existing?['associations'] as List? ?? []),
        initialEnabled: existing?['is_enabled'] != false,
        entityNames: entityNames,
        assocNames: assocNames,
      ),
    );
    if (result != null && context.mounted) {
      final constraint = {
        'name': (result['name'] as String?)?.trim().isEmpty == true ? 'CIF' : (result['name'] as String?)?.trim() ?? 'CIF',
        'type': result['type'] as String? ?? 'functional',
        'description': (result['description'] as String?)?.trim() ?? '',
        'entities': List<String>.from(result['entities'] as List? ?? []),
        'associations': List<String>.from(result['associations'] as List? ?? []),
        'is_enabled': result['is_enabled'] != false,
      };
      if (isEdit) {
        state.updateCifConstraintAt(index!, constraint);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('CIF modifiée')));
      } else {
        state.addCifConstraint(constraint);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('CIF ajoutée')));
      }
    }
  }
}

class _CifEditDialog extends StatefulWidget {
  const _CifEditDialog({
    required this.isEdit,
    required this.initialName,
    required this.initialType,
    required this.initialDescription,
    required this.initialEntities,
    required this.initialAssociations,
    required this.initialEnabled,
    required this.entityNames,
    required this.assocNames,
  });

  final bool isEdit;
  final String initialName;
  final String initialType;
  final String initialDescription;
  final List<String> initialEntities;
  final List<String> initialAssociations;
  final bool initialEnabled;
  final List<String> entityNames;
  final List<String> assocNames;

  @override
  State<_CifEditDialog> createState() => _CifEditDialogState();
}

class _CifEditDialogState extends State<_CifEditDialog> {
  late TextEditingController _nameController;
  late TextEditingController _descController;
  late String type;
  late List<String> entities;
  late List<String> associations;
  late bool isEnabled;

  @override
  void initState() {
    super.initState();
    _nameController = TextEditingController(text: widget.initialName);
    _descController = TextEditingController(text: widget.initialDescription);
    type = widget.initialType;
    entities = List<String>.from(widget.initialEntities);
    associations = List<String>.from(widget.initialAssociations);
    isEnabled = widget.initialEnabled;
  }

  @override
  void dispose() {
    _nameController.dispose();
    _descController.dispose();
    super.dispose();
  }

  void _submit() {
    Navigator.pop(context, {
      'name': _nameController.text,
      'type': type,
      'description': _descController.text,
      'entities': entities,
      'associations': associations,
      'is_enabled': isEnabled,
    });
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: AppTheme.surface,
      title: Text(widget.isEdit ? 'Modifier la CIF' : 'Nouvelle CIF'),
      content: SingleChildScrollView(
        child: SizedBox(
          width: 400,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              TextField(
                decoration: const InputDecoration(labelText: 'Nom'),
                controller: _nameController,
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                value: type,
                decoration: const InputDecoration(labelText: 'Type'),
                items: cifTypes.map((t) => DropdownMenuItem(value: t, child: Text(cifTypeLabel(t)))).toList(),
                onChanged: (v) => setState(() => type = v ?? type),
              ),
              const SizedBox(height: 12),
              TextField(
                decoration: const InputDecoration(labelText: 'Description (optionnel)'),
                controller: _descController,
                maxLines: 2,
              ),
              const SizedBox(height: 12),
              if (widget.assocNames.isNotEmpty) ...[
                const Text('Associations concernées', style: TextStyle(fontSize: 12)),
                Wrap(
                  spacing: 6,
                  children: widget.assocNames.map((a) {
                    final selected = associations.contains(a);
                    return FilterChip(
                      label: Text(a),
                      selected: selected,
                      onSelected: (v) => setState(() {
                        if (v) associations.add(a); else associations.remove(a);
                      }),
                    );
                  }).toList(),
                ),
                const SizedBox(height: 12),
              ],
              if (widget.entityNames.isNotEmpty) ...[
                const Text('Entités concernées', style: TextStyle(fontSize: 12)),
                Wrap(
                  spacing: 6,
                  children: widget.entityNames.map((e) {
                    final selected = entities.contains(e);
                    return FilterChip(
                      label: Text(e),
                      selected: selected,
                      onSelected: (v) => setState(() {
                        if (v) entities.add(e); else entities.remove(e);
                      }),
                    );
                  }).toList(),
                ),
              ],
              const SizedBox(height: 8),
              SwitchListTile(
                title: const Text('Activée'),
                value: isEnabled,
                onChanged: (v) => setState(() => isEnabled = v),
              ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Annuler')),
        FilledButton(onPressed: _submit, child: Text(widget.isEdit ? 'Enregistrer' : 'Ajouter')),
      ],
    );
  }
}
