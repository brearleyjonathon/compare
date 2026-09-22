"""Generate the SVG sources for the favicon, social card and GitHub banner.

    python tools/make_assets.py        # writes assets/*.svg
    python tools/make_assets.py ico    # builds assets/favicon.ico from the rendered PNGs

PNG rendering is done in a browser via tools/render.html (see tools/serve.py).
"""
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
os.makedirs(ASSETS, exist_ok=True)

FONT = "Segoe UI, Inter, Helvetica Neue, Helvetica, Arial, sans-serif"

# ---------------------------------------------------------------- icon
def icon_body(prefix="ig"):
    """Contents of a 64x64 icon: blue rounded square, two document panes, coloured diff lines."""
    grey, red, green, yellow = "#cbd5e1", "#ef4444", "#22c55e", "#eab308"
    lines = [
        # (pane x, y, width, colour)
        (13, 18, 12, grey), (13, 25, 9, red), (13, 32, 12, grey), (13, 39, 11, yellow), (13, 46, 8, grey),
        (39, 18, 12, grey), (39, 25, 10, green), (39, 32, 12, grey), (39, 39, 9, yellow), (39, 46, 8, grey),
    ]
    out = [
        f'<defs><linearGradient id="{prefix}" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="#3b82f6"/><stop offset="1" stop-color="#1d4ed8"/></linearGradient></defs>',
        f'<rect width="64" height="64" rx="14" fill="url(#{prefix})"/>',
        '<rect x="9" y="12" width="20" height="40" rx="3" fill="#ffffff"/>',
        '<rect x="35" y="12" width="20" height="40" rx="3" fill="#ffffff"/>',
    ]
    for x, y, w, c in lines:
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="3.5" rx="1.75" fill="{c}"/>')
    return "\n".join(out)


def icon_svg():
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">\n'
            + icon_body() + "\n</svg>\n")


def icon_at(x, y, size, prefix):
    s = size / 64
    return f'<g transform="translate({x} {y}) scale({s})">{icon_body(prefix)}</g>'


# ---------------------------------------------------------------- mock-up of the app
BG = {"eq": None, "chg": "#382f10", "ins": "#122e1c", "del": "#3a1518", "pad": "#1c2029", "off": "#0f1115"}
BAR = {"eq": "#4b5563", "chg": "#8a7418", "ins": "#2f8a4d", "del": "#b33a41"}
HL = {"chg": "#fde047"}


