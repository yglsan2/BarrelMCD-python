import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:file_picker/file_picker.dart';
import 'dart:io';
import '../core/mcd_state.dart';
import '../core/canvas_mode.dart';
import '../theme/app_theme.dart';
import '../screens/home_screen.dart';
import '../screens/sql_export_dialog.dart';
import '../screens/help_dialog.dart';
import '../screens/elements_panel.dart';
import '../screens/mld_sql_panel.dart';

/// Barre d'outils équivalente à la toolbar Python (Fichier, Entité, Association, Zoom, etc.).
class MainToolbar extends StatelessWidget {
  const MainToolbar({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
      decoration: const BoxDecoration(
        color: AppTheme.toolbarBg,
        border: Border(bottom: BorderSide(color: AppTheme.surfaceLight, width: 1)),
      ),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            _fileMenuButton(context),
            const _ToolbarDivider(),
            _modeButton(context, CanvasMode.select, Icons.select_all, 'Sélection', 'S'),
            _modeButton(context, CanvasMode.addEntity, Icons.table_chart, 'Entité', 'E'),
            _modeButton(context, CanvasMode.addAssociation, Icons.link, 'Association', 'A'),
            _modeButton(context, CanvasMode.createLink, Icons.account_tree, 'Lien', 'L'),
            _toolButton(context, Icons.auto_awesome, 'Auto-Liens', 'Ctrl+L', () => _autoLinks(context)),
            const _ToolbarDivider(),
            _toolButton(context, Icons.zoom_in, 'Zoom +', 'Z', () {}),
            _toolButton(context, Icons.zoom_out, 'Zoom -', 'X', () {}),
            _toolButton(context, Icons.fit_screen, 'Ajuster', 'F', () {}),
            _toolButton(context, Icons.grid_on, 'Grille', 'G', () => context.read<CanvasModeState>().toggleGrid()),
            const _ToolbarDivider(),
            _toolButton(context, Icons.delete_outline, 'Supprimer', 'Suppr', () => _deleteSelected(context)),
            Consumer<McdState>(
              builder: (_, state, __) => _toolButton(
                context,
                Icons.undo,
                'Annuler',
                'Ctrl+Z',
                state.canUndo ? () => state.undo() : () {},
              ),
            ),
            Consumer<McdState>(
              builder: (_, state, __) => _toolButton(
                context,
                Icons.redo,
                'Répéter',
                'Ctrl+Y',
                state.canRedo ? () => state.redo() : () {},
              ),
            ),
            const _ToolbarDivider(),
            _toolButton(context, Icons.upload_file, 'Importer', 'Ctrl+I', () => _importData(context)),
            _toolButton(context, Icons.text_snippet, 'Markdown', 'Ctrl+M', () => HomeScreen.openMarkdownImport(context)),
            _toolButton(context, Icons.schema, 'MLD/SQL', '', () => MldSqlPanel.show(context)),
            _toolButton(context, Icons.code, 'SQL', 'Ctrl+E', () => _exportSql(context)),
            _toolButton(context, Icons.image, 'Image', 'Ctrl+P', () => _exportImage(context)),
            _toolButton(context, Icons.picture_as_pdf, 'PDF', 'Ctrl+D', () => _exportPdf(context)),
            const _ToolbarDivider(),
            _toolButton(context, Icons.list, 'Éléments', '', () => ElementsPanel.show(context)),
            _toolButton(context, Icons.help_outline, 'Aide', 'F1', () => HelpDialog.show(context)),
            _toolButton(context, Icons.bug_report, 'Console', 'F12', () => _showConsole(context)),
          ],
        ),
      ),
    );
  }

  Widget _modeButton(BuildContext context, CanvasMode mode, IconData icon, String label, String shortcut) {
    return Consumer<CanvasModeState>(
      builder: (_, modeState, __) {
        final selected = modeState.mode == mode;
        return Padding(
          padding: const EdgeInsets.only(right: 4),
          child: Tooltip(
            message: '$label ($shortcut)',
            child: Material(
              color: selected ? AppTheme.primary.withValues(alpha: 0.3) : AppTheme.buttonBg,
              borderRadius: BorderRadius.circular(4),
              child: InkWell(
                onTap: () => modeState.setMode(mode),
                borderRadius: BorderRadius.circular(4),
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(icon, size: 18, color: AppTheme.textPrimary),
                      const SizedBox(width: 4),
                      Text(label, style: const TextStyle(color: AppTheme.textPrimary, fontSize: 11, fontWeight: FontWeight.w500)),
                    ],
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _fileMenuButton(BuildContext context) {
    return PopupMenuButton<String>(
      offset: const Offset(0, 40),
      color: AppTheme.surface,
      onSelected: (value) {
        switch (value) {
          case 'new':
            _newProject(context);
            break;
          case 'open':
            _openProject(context);
            break;
          case 'save':
            _saveProject(context);
            break;
          case 'save_as':
            _saveProjectAs(context);
            break;
          case 'quit':
            break;
        }
      },
      itemBuilder: (ctx) => [
        const PopupMenuItem(value: 'new', child: Text('Nouveau (Ctrl+N)')),
        const PopupMenuItem(value: 'open', child: Text('Ouvrir... (Ctrl+O)')),
        const PopupMenuDivider(),
        const PopupMenuItem(value: 'save', child: Text('Enregistrer (Ctrl+S)')),
        const PopupMenuItem(value: 'save_as', child: Text('Enregistrer sous...')),
        const PopupMenuDivider(),
        const PopupMenuItem(value: 'quit', child: Text('Quitter (Ctrl+Q)')),
      ],
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.folder_open, size: 20, color: AppTheme.textPrimary),
            const SizedBox(width: 6),
            Text('Fichier', style: TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.bold, fontSize: 12)),
            const Icon(Icons.arrow_drop_down, color: AppTheme.textPrimary),
          ],
        ),
      ),
    );
  }

  Widget _toolButton(BuildContext context, IconData icon, String label, String shortcut, VoidCallback onTap) {
    return Padding(
      padding: const EdgeInsets.only(right: 4),
      child: Tooltip(
        message: shortcut.isEmpty ? label : '$label ($shortcut)',
        child: Material(
          color: AppTheme.buttonBg,
          borderRadius: BorderRadius.circular(4),
          child: InkWell(
            onTap: onTap,
            borderRadius: BorderRadius.circular(4),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(icon, size: 18, color: AppTheme.textPrimary),
                  const SizedBox(width: 4),
                  Text(label, style: const TextStyle(color: AppTheme.textPrimary, fontSize: 11, fontWeight: FontWeight.w500)),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  void _newProject(BuildContext context) {
    context.read<McdState>().clear();
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Nouveau projet')));
    }
  }

  Future<void> _openProject(BuildContext context) async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['bar', 'json'],
      withData: false,
    );
    if (result == null || result.files.isEmpty || result.files.single.path == null) return;
    final path = result.files.single.path!;
    try {
      final file = File(path);
      final content = await file.readAsString();
      final data = jsonDecode(content) as Map<String, dynamic>;
      final entities = data['entities'] as List?;
      final associations = data['associations'] as List?;
      final links = data['association_links'] as List?;
      final inheritance = data['inheritance_links'] as List?;
      context.read<McdState>().loadFromCanvasFormat({
        'entities': entities ?? [],
        'associations': associations ?? [],
        'association_links': links ?? [],
        'inheritance_links': inheritance ?? [],
      });
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Ouvert: $path')));
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Erreur: $e')));
      }
    }
  }

  Future<void> _saveProject(BuildContext context) async {
    await _saveProjectAs(context);
  }

  Future<void> _saveProjectAs(BuildContext context) async {
    final path = await FilePicker.platform.saveFile(
      dialogTitle: 'Enregistrer le projet',
      fileName: 'projet.bar',
      type: FileType.custom,
      allowedExtensions: ['bar', 'json'],
    );
    if (path == null) return;
    try {
      final state = context.read<McdState>();
      final data = {
        'version': '1.0',
        'format': 'barrelmcd',
        'entities': state.entities,
        'associations': state.associations,
        'association_links': state.associationLinks,
        'inheritance_links': state.inheritanceLinks,
      };
      final file = File(path);
      await file.writeAsString(const JsonEncoder.withIndent('  ').convert(data), flush: true);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Enregistré: $path')));
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Erreur: $e')));
      }
    }
  }

  void _autoLinks(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Auto-liens : créez des associations puis reliez-les aux entités avec le mode Lien.')));
  }

  void _deleteSelected(BuildContext context) {
    final state = context.read<McdState>();
    state.deleteSelected();
  }

  void _importData(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Utilisez Markdown (Ctrl+M) ou Ouvrir un fichier .bar/.json')));
  }

  void _exportImage(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Export image : à intégrer (capture du canvas)')));
  }

  void _exportPdf(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Export PDF : à intégrer')));
  }

  Future<void> _exportSql(BuildContext context) async {
    final state = context.read<McdState>();
    final sql = await state.generateSql();
    if (context.mounted) {
      if (sql != null && sql.isNotEmpty) {
        SqlExportDialog.show(context, sql);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(state.lastError ?? 'Aucun MCD ou erreur API. Vérifiez que le serveur Python tourne.')),
        );
      }
    }
  }

  void _showConsole(BuildContext context) {
    final state = context.read<McdState>();
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppTheme.surface,
        title: const Text('Console / Log'),
        content: SingleChildScrollView(
          child: Text(state.logMessages.join('\n'), style: const TextStyle(fontSize: 12, fontFamily: 'monospace')),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Fermer')),
        ],
      ),
    );
  }
}

class _ToolbarDivider extends StatelessWidget {
  const _ToolbarDivider();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 1,
      height: 24,
      margin: const EdgeInsets.symmetric(horizontal: 8),
      color: AppTheme.surfaceLight,
    );
  }
}
