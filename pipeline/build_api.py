"""Génère le référentiel territorial et l'API interne en fichiers JSON versionnés (data/api/v1).

Pas de serveur ni de publication : ces fichiers fixent le contrat que les trois espaces pourront lire,
et qu'un service comme FastAPI pourra exposer après validation des licences.
Usage : python build_api.py [racine_du_projet]
"""
import json
import math
import sys
from pathlib import Path

from shapely.geometry import shape
from shapely.validation import explain_validity

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed"
API = ROOT / "data" / "api" / "v1"
VERSION, DATE = "2.0", "2026-11-02"
sys.stdout.reconfigure(encoding="utf-8")
DATA = json.loads((OUT / "rafah.json").read_text(encoding="utf-8"))
GEO = json.loads((OUT / "provinces.geojson").read_text(encoding="utf-8"))
INDS, DIMS, PROV = DATA["indicators"], DATA["dimensions"], DATA["provinces"]
KEYS = ["health", "education", "employment", "housing", "water_environment", "social_inclusion"]
RELIABILITY = {"Élevée": "high", "Moyenne": "medium", "Prudence": "caution"}
GEOM_SOURCE = {"source": "geoBoundaries gbOpen MAR ADM2 (OpenStreetMap)", "licence": "ODbL", "boundary_year": 2017, "crs": "EPSG:4326", "simplified": True}


def norm(x, i):
    return min(100, max(1, 1 + 99 * (x - i["L"] if i["sens"] > 0 else i["U"] - x) / (i["U"] - i["L"])))


def write(rel, obj):
    p = API / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


for p in PROV:
    p["_ind"] = {i["id"]: norm(p["v"][i["id"]], i) for i in INDS}
    p["_dims"] = [sum(p["_ind"][i["id"]] for i in INDS if i["dim"] == k) / 3 for k in range(6)]
    p["_score"] = math.exp(sum(map(math.log, p["_dims"])) / 6)
for n, p in enumerate(sorted(PROV, key=lambda x: -x["_score"]), 1):
    p["_rank"] = n
for r in {p["region"] for p in PROV}:
    for n, p in enumerate(sorted([x for x in PROV if x["region"] == r], key=lambda x: -x["_score"]), 1):
        p["_rrank"] = n


def summary(p):
    return dict(territory_id=str(p["code"]), name=p["nom"], type=p["type"], region=p["region"], population=p["population"], rafah_score=round(p["_score"], 1),
                national_rank=p["_rank"], regional_rank=p["_rrank"], dimensions=dict(zip(KEYS, (round(d, 1) for d in p["_dims"]))),
                reliability=RELIABILITY[p["fiab"]], reliability_reasons=p["fiabRaisons"], values_published_or_calculated=p["couverture"], data_version=VERSION)


# Contrôle des géométries : liées au code, valides, sans recouvrement notable.
shapes = {f["properties"]["code"]: shape(f["geometry"]) for f in GEO["features"]}
assert set(shapes) == {p["code"] for p in PROV} and len(GEO["features"]) == 75
invalid = {c: explain_validity(s) for c, s in shapes.items() if not s.is_valid}
fixed = {c: (s if s.is_valid else s.buffer(0)) for c, s in shapes.items()}
codes = sorted(fixed)
overlaps = []
for a_i, a in enumerate(codes):
    for b in codes[a_i + 1:]:
        if fixed[a].intersects(fixed[b]):
            area = fixed[a].intersection(fixed[b]).area
            share = area / min(fixed[a].area, fixed[b].area)
            if share > .01:
                overlaps.append(dict(a=a, b=b, part_du_plus_petit=round(share, 3)))
names = {p["code"]: p["nom"] for p in PROV}
geocheck = dict(polygones=len(fixed), invalides={names[c]: v for c, v in invalid.items()}, recouvrements_superieurs_1pct=[dict(o, a=names[o["a"]], b=names[o["b"]]) for o in overlaps])
(OUT / "controle_geometries.json").write_text(json.dumps(geocheck, ensure_ascii=False, indent=1), encoding="utf-8")

# Référentiel : la géométrie suit le code HCP, jamais le nom.
features = []
for f in GEO["features"]:
    p = next(x for x in PROV if x["code"] == f["properties"]["code"])
    features.append(dict(type="Feature", properties=dict(territory_id=str(p["code"]), name=p["nom"], type=p["type"], region=p["region"], statistical_year=2024, **GEOM_SOURCE), geometry=f["geometry"]))
