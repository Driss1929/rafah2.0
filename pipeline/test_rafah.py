"""Contrôles de reproductibilité. Usage : python test_rafah.py [racine_du_projet]"""
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed"
DATA = json.loads((OUT / "rafah.json").read_text(encoding="utf-8"))
PROV, INDS = DATA["provinces"], DATA["indicators"]
with open(OUT / "rafah_provinces.csv", encoding="utf-8-sig") as f:
    TABLE = {int(r["code_hcp"]): r for r in csv.DictReader(f)}


def norm(x, i):
    r = (x - i["L"]) / (i["U"] - i["L"]) if i["sens"] > 0 else (i["U"] - x) / (i["U"] - i["L"])
    return min(100, max(1, 1 + 99 * r))


def rafah(v):
    dims = [sum(norm(v[i["id"]], i) for i in INDS if i["dim"] == k) / 3 for k in range(6)]
    return math.exp(sum(math.log(d) for d in dims) / 6)


def test_couverture():
    assert len({p["code"] for p in PROV}) == 75
    assert len(INDS) == 18
    assert all(sum(i["dim"] == k for i in INDS) == 3 for k in range(6))
    geo = json.loads((OUT / "provinces.geojson").read_text(encoding="utf-8"))
    assert {f["properties"]["code"] for f in geo["features"]} == {p["code"] for p in PROV}


def test_totaux_officiels():
    assert sum(p["population"] for p in PROV) == 36490591
    assert round(sum(float(r["n_etab"]) for r in TABLE.values())) == 1130021
    assert sum(p["ctx"]["essp_2025"] for p in PROV) == 3086


def test_pauvrete_note_hcp():
    attendu = {"Figuig": 24.1, "Taounate": 21.1, "Azilal": 17.0, "Chichaoua": 15.1, "Essaouira": 14.8, "Taza": 14.4, "Ouezzane": 13.6}
    by = {p["nom"]: p for p in PROV}
    for n, v in attendu.items():
        assert abs(by[n]["mpi24"] - v) < .051, n


def test_recalcul_independant():
    # Écart toléré : valeurs et bornes sont arrondies dans le fichier publié.
    for p in PROV:
        assert abs(rafah(p["v"]) - float(TABLE[p["code"]]["rafah"])) < .1, p["nom"]


def test_echelle():
    for p in PROV:
        assert 1 <= rafah(p["v"]) <= 100
    i = next(x for x in INDS if x["id"] == "eau")
    assert norm(i["L"] - 10, i) == 1 and norm(i["U"], i) == 100


def test_simulation_isolee():
    # Les bornes sont fixes : modifier une province ne change pas les autres.
    avant = {p["code"]: rafah(p["v"]) for p in PROV}
    v = dict(PROV[0]["v"], eau=min(100, PROV[0]["v"]["eau"] + 30))
    assert rafah(v) >= avant[PROV[0]["code"]]
    assert all(avant[p["code"]] == rafah(p["v"]) for p in PROV[1:])


def test_valeurs_possibles():
    for p in PROV:
        assert p["population"] > 0 and p["region"] and p["type"] in ("Province", "Préfecture"), p["nom"]
        for i in INDS:
            x = p["v"][i["id"]]
            assert isinstance(x, (int, float)) and math.isfinite(x) and x >= 0, (p["nom"], i["id"])
            if i["unit"] == "%":
                assert x <= 100, (p["nom"], i["id"])
    for i in INDS:
        assert i["U"] > i["L"], i["id"]


def test_statuts():
    by = {p["nom"]: p for p in PROV}
    assert by["Aousserd"]["status"]["medecins"] == "imputé" and by["Aousserd"]["fiab"] == "Prudence"
    assert sum(s == "imputé" for p in PROV for s in p["status"].values()) == 1


def test_empreintes():
    # Passe sans contrôle si les données brutes ne sont pas présentes (dépôt public).
    raw = ROOT / "data" / "raw"
    with open(OUT / "sources_empreintes.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            p = raw / r["fichier"]
            if p.exists():
                assert hashlib.sha256(p.read_bytes()).hexdigest() == r["sha256"], r["fichier"]


if __name__ == "__main__":
    tests = [(n, f) for n, f in list(globals().items()) if n.startswith("test_")]
    for n, f in tests:
        f()
        print("OK", n)
    print(f"{len(tests)} contrôles réussis")
