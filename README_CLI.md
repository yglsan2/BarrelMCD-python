# BarrelMCD - Interface en Ligne de Commande

## 🚀 Vue d'ensemble

BarrelMCD CLI est une interface en ligne de commande puissante pour convertir des fichiers markdown en modèles de données complets (MCD, MLD, MPD, SQL). Elle supporte les fichiers de grande taille et génère des modèles de qualité professionnelle.

## 📋 Fonctionnalités

### ✅ **Fonctionnalités principales**
- **Import de fichiers markdown** de toute taille
- **Génération automatique** de MCD, MLD, MPD et SQL
- **Support des gros fichiers** avec optimisation des performances
- **Validation complète** avec score de précision
- **Rapports détaillés** de conversion
- **Gestion d'erreurs** robuste

### ✅ **Formats de sortie supportés**
- **MCD** (Modèle Conceptuel de Données) - JSON
- **MLD** (Modèle Logique de Données) - JSON  
- **MPD** (Modèle Physique de Données) - JSON
- **SQL** (Scripts de création de base de données)
- **Rapports** (Statistiques et validation)

## 🛠️ Installation

```bash
# Cloner le projet
git clone <repository>
cd barrelMCD-python

# Installer les dépendances
pip install -r requirements.txt
```

## 📖 Utilisation

### 🎯 **Utilisation basique**

```bash
# Convertir un fichier markdown en tous les formats
python cli_markdown_import.py fichier.md
```

### 🎯 **Avec répertoire de sortie personnalisé**

```bash
# Spécifier un répertoire de sortie
python cli_markdown_import.py fichier.md -o ./ma_sortie
```

### 🎯 **Formats de sortie spécifiques**

```bash
# Générer seulement le MCD
python cli_markdown_import.py fichier.md --format mcd-only

# Générer seulement le MLD
python cli_markdown_import.py fichier.md --format mld-only

# Générer seulement le MPD
python cli_markdown_import.py fichier.md --format mpd-only

# Générer seulement le SQL
python cli_markdown_import.py fichier.md --format sql-only

# Générer tous les formats (défaut)
python cli_markdown_import.py fichier.md --format all
```

### 🎯 **Mode verbeux**

```bash
# Afficher plus d'informations
python cli_markdown_import.py fichier.md --verbose
```

### 🎯 **Aide**

```bash
# Afficher l'aide
python cli_markdown_import.py --help
```

## 📝 Syntaxe Markdown Supportée

### 🏗️ **Entités**

```markdown
## NomEntite
- attribut1 (type) : description
- attribut2 (type) : description
- attribut3 (type) : description
```

### 🔗 **Associations**

```markdown
## Entite1 <-> Entite2 : NomAssociation
**Description de l'association**
Entite1 : cardinalite1
Entite2 : cardinalite2
```

### 📊 **Cardinalités supportées**

- `1,1` : Un à un
- `1,n` : Un à plusieurs
- `n,1` : Plusieurs à un
- `n,n` : Plusieurs à plusieurs
- `0,1` : Zéro ou un
- `0,n` : Zéro ou plusieurs

## 📊 Exemple d'utilisation

### 🎯 **Fichier d'entrée** (`exemple.md`)

```markdown
# Système de Gestion

## Utilisateur
- id (integer) : identifiant unique
- nom (varchar) : nom de l'utilisateur
- email (varchar) : adresse email

## Projet
- id (integer) : identifiant unique
- nom (varchar) : nom du projet
- description (text) : description

## Utilisateur <-> Projet : Gere
**Un utilisateur peut gérer plusieurs projets**
Utilisateur : 1,1
Projet : 0,n
```

### 🎯 **Commande**

```bash
python cli_markdown_import.py exemple.md -o ./sortie
```

### 🎯 **Fichiers générés**

