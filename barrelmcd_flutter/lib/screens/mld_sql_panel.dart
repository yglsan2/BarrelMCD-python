import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../core/mcd_state.dart';
import '../theme/app_theme.dart';
import '../widgets/schema_diagram.dart';

/// Panneau MLD / SQL : SGBD paramétrable, copie presse-papier.
class MldSqlPanel extends StatefulWidget {
  const MldSqlPanel({super.key});

  static void show(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppTheme.surface,
      builder: (ctx) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        minChildSize: 0.3,
        maxChildSize: 0.95,
        expand: false,
        builder: (_, scrollController) => const MldSqlPanel(),
      ),
    );
  }

  @override
  State<MldSqlPanel> createState() => _MldSqlPanelState();
}

class _MldSqlPanelState extends State<MldSqlPanel> {
  String _dbms = 'mysql';
  bool _refreshing = false;

  Future<void> _refreshAll() async {
    if (_refreshing) return;
    setState(() => _refreshing = true);
    final state = context.read<McdState>();
    if (state.entities.isNotEmpty) {
      await state.generateMld();
      for (final dbms in McdState.supportedDbms) {
        await state.generateMpd(dbms: dbms);
        await state.generateSql(dbms: dbms);
      }
    }
    if (mounted) setState(() => _refreshing = false);
  }

  @override
  Widget build(BuildContext context) {
    final state = context.read<McdState>();
    final cachedMld = state.cachedMld;
    final mldFuture = cachedMld != null ? null : (state.entities.isNotEmpty ? state.generateMld() : Future<Map<String, dynamic>?>.value(null));
    return FutureBuilder<Map<String, dynamic>?>(
      future: mldFuture,
      initialData: cachedMld,
      builder: (context, mldSnap) {
        final mld = mldSnap.data ?? cachedMld;
        return FutureBuilder<Map<String, dynamic>?>(
          key: ValueKey(_dbms),
          future: state.getCachedMpd(_dbms) != null
              ? Future<Map<String, dynamic>?>.value(state.getCachedMpd(_dbms))
              : (state.entities.isNotEmpty ? state.generateMpd(dbms: _dbms) : Future<Map<String, dynamic>?>.value(null)),
          initialData: state.getCachedMpd(_dbms),
          builder: (context, mpdSnap) {
            final mpd = mpdSnap.data;
            return FutureBuilder<String?>(
              key: ValueKey('sql_$_dbms'),
              future: state.getCachedSql(_dbms) != null
                  ? Future<String?>.value(state.getCachedSql(_dbms))
                  : (state.entities.isNotEmpty ? state.generateSql(dbms: _dbms) : Future<String?>.value(null)),
              initialData: state.getCachedSql(_dbms),
              builder: (context, sqlSnap) {
                final sql = sqlSnap.data ?? state.getCachedSql(_dbms) ?? '';
                final translations = state.getCachedSqlTranslations(_dbms);
                final loading = mldSnap.connectionState == ConnectionState.waiting
                    || mpdSnap.connectionState == ConnectionState.waiting
                    || sqlSnap.connectionState == ConnectionState.waiting;
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Padding(
                      padding: const EdgeInsets.all(12),
                      child: Row(
                        children: [
                          const Text('MLD / MPD / SQL', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                          const SizedBox(width: 16),
                          const Text('SGBD:', style: TextStyle(fontSize: 12)),
                          const SizedBox(width: 6),
                          DropdownButton<String>(
                            value: _dbms,
                            items: const [
                              DropdownMenuItem(value: 'mysql', child: Text('MySQL')),
                              DropdownMenuItem(value: 'postgresql', child: Text('PostgreSQL')),
                              DropdownMenuItem(value: 'sqlite', child: Text('SQLite')),
                              DropdownMenuItem(value: 'sqlserver', child: Text('SQL Server')),
                            ],
                            onChanged: (v) {
                              if (v != null) setState(() => _dbms = v);
                            },
                          ),
                          const Spacer(),
                          if (loading || _refreshing) const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)),
                          IconButton(
                            icon: const Icon(Icons.refresh, size: 22),
                            tooltip: 'Rafraîchir MLD / MPD / SQL (transposition instantanée)',
                            onPressed: _refreshing ? null : _refreshAll,
                          ),
                          IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(context)),
                        ],
                      ),
                    ),
                    const Divider(height: 1),
                    Expanded(
                      child: DefaultTabController(
                        length: 3,
                        child: Column(
                          children: [
                            const TabBar(
                              labelColor: AppTheme.primary,
                              tabs: [
                                Tab(text: 'MLD'),
                                Tab(text: 'MPD'),
                                Tab(text: 'SQL'),
                              ],
                            ),
                            Expanded(
                              child: TabBarView(
                                children: [
                                  _MldView(mld: mld, loading: loading, apiError: state.lastError, mcdEntities: state.entities, mcdAssociations: state.associations, mcdAssociationLinks: state.associationLinks),
                                  _MpdView(mpd: mpd, loading: loading, apiError: state.lastError, mcdEntities: state.entities, mcdAssociations: state.associations, mcdAssociationLinks: state.associationLinks),
                                  _SqlView(sql: sql, loading: loading, dbms: _dbms, translations: translations),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                );
              },
            );
          },
        );
      },
    );
  }
}

String _mldToText(Map<String, dynamic>? mld) {
  if (mld == null) return '';
  final tables = mld['tables'] as Map<String, dynamic>? ?? {};
  final buf = StringBuffer();
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

class _MldView extends StatelessWidget {
  const _MldView({
    this.mld,
    required this.loading,
    this.apiError,
    this.mcdEntities = const [],
    this.mcdAssociations = const [],
    this.mcdAssociationLinks,
  });

  final Map<String, dynamic>? mld;
  final bool loading;
  /// Erreur API éventuelle (affichée si mld == null).
  final String? apiError;
  /// Positions MCD pour afficher le MLD comme une « photo du MCD ».
  final List<Map<String, dynamic>> mcdEntities;
  final List<Map<String, dynamic>> mcdAssociations;
  final List<Map<String, dynamic>>? mcdAssociationLinks;

  @override
  Widget build(BuildContext context) {
    if (loading) return const Center(child: CircularProgressIndicator());
    if (mld == null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.table_chart, size: 48, color: AppTheme.textTertiary),
              const SizedBox(height: 12),
              const Text('Aucun MLD (vérifiez le serveur API)', textAlign: TextAlign.center, style: TextStyle(color: AppTheme.textSecondary)),
              if (apiError != null && apiError!.isNotEmpty) ...[
                const SizedBox(height: 12),
                Text(apiError!, style: const TextStyle(color: AppTheme.error, fontSize: 12), textAlign: TextAlign.center, maxLines: 8, overflow: TextOverflow.ellipsis),
              ],
            ],
          ),
        ),
      );
    }
    final text = _mldToText(mld);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              TextButton.icon(
                icon: const Icon(Icons.copy, size: 18),
                label: const Text('Copier le texte'),
                onPressed: () {
                  Clipboard.setData(ClipboardData(text: text));
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('MLD copié dans le presse-papier')));
                },
              ),
            ],
          ),
        ),
        Expanded(
          child: SchemaDiagramView(
            data: mld,
            title: 'MLD',
            showTypes: false,
            mcdEntities: mcdEntities,
            mcdAssociations: mcdAssociations,
            mcdAssociationLinks: mcdAssociationLinks,
          ),
        ),
      ],
    );
  }
}

