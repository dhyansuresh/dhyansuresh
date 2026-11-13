# Windows 95 DOS 

import base64
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "data", "terminal.json"), encoding="utf-8"))
FONT_B64 = base64.b64encode(open(os.path.join(ROOT, "assets", "fonts", "vt323.woff2"), "rb").read()).decode()
UI = "Tahoma, 'MS Sans Serif', 'Segoe UI', Arial, sans-serif"
W = 820
FS = 21
CW = 10.0
LH = 23
TB_H = 30                    # toolbar height
CON_X, CON_Y = 8, 26 + TB_H + 4     # console origin 
CON_W = W - 16
PAD_X = CON_X + 14
TOP = CON_Y + 26
CHAR_T = 0.022

C = {"dim": "#a8a8a8", "key": "#ffffff", "str": "#55ffff", "lit": "#ffff55", "bad": "#ff5555", "cmd": "#ffffff"}
key = lambda k: [('  "', "dim"), (k, "key"), ('": ', "dim")]
PROMPT = [("C:\\DHYAN>", "dim")]


def value_parts(v, color=None):
    # colored pieces
    if v is None:
      return [("null", color or "lit")]
    if isinstance(v, bool):
        return [("true" if v else "false", color or "lit")]
    if isinstance(v, (int, float)):
        return [(str(v), color or "lit")]
    if isinstance(v, list):
        out = [("[", "dim")]
        for n, item in enumerate(v):
            if n:
                out.append((", ", "dim"))
            out += value_parts(item, color)
        return out + [("]", "dim")]
    return [('"%s"' % v, color or "str")]


LINES = [[("show", [(line, "dim")])] for line in CFG.get("boot", [])]
if LINES:
    LINES.append([])
LINES.append([("show", PROMPT), ("pause", 0.5), ("type", [(CFG["command"], "cmd")]), ("pause", 0.35)])
LINES.append([("show", [("{", "dim")])])
fields = CFG["fields"]
for n, f in enumerate(fields):
    comma = [(",", "dim")] if n < len(fields) - 1 else []
    if "fix" in f:
        steps = [("type", key(f["key"])), ("type", value_parts(f["value"]) + comma), ("pause", 0.9),
                 ("erase", 1), ("pause", 0.25),
                 ("type", value_parts(f["fix"], "bad" if isinstance(f["fix"], bool) or f["fix"] is None else None) + comma)]
    else:
        steps = [("type", key(f["key"]) + value_parts(f["value"]) + comma)]
    if f.get("comment"):
        steps += [("pause", 0.2), ("type", [("  // " + f["comment"], "dim")])]
    LINES.append(steps)
LINES.append([("show", [("}", "dim")])])
LINES.append([])
LINES.append([("pause", 0.3), ("show", PROMPT), ("pause", 0.6),
              ("type", [(CFG["last_command"], "cmd")]), ("pause", 0.7)])

EXTRA = 2 * LH                               # empty space under the last line for the dialog
CON_H = 26 + LH * (len(LINES) - 1) + 16 + EXTRA
H = CON_Y + CON_H + 8

els, clips, styles, cursor_kf = [], [], [], []
t = 0.5
uid = 0
dur_of, start_of = {}, {}


def txt(parts):
    return "".join(f'<tspan fill="{C[c]}">{html.escape(x)}</tspan>' for x, c in parts)


for li, steps in enumerate(LINES):
    y = TOP + li * LH
    col = 0
    placed = []
    if not steps:
        continue
    cursor_kf.append((t, PAD_X, y, "step-end"))
    for st in steps:
        kind = st[0]
        if kind == "pause":
            t += st[1]
            placed.append(None)
            continue
        if kind == "erase":
            c0, n, eid = placed[st[1]]
            dur = n * CHAR_T * 1.4
            styles.append(f"#c{eid}{{animation:type {dur_of[eid]:.3f}s steps({n},jump-start) {start_of[eid]:.3f}s both,"
                          f"erase {dur:.3f}s steps({n},jump-start) {t:.3f}s forwards}}")
            cursor_kf.append((t, PAD_X + (c0 + n) * CW, y, f"steps({n},jump-start)"))
            t += dur
            cursor_kf.append((t, PAD_X + c0 * CW, y, "step-end"))
            col = c0
            placed.append(None)
            continue
        parts = st[1]
        n = sum(len(x) for x, _ in parts)
        uid += 1
        eid = uid
        x0 = PAD_X + col * CW
        els.append(f'<text x="{x0:.1f}" y="{y}" textLength="{n*CW:.1f}" lengthAdjust="spacingAndGlyphs" '
                   f'clip-path="url(#k{eid})">{txt(parts)}</text>')
        clips.append(f'<clipPath id="k{eid}"><rect id="c{eid}" class="r" x="{x0:.1f}" y="{y-18}" '
                     f'width="{n*CW+1:.1f}" height="{LH}"/></clipPath>')
        if kind == "show":
            styles.append(f"#c{eid}{{animation:show .08s step-start {t:.3f}s both}}")
            cursor_kf.append((t, x0 + n * CW, y, "step-end"))
        else:
            dur = n * CHAR_T
            dur_of[eid], start_of[eid] = dur, t
            styles.append(f"#c{eid}{{animation:type {dur:.3f}s steps({n},jump-start) {t:.3f}s both}}")
            cursor_kf.append((t, x0, y, f"steps({n},jump-start)"))
            t += dur
            cursor_kf.append((t, x0 + n * CW, y, "step-end"))
        placed.append((col, n, eid))
        col += n
    t += 0.06

