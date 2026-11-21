#!/usr/bin/env python3
"""Deterministic broadsheet renderer for the 21 November 2026 world-news image.

Draws a front-page broadsheet (masthead, dominant lead, 3x2 story grid with
flat-vector illustrations, an "also today" briefs band, a sport ticker and a
footer) entirely from Pillow primitives. No clock, randomness or network: two
runs write byte-identical PNGs. Every text block is measured with textbbox and
asserted to stay clear of the rule line beneath it, so nothing collides.
"""
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
M = 30                      # page margin
CW = W - 2 * M              # content width
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")

# --- palette (newsprint) ---
PAPER = (245, 240, 228)
INK = (26, 26, 26)
SOFT = (74, 70, 62)
RULE = (196, 186, 165)
RULE_DARK = (120, 110, 92)
RED = (168, 50, 50)
BLUE = (44, 95, 138)
GOLD = (176, 138, 60)
GREEN = (58, 125, 68)
PURPLE = (108, 74, 130)
TEAL = (40, 122, 120)
WHITE = (250, 248, 242)

_fc = {}
def font(name, size):
    key = (name, size)
    if key not in _fc:
        _fc[key] = ImageFont.truetype(os.path.join(FONT_DIR, name + ".ttf"), size)
    return _fc[key]

SERIF = "DejaVuSerif"
SERIFB = "DejaVuSerif-Bold"
SANS = "DejaVuSans"
SANSB = "DejaVuSans-Bold"
MONO = "DejaVuSansMono"

def wrap(text, f, maxw):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if f.getlength(trial) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def block(d, x, y, text, f, maxw, fill, leading=1.18, max_lines=None):
    """Draw wrapped text from top-left (x,y); return the bottom pixel y."""
    lines = wrap(text, f, maxw)
    if max_lines:
        lines = lines[:max_lines]
    lh = int(f.size * leading)
    cy = y
    for ln in lines:
        d.text((x, cy), ln, font=f, fill=fill, anchor="la")
        cy += lh
    # actual ink bottom of the last line
    if lines:
        bb = d.textbbox((x, cy - lh), lines[-1], font=f, anchor="la")
        return bb[3]
    return y

def rule(d, x0, x1, y, width=1, fill=RULE):
    d.rectangle([x0, y, x1, y + width - 1], fill=fill)

def vrule(d, x, y0, y1, width=1, fill=RULE):
    d.rectangle([x, y0, x + width - 1, y1], fill=fill)

def tag(d, x, y, text, color):
    f = font(SANSB, 11)
    d.text((x, y), text.upper(), font=f, fill=color, anchor="la")
    return d.textbbox((x, y), text.upper(), font=f, anchor="la")[3]

# ---------- flat-vector illustrations (geometric, consistent stroke) ----------
def ill_missile(d, x, y, w, h):
    import math
    base = y + h - 20
    # city skyline: buildings WITH windows so they read as buildings, not bars
    blds = [(x+16,22,40),(x+42,26,64),(x+72,20,48),(x+96,28,78),(x+128,22,34),(x+154,24,56)]
    for bx, bw, bh in blds:
        d.rectangle([bx, base - bh, bx + bw, base], fill=BLUE)
        for wy in range(base - bh + 6, base - 6, 12):
            for wx in range(bx + 4, bx + bw - 4, 9):
                d.rectangle([wx, wy, wx + 4, wy + 5], fill=PAPER)
    d.line([x + 10, base, x + w - 10, base], fill=INK, width=3)
    # missile: capsule body + cone nose + symmetric fins + exhaust, flying down-left
    tail = (x + w - 30, y + 26)
    nose = (x + 90, y + 84)
    ux, uy = nose[0]-tail[0], nose[1]-tail[1]
    L = math.hypot(ux, uy); ux, uy = ux/L, uy/L
    px, py = -uy, ux
    hw = 6
    b1 = (tail[0]+px*hw, tail[1]+py*hw); b2 = (tail[0]-px*hw, tail[1]-py*hw)
    n1 = (nose[0]+px*hw, nose[1]+py*hw); n2 = (nose[0]-px*hw, nose[1]-py*hw)
    d.polygon([b1, b2, n2, n1], fill=SOFT)
    tip = (nose[0]+ux*16, nose[1]+uy*16)
    d.polygon([n1, n2, tip], fill=RED)                      # warhead cone
    for s in (-1, 1):                                       # symmetric tail fins
        f1 = (tail[0]+s*px*hw, tail[1]+s*py*hw)
        f2 = (tail[0]-ux*15+s*px*17, tail[1]-uy*15+s*py*17)
        f3 = (tail[0]-ux*15, tail[1]-uy*15)
        d.polygon([f1, f2, f3], fill=SOFT)
    for s in (-4, 0, 4):                                    # exhaust flame
        d.line([(tail[0]-ux*2+s*px*0.5, tail[1]-uy*2+s*py*0.5),
                (tail[0]-ux*22+s*px, tail[1]-uy*22+s*py)], fill=GOLD, width=3)
    # interception burst ON the flight path, just ahead of the warhead
    ax, ay = nose[0]+ux*26, nose[1]+uy*26
    for a in range(0, 360, 30):
        r1, r2 = 6, 16
        d.line([ax + r1*math.cos(math.radians(a)), ay + r1*math.sin(math.radians(a)),
                ax + r2*math.cos(math.radians(a)), ay + r2*math.sin(math.radians(a))], fill=RED, width=3)
    d.ellipse([ax-4, ay-4, ax+4, ay+4], fill=GOLD)

