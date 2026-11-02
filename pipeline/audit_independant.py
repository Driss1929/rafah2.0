"""Recalcul indépendant de Rafah depuis les fichiers bruts.

N'importe rien de build_index.py : les colonnes sont retrouvées par leur intitulé et les
territoires par leur libellé, puis tout est comparé aux fichiers publiés et aux pages du site.
Usage : python audit_independant.py [racine_du_projet]
"""
import csv
import json
import math
import re
import sys
import unicodedata
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
RAW, OUT, APP = ROOT / "data" / "raw", ROOT / "data" / "processed", ROOT / "app"


def ascii_key(s):
    s = "".join(c for c in unicodedata.normalize("NFKD", str(s)) if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z]", "", s)


def header_map(df, rows):
    """(niveau 1, niveau 2, ...) -> indice de colonne, avec report des cellules fusionnées."""
    out, carry = {}, [None] * len(rows)
    for j in range(df.shape[1]):
        key = []
        for n, r in enumerate(rows):
            v = df.iat[r, j]
            if pd.notna(v):
                carry[n] = tidy(v)
                carry[n + 1:] = [None] * (len(rows) - n - 1)
            key.append(carry[n])
        out.setdefault(tuple(key), j)
    return out


def tidy(v):
    return re.sub(r"\s+", " ", str(v)).replace("’", "'").strip()


def find(head, *parts):
    key = tuple(tidy(p) if p is not None else None for p in parts)
    if key in head:
        return head[key]
    raise KeyError(f"{key} ; proches : {[k for k in head if k[-2:][0] and key[-2 if len(key) > 1 else 0] and tidy(key[1 if len(key) > 2 else 0])[:18] in str(k)][:4]}")


def territories(df):
    names = df[1].astype(str)
    return df[names.str.match(r"^(Province|Préfecture) d") & ~names.str.contains("arrondissement") & (pd.to_numeric(df[0], errors="coerce") < 100000)]


def census():
    book = RAW / "hcp_national_242671.xlsx"
    p = pd.read_excel(book, sheet_name="Population", header=None)
    m = pd.read_excel(book, sheet_name="Ménages", header=None)
    hp, hm = header_map(p, [0, 1, 2]), header_map(m, [0, 1])
    P, M = territories(p), territories(m)
    assert len(P) == 75 and len(M) == 75, (len(P), len(M))
    code = P[0].astype(int).values
    def pc(sex, label, sub=None):
        return pd.to_numeric(P[find(hp, f"Sexe : {sex}", label, sub)], errors="coerce").values
    def mc(label, sub):
        return pd.to_numeric(M[find(hm, label, sub)], errors="coerce").values
    edu = "Niveau d'études dans l'enseignement général (%)"
    st = "Statut professionnel des actifs occupés de 15 ans et plus (%)"
    confort, dech, cuis = "Disponibilité des éléments essentiels de confort (%)", "Mode d’évacuation des déchets ménagers (%)", "Combustible de cuisson utilisé (%)"
    pop = pc("Ensemble", "Population municipale")
    d = pd.DataFrame({
        "pop": pop,
        "analphabetisme": pc("Ensemble", "Taux d'analphabétisme des 10 ans et plus (%)"),
        "scolarisation": pc("Ensemble", "Taux de scolarisation des 6-11 ans en 2023/2024 (%)"),
        "secondaire": pc("Ensemble", edu, "Secondaire collégial") + pc("Ensemble", edu, "Secondaire qualifiant") + pc("Ensemble", edu, "Supérieur"),
        "chomage": pc("Ensemble", "Taux de chômage (%)"),
        "salaries": pc("Ensemble", "Population active occupée de 15 ans et plus") * (pc("Ensemble", st, "Salarié du secteur public") + pc("Ensemble", st, "Salarié du secteur privé")) / 100 / pop * 1000,
        "ecart_alpha": pc("Féminin", "Taux d'analphabétisme des 10 ans et plus (%)") - pc("Masculin", "Taux d'analphabétisme des 10 ans et plus (%)"),
        "activite_f": pc("Féminin", "Taux d'activité des 15 ans et plus (%)"),
        "assainissement": mc("Mode d’évacuation des eaux usées (%)", "Réseau public d'assainissement"),
        "electricite": mc(confort, "Électricité"),
        "eau": mc(confort, "Eau courante"),
        "bidonville": mc("Type de logement (%)", "Maison sommaire / Bidonville"),
        "bois": mc(cuis, "Charbon") + mc(cuis, "Bois énergie"),
        "dechets": mc(dech, "Bac à ordures de la commune") + mc(dech, "Camion de la commune / Camion privé"),
        "enclavement": mc("Distance moyenne des logements à la route goudronnée (Km)", None),
    }, index=code)
    d["enclavement"] = d.enclavement.fillna(0)
    d["nom"] = P[1].str.replace(r"^(Préfecture|Province) d[e']\s?", "", regex=True).values
    return d


