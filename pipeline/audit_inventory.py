"""Inventaires de l'audit M01 : fonctionnalités et jeux de données.

Usage : python pipeline/audit_inventory.py  ->  docs/audit/feature_inventory.xlsx, dataset_inventory.xlsx
Les comptes de lignes et de cellules vides ne sont calculés que si data/raw/ est présent (il n'est pas dans le dépôt).
"""
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
RAW, PROCESSED, OBS, OUT = ROOT / "data" / "raw", ROOT / "data" / "processed", ROOT / "data" / "observations", ROOT / "docs" / "audit"

# Fonctionnalité, emplacement, état (Fonctionne / Partiel / Absent), action, division ou socle, preuve.
FEATURES = [
    ("Accueil et carte statique des scores", "site/pages/index.html", "Fonctionne", "Garder", "Socle", "test_site.py"),
    ("Carte interactive Leaflet, fiches, simulateur, pondérations, comparaison de 3 territoires", "site/explorer.template.html", "Fonctionne", "Garder", "Indice Rafah", "test_site.py, vérification manuelle"),
    ("Carte MapLibre (WMS GeoServer ou GeoJSON de secours)", "site/pages/carte-maplibre.html", "Fonctionne", "Garder ; ajouter le choix d'indicateur et de division", "Socle SIG", "vérification manuelle"),
    ("Classement filtrable, export CSV, comparaison des régions", "site/pages/analyses.html", "Fonctionne", "Garder", "Indice Rafah", "test_site.py"),
    ("Rapports Intelligence et heatmap", "site/pages/intelligence.html", "Fonctionne", "Garder ; relier aux divisions", "Indice Rafah", "test_site.py"),
    ("Maquette Rafah Pro", "site/pages/pro.html", "Partiel", "Garder comme maquette, signalée comme telle", "Produit", "page marquée « maquette »"),
    ("Pages méthode, données, publications, à propos", "site/pages/", "Fonctionne", "Garder", "Socle", "test_site.py"),
    ("Hub des 12 divisions", "site/pages/divisions.html", "Fonctionne", "Garder", "Socle", "test_observatoire.py"),
    ("Division Santé (catalogue, carte, profil, comparaison, évolution, inégalités, signaux, sources)", "site/pages/sante.html, site/division.js", "Fonctionne", "Garder ; servir de modèle", "Santé", "test_observatoire.py"),
    ("Divisions Éducation à Résilience", "data/metadata/divisions.csv", "Absent", "Développer (M05 à M09)", "11 divisions", "état « prévu »"),
    ("Profils territoriaux multi-divisions", "", "Partiel", "Développer (M10) : aujourd'hui fiche indice + profil Santé séparés", "Socle", ""),
    ("Explorateur universel d'indicateurs", "", "Absent", "Développer (M10)", "Socle", ""),
    ("Recherche nationale", "", "Partiel", "Recherche par nom de territoire seulement", "Socle", ""),
    ("Régions et communes (référentiel, carte)", "", "Absent", "Développer (M02)", "Socle géographique", "75 provinces seulement"),
    ("Noms arabes des territoires", "", "Absent", "Développer (M02)", "Socle géographique", ""),
    ("API interne FastAPI en lecture seule", "backend/main.py", "Fonctionne", "Garder ; ajouter routes géographiques (M02)", "Socle", "backend/test_api.py (8 tests)"),
    ("Routes divisions, dictionnaire, observations", "backend/main.py", "Fonctionne", "Garder", "Socle", "test_divisions_and_observations"),
    ("Base PostGIS locale (territoires, scores, observatoire)", "infra/", "Fonctionne", "Garder ; passer aux schémas logiques (M03)", "Socle", "infra/check_postgis.sql, chargement local"),
    ("GeoServer local (WMS, WFS de territoires_scores)", "infra/setup_geoserver.ps1", "Fonctionne", "Garder ; publier aussi observations_courantes", "Socle SIG", "WFS 75 entités"),
    ("Déploiement serveur (Docker, Caddy)", "deploy/", "Partiel", "Non testé sur un vrai serveur ; image PostGIS amd64 seulement", "Déploiement", "deploy/smoke_test.sh"),
    ("Moteur d'ingestion et de validation", "pipeline/ingest.py, pipeline/datasets.py", "Partiel", "Ajouter mise en attente, publication et interface d'import (M04)", "Socle", "test_observatoire.py"),
    ("Versionnement des observations", "pipeline/ingest.py", "Fonctionne", "Ajouter le motif de correction et la version de méthode", "Socle", "test_versionnement_et_refus"),
    ("Registre des sources", "data/processed/data_sources_registry.csv", "Partiel", "Licences et dates de publication à confirmer", "Socle", ""),
    ("Authentification, rôles, administration", "", "Absent", "Développer (M15) ; inutile tant que tout est public en lecture", "Socle", ""),
    ("Journalisation et suivi d'erreurs", "", "Absent", "Développer avant toute mise en ligne de l'API", "Déploiement", ""),
    ("Observatoire historique", "", "Partiel", "Séries 2017-2025 du chômage, 2014/2024 pauvreté, 2024/2025 établissements ; pas de module dédié (M11)", "Socle", ""),
    ("Assistant IA", "", "Absent", "Développer (M12)", "Intelligence", ""),
    ("Alertes", "", "Absent", "Développer (M13)", "Intelligence", ""),
    ("Simulation de politiques", "site/explorer.template.html", "Partiel", "Simulateur de l'indice seulement ; scénarios d'investissement absents (M14)", "Intelligence", ""),
]