def _box(x, y, w, h):
    s = min(w, h)
    return s, x + (w - s) / 2, y + (h - s) / 2

def ill_denmark(d, x, y, w, h):
    s, ox, oy = _box(x, y, w, h)
    def P(u, v): return (ox + u*s, oy + v*s)
    sw = max(2, int(s*0.03))
    # Dannebrog flag
    (fx0, fy0), (fx1, fy1) = P(0.08, 0.22), P(0.62, 0.78)
    d.rectangle([fx0, fy0, fx1, fy1], fill=RED, outline=INK, width=sw)
    fw, fh = fx1-fx0, fy1-fy0
    d.rectangle([fx0+fw*0.30, fy0, fx0+fw*0.42, fy1], fill=WHITE)
    d.rectangle([fx0, fy0+fh*0.42, fx1, fy0+fh*0.58], fill=WHITE)
    # shield
    sx, sy = P(0.68, 0.30)
    ss = s*0.26
    d.polygon([(sx,sy),(sx+ss,sy),(sx+ss,sy+ss*0.6),(sx+ss/2,sy+ss),(sx,sy+ss*0.6)], outline=BLUE, width=sw)
    d.line([sx+ss/2, sy+ss*0.15, sx+ss/2, sy+ss*0.75], fill=BLUE, width=sw)
    d.line([sx+ss*0.15, sy+ss*0.4, sx+ss*0.85, sy+ss*0.4], fill=BLUE, width=sw)

def ill_euro(d, x, y, w, h):
    import math
    s, ox, oy = _box(x, y, w, h)
    cx, cy = ox + s/2, oy + s/2
    sw = max(2, int(s*0.04))
    d.ellipse([cx-s*0.34, cy-s*0.34, cx+s*0.34, cy+s*0.34], outline=BLUE, width=sw)
    d.text((cx, cy), "€", font=font(SERIFB, max(10, int(s*0.46))), fill=BLUE, anchor="mm")
    for i in range(12):
        a = math.radians(i*30)
        sx, sy = cx + s*0.44*math.cos(a), cy + s*0.44*math.sin(a)
        r = max(1.5, s*0.025)
        d.ellipse([sx-r, sy-r, sx+r, sy+r], fill=GOLD)

def ill_sudan(d, x, y, w, h):
    s, ox, oy = _box(x, y, w, h)
    def P(u, v): return (ox + u*s, oy + v*s)
    sw = max(2, int(s*0.035))
    # territory outline
    d.polygon([P(0.18,0.28),P(0.55,0.14),P(0.84,0.32),P(0.80,0.72),P(0.45,0.86),P(0.16,0.66)], outline=GREEN, width=sw)
    # advance arrow
    a0, a1 = P(0.28,0.72), P(0.70,0.34)
    d.line([a0, a1], fill=RED, width=sw+1)
    d.polygon([a1, P(0.58,0.36), P(0.66,0.46)], fill=RED)
    # location pin
    px, py = P(0.50,0.50)
    r = s*0.06
    d.ellipse([px-r, py-r, px+r, py+r], fill=GOLD)

def ill_gavel(d, x, y, w, h):
    s, ox, oy = _box(x, y, w, h)
    def P(u, v): return (ox + u*s, oy + v*s)
    sw = max(2, int(s*0.04))
    d.rectangle([P(0.20,0.78), P(0.80,0.88)], fill=INK)                 # sound block
    d.line([P(0.38,0.62), P(0.62,0.34)], fill=SOFT, width=max(3,int(s*0.09)))  # handle
    (hx0, hy0), (hx1, hy1) = P(0.52, 0.16), P(0.86, 0.40)
    d.rectangle([hx0, hy0, hx1, hy1], fill=BLUE, outline=INK, width=sw)  # head
    d.line([P(0.24,0.72), P(0.56,0.72)], fill=GOLD, width=sw)

