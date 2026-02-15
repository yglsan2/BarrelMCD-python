# Podman en root sur Btrfs (pour sudo ./podman-build-deb.sh)

Sous Btrfs, le stockage root de Podman (`/var/lib/containers/storage`) ne peut pas utiliser le driver **overlay**. Il faut forcer **vfs** et réinitialiser le stockage.

**À exécuter une seule fois en root :**

```bash
# Créer la config stockage pour root (driver vfs compatible Btrfs)
sudo mkdir -p /etc/containers
sudo tee /etc/containers/storage.conf << 'EOF'
[storage]
driver = "vfs"
EOF

# Réinitialiser le stockage root (sinon il garde l’ancien driver)
sudo rm -rf /var/lib/containers/storage
```

Ensuite relancer :

```bash
cd /home/benjisan/BarrelMCD-python
sudo ./barrelmcd_flutter/packaging/podman-build-deb.sh
```

La première fois, l’image sera reconstruite (un peu plus longue avec vfs).
