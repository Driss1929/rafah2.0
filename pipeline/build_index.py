"""Calcule l'indice Rafah pour les 75 provinces et préfectures du Maroc.

Usage : python build_index.py [racine_du_projet]
Entrées : data/raw/  -  Sorties : data/processed/
"""
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

DIMENSIONS = ["Santé", "Éducation", "Emploi et revenus", "Logement et services de base",
              "Eau et cadre de vie", "Inclusion sociale"]

# low/high : cible ODD quand elle existe, sinon None = centile 5 ou 95 observé.
# Pour un indicateur de sens -, "low" est la meilleure valeur et "high" la pire.
INDICATORS = [
    dict(id="medecins", dim=0, label="Médecins (public + privé) pour 10 000 habitants", sens=1, lever=True, unit="pour 10 000 hab.", source="Ministère de la Santé, carte sanitaire (2024)", low=None, high=None, cible=None),
    dict(id="essp", dim=0, label="Établissements de soins primaires pour 10 000 habitants", sens=1, lever=True, unit="pour 10 000 hab.", source="Ministère de la Santé, data.gov.ma (2024)", low=None, high=None, cible=None),
    dict(id="lits", dim=0, label="Lits d'hôpital (public + privé) pour 10 000 habitants", sens=1, lever=True, unit="pour 10 000 hab.", source="Ministère de la Santé, carte sanitaire (2024)", low=None, high=None, cible=None),
    dict(id="analphabetisme", dim=1, label="Taux d'analphabétisme (10 ans et plus)", sens=-1, lever=False, unit="%", source="HCP, RGPH 2024", low=0, high=None, cible="ODD 4.6"),
    dict(id="scolarisation", dim=1, label="Taux de scolarisation des 6-11 ans", sens=1, lever=True, unit="%", source="HCP, RGPH 2024", low=None, high=100, cible="ODD 4.1"),
    dict(id="secondaire", dim=1, label="Population de niveau secondaire ou supérieur", sens=1, lever=False, unit="%", source="HCP, RGPH 2024", low=None, high=None, cible=None),
    dict(id="chomage", dim=2, label="Taux de chômage", sens=-1, lever=False, unit="%", source="HCP, RGPH 2024", low=None, high=None, cible=None),
    dict(id="salaries", dim=2, label="Salariés (public + privé) pour 1 000 habitants", sens=1, lever=True, unit="pour 1 000 hab.", source="HCP, RGPH 2024", low=None, high=None, cible=None),
    dict(id="etablissements", dim=2, label="Établissements économiques pour 1 000 habitants", sens=1, lever=False, unit="pour 1 000 hab.", source="HCP, CEE 2023/2024", low=None, high=None, cible=None),
    dict(id="assainissement", dim=3, label="Ménages raccordés à l'assainissement", sens=1, lever=True, unit="%", source="HCP, RGPH 2024", low=None, high=100, cible="ODD 6.2"),
    dict(id="electricite", dim=3, label="Ménages disposant de l'électricité", sens=1, lever=True, unit="%", source="HCP, RGPH 2024", low=None, high=100, cible="ODD 7.1"),
    dict(id="bidonville", dim=3, label="Logements de type sommaire ou bidonville", sens=-1, lever=True, unit="%", source="HCP, RGPH 2024", low=0, high=None, cible="ODD 11.1"),
    dict(id="eau", dim=4, label="Ménages disposant de l'eau courante", sens=1, lever=True, unit="%", source="HCP, RGPH 2024", low=None, high=100, cible="ODD 6.1"),
    dict(id="bois", dim=4, label="Ménages cuisinant au bois ou au charbon", sens=-1, lever=False, unit="%", source="HCP, RGPH 2024", low=0, high=None, cible="ODD 7.1"),
    dict(id="dechets", dim=4, label="Ménages dont les déchets sont collectés", sens=1, lever=True, unit="%", source="HCP, RGPH 2024", low=None, high=100, cible="ODD 11.6"),
    dict(id="ecart_alpha", dim=5, label="Écart d'analphabétisme femmes-hommes", sens=-1, lever=False, unit="points", source="HCP, RGPH 2024", low=0, high=None, cible="ODD 4.5"),
    dict(id="activite_f", dim=5, label="Taux d'activité des femmes", sens=1, lever=False, unit="%", source="HCP, RGPH 2024", low=None, high=None, cible=None),
    dict(id="enclavement", dim=5, label="Distance moyenne des logements à la route goudronnée", sens=-1, lever=False, unit="km", source="HCP, RGPH 2024", low=None, high=None, cible=None),
]
IDS = [i["id"] for i in INDICATORS]
# Valeurs obtenues par somme ou ratio de chiffres publiés ; les autres sont reprises telles quelles.
CALCULATED = {"medecins", "essp", "lits", "secondaire", "salaries", "etablissements", "bois", "dechets", "ecart_alpha"}

