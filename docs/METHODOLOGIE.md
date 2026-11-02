# Méthodologie de l'indice Rafah

La méthode suit la fiche projet et les lignes directrices OCDE-JRC : normalisation à bornes fixes sur 1-100, moyenne arithmétique dans chaque dimension, moyenne géométrique à poids égaux entre les six dimensions.

## Hiérarchie des sources

Règle appliquée : data.gov.ma d'abord, quand il publie une mesure par province qui résiste aux tests. Sinon, HCP puis ministère de la Santé. L'inventaire a porté sur les 699 jeux du portail.

| Donnée de data.gov.ma | Usage | Pourquoi |
|---|---|---|
| Centres de soins primaires 2024 | Score | Mesure provinciale complète |
| Chômage, enquête emploi, 2017-2025 | Fiche et couche, hors score | 4 provinces manquantes, signe inverse (ci-dessous) |
| Taux d'emploi et d'activité, 2017-2025 | Fichier de contexte, hors score | Taux élevés dans des provinces rurales pauvres |
| Salariés et entreprises CNSS 2022 | Fiche, hors score | Publiés seulement par région |
| Hôpitaux 2025 | Fiche et couche, hors score | Sans nombre de lits, moins précis que les lits de la carte sanitaire |
| Écoles, collèges, lycées publics 2023 et 2026 | Fiche et couche, hors score | Nombre d'établissements, sans effectifs ni capacité |
| Maisons de jeunes, centres pour femmes, centres handicap, unités de protection de l'enfance | Fiche et couche, hors score | Listes de structures, peut-être incomplètes |

Corrélation de rang avec la pauvreté multidimensionnelle du HCP :

| Mesure | Corrélation | Lecture |
|---|---:|---|
| Chômage, recensement | +0,28 | Sens attendu |
| Chômage, portail 2024 | −0,44 | Sens inverse |
| Taux d'emploi, portail 2024 | +0,11 | Sens inverse |
| Taux d'activité, portail 2024 | −0,16 | Faible |
| Collèges et lycées pour 10 000 hab. | +0,13 | Sens inverse : ratio élevé dans des territoires peu peuplés |
| Hôpitaux pour 100 000 hab. | −0,15 | Faible |
| Maisons de jeunes pour 100 000 hab. | +0,18 | Sens inverse |

Ces mesures d'offre ou d'emploi ne sont donc pas entrées dans le score. Remplacer le chômage du recensement par celui du portail change peu le classement (corrélation de rang 0,993) et laisse la validation presque identique (−0,90 contre −0,91), mais imposerait d'imputer 4 provinces. Le portail n'a pas de données provinciales sur l'eau, l'assainissement, l'électricité, l'analphabétisme ou la population.

Les scores n'ont pas changé par rapport à la version précédente : ce travail a enrichi les fiches et les couches, pas le calcul.

## Écarts avec la grille de la fiche projet

L'inventaire a confirmé 12 indicateurs sur 18 tels que prévus. Six ont dû être adaptés, selon la règle de la fiche : remplacement dans la même dimension.

| Indicateur prévu | Retenu | Raison |
|---|---|---|
| Salariés déclarés à la CNSS pour 1 000 hab. | Salariés public + privé pour 1 000 hab. (RGPH 2024) | La CNSS ne publie que par région (2022). Le remplaçant compte aussi l'emploi salarié non déclaré. |
| NEET 15-24 ans | Distance moyenne à la route goudronnée | Aucune donnée NEET provinciale trouvée. Le chômage des femmes, autre candidat, aurait recompté le chômage. |
| Scolarisation 6-11 et 12-14 ans | 6-11 ans seulement | Le fichier du HCP ne donne pas les 12-14 ans. |
| 25 ans et plus de niveau secondaire ou supérieur | Population de niveau secondaire ou supérieur, tous âges publiés | Le fichier ne ventile pas le niveau d'études par âge. L'indicateur reste sensible à la structure par âge. |
| Raccordement au réseau d'eau potable | Eau courante dans le logement | Seule variable publiée. |
| Électricité : raccordement | Électricité disponible dans le logement | Seule variable publiée. |

Le remplacement de la CNSS est le choix le plus discutable. Le test avec la CNSS régionale donne une corrélation de rang de 0,995 avec l'indice retenu : ce choix change peu le classement.

## Traitements particuliers

- **Casablanca** : les 8 délégations sanitaires sont regroupées en une préfecture. Les effectifs sont reconstitués à partir de la population et des ratios du ministère.
- **Aousserd, médecins** : valeur absente, remplacée par la valeur de sa région et signalée. Le test avec 0 médecin ne change pas le classement arrondi.
- **Fahs-Anjra, Moulay Yacoub, Aousserd, lits** : ratio vide, compté comme 0 lit. La liste des hôpitaux 2024 du ministère ne recense aucun hôpital dans ces provinces.
- **Rabat, Casablanca, enclavement** : le HCP indique « sans objet », faute d'habitat rural. La distance est comptée 0 km.
- **Population** : population municipale du RGPH 2024, sauf pour médecins et lits, où le ministère applique ses propres dénominateurs.
- **Géographie** : un libellé arabe de Figuig est erroné dans geoBoundaries (il indique Nador). Le rapprochement utilise le nom latin, et les centres géographiques des 75 contours ont été contrôlés.

## Bornes

