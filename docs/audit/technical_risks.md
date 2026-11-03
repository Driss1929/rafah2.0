# Risques techniques et de données

| ID | Risque | Probabilité | Effet | Mesure prévue |
|---|---|---|---|---|
| R01 | Droits de réutilisation des données du HCP et de la carte sanitaire non confirmés | Élevée | Publication à retirer | Demande écrite aux producteurs avant toute diffusion institutionnelle |
| R02 | Contours geoBoundaries 2017 simplifiés, non officiels | Certaine | Superficies et cartes approximatives (H06) | M02 : source officielle ou mention explicite |
| R03 | Rapprochement des listes ministérielles par nom | Moyenne | Établissement compté dans la mauvaise province | Contrôles bloquants actuels ; table de correspondance versionnée (T-106) |
| R04 | Fichiers bruts hors registre de provenance | Corrigé | Traçabilité incomplète | 36 sur 36 enregistrés, contrôle automatique |
| R14 | Listes ministérielles contenant des coordonnées de personnes (S31, S33) | Certaine | Diffusion de données personnelles (loi 09-08) | Jamais versionnées ni publiées ; comptages seulement ; test automatique |
| R05 | Indicateurs provinciaux de santé indisponibles (infirmiers, mortalité, vaccination, accès) | Certaine | Division Santé limitée à 9 indicateurs sur 21 | Affichage « non collecté » ; demandes aux producteurs |
| R06 | Un territoire sans hôpital peut être desservi par un voisin | Certaine | Signaux mal interprétés | Avertissement sur la page ; accessibilité par itinéraires (M06) |
| R07 | Dénominateur 2024 utilisé pour les comptes 2025 | Certaine | Ratios 2025 légèrement surestimés si la population croît | Documenté dans le dictionnaire ; à remplacer par les projections HCP |
| R08 | Déploiement serveur jamais testé ; image PostGIS amd64 sur machine ARM | Élevée | Mise en ligne bloquée | Changer d'image ou de machine avant le déploiement |
| R09 | API sans authentification ni limitation de débit | Faible tant qu'elle est locale | Abus si exposée | M15 avant toute ouverture publique |
| R10 | GeoServer local avec le compte par défaut | Faible (local) | Prise de contrôle si exposé | Jamais exposé ; mot de passe généré en déploiement |
| R11 | Pages embarquant toutes les données | Moyenne au niveau communal | Pages lourdes | Chargement par l'API à partir de M02 |
| R12 | Audit et calcul écrits par la même équipe | Certaine | Erreur d'interprétation non détectée | Relecture par un statisticien |
| R13 | Projet porté par une seule personne | Élevée | Ambition des 15 jalons hors de portée avant le hackathon (21-22 décembre 2026) | Prioriser M02 à M05 ; les autres jalons restent au backlog |