ALIASES = {
    "rehamena": "rehamna", "rhamna": "rehamna", "taroudant": "taroudannt", "fkihbensaleh": "fquihbensalah",
    "fquihbensaleh": "fquihbensalah", "mohammedia": "mohammadia", "tangerassilah": "tangerassilah",
    "tangierassilah": "tangerassilah", "elkelaatessraghna": "elkelaadessraghna", "assazag": "assazag",
    "elkelatessraghna": "elkelaadessraghna", "eddakhlaouededdahab": "ouededdahab", "laayoune": "laayoune",
    "essemara": "essemara", "tantan": "tantan",
}
CASABLANCA = {"Al Fida-Mers Sultan", "Aïn Chok", "Aïn Sebaâ-Hay Mohammadi", "Ben Msick", "Casablanca Anfa",
              "Hay Hassani", "Moulay Rachid", "Sidi Bernoussi"}


def key(name):
    """Clé de rapprochement des noms de provinces entre sources."""
    s = unicodedata.normalize("NFKD", str(name))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^\x00-\x7f]", " ", s).lower()
    s = re.sub(r"^\s*(prefecture|province)\s*(of|de|d'|:)?\s*", "", s)
    s = re.sub(r"\s*(province|prefecture)\s*$", "", s)
    s = re.sub(r"[^a-z]", "", s)
    return ALIASES.get(s, s)


def is_province(code):
    if pd.isna(code):
        return False
    c = str(int(code))
    return len(c) == 4 or (len(c) == 5 and c[:2] in ("10", "11", "12"))


def region_of(code):
    return int(str(int(code))[:-3])


def census():
    f = RAW / "hcp_national_242671.xlsx"
    p = pd.read_excel(f, sheet_name="Population", header=None)
    m = pd.read_excel(f, sheet_name="Ménages", header=None)
    p["code"], m["code"] = pd.to_numeric(p[0], errors="coerce"), pd.to_numeric(m[0], errors="coerce")
    regions = {int(r.code): re.sub(r"^Région d[e'] ?(l')?", "", r[1]) for _, r in p[p.code.between(1, 12)].iterrows()}
    p, m = p[p.code.map(is_province)].set_index("code"), m[m.code.map(is_province)].set_index("code")
    assert len(p) == 75 and len(m) == 75, (len(p), len(m))
    n = lambda df, c: pd.to_numeric(df[c], errors="coerce")
    d = pd.DataFrame(index=p.index.astype(int))
    d["nom"] = p[1].str.replace(r"^(Préfecture|Province) d[e']\s?", "", regex=True)
    d["type"] = p[1].str.split().str[0]
    d["region_code"] = [region_of(c) for c in d.index]
    d["region"] = d.region_code.map(regions)
    d["population"] = n(p, 3).astype(int)
    d["analphabetisme"] = n(p, 34)
    d["scolarisation"] = n(p, 32)
    d["secondaire"] = n(p, 45) + n(p, 46) + n(p, 47)
    d["chomage"] = n(p, 57)
    d["salaries"] = n(p, 58) * (n(p, 61) + n(p, 62)) / 100 / d.population * 1000
    d["assainissement"] = n(m, 25)
    d["electricite"] = n(m, 23)
    d["bidonville"] = n(m, 9)
    d["eau"] = n(m, 24)
    d["bois"] = n(m, 34) + n(m, 35)
    d["dechets"] = n(m, 28) + n(m, 29)
    d["ecart_alpha"] = n(p, 158) - n(p, 95)
    d["activite_f"] = n(p, 180)
    d["enclavement"] = n(m, 37)
    d["_enclavement_na"] = d.enclavement.isna()
    # "…" = sans objet selon le HCP : préfectures sans habitat rural, donc aucune distance à mesurer.
    d["enclavement"] = d.enclavement.fillna(0)
    return d


