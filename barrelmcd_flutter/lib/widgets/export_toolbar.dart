import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../core/mcd_state.dart';
import '../theme/app_theme.dart';
import '../screens/markdown_import_screen.dart';
import '../screens/mld_sql_panel.dart';
import '../screens/help_dialog.dart';
import '../screens/glossary_dialog.dart';
import '../screens/inheritance_panel.dart';
import '../screens/cif_panel.dart';
import '../screens/links_panel.dart';
import 'main_toolbar.dart';

/// Deuxième barre d'outils : Markdown, MLD, MPD, SQL — conversion directe.
class ExportToolbar extends StatelessWidget {
  const ExportToolbar({super.key});

  static String _formatMldAsText(Map<String, dynamic> mld) {
    final buf = StringBuffer();
    final tables = mld['tables'] as Map<String, dynamic>? ?? {};
    for (final e in tables.entries) {
      buf.writeln('Table: ${e.key}');
      final cols = (e.value as Map)['columns'] as List? ?? [];
      for (final c in cols) {
        final col = c as Map;
        buf.writeln('  - ${col['name']} ${col['type']}');
      }
      buf.writeln();
    }
    final fks = mld['foreign_keys'] as List? ?? [];
    if (fks.isNotEmpty) {
      buf.writeln('Clés étrangères:');
      for (final fk in fks) {
        final m = fk is Map ? fk as Map<String, dynamic> : {};
        buf.writeln('  - ${m['table']}.${m['column']} -> ${m['referenced_table']}.${m['referenced_column']}');
      }
    }
    return buf.toString();
  }

  static String _formatMpdAsText(Map<String, dynamic> mpd) {
    final buf = StringBuffer();
    buf.writeln('MPD (dbms: ${mpd['dbms'] ?? 'mysql'})\n');
    final tables = mpd['tables'] as Map<String, dynamic>? ?? {};
    for (final e in tables.entries) {
      buf.writeln('Table: ${e.key}');
      final cols = (e.value as Map)['columns'] as List? ?? [];
      for (final c in cols) {
        final col = c as Map;
        buf.writeln('  - ${col['name']} ${col['type']}');
      }
      buf.writeln();
    }
    return buf.toString();
  }

