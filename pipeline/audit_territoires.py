"""Compare les 75 territoires de Rafah aux monographies régionales de la DGCT.

Listes relevées dans la section « Cadre administratif » de chaque monographie (édition 2015).
Usage : python audit_territoires.py [racine_du_projet]
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
BASE = "https://collectivites-territoriales.gov.ma/sites/default/files/pnct/"
# Région : (fichier source, préfectures, provinces). Noms écrits comme dans la monographie.
OFFICIEL = {
    "Tanger-Tétouan-Al Hoceima": ("2021-01/MONOGRAPHIE%20DE%20LA%20REGION%20DE%20TANGER%20TETOUAN_fr.pdf", ["Tanger-Assilah", "M'Diq-Fnideq"], ["Al Hoceima", "Chefchaouen", "Fahs-Anjra", "Larache", "Ouezzane", "Tétouan"]),
    "Oriental": ("2021-01/MONOGRAPHIE%20DE%20LA%20REGION%20DE%20L%27ORIENTAL_fr.pdf", ["Oujda-Angad"], ["Berkane", "Taourirt", "Jerada", "Figuig", "Driouch", "Guercif", "Nador"]),
    "Fès-Meknès": ("2021-01/MONOGRAPHIE%20DE%20LA%20REGION%20DE%20FES%20MEKNES_fr.pdf", ["Fès", "Meknès"], ["Boulemane", "El Hajeb", "Ifrane", "Moulay Yaâcoub", "Sefrou", "Taounate", "Taza"]),
    "Rabat-Salé-Kénitra": ("2021-01/MONOGRAPHIE%20DE%20LA%20REGION%20DE%20RABAT%20SALE%20%20KENITRA%20FR.pdf", ["Rabat", "Salé", "Skhirate-Témara"], ["Kénitra", "Khémisset", "Sidi Kacem", "Sidi Slimane"]),
    "Béni Mellal-Khénifra": ("2021-01/MONOGRAPHIE%20DE%20LA%20REGION%20DE%20%20BENI%20MELLAL%20KHNIFRA%20FR.pdf", [], ["Azilal", "Béni Mellal", "Fquih Ben Salah", "Khénifra", "Khouribga"]),
    "Casablanca-Settat": ("2021-01/MONOGRAPHIE%20DE%20LA%20REGION%20DE%20CASABLANCA%20%20SETTAT_fr.pdf", ["Casablanca", "Mohammedia"], ["Settat", "El Jadida", "Ben Slimane", "Mediouna", "Nouaceur", "Berrechid", "Sidi Bennour"]),
    "Marrakech-Safi": ("2021-07/MONOGRAPPHIE%20DE%20LA%20REGION%20DE%20MARRAKECH%20SAFI.pdf", ["Marrakech"], ["Chichaoua", "Al Haouz", "El Kelâa des Sraghna", "Essaouira", "Rehamna", "Safi", "Youssoufia"]),
    "Drâa-Tafilalet": ("2021-01/MONOGRAPHIE%20DE%20LA%20REGION%20DE%20DRAA%20TAFILALET%20FR.pdf", [], ["Errachidia", "Midelt", "Tinghir", "Ouarzazate", "Zagora"]),
    "Souss-Massa": ("2021-01/MONOGRAPPHIE%20DE%20LA%20REGION%20DE%20SOUSS%20MASSA%20FR.pdf", ["Agadir-Ida-Ou-Tanane", "Inezgane-Ait Melloul"], ["Chtouka-Ait Baha", "Taroudannt", "Tata", "Tiznit"]),
    "Guelmim-Oued Noun": ("2021-01/MONOGRAPHIE%20DE%20LA%20REGION%20DE%20GUELMIM%20OUED%20NOUN%20FR_0.pdf", [], ["Guelmim", "Sidi Ifni", "Tan-Tan", "Assa Zag"]),
    "Laâyoune-Sakia El Hamra": ("2021-01/MONOGRAPHIE%20DE%20LA%20REGION%20DE%20LAAYOUNE%20SAKIA%20EL%20HAMRA%20FR.pdf", [], ["Boujdour", "Es-Smara", "Laâyoune", "Tarfaya"]),
    "Dakhla-Oued Ed-Dahab": ("2021-01/MONOGRAPHIE%20DE%20LA%20REGION%20DE%20DAKHLA_OUED%20EDDAHAB%20FR.pdf", [], ["Oued Eddahab", "Aousserd"]),
}
# Nom Rafah (repris du RGPH 2024) -> nom de la monographie, quand ils diffèrent.
GRAPHIES = {"M'diq-Fnideq": "M'Diq-Fnideq", "Moulay Yacoub": "Moulay Yaâcoub", "Mohammadia": "Mohammedia", "Benslimane": "Ben Slimane", "Médiouna": "Mediouna",
            "El Kelâa Des-Sraghna": "El Kelâa des Sraghna", "Inezgane-Aït Melloul": "Inezgane-Ait Melloul", "Chtouka-Aït Baha": "Chtouka-Ait Baha",
            "Assa-Zag": "Assa Zag", "Es-Semara": "Es-Smara", "Oued Ed-Dahab": "Oued Eddahab"}

provinces = json.loads((ROOT / "data" / "processed" / "rafah.json").read_text(encoding="utf-8"))["provinces"]
assert len(OFFICIEL) == 12 and sum(len(v[1]) + len(v[2]) for v in OFFICIEL.values()) == 75
rows, seen = [], set()
for p in provinces:
    src, pref, prov = OFFICIEL[p["region"]]
    name = GRAPHIES.get(p["nom"], p["nom"])
    kind = "Préfecture" if name in pref else "Province" if name in prov else None
    assert kind, f"{p['nom']} absent de la monographie de {p['region']}"
    assert kind == p["type"], f"{p['nom']} : {kind} / {p['type']}"
    seen.add((p["region"], name))
    obs = "Graphie différente, même territoire" if name != p["nom"] else ""
    if p["nom"] == "Marrakech":
        obs = "La monographie annonce « huit provinces et une préfecture » mais en énumère sept et une"
    rows.append(dict(code_hcp=p["code"], nom_rafah=p["nom"], nom_monographie=name, region=p["region"], type=kind, source=BASE + src, statut="Vérifié", observation=obs))
assert len(seen) == 75 and len({r["code_hcp"] for r in rows}) == 75
with open(ROOT / "data" / "processed" / "audit_territoires.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)
print(f"{len(rows)} territoires vérifiés, {sum('Graphie' in r['observation'] for r in rows)} graphies différentes, aucun manquant ni doublon")