DIALOG_T = t
TOTAL = t + 0.1
kf = [f"0%{{transform:translate({cursor_kf[0][1]:.1f}px,{cursor_kf[0][2]+2}px)}}"]
for tm, x, y, fn in cursor_kf:
    kf.append(f"{tm / TOTAL * 100:.3f}%{{transform:translate({x:.1f}px,{y+2}px);animation-timing-function:{fn}}}")
kf.append(f"100%{{transform:translate({cursor_kf[-1][1]:.1f}px,{cursor_kf[-1][2]+2}px)}}")


def bevel(x, y, w, h, raised=True, fill="#c0c0c0", thick=True):
    """Classic 2px Windows 95 bevel."""
    lt1, rb1, lt2, rb2 = ("#ffffff", "#000000", "#dfdfdf", "#808080") if raised else ("#808080", "#ffffff", "#000000", "#dfdfdf")
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>',
           f'<path d="M{x} {y+h}V{y}H{x+w}" fill="none" stroke="{lt1}" stroke-width="1" transform="translate(.5 .5)"/>',
           f'<path d="M{x} {y+h-0.5}H{x+w-0.5}V{y}" fill="none" stroke="{rb1}" stroke-width="1" transform="translate(.5 0)"/>']
    if thick:
        out += [f'<path d="M{x+1} {y+h-1}V{y+1}H{x+w-1}" fill="none" stroke="{lt2}" stroke-width="1" transform="translate(.5 .5)"/>',
                f'<path d="M{x+1} {y+h-1.5}H{x+w-1.5}V{y+1}" fill="none" stroke="{rb2}" stroke-width="1" transform="translate(.5 0)"/>']
    return "".join(out)


def title_btn(x, y, glyph):
    g = {"min": f'<rect x="{x+4}" y="{y+9}" width="6" height="2" fill="#000"/>',
         "max": f'<rect x="{x+3.5}" y="{y+2.5}" width="8" height="8" fill="none" stroke="#000"/><rect x="{x+3}" y="{y+2}" width="9" height="2" fill="#000"/>',
         "close": f'<path d="M{x+4} {y+3}l7 7M{x+11} {y+3}l-7 7" stroke="#000" stroke-width="1.6"/>'}[glyph]
    return bevel(x, y, 16, 14) + g


def title_bar(x, y, w, title, icon=True):
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="18" fill="url(#tb)"/>']
    tx = x + 4
    if icon:
        out.append(f'<rect x="{x+3}" y="{y+2}" width="14" height="14" fill="#000"/><rect x="{x+3.5}" y="{y+2.5}" width="13" height="13" fill="none" stroke="#c0c0c0"/>'
                   f'<text x="{x+5}" y="{y+13}" fill="#fff" style="font-family:{UI};font-size:8px;font-weight:700">C:</text>')
        tx = x + 21
    out.append(f'<text x="{tx}" y="{y+13.5}" fill="#fff" style="font-family:{UI};font-size:12px;font-weight:700">{html.escape(title)}</text>')
    bx = x + w - 2 - 16
    out.append(title_btn(bx, y + 2, "close"))
    if icon:
        out.append(title_btn(bx - 18, y + 2, "max"))
        out.append(title_btn(bx - 34, y + 2, "min"))
    return "".join(out)


# toolbar
tb = [bevel(4, 26, W - 8, TB_H, thick=False)]
tb.append(bevel(10, 30, 66, 22, raised=False, fill="#ffffff"))
tb.append(f'<text x="15" y="45" style="font-family:{UI};font-size:12px" fill="#000">Auto</text>')
tb.append(bevel(58, 32, 16, 18) + '<path d="M62 39h8l-4 4z" fill="#000"/>')
icons = ["M5 4h8v10H5z", "M4 5h10M4 9h10M4 13h10", "M4 4h4v4H4zM10 4h4v4h-4zM4 10h4v4H4zM10 10h4v4h-4z", "M9 3v12M3 9h12", "M4 13l4-8 4 6 3-3"]
bx = 86
for d in icons:
    tb.append(bevel(bx, 30, 22, 22))
    tb.append(f'<path transform="translate({bx+2} 32)" d="{d}" fill="none" stroke="#000" stroke-width="1.3"/>')
    bx += 24 if d != icons[2] else 32
