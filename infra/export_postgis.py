"""Écrit le script SQL qui charge le référentiel Rafah dans PostGIS.

Usage : python infra/export_postgis.py [racine_du_projet]  ->  infra/rafah_postgis.sql
"""
import json
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
API = ROOT / "data" / "api" / "v1"
load = lambda rel: json.loads((API / rel).read_text(encoding="utf-8"))


def q(v):
    if v is None:
        return "NULL"
    return str(v) if isinstance(v, (int, float)) else "'" + str(v).replace("'", "''") + "'"


sql = ["""-- Généré par infra/export_postgis.py. Résultats non officiels.
BEGIN;
CREATE EXTENSION IF NOT EXISTS postgis;
DROP VIEW IF EXISTS territoires_scores;
DROP TABLE IF EXISTS territory_indicators, territory_dimensions, territories, indicators, dimensions, data_versions;
CREATE TABLE data_versions (version text PRIMARY KEY, computed_on date NOT NULL, note text);
CREATE TABLE dimensions (id text PRIMARY KEY, name text NOT NULL);
CREATE TABLE indicators (id text PRIMARY KEY, name text NOT NULL, dimension_id text NOT NULL REFERENCES dimensions, direction text NOT NULL CHECK (direction IN ('positive','negative')),
  unit text NOT NULL, source text NOT NULL, lower_bound double precision NOT NULL, upper_bound double precision NOT NULL, bound_basis text NOT NULL);
CREATE TABLE territories (id text PRIMARY KEY, name text NOT NULL, type text NOT NULL CHECK (type IN ('Province','Préfecture')), region text NOT NULL, population integer NOT NULL CHECK (population > 0),
  rafah_score double precision NOT NULL CHECK (rafah_score BETWEEN 1 AND 100), national_rank integer NOT NULL UNIQUE, regional_rank integer NOT NULL, reliability text NOT NULL,
  data_version text NOT NULL REFERENCES data_versions, geom geometry(MultiPolygon, 4326) NOT NULL CHECK (ST_IsValid(geom)));
CREATE INDEX territories_geom_idx ON territories USING GIST (geom);
CREATE TABLE territory_dimensions (territory_id text NOT NULL REFERENCES territories, dimension_id text NOT NULL REFERENCES dimensions, score double precision NOT NULL CHECK (score BETWEEN 1 AND 100), PRIMARY KEY (territory_id, dimension_id));
CREATE TABLE territory_indicators (territory_id text NOT NULL REFERENCES territories, indicator_id text NOT NULL REFERENCES indicators, value double precision NOT NULL, normalized double precision NOT NULL CHECK (normalized BETWEEN 1 AND 100), status text NOT NULL, PRIMARY KEY (territory_id, indicator_id));
"""]
meta = load("metadata.json")
sql.append(f"INSERT INTO data_versions VALUES ({q(meta['data_version'])}, {q(meta['computed_on'])}, 'Résultats non officiels');")
dims = load("dimensions.json")
sql += [f"INSERT INTO dimensions VALUES ({q(d['id'])}, {q(d['name'])});" for d in dims]
sql += [f"INSERT INTO indicators VALUES ({q(i['id'])}, {q(i['name'])}, {q(i['dimension'])}, {q(i['direction'])}, {q(i['unit'])}, {q(i['source'])}, {i['lower_bound']}, {i['upper_bound']}, {q(i['bound_basis'])});" for i in load("indicators.json")]
for t in load("territories.json")["territories"]:
    tid = t["territory_id"]
    s = load(f"territories/{tid}/index.json")
    geom = json.dumps(load(f"territories/{tid}/geometry.json")["geometry"], separators=(",", ":"))
    sql.append(f"INSERT INTO territories VALUES ({q(tid)}, {q(s['name'])}, {q(s['type'])}, {q(s['region'])}, {s['population']}, {s['rafah_score']}, {s['national_rank']}, {s['regional_rank']}, {q(s['reliability'])}, {q(s['data_version'])}, ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON({q(geom)}), 4326)));")
    sql += [f"INSERT INTO territory_dimensions VALUES ({q(tid)}, {q(k)}, {v});" for k, v in load(f"territories/{tid}/dimensions.json")["dimensions"].items()]
    sql += [f"INSERT INTO territory_indicators VALUES ({q(tid)}, {q(i['id'])}, {i['value']}, {i['normalized']}, {q(i['status'])});" for i in load(f"territories/{tid}/indicators.json")["indicators"]]
sql.append("""CREATE VIEW territoires_scores AS
SELECT t.id, t.name, t.type, t.region, t.population, t.rafah_score, t.national_rank, t.reliability,
  max(d.score) FILTER (WHERE d.dimension_id = 'health') AS health, max(d.score) FILTER (WHERE d.dimension_id = 'education') AS education,
  max(d.score) FILTER (WHERE d.dimension_id = 'employment') AS employment, max(d.score) FILTER (WHERE d.dimension_id = 'housing') AS housing,
  max(d.score) FILTER (WHERE d.dimension_id = 'water_environment') AS water_environment, max(d.score) FILTER (WHERE d.dimension_id = 'social_inclusion') AS social_inclusion, t.geom
FROM territories t JOIN territory_dimensions d ON d.territory_id = t.id GROUP BY t.id;
COMMIT;""")
out = ROOT / "infra" / "rafah_postgis.sql"
out.write_text("\n".join(sql) + "\n", encoding="utf-8")
print(out.name, len(sql), "instructions")
