"""Moteur d'ingestion commun aux 12 divisions.

Chaque jeu de données (pipeline/datasets.py) fournit seulement son extraction. Le moteur se charge du reste :
empreinte des fichiers bruts, rapprochement des territoires, contrôles, versionnement des observations, rapport qualité.

Usage : python pipeline/ingest.py [identifiant_de_jeu ...]
Entrées : data/raw/ (non versionné), data/processed/, data/metadata/
Sorties : data/observations/observations.csv, datasets.csv, quality/<jeu>.json
"""
import csv
import hashlib
import json
import math
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Callable

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
RAW, PROCESSED, META = ROOT / "data" / "raw", ROOT / "data" / "processed", ROOT / "data" / "metadata"
OBS = ROOT / "data" / "observations"
COLUMNS = ["indicator_id", "territory_id", "period", "value", "status", "note", "source_id", "dataset_id", "version", "ingested_on", "is_current"]
KEY = ["indicator_id", "territory_id", "period"]
PERCENT_UNITS = {"%"}


@dataclass
class Dataset:
    id: str
    source_id: str
    description: str
    files: list[str]                      # chemins relatifs à data/ ; un fichier absent suspend le jeu sans effacer l'existant
    extract: Callable[["Context"], pd.DataFrame]
    kind: str = "brut"                    # "brut" : fichier du producteur ; "dérivé" : sortie d'un calcul Rafah déjà contrôlé


@dataclass
class Context:
    territories: pd.DataFrame             # index : code HCP ; colonnes nom, region_code, population
    dictionary: dict
    extras: dict = field(default_factory=dict)


def read_csv(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_dictionary():
    """Dictionnaire complet : 18 indicateurs de l'indice (rafah_metadonnees.csv) et indicateurs des divisions."""
    out = {}
    for r in read_csv(PROCESSED / "rafah_metadonnees.csv"):
        out[r["id"]] = dict(indicator_id=r["id"], division=None, nom=r["label"], unite=r["unit"], disponibilite="disponible", indicateur_rafah=r["id"], niveau="Province")
    for r in read_csv(META / "indicator_dictionary.csv"):
        out[r["indicator_id"]] = r
    return out


def context():
    t = pd.read_csv(PROCESSED / "rafah_provinces.csv", index_col="code_hcp")[["nom", "type", "region_code", "region", "population"]]
    return Context(territories=t, dictionary=load_dictionary())


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def match_territories(df, ctx):
    """Accepte un code HCP (territory_id) ou un nom (territory_name), rapproché par la clé commune de build_index."""
    if "territory_name" in df:
        from build_index import key
        idx = {key(n): c for c, n in ctx.territories.nom.items()}
        codes = df.territory_name.map(lambda n: idx.get(key(n)))
        df = df.assign(territory_id=df.get("territory_id", codes).fillna(codes)).drop(columns="territory_name")
    unknown = df[~df.territory_id.isin(ctx.territories.index)]
    assert unknown.empty, f"territoires inconnus : {unknown.territory_id.unique()[:10]}"
    return df.assign(territory_id=df.territory_id.astype(int))


def validate(df, ctx, ds):
    """Erreurs bloquantes (assert) et avertissements (rapport)."""
    statuses = {r["status"]: r["valeur_presente"] == "oui" for r in read_csv(META / "value_status.csv")}
    errors, warnings = [], []
    if missing := sorted(set(df.indicator_id) - set(ctx.dictionary)):
        errors.append(f"indicateurs absents du dictionnaire : {missing}")
    if bad := sorted(set(df.status) - set(statuses)):
        errors.append(f"statuts inconnus : {bad}")
    if df.duplicated(KEY).any():
        errors.append(f"doublons : {df[df.duplicated(KEY)][KEY].head().to_dict('records')}")
    for r in df.itertuples():
        has = r.value is not None and not (isinstance(r.value, float) and math.isnan(r.value))
        if statuses.get(r.status) is not None and has != statuses[r.status]:
            # Une valeur absente n'est jamais remplacée par 0 : elle porte un statut sans valeur.
            errors.append(f"{r.indicator_id} {r.territory_id} {r.period} : statut {r.status} et valeur {r.value}")
        elif has and (not math.isfinite(r.value) or r.value < 0):
            errors.append(f"{r.indicator_id} {r.territory_id} : valeur impossible {r.value}")
        elif has and ctx.dictionary[r.indicator_id]["unite"] in PERCENT_UNITS and r.value > 100:
            errors.append(f"{r.indicator_id} {r.territory_id} : pourcentage {r.value} > 100")
        if r.status == "zero_reel" and has and r.value != 0:
            errors.append(f"{r.indicator_id} {r.territory_id} : zéro réel non nul")
        if r.status in ("estime", "convention", "zero_reel") and not r.note:
            errors.append(f"{r.indicator_id} {r.territory_id} : statut {r.status} sans justification")
    assert not errors, f"[{ds.id}] " + " ; ".join(errors[:12])
    coverage = {}
    expected = len(ctx.territories)
    for (ind, per), g in df.groupby(["indicator_id", "period"]):
        n = int(g.status.map(statuses).sum())
        coverage[f"{ind} {per}"] = round(100 * n / expected, 1)
        if n < expected:
            warnings.append(f"{ind} {per} : {expected - n} territoires sans valeur")
    return coverage, warnings


def save_versioned(df, ds, today):
    """Ajoute les nouvelles observations sans jamais réécrire l'historique : une valeur corrigée crée une version."""
    path = OBS / "observations.csv"
    old = pd.read_csv(path, dtype={"period": str, "note": str}, keep_default_na=False, na_values=[""]) if path.exists() else pd.DataFrame(columns=COLUMNS)
    old["note"] = old.note.fillna("")
    current = old[old.is_current.astype(str) == "True"].set_index(KEY)
    rows, retired, unchanged = [], [], 0
    for r in df.itertuples(index=False):
        k = (r.indicator_id, r.territory_id, str(r.period))
        prev = current.loc[k] if k in current.index else None
        # Une source corrigée est une correction comme une autre : elle crée une version.
        same = prev is not None and prev.status == r.status and prev.note == r.note and prev.source_id == r.source_id and (
            (pd.isna(prev.value) and pd.isna(r.value)) or (pd.notna(prev.value) and pd.notna(r.value) and math.isclose(float(prev.value), r.value, rel_tol=1e-8, abs_tol=1e-9)))
        if same:
            unchanged += 1
            continue
        version = 1 if prev is None else int(prev.version) + 1
        if prev is not None:
            retired.append(k)
        rows.append(dict(indicator_id=r.indicator_id, territory_id=r.territory_id, period=str(r.period), value=r.value, status=r.status, note=r.note,
                         source_id=r.source_id, dataset_id=ds.id, version=version, ingested_on=today, is_current=True))
    if retired:
        mask = old.set_index(KEY).index.isin(retired) & (old.is_current.astype(str) == "True")
        old.loc[mask, "is_current"] = False
    out = pd.concat([old, pd.DataFrame(rows, columns=COLUMNS)], ignore_index=True) if rows else old
    out["is_current"] = out.is_current.astype(str) == "True"
    out = out.sort_values(["indicator_id", "period", "territory_id", "version"])
    OBS.mkdir(parents=True, exist_ok=True)
    out.to_csv(path, index=False, columns=COLUMNS, float_format="%.12g", lineterminator="\n")
    return dict(nouvelles=len(rows) - len(retired), corrigees=len(retired), inchangees=unchanged)


def register(ds, hashes, df, today):
    path = OBS / "datasets.csv"
    rows = [r for r in read_csv(path) if r["dataset_id"] != ds.id] if path.exists() else []
    rows.append(dict(dataset_id=ds.id, source_id=ds.source_id, description=ds.description, nature=ds.kind, fichiers=";".join(ds.files),
                     sha256=";".join(hashes), observations=len(df), indicateurs=";".join(sorted(df.indicator_id.unique())),
                     periodes=";".join(sorted(df.period.astype(str).unique())), ingere_le=today))
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: r["dataset_id"]))


