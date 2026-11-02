"""Insère les données calculées dans la page : app/template.html -> app/index.html."""
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
page = (ROOT / "app" / "template.html").read_text(encoding="utf-8")
for mark, name in [("__DATA__", "rafah.json"), ("__GEO__", "provinces.geojson")]:
    page = page.replace(mark, (ROOT / "data" / "processed" / name).read_text(encoding="utf-8").replace("</", "<\\/"))
(ROOT / "app" / "index.html").write_text(page, encoding="utf-8")
print(f"app/index.html : {len(page) // 1024} Ko")