def mockup(x, y, w, h, names, rows, idp):
    """Stylised diff view. `rows` is a list of tuples with one kind per pane plus a width fraction."""
    n = len(names)
    gutter, ruler, header, ln = 34, 18, 40, 26
    pane_w = (w - ruler - gutter * (n - 1)) / n
    rh = (h - header) / len(rows)
    o = []
    o.append(f'<defs><filter id="sh{idp}" x="-10%" y="-10%" width="120%" height="130%">'
             f'<feGaussianBlur stdDeviation="18"/></filter>'
             f'<clipPath id="clip{idp}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14"/></clipPath></defs>')
    o.append(f'<rect x="{x + 10}" y="{y + 26}" width="{w - 20}" height="{h}" rx="14" fill="#000" opacity=".55" filter="url(#sh{idp})"/>')
    o.append(f'<g clip-path="url(#clip{idp})">')
    o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#171a21"/>')
    # header with tabs
    o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{header}" fill="#0f1115"/>')
    o.append(f'<rect x="{x}" y="{y + header - 1}" width="{w}" height="1" fill="#2a2f3a"/>')
    for p in range(n):
        px = x + p * (pane_w + gutter)
        tw = min(pane_w - 16, 9 + len(names[p]) * 7.4)
        o.append(f'<rect x="{px + 8}" y="{y + 9}" width="{tw}" height="{header - 9}" rx="7" fill="#171a21" stroke="#2a2f3a"/>')
        o.append(f'<rect x="{px + 9}" y="{y + 9}" width="{tw - 2}" height="2" fill="#60a5fa"/>')
        o.append(f'<text x="{px + 16}" y="{y + 30}" font-family="{FONT}" font-size="13" fill="#e5e7eb">{names[p]}</text>')
        if p < n - 1:
            gx = px + pane_w
            o.append(f'<rect x="{gx}" y="{y}" width="{gutter}" height="{h}" fill="#171a21"/>')
            o.append(f'<rect x="{gx}" y="{y}" width="1" height="{h}" fill="#2a2f3a"/>')
            o.append(f'<rect x="{gx + gutter - 1}" y="{y}" width="1" height="{h}" fill="#2a2f3a"/>')
    # rows
    prev = None
    for i, spec in enumerate(rows):
        kinds, frac = spec[:n], spec[n]
        ry = y + header + i * rh
        first = kinds != prev and any(k != "eq" for k in kinds)
        prev = kinds
        for p in range(n):
            px = x + p * (pane_w + gutter)
            k = kinds[p]
            if BG[k]:
                o.append(f'<rect x="{px}" y="{ry}" width="{pane_w}" height="{rh}" fill="{BG[k]}"/>')
            if k == "pad":
                for sx in range(0, int(pane_w) + int(rh), 10):
                    o.append(f'<line x1="{px + sx}" y1="{ry + rh}" x2="{px + sx + rh}" y2="{ry}" stroke="#262b36" stroke-width="2"/>')
                continue
            if k == "off":
                continue
            # line-number stub
            o.append(f'<rect x="{px + 8}" y="{ry + rh * 0.36}" width="10" height="{rh * 0.28}" rx="2" fill="#2f3541"/>')
            o.append(f'<rect x="{px + ln}" y="{ry}" width="1" height="{rh}" fill="#2a2f3a"/>')
            bw = (pane_w - ln - 18) * frac * (0.85 + 0.15 * ((i * 7 + p * 3) % 3) / 2)
            bx = px + ln + 10
            o.append(f'<rect x="{bx}" y="{ry + rh * 0.33}" width="{bw:.1f}" height="{rh * 0.34}" rx="3" fill="{BAR[k]}"/>')
            if k in HL:
                o.append(f'<rect x="{bx + bw * 0.55:.1f}" y="{ry + rh * 0.33}" width="{bw * 0.28:.1f}" height="{rh * 0.34}" rx="3" fill="{HL[k]}"/>')
        # merge arrows in gutters
        if first:
            for p in range(n - 1):
                if kinds[p] == "eq" and kinds[p + 1] == "eq":
                    continue
                gx = x + p * (pane_w + gutter) + pane_w
                o.append(f'<rect x="{gx + 4}" y="{ry + rh / 2 - 8}" width="12" height="16" rx="3" fill="#0f1115" stroke="#3b4252"/>')
                o.append(f'<rect x="{gx + 18}" y="{ry + rh / 2 - 8}" width="12" height="16" rx="3" fill="#0f1115" stroke="#3b4252"/>')
                cy = ry + rh / 2
                # right arrow in the first button, left arrow in the second
                o.append(f'<path d="M{gx + 7} {cy}h6m-2.5 -2.5l2.5 2.5l-2.5 2.5" fill="none" stroke="#cbd5e1" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>')
                o.append(f'<path d="M{gx + 27} {cy}h-6m2.5 -2.5l-2.5 2.5l2.5 2.5" fill="none" stroke="#cbd5e1" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>')
    # overview ruler
    rx = x + w - ruler
    o.append(f'<rect x="{rx}" y="{y}" width="{ruler}" height="{h}" fill="#0f1115"/>')
    o.append(f'<rect x="{rx}" y="{y}" width="1" height="{h}" fill="#2a2f3a"/>')
    lane = (ruler - 3 * (n + 1)) / n
    total = h - header
    for i, spec in enumerate(rows):
        for p in range(n):
            k = spec[p]
            col = {"eq": "#3a4150", "chg": "#fde047", "ins": "#4ade80", "del": "#f87171", "pad": "#262b36", "off": None}[k]
            if not col:
                continue
            ly = y + header + i * (total / len(rows)) * 0.6 + 6
            o.append(f'<rect x="{rx + 3 + p * (lane + 3):.1f}" y="{ly:.1f}" width="{lane:.1f}" height="{total / len(rows) * 0.6 - 2:.1f}" fill="{col}" opacity="{0.55 if k == "eq" else 1}"/>')
    o.append(f'<rect x="{rx + 1}" y="{y + header + 4}" width="{ruler - 2}" height="{total * 0.42:.1f}" fill="#60a5fa" opacity=".18"/>')
    o.append(f'<rect x="{rx + 1}" y="{y + header + 4}" width="{ruler - 2}" height="1.5" fill="#60a5fa" opacity=".8"/>')
    o.append(f'<rect x="{rx + 1}" y="{y + header + 4 + total * 0.42:.1f}" width="{ruler - 2}" height="1.5" fill="#60a5fa" opacity=".8"/>')
    o.append("</g>")
    o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="none" stroke="#2a2f3a"/>')
    return "\n".join(o)


ROWS3 = [
    ("eq", "eq", "eq", .55), ("eq", "eq", "eq", .4), ("chg", "chg", "eq", .6), ("del", "pad", "pad", .5),
    ("eq", "eq", "eq", .7), ("eq", "eq", "eq", .35), ("eq", "chg", "chg", .55), ("pad", "pad", "ins", .45),
    ("eq", "eq", "eq", .6), ("eq", "eq", "eq", .5), ("chg", "chg", "chg", .65), ("eq", "eq", "eq", .4),
    ("pad", "pad", "ins", .5), ("pad", "pad", "ins", .35), ("eq", "eq", "eq", .6), ("eq", "eq", "eq", .45),
]
ROWS2 = [
    ("eq", "eq", .6), ("eq", "eq", .4), ("chg", "chg", .65), ("del", "pad", .5), ("eq", "eq", .7),
    ("eq", "eq", .35), ("pad", "ins", .55), ("eq", "eq", .6), ("eq", "eq", .5), ("chg", "chg", .45),
    ("eq", "eq", .65), ("pad", "ins", .5), ("pad", "ins", .4), ("eq", "eq", .6),
]


