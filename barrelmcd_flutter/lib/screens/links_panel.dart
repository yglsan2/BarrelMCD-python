import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/mcd_state.dart';
import '../widgets/mcd_canvas.dart';
import '../theme/app_theme.dart';

/// Panneau « Flèches » : sélectionner un lien et modifier son style (ligne, sens flèche, épaisseur), cardinalités, ou supprimer.
class LinksPanel extends StatelessWidget {
  const LinksPanel({super.key});

  static const List<String> lineStyles = ['straight', 'elbow_h', 'elbow_v', 'curved'];
  static const Map<String, String> lineStyleLabels = {
    'straight': 'Droite',
    'elbow_h': 'Coudé (H)',
    'elbow_v': 'Coudé (V)',
    'curved': 'Courbe',
  };
  static const List<String> arrowHeads = ['arrow', 'diamond', 'block', 'none'];
  static const Map<String, String> arrowHeadLabels = {
    'arrow': 'Flèche',
    'diamond': 'Losange',
    'block': 'Bloc',
    'none': 'Aucune',
  };
  static const List<String> startCaps = ['dot', 'diamond', 'square', 'none'];
  static const Map<String, String> startCapLabels = {
    'dot': 'Point',
    'diamond': 'Losange',
    'square': 'Carré',
    'none': 'Aucune',
  };

  static void show(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppTheme.surface,
      builder: (ctx) => DraggableScrollableSheet(
        initialChildSize: 0.45,
        minChildSize: 0.25,
        maxChildSize: 0.85,
        expand: false,
        builder: (_, scrollController) => const LinksPanel(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<McdState>(
      builder: (context, state, _) {
        final links = state.associationLinks;
        final selectedLinkIndex = state.selectedType == 'link' ? state.selectedIndex : -1;
        final hasSelection = selectedLinkIndex >= 0 && selectedLinkIndex < links.length;

        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  const Icon(Icons.alt_route, color: AppTheme.primary, size: 24),
                  const SizedBox(width: 8),
                  const Text('Flèches et liens', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const Spacer(),
                  IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(context)),
                ],
              ),
            ),
            const Divider(height: 1),
            Expanded(
              child: links.isEmpty
                  ? const Center(
                      child: Padding(
                        padding: EdgeInsets.all(24),
                        child: Text(
                          'Aucun lien. Créez des liens entre entités et associations depuis le mode Lien (icône chaîne).',
                          textAlign: TextAlign.center,
                          style: TextStyle(color: AppTheme.textSecondary),
                        ),
                      ),
                    )
                  : ListView(
                      padding: const EdgeInsets.all(12),
                      children: [
                        const Text('Choisir un lien à modifier :', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 12)),
                        const SizedBox(height: 8),
                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: List.generate(links.length, (i) {
                            final link = links[i];
                            final assoc = link['association'] as String? ?? '?';
                            final entity = link['entity'] as String? ?? '?';
                            final selected = i == selectedLinkIndex;
                            return ChoiceChip(
                              label: Text('${i + 1}: $assoc → $entity'),
                              selected: selected,
                              onSelected: (_) {
                                state.selectLink(i);
                              },
                            );
                          }),
                        ),
                        if (hasSelection) ...[
                          const SizedBox(height: 20),
                          _LinkOptions(linkIndex: selectedLinkIndex),
                        ],
                      ],
                    ),
            ),
          ],
        );
      },
    );
  }
}

class _LinkOptions extends StatelessWidget {
  const _LinkOptions({required this.linkIndex});

  final int linkIndex;

