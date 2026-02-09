import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../core/mcd_state.dart';
import '../theme/app_theme.dart';

/// Panneau MLD / SQL (comme Looping) : SGBD paramétrable, copie presse-papier.
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

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, dynamic>?>(
      future: context.read<McdState>().generateMld(),
      builder: (context, mldSnap) {
        final mld = mldSnap.data;
        return FutureBuilder<String?>(
          future: context.read<McdState>().generateSql(dbms: _dbms),
          builder: (context, sqlSnap) {
            final sql = sqlSnap.data ?? '';
            final loading = mldSnap.connectionState == ConnectionState.waiting || sqlSnap.connectionState == ConnectionState.waiting;
            return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Padding(
                  padding: const EdgeInsets.all(12),
                  child: Row(
                    children: [
                      const Text('MLD / SQL', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      const SizedBox(width: 16),
                      const Text('SGBD:', style: TextStyle(fontSize: 12)),
                      const SizedBox(width: 6),
                      DropdownButton<String>(
                        value: _dbms,
                        items: const [
                          DropdownMenuItem(value: 'mysql', child: Text('MySQL')),
                          DropdownMenuItem(value: 'postgresql', child: Text('PostgreSQL')),
                          DropdownMenuItem(value: 'sqlite', child: Text('SQLite')),
                        ],
                        onChanged: (v) {
                          if (v != null) setState(() => _dbms = v);
                        },
                      ),
                      const Spacer(),
                      if (loading) const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)),
                      IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(context)),
                    ],
                  ),
                ),
                const Divider(height: 1),
                Expanded(
                  child: DefaultTabController(
                    length: 2,
                    child: Column(
                      children: [
                        const TabBar(
                          labelColor: AppTheme.primary,
                          tabs: [
                            Tab(text: 'MLD'),
                            Tab(text: 'SQL'),
                          ],
                        ),
                        Expanded(
                          child: TabBarView(
                            children: [
                              _MldView(mld: mld, loading: loading),
                              _SqlView(sql: sql, loading: loading),
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
  }
}

class _MldView extends StatelessWidget {
  const _MldView({this.mld, required this.loading});

  final Map<String, dynamic>? mld;
  final bool loading;

  @override
  Widget build(BuildContext context) {
    if (loading) return const Center(child: CircularProgressIndicator());
    if (mld == null) return const Center(child: Text('Aucun MLD (vérifiez le serveur API)'));
    final tables = mld!['tables'] as Map<String, dynamic>? ?? {};
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
    final text = buf.toString();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              TextButton.icon(
                icon: const Icon(Icons.copy, size: 18),
                label: const Text('Copier'),
                onPressed: () {
                  Clipboard.setData(ClipboardData(text: text));
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('MLD copié dans le presse-papier')));
                },
              ),
            ],
          ),
        ),
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: SelectableText(text, style: const TextStyle(fontFamily: 'monospace', fontSize: 12)),
          ),
        ),
      ],
    );
  }
}

class _SqlView extends StatelessWidget {
  const _SqlView({required this.sql, required this.loading});

  final String sql;
  final bool loading;

  @override
  Widget build(BuildContext context) {
    if (loading) return const Center(child: CircularProgressIndicator());
    if (sql.isEmpty) return const Center(child: Text('Aucun SQL généré'));
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
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
