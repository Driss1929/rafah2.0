# Audit technique de Rafah (M01)

Date : 3 novembre 2026. Branche : `feature/rafah-foundation-audit`, partie du commit `0adc9ab` (« Add server deployment for FastAPI, PostGIS and GeoServer »).
Inventaires détaillés : `feature_inventory.xlsx` (29 fonctionnalités) et `dataset_inventory.xlsx` (36 fichiers bruts), régénérés par `python pipeline/audit_inventory.py`.
Documents liés : `architecture_current.md`, `development_backlog.md`, `technical_risks.md`.

## 1. Synthèse

Rafah est aujourd'hui un indice composite reproductible (18 indicateurs, 6 dimensions, 75 provinces et préfectures), publié en site statique, avec une API interne en lecture seule, une base PostGIS et un GeoServer locaux. Le calcul est contrôlé : recalcul indépendant sans écart de rang, 9 contrôles de reproductibilité, 8 contrôles du socle, 8 tests d'API, 14 pages contrôlées.

Pendant cet audit, le socle commun aux 12 divisions existe sous une première forme : dictionnaire d'indicateurs, statuts de valeur, moteur d'ingestion avec versionnement, schéma PostGIS de l'observatoire, et une division pilote, Santé, alimentée uniquement par des données réelles.

Ce qui manque pour la suite, par ordre d'importance :

1. Un référentiel géographique complet : les régions n'ont pas de contour, les communes sont absentes, les noms arabes aussi, et les contours viennent de geoBoundaries (2017, OpenStreetMap), pas d'une source administrative officielle (M02).
2. Un circuit de publication en quatre états (brut, attente, validé, publié) et une interface d'import (M04).
3. Le registre des sources : 18 fichiers téléchargés n'y sont pas, dont un utilisé par la division Santé. Les licences du HCP et de la carte sanitaire ne sont pas confirmées.
4. Les 11 autres divisions, l'observatoire historique, l'IA, les alertes et la simulation de politiques (M05 à M14).
5. Sécurité et exploitation : pas d'authentification, pas de journalisation, déploiement serveur jamais testé (M15).

## 2. Architecture existante

Voir `architecture_current.md`. En résumé : des scripts Python lisent `data/raw/` (non versionné), écrivent des résultats contrôlés dans `data/processed/`, puis trois sorties sont produites à partir des mêmes fichiers : le site statique `app/`, le contrat d'API `data/api/v1/` servi par FastAPI, et deux scripts SQL pour PostGIS.

## 3. Fonctionnalités existantes

13 fonctionnent, 8 sont partielles, 8 absentes (détail dans `feature_inventory.xlsx`).

| Fonctionnalité | État | Action |
|---|---|---|
| Carte nationale (Leaflet, MapLibre, GeoServer) | Fonctionne | Garder ; ajouter le choix de division et d'indicateur |
| Fiches de territoire | Partiel | Fiche de l'indice et profil Santé séparés ; profil unique à construire (M10) |
| Explorateur d'indicateurs | Partiel | Indice et Santé seulement ; explorateur universel à construire (M10) |
| Graphiques et tableaux | Fonctionne | Garder ; composant `site/division.js` réutilisable |
| Affichage des sources | Fonctionne | Garder ; compléter le registre |
| Simulateur | Partiel | Pondérations de l'indice seulement (M14) |
| Authentification et administration | Absent | Inutile tant que tout est public en lecture (M15) |

## 4. Jeux de données

36 fichiers bruts sont présents localement : 18 sont décrits dans `provenance_sources.csv`, 18 ne le sont pas. 7 jeux sont ingérés dans l'observatoire (2 250 observations courantes, 39 indicateurs au dictionnaire). Le détail (producteur, URL, format, lignes, cellules vides, empreinte, usage) est dans `dataset_inventory.xlsx`.

Constats :

- `datagov/hopitaux-2024.xlsx` alimente la division Santé mais n'est pas dans le registre de provenance.
- Les listes scolaires de juin 2023 et quatre listes de structures sociales servent de contexte sans être enregistrées.
- Les dates de publication des jeux n'ont pas été relevées.
- Les licences sont « À confirmer » pour le HCP et la carte sanitaire, « ODbL annoncée » pour data.gov.ma.

## 5. Base de données

PostGIS 3.6 sur PostgreSQL 18, portable, port 5544, local uniquement. Deux scripts générés :

