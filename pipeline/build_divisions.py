"""Publie les divisions à partir des observations versionnées : dictionnaire, couverture, analyses, SQL PostGIS.

Usage : python pipeline/build_divisions.py   (après pipeline/ingest.py)
Sorties : data/api/v1/dictionary.json, divisions.json, divisions/<id>.json, observations/<indicateur>.json, infra/observatoire.sql
Rien ici ne modifie l'indice Rafah : les divisions sont des observatoires thématiques, pas des dimensions supplémentaires.
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from ingest import META, OBS, PROCESSED, ROOT, load_dictionary, read_csv

API = ROOT / "data" / "api" / "v1"
TERR = pd.read_csv(PROCESSED / "rafah_provinces.csv", index_col="code_hcp")
STATUSES = {r["status"]: r for r in read_csv(META / "value_status.csv")}


def write(rel, obj):
    p = API / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def observations():
    o = pd.read_csv(OBS / "observations.csv", dtype={"period": str}, keep_default_na=False, na_values=[""])
    o["note"] = o.note.fillna("")
    return o[o.is_current.astype(str) == "True"]


def gini(values, weights):
    """Gini pondéré : 0 si chaque habitant dispose de la même dotation, proche de 1 si tout est concentré."""
    x, w = values.to_numpy(float), weights.to_numpy(float)
    mu = (x * w).sum() / w.sum()
    return float((w[:, None] * w[None, :] * abs(x[:, None] - x[None, :])).sum() / (2 * w.sum() ** 2 * mu))


def coverage(obs, dictionary):
    out = {}
    for ind, g in obs.groupby("indicator_id"):
        latest = max(g.period)
        cur = g[g.period == latest]
        valid = cur.status.map(lambda s: STATUSES[s]["valeur_presente"] == "oui").sum()
        out[ind] = dict(periodes=sorted(g.period.unique()), derniere_periode=latest, couverture_pct=round(100 * valid / len(TERR), 1),
                        statuts=cur.status.value_counts().to_dict())
    return out


def health(obs, dictionary, cov, registry):
    piv = lambda ind, per: obs[(obs.indicator_id == ind) & (obs.period == per)].set_index("territory_id").value
    pop = TERR.population
    latest = {"H01": "2025", "H02": "2024", "H03": "2024", "H05": "2025"}
    ineq = []
    for ind, per in latest.items():
        v = piv(ind, per)
        ineq.append(dict(indicator_id=ind, nom=dictionary[ind]["nom"], periode=per, gini=round(gini(v, pop[v.index]), 3),
                         min=dict(territoire=TERR.nom[v.idxmin()], valeur=round(v.min(), 2)), max=dict(territoire=TERR.nom[v.idxmax()], valeur=round(v.max(), 2)),
                         rapport_p90_p10=round(v.quantile(.9) / v.quantile(.1), 1) if v.quantile(.1) > 0 else None))

    # Territoires à examiner : signaux descriptifs, jamais un jugement sur la qualité des soins.
    med, lits = piv("H03", "2024"), piv("H02", "2024")
    low_med, low_lits = med <= med.quantile(.2), lits <= lits.quantile(.2)
    hop = piv("H01N", "2025")
    flags = []
    for c in TERR.index:
        reasons = []
        if low_med[c]:
            reasons.append(f"médecins dans le quintile le plus bas ({med[c]:.1f} pour 10 000)")
        if low_lits[c]:
            reasons.append(f"lits dans le quintile le plus bas ({lits[c]:.2f} pour 1 000)")
        if hop[c] == 0:
            reasons.append("aucun établissement hospitalier public dans la liste 2025")
        if reasons:
            flags.append(dict(territory_id=str(c), nom=TERR.nom[c], region=TERR.region[c], population=int(pop[c]), signaux=reasons, nombre=len(reasons)))
    flags.sort(key=lambda f: (-f["nombre"], f["nom"]))

    hist = []
    for n_id in ["H01N", "H05N"]:
        a, b = piv(n_id, "2024"), piv(n_id, "2025")
        d = (b - a)
        hist.append(dict(indicator_id=n_id, nom=dictionary[n_id]["nom"], total={"2024": int(a.sum()), "2025": int(b.sum())},
                         hausses=int((d > 0).sum()), baisses=int((d < 0).sum()), stables=int((d == 0).sum()),
                         plus_fortes_variations=[dict(territoire=TERR.nom[c], **{"2024": int(a[c]), "2025": int(b[c])}) for c in d.abs().sort_values(ascending=False).index[:8] if d[c] != 0]))

    table_ids = [("H01", "2025"), ("H02", "2024"), ("H03", "2024"), ("H05", "2025"), ("H06", "2025"), ("H19", "2024"), ("H01N", "2025"), ("H05N", "2025")]
    rows = []
    for c in TERR.index:
        vals, st = {}, {}
        for ind, per in table_ids:
            r = obs[(obs.indicator_id == ind) & (obs.period == per) & (obs.territory_id == c)].iloc[0]
            vals[ind] = None if pd.isna(r.value) else round(float(r.value), 3)
            if r.status not in ("observe", "calcule"):
                st[ind] = dict(statut=r.status, note=r.note)
        rows.append(dict(territory_id=str(c), nom=TERR.nom[c], region=TERR.region[c], population=int(pop[c]), valeurs=vals, statuts=st))

    division_inds = [r for r in dictionary.values() if r.get("division") == "sante" and r.get("indicateur_rafah") != r["indicator_id"]]
    used = sorted({s for r in division_inds for s in r.get("sources", "").split(";") if s})
    return dict(
        id="sante", nom="Rafah Santé", objectif="Mesurer la disponibilité, la répartition et l'accessibilité des soins dans les 75 provinces et préfectures.",
        avertissement="Observatoire descriptif. Les signaux désignent des territoires à examiner ; ils ne jugent ni la qualité des soins ni la gestion locale.",
        indicateurs=[dict(**{k: r[k] for k in ("indicator_id", "sous_domaine", "nom", "unite", "formule", "niveau", "disponibilite", "note", "indicateur_rafah", "sources")}, **cov.get(r["indicator_id"], {}))
                     for r in division_inds],
        colonnes=[dict(indicator_id=i, periode=p, nom=dictionary[i]["nom"], unite=dictionary[i]["unite"]) for i, p in table_ids],
        territoires=rows, inegalites=ineq, evolution=hist, signaux=flags,
        sources=[{k: s[k] for k in ("source_id", "dataset_name", "producer", "original_url", "reference_year", "licence", "quality_class", "published_on")} for s in registry if s["source_id"] in used],
        jeux=[r for r in read_csv(OBS / "datasets.csv") if r["dataset_id"].startswith(("S04", "S06", "S07", "S08", "S01_HANDICAP"))],
    )


def q(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "NULL"
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v) if isinstance(v, (int, float)) else "'" + str(v).replace("'", "''") + "'"


def sql(all_obs, dictionary, divisions, registry):
    """Schéma central de l'observatoire, chargé après infra/rafah_postgis.sql (qui crée territories)."""
    out = ["""-- Généré par pipeline/build_divisions.py. Observatoire Rafah : données non officielles.
BEGIN;
DROP VIEW IF EXISTS observations_courantes;
DROP TABLE IF EXISTS indicator_observations, datasets, indicator_catalogue, divisions, data_sources, value_statuses CASCADE;
CREATE TABLE divisions (id text PRIMARY KEY, numero integer NOT NULL UNIQUE, name text NOT NULL, objective text NOT NULL, stage integer NOT NULL, status text NOT NULL);
CREATE TABLE data_sources (id text PRIMARY KEY, dataset_name text NOT NULL, producer text NOT NULL, url text NOT NULL, reference_year text, geographic_level text, licence text, verification_status text,
  quality_class char(1) NOT NULL CHECK (quality_class IN ('A','B','C','D','E')), resource_url text, published_on text, file_matches_portal text, personal_data text NOT NULL, usage text);
CREATE TABLE value_statuses (status text PRIMARY KEY, label text NOT NULL, has_value boolean NOT NULL, definition text NOT NULL);
CREATE TABLE indicator_catalogue (id text PRIMARY KEY, division_id text REFERENCES divisions, subdomain text, name text NOT NULL, unit text NOT NULL, formula text, formula_version integer,
  geographic_level text, availability text NOT NULL, core_indicator text, sources text, note text);
CREATE TABLE datasets (id text PRIMARY KEY, source_id text NOT NULL REFERENCES data_sources, description text NOT NULL, nature text NOT NULL, files text NOT NULL, sha256 text NOT NULL, ingested_on date NOT NULL);
-- Historique complet : une correction ajoute une version et retire la précédente (is_current), sans l'effacer.
CREATE TABLE indicator_observations (indicator_id text NOT NULL REFERENCES indicator_catalogue, territory_id text NOT NULL REFERENCES territories, period text NOT NULL,
  value double precision, status text NOT NULL REFERENCES value_statuses, note text NOT NULL DEFAULT '', source_id text NOT NULL REFERENCES data_sources, dataset_id text NOT NULL REFERENCES datasets,
  version integer NOT NULL CHECK (version >= 1), ingested_on date NOT NULL, is_current boolean NOT NULL, PRIMARY KEY (indicator_id, territory_id, period, version),
  CHECK (value IS NULL OR value >= 0));
CREATE UNIQUE INDEX observations_une_courante ON indicator_observations (indicator_id, territory_id, period) WHERE is_current;
"""]
    out += [f"INSERT INTO divisions VALUES ({q(d['division_id'])}, {d['numero']}, {q(d['nom'])}, {q(d['objectif'])}, {d['etape']}, {q(d['statut'])});" for d in divisions]
    out += [f"INSERT INTO data_sources VALUES ({q(s['source_id'])}, {q(s['dataset_name'])}, {q(s['producer'])}, {q(s['original_url'])}, {q(s['reference_year'])}, {q(s['geographic_level'])}, {q(s['licence'])}, {q(s['verification_status'])}, "
            f"{q(s['quality_class'])}, {q(s['resource_url'])}, {q(s['published_on'])}, {q(s['file_matches_portal'])}, {q(s['personal_data'])}, {q(s['usage'])});" for s in registry]
    out += [f"INSERT INTO value_statuses VALUES ({q(k)}, {q(s['libelle'])}, {q(s['valeur_presente'] == 'oui')}, {q(s['definition'])});" for k, s in STATUSES.items()]
    for r in dictionary.values():
        ver = r.get("version_formule")
        out.append(f"INSERT INTO indicator_catalogue VALUES ({q(r['indicator_id'])}, {q(r.get('division'))}, {q(r.get('sous_domaine'))}, {q(r['nom'])}, {q(r['unite'])}, {q(r.get('formule'))}, "
                   f"{int(ver) if ver else 'NULL'}, {q(r.get('niveau'))}, {q(r['disponibilite'])}, {q(r.get('indicateur_rafah') or None)}, {q(r.get('sources'))}, {q(r.get('note'))});")
    out += [f"INSERT INTO datasets VALUES ({q(d['dataset_id'])}, {q(d['source_id'])}, {q(d['description'])}, {q(d['nature'])}, {q(d['fichiers'])}, {q(d['sha256'])}, {q(d['ingere_le'])});" for d in read_csv(OBS / "datasets.csv")]
    # Les 18 indicateurs de l'indice sont rattachés à leur division thématique.
    for d in divisions:
        for i in filter(None, d["indicateurs_rafah_existants"].split(";")):
            out.append(f"UPDATE indicator_catalogue SET division_id = {q(d['division_id'])} WHERE id = {q(i)} AND division_id IS NULL;")
    for r in all_obs.itertuples():
        out.append(f"INSERT INTO indicator_observations VALUES ({q(r.indicator_id)}, {q(str(r.territory_id))}, {q(r.period)}, {q(r.value)}, {q(r.status)}, {q(r.note)}, {q(r.source_id)}, {q(r.dataset_id)}, "
                   f"{int(r.version)}, {q(r.ingested_on)}, {q(str(r.is_current) == 'True')});")
    out.append("""CREATE VIEW observations_courantes AS
SELECT o.*, c.name AS indicator_name, c.unit, c.division_id, t.name AS territory_name, t.region, t.geom
FROM indicator_observations o JOIN indicator_catalogue c ON c.id = o.indicator_id JOIN territories t ON t.id = o.territory_id WHERE o.is_current;
COMMIT;""")
    (ROOT / "infra" / "observatoire.sql").write_text("\n".join(out) + "\n", encoding="utf-8")
    return len(out)


