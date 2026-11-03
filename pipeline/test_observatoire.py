"""Contrôles du socle commun et de la division Santé. Usage : python pipeline/test_observatoire.py (ou pytest)"""
import csv
import json
import math
import shutil
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import ingest
from ingest import META, OBS, PROCESSED, ROOT, Dataset, load_dictionary

DICT = load_dictionary()
TERR = set(pd.read_csv(PROCESSED / "rafah_provinces.csv").code_hcp)
STATUS = {r["status"]: r["valeur_presente"] == "oui" for r in csv.DictReader(open(META / "value_status.csv", encoding="utf-8"))}
ALL = pd.read_csv(OBS / "observations.csv", dtype={"period": str}, keep_default_na=False, na_values=[""])
CUR = ALL[ALL.is_current.astype(str) == "True"]
DATA = json.loads((PROCESSED / "rafah.json").read_text(encoding="utf-8"))
SANTE = json.loads((ROOT / "data" / "api" / "v1" / "divisions" / "sante.json").read_text(encoding="utf-8"))
val = lambda ind, per: CUR[(CUR.indicator_id == ind) & (CUR.period == per)].set_index("territory_id").value


def test_integrite_des_observations():
    assert set(CUR.indicator_id) <= set(DICT) and set(CUR.territory_id) <= TERR
    assert set(CUR.status) <= set(STATUS)
    assert not CUR.duplicated(["indicator_id", "territory_id", "period"]).any()
    for r in CUR.itertuples():
        assert pd.notna(r.value) == STATUS[r.status], (r.indicator_id, r.territory_id)


def test_pas_de_zero_silencieux():
    # Dans les divisions, un zéro est toujours justifié par la source.
    zeros = CUR[(CUR.value == 0) & CUR.indicator_id.str.match(r"^[A-Z]")]
    assert (zeros.status == "zero_reel").all() and (zeros.note != "").all()


def test_indice_inchange():
    for p in DATA["provinces"]:
        for i, v in p["v"].items():
            per = "2023/2024" if i == "etablissements" else "2024"
            assert math.isclose(val(i, per)[p["code"]], v, rel_tol=1e-9, abs_tol=1e-9), (p["nom"], i)


def test_sante_coherente_avec_indice():
    # rafah.json arrondit à 3 décimales ; la division repart des fichiers bruts.
    for p in DATA["provinces"]:
        c = p["code"]
        assert abs(val("H03", "2024")[c] - p["v"]["medecins"]) <= 5e-4, p["nom"]
        assert abs(val("H02", "2024")[c] * 10 - p["v"]["lits"]) <= 5e-4, p["nom"]
        assert abs(val("H05", "2024")[c] - p["v"]["essp"]) <= 5e-4, p["nom"]
        assert val("H05N", "2025")[c] == p["ctx"]["essp_2025"] and val("H01N", "2025")[c] == p["ctx"]["hopitaux"]


def test_totaux_des_listes():
    assert val("H05N", "2025").sum() == 3086 and val("H05N", "2024").sum() == 3065
    assert val("H01N", "2025").sum() == 184 and val("H01N", "2024").sum() == 177


def test_division_sante():
    assert len(SANTE["territoires"]) == 75
    for i in SANTE["indicateurs"]:
        if i["disponibilite"] == "disponible" and i["niveau"] == "Province":
            assert i["couverture_pct"] == 100.0, i["indicator_id"]
        if i["disponibilite"] != "disponible":
            assert i["indicator_id"] not in set(CUR.indicator_id), i["indicator_id"]
    assert all(0 < g["gini"] < 1 for g in SANTE["inegalites"])
    assert all(f["signaux"] for f in SANTE["signaux"])


def test_versionnement_et_refus():
    tmp = Path(tempfile.mkdtemp())
    old = ingest.OBS
    ingest.OBS = tmp
    try:
        ctx = ingest.context()
        rows = lambda v, s="calcule", note="": lambda c: pd.DataFrame([dict(indicator_id="H19", territory_id=4421, period="2024", value=v, status=s, note=note)])
        ds = lambda f: Dataset("TEST", "S01", "essai", ["processed/rafah.json"], f)
        ingest.ingest(ds(rows(1.0)), ctx, "2026-01-01")
        ingest.ingest(ds(rows(1.0)), ctx, "2026-01-02")
        ingest.ingest(ds(rows(2.0)), ctx, "2026-01-03")
        o = pd.read_csv(tmp / "observations.csv")
        assert len(o) == 2 and list(o.version) == [1, 2] and list(o.is_current) == [False, True] and list(o.value) == [1.0, 2.0]
        for bad in [rows(0.0, "manquant"), rows(None, "calcule"), rows(0.0, "zero_reel"), rows(120.0), rows(-1.0)]:
            try:
                ingest.ingest(ds(bad), ctx, "2026-01-04")
            except AssertionError:
                continue
            raise AssertionError("valeur invalide acceptée")
    finally:
        ingest.OBS = old
        shutil.rmtree(tmp)


def test_sql():
    s = (ROOT / "infra" / "observatoire.sql").read_text(encoding="utf-8")
    for t in ["divisions", "data_sources", "value_statuses", "indicator_catalogue", "datasets", "indicator_observations"]:
        assert f"CREATE TABLE {t} " in s, t
    assert s.count("INSERT INTO indicator_observations") == len(ALL)


if __name__ == "__main__":
    tests = [(n, f) for n, f in list(globals().items()) if n.startswith("test_")]
    for n, f in tests:
        f()
        print("OK", n)
    print(f"{len(tests)} contrôles réussis")
