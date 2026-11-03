# Vérification technique M01

Date : 3 novembre 2026, commit `fa04d75` (branche `main`, site Vercel à jour). Aucun indicateur ni module ajouté pour cette vérification.
Résultats chiffrés : `data/processed/verification_m01.json`, régénéré par `python pipeline/verify_observatoire.py https://rafah20.vercel.app/app` (demande la base PostGIS locale).

## Suites de tests existantes

| Commande | Résultat |
|---|---|
| `python pipeline/test_rafah.py` | 9 contrôles réussis |
| `python pipeline/audit_territoires.py` | 75 territoires, 11 graphies différentes rapprochées, aucun manquant ni doublon |
| `python pipeline/test_site.py` | 14 pages, aucun problème |
| `python pipeline/test_observatoire.py` | 8 contrôles réussis |
| `python -m pytest backend/test_api.py` | 8 tests réussis |

## Les sept questions

**1. Le pipeline d'ingestion fonctionne-t-il ?** Oui. Les 7 jeux s'ingèrent depuis les fichiers bruts. Un second passage ne crée aucune nouvelle version (2 250 valeurs inchangées). Le test `test_versionnement_et_refus` vérifie qu'une valeur corrigée crée la version 2 sans effacer la version 1, et que cinq valeurs invalides sont refusées : 0 marqué manquant, valeur vide marquée calculée, zéro réel non nul, pourcentage de 120 et valeur négative.

**2. Les 75 territoires sont-ils tous rapprochés ?** Oui. Chaque couple indicateur-période couvre exactement 75 territoires dans PostGIS, et les 75 contours sont valides (`ST_IsValid`). Limite : les listes ministérielles n'ont pas de code et sont rapprochées par nom, avec des alias et un contrôle bloquant. Une table de correspondance versionnée reste à faire (backlog T-106).

**3. Chaque observation est-elle stockée avec sa source ?** Oui. Aucune observation n'est sans source ni sans jeu, et la base l'impose par des clés étrangères. Le registre était incomplet au moment de la vérification (18 fichiers absents) ; c'est corrigé, voir plus bas.

**4. Chaque division retrouve-t-elle ses indicateurs ?** Oui pour les 7 divisions qui en ont : Santé (11 indicateurs observés), Éducation (4), Économie (4), Habitat (3), Environnement (2), Eau (1) et Infrastructures (1). Hors Santé, ce sont seulement les indicateurs de l'indice qui leur sont rattachés. Agriculture, Numérique, Gouvernance, Tourisme et Résilience n'ont encore aucune observation : elles ne sont pas opérationnelles.

**5. Les valeurs manquantes sont-elles distinguées de zéro ?** Oui, de deux façons :
- **Statut et valeur toujours cohérents** : aucune valeur vide ne porte un statut qui exige une valeur, et la base le contrôle.
- **Indicateurs sans source provinciale** (12 en Santé) : ils n'ont aucune observation et sont affichés « non collecté » ou « non publié par province ».

Les 20 zéros en statut « zéro réel » sont tous justifiés par une liste officielle. Les 9 autres zéros sont :
- 7 parts de ménages cuisinant au bois ou au charbon, publiées à 0,0 % par le HCP ;
- 2 distances à la route pour Rabat et Casablanca, publiées « … » (sans objet) et comptées 0 par convention documentée.

Limite : aucune valeur réelle ne porte encore le statut « manquant », car les jeux ingérés sont complets. Seul le test exerce ce cas.

**6. La page publiée reflète-t-elle la base ?** Oui. Les 600 valeurs du tableau de la page Santé (75 territoires × 8 indicateurs) sont identiques à la vue PostGIS `observations_courantes`, aussi bien pour la page locale que pour la page en ligne. Précision : la page n'interroge pas la base. Les deux sont produites par le même script à partir des mêmes fichiers.

**7. Peut-on reproduire les résultats publiés à partir des sources documentées ?** Oui, sur ce PC. La chaîne complète a été relancée depuis `data/raw/` : `build_index`, audits, provenance, API, ingestion, divisions, SQL et site. Le seul écart avec le commit porte sur les fins de ligne de deux fichiers CSV (réglage Git sous Windows), sans aucune différence de contenu. Limite : les fichiers bruts ne sont pas dans le dépôt public. Une autre personne doit les télécharger depuis les liens du README, et la carte sanitaire a été extraite à la main.

## Ce qu'il faut corriger avant d'élargir les divisions

1. Fait : les 18 fichiers manquants sont enregistrés (S19 à S36), soit 36 sources pour 36 fichiers. Pour chacun des 31 fichiers venant de data.gov.ma, la ressource du portail a été téléchargée le 3 novembre 2026 et son empreinte SHA-256 comparée au fichier local : les 31 sont identiques. Les adresses exactes et les dates de mise en ligne sont dans `data/metadata/datagov_resources.csv`.
2. Fait : chaque source porte une classe de fiabilité. Le HCP et data.gov.ma sont en A (officiel téléchargeable), la carte sanitaire en C (recopiée d'un tableau de bord) et geoBoundaries en D (source secondaire). Aucune source n'est en B ou E pour l'instant.
3. À faire : remplacer les alias de noms par une table de correspondance versionnée.
4. À faire : faire relire cette vérification par une autre personne, puisque le même auteur a écrit le code et les contrôles.

Constats faits en complétant le registre :

- La source des hôpitaux 2024 était fausse (S08, la liste 2025). Elle est corrigée en S19. Les 75 valeurs concernées ont reçu une version 2, et la version 1 reste dans l'historique.
- Le portail range certaines ressources dans le mauvais jeu : les ESSP 2024 sont dans « Liste des hôpitaux », et les hôpitaux 2024 dans « Répartition des ESSP par catégorie ». La ressource « Infrastructures privées 2020 » contient en réalité 2022.
- Trois listes du ministère de la Solidarité contiennent des coordonnées. Deux donnent les noms, téléphones et courriels de personnes (S31 et S33), la troisième les téléphones des centres (S32). Rafah n'en tire que des comptages par province, et ces fichiers ne sont ni dans Git ni sur le site. Un test le vérifie.
- Quatre fichiers ne servent à rien pour comparer les 75 territoires : les indicateurs sociaux (nationaux), les infrastructures privées (nationales), le parc fixe de l'Habitat (un annuaire téléphonique) et l'investissement 2021 (région Souss-Massa seulement).
