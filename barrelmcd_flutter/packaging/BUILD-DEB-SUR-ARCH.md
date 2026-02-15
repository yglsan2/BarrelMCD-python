# Construire le paquet source Debian sur Arch (sans conteneur)

Sur Arch, le réseau dans les conteneurs Podman/Docker pose souvent problème (`/dev/net/tun`, pasta). La solution la plus simple est de **construire directement sur l’hôte** avec Flutter et les outils Debian (disponibles dans l’AUR).

## 1. Installer les outils de packaging

```bash
yay -S devscripts
```

Cela installe aussi `debhelper` et les outils nécessaires à `debuild`.

## 2. Lancer le build

```bash
cd /chemin/vers/BarrelMCD-python
./barrelmcd_flutter/packaging/build_source_package.sh
```

Le script va :
- faire `flutter pub get` puis `flutter build linux --release`
- créer l’archive orig et le paquet source
- produire les fichiers `.dsc` et `.changes` dans `BarrelMCD-python/`

## 3. Envoyer au PPA (optionnel)

Sur une machine où `dput` et ta clé GPG sont configurés :

```bash
cd BarrelMCD-python
debsign -k VOTRE_CLE barrelmcd-flutter_1.0.0-1_source.changes
dput ppa:VOTRE_ID/ppa barrelmcd-flutter_1.0.0-1_source.changes
```
