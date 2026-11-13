"""Draw the profile README panels as Windows 95 style DOS windows.

Reads the files in data/ (about, languages, films, book, contact), downloads the
cover and posters, and writes assets/hello.svg, assets/languages.svg,
assets/offclock.svg and one assets/btn-*.svg button per contact link.
Images are embedded so they show up inside GitHub's image proxy.
"""
import base64
import html
import io
import json
import os
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UI = "Tahoma, 'MS Sans Serif', 'Segoe UI', Arial, sans-serif"
W = 820
FS = 19
CW = 9.0                      # rough VT323 character width at FS
C = {"dim": "#a8a8a8", "white": "#ffffff", "cyan": "#55ffff", "yellow": "#ffff55",
     "red": "#ff5555", "cell": "#1f3f3f"}


def path(*p):
    return os.path.join(ROOT, *p)


FONT = base64.b64encode(open(path("assets", "fonts", "vt323.woff2"), "rb").read()).decode()


# ---------- Windows 95 chrome ----------
def bevel(x, y, w, h, raised=True, fill="#c0c0c0"):
    lt1, rb1, lt2, rb2 = ("#ffffff", "#000000", "#dfdfdf", "#808080") if raised else ("#808080", "#ffffff", "#000000", "#dfdfdf")
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>'
            f'<path d="M{x} {y+h}V{y}H{x+w}" fill="none" stroke="{lt1}" transform="translate(.5 .5)"/>'
            f'<path d="M{x} {y+h-0.5}H{x+w-0.5}V{y}" fill="none" stroke="{rb1}" transform="translate(.5 0)"/>'
            f'<path d="M{x+1} {y+h-1}V{y+1}H{x+w-1}" fill="none" stroke="{lt2}" transform="translate(.5 .5)"/>'
            f'<path d="M{x+1} {y+h-1.5}H{x+w-1.5}V{y+1}" fill="none" stroke="{rb2}" transform="translate(.5 0)"/>')


def title_btn(x, y, glyph):
    g = {"min": f'<rect x="{x+4}" y="{y+9}" width="6" height="2" fill="#000"/>',
         "max": f'<rect x="{x+3.5}" y="{y+2.5}" width="8" height="8" fill="none" stroke="#000"/><rect x="{x+3}" y="{y+2}" width="9" height="2" fill="#000"/>',
         "close": f'<path d="M{x+4} {y+3}l7 7M{x+11} {y+3}l-7 7" stroke="#000" stroke-width="1.6"/>'}[glyph]
    return bevel(x, y, 16, 14) + g


def window(h, title, body):
    t = [bevel(0, 0, W, h),
         f'<rect x="4" y="4" width="{W-8}" height="18" fill="url(#tb)"/>',
         '<rect x="7" y="6" width="14" height="14" fill="#000"/><rect x="7.5" y="6.5" width="13" height="13" fill="none" stroke="#c0c0c0"/>',
         f'<text x="9" y="17" fill="#fff" style="font-family:{UI};font-size:8px;font-weight:700">C:</text>',
         f'<text x="25" y="17.5" fill="#fff" style="font-family:{UI};font-size:12px;font-weight:700">{html.escape(title)}</text>',
         title_btn(W - 22, 6, "close"), title_btn(W - 40, 6, "max"), title_btn(W - 56, 6, "min"),
         bevel(6, 26, W - 12, h - 32, raised=False, fill="#000000")]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-label="{html.escape(title)}">