- `infra/rafah_postgis.sql` : `territories` (75, géométries valides, index spatial), `dimensions`, `indicators` (18), `territory_dimensions`, `territory_indicators`, vue `territoires_scores` publiée par GeoServer.
- `infra/observatoire.sql` : `divisions` (12), `data_sources`, `value_statuses`, `indicator_catalogue`, `datasets`, `indicator_observations` (versionnée, une seule valeur courante par indicateur, territoire et période, valeur nulle obligatoire pour un statut sans valeur), vue `observations_courantes`.

Écarts avec le modèle visé par le manuel : un seul schéma `public` au lieu des schémas logiques ; les périodes sont du texte (`2024`, `2023/2024`) et non des dates de début et de fin ; pas de table de contours versionnés ni de hiérarchie parent-enfant ; pas de migrations, les scripts recréent les tables.

## 6. Dette technique

- `pipeline/build_index.py` (515 lignes) mêle lecture, rapprochement des noms, calcul et export ; les extracteurs Santé le réutilisent.
- Rapprochement des listes ministérielles par nom de délégation (`key()`, alias manuels) : ces fichiers ne portent pas de code géographique. C'est contraire à la règle « ne jamais s'appuyer seulement sur le texte » ; chaque rapprochement est contrôlé par un `assert`, mais une table de correspondance versionnée est nécessaire (M02).
- Le site embarque les données dans chaque page (jusqu'à 475 Ko) : acceptable pour 75 territoires, pas pour les communes.
- Deux pipelines parallèles : l'indice (`rafah.json`) et l'observatoire (`observations.csv`). Les tests vérifient qu'ils concordent ; à terme, l'indice devrait lire l'observatoire.
- Environnement Python non figé hors `requirements.txt` ; pas d'intégration continue.

## 7. Sécurité

- API : lecture seule, routes limitées à des identifiants numériques ou alphabétiques (testé contre les chemins `..`), CORS ouvert en `GET`. Pas d'authentification, pas de limitation de débit, pas de journal.
- PostGIS local en `trust` sur `localhost` uniquement ; GeoServer local avec le compte par défaut. Acceptable sur ce PC, interdit en ligne : le déploiement Docker génère des mots de passe (`make_env.sh`) et n'expose que Caddy.
- Aucune donnée personnelle n'est traitée : uniquement des agrégats provinciaux publiés.
- Données brutes et dossier de candidature exclus de Git.

## 8. Capacités manquantes

Contours régionaux et communaux, noms arabes, hiérarchie territoriale ; circuit de validation et interface d'import ; imports planifiés ; observatoire historique dédié ; 11 divisions ; profils multi-divisions ; recherche ; IA ; alertes ; scénarios ; rôles ; journalisation ; sauvegardes ; documentation utilisateur et administrateur.

## 9. Composants réutilisables

- Moteur d'ingestion `pipeline/ingest.py` : empreinte, rapprochement, contrôles bloquants, versionnement, rapport qualité. Un nouveau jeu = une fonction d'extraction dans `pipeline/datasets.py`.
- Dictionnaire `data/metadata/indicator_dictionary.csv` et statuts `value_status.csv`.
- Composant de page `site/division.js` : catalogue, carte, profil, comparaison, export, évolution, inégalités, signaux, sources, à partir d'un seul JSON.
- `pipeline/build_divisions.py` : couverture, Gini pondéré, signaux, export API et SQL.
- Référentiel `referentiel_territoires.geojson` (code HCP comme identifiant stable).
- Chaîne PostGIS, GeoServer, MapLibre, FastAPI, Docker.

## 10. Ordre de développement recommandé

1. M02 Référentiel géographique : régions, communes, noms arabes, contours versionnés, table de correspondance des noms.
2. M03 Architecture : schémas logiques, périodes en dates, migrations, registre complet des sources.
3. M04 Ingestion : états d'attente et de publication, interface d'import, rapports de rejet.
4. M05 Éducation et Économie, en réutilisant le modèle Santé (données déjà téléchargées : RGPH, écoles, emploi 2017-2025, CNSS, établissements économiques).
5. Puis M06 à M15 dans l'ordre du manuel. Détail et critères dans `development_backlog.md`.

Test d'acceptation de M01 : ce document, les deux inventaires et le backlog doivent permettre à un autre développeur de savoir ce qui existe et ce qui reste à faire. Il n'a pas encore été relu par une autre personne.