ALIAS = {"rehamena": "rehamna", "taroudant": "taroudannt", "fkihbensaleh": "fquihbensalah", "mohammedia": "mohammadia", "tangerassilah": "tangerassilah",
         "agadiridaoutanane": "agadiridaoutanane"}
CASA = ["alfidamerssultan", "ainchok", "ainsebaahaymohammadi", "benmsick", "casablancaanfa", "hayhassani", "moulayrachid", "sidibernoussi"]


def health(d):
    idx = {ascii_key(n): c for c, n in d.nom.items()}
    def code(n):
        k = ascii_key(n)
        k = ALIAS.get(k, k)
        return idx["casablanca"] if k in CASA else idx[k]
    h = pd.read_csv(RAW / "cartesanitaire_2024.csv")
    h["c"] = h.delegation.map(code)
    h["nm"] = h.population / h.habitants_par_medecin_public_prive
    h["nl"] = (h.population / h.habitants_par_lit_public_prive).fillna(0)
    missing = h.loc[h.habitants_par_medecin_public_prive.isna(), "c"].tolist()
    g = h.groupby("c").agg(pop=("population", "sum"), nm=("nm", "sum"), nl=("nl", "sum"))
    d["medecins"], d["lits"] = g.nm / g["pop"] * 1e4, g.nl / g["pop"] * 1e4
    for c in missing:
        same = [o for o in g.index if str(o)[:-3] == str(c)[:-3] and o not in missing]
        d.loc[c, "medecins"] = g.nm[same].sum() / g["pop"][same].sum() * 1e4
    e = pd.read_excel(RAW / "datagov" / "essp-2024.xlsx", header=None)
    e = e[e[4].isin(["CSU-1", "CSU-2", "CSR-1", "CSR-2", "DR"])]
    d["essp"] = e[1].map(code).value_counts().reindex(d.index) / d["pop"] * 1e4
    return d


def enterprises(d):
    x = pd.read_excel(RAW / "hcp_cee_242672.xlsx", header=None)
    hdr = x.iloc[:8].fillna("").astype(str)
    col = None
    for j in range(x.shape[1]):
        if "but lucratif" in hdr.iat[5, j] and hdr.iat[6, j].strip().startswith("Nombre d'établissements"):
            col = j
            break
    if col is None:  # en-tête décalé d'une ligne
        col = next(j for j in range(x.shape[1]) if hdr.iloc[:, j].str.contains("but lucratif").any() and pd.to_numeric(x.iloc[7:, j], errors="coerce").sum() > 1e6)
    total = pd.to_numeric(x.iat[7, col], errors="coerce") if pd.notna(x.iat[7, col]) else None
    out = {}
    for _, r in x.iterrows():
        cells = [str(v).strip() for v in r.tolist() if pd.notna(v)]
        m = next((re.fullmatch(r"(\d\d)\.(\d{3})\.", c) for c in cells if re.fullmatch(r"(\d\d)\.(\d{3})\.", c)), None)
        if m and any(re.match(r"(Province|Préfecture)\s*:", c) for c in cells):
            out[int(m[1]) * 1000 + int(m[2])] = float(r[col])
    d["etablissements"] = pd.Series(out).reindex(d.index) / d["pop"] * 1e3
    return d, total


