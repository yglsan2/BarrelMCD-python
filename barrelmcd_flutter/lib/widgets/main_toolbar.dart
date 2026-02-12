import 'dart:convert';
import 'dart:ui' as ui;
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter/rendering.dart';
import 'package:provider/provider.dart';
import 'package:file_picker/file_picker.dart';
import 'dart:io';
import '../core/mcd_state.dart';
import '../core/canvas_mode.dart';
import 'mcd_canvas.dart';
import '../theme/app_theme.dart';
import '../screens/sql_export_dialog.dart';
import '../screens/help_dialog.dart';
import '../screens/glossary_dialog.dart';
import '../screens/elements_panel.dart';
import '../screens/attributes_panel.dart';
import '../screens/mld_sql_panel.dart';

/// Barre d'outils équivalente à la toolbar Python (Fichier, Entité, Association, Zoom, etc.).
class MainToolbar extends StatelessWidget {
  const MainToolbar({super.key, this.exportImageKey, this.canvasKey});

  final GlobalKey? exportImageKey;
  final GlobalKey<McdCanvasState>? canvasKey;

  static void triggerNew(BuildContext context) {
    context.read<McdState>().clear();
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Nouveau projet')));
  }

  static void triggerOpen(BuildContext context) {
    MainToolbar.openProject(context);
  }

  static void triggerSave(BuildContext context) {
    MainToolbar.saveProjectAs(context);
  }

