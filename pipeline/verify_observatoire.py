"""Vérification M01 : la page publiée, l'API et PostGIS donnent-ils les mêmes valeurs ?

Usage : python pipeline/verify_observatoire.py [url_du_site]
Lit la base PostGIS locale (localhost:5544, base rafah) avec psql ; compare aux données embarquées dans app/sante.html
et, si une URL est donnée, dans la page en ligne. Écrit data/processed/verification_m01.json.
"""
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
PSQL = Path(r"C:\Users\hp\rafah-tools\pgsql\bin\psql.exe")


def sql(q):
    out = subprocess.run([str(PSQL), "-h", "localhost", "-p", "5544", "-U", "rafah", "-d", "rafah", "-tAF", "\t", "-c", q], capture_output=True, text=True, encoding="utf-8", check=True).stdout
    return [l.split("\t") for l in out.strip().splitlines() if l]


def embedded(html):
    m = re.search(r"RafahDivision\.render\((\{.*?\}), \{\"type\"", html, re.S)
    return json.loads(m[1])


def compare(page, db):
    diffs, n = [], 0
    for t in page["territoires"]:
        for c in page["colonnes"]:
            v = t["valeurs"][c["indicator_id"]]
            d = db.get((c["indicator_id"], t["territory_id"], c["periode"]))
            n += 1
            if d is None or (v is None) != (d[0] is None) or (v is not None and abs(v - d[0]) > 5e-4):
                diffs.append((c["indicator_id"], t["nom"], c["periode"], v, d))
    return n, diffs


def main():
    db = {(r[0], r[1], r[2]): (float(r[3]) if r[3] else None, r[4], r[5]) for r in sql("SELECT indicator_id, territory_id, period, value, status, source_id FROM observations_courantes")}
    checks = {}
    n, diffs = compare(embedded((ROOT / "app" / "sante.html").read_text(encoding="utf-8")), db)
    checks["page_locale_vs_postgis"] = dict(valeurs=n, ecarts=len(diffs), exemples=diffs[:5])
    if len(sys.argv) > 1:
        html = urllib.request.urlopen(sys.argv[1].rstrip("/") + "/sante.html", timeout=30).read().decode("utf-8")
        n, diffs = compare(embedded(html), db)
        checks["page_en_ligne_vs_postgis"] = dict(valeurs=n, ecarts=len(diffs), exemples=diffs[:5])
    checks["observations_sans_source"] = int(sql("SELECT count(*) FROM indicator_observations WHERE source_id IS NULL OR dataset_id IS NULL")[0][0])
    checks["territoires_par_indicateur_et_periode"] = sorted({int(r[0]) for r in sql("SELECT count(DISTINCT territory_id) FROM observations_courantes GROUP BY indicator_id, period")})
    checks["statuts"] = {r[0]: int(r[1]) for r in sql("SELECT status, count(*) FROM observations_courantes GROUP BY 1 ORDER BY 1")}
    checks["zeros_sans_statut_zero"] = [r for r in sql("SELECT indicator_id, territory_name, status FROM observations_courantes WHERE value = 0 AND status <> 'zero_reel'")]
    checks["valeurs_nulles_avec_statut_a_valeur"] = int(sql("SELECT count(*) FROM indicator_observations o JOIN value_statuses s USING (status) WHERE (o.value IS NULL) = s.has_value")[0][0])
    checks["indicateurs_par_division"] = {r[0]: int(r[1]) for r in sql("SELECT coalesce(division_id, 'aucune'), count(DISTINCT indicator_id) FROM observations_courantes GROUP BY 1 ORDER BY 1")}
    checks["geometries_invalides"] = int(sql("SELECT count(*) FROM territories WHERE NOT ST_IsValid(geom)")[0][0])
    (ROOT / "data" / "processed" / "verification_m01.json").write_text(json.dumps(checks, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(json.dumps(checks, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
