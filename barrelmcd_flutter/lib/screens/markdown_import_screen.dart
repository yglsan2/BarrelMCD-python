import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/mcd_state.dart';
import '../theme/app_theme.dart';

/// Dialogue d'import Markdown (équivalent MarkdownImportDialog Python).
/// Onglets : Fichier, Éditeur, Prévisualisation, Validation.
class MarkdownImportScreen extends StatefulWidget {
  const MarkdownImportScreen({super.key});

  @override
  State<MarkdownImportScreen> createState() => _MarkdownImportScreenState();
}

enum _ImportFormat { markdown, motsCodes }

class _MarkdownImportScreenState extends State<MarkdownImportScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final TextEditingController _editorController = TextEditingController();
  _ImportFormat _format = _ImportFormat.markdown;
  String _precisionLabel = 'Score de précision: --';
  Map<String, dynamic>? _parsedResult;
  bool _importEnabled = false;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _editorController.addListener(_onEditorChanged);
  }

  @override
  void dispose() {
    _tabController.dispose();
    _editorController.dispose();
    super.dispose();
  }

  void _onEditorChanged() {
    _parseInput();
  }

  Future<void> _parseInput() async {
    final content = _editorController.text.trim();
    if (content.isEmpty) {
      setState(() {
        _parsedResult = null;
        _importEnabled = false;
        _precisionLabel = _format == _ImportFormat.motsCodes ? 'Format: Mots codés' : 'Score de précision: --';
      });
      return;
    }
    final state = context.read<McdState>();
    final Map<String, dynamic>? r = _format == _ImportFormat.motsCodes
        ? await state.parseMotsCodes(content)
        : await state.parseMarkdown(content);
    if (r == null) return;
    setState(() {
      _parsedResult = r;
      if (_format == _ImportFormat.motsCodes) {
        _precisionLabel = 'Format: Mots codés';
      } else {
        _precisionLabel = 'Score de précision: ${(r['precision_score'] ?? 0).toStringAsFixed(1)}%';
      }
      _importEnabled = true;
    });
  }

  void _importMcd() {
    if (_parsedResult == null) return;
    final state = context.read<McdState>();
    final canvas = _parsedResult!['canvas'] as Map<String, dynamic>?;
    if (canvas != null) state.loadFromCanvasFormat(canvas);
    Navigator.of(context).pop();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(_format == _ImportFormat.motsCodes ? 'MCD importé (mots codés)' : 'MCD importé depuis Markdown')),
    );
  }

  void _generateTemplate() {
    const template = '''
# Mon modèle MCD

## Client
- id (integer) PK : identifiant
- nom (varchar) : nom du client
- email (varchar) : email

## Produit
- id (integer) PK : identifiant
- libelle (varchar) : libellé
- prix (decimal) : prix

### Client <-> Produit : Commande
**Une commande lie des clients et des produits**
Client : 1,1
Produit : 0,n
''';
    _editorController.text = template;
    _parseInput();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.surface,
      appBar: AppBar(
        title: const Text('Import Markdown - BarrelMCD'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Fichier', icon: Icon(Icons.folder)),
            Tab(text: 'Éditeur', icon: Icon(Icons.edit)),
            Tab(text: 'Prévisualisation', icon: Icon(Icons.preview)),
            Tab(text: 'Validation', icon: Icon(Icons.check_circle)),
          ],
        ),
      ),
      body: Column(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            color: AppTheme.surfaceDark,
            child: Row(
              children: [
                SegmentedButton<_ImportFormat>(
                  segments: const [
                    ButtonSegment(value: _ImportFormat.markdown, label: Text('Markdown'), icon: Icon(Icons.text_snippet)),
                    ButtonSegment(value: _ImportFormat.motsCodes, label: Text('Mots codés'), icon: Icon(Icons.code)),
                  ],
                  selected: {_format},
                  onSelectionChanged: (Set<_ImportFormat> s) {
                    setState(() {
                      _format = s.first;
                      _precisionLabel = _format == _ImportFormat.motsCodes ? 'Format: Mots codés' : 'Score de précision: --';
                    });
                    _parseInput();
                  },
                ),
                const SizedBox(width: 16),
                Text(_precisionLabel, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                const Spacer(),
              ],
            ),
          ),
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildFileTab(),
                _buildEditorTab(),
                _buildPreviewTab(),
                _buildValidationTab(),
              ],
            ),
          ),
          _buildButtons(),
        ],
      ),
    );
  }

  Widget _buildFileTab() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text('Sélectionnez un fichier .md ou collez son contenu dans l\'onglet Éditeur.'),
        const SizedBox(height: 16),
        OutlinedButton.icon(
          onPressed: () => ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Sélection fichier à implémenter'))),
          icon: const Icon(Icons.upload_file),
          label: const Text('Sélectionner un fichier Markdown'),
        ),
      ],
    );
  }

  Widget _buildEditorTab() {
    final syntaxHint = _format == _ImportFormat.motsCodes
        ? 'Syntaxe : Entité: attr1, attr2 | Assoc, 11 Entité1, 1N Entité2 (11=1,1 1N=1,n 01=0,1 0N=0,n)'
        : 'Syntaxe : ## Entité | - attribut (type) PK | ### Entité1 <-> Entité2 : Association | Cardinalités';
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            syntaxHint,
            style: const TextStyle(color: AppTheme.textSecondary, fontSize: 12),
          ),
          const SizedBox(height: 8),
          Expanded(
            child: TextField(
              controller: _editorController,
              maxLines: null,
              expands: true,
              style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
              decoration: const InputDecoration(
                hintText: 'Collez ou tapez votre MCD en Markdown...',
                alignLabelWithHint: true,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPreviewTab() {
    // Markdown renvoie parsed.entities (Map) et parsed.associations ; mots codés renvoie canvas.entities (List) et canvas.associations
    final parsed = _parsedResult?['parsed'];
    final canvas = _parsedResult?['canvas'] as Map?;
    final List<dynamic>? entitiesList = canvas?['entities'] as List?;
    final Map? entitiesMap = parsed?['entities'] as Map?;
    final List? associationsFromParsed = parsed?['associations'] as List?;
    final List? associationsFromCanvas = canvas?['associations'] as List?;
    final bool hasEntities = (entitiesMap != null && entitiesMap.isNotEmpty) || (entitiesList != null && entitiesList.isNotEmpty);
    final bool hasAssoc = (associationsFromParsed != null && associationsFromParsed.isNotEmpty) || (associationsFromCanvas != null && associationsFromCanvas.isNotEmpty);
    if (!hasEntities && !hasAssoc) {
      return const Center(child: Text('Aucune donnée à prévisualiser'));
    }
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text('Entités détectées', style: TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        if (entitiesMap != null)
          ...entitiesMap.entries.map((e) => ListTile(
                title: Text(e.key.toString()),
                subtitle: Text('${(e.value as Map)['attributes']?.length ?? 0} attributs'),
              )),
        if (entitiesList != null)
          ...entitiesList.map((e) => ListTile(
                title: Text((e as Map)['name']?.toString() ?? ''),
                subtitle: Text('${(e['attributes'] as List?)?.length ?? 0} attributs'),
              )),
        const SizedBox(height: 16),
        const Text('Associations détectées', style: TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        if (associationsFromParsed != null)
          ...associationsFromParsed.map((a) => ListTile(
                title: Text(a['name']?.toString() ?? ''),
                subtitle: Text('${a['entity1']} <-> ${a['entity2']}'),
              )),
        if (associationsFromCanvas != null)
          ...associationsFromCanvas.map((a) => ListTile(
                title: Text((a as Map)['name']?.toString() ?? ''),
                subtitle: Text((a['entities'] as List?)?.join(' <-> ') ?? ''),
              )),
      ],
    );
  }

  Widget _buildValidationTab() {
    final state = context.read<McdState>();
    final canvas = _parsedResult?['canvas'] as Map<String, dynamic>?;
    final future = _parsedResult != null ? state.validateMcd(canvas) : null;
    return FutureBuilder<List<String>>(
      future: future,
      builder: (context, snap) {
        final errs = snap.data ?? [];
        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(
              snap.connectionState == ConnectionState.waiting
                  ? 'Validation...'
                  : (errs.isEmpty ? 'MCD valide.' : 'Erreurs :'),
              style: TextStyle(
                color: snap.connectionState == ConnectionState.waiting
                    ? AppTheme.textSecondary
                    : (errs.isEmpty ? AppTheme.success : AppTheme.error),
              ),
            ),
            const SizedBox(height: 8),
            ...errs.map((e) => ListTile(leading: const Icon(Icons.error, color: AppTheme.error, size: 20), title: Text(e))),
          ],
        );
      },
    );
  }

  Widget _buildButtons() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          TextButton.icon(
            onPressed: _generateTemplate,
            icon: const Icon(Icons.add),
            label: const Text('Générer template'),
          ),
          const Spacer(),
          FilledButton(
            onPressed: _importEnabled ? _importMcd : null,
            style: FilledButton.styleFrom(backgroundColor: AppTheme.success),
            child: const Text('Importer le MCD'),
          ),
          const SizedBox(width: 8),
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Annuler')),
        ],
      ),
    );
  }
}
