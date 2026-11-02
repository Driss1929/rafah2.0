"""Écrit les fiches de provenance : par fichier source et par indicateur.

Usage : python provenance.py [racine_du_projet]
"""
import csv
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed"
EXTRAIT = "2026-11-02"
ODBL = "ODbL (annoncée par data.gov.ma)"
A_CONFIRMER = "À confirmer auprès du producteur"
DG = "https://data.gov.ma/data/fr/dataset/"
# fichier local, producteur, titre exact, page source, licence, usage
SOURCES = [
    ("hcp_national_242671.xlsx", "HCP", "Indicateurs démographiques et socioéconomiques du Royaume du Maroc selon les résultats du RGPH 2024", "https://www.hcp.ma/file/242671/", A_CONFIRMER, "Score"),
    ("hcp_cee_242672.xlsx", "HCP", "Cartographie des établissements économiques 2023/2024, principaux résultats par commune", "https://www.hcp.ma/file/242672/", A_CONFIRMER, "Score"),
    ("hcp_pauvrete_245096.xls", "HCP", "Base de données de la cartographie de la pauvreté multidimensionnelle, mai 2025", "https://www.hcp.ma/file/245096/", A_CONFIRMER, "Validation"),
    ("cartesanitaire_2024.csv", "Ministère de la Santé", "Carte sanitaire, principaux indicateurs, année 2024 (recopié du flux du tableau de bord)", "https://cartesanitaire.sante.gov.ma/dashboard/pages2/indicateur_2025.html", A_CONFIRMER, "Score"),
    ("geoBoundaries-MAR-ADM2_simplified.geojson", "geoBoundaries (OpenStreetMap)", "gbOpen MAR ADM2, version simplifiée, limites de 2017", "https://www.geoboundaries.org/api/current/gbOpen/MAR/ADM2/", "ODbL", "Carte"),
    ("datagov/essp-2024.xlsx", "Ministère de la Santé", "Établissements de soins de santé primaire 2024", DG + "la-liste-des-hopitaux", ODBL, "Score"),
    ("datagov/essp-2025.xlsx", "Ministère de la Santé", "Répartition des établissements de soins de santé primaire, 2025", DG + "repartition-des-etablissements-de-soins-de-sante-primaire-par-categorie-2020", ODBL, "Contexte"),
    ("datagov/hopitaux-2025.xlsx", "Ministère de la Santé", "Liste des hôpitaux 2025", DG + "la-liste-des-hopitaux", ODBL, "Contexte"),
    ("datagov/chomage_prov.xlsx", "HCP", "Taux de chômage selon les Provinces/Préfectures et le Milieu", DG + "data_imt_txch_02", ODBL, "Contexte et test"),
    ("datagov/data_imt_txact_02__i_imt_txact_02_data.xlsx", "HCP", "Taux d'activité selon les Provinces/Préfectures et le Milieu", DG + "data_imt_txact_02", ODBL, "Contexte et test"),
    ("datagov/data_imt_txemp_02__i_imt_txemp_02_data.xlsx", "HCP", "Taux d'emploi selon les Provinces/Préfectures et le Milieu", DG + "data_imt_txemp_02", ODBL, "Contexte et test"),
    ("datagov/nombre-des-s_repartition-du-nombre-des-salaries-declares_2022.xlsx", "CNSS", "Nombre des salariés déclarés en 2022 auprès de la CNSS", DG + "nombre-des-salaries-declares-en-2022-aupres-de-la-cnss", ODBL, "Contexte et test"),
    ("datagov/entreprises-_repartition-du-nombre-des-entreprises-declarantes-_2022.xlsx", "CNSS", "Entreprises déclarantes auprès de la CNSS en 2022", DG + "entreprises-declarantes-aupres-de-la-cnss-en-2022", ODBL, "Contexte"),
    ("datagov/liste-des-etablissements-publi__etablissements_publics_primaire_juillet-2026.xlsx", "Ministère de l'Éducation nationale", "Liste des établissements publics de l'enseignement primaires, juillet 2026", DG + "liste-des-etablissements-publics-primaire", ODBL, "Contexte"),
    ("datagov/liste-de-etablissements-public__etablissements_publics_collegial_juillet-2026.xlsx", "Ministère de l'Éducation nationale", "Liste des établissements publics de l'enseignement collégial, juillet 2026", DG + "liste-de-etablissements-publics-collegial", ODBL, "Contexte"),
    ("datagov/liste-des-etablissements-publi__etablissement_publics_qualifiant_juillet-2026.xlsx", "Ministère de l'Éducation nationale", "Liste des établissements publics qualifiants, juillet 2026", DG + "liste-des-etablissements-publics-qualifiants", ODBL, "Contexte"),
    ("datagov/reseau-des-maisons-de-jeunes-r__-.xlsx", "Ministère de la Jeunesse", "Réseau des maisons de jeunes rurales et urbaines", DG + "reseau-des-maisons-de-jeunes-rurales-et-urbaines-par-region-et-par-province", ODBL, "Contexte"),
    ("datagov/liste-des-etablissements-multi__-.xlsx", "Ministère de la Solidarité", "Liste des établissements multifonctionnels des femmes", DG + "liste-des-etablissements-multifonctionnels-des-femmes-repartis-selon-la-region-et-la-province", ODBL, "Contexte"),
]
POP, MEN = "Feuille Population, Sexe : Ensemble", "Feuille Ménages"
# indicateur : fichier, variables d'origine, transformation
INDICATEURS = {
    "medecins": ("cartesanitaire_2024.csv", "Ratio Habitants par medecin (Public + Privé), 2024", "10 000 / ratio. Casablanca : somme de 8 délégations reconstituée par population / ratio. Aousserd : valeur de sa région."),
    "essp": ("datagov/essp-2024.xlsx", "Lignes CSU-1, CSU-2, CSR-1, CSR-2, DR", "Nombre de lignes / population municipale × 10 000. Casablanca : somme de 8 délégations."),
    "lits": ("cartesanitaire_2024.csv", "Ratio Habitants par lit hospitalier (Public + Privé), 2024", "10 000 / ratio. Ratio vide compté 0 (Fahs-Anjra, Moulay Yacoub, Aousserd)."),
    "analphabetisme": ("hcp_national_242671.xlsx", f"{POP}, Taux d'analphabétisme des 10 ans et plus", "Repris tel quel."),
    "scolarisation": ("hcp_national_242671.xlsx", f"{POP}, Taux de scolarisation des 6-11 ans en 2023/2024", "Repris tel quel."),
    "secondaire": ("hcp_national_242671.xlsx", f"{POP}, Niveau d'études : Secondaire collégial, Secondaire qualifiant, Supérieur", "Somme des trois parts."),
    "chomage": ("hcp_national_242671.xlsx", f"{POP}, Taux de chômage", "Repris tel quel."),
    "salaries": ("hcp_national_242671.xlsx", f"{POP}, Population active occupée ; Statut : Salarié public, Salarié privé ; Population municipale", "Actifs occupés × part de salariés / population municipale × 1 000."),
    "etablissements": ("hcp_cee_242672.xlsx", "Nombre d'établissements à but lucratif, ligne province", "Nombre / population municipale × 1 000."),
    "assainissement": ("hcp_national_242671.xlsx", f"{MEN}, Réseau public d'assainissement", "Repris tel quel."),
    "electricite": ("hcp_national_242671.xlsx", f"{MEN}, Éléments de confort : Électricité", "Repris tel quel."),
    "bidonville": ("hcp_national_242671.xlsx", f"{MEN}, Type de logement : Maison sommaire / Bidonville", "Repris tel quel."),
    "eau": ("hcp_national_242671.xlsx", f"{MEN}, Éléments de confort : Eau courante", "Repris tel quel."),
    "bois": ("hcp_national_242671.xlsx", f"{MEN}, Combustible de cuisson : Charbon, Bois énergie", "Somme des deux parts."),
    "dechets": ("hcp_national_242671.xlsx", f"{MEN}, Déchets : Bac à ordures de la commune, Camion de la commune / Camion privé", "Somme des deux parts."),
    "ecart_alpha": ("hcp_national_242671.xlsx", "Feuille Population, Taux d'analphabétisme des 10 ans et plus, Féminin et Masculin", "Féminin − Masculin, en points."),
    "activite_f": ("hcp_national_242671.xlsx", "Feuille Population, Sexe : Féminin, Taux d'activité des 15 ans et plus", "Repris tel quel."),
    "enclavement": ("hcp_national_242671.xlsx", f"{MEN}, Distance moyenne des logements à la route goudronnée", "Repris tel quel. « … » (Rabat, Casablanca) compté 0 km."),
}
with open(OUT / "sources_empreintes.csv", encoding="utf-8") as f:
    hashes = {r["fichier"]: r["sha256"] for r in csv.DictReader(f)}
