"""Dessine les illustrations originales du site dans site/images/. Usage : python make_images.py [racine]"""
import math
import random
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
OUT = ROOT / "site" / "images"
OUT.mkdir(parents=True, exist_ok=True)
NAVY, BLUE, SKY, GOLD, SAND, CLAY, TEAL, GREEN, WHITE, INK = "#0f2d55", "#2f6aa8", "#cfe2f3", "#d9a441", "#f1e3c6", "#c8693f", "#0f6b76", "#6f9e5b", "#ffffff", "#14213a"


def rect(x, y, w, h, fill, r=0, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" {extra}/>'


def circle(x, y, r, fill):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"/>'


def path(d, fill="none", stroke=None, sw=0):
    s = f' stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"' if stroke else ""
    return f'<path d="{d}" fill="{fill}"{s}/>'


def arch(x, y, w, h, fill):
    """Arc outrepassé simplifié, base à y + h."""
    return path(f"M{x} {y + h}V{y + w * .55}A{w / 2} {w * .55} 0 0 1 {x + w} {y + w * .55}V{y + h}Z", fill)


def person(x, y, s, robe, scarf, skin="#b98a68"):
    """Silhouette sans visage, pour ne représenter personne de réel."""
    return (path(f"M{x - 24 * s} {y + 90 * s}C{x - 24 * s} {y + 30 * s} {x - 15 * s} {y + 20 * s} {x} {y + 20 * s}C{x + 15 * s} {y + 20 * s} {x + 24 * s} {y + 30 * s} {x + 24 * s} {y + 90 * s}Z", robe)
            + circle(x, y, 16 * s, scarf) + circle(x, y + 2 * s, 10 * s, skin))


def save(name, w, h, title, body):
    (OUT / f"{name}.svg").write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img"><title>{title}</title>{body}</svg>\n', encoding="utf-8")


def territoires():
    random.seed(7)
    colors = ["#d9c07f", "#a9bd72", "#7f9f5b", "#c9a15f", "#e0cf9a", "#92ad66"]
    b = rect(0, 0, 300, 300, "#a9bd72")
    for gx in range(6):
        for gy in range(4):
            x, y, dx = gx * 52 - 8, 150 + gy * 40, random.randint(-8, 8)
            b += path(f"M{x + dx} {y}h54l{random.randint(-8, 8)} 42h-54z", random.choice(colors), "#f1e3c6", 1)
    for gx in range(16):
        for gy in range(7):
            if random.random() < .86 - gy * .05:
                b += rect(gx * 19 + 2, gy * 21 + 4, 15, 16, random.choice(["#d7b48a", "#c8693f", "#e6d2b0", "#b9794f"]))
    b += path("M0 168C60 150 120 186 180 158S270 140 300 150", "none", "#f6efe0", 7)
    b += path("M150 300C145 250 165 215 150 160", "none", "#f6efe0", 5)
    return save("pourquoi-disparites", 300, 300, "Ville et champs vus du ciel", b)


def economie():
    b = rect(0, 0, 300, 300, SKY)
    b += rect(0, 195, 300, 105, SAND)
    # Unité de soins mobile et file de personnes, évoquant les services au-delà du revenu.
    b += rect(150, 118, 125, 88, WHITE, 6) + rect(150, 158, 125, 12, TEAL) + rect(170, 132, 34, 22, SKY, 2) + rect(226, 126, 14, 42, TEAL) + rect(216, 140, 34, 14, TEAL)
    b += circle(176, 212, 13, INK) + circle(250, 212, 13, INK) + circle(176, 212, 5, "#ddd") + circle(250, 212, 5, "#ddd")
    for x, c, sc in [(40, BLUE, CLAY), (78, CLAY, GOLD), (114, GREEN, NAVY)]:
        b += person(x, 150, 1, c, sc)
    b += path("M30 60h60M60 30v60", stroke=WHITE, sw=0) + circle(250, 55, 24, GOLD)
    return save("pourquoi-economie", 300, 300, "Services de santé de proximité", b)


def donnees():
    random.seed(4)
    b = rect(0, 0, 300, 300, NAVY)
    for _ in range(46):
        x, y = random.randint(14, 120), random.randint(20, 280)
        b += rect(x, y, random.randint(8, 22), 5, random.choice([SKY, GOLD, BLUE, WHITE]), 2, 'opacity=".75"')
    b += path("M126 150h34m-12-12 12 12-12 12", stroke=GOLD, sw=6)
    # Grille abstraite plutôt qu'une silhouette : les vrais contours sont sur la carte du site.
    ramp = ["#b5431d", "#e59a58", "#e6d79c", "#68b3a4", "#0f6b76"]
    for gx in range(5):
        for gy in range(6):
            b += rect(172 + gx * 23, 78 + gy * 25, 20, 22, random.choice(ramp), 3)
    return save("pourquoi-donnees", 300, 300, "Des données dispersées réunies en une lecture territoriale", b)


def sante():
    b = rect(0, 0, 640, 400, "#dfeaf3") + rect(0, 320, 640, 80, "#c7d3dd")
    b += rect(70, 90, 500, 240, WHITE, 6) + rect(70, 90, 500, 34, TEAL, 6)
    for x in (110, 210, 410, 510):
        for y in (150, 230):
            b += rect(x, y, 58, 50, SKY, 3)
    b += arch(285, 200, 70, 130, BLUE) + rect(292, 142, 56, 42, WHITE, 4, f'stroke="{TEAL}" stroke-width="3"') + rect(314, 148, 12, 30, TEAL) + rect(305, 157, 30, 12, TEAL)
    for x, c, sc in [(180, TEAL, NAVY), (235, BLUE, TEAL), (450, WHITE, BLUE)]:
        b += person(x, 245, 1, c, sc)
    return save("dimension-sante", 640, 400, "Centre de santé et personnel soignant", b)


def education():
    b = rect(0, 0, 640, 400, "#f2ece0") + rect(0, 310, 640, 90, "#c9b796")
    b += rect(180, 50, 280, 130, "#2f5d50", 4, f'stroke="{CLAY}" stroke-width="7"')
    b += path("M210 90h110M210 115h170M210 140h80", stroke=WHITE, sw=4) + path("M395 80l20 45h-40z", "none", GOLD, 3)
    b += rect(30, 70, 110, 130, SKY, 4, f'stroke="{WHITE}" stroke-width="6"') + rect(505, 70, 100, 110, GOLD, 4, 'opacity=".7"')
    for row, y, s in ((0, 215, .85), (1, 245, 1.1)):
        for i in range(4 if row == 0 else 3):
            x = (130 + i * 125) if row == 0 else (150 + i * 170)
            b += person(x, y, s, [CLAY, BLUE, GOLD, GREEN][(i + row) % 4], [NAVY, CLAY, TEAL, BLUE][(i + row) % 4])
            b += rect(x - 42 * s, y + 62 * s, 84 * s, 10 * s, "#8a5a33", 2)
    return save("dimension-education", 640, 400, "Salle de classe", b)


def emploi():
    b = rect(0, 0, 640, 400, "#a9d3ea") + rect(0, 300, 640, 100, "#d8c3a0")
    b += rect(0, 90, 215, 215, "#e9d9bb") + rect(425, 70, 215, 235, "#efe0c4") + rect(190, 130, 260, 170, "#f5ead2")
    for x in (25, 90, 150, 455, 520, 585):
        b += arch(x, 120, 36, 62, "#7e5a3c")
    b += arch(285, 170, 70, 130, TEAL)
    for x, w, c in [(0, 190, CLAY), (450, 190, BLUE)]:
        b += path(f"M{x} 205h{w}l-14 34h-{w - 28}z", c) + rect(x + 14, 239, w - 28, 62, "#6d4c33")
        for i in range(5):
            b += rect(x + 24 + i * (w - 48) / 5, 262, 22, 28, [GOLD, GREEN, CLAY, SAND, TEAL][i])
    for x, y, s, c, sc in [(235, 245, 1, CLAY, NAVY), (390, 235, .95, NAVY, GOLD), (320, 265, 1.15, BLUE, CLAY)]:
        b += person(x, y, s, c, sc)
    return save("dimension-emploi", 640, 400, "Rue commerçante", b)


def logement():
    b = rect(0, 0, 640, 400, SKY) + rect(0, 300, 640, 100, "#b6a27c") + circle(570, 62, 34, GOLD)
    for x, y, w, h, c in [(50, 160, 150, 145, "#efd9b4"), (200, 120, 170, 185, "#e3bf8e"), (370, 175, 130, 130, "#f1e3c6")]:
        b += rect(x, y, w, h, c) + rect(x + 22, y + 24, 34, 40, BLUE, 2) + rect(x + w - 56, y + 24, 34, 40, BLUE, 2) + arch(x + w / 2 - 20, y + h - 62, 40, 62, CLAY)
    b += rect(540, 90, 8, 215, "#5b4632") + rect(516, 110, 56, 6, "#5b4632")
    b += path("M516 112C400 170 300 100 200 120M572 112C600 130 620 130 640 125", stroke=INK, sw=2)
    b += path("M552 150l-14 26h12l-8 22 22-30h-13l9-18z", GOLD)
    b += rect(0, 345, 640, 14, "#6d7f8c", 7) + rect(120, 305, 12, 42, "#6d7f8c") + rect(290, 305, 12, 42, "#6d7f8c") + rect(430, 305, 12, 42, "#6d7f8c")
    return save("dimension-logement", 640, 400, "Logements raccordés à l'électricité et à l'assainissement", b)


def eau():
    b = rect(0, 0, 640, 400, "#e9f1f6") + rect(0, 300, 640, 100, BLUE)
    b += path("M0 310C80 295 160 325 240 310S400 295 480 310 600 325 640 310V400H0Z", "#4a8cc7")
    b += rect(60, 70, 190, 44, "#7d8791", 6) + rect(222, 60, 42, 76, "#5f6973", 6) + rect(228, 136, 30, 18, "#5f6973")
    b += path("M243 155C226 210 212 250 225 300H262C275 250 260 210 243 155Z", "#7fbbe6")
    random.seed(3)
    for _ in range(26):
        a = random.uniform(math.pi, 2 * math.pi)
        d = random.uniform(30, 150)
        x, y, r = 243 + math.cos(a) * d, 300 + math.sin(a) * d * .6, random.uniform(3, 8)
        b += path(f"M{x:.0f} {y - r * 1.8:.0f}C{x + r:.0f} {y:.0f} {x + r:.0f} {y + r:.0f} {x:.0f} {y + r:.0f}S{x - r:.0f} {y:.0f} {x:.0f} {y - r * 1.8:.0f}Z", "#a8d4f0")
    b += path("M395 95C440 165 480 205 480 250A85 85 0 0 1 310 250C310 205 350 165 395 95Z", TEAL) + path("M352 250A43 43 0 0 0 395 293", stroke=WHITE, sw=7)
    return save("dimension-eau", 640, 400, "Eau courante", b)


def inclusion():
    b = rect(0, 0, 640, 400, "#ece4d6") + rect(0, 310, 640, 90, "#b89a72")
    b += rect(390, 50, 190, 170, BLUE, 4) + path("M420 95h130M420 125h95M420 155h115", stroke=WHITE, sw=5) + rect(55, 70, 120, 100, GOLD, 4, 'opacity=".55"')
    b += person(235, 155, 1.8, GREEN, SAND) + person(420, 165, 1.7, CLAY, "#b77f8a")
    b += rect(150, 300, 340, 16, "#7e5a3c", 3) + rect(180, 316, 12, 84, "#6d4c33") + rect(448, 316, 12, 84, "#6d4c33") + rect(285, 286, 70, 14, WHITE, 2)
    return save("dimension-inclusion", 640, 400, "Deux femmes en discussion autour d'une table", b)


for draw in (territoires, economie, donnees, sante, education, emploi, logement, eau, inclusion):
    draw()
print(len(list(OUT.glob("*.svg"))), "illustrations écrites dans site/images")