  static Future<void> _showConvertDialog(
    BuildContext context, {
    required String title,
    required Future<String?> Function() loadContent,
    String emptyMessage = 'Aucun contenu (vérifiez le serveur API).',
  }) async {
    final content = await loadContent();
    if (!context.mounted) return;
    final text = content ?? '';
    final isEmpty = text.isEmpty;
    await showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(title),
        content: SizedBox(
          width: 520,
          height: 400,
          child: isEmpty
              ? Center(child: Text(emptyMessage, textAlign: TextAlign.center))
              : Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        TextButton.icon(
                          icon: const Icon(Icons.copy, size: 18),
                          label: const Text('Copier'),
                          onPressed: () {
                            Clipboard.setData(ClipboardData(text: text));
                            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Copié dans le presse-papier')));
                          },
                        ),
                      ],
                    ),
                    Expanded(
                      child: SingleChildScrollView(
                        child: SelectableText(
                          text,
                          style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
                        ),
                      ),
                    ),
                  ],
                ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Fermer')),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: const BoxDecoration(
        color: AppTheme.surfaceLight,
        border: Border(bottom: BorderSide(color: AppTheme.surfaceLight, width: 1)),
      ),
      child: LayoutBuilder(
        builder: (context, constraints) {
          return SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: ConstrainedBox(
              constraints: BoxConstraints(minWidth: constraints.maxWidth),
              child: Padding(
                padding: const EdgeInsets.only(right: 16),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Row(mainAxisSize: MainAxisSize.min, children: [
                      _btn(context, Icons.upload_file, 'Importer', 'Ctrl+I', () => MainToolbar.openProject(context)),
                      _btn(context, Icons.text_snippet, 'Markdown', 'Ctrl+M', () {
                        Navigator.of(context).push(MaterialPageRoute(builder: (_) => const MarkdownImportScreen()));
                      }),
                      _btnTransposer(context),
                      Container(width: 1, height: 22, margin: const EdgeInsets.symmetric(horizontal: 6), color: AppTheme.textSecondary.withOpacity(0.35)),
                      _btn(context, Icons.table_chart, 'MLD', 'Convertir en MLD (texte)', () => _convertToMld(context)),
                      _btn(context, Icons.storage, 'MPD', 'Convertir en MPD (texte)', () => _convertToMpd(context)),
                      _btn(context, Icons.code, 'SQL', 'Convertir en SQL', () => _convertToSql(context)),
                      TextButton(
                        onPressed: () => MldSqlPanel.show(context),
                        child: const Text('Ouvrir MLD/SQL…', style: TextStyle(fontSize: 11)),
                      ),
                      Container(width: 1, height: 22, margin: const EdgeInsets.symmetric(horizontal: 6), color: AppTheme.textSecondary.withOpacity(0.35)),
                      _btn(context, Icons.alt_route, 'Flèches', 'Modifier les flèches et liens (style, épaisseur, cardinalités, supprimer)', () => LinksPanel.show(context)),
                      _btnCardinalityUml(context),
                      _btn(context, Icons.account_tree, 'Héritage', 'Placer un symbole d\'héritage sur le dessin (glissez pour positionner). Clic droit sur le symbole pour ouvrir le panneau.', () {
                        context.read<McdState>().ensureStandaloneInheritanceSymbol(2500, 2500);
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('Symbole héritage placé au centre. Glissez-le pour le positionner. Clic droit sur le symbole pour ouvrir le panneau Héritage.'), duration: Duration(seconds: 4)),
                          );
                        }
                      }),
                      _btn(context, Icons.rule, 'CIF / CIFF', 'Contraintes d\'intégrité fonctionnelle', () => _showCifCiffPlaceDialog(context)),
                    ]),
                    Row(mainAxisSize: MainAxisSize.min, children: [
                      Container(width: 1, height: 22, margin: const EdgeInsets.symmetric(horizontal: 6), color: AppTheme.textSecondary.withOpacity(0.35)),
                      _btn(context, Icons.help_outline, 'Aide', 'F1', () => _showHelp(context)),
                      const SizedBox(width: 4),
                      _btn(context, Icons.menu_book, 'Lexique', '', () => _showGlossary(context)),
                    ]),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  /// Bouton principal : transposer le MCD en MLD/MPD et afficher le panneau avec les schémas.
  Widget _btnTransposer(BuildContext context) {
    return Tooltip(
      message: 'Transposer le MCD en MLD et MPD puis afficher les schémas',
      child: Material(
        color: AppTheme.primary.withOpacity(0.2),
        borderRadius: BorderRadius.circular(4),
        child: InkWell(
          onTap: () async {
            final state = context.read<McdState>();
            if (state.entities.isEmpty) {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Ajoutez au moins une entité au MCD pour transposer en MLD/MPD.')),
              );
              return;
            }
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Transposition MLD/MPD en cours…'), duration: Duration(seconds: 1)),
            );
            await state.generateMld();
            for (final dbms in McdState.supportedDbms) {
              await state.generateMpd(dbms: dbms);
            }
            if (!context.mounted) return;
            MldSqlPanel.show(context);
          },
          borderRadius: BorderRadius.circular(4),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.schema, size: 18, color: AppTheme.primary),
                const SizedBox(width: 6),
                Text('Transposer MLD/MPD', style: TextStyle(color: AppTheme.primary, fontSize: 11, fontWeight: FontWeight.w600)),
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _showHelp(BuildContext context) {
    HelpDialog.show(context);
  }

  void _showGlossary(BuildContext context) {
    GlossaryDialog.show(context);
  }

  /// Demande CIF ou CIFF puis place un logo sur le dessin (déplaçable).
  Future<void> _showCifCiffPlaceDialog(BuildContext context) async {
    final choice = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Placer une CIF ou une CIFF'),
        content: const Text(
          'Choisissez le type de contrainte à placer sur le dessin. Vous pourrez ensuite la déplacer où vous voulez.',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, null), child: const Text('Annuler')),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, 'CIF'),
            child: const Text('CIF'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, 'CIFF'),
            child: const Text('CIFF'),
          ),
        ],
      ),
    );
    if (choice == null || !context.mounted) return;
    final state = context.read<McdState>();
    final count = state.cifConstraints.length;
    const baseX = 2500.0, baseY = 2500.0;
    final x = baseX + count * 120;
    final y = baseY;
    state.addCifConstraint({
      'name': choice,
      'type': 'functional',
      'description': '',
      'entities': <String>[],
      'associations': <String>[],
      'attributes': <String>[],
      'is_enabled': true,
      'position': {'x': x, 'y': y},
    });
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('$choice placée au centre. Glissez-la pour la positionner. Clic droit pour modifier ou supprimer.'), duration: const Duration(seconds: 4)),
      );
    }
  }

  /// Bouton toggle : afficher les cardinalités en notation UML (0..1, 1..*) au lieu du MCD (0,1, 1,n).
  Widget _btnCardinalityUml(BuildContext context) {
    final state = context.watch<McdState>();
    final active = state.showUmlCardinalities;
    return Tooltip(
      message: active
          ? 'Réafficher les cardinalités MCD (0,1 1,n)'
          : 'Afficher les cardinalités en notation UML (0..1, 1..*) à la place du MCD',
      child: Material(
        color: active ? AppTheme.primary.withOpacity(0.2) : Colors.transparent,
        borderRadius: BorderRadius.circular(4),
        child: InkWell(
          onTap: () => state.toggleUmlCardinalities(),
          borderRadius: BorderRadius.circular(4),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  Icons.numbers,
                  size: 18,
                  color: active ? AppTheme.primary : AppTheme.textSecondary,
                ),
                const SizedBox(width: 4),
                Text(
                  'Card. UML',
                  style: TextStyle(
                    fontSize: 11,
                    color: active ? AppTheme.primary : AppTheme.textPrimary,
                    fontWeight: active ? FontWeight.w600 : FontWeight.normal,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _btn(BuildContext context, IconData icon, String label, String tooltip, VoidCallback onTap) {
    return Tooltip(
      message: tooltip,
      child: Material(
        color: AppTheme.buttonBg,
        borderRadius: BorderRadius.circular(4),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(4),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(icon, size: 18, color: AppTheme.textPrimary),
                const SizedBox(width: 6),
                Text(label, style: const TextStyle(color: AppTheme.textPrimary, fontSize: 11, fontWeight: FontWeight.w500)),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _convertToMld(BuildContext context) async {
    final state = context.read<McdState>();
    await _showConvertDialog(
      context,
      title: 'MLD — Modèle Logique de Données',
      loadContent: () async {
        final mld = await state.generateMld();
        if (mld == null) return null;
        return ExportToolbar._formatMldAsText(mld);
      },
    );
  }

  Future<void> _convertToMpd(BuildContext context) async {
    final state = context.read<McdState>();
    await _showConvertDialog(
      context,
      title: 'MPD — Modèle Physique de Données',
      loadContent: () async {
        final mpd = await state.generateMpd(dbms: 'mysql');
        if (mpd == null) return null;
        return ExportToolbar._formatMpdAsText(mpd);
      },
    );
  }

  Future<void> _convertToSql(BuildContext context) async {
    final state = context.read<McdState>();
    await _showConvertDialog(
      context,
      title: 'SQL généré',
      loadContent: () => state.generateSql(dbms: 'mysql'),
      emptyMessage: 'Aucun SQL (MCD vide ou serveur API injoignable).',
    );
  }
}
