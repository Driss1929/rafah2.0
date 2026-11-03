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
    # Ajoutés le 3 novembre 2026 : fichiers déjà téléchargés mais absents du registre (audit M01).
    ("datagov/hopitaux-2024.xlsx", "Ministère de la Santé", "Liste nominative des établissements hospitaliers par catégorie 2024 (ressource intitulée « Répartition des hôpitaux par région et province 2024 »)", DG + "repartition-des-etablissements-de-soins-de-sante-primaire-par-categorie-2020", ODBL, "Division Santé"),
    ("datagov/chomage_prov_meta.xlsx", "HCP", "Métadonnées du taux de chômage selon les Provinces/Préfectures et le Milieu", DG + "data_imt_txch_02", ODBL, "Documentation"),
    ("datagov/indicateurs-sociaux-2012-2024__indicateurs-sociaux_fr.xlsx", "Ministère de l'Économie et des Finances", "Indicateurs sociaux, version française", DG + "indicateurs-sociaux-2012-2024", ODBL, "Non utilisé"),
    ("datagov/indicateurs-sociaux-2012-2024__indicateurs-sociaux_ar.xlsx", "Ministère de l'Économie et des Finances", "Indicateurs sociaux, version arabe", DG + "indicateurs-sociaux-2012-2024", ODBL, "Non utilisé"),
    ("datagov/indicateurs-sociaux-2012-2024__indicateurs-sociaux_fr_2025.xlsx", "Ministère de l'Économie et des Finances", "Indicateurs sociaux 2025 (annexe 7), version française", DG + "indicateurs-sociaux-2012-2024", ODBL, "Non utilisé"),
    ("datagov/indicateurs-sociaux-2012-2024__indicateurs-sociaux_ar_2025.xlsx", "Ministère de l'Économie et des Finances", "Indicateurs sociaux 2025 (annexe 7), version arabe", DG + "indicateurs-sociaux-2012-2024", ODBL, "Non utilisé"),
    ("datagov/infrastructures-privees-2020__infrastructures-privees-2022.xlsx", "Ministère de la Santé", "Infrastructures de santé du secteur privé 2022 (ressource intitulée « 2020 »)", DG + "infrastructures-privees-2020", ODBL, "Non utilisé"),
    ("datagov/infrastructures-privees-2020__infrastructures-privees-2024.xlsx", "Ministère de la Santé", "Infrastructures de santé du secteur privé 2024", DG + "infrastructures-privees-2020", ODBL, "Non utilisé"),
    ("datagov/infrastructures-privees-2020__infrastructures-privees-2025.xlsx", "Ministère de la Santé", "Infrastructures de santé du secteur privé 2025", DG + "infrastructures-privees-2020", ODBL, "Non utilisé"),
    ("datagov/liste-des-etablissements-publi__etab_pub_primaire_juin-2023.xlsx", "Ministère de l'Éducation nationale", "Liste des établissements publics primaires, juin 2023", DG + "liste-des-etablissements-publics-primaire", ODBL, "Contexte"),
    ("datagov/liste-de-etablissements-public__etab_pub_collegial_juin-2023.xlsx", "Ministère de l'Éducation nationale", "Liste des établissements publics collégiaux, juin 2023", DG + "liste-de-etablissements-publics-collegial", ODBL, "Contexte"),
    ("datagov/liste-des-etablissements-publi__etab_pub_qualifiant_juin-2023.xlsx", "Ministère de l'Éducation nationale", "Liste des établissements publics qualifiants, juin 2023", DG + "liste-des-etablissements-publics-qualifiants", ODBL, "Contexte"),
    ("datagov/liste-des-centres-d-accompagne__-.xlsx", "Ministère de la Solidarité", "Liste des centres d'accompagnement et de protection de l'enfance", DG + "liste-des-centres-d-accompagnement-et-de-protection-de-l-enfance-selon-la-region-et-la-province", ODBL, "Non utilisé"),
    ("datagov/liste-des-centres-d-orientatio__-.xlsx", "Ministère de la Solidarité", "Liste des centres d'orientation et d'assistance des personnes en situation de handicap (COAPH)", DG + "liste-des-centres-d-orientation-et-d-assistance-des-personnes-en-situation-de-handicap-coaph", ODBL, "Contexte"),
    ("datagov/liste-des-unites-de-protection__-.xlsx", "Ministère de la Solidarité", "Liste des unités de protection de l'enfance réparties selon la région et la province", DG + "liste-des-unites-de-protection-de-l-enfance-reparties-selon-la-region-et-la-province", ODBL, "Contexte"),
    ("datagov/parc-fixe-global-des-delegatio__parc-fixe-global-des-dph-.xlsx", "Ministère de l'Aménagement du territoire, de l'Urbanisme et de l'Habitat", "Parc fixe global des délégations provinciales du département de l'Habitat (annuaire téléphonique)", DG + "parc-fixe-global-des-delegations-provinciales-du-departement-de-l-habitat", ODBL, "Non utilisable"),
    ("datagov/repartition-de-l-investissemen__data-investissement-2021-add-repartition-par-provinces-commu", "Centre Régional d'Investissement Souss-Massa", "Répartition de l'investissement et des emplois directs provisoires, 2021", DG + "repartition-de-l-investissement-et-des-emplois-directs-provisoires-au-titre-de-l-annee-2021", ODBL, "Non utilisé"),
    ("datagov/reseau-des-centres-d-accueil-m__-2024-.xlsx", "Ministère de la Jeunesse, de la Culture et de la Communication", "Réseau des centres d'accueil, mars 2024, par région et par province", DG + "reseau-des-centres-d-accueil-mars-2024-par-region-et-par-province", ODBL, "Non utilisé"),
]
# Classe de fiabilité : A officiel téléchargeable, B publication officielle (PDF, bulletin), C plateforme interactive officielle,
# D source secondaire, E estimé ou modélisé. Par défaut A pour le HCP et data.gov.ma.
CLASSES = {"cartesanitaire_2024.csv": "C", "geoBoundaries-MAR-ADM2_simplified.geojson": "D"}
# Niveau et année relevés dans le contenu des fichiers ajoutés, et non déduits de leur titre.
DETAILS = {
    "hopitaux-2024": ("2024", "Établissement, regroupé par province", ""),
    "chomage_prov_meta": ("2017-2025", "Métadonnées", ""),
    "indicateurs-sociaux_fr.xlsx": ("Non relevée", "National", ""),
    "indicateurs-sociaux_ar.xlsx": ("Non relevée", "National", ""),
    "indicateurs-sociaux_fr_2025": ("2014-2025", "National", ""),
    "indicateurs-sociaux_ar_2025": ("2014-2025", "National", ""),
    "infrastructures-privees-2022": ("2022", "National", "Le nom de la ressource dit 2020, la feuille dit 2022."),
    "infrastructures-privees-2024": ("2024", "National", ""),
    "infrastructures-privees-2025": ("2025", "National", ""),
    "juin-2023": ("2023", "Établissement, regroupé par province", ""),
    "centres-d-accompagne": ("Non indiquée", "Établissement", ""),
    "centres-d-orientatio": ("Non indiquée", "Établissement, regroupé par province", ""),
    "unites-de-protection": ("Non indiquée", "Établissement, regroupé par province", ""),
    "parc-fixe": ("Non indiquée", "Service administratif", "Annuaire de lignes téléphoniques, sans donnée statistique."),
    "investissemen": ("2021", "Province (région Souss-Massa seulement)", "Couvre une seule région : inutilisable pour comparer les 75 territoires."),
    "centres-d-accueil": ("2024", "Établissement", ""),
}
# Fichiers contenant des coordonnées de personnes : jamais republiés, seuls des comptages en sont tirés.
PERSONAL = {"liste-des-centres-d-accompagne__-.xlsx": "Noms, téléphones et courriels de coordinateurs",
            "liste-des-unites-de-protection__-.xlsx": "Noms, téléphones et courriels de présidents d'association",
            "liste-des-centres-d-orientatio__-.xlsx": "Numéros de téléphone des centres"}
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
# Tout fichier brut doit être enregistré.
assert set(hashes) == {s[0] for s in SOURCES}, set(hashes) ^ {s[0] for s in SOURCES}
# Ressources de data.gov.ma dont l'empreinte a été comparée au fichier local (data/metadata/datagov_resources.csv).
with open(ROOT / "data" / "metadata" / "datagov_resources.csv", encoding="utf-8") as f:
    RESOURCES = {r["sha256"]: r for r in csv.DictReader(f)}
