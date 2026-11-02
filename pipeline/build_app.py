"""Construit le site statique dans app/ à partir de site/ et des résultats calculés."""
import html
import json
import math
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
SITE, APP, OUT = ROOT / "site", ROOT / "app", ROOT / "data" / "processed"
DATA = json.loads((OUT / "rafah.json").read_text(encoding="utf-8"))
GEO_TEXT = (OUT / "provinces.geojson").read_text(encoding="utf-8")
CSS = (SITE / "site.css").read_text(encoding="utf-8")
FONTS = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=Reem+Kufi:wght@500&display=swap">'
HEAD = '<!doctype html>\n<html lang="fr"><head><meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n<meta name="claude:viewport-fit-sides" content="cover">\n'
NAV = [("index", "Accueil"), ("comprendre", "Comprendre Rafah"), ("explorer", "Explorer"), ("indicateurs", "Indicateurs"), ("analyses", "Analyses"),
       ("explorer.html#simulateur", "Simulateur"), ("intelligence", "Intelligence"), ("pro", "Pro"), ("methodologie", "Méthodologie"), ("donnees", "Données"), ("publications", "Publications"), ("apropos", "À propos")]
DIM_TEXT = ["Médecins, centres de soins primaires et lits d'hôpital.", "Analphabétisme, scolarisation et niveau d'études.", "Chômage, emploi salarié et établissements économiques.",
            "Assainissement, électricité et logements sommaires.", "Eau courante, combustible de cuisson et collecte des déchets.", "Égalité femmes-hommes, activité des femmes et enclavement."]
DIM_IMG = [("dimension-sante", "Illustration d'un centre de santé et de son personnel"), ("dimension-education", "Illustration d'une salle de classe"), ("dimension-emploi", "Illustration d'une rue commerçante"),
           ("dimension-logement", "Illustration de logements raccordés à l'électricité et à l'assainissement"), ("dimension-eau", "Illustration d'un robinet d'eau courante"), ("dimension-inclusion", "Illustration de deux femmes en discussion autour d'une table")]
NOTES = {"salaries": "Remplace les salariés CNSS, publiés par région.", "enclavement": "Remplace les jeunes ni en emploi ni en études, non publiés par province.",
         "scolarisation": "Les 12-14 ans ne sont pas publiés.", "secondaire": "Toute la population publiée, pas seulement les 25 ans et plus.",
         "eau": "Eau courante dans le logement.", "electricite": "Électricité dans le logement.", "lits": "Public et privé, selon le lieu d'implantation.", "medecins": "Public et privé, selon le lieu d'exercice."}
fr = lambda x, d=1: f"{x:,.{d}f}".replace(",", " ").replace(".", ",")


def rafah(v):
    def n(x, i):
        r = (x - i["L"]) if i["sens"] > 0 else (i["U"] - x)
        return min(100, max(1, 1 + 99 * r / (i["U"] - i["L"])))
    dims = [sum(n(v[i["id"]], i) for i in DATA["indicators"] if i["dim"] == k) / 3 for k in range(6)]
    return math.exp(sum(map(math.log, dims)) / 6)


SCORES = {p["code"]: rafah(p["v"]) for p in DATA["provinces"]}
BY = {p["nom"]: p for p in DATA["provinces"]}


def nav(active):
    links = []
    for key, label in NAV:
        href = key if "." in key else key + ".html"
        cur = ' aria-current="page"' if key == active else ""
        links.append(f'<a href="{href}"{cur}>{label}</a>')
    return ('<header class="site-head"><div class="in"><a class="brand" href="index.html"><b>Rafah 2.0<span lang="ar" dir="rtl">رفاه</span></b>'
            '<small>Observatoire indépendant du bien-être territorial</small></a><nav class="site-nav" aria-label="Menu principal">' + "".join(links) + "</nav></div></header>"
            '<div class="notice">Projet de recherche indépendant, sans lien avec une administration. Les résultats ne sont pas des statistiques officielles.</div>')


FOOT = ('<footer class="site-foot"><div class="in"><p>Rafah 2.0. Mesurer, comprendre, agir. Prototype indépendant construit à partir de données publiques du HCP, du ministère de la Santé et de data.gov.ma. Données extraites le 2 novembre 2026.</p>'
        '<p><a href="apropos.html">À propos</a> · <a href="methodologie.html">Méthodologie</a> · <a href="donnees.html">Sources</a> · <a href="https://github.com/Driss1929/rafah2.0">GitHub</a></p></div></footer>')


