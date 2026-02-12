import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// Lexique pédagogique : principes MCD, MLD, MPD, SQL et termes détaillés.
class GlossaryDialog {
  static void show(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) {
        final maxHeight = MediaQuery.sizeOf(ctx).height * 0.85;
        return AlertDialog(
          backgroundColor: AppTheme.surface,
          title: const Row(
            children: [
              Icon(Icons.menu_book, color: AppTheme.primary),
              SizedBox(width: 8),
              Text('Lexique Merise & SQL'),
            ],
          ),
          content: SizedBox(
            width: 580,
            child: ConstrainedBox(
              constraints: BoxConstraints(maxHeight: maxHeight),
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _sectionTitle(ctx, '1. Les trois niveaux : MCD, MLD, MPD'),
                    _paragraph(ctx, 'En Merise, on décrit les données à trois niveaux successifs. Chaque niveau est une « vue » plus proche de l’ordinateur.'),
                    _buildPrinciple(ctx,
                      'MCD (Modèle Conceptuel de Données)',
                      'Le MCD décrit « quoi » : les objets du métier et les liens entre eux, sans se soucier de la technique. On y trouve des entités (ex. Client, Produit, Commande) et des associations (ex. « passer une commande ») reliées par des liens. C’est le niveau où l’on se comprend avec le métier.',
                      'En résumé : schéma lisible par tout le monde, indépendant de tout logiciel ou base de données.',
                    ),
                    _buildPrinciple(ctx,
                      'MLD (Modèle Logique de Données)',
                      'Le MLD transforme le MCD en structure exploitable par un SGBD : des tables (une par entité, une par association « avec attributs » ou de liaison), des clés primaires et des clés étrangères. On choisit un type de SGBD (relationnel, etc.).',
                      'En résumé : traduction du MCD en tables et relations, prête pour la création de la base.',
                    ),
                    _buildPrinciple(ctx,
                      'MPD (Modèle Physique de Données)',
                      'Le MPD décrit comment les données sont réellement stockées : fichiers, index, types de colonnes précis (VARCHAR(255), INTEGER), contraintes techniques. C’est le niveau du SGBD (MySQL, PostgreSQL, etc.).',
                      'En résumé : implémentation concrète dans un moteur de base de données.',
                    ),
                    _sectionTitle(ctx, '2. Le MCD en détail'),
                    _paragraph(ctx, 'Le MCD est construit avec quatre briques : entités, attributs, associations et liens.'),
                    _buildPrinciple(ctx,
                      'Entité',
                      'Une entité représente un « type d’objet » du métier (Client, Article, Commande…). Chaque « exemplaire » concret (un client précis, une commande précise) s’appelle une occurrence. Une entité a un nom et des attributs (propriétés).',
                      'Exemple : l’entité Client a les attributs id_client, nom, email. Chaque client en base est une occurrence.',
                    ),
                    _buildPrinciple(ctx,
                      'Attribut',
                      'Propriété d’une entité ou d’une association (nom, date, quantité…). On précise pour chaque attribut s’il est clé primaire, unique, obligatoire, et son type (nombre, texte, date…).',
                      'Les attributs deviennent des colonnes dans le MLD puis en SQL.',
                    ),
                    _buildPrinciple(ctx,
                      'Association',
                      'Lien entre plusieurs entités qui a un sens métier (ex. « Un client passe des commandes »). Une association peut avoir ses propres attributs (ex. date de la commande, quantité). Elle est reliée aux entités par des liens, sur lesquels on indique les cardinalités.',
                      'En MLD : une association devient souvent une table (table de liaison ou table d’association avec attributs).',
                    ),
                    _buildPrinciple(ctx,
                      'Lien',
                      'Connexion entre une entité et une association. Chaque lien est étiqueté par une cardinalité (0,1 1,1 0,n 1,n) qui dit combien de fois une occurrence d’une entité peut participer à l’association (et réciproquement).',
                      'Exemple : « Un client peut passer 0,n commandes » et « Une commande est passée par 1,1 client ».',
                    ),
                    _sectionTitle(ctx, '3. Le MLD et les tables'),
                    _paragraph(ctx, 'Le MLD traduit entités et associations en tables. Les relations sont matérialisées par des clés étrangères.'),
                    _buildPrinciple(ctx,
                      'Table',
                      'Structure en lignes et colonnes. Chaque ligne = une occurrence ; chaque colonne = un attribut. Une table correspond en général à une entité du MCD, ou à une association (table de liaison ou table avec attributs).',
                      'Nom de table souvent au pluriel ou singulier selon les conventions : Clients, Commandes.',
                    ),
                    _buildPrinciple(ctx,
                      'Clé étrangère (FK)',
                      'Colonne(s) d’une table qui font référence à la clé primaire d’une autre table (ou de la même table). Elle « pointe » vers une occurrence précise. Elle matérialise le lien du MCD.',
                      'Exemple : la table Commandes a une colonne id_client qui référence Clients.id_client. Ainsi chaque commande est reliée à un client.',
                    ),
                    _buildPrinciple(ctx,
                      'Table de liaison',
                      'Table qui relie deux (ou plusieurs) entités sans avoir d’attributs métier propres, ou avec peu. En MCD, c’est une association entre deux entités. En MLD, elle contient au minimum les clés étrangères vers les deux entités (souvent sa clé primaire est la paire de ces clés).',
                      'Exemple : Ligne_commande lie Commande et Produit (avec attributs : quantité, prix_unitaire).',
                    ),
                    _sectionTitle(ctx, '4. SQL en bref'),
                    _paragraph(ctx, 'SQL est le langage utilisé pour définir et manipuler les données dans un SGBD relationnel. Il découle directement du MLD.'),
                    _buildPrinciple(ctx,
                      'DDL (Data Definition Language)',
                      'Partie du SQL qui « crée » la structure : CREATE TABLE, ALTER TABLE, contraintes (PRIMARY KEY, FOREIGN KEY, UNIQUE, NOT NULL). BarrelMCD génère du DDL à partir de votre MLD.',
                      'On l’utilise une fois (ou lors d’évolutions) pour créer les tables.',
                    ),
                    _buildPrinciple(ctx,
                      'DML (Data Manipulation Language)',
                      'Partie du SQL qui « manipule » les données : INSERT (ajouter), UPDATE (modifier), DELETE (supprimer), SELECT (lire). C’est ce que les applications utilisent au quotidien.',
                      'Le MCD/MLD ne décrit pas le DML, mais une bonne structure MCD facilite des requêtes SELECT claires.',
                    ),
                    _sectionTitle(ctx, '5. Termes à bien maîtriser'),
                    _buildTerm(ctx, 'Clé primaire (PK)', 'Attribut (ou ensemble d’attributs) qui identifie de façon unique chaque occurrence de l’entité.',
                        'Rôle : garantir l’unicité. Une seule clé primaire par entité.\nUsage : en MLD/SQL → PRIMARY KEY ; cible des clés étrangères. Souvent un identifiant technique (id) ou un identifiant métier.'),
                    _buildTerm(ctx, 'Clé secondaire / Unique (U)', 'Attribut dont la valeur ne peut pas être répétée dans l’entité (unicité), sans être la clé primaire.',
                        'Rôle : contrainte d’unicité (email, n° sécu…). Plusieurs attributs peuvent être « unique ».\nUsage : en SQL → UNIQUE. Utile pour des identifiants métier non choisis comme PK.'),
                    _buildTerm(ctx, 'Obligatoire (NOT NULL)', 'Attribut qui doit avoir une valeur pour chaque occurrence (pas de valeur nulle).',
                        'Rôle : éviter les données manquantes. En SQL → NOT NULL. La clé primaire est toujours obligatoire.'),
                    _buildTerm(ctx, 'Cardinalité', 'Nombre min et max d’occurrences liées entre une entité et une association.',
                        'Notation : 0,1 = zéro ou une ; 1,1 = exactement une ; 0,n = zéro ou plusieurs ; 1,n = au moins une.\nDétermine les contraintes en MLD (ex. clé étrangère NOT NULL si 1,1 côté entité).'),
                    _buildTerm(ctx, 'Entité faible', 'Entité dont l’existence dépend d’une autre (identification relative). Ex. Ligne_commande ne existe pas sans Commande.',
                        'En MCD : double bordure. En MLD : la PK de l’entité faible inclut souvent la clé de l’entité « père ».'),
                    _buildTerm(ctx, 'Entité fictive', 'Entité présente sur le MCD pour la lisibilité, non générée en table dans le MLD.',
                        'Rôle : clarifier le modèle (regroupement conceptuel). Ignorée à la génération MLD/SQL.'),
                    _buildTerm(ctx, 'Occurrence', 'Une occurrence est un « exemplaire » concret d’une entité ou d’une association (un client précis, une commande précise).',
                        'En base : une ligne dans une table = une occurrence de l’entité correspondante.'),
                    _buildTerm(ctx, 'SGBD', 'Système de Gestion de Base de Données (ex. MySQL, PostgreSQL, SQLite). Logiciel qui stocke les données et exécute le SQL.',
                        'Le MPD est implémenté dans un SGBD précis ; le MLD reste souvent générique (relationnel).'),
                    const SizedBox(height: 12),
                    Text('Références : méthode Merise, Barrel MCD, JMerise, ouvrages de modélisation de données.',
                        style: Theme.of(ctx).textTheme.bodySmall?.copyWith(color: AppTheme.textTertiary, fontStyle: FontStyle.italic)),
                  ],
                ),
              ),
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Fermer')),
          ],
        );
      },
    );
  }

  static Widget _sectionTitle(BuildContext context, String title) {
    return Padding(
      padding: const EdgeInsets.only(top: 8, bottom: 6),
      child: Text(
        title,
        style: Theme.of(context).textTheme.titleMedium?.copyWith(
          color: AppTheme.primary,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  static Widget _paragraph(BuildContext context, String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(text, style: Theme.of(context).textTheme.bodyMedium?.copyWith(height: 1.4)),
    );
  }

  static Widget _buildPrinciple(BuildContext context, String term, String definition, String resume) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(term, style: Theme.of(context).textTheme.titleSmall?.copyWith(color: AppTheme.primary, fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Text(definition, style: Theme.of(context).textTheme.bodyMedium?.copyWith(height: 1.35)),
          const SizedBox(height: 4),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: AppTheme.surfaceLight.withValues(alpha: 0.5),
              borderRadius: BorderRadius.circular(6),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('En résumé : ', style: Theme.of(context).textTheme.bodySmall?.copyWith(fontWeight: FontWeight.w600)),
                Expanded(child: Text(resume, style: Theme.of(context).textTheme.bodySmall?.copyWith(height: 1.35))),
              ],
            ),
          ),
        ],
      ),
    );
  }

  static Widget _buildTerm(BuildContext context, String term, String definition, String roleUsage) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(term, style: Theme.of(context).textTheme.titleSmall?.copyWith(color: AppTheme.primary, fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Text(definition, style: Theme.of(context).textTheme.bodyMedium?.copyWith(height: 1.35)),
          const SizedBox(height: 6),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
            decoration: BoxDecoration(
              color: AppTheme.surfaceLight.withValues(alpha: 0.6),
              borderRadius: BorderRadius.circular(6),
              border: Border.all(color: AppTheme.primary.withValues(alpha: 0.3)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Rôle et usage', style: Theme.of(context).textTheme.labelMedium?.copyWith(color: AppTheme.primary)),
                const SizedBox(height: 4),
                Text(roleUsage, style: Theme.of(context).textTheme.bodySmall?.copyWith(height: 1.35)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