def health(d):
    h = pd.read_csv(RAW / "cartesanitaire_2024.csv")
    assert len(h) == 82
    h["k"] = h.delegation.map(lambda x: "casablanca" if x in CASABLANCA else key(x))
    idx = {key(v): c for c, v in d.nom.items()}
    h["code"] = h.k.map(idx)
    assert h.code.notna().all(), h[h.code.isna()].delegation.tolist()
    for c, r in [("n_med", "habitants_par_medecin_public_prive"), ("n_lit", "habitants_par_lit_public_prive")]:
        h[c] = h.population / h[r]
    h["med_na"] = h.habitants_par_medecin_public_prive.isna()
    # Ratio vide pour les lits : aucun hôpital dans la délégation, confirmé par la liste du ministère.
    h["n_lit"] = h.n_lit.fillna(0)
    g = h.groupby("code").agg(pop=("population", "sum"), n_med=("n_med", "sum"), n_lit=("n_lit", "sum"), med_na=("med_na", "any"))
    d["medecins"] = g.n_med / g["pop"] * 1e4
    d["lits"] = g.n_lit / g["pop"] * 1e4
    d["_imput_medecins"] = g.med_na
    for c in d.index[d._imput_medecins]:
        peers = g[(g.index.map(region_of) == d.region_code[c]) & ~g.med_na]
        d.loc[c, "medecins"] = peers.n_med.sum() / peers["pop"].sum() * 1e4

    e = pd.read_excel(RAW / "datagov" / "essp-2024.xlsx", header=1)
    e = e.iloc[:, :5]
    e.columns = ["region", "delegation", "commune", "nom", "cat"]
    e = e[e.cat.isin(["CSU-1", "CSU-2", "CSR-1", "CSR-2", "DR"])].copy()
    e["delegation"] = e.delegation.astype(str).str.strip()
    e["code"] = e.delegation.map(lambda x: 6141 if x in CASABLANCA else idx.get(key(x)))
    assert e.code.notna().all(), e[e.code.isna()].delegation.unique()
    d["n_essp"] = e.groupby("code").size()
    d["essp"] = d.n_essp / d.population * 1e4
    return d


def enterprises(d):
    x = pd.read_excel(RAW / "hcp_cee_242672.xlsx", header=None)
    out = {}
    for _, r in x.iterrows():
        v = [c for c in r.tolist() if pd.notna(c)]
        m = next((re.fullmatch(r"(\d\d)\.(\d{3})\.", str(c).strip()) for c in v if re.fullmatch(r"(\d\d)\.(\d{3})\.", str(c).strip())), None)
        if not m:
            continue
        pos = [i for i, c in enumerate(v) if re.match(r"(Province|Préfecture)\b", str(c))]
        if pos:
            out[int(m[1]) * 1000 + int(m[2])] = float(v[pos[0] + 5])
    s = pd.Series(out)
    missing = set(d.index) - set(s.index)
    assert not missing, missing
    d["n_etab"] = s
    d["etablissements"] = d.n_etab / d.population * 1e3
    return d


def poverty(d):
    x = pd.read_excel(RAW / "hcp_pauvrete_245096.xls", sheet_name="Ensemble", header=None, skiprows=6)
    x = x[x[2] == "province"]
    for y, s in [(2024, "mpi_2024"), (2014, "mpi_2014")]:
        d[s] = x[x[3] == y].assign(c=lambda t: t[1].astype(int)).set_index("c")[5].astype(float)
    assert d.mpi_2024.notna().all() and d.mpi_2014.notna().all()
    return d


def cnss_regional(d):
    c = pd.read_excel(RAW / "datagov" / "nombre-des-s_repartition-du-nombre-des-salaries-declares_2022.xlsx", header=None)
    names = {"Tanger-Tetouan-Al Hoceima": 1, "Oriental": 2, "Fès-Meknès": 3, "Rabat-Salé-Kénitra": 4, "Béni Mellal-Khénifra": 5,
             "Grand Casablanca-Settat": 6, "Marrakech-Safi": 7, "Drâa-Tafilalet": 8, "Souss-Massa": 9, "Guelmim-Oued Noun": 10,
             "Laayoune-Sakia El Hamra": 11, "Eddakhla-Oued Eddahab": 12}
    v = {names[r[0]]: float(r[1]) for _, r in c.iloc[:18].iterrows() if r[0] in names}
    assert len(v) == 12
    pop = d.groupby("region_code").population.sum()
    return d.region_code.map(lambda r: v[r] / pop[r] * 1000)


