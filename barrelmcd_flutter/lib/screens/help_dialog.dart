import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class HelpDialog {
  static void show(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppTheme.surface,
        title: const Text('Aide BarrelMCD'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Création :', style: TextStyle(fontWeight: FontWeight.bold)),
              const Text('• E : Entité\n• A : Association\n• L : Lien\n• Ctrl+L : Auto-Liens'),
              const SizedBox(height: 12),
              const Text('Navigation :', style: TextStyle(fontWeight: FontWeight.bold)),
              const Text('• Z : Zoom +  • X : Zoom -  • F : Ajuster  • G : Grille'),
              const SizedBox(height: 12),
              const Text('Édition :', style: TextStyle(fontWeight: FontWeight.bold)),
              const Text('• Suppr : Supprimer  • Ctrl+Z : Annuler  • Ctrl+Y : Répéter'),
              const SizedBox(height: 12),
              const Text('Import/Export :', style: TextStyle(fontWeight: FontWeight.bold)),
              const Text('• Ctrl+M : Markdown  • Ctrl+E : SQL  • Ctrl+P : Image  • Ctrl+D : PDF'),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Fermer')),
        ],
      ),
    );
  }
}