tb.append(f'<text x="{W-14}" y="45" text-anchor="end" style="font-family:{UI};font-size:11px" fill="#404040">80 x 25</text>')

# error dialog
DW, DH = 330, 128
DX, DY = W - DW - 26, CON_Y + CON_H - DH - 14
ERR = CFG.get("error")
if ERR:
    b1, b2 = (ERR.get("buttons", ["OK"]) + [None])[:2]
    dialog = (bevel(DX, DY, DW, DH) + title_bar(DX + 3, DY + 3, DW - 6, ERR.get("title", "Error"), icon=False) +
              f'<circle cx="{DX+34}" cy="{DY+52}" r="15" fill="#ff0000" stroke="#800000"/>'
              f'<path d="M{DX+28} {DY+46}l12 12M{DX+40} {DY+46}l-12 12" stroke="#fff" stroke-width="3"/>')
    for n, line in enumerate(ERR.get("lines", [])[:3]):
        dialog += f'<text x="{DX+62}" y="{DY+46+n*17}" style="font-family:{UI};font-size:12px" fill="#000">{html.escape(line)}</text>'
    if b2:
        dialog += (bevel(DX + DW / 2 - 116, DY + DH - 36, 110, 24) +
                   f'<rect x="{DX+DW/2-112.5}" y="{DY+DH-32.5}" width="103" height="17" fill="none" stroke="#000" stroke-dasharray="1 1"/>'
                   f'<text x="{DX+DW/2-61}" y="{DY+DH-19.5}" text-anchor="middle" style="font-family:{UI};font-size:12px" fill="#000">{html.escape(b1)}</text>'
                   + bevel(DX + DW / 2 + 6, DY + DH - 36, 110, 24) +
                   f'<text x="{DX+DW/2+61}" y="{DY+DH-19.5}" text-anchor="middle" style="font-family:{UI};font-size:12px" fill="#000">{html.escape(b2)}</text>')
    else:
        dialog += (bevel(DX + DW / 2 - 55, DY + DH - 36, 110, 24) +
                   f'<rect x="{DX+DW/2-51.5}" y="{DY+DH-32.5}" width="103" height="17" fill="none" stroke="#000" stroke-dasharray="1 1"/>'
                   f'<text x="{DX+DW/2}" y="{DY+DH-19.5}" text-anchor="middle" style="font-family:{UI};font-size:12px" fill="#000">{html.escape(b1)}</text>')
else:
    dialog = ""

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Windows 95 style DOS prompt typing out a JSON file about Dhyan">
<style>
@font-face{{font-family:'VT323';src:url(data:font/woff2;base64,{FONT_B64}) format('woff2')}}
.con text{{font-family:'VT323',monospace;font-size:{FS}px;white-space:pre}}
.r{{transform-box:fill-box;transform-origin:left center}}
@keyframes type{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
@keyframes erase{{from{{transform:scaleX(1)}}to{{transform:scaleX(0)}}}}
@keyframes show{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
@keyframes cur{{{"".join(kf)}}}
@keyframes blink{{0%,49%{{opacity:1}}50%,100%{{opacity:0}}}}
@keyframes pop{{from{{opacity:0}}to{{opacity:1}}}}
#cur{{animation:cur {TOTAL:.3f}s linear forwards}}
#blink{{animation:blink .5s step-end infinite}}
#dlg{{animation:pop .08s step-start {DIALOG_T:.3f}s both}}
{"".join(styles)}
</style>
<defs>{"".join(clips)}
<linearGradient id="tb" x1="0" x2="1"><stop offset="0" stop-color="#000080"/><stop offset="1" stop-color="#1084d0"/></linearGradient></defs>
{bevel(0, 0, W, H)}
{title_bar(4, 4, W - 8, "DOS Prompt - DHYAN")}
{"".join(tb)}
{bevel(CON_X - 2, CON_Y - 2, CON_W + 4, CON_H + 4, raised=False, fill="#000000")}
<g class="con">
{"".join(els)}
<g id="cur"><rect id="blink" width="{CW:.1f}" height="3" fill="#c0c0c0"/></g>
</g>
<g id="dlg">{dialog}</g>
</svg>'''
open(os.path.join(ROOT, "assets", "terminal.svg"), "w", encoding="utf-8").write(svg)
print("terminal", round(TOTAL, 2), "s", len(svg), "bytes", W, "x", H)