```
sortie/
├── exemple_mcd.json      # Modèle conceptuel
├── exemple_mld.json      # Modèle logique
├── exemple_mpd.json      # Modèle physique
├── exemple.sql           # Script SQL
└── exemple_report.txt    # Rapport de conversion
```

## 📈 Statistiques de performance

### 🚀 **Capacités de traitement**

- **Fichiers jusqu'à 10MB+** : Traitement optimisé
- **16+ entités** : Support complet
- **18+ associations** : Gestion avancée
- **Score de précision** : 98.6% sur les exemples

### ⚡ **Performance**

- **Parsing** : < 0.01s pour 9KB
- **Génération** : < 0.01s pour 16 entités
- **Mémoire** : Optimisée pour gros fichiers

## 🔧 Options avancées

### 📁 **Répertoire de sortie**

```bash
-o, --output DIR     # Répertoire de sortie (défaut: output)
```

### 📄 **Format de sortie**

```bash
--format FORMAT       # Format: mcd-only, mld-only, mpd-only, sql-only, all
```

### 🔍 **Mode verbeux**

```bash
-v, --verbose        # Afficher plus d'informations
```

## 📊 Exemple de sortie

### 🎯 **Exécution**

```bash
$ python cli_markdown_import.py complex_system.md

🚀 BARRELMCD - IMPORT MARKDOWN CLI
==================================================
📁 Chargement du fichier: complex_system.md
📊 Taille du fichier: 9,357 octets (9.1 KB)
✅ Fichier chargé: 9228 caractères
🔄 Parsing du markdown vers MCD...
✅ Parsing terminé en 0.01s
📊 Statistiques MCD:
   • Entités: 16
   • Associations: 18
   • Score de précision: 98.6%
📋 Entités détectées:
   • Utilisateur: 10 attributs
   • Role: 6 attributs
   • Departement: 7 attributs
   • Projet: 10 attributs
   • Tache: 9 attributs
   • Client: 11 attributs
   • Fournisseur: 11 attributs
   • Produit: 12 attributs
   • Categorie: 6 attributs
   • Commande: 11 attributs
   • Lignecommande: 5 attributs
   • Facture: 10 attributs
   • Paiement: 7 attributs
   • Livraison: 8 attributs
   • Document: 8 attributs
   • Notification: 7 attributs
🔗 Associations détectées:
   • Utilisateur <-> Role: Possede
     Cardinalités: 0,n / 0,n
   • Utilisateur <-> Departement: Appartient
     Cardinalités: 0,n / 1,1
   • Departement <-> Projet: Gere
     Cardinalités: 1,1 / 0,n
   • Projet <-> Tache: Contient
     Cardinalités: 1,1 / 0,n
   • Utilisateur <-> Tache: Assigne
     Cardinalités: 0,n / 0,n
   • Client <-> Commande: Passe
     Cardinalités: 1,1 / 0,n
   • Commande <-> Lignecommande: Contient
     Cardinalités: 1,1 / 1,1
   • Produit <-> Lignecommande: Reference
     Cardinalités: 1,1 / 1,1
   • Commande <-> Facture: Genere
     Cardinalités: 1,1 / 0,n
   • Facture <-> Paiement: Recouvre
     Cardinalités: 1,1 / 0,n
   • Commande <-> Livraison: Expedie
     Cardinalités: 1,1 / 0,n
   • Fournisseur <-> Produit: Fournit
     Cardinalités: 1,1 / 0,n
   • Categorie <-> Produit: Classe
     Cardinalités: 1,1 / 0,n
   • Categorie <-> Categorie: SousCategorie
     Cardinalités: 0,n / 1,1
   • Utilisateur <-> Document: Possede
     Cardinalités: 1,1 / 0,n
   • Projet <-> Document: Reference
     Cardinalités: 0,n / 0,n
   • Utilisateur <-> Notification: Recoit
     Cardinalités: 1,1 / 0,n
   • Projet <-> Notification: Declenche
     Cardinalités: 1,1 / 0,n
🔄 Génération des modèles...
  📊 Génération MLD...
  📊 Génération MPD...
  📊 Génération SQL...
✅ Génération terminée en 0.00s
📊 Statistiques des modèles:
   • Tables MLD: 19
   • Clés étrangères MLD: 21
   • Tables MPD: 19
   • Longueur SQL: 12135 caractères
💾 Sauvegarde des modèles dans: output
✅ MCD sauvegardé: output/complex_system_mcd.json
✅ MLD sauvegardé: output/complex_system_mld.json
✅ MPD sauvegardé: output/complex_system_mpd.json
✅ SQL sauvegardé: output/complex_system.sql
✅ Rapport généré: output/complex_system_report.txt

🎉 CONVERSION TERMINÉE AVEC SUCCÈS!
📁 Résultats sauvegardés dans: output
📄 Fichiers générés:
   • complex_system_mcd.json
   • complex_system_mld.json
   • complex_system_mpd.json
   • complex_system.sql
   • complex_system_report.txt
```

