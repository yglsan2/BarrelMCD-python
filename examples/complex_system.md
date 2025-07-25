# Système de Gestion d'Entreprise Complexe

## Utilisateur
- id (integer) : identifiant unique de l'utilisateur
- nom (varchar) : nom de l'utilisateur
- prenom (varchar) : prénom de l'utilisateur
- email (varchar) : adresse email
- telephone (varchar) : numéro de téléphone
- date_naissance (date) : date de naissance
- date_inscription (datetime) : date d'inscription
- statut (varchar) : statut du compte
- mot_de_passe_hash (varchar) : hash du mot de passe
- derniere_connexion (datetime) : dernière connexion

## Role
- id (integer) : identifiant unique du rôle
- nom (varchar) : nom du rôle
- description (text) : description du rôle
- permissions (json) : permissions associées
- niveau_acces (integer) : niveau d'accès
- date_creation (datetime) : date de création

## Departement
- id (integer) : identifiant unique du département
- nom (varchar) : nom du département
- description (text) : description du département
- responsable_id (integer) : responsable du département
- budget_annuel (decimal) : budget annuel
- date_creation (datetime) : date de création
- statut (varchar) : statut du département

## Projet
- id (integer) : identifiant unique du projet
- nom (varchar) : nom du projet
- description (text) : description du projet
- date_debut (date) : date de début
- date_fin_prevue (date) : date de fin prévue
- date_fin_reelle (date) : date de fin réelle
- budget_initial (decimal) : budget initial
- budget_consomme (decimal) : budget consommé
- statut (varchar) : statut du projet
- priorite (integer) : priorité du projet

## Tache
- id (integer) : identifiant unique de la tâche
- nom (varchar) : nom de la tâche
- description (text) : description de la tâche
- date_debut (date) : date de début
- date_fin_prevue (date) : date de fin prévue
- date_fin_reelle (date) : date de fin réelle
- priorite (integer) : priorité de la tâche
- statut (varchar) : statut de la tâche
- pourcentage_avancement (integer) : pourcentage d'avancement

## Client
- id (integer) : identifiant unique du client
- nom (varchar) : nom du client
- prenom (varchar) : prénom du client
- email (varchar) : adresse email
- telephone (varchar) : numéro de téléphone
- adresse (text) : adresse complète
- ville (varchar) : ville
- code_postal (varchar) : code postal
- pays (varchar) : pays
- date_creation (datetime) : date de création
- statut (varchar) : statut du client

## Fournisseur
- id (integer) : identifiant unique du fournisseur
- nom (varchar) : nom du fournisseur
- siret (varchar) : numéro SIRET
- email (varchar) : adresse email
- telephone (varchar) : numéro de téléphone
- adresse (text) : adresse complète
- ville (varchar) : ville
- code_postal (varchar) : code postal
- pays (varchar) : pays
- date_creation (datetime) : date de création
- statut (varchar) : statut du fournisseur

## Produit
- id (integer) : identifiant unique du produit
- nom (varchar) : nom du produit
- description (text) : description du produit
- reference (varchar) : référence du produit
- prix_achat (decimal) : prix d'achat
- prix_vente (decimal) : prix de vente
- stock_disponible (integer) : stock disponible
- stock_minimum (integer) : stock minimum
- categorie_id (integer) : catégorie du produit
- fournisseur_id (integer) : fournisseur du produit
- date_creation (datetime) : date de création
- statut (varchar) : statut du produit

## Categorie
- id (integer) : identifiant unique de la catégorie
- nom (varchar) : nom de la catégorie
- description (text) : description de la catégorie
- categorie_parent_id (integer) : catégorie parente
- niveau (integer) : niveau dans l'arborescence
- date_creation (datetime) : date de création

## Commande
- id (integer) : identifiant unique de la commande
- numero (varchar) : numéro de commande
- date_commande (datetime) : date de commande
- date_livraison_prevue (date) : date de livraison prévue
- date_livraison_reelle (date) : date de livraison réelle
- montant_total (decimal) : montant total
- montant_tva (decimal) : montant de la TVA
- montant_remise (decimal) : montant de la remise
- statut (varchar) : statut de la commande
- mode_paiement (varchar) : mode de paiement
- notes (text) : notes sur la commande

## LigneCommande
- id (integer) : identifiant unique de la ligne
- quantite (integer) : quantité commandée
- prix_unitaire (decimal) : prix unitaire
- remise_ligne (decimal) : remise sur la ligne
- total_ligne (decimal) : total de la ligne

## Facture
- id (integer) : identifiant unique de la facture
- numero (varchar) : numéro de facture
- date_facture (date) : date de facturation
- date_echeance (date) : date d'échéance
- montant_ht (decimal) : montant hors taxes
- montant_tva (decimal) : montant de la TVA
- montant_ttc (decimal) : montant TTC
- statut (varchar) : statut de la facture
- mode_paiement (varchar) : mode de paiement
- notes (text) : notes sur la facture