class _MpdView extends StatelessWidget {
  const _MpdView({
    this.mpd,
    required this.loading,
    this.apiError,
    this.mcdEntities = const [],
    this.mcdAssociations = const [],
    this.mcdAssociationLinks,
  });

  final Map<String, dynamic>? mpd;
  final bool loading;
  final String? apiError;
  final List<Map<String, dynamic>> mcdEntities;
  final List<Map<String, dynamic>> mcdAssociations;
  final List<Map<String, dynamic>>? mcdAssociationLinks;

  @override
  Widget build(BuildContext context) {
    if (loading) return const Center(child: CircularProgressIndicator());
    if (mpd == null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.table_chart, size: 48, color: AppTheme.textTertiary),
              const SizedBox(height: 12),
              const Text('Aucun MPD (vérifiez le serveur API)', textAlign: TextAlign.center, style: TextStyle(color: AppTheme.textSecondary)),
              if (apiError != null && apiError!.isNotEmpty) ...[
                const SizedBox(height: 12),
                Text(apiError!, style: const TextStyle(color: AppTheme.error, fontSize: 12), textAlign: TextAlign.center, maxLines: 8, overflow: TextOverflow.ellipsis),
              ],
            ],
          ),
        ),
      );
    }
    return SchemaDiagramView(
      data: mpd,
      title: 'MPD',
      showTypes: true,
      mcdEntities: mcdEntities,
      mcdAssociations: mcdAssociations,
      mcdAssociationLinks: mcdAssociationLinks,
    );
  }
}

class _SqlView extends StatelessWidget {
  const _SqlView({
    required this.sql,
    required this.loading,
    this.dbms = 'mysql',
    this.translations = const [],
  });

  final String sql;
  final bool loading;
  final String dbms;
  final List<Map<String, dynamic>> translations;

  static String _dbmsLabel(String dbms) {
    switch (dbms) {
      case 'mysql': return 'MySQL';
      case 'postgresql': return 'PostgreSQL';
      case 'sqlite': return 'SQLite';
      case 'sqlserver': return 'SQL Server';
      default: return dbms;
    }
  }

  @override
  Widget build(BuildContext context) {
    if (loading) return const Center(child: CircularProgressIndicator());
    if (sql.isEmpty) return const Center(child: Text('Aucun SQL généré'));
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (translations.isNotEmpty)
          Material(
            color: AppTheme.primary.withOpacity(0.12),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              child: Row(
                children: [
                  Icon(Icons.info_outline, size: 20, color: AppTheme.primary),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Des types SQL ont été traduits automatiquement pour ${_dbmsLabel(dbms)} (ex. ${(translations.first['original_type'] ?? '')} → ${translations.first['translated_type'] ?? ''}). La version avec les types d\'origine est enregistrée localement.',
                      style: const TextStyle(fontSize: 12),
                    ),
                  ),
                ],
              ),
            ),
          ),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              TextButton.icon(
                icon: const Icon(Icons.copy, size: 18),
                label: const Text('Copier SQL'),
                onPressed: () {
                  Clipboard.setData(ClipboardData(text: sql));
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('SQL copié dans le presse-papier')));
                },
              ),
            ],
          ),
        ),
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: SelectableText(sql, style: const TextStyle(fontFamily: 'monospace', fontSize: 12)),
          ),
        ),
      ],
    );
  }
}