AR_NAMES = {
    "اسفي": "Safi", "ازيلال": "Azilal", "اكادير": "Agadir-Ida-Ou-Tanane", "ابنسليمان": "Benslimane", "بنسليمان": "Benslimane",
    "اسا/الزاك": "Assa-Zag", "اساالزاك": "Assa-Zag", "اسا": "Assa-Zag", "اشتوكهايتباها": "Chtouka-Aït Baha", "الجديده": "El Jadida",
    "الحسيمه": "Al Hoceima", "الحاجب": "El Hajeb", "الحوز": "Al Haouz", "الخميسات": "Khémisset", "الداخله": "Oued Ed-Dahab", "واديالذهب": "Oued Ed-Dahab",
    "الدريوش": "Driouch", "الرباط": "Rabat", "دالمستقلهتواكه": "Rabat", "بنمسيك": "Casablanca", "حيالمحمديعينالسبع": "Casablanca", "اكاديراداوتنان": "Agadir-Ida-Ou-Tanane", "وجدهانكاد": "Oujda-Angad","الرحامنه": "Rehamna", "السماره": "Es-Semara", "الصخيراتتماره": "Skhirate-Témara",
    "الصويره": "Essaouira", "العرائش": "Larache", "العيون": "Laâyoune", "الرشيديه": "Errachidia", "الفحصانجره": "Fahs-Anjra",
    "الفقيهبنصالح": "Fquih Ben Salah", "القنيطره": "Kénitra", "المحمديه": "Mohammadia", "المضيقالفنيدق": "M'diq-Fnideq", "الناضور": "Nador", "الناظور": "Nador",
    "اليوسفيه": "Youssoufia", "برشيد": "Berrechid", "بركان": "Berkane", "بولمان": "Boulemane", "بوجدور": "Boujdour", "بنيملال": "Béni Mellal",
    "تزنيت": "Tiznit", "تيزنيت": "Tiznit", "تطوان": "Tétouan", "تارودانت": "Taroudannt", "تاونات": "Taounate", "تازه": "Taza", "تنغير": "Tinghir",
    "تاوريرت": "Taourirt", "تاوريريت": "Taourirt", "جراده": "Jerada", "جرسيف": "Guercif", "خريبكه": "Khouribga", "خنيفره": "Khénifra", "زاكوره": "Zagora",
    "سطات": "Settat", "سلا": "Salé", "سيديسليمان": "Sidi Slimane", "سيديقاسم": "Sidi Kacem", "سيديايفني": "Sidi Ifni", "سيديافني": "Sidi Ifni", "سيديبنور": "Sidi Bennour",
    "شفشاون": "Chefchaouen", "شيشاوه": "Chichaoua", "صفرو": "Sefrou", "طرفايه": "Tarfaya", "طانطان": "Tan-Tan", "طاطا": "Tata", "طنجهاصيله": "Tanger-Assilah", "طنجه": "Tanger-Assilah",
    "فاس": "Fès", "فكيك": "Figuig", "فجيجبوعرفه": "Figuig", "فجيج": "Figuig", "قلعهالسراغنه": "El Kelâa Des-Sraghna", "السراغنه": "El Kelâa Des-Sraghna", "كلميم": "Guelmim", "ميعقوب": "Moulay Yacoub", "مولاييعقوب": "Moulay Yacoub",
    "مراكش": "Marrakech", "مديونه": "Médiouna", "مكناس": "Meknès", "ميدلت": "Midelt", "وجده": "Oujda-Angad", "ورزازات": "Ouarzazate", "وزان": "Ouezzane", "يفرن": "Ifrane", "افران": "Ifrane",
    "اوسرد": "Aousserd", "النواصر": "Nouaceur", "انزكانايتملول": "Inezgane-Aït Melloul",
    "ابنمسيكمولايرشيد": "Casablanca", "الدارالبيضاءانفا": "Casablanca", "الدارالبيضاء": "Casablanca", "الفداءمرسالسلطان": "Casablanca", "سالبرنوصيزناته": "Casablanca", "سيديالبرنوصي": "Casablanca",
    "عينالسبعالحيالمحمدي": "Casablanca", "عينالشقالحيالحسني": "Casablanca", "الحيالحسني": "Casablanca", "عينالشق": "Casablanca", "ابنمسيك": "Casablanca", "مولايرشيد": "Casablanca", "انفا": "Casablanca",
}
AR_IGNORE = {"دورالشبابالحضريه", "دورالشبابالقرويه", "مجموعدورالشباب", "nan", "الاقليم", "المديريهالاقليميه"}


def ar_key(s):
    s = re.sub(r"[ـ\s\-–/.,،]", "", str(s))
    return s.translate(str.maketrans("أإآة", "ااا" + "ه")).replace("ى", "ي")


def count_ar(d, path, col, header=0, label=""):
    """Compte les lignes d'une liste à noms de provinces arabes."""
    x = pd.read_excel(path, header=header)
    names = x.iloc[:, col].ffill().map(ar_key)
    idx = {v: c for c, v in d.nom.items()}
    aliases = {ar_key(k): v for k, v in AR_NAMES.items()}
    unknown = sorted({n for n in names if n not in aliases and n not in AR_IGNORE})
    print(f"[{label}] lignes {len(x)}, noms inconnus : {unknown}")
    assert not [n for n in names if n in aliases and aliases[n] not in idx]
    return names[names.isin(aliases)].map(lambda n: idx[aliases[n]]).value_counts().reindex(d.index, fill_value=0)


