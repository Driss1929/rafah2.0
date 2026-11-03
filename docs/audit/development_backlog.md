# Backlog de développement

Statuts : Backlog, Prêt, En cours, Bloqué, En revue, Terminé. Une tâche n'est terminée que si elle utilise des données réelles, a une source identifiée, une formule documentée, des valeurs manquantes traitées, des tests qui passent et une documentation.

## Fait sur la branche `feature/rafah-foundation-audit` (en revue, non poussé)

| ID | Jalon | Tâche | Preuve |
|---|---|---|---|
| T-001 | M01 | Audit, inventaires, architecture, risques, backlog | `docs/audit/` |
| T-002 | M03 | Dictionnaire d'indicateurs (39) et statuts de valeur (8) | `data/metadata/` |
| T-003 | M03 | Schéma PostGIS de l'observatoire, observations versionnées | `infra/observatoire.sql`, chargé en local |
| T-004 | M04 | Moteur d'ingestion : empreinte, rapprochement, contrôles, versions, rapports | `test_versionnement_et_refus` |
| T-005 | M05 | Division Santé pilote : 9 indicateurs disponibles sur 21, 75 territoires | `app/sante.html`, `test_division_sante` |
| T-006 | M03 | Routes API divisions, dictionnaire, observations | `test_divisions_and_observations` |

## M02 Référentiel géographique (prochain)

| ID | Tâche | Données | Acceptation |
|---|---|---|---|
| T-101 | Rechercher les contours administratifs officiels (ANCFCC, ministère de l'Intérieur) et leurs conditions d'usage | ANCFCC, data.gov.ma | Source et licence enregistrées, ou absence documentée |
| T-102 | Ajouter les 12 régions : code, noms français et arabe, contour par union des provinces | RGPH 2024, référentiel | 12 régions, chaque province a un parent |
| T-103 | Ajouter les communes : codes HCP du RGPH 2024 et contours si une source fiable existe | RGPH 2024 (feuilles communales), sources de contours | Chaque commune a un code unique et un parent ; contour vérifié ou marqué absent |
| T-104 | Noms arabes des 75 provinces | RGPH 2024 version arabe | 75 noms, relus |
| T-105 | Tables `territories` (niveau, parent, validité) et `territory_boundaries` (version, source, SRID) | — | `ST_IsValid` sur tous les contours, aucune boucle de parenté |
| T-106 | Table de correspondance des noms ministériels vers les codes, versionnée | listes data.gov.ma | Plus aucun alias dans le code |
| T-107 | Routes `/v1/regions`, `/v1/provinces`, `/v1/communes`, `/v1/territories/{id}/children` | — | Tests d'API |
| T-108 | Navigateur de hiérarchie et choix région, province, commune sur la carte | — | Test manuel sur mobile et ordinateur |

## M03 Architecture centrale

| ID | Tâche | Acceptation |
|---|---|---|
| T-201 | Schémas logiques (`geography`, `catalog`, `sources`, `observations`…) et migrations versionnées | Base recréée depuis zéro par les migrations |
| T-202 | Périodes en dates de début et de fin, version de méthode, date de publication sur chaque observation | Contrainte d'unicité indicateur, territoire, période, version |
| T-203 | Registre des sources complet : 18 fichiers à ajouter, dates de publication, fréquence | Aucun fichier brut hors registre |
| T-204 | Noms arabes, sens d'interprétation, règles d'éligibilité dans le dictionnaire | Dictionnaire relu |
| T-205 | Motif de chaque correction dans l'historique | Test de versionnement étendu |
| T-206 | Faire lire l'indice depuis l'observatoire au lieu de `rafah.json` | Scores identiques, 0 rang différent |

## M04 Ingestion et validation

| ID | Tâche | Acceptation |
|---|---|---|
| T-301 | États brut, attente, validé, publié ; seules les observations publiées sont exposées | Un import non validé n'apparaît ni dans l'API ni sur le site |
| T-302 | Rapport détaillé : reçues, acceptées, rejetées, doublons, manquantes, territoires non rapprochés | Rapport produit pour chaque jeu |
| T-303 | Contrôles de valeurs extrêmes et de dénominateurs | Erreurs volontaires détectées dans un jeu d'essai |
| T-304 | Interface d'import (choix de la source, du niveau, des colonnes, aperçu) | Nécessite l'authentification (M15) |
| T-305 | Imports planifiés pour les seules sources qui l'autorisent | Conditions d'usage vérifiées pour chaque source |

## M05 à M09 Divisions

Ordre : Éducation et Économie (données déjà téléchargées), puis Eau et Infrastructures, Habitat et Environnement, Agriculture et Numérique, Gouvernance, Tourisme et Résilience. Pour chacune : catalogue dans le dictionnaire, sources enregistrées, au moins un jeu ingéré, rapport qualité, page via `site/division.js`, tests. Les indicateurs sans source provinciale restent affichés « non collecté ».

Points de vigilance déjà connus :

- Éducation : distinguer scolarisation brute et nette ; années scolaires et non civiles.
- Économie : ne pas croiser le PIB régional avec le chômage provincial au même niveau.
- Eau : un taux de remplissage de barrage appartient au bassin, pas à la province.
- Infrastructures : demande un moteur d'itinéraires (OSRM ou Valhalla) et le réseau routier ; ne pas utiliser la distance à vol d'oiseau comme temps de trajet.

## M10 à M15

| Jalon | Contenu | Pré-requis |
|---|---|---|
| M10 | Tableau de bord national, explorateur universel, profils multi-divisions, recherche | M02 à M05 |
| M11 | Observatoire historique, convergence (Gini, Theil, coefficient de variation), recensements 2004-2014-2024 | M03, changements de contours documentés |
| M12 | Assistant IA limité à des requêtes validées, avec citations ; jeu de 100 questions vérifiées | M10, M11 |
| M13 | Alertes à règles puis anomalies statistiques, jamais présentées comme alertes officielles | M11 |
| M14 | Scénarios transparents (santé, éducation, eau, mobilité) | M06 pour l'accessibilité |
| M15 | Rôles, authentification, limitation de débit, journaux, sauvegardes, licences, loi 09-08, pilote institutionnel | Toutes |