def mini_map():
    """Carte statique de l'accueil, colorée par classe de score."""
    def color(s):
        return "var(--c" + str(1 + (s >= 25) + (s >= 40) + (s >= 55) + (s >= 70)) + ")"
    k = math.cos(math.radians(29))
    x0, y1 = -17.6, 36.1
    def pts(ring):
        return "M" + "L".join(f"{(c[0] - x0) * k * 6:.1f} {(y1 - c[1]) * 6:.1f}" for c in ring) + "Z"
    paths = []
    for f in json.loads(GEO_TEXT)["features"]:
        g = f["geometry"]
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        d = "".join(pts(r) for poly in polys for r in poly)
        paths.append(f'<path d="{d}" fill="{color(SCORES[f["properties"]["code"]])}"/>')
    w, h = (17.6 - .9) * k * 6, (36.1 - 20.6) * 6
    return f'<svg viewBox="0 0 {w:.0f} {h:.0f}" role="img" aria-label="Carte du Maroc par province, colorée selon le score Rafah">{"".join(paths)}</svg>'


def indicator_tables():
    out = []
    for k, d in enumerate(DATA["dimensions"]):
        rows = []
        for i in [x for x in DATA["indicators"] if x["dim"] == k]:
            note = f'<br><small>{NOTES[i["id"]]}</small>' if i["id"] in NOTES else ""
            rows.append(f'<tr><td>{i["label"]}{note}</td><td class="n">{"+" if i["sens"] > 0 else "−"}</td><td>{i["unit"]}</td><td>{i["source"]}</td><td>Province</td><td>{"Oui" if i["lever"] else "Non"}</td><td class="n">{fr(i["L"])} à {fr(i["U"])}</td><td>{i["bornes"]}</td></tr>')
        out.append(f'<section><h2>{d}</h2><p>{DIM_TEXT[k]}</p><div class="scroll"><table><tr><th>Indicateur</th><th class="n">Sens</th><th>Unité</th><th>Source et année</th><th>Niveau</th><th>Levier</th><th class="n">Bornes</th><th>Base des bornes</th></tr>{"".join(rows)}</table></div></section>')
    return "".join(out)


def robust():
    head = '<tr><th>Variante</th><th class="n">Corrélation de rang</th><th class="n">Écart de rang moyen</th><th class="n">15 derniers conservés</th></tr>'
    return head + "".join(f'<tr><td>{html.escape(r["scenario"])}</td><td class="n">{fr(r["spearman"], 2)}</td><td class="n">{fr(r["ecart_rang_moyen"])}</td><td class="n">{r["bas15_conserves"]} sur 15</td></tr>' for r in DATA["robustness"])


def region_profiles():
    def dims(p):
        out = []
        for k in range(6):
            s = []
            for i in [x for x in DATA["indicators"] if x["dim"] == k]:
                r = (p["v"][i["id"]] - i["L"]) if i["sens"] > 0 else (i["U"] - p["v"][i["id"]])
                s.append(min(100, max(1, 1 + 99 * r / (i["U"] - i["L"]))))
            out.append(sum(s) / 3)
        return out
    order = sorted({p["region"] for p in DATA["provinces"]}, key=lambda r: -sum(SCORES[p["code"]] * p["population"] for p in DATA["provinces"] if p["region"] == r) / sum(p["population"] for p in DATA["provinces"] if p["region"] == r))
    names = DATA["dimensions"]
    out = []
    for r in order:
        ps = sorted([p for p in DATA["provinces"] if p["region"] == r], key=lambda p: -SCORES[p["code"]])
        pop = sum(p["population"] for p in ps)
        mean = sum(SCORES[p["code"]] * p["population"] for p in ps) / pop
        dm = [sum(dims(p)[k] * p["population"] for p in ps) / pop for k in range(6)]
        weak, strong = names[dm.index(min(dm))], names[dm.index(max(dm))]
        rows = "".join(f'<tr><td><a href="intelligence.html#t{p["code"]}">{p["nom"]}</a></td><td class="n">{fr(SCORES[p["code"]])}</td>' + "".join(f'<td class="n">{fr(d)}</td>' for d in dims(p)) + f'<td>{p["fiab"]}</td></tr>' for p in ps)
        head = "<tr><th>Territoire</th><th class=\"n\">Rafah</th>" + "".join(f'<th class="n">{n}</th>' for n in names) + "<th>Fiabilité</th></tr>"
        out.append(f'<details class="card" style="margin-bottom:8px"><summary><b>{r}</b> : {fr(mean)}, {len(ps)} territoires, {fr(pop, 0)} habitants</summary><p>Écart interne : de {fr(SCORES[ps[-1]["code"]])} à {ps[-1]["nom"]} à {fr(SCORES[ps[0]["code"]])} à {ps[0]["nom"]}. Dimension moyenne la plus élevée : {strong}. La plus faible : {weak}.</p><div class="scroll"><table>{head}{rows}</table></div></details>')
    return "".join(out)