def schools(d, f):
    x = pd.read_excel(RAW / "datagov" / f)
    col = "LL_PROV" if "LL_PROV" in x else "PROVINCE"
    idx = {key(v): c for c, v in d.nom.items()}
    def code(n):
        n = str(n).strip()
        if n.startswith("Préf. d"):
            return 6141
        k = key(re.sub(r"^(Préfecture|Province)\s*:\s*", "", n))
        # Le ministère tronque les noms à 25 caractères.
        hits = [c for o, c in idx.items() if o.startswith(k)]
        return idx.get(k, hits[0] if len(hits) == 1 else None)
    c = x[col].map(code)
    assert c.notna().all(), sorted(x[col][c.isna()].astype(str).unique())
    return c.value_counts().reindex(d.index, fill_value=0)


def latin_list_counts(d, f, header, cats=None):
    x = pd.read_excel(RAW / "datagov" / f, header=header).iloc[:, :5]
    x.columns = ["region", "delegation", "commune", "nom", "cat"]
    x = x[x.delegation.notna() & x.cat.notna() & (x.cat != "Catégorie")]
    if cats:
        x = x[x.cat.isin(cats)]
    idx = {key(v): c for c, v in d.nom.items()}
    c = x.delegation.astype(str).str.strip().map(lambda n: 6141 if n in CASABLANCA else idx.get(key(n)))
    assert c.notna().all(), sorted(x.delegation[c.isna()].unique())
    return c.value_counts().reindex(d.index, fill_value=0)


def regional_portal(d, stem):
    """Valeur régionale CNSS pour 1 000 habitants (répétée sur chaque province de la région)."""
    f = next(p for p in (RAW / "datagov").iterdir() if p.name.startswith(stem))
    c = pd.read_excel(f, header=None)
    names = {"Tanger-Tetouan-Al Hoceima": 1, "Oriental": 2, "Fès-Meknès": 3, "Rabat-Salé-Kénitra": 4, "Béni Mellal-Khénifra": 5, "Grand Casablanca-Settat": 6,
             "Marrakech-Safi": 7, "Drâa-Tafilalet": 8, "Souss-Massa": 9, "Guelmim-Oued Noun": 10, "Laayoune-Sakia El Hamra": 11, "Eddakhla-Oued Eddahab": 12}
    v = {names[r[0]]: float(r[1]) for _, r in c.iloc[:18].iterrows() if r[0] in names}
    pop = d.groupby("region_code").population.sum()
    return d.region_code.map(lambda r: v[r] / pop[r] * 1000)


def ene_series(d, stem):
    f = next(p for p in (RAW / "datagov").iterdir() if stem in p.name and "meta" not in p.name)
    x = pd.read_excel(f, header=1)
    x = x[x.Milieu == "National"].copy()
    idx = {key(v): c for c, v in d.nom.items()}
    x["code"] = x.iloc[:, 1].astype(str).str.strip().map(lambda n: idx.get(key(n)))
    assert x.code.notna().all()
    years = [str(y) for y in range(2017, 2026)]
    return x.set_index("code")[years].apply(pd.to_numeric, errors="coerce")


def context(d):
    """Données complémentaires, affichées mais exclues du score."""
    pop = d.population
    dg = RAW / "datagov"
    find = lambda s: next(p.name for p in dg.iterdir() if s in p.name)
    c = pd.DataFrame(index=d.index)
    c["hopitaux"] = latin_list_counts(d, "hopitaux-2025.xlsx", 0)
    c["essp_2025"] = latin_list_counts(d, "essp-2025.xlsx", 2, ["CSU-1", "CSU-2", "CSR-1", "CSR-2", "DR"])
    c["primaires"] = schools(d, find("publics_primaire_juillet"))
    c["colleges"] = schools(d, find("publics_collegial_juillet"))
    c["lycees"] = schools(d, find("publics_qualifiant_juillet"))
    c["primaires_2023"] = schools(d, find("etab_pub_primaire_juin"))
    c["colleges_2023"] = schools(d, find("etab_pub_collegial_juin"))
    c["lycees_2023"] = schools(d, find("etab_pub_qualifiant_juin"))
    c["maisons_jeunes"] = count_ar(d, dg / find("reseau-des-maisons"), 1, 0, "maisons de jeunes")
    c["centres_femmes"] = count_ar(d, dg / find("liste-des-etablissements-multi"), 1, 0, "centres femmes")
    c["centres_handicap"] = count_ar(d, dg / find("liste-des-centres-d-orientatio"), 2, 0, "COAPH")
    c["unites_enfance"] = count_ar(d, dg / find("liste-des-unites-de-protection"), 1, 0, "protection enfance")
    c["cnss_region"] = regional_portal(d, "nombre-des-s_")
    c["entreprises_region"] = regional_portal(d, "entreprises-_")
    c["hop_100k"] = c.hopitaux / pop * 1e5
    c["secondaire_10k"] = (c.colleges + c.lycees) / pop * 1e4
    c["jeunes_100k"] = c.maisons_jeunes / pop * 1e5
    ene = {k: ene_series(d, s) for k, s in [("chomage", "chomage_prov.xlsx"), ("activite", "imt_txact"), ("emploi", "imt_txemp")]}
    c["ene_chomage_2025"] = ene["chomage"]["2025"]
    return c, ene


