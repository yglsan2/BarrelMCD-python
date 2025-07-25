CREATE TABLE utilisateur (
    id INTEGER NOT NULL,
    nom VARCHAR(255),
    prenom VARCHAR(255),
    email VARCHAR(255),
    telephone VARCHAR(255),
    date_naissance DATE,
    date_inscription DATE,
    statut VARCHAR(255),
    mot_de_passe_hash VARCHAR(255),
    derniere_connexion DATE,
    departement_id INTEGER NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE role (
    id INTEGER NOT NULL,
    nom VARCHAR(255),
    description VARCHAR(255),
    permissions VARCHAR(255),
    niveau_acces INTEGER,
    date_creation DATE,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE departement (
    id INTEGER NOT NULL,
    nom VARCHAR(255),
    description VARCHAR(255),
    responsable_id INTEGER,
    budget_annuel DECIMAL(10,2),
    date_creation DATE,
    statut VARCHAR(255),
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE projet (
    id INTEGER NOT NULL,
    nom VARCHAR(255),
    description VARCHAR(255),
    date_debut DATE,
    date_fin_prevue DATE,
    date_fin_reelle DATE,
    budget_initial DECIMAL(10,2),
    budget_consomme DECIMAL(10,2),
    statut VARCHAR(255),
    priorite INTEGER,
    departement_id INTEGER NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE tache (
    id INTEGER NOT NULL,
    nom VARCHAR(255),
    description VARCHAR(255),
    date_debut DATE,
    date_fin_prevue DATE,
    date_fin_reelle DATE,
    priorite INTEGER,
    statut VARCHAR(255),
    pourcentage_avancement INTEGER,
    projet_id INTEGER NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE client (
    id INTEGER NOT NULL,
    nom VARCHAR(255),
    prenom VARCHAR(255),
    email VARCHAR(255),
    telephone VARCHAR(255),
    adresse VARCHAR(255),
    ville VARCHAR(255),
    code_postal VARCHAR(255),
    pays VARCHAR(255),
    date_creation DATE,
    statut VARCHAR(255),
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE fournisseur (
    id INTEGER NOT NULL,
    nom VARCHAR(255),
    siret VARCHAR(255),
    email VARCHAR(255),
    telephone VARCHAR(255),
    adresse VARCHAR(255),
    ville VARCHAR(255),
    code_postal VARCHAR(255),
    pays VARCHAR(255),
    date_creation DATE,
    statut VARCHAR(255),
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE produit (
    id INTEGER NOT NULL,
    nom VARCHAR(255),
    description VARCHAR(255),
    reference VARCHAR(255),
    prix_achat DECIMAL(10,2),
    prix_vente DECIMAL(10,2),
    stock_disponible INTEGER,
    stock_minimum INTEGER,
    categorie_id INTEGER,
    fournisseur_id INTEGER,
    date_creation DATE,
    statut VARCHAR(255),
    lignecommande_id INTEGER NOT NULL,
    fournisseur_id INTEGER NOT NULL,
    categorie_id INTEGER NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE categorie (
    id INTEGER NOT NULL,
    nom VARCHAR(255),
    description VARCHAR(255),
    categorie_parent_id INTEGER,
    niveau INTEGER,
    date_creation DATE,
    categorie_id INTEGER NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE commande (
    id INTEGER NOT NULL,
    numero VARCHAR(255) NOT NULL,
    date_commande DATE,
    date_livraison_prevue DATE,
    date_livraison_reelle DATE,
    montant_total DECIMAL(10,2),
    montant_tva DECIMAL(10,2),
    montant_remise DECIMAL(10,2),
    statut VARCHAR(255),
    mode_paiement VARCHAR(255),
    notes VARCHAR(255),
    client_id INTEGER NOT NULL,
    lignecommande_id INTEGER NOT NULL,
    PRIMARY KEY (id, numero)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE lignecommande (
    id INTEGER NOT NULL,
    quantite INTEGER,
    prix_unitaire DECIMAL(10,2),
    remise_ligne DECIMAL(10,2),
    total_ligne DECIMAL(10,2),
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE facture (
    id INTEGER NOT NULL,
    numero VARCHAR(255) NOT NULL,
    date_facture DATE,
    date_echeance DATE,
    montant_ht DECIMAL(10,2),
    montant_tva DECIMAL(10,2),
    montant_ttc DECIMAL(10,2),
    statut VARCHAR(255),
    mode_paiement VARCHAR(255),
    notes VARCHAR(255),
    commande_id INTEGER NOT NULL,
    PRIMARY KEY (id, numero)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE paiement (
    id INTEGER NOT NULL,
    montant DECIMAL(10,2),
    date_paiement DATE,
    mode_paiement VARCHAR(255),
    reference_paiement VARCHAR(255),
    statut VARCHAR(255),
    notes VARCHAR(255),
    facture_id INTEGER NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE livraison (
    id INTEGER NOT NULL,
    numero_suivi VARCHAR(255),
    date_expedition DATE,
    date_livraison DATE,
    transporteur VARCHAR(255),
    cout_transport DECIMAL(10,2),
    statut VARCHAR(255),
    adresse_livraison VARCHAR(255),
    commande_id INTEGER NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE document (
    id INTEGER NOT NULL,
    nom VARCHAR(255),
    type VARCHAR(255),
    chemin_fichier VARCHAR(255),
    taille_fichier INTEGER,
    format_fichier VARCHAR(255),
    date_upload DATE,
    description VARCHAR(255),
    utilisateur_id INTEGER NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE notification (
    id INTEGER NOT NULL,
    titre VARCHAR(255),
    message VARCHAR(255),
    type VARCHAR(255),
    date_creation DATE,
    date_lecture DATE,
    statut VARCHAR(255),
    utilisateur_id INTEGER NOT NULL,
    projet_id INTEGER NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE utilisateur_role (
    utilisateur_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    PRIMARY KEY (utilisateur_id, role_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE utilisateur_tache (
    utilisateur_id INTEGER NOT NULL,
    tache_id INTEGER NOT NULL,
    PRIMARY KEY (utilisateur_id, tache_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE projet_document (
    projet_id INTEGER NOT NULL,
    document_id INTEGER NOT NULL,
    PRIMARY KEY (projet_id, document_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER TABLE utilisateur_role ADD CONSTRAINT fk_utilisateur_role_utilisateur FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id);

ALTER TABLE utilisateur_role ADD CONSTRAINT fk_utilisateur_role_role FOREIGN KEY (role_id) REFERENCES role(id);

ALTER TABLE utilisateur ADD CONSTRAINT fk_utilisateur_departement FOREIGN KEY (departement_id) REFERENCES departement(id);

ALTER TABLE projet ADD CONSTRAINT fk_projet_departement FOREIGN KEY (departement_id) REFERENCES departement(id);

ALTER TABLE tache ADD CONSTRAINT fk_tache_projet FOREIGN KEY (projet_id) REFERENCES projet(id);

ALTER TABLE utilisateur_tache ADD CONSTRAINT fk_utilisateur_tache_utilisateur FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id);

ALTER TABLE utilisateur_tache ADD CONSTRAINT fk_utilisateur_tache_tache FOREIGN KEY (tache_id) REFERENCES tache(id);

ALTER TABLE commande ADD CONSTRAINT fk_commande_client FOREIGN KEY (client_id) REFERENCES client(id);

ALTER TABLE commande ADD CONSTRAINT fk_commande_lignecommande FOREIGN KEY (lignecommande_id) REFERENCES lignecommande(id);

ALTER TABLE produit ADD CONSTRAINT fk_produit_lignecommande FOREIGN KEY (lignecommande_id) REFERENCES lignecommande(id);

ALTER TABLE facture ADD CONSTRAINT fk_facture_commande FOREIGN KEY (commande_id) REFERENCES commande(id);

ALTER TABLE paiement ADD CONSTRAINT fk_paiement_facture FOREIGN KEY (facture_id) REFERENCES facture(id);

ALTER TABLE livraison ADD CONSTRAINT fk_livraison_commande FOREIGN KEY (commande_id) REFERENCES commande(id);

ALTER TABLE produit ADD CONSTRAINT fk_produit_fournisseur FOREIGN KEY (fournisseur_id) REFERENCES fournisseur(id);

ALTER TABLE produit ADD CONSTRAINT fk_produit_categorie FOREIGN KEY (categorie_id) REFERENCES categorie(id);

ALTER TABLE categorie ADD CONSTRAINT fk_categorie_categorie FOREIGN KEY (categorie_id) REFERENCES categorie(id);

ALTER TABLE document ADD CONSTRAINT fk_document_utilisateur FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id);

ALTER TABLE projet_document ADD CONSTRAINT fk_projet_document_projet FOREIGN KEY (projet_id) REFERENCES projet(id);

ALTER TABLE projet_document ADD CONSTRAINT fk_projet_document_document FOREIGN KEY (document_id) REFERENCES document(id);

ALTER TABLE notification ADD CONSTRAINT fk_notification_utilisateur FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id);

ALTER TABLE notification ADD CONSTRAINT fk_notification_projet FOREIGN KEY (projet_id) REFERENCES projet(id);

CREATE INDEX idx_utilisateur_departement_id ON utilisateur (departement_id);

CREATE INDEX idx_utilisateur_nom ON utilisateur (nom);

CREATE INDEX idx_utilisateur_email ON utilisateur (email);

CREATE INDEX idx_role_nom ON role (nom);

CREATE INDEX idx_role_date_creation ON role (date_creation);

CREATE INDEX idx_departement_responsable_id ON departement (responsable_id);

CREATE INDEX idx_departement_nom ON departement (nom);

CREATE INDEX idx_departement_date_creation ON departement (date_creation);

CREATE INDEX idx_projet_departement_id ON projet (departement_id);

CREATE INDEX idx_projet_nom ON projet (nom);

CREATE INDEX idx_tache_projet_id ON tache (projet_id);

CREATE INDEX idx_tache_nom ON tache (nom);

CREATE INDEX idx_client_nom ON client (nom);

CREATE INDEX idx_client_email ON client (email);

CREATE INDEX idx_client_date_creation ON client (date_creation);

CREATE INDEX idx_fournisseur_nom ON fournisseur (nom);

CREATE INDEX idx_fournisseur_email ON fournisseur (email);

CREATE INDEX idx_fournisseur_date_creation ON fournisseur (date_creation);

CREATE INDEX idx_produit_categorie_id ON produit (categorie_id);

CREATE INDEX idx_produit_fournisseur_id ON produit (fournisseur_id);

CREATE INDEX idx_produit_lignecommande_id ON produit (lignecommande_id);

CREATE INDEX idx_produit_fournisseur_id ON produit (fournisseur_id);

CREATE INDEX idx_produit_categorie_id ON produit (categorie_id);

CREATE INDEX idx_produit_nom ON produit (nom);

CREATE INDEX idx_produit_date_creation ON produit (date_creation);

CREATE INDEX idx_categorie_categorie_parent_id ON categorie (categorie_parent_id);

CREATE INDEX idx_categorie_categorie_id ON categorie (categorie_id);

CREATE INDEX idx_categorie_nom ON categorie (nom);

CREATE INDEX idx_categorie_date_creation ON categorie (date_creation);

CREATE INDEX idx_commande_client_id ON commande (client_id);

CREATE INDEX idx_commande_lignecommande_id ON commande (lignecommande_id);

CREATE INDEX idx_facture_commande_id ON facture (commande_id);

CREATE INDEX idx_paiement_facture_id ON paiement (facture_id);

CREATE INDEX idx_livraison_commande_id ON livraison (commande_id);

CREATE INDEX idx_document_utilisateur_id ON document (utilisateur_id);

CREATE INDEX idx_document_nom ON document (nom);

CREATE INDEX idx_notification_utilisateur_id ON notification (utilisateur_id);

CREATE INDEX idx_notification_projet_id ON notification (projet_id);

CREATE INDEX idx_notification_date_creation ON notification (date_creation);

CREATE INDEX idx_utilisateur_role_utilisateur_id ON utilisateur_role (utilisateur_id);

CREATE INDEX idx_utilisateur_role_role_id ON utilisateur_role (role_id);

CREATE INDEX idx_utilisateur_tache_utilisateur_id ON utilisateur_tache (utilisateur_id);

CREATE INDEX idx_utilisateur_tache_tache_id ON utilisateur_tache (tache_id);

CREATE INDEX idx_projet_document_projet_id ON projet_document (projet_id);

CREATE INDEX idx_projet_document_document_id ON projet_document (document_id);