def pro_table():
    """Lignes de la maquette Pro : vraies valeurs de territoires pris en exemple."""
    def spark(vals):
        pts = [(i, v) for i, v in enumerate(vals) if v is not None]
        lo, hi = min(v for _, v in pts), max(v for _, v in pts)
        path = " ".join(f"{4 + i * 11:.0f},{22 - (v - lo) / ((hi - lo) or 1) * 18:.1f}" for i, v in pts)
        return f'<svg viewBox="0 0 96 26" width="96" height="26" role="img" aria-label="Chômage de 2017 à 2025"><polyline points="{path}" fill="none" stroke="var(--accent)" stroke-width="2"/></svg>'
    rows = ['<tr><th>Territoire</th><th class="n">Score Rafah</th><th class="n">Pauvreté HCP 2014</th><th class="n">Pauvreté HCP 2024</th><th>Chômage 2017-2025 (enquête emploi)</th><th>Fiabilité</th></tr>']
    for name in ["Figuig", "Sidi Bennour", "Taounate"]:
        p = BY[name]
        rows.append(f'<tr><td>{name}</td><td class="n">{fr(SCORES[p["code"]])}</td><td class="n">{fr(p["mpi14"])} %</td><td class="n">{fr(p["mpi24"])} %</td><td>{spark(p["ene"]["chomage"])}</td><td>{p["fiab"]}</td></tr>')
    return "".join(rows)


def audit_block():
    a = json.loads((OUT / "audit_independant.json").read_text(encoding="utf-8"))
    labels = {i["id"]: i["label"] for i in DATA["indicators"]}
    alpha = "".join(f'<tr><td>{d}</td><td class="n">{fr(v, 2)}</td></tr>' for d, v in a["alpha_cronbach"].items())
    var = "".join(f'<tr><td>{k}</td><td class="n">{fr(v["spearman"], 3)}</td><td class="n">{v["bas15"]} sur 15</td><td class="n">{fr(v["pauvrete"], 2)}</td></tr>' for k, v in a["variantes"].items())
    neg = " et ".join(f"« {labels[i]} »" for i in a["indicateurs_negatifs_dans_leur_dimension"])
    return f'''<section id="audit">
  <h2>Recalcul de contrôle</h2>
  <p>Un second script, sans code commun avec le calcul, repart des fichiers bruts et retrouve les colonnes par leur intitulé. Il a été écrit dans le cadre du même projet : c'est un contrôle de reproductibilité, pas une relecture externe.</p>
  <ul>
    <li>{a["territoires"]} territoires, {a["scores_indicateurs_compares"]} scores d'indicateurs, {a["scores_dimensions_compares"]} scores de dimensions et {a["indices_compares"]} indices comparés.</li>
    <li>Écart maximal sur l'indice : {fr(a["ecart_max_indice"], 2)} point, dû à l'arrondi à une décimale des résultats publiés. {a["rangs_differents"]} rang différent.</li>
    <li>Les {a["carte"]["chefs_lieux_testes"]} chefs-lieux, placés à partir de coordonnées approximatives, tombent dans le contour du bon territoire.</li>
  </ul>
  <h3>Autres normalisations testées</h3>
  <div class="scroll"><table><tr><th>Variante</th><th class="n">Corrélation de rang avec l'indice</th><th class="n">15 derniers conservés</th><th class="n">Corrélation avec la pauvreté</th></tr>{var}</table></div>
  <h3>Cohérence des dimensions</h3>
  <p>Certaines dimensions réunissent des aspects différents, et leur alpha de Cronbach reste faible. Dans ce type d'indice, un alpha faible n'invalide pas la dimension, mais il montre que ses indicateurs ne mesurent pas une seule et même chose. Deux indicateurs, {neg}, évoluent même en sens inverse du reste de leur dimension. Les causes restent à étudier.</p>
  <div class="scroll" style="max-width:420px"><table><tr><th>Dimension</th><th class="n">Alpha de Cronbach</th></tr>{alpha}</table></div>
  <h3>Redondance</h3>
  <p>{len(a["paires_redondantes"])} paires d'indicateurs ont une corrélation de rang d'au moins 0,8, la plus forte étant de {fr(a["paires_redondantes"][0][2], 2)} entre « {labels[a["paires_redondantes"][0][0]]} » et « {labels[a["paires_redondantes"][0][1]]} ». Ces conditions de vie vont souvent de pair, en lien avec l'urbanisation, ce qui peut donner plus de poids à cet écart ville-campagne. Aucun indicateur n'a été retiré à ce stade.</p>
  <p>La distance à la route mesure l'accessibilité physique plus que l'inclusion sociale. Sans elle, le classement reste proche, mais 3 des 15 derniers territoires changent : ce choix reste à discuter avec des relecteurs.</p>
</section>'''


