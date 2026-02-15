# Publication de BarrelMCD Flutter

Guide pour publier l’application sur **Arch Linux (AUR)**, **Debian/Ubuntu** et **Snap Store** (Snapcraft).

**Ordre recommandé :** 1. AUR → 2. Debian → 3. Snap.

---

## 1. Arch Linux (AUR)

L’AUR permet aux utilisateurs d’installer avec `yay -S barrelmcd-flutter` (ou `paru`, etc.).

### Prérequis

- Compte sur [AUR](https://aur.archlinux.org/register).
- Clé SSH associée à ce compte (pour pousser le paquet).
- Paquet soumis via **Git** : dépôt `ssh://aur@aur.archlinux.org/barrelmcd-flutter.git`.

### Étapes

1. **Réserver le nom (si le paquet n’existe pas)**  
   Sur [AUR](https://aur.archlinux.org/), connecté, créer un paquet nommé `barrelmcd-flutter`. Vous obtiendrez l’URL du dépôt Git.

2. **Cloner le dépôt AUR** (le paquet n’existe pas encore : un « empty repository » est normal)
   ```bash
   git -c init.defaultBranch=master clone ssh://aur@aur.archlinux.org/barrelmcd-flutter.git aur-barrelmcd
   cd aur-barrelmcd
   ```

3. **Copier les fichiers du paquet**
   - Copier `barrelmcd_flutter/packaging/PKGBUILD.aur` → `PKGBUILD` (éditer la ligne `# Maintainer:` avec ton nom et email).
   - Copier `barrelmcd_flutter/packaging/LICENSE.aur` → `LICENSE` (licence du dépôt AUR, 0BSD).
   - Dans le clone AUR : exécuter `updpkgsums` pour remplir `sha256sums`.

4. **Générer .SRCINFO**
   ```bash
   makepkg --printsrcinfo > .SRCINFO
   ```

5. **Commit et push** (l’AUR n’accepte que la branche **master**)
   ```bash
   git add PKGBUILD .SRCINFO LICENSE
   git commit -m "Initial commit: barrelmcd-flutter 1.0.0"
   git push origin master
   ```

### Mise à jour ultérieure

- Modifier `pkgver` / `pkgrel` dans le PKGBUILD pour une nouvelle release.
- Relancer `updpkgsums`, puis `makepkg --printsrcinfo > .SRCINFO`, commit + push.

Fichiers : `packaging/PKGBUILD.aur` (tag GitHub, reproductible) ou `packaging/PKGBUILD` (branche main).

---

## 2. Debian / Ubuntu

### Option A : Téléchargement direct (déjà en place)

Le fichier `.deb` est fourni sur les [Releases GitHub](https://github.com/yglsan2/BarrelMCD-python/releases). Les utilisateurs Ubuntu/Debian peuvent :

```bash
# Télécharger le .deb depuis la release, puis :
sudo dpkg -i barrelmcd-flutter_1.0.0_amd64.deb
sudo apt-get install -f   # corriger les dépendances si besoin
```

### Option B : PPA sur Launchpad

Pour proposer un PPA (installation via `apt` et mises à jour automatiques) :

1. **Prérequis**
   - Compte sur [Launchpad](https://launchpad.net/).
   - Clé GPG : `gpg --full-generate-key` si besoin, puis l’importer sur [Clés OpenPGP Launchpad](https://launchpad.net/~/+editpgpkeys).
   - Sur la machine de build (Debian/Ubuntu) : `sudo apt install devscripts build-essential debhelper`.

2. **Créer le PPA**
   - Sur Launchpad : [Créer un PPA](https://launchpad.net/ppas) (ex. nom « ppa »).

3. **Construire et envoyer le paquet source**
   - **Avec Docker (recommandé, depuis n’importe quelle distro)** :
     ```bash
     cd BarrelMCD-python
     ./barrelmcd_flutter/packaging/docker-build-deb.sh
     ```
     La première fois, l’image `barrelmcd-deb` est construite (Ubuntu 22.04 + Flutter + outils Debian). Le paquet source est généré dans `BarrelMCD-python/`.
   - **Sans Docker** (machine Debian/Ubuntu avec Flutter installé) :
     ```bash
     cd BarrelMCD-python/barrelmcd_flutter
     ./packaging/build_source_package.sh
     ```
   - Signer (si demandé) : `debsign -k VOTRE_CLE barrelmcd-flutter_1.0.0-1_source.changes`
   - Envoyer : `cd BarrelMCD-python && dput ppa:VOTRE_ID_LAUNCHPAD/ppa barrelmcd-flutter_1.0.0-1_source.changes`

4. **Côté utilisateur**
   ```bash
   sudo add-apt-repository ppa:VOTRE_ID/ppa
   sudo apt update
   sudo apt install barrelmcd-flutter
   ```

Le dossier `debian/` (control, changelog, rules, compat, desktop) est dans `barrelmcd_flutter/debian/`. L’archive « orig » contient le bundle Linux déjà compilé pour que Launchpad n’ait pas besoin de Flutter.

---

## 3. Snap Store (Snapcraft)

Publication sur le [Snap Store](https://snapcraft.io/store) pour une installation type `snap install barrelmcd-flutter` sur Ubuntu et autres distributions compatibles Snap.

### Prérequis

- Ubuntu 18.04 LTS ou plus (ou environnement équivalent pour construire).
- Snapcraft : `sudo snap install snapcraft --classic`
- LXD (pour la construction en conteneur) : `sudo snap install lxd` puis `sudo lxd init`, et ajouter votre utilisateur au groupe `lxd` : `sudo usermod -a -G lxd $USER` (puis se déconnecter/reconnecter si besoin).

### Fichiers dans le dépôt

- `snap/snapcraft.yaml` : définition du snap (nom, version, partie Flutter, app, etc.).
- `snap/gui/barrelmcd-flutter.desktop` : entrée menu.
- `snap/gui/barrelmcd-flutter.png` : icône (copier `assets/images/logo.png` vers ce fichier avant de construire).

### Construction

```bash
cd barrelmcd_flutter
# Copier l’icône si pas déjà fait
cp assets/images/logo.png snap/gui/barrelmcd-flutter.png
snapcraft --use-lxd
```

Vous obtiendrez un fichier `barrelmcd-flutter_1.0.0_amd64.snap`.

### Test local

```bash
sudo snap install ./barrelmcd-flutter_1.0.0_amd64.snap --dangerous
barrelmcd-flutter
```

### Publication sur le Snap Store

1. Compte : [snapcraft.io](https://snapcraft.io/) → créer un compte développeur.
2. Connexion : `snapcraft login`
3. Réserver le nom : `snapcraft register barrelmcd-flutter` (si le nom est libre).
4. Upload et publication :
   ```bash
   snapcraft upload --release=stable barrelmcd-flutter_1.0.0_amd64.snap
   ```

Ensuite, les utilisateurs pourront installer avec :

```bash
sudo snap install barrelmcd-flutter
```

---

## Récapitulatif

| Ordre | Plateforme   | Fichiers / actions principales                          | Commande utilisateur typique        |
|-------|-------------|----------------------------------------------------------|-------------------------------------|
| 1     | Arch (AUR)  | PKGBUILD.aur + .SRCINFO dans le dépôt AUR                | `yay -S barrelmcd-flutter`          |
| 2     | Debian      | Release GitHub (.deb) ou PPA (paquet source + Launchpad) | `dpkg -i …` ou `apt install …`      |
| 3     | Snap Store  | `snap/snapcraft.yaml` + `snap/gui/*`                     | `snap install barrelmcd-flutter`    |

**Note :** Si vous pensiez à une autre plateforme que Snapcraft (par exemple **Flathub** pour Flatpak), on peut ajouter une section dédiée et les fichiers nécessaires.

---

## Artefacts CI (itch.io / partage)

Le workflow **Build paquet source Debian** (sur push `main` ou manuellement) produit :

| Artefact | Contenu | Usage |
|----------|---------|--------|
| **Debian-source-package** | .orig, .dsc, .changes, .buildinfo, .debian.tar.xz | Envoi PPA (optionnel) |
| **Linux-installers** | `barrelmcd-flutter_1.0.0-1_amd64.deb`, `barrelmcd-flutter_1.0.0_linux-x64.tar.gz` | itch.io, partage direct |
| **Arch-installer** | `barrelmcd-flutter-1.0.0-1-x86_64.pkg.tar.zst` | itch.io / utilisateurs Arch (install : `sudo pacman -U …`) |

Pour itch.io : Windows (zip), macOS (dmg), Linux .deb, tarball Linux, et paquet Arch (.pkg.tar.zst) sont disponibles après un run réussi des workflows.
