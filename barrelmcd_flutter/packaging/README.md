# Packaging BarrelMCD Flutter

Ce dossier contient les scripts et configurations pour générer les installables par plateforme.

**Important :**
- **Windows** : à construire **sous Windows** (Flutter ne cross-compile pas vers Windows depuis Linux).
- **macOS** : à construire **sous macOS** (Flutter ne cross-compile pas vers macOS depuis Linux).
- **.deb** et **Arch** : peuvent être construits sous Linux (Debian/Ubuntu pour .deb, Arch pour .pkg.tar.zst).

---

## 1. Windows (.exe / portable)

**Sans machine Windows :** utilisez **GitHub Actions**. Poussez sur `main` (ou déclenchez le workflow « Build Windows et macOS » dans l’onglet Actions). Téléchargez l’artifact **BarrelMCD-Flutter-Windows-x64** : c’est un zip contenant `barrelmcd_flutter.exe` et les DLL. Décompressez et lancez l’exécutable.

**Sur une machine Windows :**  
Prérequis : Flutter SDK, optionnel [Inno Setup 6](https://jrsoftware.org/isinfo.php) pour un installeur.

```cmd
cd barrelmcd_flutter
flutter pub get
flutter build windows --release
```

- **Portable :** les fichiers sont dans `build\windows\x64\runner\Release\`. Lancez `barrelmcd_flutter.exe`.
- **Installeur .exe :** ouvrir `packaging\barrelmcd_flutter.iss` dans Inno Setup et compiler → `Output\BarrelMCD_Flutter_Setup_1.0.0.exe`.

---

## 2. Debian / Ubuntu (.deb)

**Prérequis :** Flutter SDK, `dpkg-deb`.

```bash
cd barrelmcd_flutter
./packaging/build_deb.sh
```

Génère : `barrelmcd-flutter_1.0.0_amd64.deb` dans `packaging/out/`.

Installation : `sudo dpkg -i barrelmcd-flutter_1.0.0_amd64.deb`

---

## 3. Arch Linux (.pkg.tar.zst)

**Prérequis :** Arch (ou chroot Arch), Flutter SDK.

**Option A – depuis le clone (recommandé) :**
```bash
cd barrelmcd_flutter
./packaging/build_arch.sh
```
Génère : `packaging/out/barrelmcd-flutter-1.0.0-1-x86_64.pkg.tar.zst`.

**Option B – avec PKGBUILD (pour AUR / tarball) :** copier `packaging/PKGBUILD` à la racine du dépôt, mettre à jour `source` et `sha256sums` si besoin, puis `makepkg -sf`.

Installation : `sudo pacman -U barrelmcd-flutter-1.0.0-1-x86_64.pkg.tar.zst`

---

## 4. macOS (.dmg)

**Sans Mac :** utilisez **GitHub Actions**. Même workflow que pour Windows. Téléchargez l’artifact **BarrelMCD-Flutter-macOS** → fichier `BarrelMCD_Flutter-1.0.0.dmg` à ouvrir sur un Mac.

**Sur un Mac :**  
Prérequis : Flutter SDK.

```bash
cd barrelmcd_flutter
./packaging/build_macos_dmg.sh
```

Génère : `packaging/out/BarrelMCD_Flutter-1.0.0.dmg`.
