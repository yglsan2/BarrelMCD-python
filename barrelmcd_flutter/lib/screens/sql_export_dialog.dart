import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../core/mcd_state.dart';
import '../theme/app_theme.dart';

class SqlExportDialog {
  /// Affiche le SQL pour un dialecte (bouton SQL / Ctrl+E).
  static void show(BuildContext context, String sql, {String dbms = 'mysql'}) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppTheme.surface,
        title: Text('Script SQL — $dbms'),
        content: SizedBox(
          width: 500,
          height: 400,
          child: SelectableText(sql, style: const TextStyle(fontFamily: 'monospace', fontSize: 12)),
        ),
        actions: [
          TextButton(
            onPressed: () {
              Clipboard.setData(ClipboardData(text: sql));
              ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('SQL copié')));
            },
            child: const Text('Copier'),
          ),
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Fermer')),
        ],
      ),
    );
  }

  /// Affiche les onglets SQL pour tous les SGBD (MySQL, PostgreSQL, SQLite, SQL Server) pour passer de l’un à l’autre.
  static void showMultiDbms(BuildContext context) async {
    final state = context.read<McdState>();
    final Map<String, String> sqlByDbms = {};
    for (final dbms in McdState.supportedDbms) {
      final sql = state.getCachedSql(dbms);
      if (sql != null && sql.isNotEmpty) {
        sqlByDbms[dbms] = sql;
      } else if (state.entities.isNotEmpty) {
        final s = await state.generateSql(dbms: dbms);
        if (s != null && s.isNotEmpty) sqlByDbms[dbms] = s;
      }
    }
    if (!context.mounted) return;
    if (sqlByDbms.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Aucun SQL à afficher.')));
      return;
    }
    showDialog(
      context: context,
      builder: (ctx) => _MultiSqlDialog(sqlByDbms: sqlByDbms),
    );
  }
}

class _MultiSqlDialog extends StatefulWidget {
  const _MultiSqlDialog({required this.sqlByDbms});

  final Map<String, String> sqlByDbms;

  @override
  State<_MultiSqlDialog> createState() => _MultiSqlDialogState();
}

class _MultiSqlDialogState extends State<_MultiSqlDialog> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: widget.sqlByDbms.length, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final keys = widget.sqlByDbms.keys.toList();
    return AlertDialog(
      backgroundColor: AppTheme.surface,
      title: const Text('Scripts SQL — tous les SGBD'),
      content: SizedBox(
        width: 560,
        height: 440,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TabBar(
              controller: _tabController,
              labelColor: AppTheme.primary,
              tabs: keys.map((d) => Tab(text: d)).toList(),
            ),
            Expanded(
              child: TabBarView(
                controller: _tabController,
                children: keys
                    .map((dbms) => SingleChildScrollView(
                          padding: const EdgeInsets.all(8),
                          child: SelectableText(
                            widget.sqlByDbms[dbms]!,
                            style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
                          ),
                        ))
                    .toList(),
              ),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () {
            final dbms = keys[_tabController.index];
            Clipboard.setData(ClipboardData(text: widget.sqlByDbms[dbms]!));
            ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('SQL $dbms copié')));
          },
          child: const Text('Copier (dialecte actif)'),
        ),
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Fermer')),
      ],
    );
  }
}