def bounds(d):
    for i in INDICATORS:
        i["L"] = i["low"] if i["low"] is not None else float(np.percentile(d[i["id"]], 5))
        i["U"] = i["high"] if i["high"] is not None else float(np.percentile(d[i["id"]], 95))
        if i["sens"] < 0 and i["low"] is None:
            i["best"], i["worst"] = i["L"], i["U"]
        assert i["U"] > i["L"], i["id"]
    return INDICATORS


def normalise(values, ind):
    r = (values - ind["L"]) / (ind["U"] - ind["L"])
    if ind["sens"] < 0:
        r = (ind["U"] - values) / (ind["U"] - ind["L"])
    return (1 + 99 * r).clip(1, 100)


def scores(d, inds=None):
    inds = inds or INDICATORS
    s = pd.DataFrame({i["id"]: normalise(d[i["id"]], i) for i in inds}, index=d.index)
    dims = pd.DataFrame({n: s[[i["id"] for i in inds if i["dim"] == k]].mean(axis=1) for k, n in enumerate(DIMENSIONS)})
    return s, dims


def geo(dims, w=None):
    w = np.full(dims.shape[1], 1 / dims.shape[1]) if w is None else np.asarray(w) / np.sum(w)
    return pd.Series(np.exp((np.log(dims.values) * w).sum(axis=1)), index=dims.index)


def compare(base, alt, name, k=15):
    rb, ra = base.rank(ascending=False), alt.rank(ascending=False)
    return dict(scenario=name, spearman=round(base.corr(alt, method="spearman"), 3),
                ecart_rang_moyen=round((rb - ra).abs().mean(), 1), ecart_rang_max=int((rb - ra).abs().max()),
                bas15_conserves=int(len(set(base.nsmallest(k).index) & set(alt.nsmallest(k).index))))


def robustness(d, dims, idx):
    res = []
    res.append(compare(idx, dims.mean(axis=1), "Moyenne arithmétique au lieu de géométrique"))
    z = (dims - dims.mean()) / dims.std()
    vals, vecs = np.linalg.eigh(np.corrcoef(z.T))
    load = vecs[:, -1] ** 2
    pca_w = dict(zip(DIMENSIONS, load.round(3).tolist()))
    res.append(compare(idx, geo(dims, load), "Poids issus de l'ACP"))
    for n in DIMENSIONS:
        res.append(compare(idx, geo(dims.drop(columns=n)), f"Sans la dimension {n}"))
    alt = d.copy()
    alt["salaries"] = cnss_regional(d)
    inds = [dict(i) for i in INDICATORS]
    for i in inds:
        if i["id"] == "salaries":
            i["L"], i["U"] = np.percentile(alt.salaries, 5), np.percentile(alt.salaries, 95)
    res.append(compare(idx, geo(scores(alt, inds)[1]), "CNSS 2022 régional au lieu des salariés provinciaux"))
    if d._imput_medecins.any():
        alt = d.copy()
        alt.loc[alt._imput_medecins, "medecins"] = 0
        res.append(compare(idx, geo(scores(alt)[1]), "Aousserd : 0 médecin au lieu de la valeur régionale"))
    rng = np.random.default_rng(2026)
    draws = rng.dirichlet(np.ones(6) * 4, 5000)
    logs = np.log(dims.values)
    mc = pd.DataFrame(np.exp(logs @ draws.T), index=dims.index)
    ranks = mc.rank(ascending=False)
    stab = pd.DataFrame({"rang_p05": ranks.quantile(.05, axis=1), "rang_p95": ranks.quantile(.95, axis=1),
                         "prob_bas15": (ranks > 60).mean(axis=1)})
    return res, pca_w, stab


