# Commandes à copier-coller pour les installables

---

## 1. Debian / Ubuntu (.deb)

```bash
cd /home/benjisan/BarrelMCD-python/barrelmcd_flutter && ./packaging/build_deb.sh
```

---

## 2. Arch Linux (.pkg.tar.zst)

```bash
cd /home/benjisan/BarrelMCD-python/barrelmcd_flutter && ./packaging/build_arch.sh
```

---

## 3. Windows (installeur .exe)

À exécuter **sous Windows** (PowerShell ou CMD) :

```cmd
cd barrelmcd_flutter
flutter pub get
flutter build windows --release
```

Puis compiler le script Inno Setup (ouvrir `packaging\barrelmcd_flutter.iss` dans Inno Setup et lancer la compilation, ou en ligne de commande) :

```cmd
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" packaging\barrelmcd_flutter.iss
```

---

## 4. macOS (.dmg)

À exécuter **sous macOS** :

```bash
cd barrelmcd_flutter
./packaging/build_macos_dmg.sh
```

---

## Installation après build

**Debian/Ubuntu :**
```bash
sudo dpkg -i packaging/out/barrelmcd-flutter_1.0.0_amd64.deb
```

**Arch :**
```bash
sudo pacman -U packaging/out/barrelmcd-flutter-1.0.0-1-x86_64.pkg.tar.zst
```