def pills(x, y, items, size=17, gap=10, maxw=None):
    out, cx, cy = [], x, y
    for t in items:
        w = len(t) * size * 0.52 + 30
        if maxw and cx + w > x + maxw:
            cx, cy = x, cy + 44
        out.append(f'<rect x="{cx}" y="{cy}" width="{w:.0f}" height="34" rx="17" fill="#171a21" stroke="#2a2f3a"/>')
        out.append(f'<text x="{cx + w / 2:.0f}" y="{cy + 22.5}" text-anchor="middle" font-family="{FONT}" font-size="{size}" fill="#cbd5e1">{t}</text>')
        cx += w + gap
    return "\n".join(out)


def backdrop(w, h, idp):
    return (f'<defs><radialGradient id="glow{idp}" cx="22%" cy="25%" r="70%">'
            f'<stop offset="0" stop-color="#2563eb" stop-opacity=".38"/><stop offset=".55" stop-color="#2563eb" stop-opacity=".08"/>'
            f'<stop offset="1" stop-color="#2563eb" stop-opacity="0"/></radialGradient>'
            f'<pattern id="grid{idp}" width="40" height="40" patternUnits="userSpaceOnUse">'
            f'<path d="M40 0H0V40" fill="none" stroke="#ffffff" stroke-opacity=".035"/></pattern></defs>'
            f'<rect width="{w}" height="{h}" fill="#0b0d12"/>'
            f'<rect width="{w}" height="{h}" fill="url(#grid{idp})"/>'
            f'<rect width="{w}" height="{h}" fill="url(#glow{idp})"/>')


FEATURES = ["Side-by-side diff", "3-way merge", "Word-level highlights", "Overview ruler", "Single HTML file"]


def social_card():
    w, h = 1200, 630
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">', backdrop(w, h, "s")]
    o.append(icon_at(80, 84, 92, "igs"))
    o.append(f'<text x="196" y="156" font-family="{FONT}" font-size="66" font-weight="700" fill="#f3f4f6" letter-spacing="-1">Compare</text>')
    o.append(f'<text x="80" y="246" font-family="{FONT}" font-size="30" fill="#e5e7eb">Two-way and three-way file comparison</text>')
    o.append(f'<text x="80" y="288" font-family="{FONT}" font-size="30" fill="#e5e7eb">and merge in the browser.</text>')
    o.append(f'<text x="80" y="336" font-family="{FONT}" font-size="20" fill="#9aa3b2">Open files, see every change, copy blocks, save.</text>')
    o.append(pills(80, 392, FEATURES, maxw=470))
    o.append(mockup(610, 96, 528, 460, ["config-mine.yaml", "config-base.yaml", "config-theirs.yaml"], ROWS3, "s"))
    o.append("</svg>\n")
    return "\n".join(o)


def github_banner():
    w, h = 1600, 500
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">', backdrop(w, h, "g")]
    o.append(icon_at(80, 86, 84, "igg"))
    o.append(f'<text x="186" y="152" font-family="{FONT}" font-size="62" font-weight="700" fill="#f3f4f6" letter-spacing="-1">Compare</text>')
    o.append(f'<text x="80" y="236" font-family="{FONT}" font-size="28" fill="#e5e7eb">Two-way and three-way file comparison and merge,</text>')
    o.append(f'<text x="80" y="274" font-family="{FONT}" font-size="28" fill="#e5e7eb">in a single self-contained HTML file.</text>')
    o.append(pills(80, 328, FEATURES, size=16, maxw=620))
    o.append(mockup(780, 56, 740, 388, ["config-mine.yaml", "config-base.yaml", "config-theirs.yaml"], ROWS3, "g"))
    o.append("</svg>\n")
    return "\n".join(o)


def build_ico():
    """favicon.ico containing PNG-encoded 16, 32 and 48 px images."""
    entries = []
    for size in (16, 32, 48):
        with open(os.path.join(ASSETS, f"favicon-{size}.png"), "rb") as f:
            entries.append((size, f.read()))
    header = struct.pack("<HHH", 0, 1, len(entries))
    offset = 6 + 16 * len(entries)
    dirs, blobs = b"", b""
    for size, data in entries:
        dirs += struct.pack("<BBBBHHII", size, size, 0, 0, 1, 32, len(data), offset)
        blobs += data
        offset += len(data)
    with open(os.path.join(ASSETS, "favicon.ico"), "wb") as f:
        f.write(header + dirs + blobs)
    print("wrote assets/favicon.ico")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "ico":
        build_ico()
    else:
        for name, content in (("icon.svg", icon_svg()), ("social-card.svg", social_card()), ("github-banner.svg", github_banner())):
            with open(os.path.join(ASSETS, name), "w", encoding="utf-8") as f:
                f.write(content)
            print("wrote assets/" + name)
