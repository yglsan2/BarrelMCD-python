import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

// Garde les const pour prefer_const_constructors ; évite le conflit avec unnecessary_const.
// ignore_for_file: unnecessary_const

class HelpDialog {
  static void show(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppTheme.surface,
        title: const Text('Aide BarrelMCD'),
        content: const SingleChildScrollView(
          child: const Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: const [
              Text('Création :', style: TextStyle(fontWeight: FontWeight.bold)),
              Text('• E : Entité\n• A : Association\n• L : Lien\n• Ctrl+L : Auto-Liens'),
              SizedBox(height: 12),
              Text('Navigation :', style: TextStyle(fontWeight: FontWeight.bold)),
              Text('• Z : Zoom +  • X : Zoom -  • F : Ajuster  • G : Grille'),
              SizedBox(height: 12),
              Text('Édition :', style: TextStyle(fontWeight: FontWeight.bold)),
              Text('• Suppr : Supprimer  • Ctrl+Z : Annuler  • Ctrl+Y : Répéter'),
              SizedBox(height: 12),
              Text('Import/Export :', style: TextStyle(fontWeight: FontWeight.bold)),
              Text('• Ctrl+M : Markdown  • Ctrl+E : SQL  • Ctrl+P : Image  • Ctrl+D : PDF'),
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