collection = dict(type="FeatureCollection", features=features)
(OUT / "referentiel_territoires.geojson").write_text(json.dumps(collection, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

write("territories.json", dict(data_version=VERSION, count=len(PROV), territories=[{k: summary(p)[k] for k in ("territory_id", "name", "type", "region", "population")} for p in PROV]))
write("geojson/morocco.json", collection)
write("dimensions.json", [dict(id=k, name=d, indicators=[i["id"] for i in INDS if i["dim"] == n]) for n, (k, d) in enumerate(zip(KEYS, DIMS))])
write("indicators.json", [dict(id=i["id"], name=i["label"], dimension=KEYS[i["dim"]], direction="positive" if i["sens"] > 0 else "negative", unit=i["unit"], source=i["source"], lower_bound=i["L"], upper_bound=i["U"], bound_basis=i["bornes"], policy_lever=i["lever"]) for i in INDS])
write("metadata.json", dict(api_version="v1", data_version=VERSION, computed_on=DATE, status="internal", official_statistics=False, territories=75, indicators=18, dimensions=6, aggregation="moyenne arithmétique dans les dimensions, moyenne géométrique entre dimensions",
                            data_years=dict(census=2024, health=2024, economic_establishments="2023/2024"), geometry=GEOM_SOURCE, licences_note="Droits de réutilisation du HCP et de la carte sanitaire à confirmer : pas de diffusion publique de cette API avant validation."))
for key, label in [("overall", None), *zip(KEYS, range(6))]:
    get = (lambda p: p["_score"]) if key == "overall" else (lambda p, k=label: p["_dims"][k])
    write(f"rankings/{key}.json", dict(scope="national", dimension=key, data_version=VERSION, ranking=[dict(rank=n, territory_id=str(p["code"]), name=p["nom"], region=p["region"], value=round(get(p), 1)) for n, p in enumerate(sorted(PROV, key=lambda x: -get(x)), 1)]))
for p, f in ((x, next(g for g in features if g["properties"]["territory_id"] == str(x["code"]))) for x in PROV):
    tid = str(p["code"])
    write(f"territories/{tid}/index.json", summary(p))
    write(f"territories/{tid}/geometry.json", f)
    write(f"territories/{tid}/dimensions.json", dict(territory_id=tid, data_version=VERSION, dimensions=dict(zip(KEYS, (round(d, 2) for d in p["_dims"])))))
    write(f"territories/{tid}/indicators.json", dict(territory_id=tid, data_version=VERSION, indicators=[dict(id=i["id"], value=round(p["v"][i["id"]], 3), unit=i["unit"], normalized=round(p["_ind"][i["id"]], 2), status=p["status"][i["id"]], source=i["source"]) for i in INDS]))

# Le contrat public de ces fichiers.
routes = {"/territories": "Liste des 75 territoires", "/territories/{id}": "Fiche synthétique", "/territories/{id}/geometry": "Géométrie GeoJSON", "/territories/{id}/indicators": "18 indicateurs, valeurs, unités, sources et statuts",
          "/territories/{id}/dimensions": "Six scores", "/rankings/{dimension}": "Classement national, overall ou une dimension", "/dimensions": "Catalogue des dimensions", "/indicators": "Catalogue des indicateurs", "/geojson/morocco": "FeatureCollection des 75 géométries", "/metadata": "Version, millésimes et méthode"}
def param(path):
    names_in = [s[1:-1] for s in path.split("/") if s.startswith("{")]
    return [dict(name=n, **{"in": "path"}, required=True, schema=dict(type="string")) for n in names_in]
openapi = dict(openapi="3.1.0", info=dict(title="API interne Rafah", version="1.0.0", description="Contrat interne, non publié. Résultats non officiels. id = code géographique HCP."),
               paths={r: dict(get=dict(summary=s, parameters=param(r), responses={"200": dict(description="Réponse JSON"), "404": dict(description="Territoire inconnu")})) for r, s in routes.items()})
(API / "openapi.json").write_text(json.dumps(openapi, ensure_ascii=False, indent=1), encoding="utf-8")

# Tests de cohérence avec les résultats publiés.
import csv
with open(OUT / "rafah_provinces.csv", encoding="utf-8-sig") as fh:
    pub = {int(r["code_hcp"]): r for r in csv.DictReader(fh)}
assert all(abs(p["_score"] - float(pub[p["code"]]["rafah"])) < .1 for p in PROV)
assert all(p["_rank"] == int(pub[p["code"]]["rang"]) for p in PROV)
assert len(json.loads((API / "rankings/overall.json").read_text(encoding="utf-8"))["ranking"]) == 75
assert len(json.loads((API / "geojson/morocco.json").read_text(encoding="utf-8"))["features"]) == 75
files = sum(1 for x in API.rglob("*") if x.is_file())
print(f"API interne : {files} fichiers, {len(routes)} routes. Géométries : {len(fixed)}, invalides : {len(invalid)}, recouvrements > 1 % : {len(overlaps)}")
print(json.dumps(geocheck, ensure_ascii=False))
