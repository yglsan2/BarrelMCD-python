# Docker sur Arch avec noyau 6.18

Sur noyau 6.18, Docker peut échouer avec :
- `Module ip_tables not found` (iptables absent du noyau)
- `nftables: cache initialization failed: Invalid argument`
- `Failed to create bridge docker0 via netlink: operation not supported`

**Deux solutions qui fonctionnent :**

---

## Option A : Utiliser Podman (recommandé, sans changer de noyau)

Podman est compatible Docker (même Dockerfile, même `run`) et n’a pas de démon. Il fonctionne en général avec le noyau 6.18.

```bash
sudo pacman -S podman
cd BarrelMCD-python
./barrelmcd_flutter/packaging/podman-build-deb.sh
```

Le script utilise le même `Dockerfile.deb` que pour Docker.

---

## Option B : Noyau LTS (pour continuer à utiliser Docker)

Le noyau LTS embarque encore les modules réseau attendus par Docker.

```bash
sudo pacman -S linux-lts
# Redémarrer la machine, puis au démarrage (GRUB) choisir « Linux LTS ».
# Ensuite Docker devrait démarrer normalement ; tu peux vider ou supprimer /etc/docker/daemon.json.
sudo systemctl start docker
```