def main():
    report = {}
    d, cee_total = enterprises(health(census()))
    meta = pd.read_csv(OUT / "rafah_metadonnees.csv", encoding="utf-8-sig")
    pub = pd.read_csv(OUT / "rafah_provinces.csv", encoding="utf-8-sig").set_index("code_hcp").reindex(d.index)
    ids = meta.id.tolist()
    assert d[ids].notna().all().all(), d[ids].isna().sum()
    report["territoires"] = len(d)
    diff = {i: float((d[i] - pub[i]).abs().max()) for i in ids}
    report["ecart_max_valeurs"] = max(diff.values())
    bad = {k: round(v, 4) for k, v in diff.items() if v > .0015}
    report["indicateurs_divergents"] = bad

    # Bornes recalculées : cible déclarée, sinon centiles 5 et 95.
    L, U = {}, {}
    for _, m in meta.iterrows():
        v = d[m.id]
        target = isinstance(m.cible, str)
        if m.sens > 0:
            L[m.id], U[m.id] = float(np.percentile(v, 5)), (100.0 if target else float(np.percentile(v, 95)))
        else:
            L[m.id], U[m.id] = (0.0 if target else float(np.percentile(v, 5))), float(np.percentile(v, 95))
    report["ecart_max_bornes"] = max(max(abs(L[i] - meta.set_index("id").L[i]), abs(U[i] - meta.set_index("id").U[i])) for i in ids)

    S = pd.DataFrame({m.id: (1 + 99 * ((d[m.id] - L[m.id]) if m.sens > 0 else (U[m.id] - d[m.id])) / (U[m.id] - L[m.id])).clip(1, 100) for _, m in meta.iterrows()})
    dims = pd.DataFrame({k: S[meta[meta.dim == k].id].mean(axis=1) for k in range(6)})
    index = np.exp(np.log(dims).mean(axis=1))
    pubS = pd.read_csv(OUT / "rafah_scores_indicateurs.csv", encoding="utf-8-sig").set_index("code_hcp").reindex(d.index)
    names = ["Santé", "Éducation", "Emploi et revenus", "Logement et services de base", "Eau et cadre de vie", "Inclusion sociale"]
    report["scores_indicateurs_compares"] = int(S.size)
    report["ecart_max_scores_indicateurs"] = float((S - pubS[S.columns]).abs().max().max())
    report["scores_dimensions_compares"] = int(dims.size)
    report["ecart_max_dimensions"] = max(float((dims[k] - pub["D_" + n]).abs().max()) for k, n in enumerate(names))
    report["indices_compares"] = len(index)
    report["ecart_max_indice"] = float((index - pub.rafah).abs().max())
    report["rangs_differents"] = int((index.rank(ascending=False, method="min") != pub.rang).sum())

    # Ce que les pages embarquent réellement.
    page = (APP / "explorer.html").read_text(encoding="utf-8")
    emb = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>', page, re.S)[1].replace("<\\/", "</"))
    im = {i["id"]: i for i in emb["indicators"]}
    def js(v):
        ds = [sum(min(100, max(1, 1 + 99 * ((v[i["id"]] - i["L"]) if i["sens"] > 0 else (i["U"] - v[i["id"]])) / (i["U"] - i["L"]))) for i in emb["indicators"] if i["dim"] == k) / 3 for k in range(6)]
        return math.exp(sum(map(math.log, ds)) / 6)
    app_scores = pd.Series({p["code"]: js(p["v"]) for p in emb["provinces"]})
    report["ecart_max_site_vs_calcul"] = float((app_scores.reindex(d.index) - index).abs().max())
    report["statuts_complets"] = all(set(p["status"]) == set(ids) and all(p["v"][i] is not None for i in ids) for p in emb["provinces"])
    report["etablissements_total_ok"] = bool(abs(pub.n_etab.sum() - 1130021) < 1)

    # Contours : le chef-lieu de chaque territoire doit tomber dans son polygone.
    report["carte"] = check_map(d)

    # Analyses de méthode : redondance et cohérence.
    corr = S.corr(method="spearman")
    pairs = [(a, b, round(float(corr.loc[a, b]), 2)) for n, a in enumerate(ids) for b in ids[n + 1:] if abs(corr.loc[a, b]) >= .8]
    report["paires_redondantes"] = sorted(pairs, key=lambda t: -abs(t[2]))
    alpha = {}
    within = {}
    for k, n in enumerate(names):
        sub = S[meta[meta.dim == k].id]
        c = sub.shape[1]
        alpha[n] = round(float(c / (c - 1) * (1 - sub.var().sum() / sub.sum(axis=1).var())), 2)
        within[n] = {i: round(float(sub[i].corr(sub.drop(columns=i).mean(axis=1), method="spearman")), 2) for i in sub.columns}
    report["alpha_cronbach"] = alpha
    report["correlation_reste_de_dimension"] = within
    report["indicateurs_negatifs_dans_leur_dimension"] = [i for w in within.values() for i, v in w.items() if v < 0]

    variants = {}
    # Normalisation homogène : centiles 5-95 partout, sans cible ODD.
    H = pd.DataFrame({m.id: (1 + 99 * (((d[m.id] - np.percentile(d[m.id], 5)) if m.sens > 0 else (np.percentile(d[m.id], 95) - d[m.id])) / (np.percentile(d[m.id], 95) - np.percentile(d[m.id], 5)))).clip(1, 100) for _, m in meta.iterrows()})
    variants["Bornes homogènes : centiles 5-95 partout"] = np.exp(np.log(pd.DataFrame({k: H[meta[meta.dim == k].id].mean(axis=1) for k in range(6)})).mean(axis=1))
    Z = pd.DataFrame({m.id: m.sens * (d[m.id] - d[m.id].mean()) / d[m.id].std() for _, m in meta.iterrows()})
    variants["Scores z, moyenne arithmétique"] = pd.DataFrame({k: Z[meta[meta.dim == k].id].mean(axis=1) for k in range(6)}).mean(axis=1)
    variants["Inclusion sans la distance à la route"] = np.exp(np.log(dims.assign(**{"5": S[["ecart_alpha", "activite_f"]].mean(axis=1)}).drop(columns=[5])).mean(axis=1))
    bottom = set(index.nsmallest(15).index)
    report["variantes"] = {k: dict(spearman=round(float(index.corr(v, method="spearman")), 3), bas15=len(bottom & set(v.nsmallest(15).index)),
                                   pauvrete=round(float(v.corr(pub.mpi_2024, method="spearman")), 3)) for k, v in variants.items()}
    (OUT / "audit_independant.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1))


# Chefs-lieux, coordonnées approximatives (lat, lon).
SEATS = {"Tanger-Assilah": (35.76, -5.80), "M'diq-Fnideq": (35.68, -5.33), "Tétouan": (35.57, -5.37), "Fahs-Anjra": (35.68, -5.62), "Larache": (35.15, -6.10), "Al Hoceima": (35.15, -3.95), "Chefchaouen": (35.17, -5.26), "Ouezzane": (34.80, -5.58),
         "Oujda-Angad": (34.68, -1.91), "Nador": (35.15, -2.95), "Driouch": (34.98, -3.38), "Jerada": (34.31, -2.16), "Berkane": (34.92, -2.32), "Taourirt": (34.41, -2.90), "Guercif": (34.23, -3.35), "Figuig": (32.49, -1.97),
         "Fès": (34.03, -4.99), "Meknès": (33.88, -5.55), "El Hajeb": (33.69, -5.37), "Ifrane": (33.53, -5.11), "Moulay Yacoub": (34.09, -5.18), "Sefrou": (33.83, -4.83), "Boulemane": (33.36, -4.73), "Taounate": (34.54, -4.64), "Taza": (34.21, -4.01),
         "Rabat": (34.00, -6.84), "Salé": (34.03, -6.78), "Skhirate-Témara": (33.92, -6.91), "Kénitra": (34.26, -6.57), "Khémisset": (33.82, -6.07), "Sidi Kacem": (34.22, -5.71), "Sidi Slimane": (34.26, -5.93),
         "Béni Mellal": (32.34, -6.36), "Azilal": (31.96, -6.57), "Fquih Ben Salah": (32.50, -6.69), "Khénifra": (32.94, -5.67), "Khouribga": (32.88, -6.91),
         "Casablanca": (33.58, -7.60), "Mohammadia": (33.69, -7.38), "El Jadida": (33.25, -8.50), "Nouaceur": (33.37, -7.58), "Médiouna": (33.45, -7.51), "Benslimane": (33.61, -7.12), "Berrechid": (33.27, -7.59), "Settat": (33.00, -7.62), "Sidi Bennour": (32.65, -8.43),
         "Marrakech": (31.63, -8.00), "Chichaoua": (31.54, -8.76), "Al Haouz": (31.45, -7.97), "El Kelâa Des-Sraghna": (32.05, -7.41), "Essaouira": (31.51, -9.76), "Rehamna": (32.25, -7.95), "Safi": (32.30, -9.23), "Youssoufia": (32.25, -8.53),
         "Errachidia": (31.93, -4.43), "Ouarzazate": (30.92, -6.89), "Midelt": (32.68, -4.74), "Tinghir": (31.51, -5.53), "Zagora": (30.33, -5.84),
         "Agadir-Ida-Ou-Tanane": (30.42, -9.60), "Inezgane-Aït Melloul": (30.35, -9.54), "Chtouka-Aït Baha": (30.07, -9.15), "Taroudannt": (30.47, -8.88), "Tiznit": (29.70, -9.73), "Tata": (29.74, -7.97),
         "Guelmim": (28.99, -10.06), "Assa-Zag": (28.61, -9.43), "Tan-Tan": (28.44, -11.10), "Sidi Ifni": (29.38, -10.17),
         "Laâyoune": (27.15, -13.20), "Boujdour": (26.13, -14.48), "Tarfaya": (27.94, -12.92), "Es-Semara": (26.74, -11.67), "Oued Ed-Dahab": (23.72, -15.94), "Aousserd": (22.56, -14.33)}


def inside(lon, lat, ring):
    hit = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        if (y1 > lat) != (y2 > lat) and lon < x1 + (lat - y1) / (y2 - y1) * (x2 - x1):
            hit = not hit
    return hit


def check_map(d):
    geo = json.loads((OUT / "provinces.geojson").read_text(encoding="utf-8"))["features"]
    polys = {}
    for f in geo:
        g = f["geometry"]
        polys[f["properties"]["code"]] = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
    assert len(polys) == 75 and set(SEATS) == set(d.nom), set(SEATS) ^ set(d.nom)
    wrong, near = [], []
    for code, name in d.nom.items():
        lat, lon = SEATS[name]
        holder = [c for c, ps in polys.items() if any(inside(lon, lat, p[0]) for p in ps)]
        if code in holder:
            continue
        nearest = min(polys, key=lambda c: min((x - lon) ** 2 + (y - lat) ** 2 for p in polys[c] for x, y in p[0]))
        (near if nearest == code and not holder else wrong).append(name + (f" -> {[d.nom[h] for h in holder] or d.nom[nearest]}"))
    return dict(chefs_lieux_testes=len(SEATS), dans_leur_polygone=75 - len(wrong) - len(near), en_bord_de_cote=near, a_examiner=wrong)


if __name__ == "__main__":
    main()