def raw_stats(path):
    if not path.exists():
        return None, None, None
    if path.suffix == ".csv":
        sheets = {"csv": pd.read_csv(path, header=None)}
    elif path.suffix in (".xlsx", ".xls"):
        sheets = pd.read_excel(path, sheet_name=None, header=None)
    else:
        return None, None, None
    rows = sum(len(s) for s in sheets.values())
    cells = sum(s.size for s in sheets.values())
    empty = sum(int(s.isna().sum().sum()) for s in sheets.values())
    return len(sheets), rows, round(100 * empty / cells, 1) if cells else None


def datasets():
    prov = pd.read_csv(PROCESSED / "provenance_sources.csv")
    ingested = pd.read_csv(OBS / "datasets.csv")
    used = {}
    for r in ingested.itertuples():
        for f in r.fichiers.split(";"):
            used.setdefault(f.removeprefix("raw/"), []).append(r.dataset_id)
    rows = []
    for r in prov.itertuples():
        sheets, n, empty = raw_stats(RAW / r.fichier)
        rows.append(dict(fichier=r.fichier, producteur=r.producteur, titre=r.titre, url=r.page_source, extrait_le=r.date_extraction, licence=r.licence,
                         format=Path(r.fichier).suffix.lstrip(".") or "inconnu", feuilles=sheets, lignes_brutes=n, cellules_vides_pct=empty,
                         usage_indice=r.usage, jeux_ingeres=", ".join(used.get(r.fichier, [])) or "aucun", sha256=r.sha256,
                         date_publication="non relevée", niveau_geographique="voir data_sources_registry.csv"))
    # Fichiers téléchargés mais absents du registre de provenance : à enregistrer avant tout usage public.
    known = set(prov.fichier)
    for p in sorted(RAW.rglob("*")) if RAW.exists() else []:
        rel = p.relative_to(RAW).as_posix()
        if p.is_file() and rel not in known:
            sheets, n, empty = raw_stats(p)
            rows.append(dict(fichier=rel, producteur="non enregistré", titre="", url="", extrait_le="", licence="à relever", format=p.suffix.lstrip(".") or "inconnu",
                             feuilles=sheets, lignes_brutes=n, cellules_vides_pct=empty, usage_indice="aucun", jeux_ingeres=", ".join(used.get(rel, [])) or "aucun",
                             sha256="", date_publication="non relevée", niveau_geographique=""))
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    f = pd.DataFrame(FEATURES, columns=["fonctionnalite", "emplacement", "etat", "action", "division", "preuve"])
    with pd.ExcelWriter(OUT / "feature_inventory.xlsx") as w:
        f.to_excel(w, sheet_name="Fonctionnalites", index=False)
        pd.read_csv(ROOT / "data" / "metadata" / "divisions.csv").to_excel(w, sheet_name="Divisions", index=False)
    d = datasets()
    with pd.ExcelWriter(OUT / "dataset_inventory.xlsx") as w:
        d.to_excel(w, sheet_name="Fichiers", index=False)
        pd.read_csv(PROCESSED / "data_sources_registry.csv").to_excel(w, sheet_name="Registre", index=False)
        pd.read_csv(OBS / "datasets.csv").to_excel(w, sheet_name="Jeux ingeres", index=False)
    print(f"{len(f)} fonctionnalités ({f.etat.value_counts().to_dict()}) ; {len(d)} fichiers, {int(d.lignes_brutes.notna().sum())} lus")


if __name__ == "__main__":
    main()
