# Architecture actuelle

```
data/raw/ (non versionné, 36 fichiers : HCP, ministère de la Santé, data.gov.ma, geoBoundaries)
   │
   ├─ pipeline/build_index.py ──► data/processed/  (indice, contexte, contours, métadonnées)
   │     └─ audit_territoires.py, audit_independant.py, provenance.py  (contrôles et provenance)
   │
   ├─ pipeline/ingest.py + datasets.py ──► data/observations/  (observations versionnées, jeux, rapports qualité)
   │
   ├─ pipeline/build_api.py ───────► data/api/v1/ (territoires, classements, géométries)
   ├─ pipeline/build_divisions.py ─► data/api/v1/ (dictionnaire, divisions, observations) + infra/observatoire.sql
   ├─ infra/export_postgis.py ─────► infra/rafah_postgis.sql
   └─ pipeline/build_app.py ───────► app/ (site statique, Vercel)

Services locaux :
   FastAPI  backend/main.py        127.0.0.1:8000  lit data/api/v1
   PostGIS  C:\Users\hp\rafah-tools  localhost:5544  charge rafah_postgis.sql puis observatoire.sql
   GeoServer                         127.0.0.1:8085  publie la vue territoires_scores (WMS, WFS)
   Site     app/                     127.0.0.1:8090  ou https://rafah20.vercel.app/app/
Déploiement serveur préparé, non testé : deploy/ (Docker Compose, Caddy, PostGIS, GeoServer, API).
```

## Identifiants

Le code géographique HCP (4 chiffres, 5 pour les régions 10 à 12) identifie chaque province ou préfecture partout : CSV, JSON, API, PostGIS, contours. Les listes ministérielles n'ont pas de code : elles sont rapprochées par nom normalisé, avec alias manuels et contrôle bloquant.

## Modèle de l'observatoire

| Objet | Fichier | Table PostGIS |
|---|---|---|
| Division | `data/metadata/divisions.csv` | `divisions` |
| Indicateur | `rafah_metadonnees.csv` (indice) + `data/metadata/indicator_dictionary.csv` | `indicator_catalogue` |
| Statut de valeur | `data/metadata/value_status.csv` | `value_statuses` |
| Source | `data/processed/data_sources_registry.csv` | `data_sources` |
| Jeu ingéré | `data/observations/datasets.csv` | `datasets` |
| Observation | `data/observations/observations.csv` | `indicator_observations` |
| Contrôle qualité | `data/observations/quality/<jeu>.json` | (fichiers) |

Une observation porte : indicateur, territoire, période, valeur, statut, justification, source, jeu, version, date d'ingestion, drapeau « courante ». Une correction ajoute une version ; l'ancienne reste, marquée non courante.

## Tests

| Commande | Contrôles |
|---|---|
| `python pipeline/test_rafah.py` | 9 : couverture, totaux officiels, recalcul, échelle, statuts, empreintes |
| `python pipeline/test_observatoire.py` | 8 : intégrité, zéros justifiés, indice inchangé, cohérence Santé, totaux, versionnement, refus des valeurs invalides, SQL |
| `python -m pytest backend/test_api.py` | 8 : routes, scores, sécurité des identifiants, divisions, observations |
| `python pipeline/test_site.py` | 14 pages |
