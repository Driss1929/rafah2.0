"""API interne Rafah, en local uniquement. Elle sert les fichiers versionnés de data/api/v1.

Lancement : python -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000
Documentation générée : http://127.0.0.1:8000/docs
"""
import json
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "api" / "v1"
Dimension = Literal["overall", "health", "education", "employment", "housing", "water_environment", "social_inclusion"]

app = FastAPI(title="API Rafah", version="1.0.0", description="Projet indépendant, lecture seule. Résultats non officiels. L'identifiant est le code géographique HCP.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"])


def load(rel):
    path = DATA / rel
    if not path.is_file():
        raise HTTPException(404, "Ressource inconnue")
    return json.loads(path.read_text(encoding="utf-8"))


def territory(tid, rel="index.json"):
    # L'identifiant est un code numérique : cela écarte aussi tout chemin construit par la requête.
    if not tid.isdigit():
        raise HTTPException(404, "Territoire inconnu")
    return load(f"territories/{tid}/{rel}")


@app.get("/v1/metadata")
def metadata():
    return load("metadata.json")


@app.get("/v1/territories")
def territories(region: str | None = None):
    data = load("territories.json")
    if region:
        data["territories"] = [t for t in data["territories"] if t["region"] == region]
        data["count"] = len(data["territories"])
    return data


@app.get("/v1/territories/{tid}")
def one_territory(tid: str):
    return territory(tid)


@app.get("/v1/territories/{tid}/geometry")
def geometry(tid: str):
    return territory(tid, "geometry.json")


@app.get("/v1/territories/{tid}/indicators")
def indicators_of(tid: str):
    return territory(tid, "indicators.json")


@app.get("/v1/territories/{tid}/dimensions")
def dimensions_of(tid: str):
    return territory(tid, "dimensions.json")


@app.get("/v1/rankings")
def rankings(dimension: Dimension = "overall", region: str | None = None):
    data = load(f"rankings/{dimension}.json")
    if region:
        data["ranking"] = [r for r in data["ranking"] if r["region"] == region]
        data["scope"] = "region"
    return data


@app.get("/v1/dimensions")
def dimensions():
    return load("dimensions.json")


@app.get("/v1/indicators")
def indicators():
    return load("indicators.json")


@app.get("/v1/geojson/morocco")
def morocco():
    return load("geojson/morocco.json")


@app.get("/v1/dictionary")
def dictionary(division: str | None = None):
    data = load("dictionary.json")
    return [i for i in data if i.get("division") == division] if division else data


@app.get("/v1/divisions")
def divisions():
    return load("divisions.json")


@app.get("/v1/divisions/{did}")
def division(did: str):
    # Seules les divisions publiées ont un fichier ; le nom est vérifié pour écarter tout chemin.
    if not did.isalpha():
        raise HTTPException(404, "Division inconnue")
    return load(f"divisions/{did}.json")


@app.get("/v1/observations/{indicator}")
def observations(indicator: str, territory: str | None = None, period: str | None = None):
    if not indicator.replace("_", "").isalnum():
        raise HTTPException(404, "Indicateur inconnu")
    data = load(f"observations/{indicator}.json")
    data["observations"] = [o for o in data["observations"] if (not territory or o["territory_id"] == territory) and (not period or o["period"] == period)]
    return data