def validation(d, dims, idx):
    sub = geo(dims[["Santé", "Emploi et revenus"]])
    out = dict(
        pearson=round(idx.corr(d.mpi_2024), 3), spearman=round(idx.corr(d.mpi_2024, method="spearman"), 3),
        pearson_sans_chevauchement=round(sub.corr(d.mpi_2024), 3), spearman_sans_chevauchement=round(sub.corr(d.mpi_2024, method="spearman"), 3),
    )
    out["dimensions"] = {n: round(dims[n].corr(d.mpi_2024, method="spearman"), 3) for n in DIMENSIONS}
    return out


def geometry(d):
    g = json.loads((RAW / "geoBoundaries-MAR-ADM2_simplified.geojson").read_text(encoding="utf-8"))
    idx = {key(v): c for c, v in d.nom.items()}
    feats, unmatched = [], []
    def round_c(c):
        return [round(c[0], 3), round(c[1], 3)] if isinstance(c[0], (int, float)) else [round_c(x) for x in c]
    for f in g["features"]:
        name = f["properties"]["shapeName"]
        k = key(name)
        code = idx.get(k)
        if code is None:
            unmatched.append((name, k))
            continue
        feats.append(dict(type="Feature", properties=dict(code=int(code)),
                          geometry=dict(type=f["geometry"]["type"], coordinates=round_c(f["geometry"]["coordinates"]))))
    assert not unmatched and len({f["properties"]["code"] for f in feats}) == 75, unmatched
    return dict(type="FeatureCollection", features=feats)