  /// Transpose le MCD en MLD/MPD puis ouvre le panneau (bouton « Transposer MLD/MPD »).
  static Future<void> _transposerMldMpd(BuildContext context) async {
    final state = context.read<McdState>();
    if (state.entities.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Ajoutez au moins une entité au MCD pour transposer en MLD/MPD.')),
      );
      return;
    }
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Transposition MLD/MPD…'), duration: Duration(seconds: 1)),
    );
    await state.generateMld();
    for (final dbms in McdState.supportedDbms) {
      await state.generateMpd(dbms: dbms);
    }
    if (!context.mounted) return;
    MldSqlPanel.show(context);
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
      decoration: const BoxDecoration(
        color: AppTheme.toolbarBg,
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
                      _fileMenuButton(context),
                      const _ToolbarDivider(),
                      _modeButton(context, CanvasMode.select, Icons.select_all, 'Sélection', 'S'),
                      _modeButton(context, CanvasMode.addEntity, Icons.table_chart, 'Entité', 'E'),
                      _modeButton(context, CanvasMode.addAssociation, Icons.link, 'Association', 'A'),
                      _modeButton(context, CanvasMode.createLink, Icons.account_tree, 'Lien', 'L'),
                      _linkPrecisionButton(context),
                      _toolButton(context, Icons.auto_awesome, 'Auto-layout', 'Ctrl+L', () => _showAutoLayoutDialog(context)),
                    ]),
                    Row(mainAxisSize: MainAxisSize.min, children: [
                      const _ToolbarDivider(),
                      _toolButton(context, Icons.zoom_in, 'Zoom +', 'Z', () => canvasKey?.currentState?.zoomIn()),
                      _toolButton(context, Icons.zoom_out, 'Zoom -', 'X', () => canvasKey?.currentState?.zoomOut()),
                      _toolButton(context, Icons.fit_screen, 'Ajuster', 'F', () => canvasKey?.currentState?.fitToView(context.read<McdState>())),
                      _toolButton(context, Icons.grid_on, 'Grille', 'G', () => context.read<CanvasModeState>().toggleGrid()),
                      const _ToolbarDivider(),
                      Consumer<McdState>(
                        builder: (_, state, __) {
                          final isEntity = state.selectedType == 'entity' && state.selectedIndex >= 0;
                          final isAssoc = state.selectedType == 'association' && state.selectedIndex >= 0;
                          if (!isEntity && !isAssoc) return const SizedBox.shrink();
                          return Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Padding(
                                padding: const EdgeInsets.only(right: 4),
                                child: Tooltip(
                                  message: isEntity ? 'Modifier les attributs de l\'entité' : 'Modifier les attributs de l\'association',
                                  child: Material(
                                    color: AppTheme.buttonBg,
                                    borderRadius: BorderRadius.circular(4),
                                    child: InkWell(
                                      onTap: () {
                                        if (isEntity) {
                                          canvasKey?.currentState?.openEntityAttributesDialog(context);
                                        } else {
                                          canvasKey?.currentState?.openAssociationAttributesDialog(context);
                                        }
                                      },
                                      borderRadius: BorderRadius.circular(4),
                                      child: const Padding(
                                        padding: EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                                        child: Row(
                                          mainAxisSize: MainAxisSize.min,
                                          children: [
                                            Icon(Icons.tune, size: 18, color: AppTheme.textPrimary),
                                            SizedBox(width: 4),
                                            Text('Attributs', style: TextStyle(color: AppTheme.textPrimary, fontSize: 11, fontWeight: FontWeight.w500)),
                                          ],
                                        ),
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                              if (isEntity)
                                _toolButton(context, Icons.copy_all, 'Dupliquer l\'entité', '', () {
                                  final idx = state.selectedIndex ?? 0;
                                  final newIndex = state.duplicateEntity(idx);
                                  if (newIndex >= 0) state.selectEntity(newIndex);
                                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Entité dupliquée')));
                                }),
                            ],
                          );
                        },
                      ),
                      _toolButton(context, Icons.delete_outline, 'Supprimer', 'Suppr', () => _deleteSelected(context)),
                      Consumer<McdState>(
                        builder: (_, state, __) => _toolButton(context, Icons.undo, 'Annuler', 'Ctrl+Z', state.canUndo ? () => state.undo() : () {}),
                      ),
                      Consumer<McdState>(
                        builder: (_, state, __) => _toolButton(context, Icons.redo, 'Répéter', 'Ctrl+Y', state.canRedo ? () => state.redo() : () {}),
                      ),
                    ]),
                    Row(mainAxisSize: MainAxisSize.min, children: [
                      const _ToolbarDivider(),
                      _toolButton(context, Icons.schema, 'Transposer MLD/MPD', 'Ouvrir le panneau MLD/MPD/SQL', () => _transposerMldMpd(context)),
                      _toolButton(context, Icons.check_circle_outline, 'Valider', '', () => _validateMcd(context)),
                      _toolButton(context, Icons.code, 'SQL', 'Ctrl+E', () => _exportSql(context)),
                      _toolButton(context, Icons.image, 'Image', 'Ctrl+P', () => _exportImage(context)),
                      _toolButton(context, Icons.picture_as_pdf, 'PDF', 'Ctrl+D', () => _exportPdf(context)),
                    ]),
                    Row(mainAxisSize: MainAxisSize.min, children: [
                      const _ToolbarDivider(),
                      _toolButton(context, Icons.copy_all, 'Copier MCD', '', () => _copyMcdToClipboard(context)),
                      _toolButton(context, Icons.tune, 'Attributs…', '', () => AttributesPanel.show(context)),
                      _toolButton(context, Icons.list, 'Éléments', '', () => ElementsPanel.show(context)),
                      _toolButton(context, Icons.bug_report, 'Console', 'F12', () => _showConsole(context)),
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
                onTap: () {
                  try {
                    if (kDebugMode) debugPrint('[MainToolbar] mode tap: $mode (label=$label)');
                    modeState.setMode(mode);
                    if (mode == CanvasMode.addEntity) {
                      canvasKey?.currentState?.addNewEntityAtViewCenter();
                    } else if (mode == CanvasMode.addAssociation) {
                      canvasKey?.currentState?.addNewAssociationAtViewCenter();
                    } else if (mode == CanvasMode.createLink) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('Mode Lien : cliquez sur une entité puis une association (ou l\'inverse) pour créer un lien et choisir la cardinalité (0,1 1,1 0,n 1,n).'),
                          duration: Duration(seconds: 4),
                        ),
                      );
                    }
                  } catch (e, st) {
                    debugPrint('[MainToolbar] mode tap ERROR: $e\n$st');
                  }
                },
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

  Widget _linkPrecisionButton(BuildContext context) {
    return Consumer<CanvasModeState>(
      builder: (_, modeState, __) {
        final on = modeState.linkPrecisionMode;
        return Padding(
          padding: const EdgeInsets.only(right: 4),
          child: Tooltip(
            message: on
                ? 'Mode Précision : bras rotatifs et liens courbes (désactiver pour le mode simple)'
                : 'Mode Simple : liens droits comme Barrel. Cliquez pour le mode Précision, ou maintenez Ctrl pendant le tracé d\'un lien.',
            child: Material(
              color: on ? AppTheme.primary.withValues(alpha: 0.35) : AppTheme.buttonBg,
              borderRadius: BorderRadius.circular(4),
              child: InkWell(
                onTap: () => modeState.toggleLinkPrecisionMode(),
                borderRadius: BorderRadius.circular(4),
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(on ? Icons.push_pin : Icons.linear_scale, size: 18, color: AppTheme.textPrimary),
                      const SizedBox(width: 4),
                      Text(on ? 'Précision' : 'Aimant', style: const TextStyle(color: AppTheme.textPrimary, fontSize: 11, fontWeight: FontWeight.w500)),
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
      onSelected: (value) async {
        if (value.startsWith('_')) return;
        if (value == 'new') {
          _newProject(context);
          return;
        }
        if (value == 'open') {
          MainToolbar.openProject(context);
          return;
        }
        if (value == 'save') {
          _saveProject(context);
          return;
        }
        if (value == 'save_as') {
          MainToolbar.saveProjectAs(context);
          return;
        }
        if (value == 'open_mld') {
          MainToolbar.openMld(context);
          return;
        }
        if (value == 'save_mld') {
          MainToolbar.saveMld(context);
          return;
        }
        if (value == 'save_mpd') {
          MainToolbar.saveMpd(context);
          return;
        }
        if (value == 'export_sql') {
          MainToolbar.exportSql(context);
          return;
        }
        if (value == 'export_sql_all') {
          MainToolbar.exportSqlAll(context);
          return;
        }
        if (value == 'quit') return;
        if (value == 'new_entity') {
          canvasKey?.currentState?.addNewEntityAtViewCenter();
          return;
        }
        if (value == 'new_association') {
          canvasKey?.currentState?.addNewAssociationAtViewCenter();
          return;
        }
        if (value == 'attrs_panel') {
          AttributesPanel.show(context);
          return;
        }
        if (value.startsWith('entity_')) {
          final index = int.tryParse(value.substring(7)) ?? -1;
          if (index >= 0 && context.mounted) {
            await showEntityAttributesFor(context, index);
          }
          return;
        }
        if (value.startsWith('assoc_')) {
          final index = int.tryParse(value.substring(6)) ?? -1;
          if (index >= 0 && context.mounted) {
            await showAssociationTextFor(context, index);
          }
          return;
        }
        if (value == 'lexique') {
          GlossaryDialog.show(context);
          return;
        }
      },
      itemBuilder: (ctx) {
        final state = context.read<McdState>();
        final entities = state.entities;
        final associations = state.associations;
        final items = <PopupMenuEntry<String>>[
          const PopupMenuItem(value: 'new', child: Text('Nouveau (Ctrl+N)')),
          const PopupMenuItem(value: 'open', child: Text('Ouvrir... (Ctrl+O)')),
          const PopupMenuDivider(),
          const PopupMenuItem(value: 'new_entity', child: Text('Nouvelle entité')),
          const PopupMenuItem(value: 'new_association', child: Text('Nouvelle association')),
          const PopupMenuDivider(),
          const PopupMenuItem(value: 'save', child: Text('Enregistrer (Ctrl+S)')),
          const PopupMenuItem(value: 'save_as', child: Text('Enregistrer sous...')),
          const PopupMenuItem(value: 'open_mld', child: Text('Ouvrir un MLD...')),
          const PopupMenuDivider(),
          const PopupMenuItem(value: 'save_mld', child: Text('Enregistrer le MLD...')),
          const PopupMenuItem(value: 'save_mpd', child: Text('Enregistrer le MPD...')),
          const PopupMenuItem(value: 'export_sql', child: Text('Exporter le SQL...')),
          const PopupMenuItem(value: 'export_sql_all', child: Text('Exporter tout le SQL (tous SGBD)')),
          const PopupMenuDivider(),
          const PopupMenuItem(value: 'attrs_panel', child: ListTile(
            leading: Icon(Icons.tune, size: 20),
            title: Text('Ouvrir le panneau Attributs...'),
            contentPadding: EdgeInsets.zero,
            dense: true,
          )),
        ];
        if (entities.isNotEmpty || associations.isNotEmpty) {
          items.add(const PopupMenuDivider());
          items.add(const PopupMenuItem<String>(
            value: '_header_entities',
            enabled: false,
            child: Text('Entités — clic pour modifier les attributs', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
          ));
          for (final e in entities.asMap().entries) {
            final name = e.value['name'] as String? ?? 'Sans nom';
            final count = (e.value['attributes'] as List?)?.length ?? 0;
            items.add(PopupMenuItem(
              value: 'entity_${e.key}',
              child: ListTile(
                leading: const Icon(Icons.table_chart, size: 20),
                title: Text(name),
                subtitle: Text('$count attribut${count > 1 ? 's' : ''} — types, clé primaire, etc.'),
                contentPadding: EdgeInsets.zero,
                dense: true,
              ),
            ));
          }
          if (associations.isNotEmpty) {
            items.add(const PopupMenuDivider());
            items.add(const PopupMenuItem<String>(
              value: '_header_assoc',
              enabled: false,
              child: Text('Associations — clic pour modifier texte et bras', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
            ));
            for (final a in associations.asMap().entries) {
              final name = a.value['name'] as String? ?? 'Sans nom';
              final armCount = (a.value['arm_angles'] as List?)?.length ?? 2;
              final count = (a.value['attributes'] as List?)?.length ?? 0;
              items.add(PopupMenuItem(
                value: 'assoc_${a.key}',
                child: ListTile(
                  leading: const Icon(Icons.link, size: 20),
                  title: Text(name),
                  subtitle: Text('$armCount bras — $count attribut${count > 1 ? 's' : ''}'),
                  contentPadding: EdgeInsets.zero,
                  dense: true,
                ),
              ));
            }
          }
        }
        items.add(const PopupMenuDivider());
        items.add(const PopupMenuItem(value: 'lexique', child: ListTile(
          leading: Icon(Icons.menu_book, size: 20),
          title: Text('Lexique'),
          subtitle: const Text('Termes MCD, MLD, MPD et SQL'),
          contentPadding: EdgeInsets.zero,
          dense: true,
        )));
        items.add(const PopupMenuDivider());
        items.add(const PopupMenuItem(value: 'quit', child: Text('Quitter (Ctrl+Q)')));
        return items;
      },
      child: const Padding(
        padding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.folder_open, size: 20, color: AppTheme.textPrimary),
            SizedBox(width: 6),
            Text('Fichier', style: TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.bold, fontSize: 12)),
            Icon(Icons.arrow_drop_down, color: AppTheme.textPrimary),
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

  static Future<void> openProject(BuildContext context) async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['bar', 'json', 'loo'],
      withData: false,
    );
    if (result == null || result.files.isEmpty || result.files.single.path == null) return;
    final path = result.files.single.path!;
    try {
      final file = File(path);
      final content = await file.readAsString();
      final data = jsonDecode(content) as Map<String, dynamic>;
      // Support format Barrel/Flutter (position, association_links) et format Python (x,y, relations)
      final rawEntities = data['entities'] as List? ?? [];
      final rawAssociations = data['associations'] as List? ?? [];
      List<Map<String, dynamic>> entities = MainToolbar.normalizeEntities(rawEntities);
      List<Map<String, dynamic>> associations = MainToolbar.normalizeAssociations(rawAssociations);
      List<Map<String, dynamic>> associationLinks = MainToolbar.normalizeAssociationLinks(
        data['association_links'] as List?,
        rawAssociations,
        rawEntities,
      );
      final inheritance = data['inheritance_links'] as List? ?? [];
      final cifConstraints = data['cif_constraints'] as List? ?? [];
      final inheritanceSymbolPositions = data['inheritance_symbol_positions'] as Map<String, dynamic>? ?? {};
      if (!context.mounted) return;
      final state = context.read<McdState>();
      state.loadFromCanvasFormat({
        'entities': entities,
        'associations': associations,
        'association_links': associationLinks,
        'inheritance_links': inheritance,
        'cif_constraints': cifConstraints,
        'inheritance_symbol_positions': inheritanceSymbolPositions,
      });
      if (data.containsKey('mld') || data.keys.any((k) => k.startsWith('mpd_') || k.startsWith('sql_'))) {
        state.restoreMldMpdSqlCache(data);
      }
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Ouvert: $path')));
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Erreur: $e')));
      }
    }
  }

  static Future<void> openMld(BuildContext context) async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['mld', 'json'],
      withData: false,
    );
    if (result == null || result.files.isEmpty || result.files.single.path == null) return;
    final path = result.files.single.path!;
    try {
      final file = File(path);
      final content = await file.readAsString();
      final data = jsonDecode(content) as Map<String, dynamic>;
      if (!context.mounted) return;
      context.read<McdState>().setCachedMld(data);
      MldSqlPanel.show(context);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('MLD chargé: $path')));
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Erreur: $e')));
      }
    }
  }

  static Future<void> saveMld(BuildContext context) async {
    final state = context.read<McdState>();
    Map<String, dynamic>? mld = state.cachedMld;
    if (mld == null && state.entities.isNotEmpty) {
      mld = await state.generateMld();
      if (!context.mounted) return;
    }
    if (mld == null) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Aucun MLD à enregistrer (générez-en un depuis le panneau MLD/MPD/SQL).')));
      }
      return;
    }
    final path = await FilePicker.platform.saveFile(
      dialogTitle: 'Enregistrer le MLD',
      fileName: 'modele.mld',
      type: FileType.custom,
      allowedExtensions: ['mld', 'json'],
    );
    if (path == null || !context.mounted) return;
    try {
      final file = File(path);
      await file.writeAsString(const JsonEncoder.withIndent('  ').convert(mld), flush: true);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('MLD enregistré: $path')));
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Erreur: $e')));
      }
    }
  }

  static Future<void> saveMpd(BuildContext context) async {
    final state = context.read<McdState>();
    final dbms = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppTheme.surface,
        title: const Text('Enregistrer le MPD'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: McdState.supportedDbms
              .map((d) => ListTile(
                    title: Text(d),
                    onTap: () => Navigator.pop(ctx, d),
                  ))
              .toList(),
        ),
      ),
    );
    if (dbms == null || !context.mounted) return;
    Map<String, dynamic>? mpd = state.getCachedMpd(dbms);
    if (mpd == null && state.entities.isNotEmpty) {
      mpd = await state.generateMpd(dbms: dbms);
      if (!context.mounted) return;
    }
    if (mpd == null) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Impossible de générer le MPD.')));
      }
      return;
    }
    final path = await FilePicker.platform.saveFile(
      dialogTitle: 'Enregistrer le MPD ($dbms)',
      fileName: 'modele_$dbms.mpd',
      type: FileType.custom,
      allowedExtensions: ['mpd', 'json'],
    );
    if (path == null || !context.mounted) return;
    try {
      final file = File(path);
      await file.writeAsString(const JsonEncoder.withIndent('  ').convert(mpd), flush: true);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('MPD enregistré: $path')));
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Erreur: $e')));
      }
    }
  }

  static Future<void> exportSql(BuildContext context) async {
    final state = context.read<McdState>();
    final dbms = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppTheme.surface,
        title: const Text('Exporter le SQL'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: McdState.supportedDbms
              .map((d) => ListTile(
                    title: Text(d),
                    onTap: () => Navigator.pop(ctx, d),
                  ))
              .toList(),
        ),
      ),
    );
    if (dbms == null || !context.mounted) return;
    String? sql = state.getCachedSql(dbms);
    if (sql == null && state.entities.isNotEmpty) {
      sql = await state.generateSql(dbms: dbms);
      if (!context.mounted) return;
    }
    if (sql == null || sql.isEmpty) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Aucun SQL à exporter.')));
      }
      return;
    }
    final path = await FilePicker.platform.saveFile(
      dialogTitle: 'Exporter le SQL ($dbms)',
      fileName: 'schema_$dbms.sql',
      type: FileType.custom,
      allowedExtensions: ['sql'],
    );
    if (path == null || !context.mounted) return;
    try {
      final file = File(path);
      await file.writeAsString(sql, flush: true);
      final translations = state.getCachedSqlTranslations(dbms);
      final sqlOriginal = state.getCachedSqlOriginal(dbms);
      if (translations.isNotEmpty && sqlOriginal != null && sqlOriginal.isNotEmpty) {
        final sep = path.contains(RegExp(r'[/\\]')) ? (path.contains('/') ? '/' : r'\') : null;
        String originalPath;
        String originalFileName;
        if (sep != null) {
          final lastSep = path.lastIndexOf(sep);
          final dir = path.substring(0, lastSep);
          final baseName = path.substring(lastSep + 1);
          final nameWithoutExt = baseName.endsWith('.sql') ? baseName.substring(0, baseName.length - 4) : baseName;
          originalFileName = '${nameWithoutExt}_original.sql';
          originalPath = '$dir$sep$originalFileName';
        } else {
          originalFileName = path.endsWith('.sql') ? '${path.replaceRange(path.length - 4, path.length, '')}_original.sql' : '${path}_original.sql';
          originalPath = originalFileName;
        }
        try {
          await File(originalPath).writeAsString(sqlOriginal, flush: true);
        } catch (_) {}
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('SQL enregistré (traduit pour $dbms). Version originale : $originalFileName. Des types ont été convertis automatiquement.'),
              duration: const Duration(seconds: 4),
            ),
          );
        }
      } else if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('SQL enregistré: $path')));
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Erreur: $e')));
      }
    }
  }

  static Future<void> exportSqlAll(BuildContext context) async {
    final state = context.read<McdState>();
    if (state.entities.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Aucun MCD. Créez un modèle puis réessayez.')));
      return;
    }
    final directory = await FilePicker.platform.getDirectoryPath(dialogTitle: 'Dossier pour les scripts SQL');
    if (directory == null || !context.mounted) return;
    int saved = 0;
    for (final dbms in McdState.supportedDbms) {
      String? sql = state.getCachedSql(dbms);
      if (sql == null) sql = await state.generateSql(dbms: dbms);
      if (sql != null && sql.isNotEmpty) {
        try {
          final file = File('$directory/schema_$dbms.sql');
          await file.writeAsString(sql, flush: true);
          saved++;
        } catch (_) {}
      }
    }
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$saved script(s) SQL enregistré(s) dans $directory')));
    }
  }

  /// Normalise les entités : format import (x, y, primary) → Flutter (position, is_primary_key).
  static List<Map<String, dynamic>> normalizeEntities(List<dynamic> raw) {
    final out = <Map<String, dynamic>>[];
    for (final e in raw) {
      final map = Map<String, dynamic>.from(e as Map);
      if (map['position'] == null && (map['x'] != null || map['y'] != null)) {
        map['position'] = {
          'x': (map['x'] as num?)?.toDouble() ?? 100.0,
          'y': (map['y'] as num?)?.toDouble() ?? 100.0,
        };
      }
      map['position'] ??= {'x': 100.0, 'y': 100.0};
      final attrs = (map['attributes'] as List?)?.cast<Map<String, dynamic>>() ?? [];
      map['attributes'] = attrs.map((a) {
        final m = Map<String, dynamic>.from(a);
        if (m['is_primary_key'] == null && m['primary'] != null) {
          m['is_primary_key'] = m['primary'] == true;
        }
        m['type'] ??= 'VARCHAR(255)';
        return m;
      }).toList();
      map['name'] ??= 'Entité';
      out.add(map);
    }
    return out;
  }

  /// Normalise les associations : x,y → position.
  static List<Map<String, dynamic>> normalizeAssociations(List<dynamic> raw) {
    final out = <Map<String, dynamic>>[];
    for (final a in raw) {
      final map = Map<String, dynamic>.from(a as Map);
      if (map['position'] == null && (map['x'] != null || map['y'] != null)) {
        map['position'] = {
          'x': (map['x'] as num?)?.toDouble() ?? 300.0,
          'y': (map['y'] as num?)?.toDouble() ?? 300.0,
        };
      }
      map['position'] ??= {'x': 300.0, 'y': 300.0};
      map['name'] ??= 'Association';
      map['entities'] ??= [];
      map['cardinalities'] ??= {};
      out.add(map);
    }
    return out;
  }

  /// Construit association_links : soit depuis le champ existant, soit depuis relations (format import Barrel).
  static List<Map<String, dynamic>> normalizeAssociationLinks(
    List<dynamic>? links,
    List<dynamic> rawAssociations,
    List<dynamic> rawEntities,
  ) {
    if (links != null && links.isNotEmpty) {
      return links.map((l) => Map<String, dynamic>.from(l as Map)).toList();
    }
    // Format import : associations avec relations (entity_id, cardinality). On a besoin id -> nom entité.
    final idToName = <String, String>{};
    for (final e in rawEntities) {
      final m = e as Map<String, dynamic>;
      final id = m['id']?.toString();
      final name = m['name']?.toString();
      if (id != null && name != null) idToName[id] = name;
    }
    final result = <Map<String, dynamic>>[];
    for (final a in rawAssociations) {
      final assoc = a as Map<String, dynamic>;
      final assocName = assoc['name']?.toString() ?? 'Association';
      final relations = assoc['relations'] as List?;
      if (relations != null) {
        int armIndex = 0;
        for (final r in relations) {
          final rel = r as Map<String, dynamic>;
          final entityId = rel['entity_id']?.toString();
          final entityName = entityId != null ? idToName[entityId] : null;
          final card = rel['cardinality']?.toString() ?? '1,n';
          if (entityName != null) {
            result.add({
              'association': assocName,
              'entity': entityName,
              'card_entity': card,
              'card_assoc': rel['cardinality_assoc']?.toString() ?? '1,n',
              'arm_index': armIndex,
            });
            armIndex = (armIndex + 1) % 2;
          }
        }
      }
    }
    return result;
  }

  Future<void> _saveProject(BuildContext context) async {
    await MainToolbar.saveProjectAs(context);
  }

  static Future<void> saveProjectAs(BuildContext context) async {
    final path = await FilePicker.platform.saveFile(
      dialogTitle: 'Enregistrer le projet',
      fileName: 'projet.bar',
      type: FileType.custom,
      allowedExtensions: ['bar', 'json'],
    );
    if (path == null) return;
    if (!context.mounted) return;
    try {
      final state = context.read<McdState>();
      final data = <String, dynamic>{
        'version': '1.0',
        'format': 'barrelmcd',
        'entities': state.entities,
        'associations': state.associations,
        'association_links': state.associationLinks,
        'inheritance_links': state.inheritanceLinks,
        'cif_constraints': state.cifConstraints,
        'inheritance_symbol_positions': state.inheritanceSymbolPositions,
      };
      final mld = state.cachedMld;
      if (mld != null) data['mld'] = mld;
      for (final dbms in McdState.supportedDbms) {
        final mpd = state.getCachedMpd(dbms);
        if (mpd != null) data['mpd_$dbms'] = mpd;
        final sql = state.getCachedSql(dbms);
        if (sql != null && sql.isNotEmpty) data['sql_$dbms'] = sql;
        final sqlOrig = state.getCachedSqlOriginal(dbms);
        if (sqlOrig != null && sqlOrig.isNotEmpty) data['sql_original_$dbms'] = sqlOrig;
        final tr = state.getCachedSqlTranslations(dbms);
        if (tr.isNotEmpty) data['sql_translations_$dbms'] = tr;
      }
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

  /// Ouvre le dialogue « Paramètres des flèches » (marges et épaisseur par défaut).
  static Future<void> _showArrowParamsDialog(BuildContext context, McdState state) async {
    final startController = TextEditingController(text: state.arrowStartMargin.toString());
    final tipController = TextEditingController(text: state.arrowTipMargin.toString());
    final strokeController = TextEditingController(text: state.defaultStrokeWidth.toString());
    await showDialog<void>(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          backgroundColor: AppTheme.surface,
          title: const Text('Paramètres des flèches'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                TextField(
                  controller: startController,
                  decoration: const InputDecoration(
                    labelText: 'Marge début de flèche (px)',
                    hintText: '10',
                    border: OutlineInputBorder(),
                  ),
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: tipController,
                  decoration: const InputDecoration(
                    labelText: 'Marge pointe de flèche (px)',
                    hintText: '12',
                    border: OutlineInputBorder(),
                  ),
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: strokeController,
                  decoration: const InputDecoration(
                    labelText: 'Épaisseur par défaut (1–6)',
                    hintText: '2.5',
                    border: OutlineInputBorder(),
                  ),
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.of(ctx).pop(), child: const Text('Annuler')),
            FilledButton(
              onPressed: () {
                final start = double.tryParse(startController.text);
                final tip = double.tryParse(tipController.text);
                final stroke = double.tryParse(strokeController.text);
                if (start != null) state.arrowStartMargin = start;
                if (tip != null) state.arrowTipMargin = tip;
                if (stroke != null) state.defaultStrokeWidth = stroke;
                Navigator.of(ctx).pop();
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Paramètres des flèches enregistrés.')));
                }
              },
              child: const Text('OK'),
            ),
          ],
        );
      },
    );
  }

  static Future<void> showAutoLayoutDialog(BuildContext context, {GlobalKey<McdCanvasState>? canvasKey}) {
    return showDialog<void>(
      context: context,
      builder: (ctx) {
        final state = context.read<McdState>();
        if (state.entities.isEmpty && state.associations.isEmpty) {
          return AlertDialog(
            title: const Text('Auto-layout'),
            content: const Text('Ajoutez au moins une entité ou une association pour utiliser l\'auto-layout.'),
            actions: [TextButton(onPressed: () => Navigator.of(ctx).pop(), child: const Text('OK'))],
          );
        }
        void afterLayout() {
          canvasKey?.currentState?.fitToView(state);
          if (ctx.mounted) Navigator.of(ctx).pop();
          if (context.mounted) {
            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Mise en page appliquée. Vue ajustée.')));
          }
        }
        void afterImproveLinks() {
          canvasKey?.currentState?.fitToView(state);
          if (ctx.mounted) Navigator.of(ctx).pop();
          if (context.mounted) {
            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Liens améliorés (accroches recentrées).')));
          }
        }
        return AlertDialog(
          title: const Text('Auto-layout'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Mise en page : réorganise entités et associations, puis recalcule les liaisons.',
                  style: TextStyle(fontWeight: FontWeight.w500),
                ),
                const SizedBox(height: 8),
                const Text(
                  '• Hiérarchique : entités en grille, associations en dessous.\n'
                  '• Force-directed : ressorts et répulsion.\n'
                  '• Circulaire : nœuds sur un cercle (robuste, style BarrelMCD).',
                ),
                const SizedBox(height: 16),
                const Divider(),
                const Text(
                  'Liens et flèches',
                  style: TextStyle(fontWeight: FontWeight.w500),
                ),
                const SizedBox(height: 4),
                const Text(
                  'Améliorer les liens uniquement : recentre les accroches et réinitialise les pointes des flèches sans déplacer les nœuds.',
                  style: TextStyle(fontSize: 12),
                ),
                const SizedBox(height: 8),
                TextButton.icon(
                  onPressed: () async {
                    await _showArrowParamsDialog(ctx, state);
                  },
                  icon: const Icon(Icons.tune, size: 18),
                  label: const Text('Paramètres des flèches…'),
                ),
                const SizedBox(height: 4),
                TextButton.icon(
                  onPressed: () {
                    if (state.associationLinks.isEmpty) {
                      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Aucun lien à modifier.')));
                      return;
                    }
                    state.applyDefaultStrokeWidthToAllLinks();
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Épaisseur par défaut appliquée à tous les liens.')));
                    }
                  },
                  icon: const Icon(Icons.format_paint, size: 18),
                  label: const Text('Appliquer l\'épaisseur par défaut à tous les liens'),
                ),
                const SizedBox(height: 12),
                const Text(
                  'Création automatique de liens',
                  style: TextStyle(fontWeight: FontWeight.w500),
                ),
                const SizedBox(height: 4),
                const Text(
                  'Proposer les liens manquants : pour chaque association, propose des liens vers les entités les plus proches (non encore liées).',
                  style: TextStyle(fontSize: 12),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.of(ctx).pop(), child: const Text('Annuler')),
            OutlinedButton(
              onPressed: () async {
                final suggested = state.suggestLinksByProximity(maxLinksPerAssociation: 2);
                if (suggested.isEmpty) {
                  if (ctx.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Aucun lien manquant à proposer.')));
                  }
                  return;
                }
                final confirmed = await showDialog<List<({String association, String entity})>>(
                  context: ctx,
                  builder: (dialogCtx) => AlertDialog(
                    title: const Text('Liens proposés'),
                    content: SingleChildScrollView(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Créer les liens suivants ? (association — entité)'),
                          const SizedBox(height: 8),
                          ...suggested.map((p) => Padding(
                            padding: const EdgeInsets.symmetric(vertical: 2),
                            child: Text('• ${p.association} — ${p.entity}'),
                          )),
                        ],
                      ),
                    ),
                    actions: [
                      TextButton(
                        onPressed: () => Navigator.of(dialogCtx).pop(null),
                        child: const Text('Annuler'),
                      ),
                      FilledButton(
                        onPressed: () => Navigator.of(dialogCtx).pop(suggested),
                        child: const Text('Créer ces liens'),
                      ),
                    ],
                  ),
                );
                if (confirmed != null && confirmed.isNotEmpty && ctx.mounted) {
                  for (final p in confirmed) {
                    state.addAssociationLink(p.association, p.entity, '1,n', '1,n');
                  }
                  if (ctx.mounted) Navigator.of(ctx).pop();
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('${confirmed.length} lien(s) créé(s).')));
                  }
                  canvasKey?.currentState?.fitToView(state);
                }
              },
              child: const Text('Proposer les liens'),
            ),
            OutlinedButton(
              onPressed: () {
                state.improveLinksOnly();
                afterImproveLinks();
              },
              child: const Text('Améliorer les liens'),
            ),
            OutlinedButton(
              onPressed: () {
                state.applyDefaultArrowParamsToAllLinks();
                if (ctx.mounted) Navigator.of(ctx).pop();
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Paramètres par défaut appliqués à toutes les flèches.')));
                }
              },
              child: const Text('Appliquer défaut flèches'),
            ),
            TextButton(
              onPressed: () {
                state.applyAutoLayout('hierarchical');
                afterLayout();
              },
              child: const Text('Hiérarchique'),
            ),
            TextButton(
              onPressed: () {
                state.applyAutoLayout('circular');
                afterLayout();
              },
              child: const Text('Circulaire'),
            ),
            FilledButton(
              onPressed: () {
                state.applyAutoLayout('force');
                afterLayout();
              },
              child: const Text('Force-directed'),
            ),
          ],
        );
      },
    );
  }

  void _showAutoLayoutDialog(BuildContext context) {
    MainToolbar.showAutoLayoutDialog(context, canvasKey: canvasKey);
  }

  void _deleteSelected(BuildContext context) {
    final state = context.read<McdState>();
    state.deleteSelected();
  }

  Future<void> _exportImage(BuildContext context) async {
    final key = exportImageKey;
    if (key?.currentContext == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Export image indisponible')));
      return;
    }
    final boundary = key!.currentContext!.findRenderObject() as RenderRepaintBoundary?;
    if (boundary == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Export image indisponible')));
      return;
    }
    try {
      final image = await boundary.toImage(pixelRatio: 2.0);
      final byteData = await image.toByteData(format: ui.ImageByteFormat.png);
      if (byteData == null) throw Exception('toByteData null');
      final path = await FilePicker.platform.saveFile(
        dialogTitle: 'Enregistrer l\'image',
        fileName: 'mcd.png',
        type: FileType.custom,
        allowedExtensions: ['png'],
      );
      if (path != null) {
        final file = File(path);
        await file.writeAsBytes(byteData.buffer.asUint8List());
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Image enregistrée: $path')));
        }
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Erreur export: $e')));
      }
    }
  }

  Future<void> _validateMcd(BuildContext context) async {
    final state = context.read<McdState>();
    final errors = await state.validateMcd();
    if (!context.mounted) return;
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Validation MCD'),
        content: SizedBox(
          width: 400,
          child: errors.isEmpty
              ? const Text('Aucune erreur. Le modèle est valide.')
              : Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: errors.map((e) => Padding(
                    padding: const EdgeInsets.only(bottom: 6),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Icon(Icons.error_outline, size: 20, color: AppTheme.error),
                        const SizedBox(width: 8),
                        Expanded(child: Text(e)),
                      ],
                    ),
                  )).toList(),
                ),
        ),
        actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Fermer'))],
      ),
    );
  }

  void _exportPdf(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Export PDF : à intégrer')));
  }

  Future<void> _exportSql(BuildContext context) async {
    final state = context.read<McdState>();
    if (state.entities.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Aucun MCD. Créez un modèle puis ouvrez le panneau MLD/MPD/SQL ou exportez le SQL.')));
      return;
    }
    SqlExportDialog.showMultiDbms(context);
  }

  void _copyMcdToClipboard(BuildContext context) {
    final state = context.read<McdState>();
    final json = const JsonEncoder.withIndent('  ').convert(state.mcdData);
    Clipboard.setData(ClipboardData(text: json));
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('MCD copié dans le presse-papier (JSON)')));
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

