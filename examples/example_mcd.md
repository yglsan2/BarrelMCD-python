# Modèle Conceptuel de Données - Système de Gestion de Bibliothèque

## Livre
- id (integer) PK : identifiant unique du livre
- titre (varchar) : titre du livre
- auteur (varchar) : nom de l'auteur
- isbn (varchar) : numéro ISBN
- annee_publication (integer) : année de publication
- nombre_pages (integer) : nombre de pages
- prix (decimal) : prix du livre
- disponible (boolean) : si le livre est disponible

## Lecteur
- id (integer) PK : identifiant unique du lecteur
- nom (varchar) : nom du lecteur
- prenom (varchar) : prénom du lecteur
- email (varchar) : adresse email
- telephone (varchar) : numéro de téléphone
- date_inscription (date) : date d'inscription
- adresse (varchar) : adresse postale

## Categorie
- id (integer) PK : identifiant unique de la catégorie
- nom (varchar) : nom de la catégorie
- description (text) : description de la catégorie

## Emprunt
- id (integer) PK : identifiant unique de l'emprunt
- date_emprunt (date) : date d'emprunt
- date_retour_prevue (date) : date de retour prévue
- date_retour_effective (date) : date de retour effective
- statut (varchar) : statut de l'emprunt

### Livre <-> Categorie : Appartient
**Un livre appartient à une catégorie**
Livre : 1,1
Categorie : 0,n

### Lecteur <-> Emprunt : Effectue
**Un lecteur peut effectuer plusieurs emprunts**
Lecteur : 1,1
Emprunt : 0,n

### Livre <-> Emprunt : Est_emprunte
**Un livre peut être emprunté plusieurs fois**
Livre : 1,1
Emprunt : 0,n

## Auteur
- id (integer) PK : identifiant unique de l'auteur
- nom (varchar) : nom de l'auteur
- prenom (varchar) : prénom de l'auteur
- biographie (text) : biographie de l'auteur
- nationalite (varchar) : nationalité de l'auteur

### Auteur <-> Livre : Ecrit
**Un auteur peut écrire plusieurs livres**
Auteur : 1,1
Livre : 0,n

## Editeur
- id (integer) PK : identifiant unique de l'éditeur
- nom (varchar) : nom de l'éditeur
- adresse (varchar) : adresse de l'éditeur
- telephone (varchar) : numéro de téléphone
- email (varchar) : adresse email

### Editeur <-> Livre : Publie
**Un éditeur peut publier plusieurs livres**
Editeur : 1,1
Livre : 0,n 