with open(OUT / "provenance_sources.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["fichier", "producteur", "titre", "page_source", "date_extraction", "licence", "usage", "sha256"])
    for s in SOURCES:
        assert s[0] in hashes, s[0]
        w.writerow([s[0], s[1], s[2], s[3], EXTRAIT, s[4], s[5], hashes[s[0]]])
# Registre des droits : ce qui n'a pas été vérifié juridiquement reste marqué comme tel.
YEARS = {"hcp_national": "2024", "hcp_cee": "2023/2024", "hcp_pauvrete": "2014, 2024", "cartesanitaire": "2024", "geoBoundaries": "2017", "essp-2024": "2024", "essp-2025": "2025", "hopitaux-2025": "2025", "chomage_prov": "2017-2025", "txact": "2017-2025", "txemp": "2017-2025", "nombre-des-s": "2022", "entreprises-": "2022", "juillet-2026": "2026", "maisons": "Non indiquée", "reseau-des-maisons": "Non indiquée", "multi": "Non indiquée"}
def levels(s):
    if s[1] == "CNSS":
        return "Région"
    lists = ("essp", "hopitaux", "juillet", "maisons", "multi")
    return "Établissement, regroupé par province" if any(k in s[0] for k in lists) else "Province"
with open(OUT / "data_sources_registry.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["source_id", "dataset_name", "producer", "original_url", "reference_year", "geographic_level", "licence", "commercial_use", "redistribution", "attribution", "verification_status"])
    for n, s in enumerate(SOURCES, 1):
        year = next((y for k, y in YEARS.items() if k in s[0]), "Non indiquée")
        if s[4] == A_CONFIRMER:
            rights = ("À vérifier", "À vérifier", "À vérifier", "À vérifier auprès du producteur")
        else:
            rights = ("Permis sous conditions ODbL", "Permise sous conditions ODbL (partage à l'identique)", "Oui", "Licence relevée, conditions non revues par un juriste")
        w.writerow([f"S{n:02d}", s[2], s[1], s[3], year, levels(s), s[4], *rights])
with open(OUT / "rafah_metadonnees.csv", encoding="utf-8-sig") as f:
    meta = list(csv.DictReader(f))
assert {m["id"] for m in meta} == set(INDICATEURS)
with open(OUT / "provenance_indicateurs.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["indicateur", "libelle", "fichier_source", "variables_origine", "transformation", "borne_basse", "borne_haute", "base_des_bornes"])
    for m in meta:
        w.writerow([m["id"], m["label"], *INDICATEURS[m["id"]], m["L"], m["U"], m["bornes"]])
print(f"{len(SOURCES)} sources et {len(meta)} indicateurs documentés")