# Registre des droits : ce qui n'a pas été vérifié juridiquement reste marqué comme tel.
YEARS = {"hcp_national": "2024", "hcp_cee": "2023/2024", "hcp_pauvrete": "2014, 2024", "cartesanitaire": "2024", "geoBoundaries": "2017", "essp-2024": "2024", "essp-2025": "2025", "hopitaux-2025": "2025", "chomage_prov": "2017-2025", "txact": "2017-2025", "txemp": "2017-2025", "nombre-des-s": "2022", "entreprises-": "2022", "juillet-2026": "2026", "maisons": "Non indiquée", "reseau-des-maisons": "Non indiquée", "multi": "Non indiquée"}
def levels(s):
    if s[1] == "CNSS":
        return "Région"
    lists = ("essp", "hopitaux", "juillet", "maisons", "multi")
    return "Établissement, regroupé par province" if any(k in s[0] for k in lists) else "Province"
with open(OUT / "data_sources_registry.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["source_id", "dataset_name", "producer", "original_url", "reference_year", "geographic_level", "licence", "commercial_use", "redistribution", "attribution", "verification_status",
                "quality_class", "file", "resource_url", "published_on", "file_matches_portal", "personal_data", "usage", "note"])
    for n, s in enumerate(SOURCES, 1):
        detail = next((d for k, d in DETAILS.items() if k in s[0]), None)
        year = detail[0] if detail else next((y for k, y in YEARS.items() if k in s[0]), "Non indiquée")
        level = detail[1] if detail else levels(s)
        if s[4] == A_CONFIRMER:
            rights = ("À vérifier", "À vérifier", "À vérifier", "À vérifier auprès du producteur")
        else:
            rights = ("Permis sous conditions ODbL", "Permise sous conditions ODbL (partage à l'identique)", "Oui", "Licence relevée, conditions non revues par un juriste")
        res = RESOURCES.get(hashes[s[0]])
        match = "Oui, empreinte identique (vérifié le 2026-11-03)" if res else ("Non vérifié" if s[0].startswith("datagov/") else "Sans objet (hors data.gov.ma)")
        w.writerow([f"S{n:02d}", s[2], s[1], s[3], year, level, s[4], *rights, CLASSES.get(s[0], "A"), s[0], res["resource_url"] if res else s[3],
                    res["resource_created"] if res else "Non relevée", match, PERSONAL.get(s[0].removeprefix("datagov/"), "Non"), s[5], detail[2] if detail else ""])
with open(OUT / "rafah_metadonnees.csv", encoding="utf-8-sig") as f:
    meta = list(csv.DictReader(f))
assert {m["id"] for m in meta} == set(INDICATEURS)
with open(OUT / "provenance_indicateurs.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["indicateur", "libelle", "fichier_source", "variables_origine", "transformation", "borne_basse", "borne_haute", "base_des_bornes"])
    for m in meta:
        w.writerow([m["id"], m["label"], *INDICATEURS[m["id"]], m["L"], m["U"], m["bornes"]])
print(f"{len(SOURCES)} sources et {len(meta)} indicateurs documentés")