def ill_football(d, x, y, w, h):
    s, ox, oy = _box(x, y, w, h)
    cx, cy = ox + s/2, oy + s/2
    sw = max(2, int(s*0.035))
    d.ellipse([cx-s*0.42, cy-s*0.24, cx+s*0.42, cy+s*0.24], fill=(120,72,40), outline=INK, width=sw)
    d.line([cx-s*0.26, cy, cx+s*0.26, cy], fill=WHITE, width=sw)
    for i in range(-2, 3):
        d.line([cx+i*s*0.11, cy-s*0.07, cx+i*s*0.11, cy+s*0.07], fill=WHITE, width=sw)

def ill_tanker(d, x, y, w, h):
    s, ox, oy = _box(x, y, w, h)
    def P(u, v): return (ox + u*s, oy + v*s)
    sw = max(2, int(s*0.03))
    d.rectangle([P(0.12,0.50), P(0.88,0.72)], fill=BLUE, outline=INK, width=sw)   # hull
    d.rectangle([P(0.66,0.30), P(0.84,0.50)], fill=SOFT)                          # bridge
    d.rectangle([P(0.22,0.36), P(0.32,0.50)], fill=GOLD)                          # deck house
    d.line([P(0.08,0.80), P(0.92,0.80)], fill=TEAL, width=sw)
    d.line([P(0.14,0.88), P(0.86,0.88)], fill=TEAL, width=max(1,sw-1))
    d.polygon([P(0.40,0.12), P(0.46,0.26), P(0.34,0.26)], fill=RED)               # alert

ICONS = {"missile": ill_missile, "denmark": ill_denmark, "euro": ill_euro,
         "sudan": ill_sudan, "gavel": ill_gavel, "football": ill_football, "tanker": ill_tanker}

# ---------- content ----------
LEAD = {
    "tag": "MIDDLE EAST", "color": RED,
    "head": "Saudi coalition intercepts Houthi missiles over Riyadh",
    "deck": "Saudi Arabia issued and lifted emergency alerts for Riyadh for a third night as the "
            "Saudi-led coalition said it downed three ballistic missiles. The Houthis threatened Red "
            "Sea ports, a power station and the capital's financial centre after coalition strikes on "
            "Hodeidah port and Sanaa.",
    "icon": "missile",
}
GRID = [
    {"tag":"EUROPE","color":BLUE,"icon":"denmark",
     "head":"Denmark expels Russian attache over assassination plot",
     "body":"Danish intelligence says Moscow plotted to kill Ukrainian-American rapper Kyivstoner near Copenhagen; von der Leyen condemns."},
    {"tag":"EUROPE","color":BLUE,"icon":"euro",
     "head":"EU budget keeps Ukraine funding flat at €89bn",
     "body":"Costa's 2028-2034 proposal holds Ukraine support steady, far short of Kyiv's needs; leaders meet 26-27 Nov."},
    {"tag":"AFRICA","color":GREEN,"icon":"sudan",
     "head":"Sudan army advances in Darfur and Kordofan",
     "body":"SAF pushes against the RSF; the UN counts 2,230 civilians killed Jan-Oct, over 1,630 by drones."},
    {"tag":"ASIA","color":GOLD,"icon":"gavel",
     "head":"Nikhil Gupta gets 19 years for Pannun plot",
     "body":"A US court sentences Gupta for the foiled plot to kill Sikh separatist Gurpatwant Singh Pannun."},
    {"tag":"AMERICAS","color":PURPLE,"icon":"football",
     "head":"Patriots QB Drake Maye fractured fibula",
     "body":"Tests show a fractured right fibula; no surgery, but likely out deep into the season, per ESPN."},
    {"tag":"MIDDLE EAST","color":RED,"icon":"tanker",
     "head":"Oil tanker struck in Strait of Hormuz",
     "body":"Iranian attacks deter crossings; November oil flows through the strait fell about 20%."},
]
BRIEFS = [
    ("GAZA", RED, "IDF strike on a vehicle in Gaza City's Tel al-Hawa kills 3."),
    ("IRAN", RED, "FM Araqchi: enriched uranium must stay in Iran."),
    ("ITALY", BLUE, "Naples MED: Saudi, Turkey urge regional security cooperation."),
    ("ISRAEL", RED, "Woman dies in car explosion in Tira; two children hurt."),
    ("EGYPT", GREEN, "Egypt and Sudan sign a training and capacity-building MoU."),
    ("HORN", GREEN, "Ethiopia-Eritrea: artillery fire near disputed Badme."),
    ("GUINEA", GREEN, "Siguiri court jails 202 illegal miners for 3 years."),
    ("W.AFRICA", GREEN, "ECOWAS reaffirms its strategic partnership with the UN."),
    ("INDIA", GOLD, "First bullet train to begin operations in 2027."),
    ("INDIA", GOLD, "Air India suspends Jeddah flights to 24 Nov, Riyadh to 30 Nov."),
    ("USA", PURPLE, "New wildfires in Los Angeles and Riverside counties."),
    ("USA", PURPLE, "MLBPA rejects the league's international draft proposal."),
    ("USA", PURPLE, "NBA: Lakers edge Kings; Nets star beaten by brother's 35."),
    ("USA", PURPLE, "New Mexico: mother and two children killed by father."),
    ("OCEANIA", TEAL, "Australia host England in T20I at the MCG."),
    ("OCEANIA", TEAL, "Brisbane P-plater hits 5 pedestrians; all survive."),
    ("S.AMERICA", GOLD, "Copa Sudamericana final: Boca v Mineiro, Barranquilla."),
    ("S.AMERICA", GOLD, "M6.7 quake shakes central Peru; felt in Lima, no casualties."),
]
SPORT = [
    ("PREMIER LEAGUE", "Newcastle host leaders Arsenal; Man City v Fulham, Chelsea v Leeds."),
    ("FORMULA 1", "Las Vegas Grand Prix race day, cool and dry."),
    ("ATP FINALS", "Turin semifinals: Alcaraz v Shelton; Zverev v Medvedev."),
]