## Paiement
- id (integer) : identifiant unique du paiement
- montant (decimal) : montant du paiement
- date_paiement (datetime) : date du paiement
- mode_paiement (varchar) : mode de paiement
- reference_paiement (varchar) : référence du paiement
- statut (varchar) : statut du paiement
- notes (text) : notes sur le paiement

## Livraison
- id (integer) : identifiant unique de la livraison
- numero_suivi (varchar) : numéro de suivi
- date_expedition (datetime) : date d'expédition
- date_livraison (datetime) : date de livraison
- transporteur (varchar) : transporteur
- cout_transport (decimal) : coût du transport
- statut (varchar) : statut de la livraison
- adresse_livraison (text) : adresse de livraison

## Document
- id (integer) : identifiant unique du document
- nom (varchar) : nom du document
- type (varchar) : type de document
- chemin_fichier (varchar) : chemin du fichier
- taille_fichier (integer) : taille du fichier
- format_fichier (varchar) : format du fichier
- date_upload (datetime) : date d'upload
- description (text) : description du document

## Notification
- id (integer) : identifiant unique de la notification
- titre (varchar) : titre de la notification
- message (text) : message de la notification
- type (varchar) : type de notification
- date_creation (datetime) : date de création
- date_lecture (datetime) : date de lecture
- statut (varchar) : statut de la notification

## Utilisateur <-> Role : Possede
**Un utilisateur peut avoir plusieurs rôles et un rôle peut être attribué à plusieurs utilisateurs**
Utilisateur : 0,n
Role : 0,n

## Utilisateur <-> Departement : Appartient
**Un utilisateur appartient à un département et un département peut avoir plusieurs utilisateurs**
Utilisateur : 0,n
Departement : 1,1

## Departement <-> Projet : Gere
**Un département peut gérer plusieurs projets et un projet est géré par un département**
Departement : 1,1
Projet : 0,n

## Projet <-> Tache : Contient
**Un projet contient plusieurs tâches et une tâche appartient à un projet**
Projet : 1,1
Tache : 0,n

## Utilisateur <-> Tache : Assigne
**Un utilisateur peut être assigné à plusieurs tâches et une tâche peut être assignée à plusieurs utilisateurs**
Utilisateur : 0,n
Tache : 0,n

## Client <-> Commande : Passe
**Un client peut passer plusieurs commandes et une commande appartient à un client**
Client : 1,1
Commande : 0,n

## Commande <-> LigneCommande : Contient
**Une commande contient plusieurs lignes et une ligne appartient à une commande**
Commande : 1,1
LigneCommande : 0,n

## Produit <-> LigneCommande : Reference
**Un produit peut être référencé dans plusieurs lignes et une ligne référence un produit**
Produit : 1,1
LigneCommande : 0,n

## Commande <-> Facture : Genere
**Une commande peut générer plusieurs factures et une facture est générée par une commande**
Commande : 1,1
Facture : 0,n

## Facture <-> Paiement : Recouvre
**Une facture peut être recouvrée par plusieurs paiements et un paiement recouvre une facture**
Facture : 1,1
Paiement : 0,n

## Commande <-> Livraison : Expedie
**Une commande peut être expédiée en plusieurs livraisons et une livraison expédie une commande**
Commande : 1,1
Livraison : 0,n

## Fournisseur <-> Produit : Fournit
**Un fournisseur peut fournir plusieurs produits et un produit est fourni par un fournisseur**
Fournisseur : 1,1
Produit : 0,n

## Categorie <-> Produit : Classe
**Une catégorie peut classer plusieurs produits et un produit appartient à une catégorie**
Categorie : 1,1
Produit : 0,n

## Categorie <-> Categorie : SousCategorie
**Une catégorie peut avoir plusieurs sous-catégories et une sous-catégorie appartient à une catégorie parente**
Categorie : 1,1
Categorie : 0,n

## Utilisateur <-> Document : Possede
**Un utilisateur peut posséder plusieurs documents et un document appartient à un utilisateur**
Utilisateur : 1,1
Document : 0,n

## Projet <-> Document : Reference
**Un projet peut référencer plusieurs documents et un document peut référencer plusieurs projets**
Projet : 0,n
Document : 0,n

## Utilisateur <-> Notification : Recoit
**Un utilisateur peut recevoir plusieurs notifications et une notification est reçue par un utilisateur**
Utilisateur : 1,1
Notification : 0,n

## Projet <-> Notification : Declenche
**Un projet peut déclencher plusieurs notifications et une notification peut être déclenchée par un projet**
Projet : 1,1
Notification : 0,n 