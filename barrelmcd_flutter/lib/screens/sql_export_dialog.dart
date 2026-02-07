import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../theme/app_theme.dart';

class SqlExportDialog {
  static void show(BuildContext context, String sql) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppTheme.surface,
        title: const Text('Script SQL'),
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
}
