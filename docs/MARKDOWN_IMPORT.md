# Import Markdown - BarrelMCD

## Vue d'ensemble

BarrelMCD dispose maintenant d'une fonctionnalité d'import depuis des fichiers Markdown. Cette fonctionnalité permet de générer automatiquement un Modèle Conceptuel de Données (MCD) à partir d'une description textuelle en format Markdown.

## Fonctionnalités

### ✨ Parsing automatique
- Détection automatique des entités (titres de niveau 2)
- Détection automatique des associations (titres de niveau 3)
- Parsing des attributs et leurs types
- Détection des clés primaires (PK)
- Détection des cardinalités

### 🎯 Interface utilisateur intuitive
- Dialogue d'import avec onglets multiples
- Prévisualisation en temps réel
- Validation automatique du MCD
- Génération de templates

### 🔧 Formats supportés
- Fichiers `.md` et `.markdown`
- Édition directe dans l'interface
- Export vers JSON

## Utilisation

### 1. Accès à la fonctionnalité

**Via la barre d'outils :**
- Cliquez sur le bouton "Markdown" dans la barre d'outils
- Ou utilisez le raccourci `Ctrl+M`

**Via le menu :**
- Fichier → Importer → Depuis Markdown

### 2. Interface d'import

Le dialogue d'import comprend 4 onglets :

#### 📁 Onglet Fichier
- Sélection d'un fichier Markdown existant
- Prévisualisation du contenu

#### ✏️ Onglet Éditeur
- Édition directe du contenu Markdown
- Mise à jour en temps réel

#### 👁️ Onglet Prévisualisation
- Affichage des entités détectées
- Affichage des associations détectées
- Statistiques du MCD

#### ✅ Onglet Validation
- Validation automatique du MCD
- Affichage des erreurs éventuelles
- Statistiques détaillées

### 3. Syntaxe Markdown

#### Entités
```markdown
## NomEntité
- attribut1 (type) : description
- attribut2 (type) : description
- id (integer) PK : identifiant unique
```

#### Associations
```markdown
### Entité1 <-> Entité2 : NomAssociation
**Description de l'association**
Entité1 : 1,1
Entité2 : 0,n
```

#### Types d'attributs supportés
- `integer` : Nombre entier
- `varchar` : Chaîne de caractères
- `text` : Texte long
- `date` : Date
- `datetime` : Date et heure
- `decimal` : Nombre décimal
- `boolean` : Booléen
- `char` : Caractère unique

#### Cardinalités supportées
- `1,1` : Un à un
- `1,n` : Un à plusieurs
- `n,1` : Plusieurs à un
- `n,n` : Plusieurs à plusieurs
- `0,1` : Zéro à un
- `0,n` : Zéro à plusieurs

## Exemples

### Exemple simple - Système de bibliothèque

```markdown
# Modèle Conceptuel de Données - Bibliothèque

## Livre
- id (integer) PK : identifiant unique
- titre (varchar) : titre du livre
- auteur (varchar) : nom de l'auteur
- isbn (varchar) : numéro ISBN
- prix (decimal) : prix du livre

## Lecteur
- id (integer) PK : identifiant unique
- nom (varchar) : nom du lecteur
- email (varchar) : adresse email
- date_inscription (date) : date d'inscription

### Livre <-> Lecteur : Emprunte
**Un lecteur peut emprunter plusieurs livres**
Livre : 1,1
Lecteur : 0,n
```

### Exemple complexe - E-commerce

```markdown
# Modèle Conceptuel de Données - E-commerce

## Client
- id (integer) PK : identifiant unique
- nom (varchar) : nom du client
- email (varchar) : adresse email
- telephone (varchar) : numéro de téléphone
- adresse (text) : adresse complète

## Produit
- id (integer) PK : identifiant unique
- nom (varchar) : nom du produit
- description (text) : description détaillée
- prix (decimal) : prix unitaire
- stock (integer) : quantité en stock
- categorie_id (integer) FK : référence vers catégorie

## Categorie
- id (integer) PK : identifiant unique
- nom (varchar) : nom de la catégorie
- description (text) : description de la catégorie

## Commande
- id (integer) PK : identifiant unique
- date_commande (datetime) : date de la commande
- statut (varchar) : statut de la commande
- montant_total (decimal) : montant total

### Client <-> Commande : Passe
**Un client peut passer plusieurs commandes**
Client : 1,1
Commande : 0,n

### Produit <-> Commande : Contient
**Une commande peut contenir plusieurs produits**
Produit : 1,1
Commande : 0,n

### Categorie <-> Produit : Appartient
**Une catégorie peut contenir plusieurs produits**
Categorie : 1,1
Produit : 0,n
```

## Validation

Le système valide automatiquement :

✅ **Cohérence des entités**
- Toutes les entités référencées dans les associations existent
- Chaque entité a au moins un attribut

✅ **Cohérence des associations**
- Les cardinalités sont valides
- Les descriptions sont présentes

✅ **Cohérence des attributs**
- Les types sont reconnus
- Les clés primaires sont détectées

## Gestion des erreurs

### Erreurs courantes

1. **Entité manquante**
   ```
   Erreur: Entité 'Client' référencée dans l'association 'Commande' n'existe pas
   ```

2. **Attribut manquant**
   ```
   Erreur: L'entité 'Produit' n'a aucun attribut
   ```

3. **Cardinalité invalide**
   ```
   Erreur: Cardinalité '2,3' non reconnue
   ```

### Solutions

- Vérifiez que toutes les entités sont définies avant les associations
- Assurez-vous que chaque entité a au moins un attribut
- Utilisez les cardinalités standard (1,1, 1,n, n,1, n,n, 0,1, 0,n)

## Astuces

### 💡 Bonnes pratiques

1. **Organisation du fichier**
   - Définissez d'abord toutes les entités
   - Puis définissez les associations
   - Utilisez des descriptions claires

2. **Nommage**
   - Utilisez des noms d'entités au singulier
   - Utilisez des noms d'associations descriptifs
   - Soyez cohérent dans la nomenclature

3. **Documentation**
   - Ajoutez des descriptions pour les associations
   - Commentez les attributs complexes
   - Utilisez des exemples dans les descriptions

### 🔧 Fonctionnalités avancées

- **Génération de template** : Utilisez le bouton "Générer Template" pour créer un fichier de base
- **Export JSON** : Exportez la structure parsée pour réutilisation
- **Validation en temps réel** : Les erreurs sont détectées instantanément

## Support technique

### Dépendances
- Python 3.7+
- PyQt5
- Regex (built-in)

### Fichiers concernés
- `views/markdown_mcd_parser.py` : Parseur principal
- `views/markdown_import_dialog.py` : Interface utilisateur
- `views/main_window.py` : Intégration dans l'application

### Tests
```bash
python test_markdown_parser.py
```

## Évolutions futures

- [ ] Support des associations ternaires
- [ ] Import depuis d'autres formats (CSV, Excel)
- [ ] Export vers d'autres formats (PlantUML, Mermaid)
- [ ] Validation plus poussée (normalisation)
- [ ] Suggestions automatiques d'amélioration 