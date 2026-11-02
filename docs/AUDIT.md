# Audit du calcul et des données

Date : 2 novembre 2026. Détail chiffré : `data/processed/audit_independant.json`. À relancer avec `pipeline/audit_independant.py`.

Cet audit est un contrôle de reproductibilité écrit dans le projet. Il ne remplace pas une relecture par un statisticien.

## Reproductibilité

| Contrôle | Résultat |
|---|---|
| Territoires retrouvés depuis le recensement | 75 |
| Écart maximal sur les valeurs des 18 indicateurs | 0,0005 (arrondi) |
| Écart maximal sur les bornes | 0,0005 (arrondi) |
| 1 350 scores d'indicateurs | Écart maximal 0,005 (arrondi) |
| 450 scores de dimensions | Écart maximal 0,05 (arrondi) |
| 75 indices | Écart maximal 0,05 (arrondi) |
| Rangs différents | 0 |
| Données embarquées dans le site et calcul | Écart maximal 0,008 |
| Statut renseigné pour chaque valeur | Oui |
| Chefs-lieux dans le bon contour | 75 sur 75 |

Le script ne partage aucun code avec le calcul et retrouve les colonnes par leur intitulé. Il a pourtant été écrit par le même auteur à partir de la même compréhension des fichiers : une erreur d'interprétation d'une variable ne serait pas détectée. Les coordonnées des chefs-lieux sont approximatives et n'ont pas été reprises d'une source officielle.

## Tests de méthode

| Variante | Corrélation de rang avec l'indice | 15 derniers conservés | Corrélation avec la pauvreté |
|---|---:|---:|---:|
| Centiles 5-95 pour tous les indicateurs | 0,998 | 15 | −0,91 |
| Scores z, moyenne arithmétique | 0,988 | 13 | −0,94 |
| Inclusion sans la distance à la route | 0,984 | 12 | −0,90 |

Le mélange de bornes ODD et de centiles change très peu le classement. Il peut toutefois changer le niveau d'un score et la dimension la plus faible d'une province.

## Points faibles de conception

1. **Santé (alpha 0,24).** Les centres de soins primaires évoluent en sens inverse de médecins et lits (−0,31). Cela peut refléter une logique de maillage des territoires peu denses, à vérifier, mais ces indicateurs ne mesurent pas la même chose.
2. **Logement (alpha 0,30).** Les logements sommaires évoluent en sens inverse du reste (−0,15).
3. **Redondance.** 11 paires d'indicateurs dépassent 0,8 en corrélation de rang, par exemple assainissement et déchets (0,92). L'écart ville-campagne pèse donc probablement plus que ne le suggèrent les poids égaux.
4. **Distance à la route.** Elle mesure l'accessibilité physique plus que l'inclusion sociale. La retirer change 3 des 15 derniers territoires.
5. **Validation.** La corrélation avec la pauvreté du HCP est en partie mécanique. Aucune autre mesure indépendante n'a encore servi de validation.

Aucun de ces points n'a modifié la formule : ce sont des décisions à prendre avec des relecteurs.

## Corrections apportées

- Leaflet est hébergé avec le site, et la page reste utilisable si la carte ne charge pas.
- Les poids affichent leur pourcentage, et ils ne peuvent plus être tous nuls. Auparavant, tout mettre à zéro donnait 1 à tous les territoires.
- La fiche et le classement affichent le nombre de valeurs publiées ou calculées et les raisons de la fiabilité.
- Le texte des zéros déduits précise qu'ils restent à confirmer.
- Fiches de provenance ajoutées, par source et par indicateur.
- La page Méthodologie décrit l'indice comme une mesure de conditions territoriales, pas de bien-être vécu.

## Hors de portée de cet audit

- Exactitude des fichiers publiés par les producteurs eux-mêmes.
- Textes juridiques récents sur le découpage administratif.
- Droits de réutilisation des données du HCP et de la carte sanitaire.
- Accessibilité complète et tests sur appareils réels.