def main():
    dictionary = load_dictionary()
    divisions = read_csv(META / "divisions.csv")
    registry = read_csv(PROCESSED / "data_sources_registry.csv")
    core_div = {i: d["division_id"] for d in divisions for i in filter(None, d["indicateurs_rafah_existants"].split(";"))}
    for i, r in dictionary.items():
        if r.get("division") is None:
            r["division"] = core_div.get(i)
    all_obs = pd.read_csv(OBS / "observations.csv", dtype={"period": str}, keep_default_na=False, na_values=[""])
    all_obs["note"] = all_obs.note.fillna("")
    obs = observations()
    cov = coverage(obs, dictionary)

    write("dictionary.json", [dict(r, **cov.get(i, dict(couverture_pct=0.0))) for i, r in dictionary.items()])
    summary = []
    for d in divisions:
        inds = [r for r in dictionary.values() if r.get("division") == d["division_id"]]
        catalogue = [r for r in inds if r.get("indicateur_rafah") != r["indicator_id"]]   # indicateurs propres à la division
        summary.append(dict(id=d["division_id"], numero=int(d["numero"]), nom=d["nom"], objectif=d["objectif"], etape=int(d["etape"]), statut=d["statut"],
                            indicateurs_rafah=[r["indicator_id"] for r in inds if r.get("indicateur_rafah") == r["indicator_id"]],
                            catalogue=len(catalogue), disponibles=sum(r["disponibilite"] == "disponible" for r in catalogue)))
    write("divisions.json", summary)
    payload = health(obs, dictionary, cov, registry)
    write("divisions/sante.json", payload)
    for ind, g in obs.groupby("indicator_id"):
        write(f"observations/{ind}.json", dict(indicator_id=ind, nom=dictionary[ind]["nom"], unite=dictionary[ind]["unite"],
                                               observations=[dict(territory_id=str(r.territory_id), period=r.period, value=None if pd.isna(r.value) else r.value, status=r.status, note=r.note,
                                                                  source_id=r.source_id, dataset_id=r.dataset_id, version=int(r.version)) for r in g.itertuples()]))
    n = sql(all_obs, dictionary, divisions, registry)
    (PROCESSED / "division_sante.json").write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Dictionnaire : {len(dictionary)} indicateurs ; observations courantes : {len(obs)} ; SQL : {n} instructions")
    print("Inégalités :", [(i["indicator_id"], i["gini"]) for i in payload["inegalites"]])
    print("Territoires signalés :", len(payload["signaux"]), [f["nom"] for f in payload["signaux"][:6]])


if __name__ == "__main__":
    main()
