"""Jeux de données connus du moteur d'ingestion. Ajouter un jeu = écrire son extraction et l'inscrire dans CATALOG.

Chaque extraction renvoie un tableau long : indicator_id, territory_id (code HCP) ou territory_name, period, value, status, note.
Les identifiants de source renvoient à data/processed/data_sources_registry.csv.
"""
import json
import math

import pandas as pd

from ingest import PROCESSED, RAW, Dataset

STATUS = {"publié": "observe", "calculé": "calcule", "déduit": "zero_reel", "convention": "convention", "imputé": "estime"}
NOTES = {"zero_reel": "Aucun hôpital dans la délégation selon la liste du ministère.",
         "convention": "« … » publié par le HCP (sans objet, pas d'habitat rural), compté 0 km.",
         "estime": "Ratio non publié pour la délégation ; valeur de sa région."}
CORE_SOURCES = {"cartesanitaire_2024.csv": "S04", "datagov/essp-2024.xlsx": "S06", "hcp_national_242671.xlsx": "S01", "hcp_cee_242672.xlsx": "S02"}
HEALTH_CATS = ["CSU-1", "CSU-2", "CSR-1", "CSR-2", "DR"]


def core_index(ctx):
    """Les 18 indicateurs de l'indice, tels que calculés et contrôlés par build_index.py."""
    data = json.loads((PROCESSED / "rafah.json").read_text(encoding="utf-8"))
    period = {"etablissements": "2023/2024"}
    source = {r["indicateur"]: CORE_SOURCES[r["fichier_source"]] for r in pd.read_csv(PROCESSED / "provenance_indicateurs.csv").to_dict("records")}
    rows = [dict(indicator_id=i, territory_id=p["code"], period=period.get(i, "2024"), value=v, status=STATUS[p["status"][i]], note=NOTES.get(STATUS[p["status"][i]], ""), source_id=source[i])
            for p in data["provinces"] for i, v in p["v"].items()]
    return pd.DataFrame(rows)


def _counts(ctx, file, header, cats, count_id, rate_id, per, period):
    from build_index import latin_list_counts
    n = latin_list_counts(ctx.territories, file, header, cats)
    pop = ctx.territories.population
    rows = []
    for code, v in n.items():
        # Zéro dans une liste exhaustive du ministère : absence réelle d'établissement, pas une donnée manquante.
        status, note = ("zero_reel", "Aucun établissement de la catégorie dans la liste du ministère.") if v == 0 else ("calcule", "")
        rows.append(dict(indicator_id=count_id, territory_id=code, period=period, value=float(v), status=status, note=note))
        rows.append(dict(indicator_id=rate_id, territory_id=code, period=period, value=v / pop[code] * per, status=status, note=note))
    return pd.DataFrame(rows)


def hospitals(year):
    return lambda ctx: _counts(ctx, f"hopitaux-{year}.xlsx", 0, None, "H01N", "H01", 1e5, str(year))


def primary_care(year):
    header = {2024: 1, 2025: 2}[year]
    def extract(ctx):
        df = _counts(ctx, f"essp-{year}.xlsx", header, HEALTH_CATS, "H05N", "H05", 1e4, str(year))
        if year == 2025:
            area = ctx.extras.get("area_km2") or areas()
            n = df[df.indicator_id == "H05N"].set_index("territory_id").value
            dens = [dict(indicator_id="H06", territory_id=c, period="2025", value=n[c] / area[c] * 1e3, status="zero_reel" if n[c] == 0 else "calcule",
                         note="Aucun établissement dans la liste du ministère." if n[c] == 0 else "") for c in n.index]
            df = pd.concat([df, pd.DataFrame(dens)])
        return df
    return extract


def health_map(ctx):
    """Carte sanitaire 2024 : mêmes règles que build_index.health (Casablanca regroupée, Aousserd estimée)."""
    from build_index import health
    d = ctx.territories.copy()
    d = health(d)
    rows = []
    for code, r in d.iterrows():
        est = bool(r._imput_medecins)
        rows.append(dict(indicator_id="H03", territory_id=code, period="2024", value=r.medecins, status="estime" if est else "calcule", note=NOTES["estime"] if est else ""))
        zero = r.lits == 0
        rows.append(dict(indicator_id="H02", territory_id=code, period="2024", value=r.lits / 10, status="zero_reel" if zero else "calcule", note=NOTES["zero_reel"] if zero else ""))
    return pd.DataFrame(rows)


def disability(ctx):
    p = pd.read_excel(RAW / "hcp_national_242671.xlsx", sheet_name="Population", header=None)
    assert "handicap" in str(p.iloc[:6, 30].tolist()), "colonne du handicap déplacée"
    code = pd.to_numeric(p[0], errors="coerce")
    p = p[code.isin(ctx.territories.index)]
    return pd.DataFrame(dict(indicator_id="H19", territory_id=code[p.index].astype(int), period="2024", value=pd.to_numeric(p[30]), status="observe", note=""))


def areas():
    """Superficie en km² sur la sphère authalique (écart de l'ordre de 0,5 % avec l'ellipsoïde)."""
    geo = json.loads((PROCESSED / "referentiel_territoires.geojson").read_text(encoding="utf-8"))
    r = 6371007.2
    def ring(c):
        s = sum(math.radians(c[i + 1][0] - c[i][0]) * (2 + math.sin(math.radians(c[i][1])) + math.sin(math.radians(c[i + 1][1]))) for i in range(len(c) - 1))
        return abs(s) * r * r / 2
    out = {}
    for f in geo["features"]:
        g = f["geometry"]
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        out[int(f["properties"]["territory_id"])] = sum(ring(p[0]) - sum(ring(h) for h in p[1:]) for p in polys) / 1e6
    return out


CATALOG = [
    Dataset("RAFAH_INDICE_2024", "S01", "18 indicateurs de l'indice Rafah, sortie contrôlée de build_index.py", ["processed/rafah.json"], core_index, kind="dérivé"),
    Dataset("S04_CARTE_SANITAIRE_2024", "S04", "Carte sanitaire 2024 : médecins et lits", ["raw/cartesanitaire_2024.csv"], health_map),
    Dataset("S08_HOPITAUX_2024", "S08", "Liste des hôpitaux 2024", ["raw/datagov/hopitaux-2024.xlsx"], hospitals(2024)),
    Dataset("S08_HOPITAUX_2025", "S08", "Liste des hôpitaux 2025", ["raw/datagov/hopitaux-2025.xlsx"], hospitals(2025)),
    Dataset("S06_ESSP_2024", "S06", "Établissements de soins primaires 2024", ["raw/datagov/essp-2024.xlsx"], primary_care(2024)),
    Dataset("S07_ESSP_2025", "S07", "Établissements de soins primaires 2025 et densité au km²", ["raw/datagov/essp-2025.xlsx", "processed/referentiel_territoires.geojson"], primary_care(2025)),
    Dataset("S01_HANDICAP_2024", "S01", "RGPH 2024 : prévalence du handicap", ["raw/hcp_national_242671.xlsx"], disability),
]