def ingest(ds, ctx, today=None):
    today = today or date.today().isoformat()
    paths = [ROOT / "data" / f for f in ds.files]
    if absent := [p.name for p in paths if not p.exists()]:
        print(f"[{ds.id}] suspendu, fichiers absents : {absent}")
        return None
    hashes = [sha256(p) for p in paths]                       # le brut n'est jamais modifié ; son empreinte date l'observation
    df = ds.extract(ctx)
    df = match_territories(df, ctx)
    df["period"] = df.period.astype(str)
    df["note"] = df.note.fillna("") if "note" in df else ""
    df["value"] = df.value.astype(float)
    if "source_id" not in df:
        df["source_id"] = ds.source_id
    coverage, warnings = validate(df, ctx, ds)
    counts = save_versioned(df, ds, today)
    register(ds, hashes, df, today)
    report = dict(dataset_id=ds.id, source_id=ds.source_id, nature=ds.kind, fichiers=dict(zip(ds.files, hashes)), ingere_le=today,
                  observations=len(df), statuts=df.status.value_counts().to_dict(), couverture_pct=coverage, avertissements=warnings, **counts)
    (OBS / "quality").mkdir(parents=True, exist_ok=True)
    (OBS / "quality" / f"{ds.id}.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[{ds.id}] {len(df)} observations ; nouvelles {counts['nouvelles']}, corrigées {counts['corrigees']}, inchangées {counts['inchangees']} ; {len(warnings)} avertissement(s)")
    return report


def main(ids):
    sys.path.insert(0, str(Path(__file__).parent))
    from datasets import CATALOG
    ctx = context()
    for ds in CATALOG:
        if not ids or ds.id in ids:
            ingest(ds, ctx)


if __name__ == "__main__":
    main(sys.argv[1:])