Les bornes sont gelées dans `data/processed/rafah_metadonnees.csv`. Neuf indicateurs ont une cible inspirée d'un ODD (100 % d'accès, 0 % de bidonville, 0 point d'écart). L'autre borne et les neuf indicateurs restants utilisent les centiles 5 et 95 de 2024.

Aucune cible chiffrée du Nouveau Modèle de Développement n'a été reprise, car aucune n'a été vérifiée dans le document source. Les correspondances avec les ODD sont mon interprétation et restent à faire valider par un mentor.

## Résultats

- Indice : moyenne de 43,2 entre provinces, de 13,9 (Taounate) à 85,1 (Rabat).
- Dix premiers : Rabat, Casablanca, Agadir-Ida-Ou-Tanane, Tanger-Assilah, Marrakech, Fès, Laâyoune, Oujda-Angad, Tarfaya, Skhirate-Témara.
- Huit provinces sont dans les 15 dernières pour plus de 90 % des pondérations testées : Ouezzane, Moulay Yacoub, Chichaoua, Chefchaouen, Azilal, Figuig, Sidi Bennour, Taounate.

## Validation externe

Corrélation avec le taux de pauvreté multidimensionnelle du HCP 2024, qui n'entre pas dans le calcul :

| Mesure | Pearson | Spearman |
|---|---|---|
| Indice complet | −0,83 | −0,91 |
| Santé et Emploi seulement | −0,58 | −0,68 |

Le signe et la force correspondent à l'attente de la fiche. Le chiffre de −0,91 est toutefois en partie mécanique, car les deux mesures utilisent des variables voisines du recensement (éducation, eau, électricité, logement, cuisson). La seconde ligne, sans ce recoupement, est le test le plus exigeant.

## Robustesse

| Variante | Corrélation de rang | Écart de rang moyen | Écart maximal | 15 derniers conservés |
|---|---:|---:|---:|---:|
| Moyenne arithmétique | 0,988 | 2,4 | 11 | 13 |
| Poids issus de l'ACP | 0,990 | 2,3 | 9 | 13 |
| Sans Santé | 0,973 | 3,5 | 16 | 13 |
| Sans Éducation | 0,987 | 2,5 | 10 | 13 |
| Sans Emploi et revenus | 0,979 | 3,2 | 17 | 12 |
| Sans Logement | 0,992 | 2,0 | 9 | 13 |
| Sans Eau et cadre de vie | 0,992 | 1,8 | 11 | 14 |
| Sans Inclusion | 0,990 | 2,3 | 8 | 14 |
| CNSS régionale 2022 | 0,995 | 1,5 | 6 | 14 |
| Aousserd à 0 médecin | 1,000 | 0,0 | 0 | 15 |
| Chômage du portail | 0,993 | 1,7 | 9 | 13 |

La fourchette de rang de chaque fiche vient de 5 000 tirages aléatoires de poids (Dirichlet, paramètre 4, graine fixe). Sa largeur moyenne est de 10 rangs : un écart de quelques rangs entre deux provinces ne doit pas être surinterprété.

## Statut et fiabilité des données

Chaque valeur porte un statut : publiée, calculée, déduite, imputée ou conventionnelle. Chaque province reçoit aussi un niveau de fiabilité (`data/processed/rafah_fiabilite.csv`) :

- **Prudence** : une valeur imputée, ou moins de 100 000 habitants.
- **Moyenne** : un 0 déduit, ou une fourchette de rang d'au moins 15 places.
- **Élevée** : aucun de ces cas.

Cette règle est un repère de lecture choisi pour ce projet. Les seuils de 100 000 habitants et de 15 places sont des conventions, et ce n'est pas une mesure statistique de l'erreur.

## Reproductibilité

`pipeline/test_rafah.py` recalcule les 75 scores indépendamment du pipeline et contrôle les totaux officiels, les taux de pauvreté publiés par le HCP, l'échelle et l'isolement des simulations. `data/processed/sources_empreintes.csv` donne l'empreinte SHA-256 de chaque fichier source utilisé pour cette version.

## Limites

1. L'offre de soins est comptée sur le lieu d'implantation. Les hôpitaux régionaux de Rabat gonflent son score, et les provinces voisines des grandes villes sont pénalisées.
2. Les petites provinces ont des ratios instables : quelques lits suffisent à placer Tarfaya (15 218 habitants) au plafond.
3. La Santé est la dimension la plus faible dans 44 provinces sur 75. Ce chiffre vient en partie des bornes, car la répartition des médecins et des lits est très concentrée. Il ne prouve pas à lui seul que la santé est le premier problème national.
4. Les bornes de centiles dépendent de la distribution de 2024 : elles ne sont pas des seuils de bien-être absolus.
5. Les années ne sont pas toutes identiques : RGPH 2024, santé 2024, établissements 2023/2024.
6. Les contours géographiques datent de 2017 et sont simplifiés. Ils conviennent à une carte, pas à un calcul de surface.

## Non réalisé

- **Évolution de l'indice Rafah** : elle demande les 18 indicateurs de 2014 aux mêmes définitions. La fiche affiche à la place la pauvreté (2014-2024), le chômage (2017-2025) et les établissements scolaires (2023-2026).
- **Couche de contexte des barrages** : non construite. Le portail ne couvre que les bassins de Souss-Massa et du Tensift, pas tout le pays.
- **Publication en open data sur le portail national** : à faire après confirmation des licences.
