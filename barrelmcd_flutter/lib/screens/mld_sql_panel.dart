import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/mcd_state.dart';
import '../theme/app_theme.dart';

/// Panneau MLD / SQL en temps réel (comme Looping) : affiche le MLD et le SQL générés.
class MldSqlPanel extends StatelessWidget {
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
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, dynamic>?>(
      future: context.read<McdState>().generateMld(),
      builder: (context, mldSnap) {
        final mld = mldSnap.data;
        return FutureBuilder<String?>(
          future: context.read<McdState>().generateSql(),
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
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: SelectableText(buf.toString(), style: const TextStyle(fontFamily: 'monospace', fontSize: 12)),
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
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: SelectableText(sql, style: const TextStyle(fontFamily: 'monospace', fontSize: 12)),
    );
  }
}