## 🧪 Tests

### 🎯 **Lancer tous les tests**

```bash
python test_cli.py
```

### 🎯 **Résultats attendus**

```
🚀 TESTS CLI BARRELMCD
==================================================
🧪 TEST CLI BASIQUE
✅ Test basique: RÉUSSI

🧪 TEST CLI AVEC RÉPERTOIRE DE SORTIE
✅ complex_system_mcd.json: 50,204 octets
✅ complex_system_mld.json: 38,843 octets
✅ complex_system_mpd.json: 48,649 octets
✅ complex_system.sql: 12,135 octets
✅ complex_system_report.txt: 5,577 octets
✅ Test répertoire de sortie: RÉUSSI

🧪 TEST DES DIFFÉRENTS FORMATS
✅ Test formats: RÉUSSI

🧪 TEST AIDE CLI
✅ Test aide: RÉUSSI

🧪 TEST GESTION D'ERREURS
✅ Test gestion d'erreurs: RÉUSSI

🧪 VALIDATION DES FICHIERS GÉNÉRÉS
✅ Validation MCD réussie
✅ Validation SQL réussie
✅ Validation fichiers: RÉUSSI

==================================================
📊 RÉSULTATS DES TESTS
✅ Tests réussis: 6/6
📈 Taux de réussite: 100.0%

🎉 TOUS LES TESTS CLI SONT RÉUSSIS!
🚀 Le CLI BarrelMCD est prêt à être utilisé!
```

## 🐛 Dépannage

### ❌ **Erreurs courantes**

1. **Fichier non trouvé**
   ```
   ❌ Erreur: Fichier 'fichier.md' non trouvé
   ```
   **Solution** : Vérifier le chemin du fichier

2. **Problème d'encodage**
   ```
   ❌ Erreur: Problème d'encodage dans 'fichier.md'
   ```
   **Solution** : Utiliser l'encodage UTF-8

3. **Répertoire de sortie inaccessible**
   ```
   ❌ Erreur lors de la sauvegarde
   ```
   **Solution** : Vérifier les permissions du répertoire

### ✅ **Vérifications**

- **Fichier markdown valide** : Syntaxe correcte
- **Permissions** : Lecture du fichier d'entrée, écriture du répertoire de sortie
- **Espace disque** : Suffisant pour les fichiers générés

## 📚 Références

### 🔗 **Liens utiles**

- [Documentation BarrelMCD](../README.md)
- [Guide de syntaxe markdown](syntax_guide.md)
- [Exemples de fichiers](../examples/)

### 📞 **Support**

- **Issues** : [GitHub Issues](https://github.com/...)
- **Documentation** : [Wiki](https://github.com/.../wiki)
- **Tests** : `python test_cli.py`

---

**BarrelMCD CLI** - Transformez vos fichiers markdown en modèles de données professionnels ! 🚀 