# Mettre Rafah en ligne

Un seul serveur Linux suffit, avec au moins 2 Go de mémoire (4 Go conseillés), car GeoServer en consomme beaucoup. Le fournisseur et ses tarifs sont à vérifier au moment de la commande.

Résultat :

- `https://api.DOMAINE/docs` : FastAPI.
- `https://geoserver.DOMAINE/geoserver/rafah/ows` : services WMS et WFS, en lecture seule.
- PostGIS : en ligne sur le serveur, mais privé. Il n'est accessible que par GeoServer, jamais depuis Internet.

## Installation

Sur un serveur Ubuntu 24.04 neuf, connecté en SSH :

```bash
curl -fsSL https://get.docker.com | sh
```

```bash
git clone https://github.com/Driss1929/rafah2.0.git && cd rafah2.0/deploy
```

Sans nom de domaine, utilisez `IP_DU_SERVEUR.sslip.io` comme domaine :

```bash
sh make_env.sh DOMAINE
```

```bash
docker compose up -d --build
```

Ouvrez seulement les ports 22, 80 et 443 dans le pare-feu. Si vous utilisez un vrai domaine, créez d'abord les enregistrements DNS `api` et `geoserver` vers l'adresse du serveur.

Contrôle depuis votre machine :

```bash
sh smoke_test.sh DOMAINE
```

## Administration de GeoServer

L'administration est fermée au public. Pour y accéder, ajoutez temporairement au service `geoserver` un port limité à `127.0.0.1:8085:8080`, puis ouvrez un tunnel SSH. Le mot de passe est dans `deploy/.env`.

## Mise à jour

```bash
git pull && docker compose up -d --build
```

Les fichiers `rafah_postgis.sql` puis `observatoire.sql` ne sont chargés qu'à la première création de la base. Après un recalcul, dans cet ordre :

```bash
docker compose exec -T db psql -U rafah -d rafah < ../infra/rafah_postgis.sql
```

```bash
docker compose exec -T db psql -U rafah -d rafah < ../infra/observatoire.sql
```

## Avant de publier

- Les droits de réutilisation des données du HCP et de la carte sanitaire ne sont pas confirmés.
- Les résultats restent non officiels.
- Ces fichiers n'ont pas encore été testés sur un vrai serveur : `smoke_test.sh` sert à le vérifier.
- `.env` contient des mots de passe : il ne doit jamais être envoyé sur GitHub.
- Prévoyez les mises à jour du serveur et des sauvegardes.
