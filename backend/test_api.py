"""Tests de l'API interne. Usage : python -m pytest backend/test_api.py"""
import csv
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent))
from main import ROOT, app

client = TestClient(app)
with open(ROOT / "data" / "processed" / "rafah_provinces.csv", encoding="utf-8-sig") as f:
    PUBLISHED = {r["code_hcp"]: r for r in csv.DictReader(f)}


def test_territories():
    data = client.get("/v1/territories").json()
    assert data["count"] == 75 and {t["territory_id"] for t in data["territories"]} == set(PUBLISHED)


def test_scores_match_published_results():
    for tid, row in PUBLISHED.items():
        t = client.get(f"/v1/territories/{tid}").json()
        assert abs(t["rafah_score"] - float(row["rafah"])) < .051 and t["national_rank"] == int(row["rang"]), tid


def test_details():
    assert len(client.get("/v1/territories/2251/indicators").json()["indicators"]) == 18
    assert len(client.get("/v1/territories/2251/dimensions").json()["dimensions"]) == 6
    assert client.get("/v1/territories/2251/geometry").json()["properties"]["territory_id"] == "2251"


def test_status_is_exposed():
    rows = client.get("/v1/territories/12066/indicators").json()["indicators"]
    assert {r["id"]: r["status"] for r in rows}["medecins"] == "imputé"


def test_rankings():
    ranking = client.get("/v1/rankings").json()["ranking"]
    assert len(ranking) == 75 and ranking[0]["name"] == "Rabat"
    assert [r["rank"] for r in ranking] == list(range(1, 76))
    assert len(client.get("/v1/rankings", params={"dimension": "health", "region": "Oriental"}).json()["ranking"]) == 8
    assert client.get("/v1/rankings", params={"dimension": "autre"}).status_code == 422


def test_catalogues_and_geojson():
    assert len(client.get("/v1/dimensions").json()) == 6
    assert len(client.get("/v1/indicators").json()) == 18
    assert len(client.get("/v1/geojson/morocco").json()["features"]) == 75
    assert client.get("/v1/metadata").json()["official_statistics"] is False


def test_unknown_or_unsafe_ids():
    for tid in ("99999", "abc", "..%2F..%2Fmetadata", "2251x"):
        assert client.get(f"/v1/territories/{tid}").status_code == 404, tid
    for path in ("/v1/divisions/eau", "/v1/divisions/..%2Fmetadata", "/v1/observations/inconnu", "/v1/observations/..%2Fmetadata"):
        assert client.get(path).status_code == 404, path


def test_divisions_and_observations():
    divs = client.get("/v1/divisions").json()
    assert len(divs) == 12 and [d["id"] for d in divs if d["statut"] == "pilote"] == ["sante"]
    assert len(client.get("/v1/divisions/sante").json()["territoires"]) == 75
    assert {i["indicator_id"] for i in client.get("/v1/dictionary", params={"division": "sante"}).json()} >= {"H01", "H19", "medecins"}
    obs = client.get("/v1/observations/H03", params={"territory": "12066"}).json()["observations"]
    assert len(obs) == 1 and obs[0]["status"] == "estime"
    assert len(client.get("/v1/observations/H05N", params={"period": "2025"}).json()["observations"]) == 75
