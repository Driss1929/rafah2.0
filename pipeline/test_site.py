"""Contrôle du site construit dans app/ : liens internes, ancres, marqueurs oubliés, mention d'indépendance.

Usage : python test_site.py [racine_du_projet]
"""
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
APP = ROOT / "app"
pages = {p.name: p.read_text(encoding="utf-8") for p in APP.glob("*.html")}
assert {"index.html", "explorer.html", "analyses.html", "indicateurs.html", "methodologie.html", "donnees.html", "comprendre.html", "apropos.html"} <= set(pages)
problems = []
for name, text in pages.items():
    # Les données et le script peuvent contenir de faux liens : on ne lit que le balisage visible.
    markup = re.sub(r"<script\b.*?</script>", "", text, flags=re.S)
    if "{{" in markup or re.search(r"__[A-Z]+__", markup):
        problems.append(f"{name} : marqueur non remplacé")
    if "Projet de recherche indépendant" not in markup:
        problems.append(f"{name} : mention d'indépendance absente")
    for src in set(re.findall(r'<(?:script|img) src="([^"]+)"', text)):
        if not re.match(r"https?:", src) and not (APP / src).exists():
            problems.append(f"{name} : script absent {src}")
    for href in set(re.findall(r'href="([^"]+)"', markup)):
        if re.match(r"https?:", href):
            continue
        target, _, anchor = href.partition("#")
        path = APP / target if target else APP / name
        if not path.exists():
            problems.append(f"{name} : lien cassé {href}")
        elif anchor and path.suffix == ".html" and f'id="{anchor}"' not in path.read_text(encoding="utf-8"):
            problems.append(f"{name} : ancre absente {href}")
print("\n".join(problems) or f"{len(pages)} pages contrôlées : aucun problème")
sys.exit(1 if problems else 0)