def render(out_path):
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    checks = []
    def ck(label, bottom, limit):
        checks.append((label, bottom, limit))
        assert bottom <= limit, f"COLLISION {label}: bottom {bottom} > limit {limit}"

    # ===== Masthead =====
    title_f = font(SERIFB, 47)
    title = "The World Ledger"
    tw = title_f.getlength(title)
    d.text(((W - tw) / 2, 22), title, font=title_f, fill=INK, anchor="la")
    title_bb = d.textbbox(((W - tw) / 2, 22), title, font=title_f, anchor="la")
    ck("masthead title", title_bb[3], 78)
    # date line centered
    date_f = font(SANSB, 15)
    dateline = "SATURDAY, 21 NOVEMBER 2026   ·   WORLD EDITION   ·   ONE DAY IN REVIEW"
    dw = date_f.getlength(dateline)
    d.text(((W - dw) / 2, 84), dateline, font=date_f, fill=SOFT, anchor="la")
    date_bb = d.textbbox(((W - dw) / 2, 84), dateline, font=date_f, anchor="la")
    ck("masthead date", date_bb[3], 104)
    rule(d, M, W - M, 110, 3, RULE_DARK)
    rule(d, M, W - M, 115, 1, RULE_DARK)

    # ===== Lead =====
    ly = 126
    tag(d, M, ly, LEAD["tag"], LEAD["color"])
    head_f = font(SERIFB, 29)
    hb = block(d, M, ly + 18, LEAD["head"], head_f, CW, INK, leading=1.12)
    ck("lead headline", hb, 208)
    # illustration left, deck right
    iy = 214
    iw, ih = 200, 132
    d.rectangle([M, iy, M + iw, iy + ih], outline=RULE, width=1)
    ICONS[LEAD["icon"]](d, M, iy, iw, ih)
    deck_x = M + iw + 22
    deck_w = CW - iw - 22
    deck_f = font(SANS, 16)
    db = block(d, deck_x, iy + 4, LEAD["deck"], deck_f, deck_w, SOFT, leading=1.3)
    ck("lead deck", db, iy + ih)
    rule(d, M, W - M, 356, 2, RULE_DARK)

    # ===== Grid 3 x 2 =====
    gy = 368
    gap = 22
    colw = (CW - 2 * gap) / 3
    rowh = 150
    for idx, story in enumerate(GRID):
        r, c = divmod(idx, 3)
        cx = M + c * (colw + gap)
        cy = gy + r * (rowh + 12)
        # vertical rules between columns
        if c > 0:
            vrule(d, int(cx - gap / 2), gy, gy + 2 * rowh + 12, 1, RULE)
        tag(d, cx, cy, story["tag"], story["color"])
        # icon
        ic_h = 46
        ICONS[story["icon"]](d, cx, cy + 16, ic_h, ic_h)
        hf = font(SANSB, 17)
        hb2 = block(d, cx, cy + 16 + ic_h + 4, story["head"], hf, colw, INK, leading=1.1, max_lines=2)
        bf = font(SANS, 12)
        bb2 = block(d, cx, hb2 + 4, story["body"], bf, colw, SOFT, leading=1.15, max_lines=3)
        ck(f"grid{idx} body", bb2, cy + rowh)
    rule(d, M, W - M, gy + 2 * rowh + 24, 2, RULE_DARK)

    # ===== Also today (briefs) =====
    by = gy + 2 * rowh + 36
    band_f = font(SERIFB, 18)
    d.text((M, by), "Also today", font=band_f, fill=INK, anchor="la")
    band_bb = d.textbbox((M, by), "Also today", font=band_f, anchor="la")
    rule(d, M + band_bb[2] - M + 16, W - M, by + 12, 1, RULE_DARK)
    by2 = by + 30
    half = (CW - 24) / 2
    colx = [M, M + half + 24]
    bf = font(SANS, 12)
    bfb = font(SANSB, 12)
    per_col = 9
    rowh_b = 22
    vrule(d, int(M + half + 12), by2, by2 + per_col * rowh_b, 1, RULE)
    for i, (rg, col, txt) in enumerate(BRIEFS):
        c = 0 if i < per_col else 1
        rr = i if i < per_col else i - per_col
        x = colx[c]
        y = by2 + rr * rowh_b
        d.text((x, y), rg, font=bfb, fill=col, anchor="la")
        rgw = bfb.getlength(rg) + 8
        avail = half - rgw
        assert bf.getlength(txt) <= avail, f"brief{i} too wide: {bf.getlength(txt):.0f} > {avail:.0f} ({txt})"
        d.text((x + rgw, y), txt, font=bf, fill=INK, anchor="la")
        bb = d.textbbox((x + rgw, y), txt, font=bf, anchor="la")
        ck(f"brief{i}", bb[3], y + rowh_b - 2)
    briefs_bottom = by2 + per_col * rowh_b
    rule(d, M, W - M, briefs_bottom + 4, 2, RULE_DARK)

    # ===== Sport ticker =====
    sy = briefs_bottom + 14
    sf = font(SANSB, 12)
    d.text((M, sy), "SPORT", font=font(SANSB, 13), fill=RED, anchor="la")
    sx = M + sf.getlength("SPORT") + 18
    segw = (W - M - sx) / 3
    for i, (lbl, txt) in enumerate(SPORT):
        x = sx + i * segw
        if i > 0:
            vrule(d, int(x - 8), sy - 2, sy + 34, 1, RULE)
        d.text((x, sy), lbl, font=font(SANSB, 11), fill=BLUE, anchor="la")
        bb = block(d, x, sy + 15, txt, font(SANS, 11), segw - 12, SOFT, leading=1.1, max_lines=2)
        ck(f"sport{i}", bb, sy + 40)
    rule(d, M, W - M, sy + 46, 1, RULE_DARK)

    # ===== Footer =====
    fy = sy + 50
    ff = font(SANS, 12)
    foot = "Compiled from wire reports of 21 November 2026  ·  Events verified to the day in any time zone"
    d.text((M, fy), foot, font=ff, fill=SOFT, anchor="la")
    fb = d.textbbox((M, fy), foot, font=ff, anchor="la")
    ck("footer left", fb[3], H - 12)
    credit = "Built by an AI agent for make.fun"
    cf = font(SANSB, 12)
    cwd = cf.getlength(credit)
    d.text((W - M - cwd, fy), credit, font=cf, fill=RED, anchor="la")
    cb = d.textbbox((W - M - cwd, fy), credit, font=cf, anchor="la")
    ck("footer credit", cb[3], H - 12)
    # footer credit must not overlap left text
    assert (W - M - cwd) > fb[2] + 12, "footer credit overlaps left text"

    img.save(out_path, "PNG", optimize=True)
    return checks

if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    checks = render(out)
    sz = os.path.getsize(out)
    print(f"wrote {out} ({sz} bytes)")
    print("tightest margins (limit - bottom):")
    for label, bottom, limit in sorted(checks, key=lambda c: c[2] - c[1])[:8]:
        print(f"  {label}: {limit - bottom}px clear")
    assert sz <= 1048576, f"image too large: {sz}"
    print("size OK <= 1 MiB")