def main():
    d = poverty(enterprises(health(census())))
    assert d[IDS].notna().all().all(), d[IDS].isna().sum()
    bounds(d)
    s, dims = scores(d)
    idx = geo(dims)
    res, pca_w, stab = robustness(d, dims, idx)
    val = validation(d, dims, idx)
    ctx, ene = context(d)

    # Test des séries d'emploi du portail : la région comble les provinces absentes.
    alt = d.copy()
    e = ene["chomage"]["2024"].reindex(d.index)
    alt["chomage"] = e.fillna(e.groupby(d.region_code).transform("mean"))
    inds = [dict(i) for i in INDICATORS]
    for i in inds:
        if i["id"] == "chomage":
            i["L"], i["U"] = np.percentile(alt.chomage, 5), np.percentile(alt.chomage, 95)
    alt_idx = geo(scores(alt, inds)[1])
    res.append(compare(idx, alt_idx, "Chômage de l'enquête emploi (data.gov.ma) au lieu du RGPH"))
    val["chomage_portail_pauvrete"] = round(ene["chomage"]["2024"].reindex(d.index).corr(d.mpi_2024, method="spearman"), 3)
    val["emploi_portail_pauvrete"] = round(ene["emploi"]["2024"].reindex(d.index).corr(d.mpi_2024, method="spearman"), 3)
    val["activite_portail_pauvrete"] = round(ene["activite"]["2024"].reindex(d.index).corr(d.mpi_2024, method="spearman"), 3)
    val["chomage_rgph_pauvrete"] = round(d.chomage.corr(d.mpi_2024, method="spearman"), 3)
    val["indice_avec_chomage_portail"] = round(alt_idx.corr(d.mpi_2024, method="spearman"), 3)
    val["secondaire_10k_pauvrete"] = round(ctx.secondaire_10k.corr(d.mpi_2024, method="spearman"), 3)
    val["hop_100k_pauvrete"] = round(ctx.hop_100k.corr(d.mpi_2024, method="spearman"), 3)
    val["jeunes_100k_pauvrete"] = round(ctx.jeunes_100k.corr(d.mpi_2024, method="spearman"), 3)
    ctx.round(3).join(d.nom).to_csv(OUT / "rafah_contexte.csv", encoding="utf-8-sig", index_label="code_hcp")

    t = d.drop(columns=[c for c in d.columns if c.startswith("_")]).copy()
    t["rafah"] = idx.round(1)
    t["rang"] = idx.rank(ascending=False, method="min").astype(int)
    t["ecart_moyenne"] = (idx - idx.mean()).round(1)
    t["dimension_faible"] = dims.idxmin(axis=1)
    for n in DIMENSIONS:
        t["D_" + n] = dims[n].round(1)
    t = t.join(stab)
    t.sort_values("rang").to_csv(OUT / "rafah_provinces.csv", encoding="utf-8-sig", index_label="code_hcp", float_format="%.3f")
    s.round(2).to_csv(OUT / "rafah_scores_indicateurs.csv", encoding="utf-8-sig", index_label="code_hcp")

    meta = [{k: v for k, v in i.items() if k not in ("low", "high", "best", "worst")} for i in INDICATORS]
    for m in meta:
        m["L"], m["U"] = round(m["L"], 3), round(m["U"], 3)
        m["bornes"] = m["cible"] or "centiles 5-95 (2024)"
    provinces = []
    for c, r in d.iterrows():
        status = {i: ("calculé" if i in CALCULATED else "publié") for i in IDS}
        reasons = []
        if r._imput_medecins:
            status["medecins"] = "imputé"
            reasons.append("Médecins : valeur régionale utilisée")
        if r.lits == 0:
            status["lits"] = "déduit"
            reasons.append("Lits : 0 déduit de l'absence d'hôpital dans la liste du ministère")
        if r._enclavement_na:
            status["enclavement"] = "convention"
        small = r.population < 100000
        if small:
            reasons.append("Moins de 100 000 habitants : ratios instables")
        lo, hi = int(round(stab.rang_p05[c])), int(round(stab.rang_p95[c]))
        if hi - lo >= 15:
            reasons.append(f"Rang sensible aux pondérations : {lo} à {hi}")
        fiab = "Prudence" if r._imput_medecins or small else "Moyenne" if reasons else "Élevée"
        provinces.append(dict(code=int(c), nom=r.nom, type=r.type, region=r.region, population=int(r.population), status=status, fiab=fiab, fiabRaisons=reasons,
                              v={i: round(float(r[i]), 3) for i in IDS}, mpi24=round(r.mpi_2024, 1), mpi14=round(r.mpi_2014, 1),
                              ctx={k: (None if pd.isna(x) else round(float(x), 3)) for k, x in ctx.loc[c].items()},
                              ene={k: [None if (c not in s.index or pd.isna(x)) else float(x) for x in (s.loc[c] if c in s.index else [None] * 9)] for k, s in ene.items()},
                              rangP05=int(round(stab.rang_p05[c])), rangP95=int(round(stab.rang_p95[c])),
                              flags=[f for f, on in [("Médecins : valeur régionale imputée", r._imput_medecins),
                                                     ("Aucun hôpital recensé dans la province (0 lit)", r.lits == 0),
                                                     ("Enclavement : sans objet pour le HCP, compté 0 km", r._enclavement_na)] if on]))
    (OUT / "rafah.json").write_text(json.dumps(dict(dimensions=DIMENSIONS, indicators=meta, provinces=provinces, validation=val, robustness=res, pca=pca_w), ensure_ascii=False), encoding="utf-8")
    (OUT / "provinces.geojson").write_text(json.dumps(geometry(d), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    pd.DataFrame(meta).to_csv(OUT / "rafah_metadonnees.csv", encoding="utf-8-sig", index=False)
    pd.DataFrame([dict(code_hcp=p["code"], province=p["nom"], fiabilite=p["fiab"], raisons=" ; ".join(p["fiabRaisons"])) for p in provinces]).to_csv(OUT / "rafah_fiabilite.csv", encoding="utf-8-sig", index=False)
    pd.DataFrame([dict(fichier=p.relative_to(RAW).as_posix(), octets=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                  for p in sorted(RAW.rglob("*")) if p.is_file()]).to_csv(OUT / "sources_empreintes.csv", index=False)
    print("Fiabilité :", pd.Series([p["fiab"] for p in provinces]).value_counts().to_dict())
    print("Prudence :", [p["nom"] for p in provinces if p["fiab"] == "Prudence"])

    sys.stdout.reconfigure(encoding="utf-8")
    print(d[IDS].describe().T[["min", "mean", "max"]].round(2))
    print(pd.DataFrame(meta)[["id", "sens", "L", "U", "bornes"]])
    show = ["nom", "population", "rafah", "dimension_faible", "mpi_2024"]
    print(t.sort_values("rang")[show].head(10).to_string())
    print(t.sort_values("rang")[show].tail(12).to_string())
    print("Moyenne", round(idx.mean(), 1), "min", round(idx.min(), 1), "max", round(idx.max(), 1))
    print(dims.describe().T[["min", "mean", "max"]].round(1))
    print(json.dumps(val, ensure_ascii=False, indent=1))
    print(pd.DataFrame(res).to_string())
    print("ACP", pca_w)
    print("Enclavement sans objet:", d.nom[d._enclavement_na].tolist())
    print("Imputés:", d.nom[d._imput_medecins].tolist(), "| 0 lit:", d.nom[d.lits == 0].tolist())
    print(t.dimension_faible.value_counts().to_string())
    print(ctx[["hopitaux", "essp_2025", "primaires", "colleges", "lycees", "primaires_2023", "colleges_2023", "lycees_2023", "maisons_jeunes", "centres_femmes", "centres_handicap", "unites_enfance"]].sum().to_string())
    print("Provinces à zéro :", {k: d.nom[ctx[k] == 0].tolist() for k in ["hopitaux", "colleges", "lycees", "maisons_jeunes"]})


if __name__ == "__main__":
    main()