class _ArrowParamsDialog extends StatefulWidget {
  const _ArrowParamsDialog({required this.state});

  final McdState state;

  @override
  State<_ArrowParamsDialog> createState() => _ArrowParamsDialogState();
}

class _ArrowParamsDialogState extends State<_ArrowParamsDialog> {
  late final TextEditingController _startController;
  late final TextEditingController _tipController;
  late final TextEditingController _strokeController;

  @override
  void initState() {
    super.initState();
    _startController = TextEditingController(text: widget.state.arrowStartMargin.toInt().toString());
    _tipController = TextEditingController(text: widget.state.arrowTipMargin.toInt().toString());
    _strokeController = TextEditingController(text: widget.state.defaultStrokeWidth.toStringAsFixed(1));
  }

  @override
  void dispose() {
    _startController.dispose();
    _tipController.dispose();
    _strokeController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Paramètres des flèches'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: _startController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: 'Marge début de flèche (px)',
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _tipController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: 'Marge pointe de flèche (px)',
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _strokeController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: 'Épaisseur par défaut (1–6)',
              ),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Annuler')),
        FilledButton(
          onPressed: () {
            final start = (double.tryParse(_startController.text.replaceAll(',', '.')) ?? widget.state.arrowStartMargin).clamp(0.0, 50.0);
            final tip = (double.tryParse(_tipController.text.replaceAll(',', '.')) ?? widget.state.arrowTipMargin).clamp(0.0, 50.0);
            final stroke = (double.tryParse(_strokeController.text.replaceAll(',', '.')) ?? widget.state.defaultStrokeWidth).clamp(1.0, 6.0);
            widget.state.arrowStartMargin = start;
            widget.state.arrowTipMargin = tip;
            widget.state.defaultStrokeWidth = stroke;
            Navigator.of(context).pop();
          },
          child: const Text('OK'),
        ),
      ],
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
