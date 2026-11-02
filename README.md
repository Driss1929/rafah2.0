# Rafah (رفاه)

Indice composite de bien-être des 75 provinces et préfectures du Maroc, avec carte interactive et simulateur. Projet préparé pour le 3e Hackathon Open Data (21-22 décembre 2026).

## Contenu

| Élément | Emplacement |
|---|---|
| Site construit, à déployer | `app/` |
| Accueil et pages éditoriales | `site/pages/`, `site/site.css` |
| Carte, fiches, simulateur, pondérations | `site/explorer.template.html`, publié en `app/explorer.html` |
| Contrôle des 75 territoires | `data/processed/audit_territoires.csv` |
| Résultats par province | `data/processed/rafah_provinces.csv` |
| Scores des 18 indicateurs | `data/processed/rafah_scores_indicateurs.csv` |
| Bornes et sources | `data/processed/rafah_metadonnees.csv` |
| Données de contexte du portail, hors score | `data/processed/rafah_contexte.csv` |
| Méthode et écarts avec la grille initiale | `docs/METHODOLOGIE.md` |
| Code de calcul | `pipeline/build_index.py`, `pipeline/build_app.py` |

## Recalculer

Les fichiers sources ne sont pas dans ce dépôt. Téléchargez-les depuis les liens ci-dessous et placez-les dans `data/raw/`, sous les noms indiqués.

```bash
pip install -r requirements.txt
```

```bash
python pipeline/build_index.py
```

```bash
python pipeline/build_app.py
```

Pour contrôler les résultats, même sans les données brutes :

```bash
python pipeline/test_rafah.py
```

```bash
python pipeline/audit_territoires.py
```

```bash
python pipeline/test_site.py
```

La page charge Leaflet depuis cdnjs et ses polices depuis Google Fonts : elle a besoin d'Internet. Le jour de la démonstration, prévoir une connexion ou le lien publié.

## Sources (`data/raw/`)

| Fichier | Source | Licence |
|---|---|---|
| `hcp_national_242671.xlsx` | [HCP, indicateurs RGPH 2024](https://www.hcp.ma/file/242671/) | À confirmer |
| `hcp_cee_242672.xlsx` | [HCP, établissements économiques 2023/2024](https://www.hcp.ma/file/242672/) | À confirmer |
| `hcp_pauvrete_245096.xls` | [HCP, pauvreté multidimensionnelle](https://www.hcp.ma/file/245096/) | À confirmer |
| `cartesanitaire_2024.csv` | [Ministère de la Santé, carte sanitaire](https://cartesanitaire.sante.gov.ma/dashboard/pages2/indicateur_2025.html) | À confirmer |
| `datagov/essp-2024.xlsx` | [data.gov.ma, soins primaires](https://data.gov.ma/data/fr/dataset/la-liste-des-hopitaux) | ODbL |
| `datagov/nombre-des-s_*.xlsx` | [data.gov.ma, CNSS 2022](https://data.gov.ma/data/fr/dataset/nombre-des-salaries-declares-en-2022-aupres-de-la-cnss) | ODbL |
| `datagov/` (autres fichiers) | [data.gov.ma](https://data.gov.ma/data/fr/dataset) : emploi par province, hôpitaux, établissements scolaires, maisons de jeunes, structures sociales | À vérifier par jeu |
| `geoBoundaries-MAR-ADM2_simplified.geojson` | [geoBoundaries](https://www.geoboundaries.org/api/current/gbOpen/MAR/ADM2/) | ODbL |

`cartesanitaire_2024.csv` a été extrait manuellement du fichier que charge le tableau de bord du ministère (`/ws/ws_indicateur_csv.ashx`, année 2024). Il ne peut pas être téléchargé par script simple, car le site filtre les robots.

Les résultats et la page reprennent des valeurs issues de ces sources : HCP, ministère de la Santé, data.gov.ma et geoBoundaries (OpenStreetMap). Projet indépendant, sans lien avec ces organismes. Contours et données sous ODbL : leurs conditions d'attribution et de partage s'appliquent. Les conditions de réutilisation des données du HCP et de la carte sanitaire restent à confirmer ; tout ayant droit peut demander une correction ou un retrait.