<style>
@font-face{{font-family:'VT323';src:url(data:font/woff2;base64,{FONT}) format('woff2')}}
.t{{font-family:'VT323',monospace;font-size:{FS}px;white-space:pre}}
</style>
<defs><linearGradient id="tb" x1="0" x2="1"><stop offset="0" stop-color="#000080"/><stop offset="1" stop-color="#1084d0"/></linearGradient></defs>
{"".join(t)}
{body}
</svg>'''


def text(x, y, s, color="white", size=None, anchor=None):
    extra = f' style="font-size:{size}px"' if size else ""
    a = f' text-anchor="{anchor}"' if anchor else ""
    return f'<text class="t" x="{x}" y="{y}" fill="{C[color]}"{a}{extra}>{html.escape(s)}</text>'


def prompt(x, y, cmd):
    return (f'<text class="t" x="{x}" y="{y}"><tspan fill="{C["dim"]}">C:\\DHYAN&gt;</tspan>'
            f'<tspan fill="{C["white"]}">{html.escape(cmd)}</tspan></text>')


def wrap(s, width, max_lines):
    words, lines, cur = s.split(), [], ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) <= width:
            cur = f"{cur} {w}".strip()
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][: width - 1].rstrip() + "…"
    return lines


def star(cx, cy, r, fill_frac, uid):
    import math
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rad = r if i % 2 == 0 else r * 0.45
        pts.append(f"{cx + rad*math.cos(ang):.1f},{cy + rad*math.sin(ang):.1f}")
    p = " ".join(pts)
    if fill_frac >= 1:
        return f'<polygon points="{p}" fill="{C["yellow"]}"/>'
    return (f'<clipPath id="h{uid}"><rect x="{cx-r}" y="{cy-r}" width="{r}" height="{2*r}"/></clipPath>'
            f'<polygon points="{p}" fill="{C["yellow"]}" clip-path="url(#h{uid})"/>')


def stars(x, y, rating, uid):
    if rating is None:
        return ""
    out, full = [], int(rating)
    for i in range(full):
        out.append(star(x + 7 + i * 15, y - 6, 6.5, 1, f"{uid}_{i}"))
    if rating - full >= 0.5:
        out.append(star(x + 7 + full * 15, y - 6, 6.5, 0.5, f"{uid}_h"))
    return "".join(out)


# ---------- images ----------
def image_data(url, w, h):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (profile README updater)"})
    raw = urllib.request.urlopen(req, timeout=20).read()
    mime = "image/jpeg"
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(raw)).convert("RGB")
        im = im.resize((w * 2, h * 2), Image.LANCZOS)   # 2x for sharp screens
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=82, optimize=True)
        raw = buf.getvalue()
    except ImportError:
        pass
    return f"data:{mime};base64,{base64.b64encode(raw).decode()}"


def picture(x, y, w, h, url):
    frame = bevel(x - 3, y - 3, w + 6, h + 6, raised=False, fill="#202020")
    try:
        src = image_data(url, w, h)
        return frame + f'<image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid slice" href="{src}"/>'
    except Exception as e:
        print(f"image failed {url}: {e}")
        return frame + text(x + w / 2, y + h / 2, "NO IMAGE", "dim", anchor="middle")


# ---------- panels ----------
def languages_panel():
    langs = json.load(open(path("data", "languages.json")))
    rows = langs["languages"]
    y0, lh = 26 + 30, 25
    body = [prompt(22, y0, "langs --all"),
            text(22, y0 + lh, f"Most used languages across {langs['repos']} repos:", "dim")]
    bx, cell, gap, n = 190, 13, 3, 25
    for i, row in enumerate(rows):
        y = y0 + lh * (i + 2) + 6
        body.append(text(22, y, row["name"], "white"))
        filled = max(1, round(row["pct"] / 100 * n))
        for k in range(n):
            col = C["cyan"] if k < filled else C["cell"]
            body.append(f'<rect x="{bx + k*(cell+gap)}" y="{y-13}" width="{cell}" height="{cell}" fill="{col}"/>')
        body.append(text(bx + n * (cell + gap) + 18, y, f"{row['pct']:5.2f} %", "yellow"))
    h = y0 + lh * (len(rows) + 2) + 26
    return window(h, "LANGS.EXE", "".join(body))


def offclock_panel():
    book = json.load(open(path("data", "book.json")))
    films = json.load(open(path("data", "films.json")))[:4]
    y0 = 26 + 30
    body = [prompt(22, y0, "dir \\offclock")]
    top = y0 + 30
    body.append(text(22, top, "NOW READING", "yellow"))
    body.append(text(262, top, "RECENTLY WATCHED", "yellow"))
    iy = top + 16
    # book
    cw, ch = 120, 180
    body.append(picture(25, iy, cw, ch, book["cover"]))
    ty = iy + ch + 26
    for j, line in enumerate(wrap(book["title"], 24, 3)):
        body.append(text(22, ty + j * 20, line, "cyan"))
    body.append(text(22, ty + 3 * 20, book["author"], "dim"))
    # films
    pw, ph, step = 112, 168, 136
    for i, f in enumerate(films):
        x = 265 + i * step
        body.append(picture(x, iy, pw, ph, f["poster"]) if f.get("poster") else bevel(x - 3, iy - 3, pw + 6, ph + 6, False, "#202020"))
        fy = iy + ph + 26
        lines = wrap(f["title"], 13, 2)
        for j, line in enumerate(lines):
            body.append(text(x - 2, fy + j * 20, line, "cyan"))
        sy = fy + 2 * 20
        body.append(text(x - 2, sy, str(f.get("year", "")), "dim"))
        body.append(stars(x + 38, sy, f.get("rating"), i))
    h = iy + ch + 26 + 3 * 20 + 26
    return window(h, "OFFCLOCK.EXE", "".join(body))


def hello_panel():
    about = json.load(open(path("data", "about.json")))
    y0, lh = 26 + 30, 25
    body = [prompt(22, y0, "type hello.txt"), text(22, y0 + lh + 6, about["greeting"], "yellow", size=24)]
    for i, line in enumerate(about["lines"]):
        body.append(text(22, y0 + lh * (i + 2) + 12, line, "white"))
    h = y0 + lh * (len(about["lines"]) + 1) + 12 + 28
    return window(h, "HELLO.EXE", "".join(body))


def button(label, value):
    bw, bh = 268, 64
    body = [bevel(0, 0, bw, bh),
            bevel(6, 6, bw - 12, bh - 12, raised=False, fill="#000000"),
            text(18, 28, label, "yellow", size=17),
            text(18, 48, value, "cyan", size=21),
            f'<path d="M{bw-30} 24l10 8-10 8" fill="none" stroke="{C["cyan"]}" stroke-width="2.5"/>']
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{bw}" height="{bh}" viewBox="0 0 {bw} {bh}" role="img" aria-label="{html.escape(label)}: {html.escape(value)}">
<style>
@font-face{{font-family:'VT323';src:url(data:font/woff2;base64,{FONT}) format('woff2')}}
.t{{font-family:'VT323',monospace;font-size:{FS}px;white-space:pre}}
</style>
{"".join(body)}
</svg>'''


def main():
    open(path("assets", "hello.svg"), "w", encoding="utf-8").write(hello_panel())
    for c in json.load(open(path("data", "contact.json"))):
        open(path("assets", f"btn-{c['id']}.svg"), "w", encoding="utf-8").write(button(c["label"], c["value"]))
    open(path("assets", "languages.svg"), "w", encoding="utf-8").write(languages_panel())
    open(path("assets", "offclock.svg"), "w", encoding="utf-8").write(offclock_panel())
    print("panels written")


if __name__ == "__main__":
    main()