  @override
  Widget build(BuildContext context) {
    final state = context.read<McdState>();
    if (linkIndex < 0 || linkIndex >= state.associationLinks.length) return const SizedBox.shrink();
    final link = state.associationLinks[linkIndex];
    final lineStyle = link['line_style'] as String? ?? 'straight';
    final arrowReversed = link['arrow_reversed'] == true;
    final strokeW = (link['stroke_width'] as num?)?.toDouble() ?? 2.5;
    final arrowHead = link['arrow_head'] as String? ?? 'arrow';
    final startCap = link['start_cap'] as String? ?? 'dot';

    return Card(
      color: AppTheme.surfaceLight,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text('Style de la ligne', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 12)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: LinksPanel.lineStyles.map((s) {
                return ChoiceChip(
                  label: Text(LinksPanel.lineStyleLabels[s] ?? s),
                  selected: lineStyle == s,
                  onSelected: (_) => state.updateLinkStyle(linkIndex, lineStyle: s),
                );
              }).toList(),
            ),
            const SizedBox(height: 16),
            const Text('Forme de la pointe', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 12)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: LinksPanel.arrowHeads.map((s) {
                return ChoiceChip(
                  label: Text(LinksPanel.arrowHeadLabels[s] ?? s),
                  selected: arrowHead == s,
                  onSelected: (_) => state.updateLinkStyle(linkIndex, arrowHead: s),
                );
              }).toList(),
            ),
            const SizedBox(height: 16),
            const Text('Forme du départ', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 12)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: LinksPanel.startCaps.map((s) {
                return ChoiceChip(
                  label: Text(LinksPanel.startCapLabels[s] ?? s),
                  selected: startCap == s,
                  onSelected: (_) => state.updateLinkStyle(linkIndex, startCap: s),
                );
              }).toList(),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                const Icon(Icons.swap_horiz, size: 20),
                const SizedBox(width: 8),
                const Text('Sens flèche inversé', style: TextStyle(fontSize: 12)),
                const SizedBox(width: 8),
                Switch(
                  value: arrowReversed,
                  onChanged: (_) => state.updateLinkStyle(linkIndex, arrowReversed: !arrowReversed),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                const Text('Épaisseur : ', style: TextStyle(fontSize: 12)),
                SizedBox(
                  width: 120,
                  child: Slider(
                    value: strokeW.clamp(1.0, 6.0),
                    min: 1,
                    max: 6,
                    divisions: 10,
                    onChanged: (v) => state.updateLinkStyle(linkIndex, strokeWidth: v),
                  ),
                ),
                Text('${strokeW.toStringAsFixed(1)}', style: const TextStyle(fontSize: 11)),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                FilledButton.icon(
                  icon: const Icon(Icons.edit, size: 18),
                  label: const Text('Cardinalités'),
                  onPressed: () => _showEditCardinalityDialog(context, state, linkIndex),
                ),
                const SizedBox(width: 12),
                TextButton.icon(
                  icon: const Icon(Icons.delete_outline, size: 18, color: AppTheme.error),
                  label: const Text('Supprimer le lien', style: TextStyle(color: AppTheme.error, fontWeight: FontWeight.w600)),
                  onPressed: () {
                    state.removeAssociationLinkAt(linkIndex);
                    state.selectNone();
                    if (context.mounted) {
                      Navigator.pop(context);
                      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Lien supprimé.')));
                    }
                  },
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  static Future<void> _showEditCardinalityDialog(BuildContext context, McdState state, int linkIndex) async {
    if (linkIndex < 0 || linkIndex >= state.associationLinks.length) return;
    final link = state.associationLinks[linkIndex];
    final cardEntity = link['card_entity'] as String? ?? link['cardinality'] as String? ?? '1,n';
    final cardAssoc = link['card_assoc'] as String? ?? '1,n';
    const cards = McdCanvas.mcdCardinalities;

    String selEntity = cardEntity;
    String selAssoc = cardAssoc;

    final result = await showDialog<({String cardEntity, String cardAssoc})>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setState) => AlertDialog(
          title: const Text('Modifier les cardinalités du lien'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text('Côté entité :', style: TextStyle(fontWeight: FontWeight.w500)),
              const SizedBox(height: 4),
              DropdownButton<String>(
                value: cards.contains(selEntity) ? selEntity : cards.first,
                isExpanded: true,
                items: cards.map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
                onChanged: (v) {
                  if (v != null) setState(() => selEntity = v);
                },
              ),
              const SizedBox(height: 16),
              const Text('Côté association :', style: TextStyle(fontWeight: FontWeight.w500)),
              const SizedBox(height: 4),
              DropdownButton<String>(
                value: cards.contains(selAssoc) ? selAssoc : cards.first,
                isExpanded: true,
                items: cards.map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
                onChanged: (v) {
                  if (v != null) setState(() => selAssoc = v);
                },
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Annuler')),
            FilledButton(
              onPressed: () => Navigator.pop(ctx, (cardEntity: selEntity, cardAssoc: selAssoc)),
              child: const Text('OK'),
            ),
          ],
        ),
      ),
    );
    if (result != null && context.mounted) {
      state.updateAssociationLinkCardinalities(linkIndex, result.cardEntity, result.cardAssoc);
    }
  }
}