def fill(text):
    low, high = min(SCORES, key=SCORES.get), max(SCORES, key=SCORES.get)
    names = {p["code"]: p["nom"] for p in DATA["provinces"]}
    sb, fi, val = BY["Sidi Bennour"], BY["Figuig"], DATA["validation"]
    values = {"min": fr(SCORES[low]), "max": fr(SCORES[high]), "min_nom": names[low], "max_nom": names[high],
              "sb": fr(SCORES[sb["code"]]), "fi": fr(SCORES[fi["code"]]), "sb_mpi": fr(sb["mpi24"]), "fi_mpi": fr(fi["mpi24"]), "sb_eau": fr(sb["v"]["eau"]), "sb_dechets": fr(sb["v"]["dechets"]),
              "sp": fr(val["spearman"], 2), "sp2": fr(val["spearman_sans_chevauchement"], 2), "chom_portail": fr(val["chomage_portail_pauvrete"], 2), "chom_rgph": fr(val["chomage_rgph_pauvrete"], 2),
              "dim_cards": "".join(f'<div class="card dim-card"><img src="images/{DIM_IMG[k][0]}.svg" alt="{DIM_IMG[k][1]}" width="640" height="400" loading="lazy"><h3>{k + 1:02d}. {d}</h3><p>{DIM_TEXT[k]}</p></div>' for k, d in enumerate(DATA["dimensions"]))}
    for key, fn in [("mini_map", mini_map), ("indicator_tables", indicator_tables), ("robust", robust), ("audit_block", audit_block), ("pro_table", pro_table), ("region_profiles", region_profiles)]:
        if "{{" + key + "}}" in text:
            values[key] = fn()
    if "{{geo_json}}" in text:
        values["geo_json"] = GEO_TEXT.replace("</", "<\\/")
    if "{{data_json}}" in text:
        values["data_json"] = json.dumps(DATA, ensure_ascii=False).replace("</", "<\\/")
    text = re.sub(r"\{\{(\w+)\}\}", lambda m: str(values[m[1]]), text)
    return text


def main():
    for page in sorted((SITE / "pages").glob("*.html")):
        src = page.read_text(encoding="utf-8")
        title = re.match(r"<!-- title: (.*?) -->", src)[1]
        body = fill(src.split("-->", 1)[1])
        extra = '<link rel="stylesheet" href="vendor/maplibre-gl.css">' if page.stem == "carte-maplibre" else ""
        (APP / page.name).write_text(f'{HEAD}<title>{title}</title>{FONTS}{extra}<style>{CSS}</style></head><body>{nav(page.stem)}<main class="page">{body}</main>{FOOT}</body></html>\n', encoding="utf-8")
    ex = (SITE / "explorer.template.html").read_text(encoding="utf-8")
    for mark, value in [("__NAV__", nav("explorer")), ("__FOOT__", FOOT), ("__SITECSS__", CSS), ("__FONTS__", FONTS),
                        ("__DATA__", json.dumps(DATA, ensure_ascii=False).replace("</", "<\\/")), ("__GEO__", GEO_TEXT.replace("</", "<\\/"))]:
        ex = ex.replace(mark, value)
    (APP / "explorer.html").write_text("<!doctype html>\n" + ex, encoding="utf-8")
    shutil.copytree(SITE / "images", APP / "images", dirs_exist_ok=True)
    dl = APP / "donnees"
    dl.mkdir(exist_ok=True)
    for f in ["rafah_provinces", "rafah_scores_indicateurs", "rafah_metadonnees", "rafah_contexte", "rafah_fiabilite", "audit_territoires", "sources_empreintes", "provenance_sources", "provenance_indicateurs", "data_sources_registry"]:
        shutil.copy(OUT / f"{f}.csv", dl / f"{f}.csv")
    sizes = {p.name: p.stat().st_size // 1024 for p in sorted(APP.glob("*.html"))}
    print("Pages (Ko) :", sizes)


if __name__ == "__main__":
    main()
