"""Pull Dhyan's latest Letterboxd diary entries into README.md.

If Letterboxd can't be reached, the README is left as it is.
"""
import re
import urllib.request
import xml.etree.ElementTree as ET

USER = "dsuresh"
COUNT = 4
FEED = f"https://letterboxd.com/{USER}/rss/"
START, END = "<!--FILMS:START-->", "<!--FILMS:END-->"
NS = {"letterboxd": "https://letterboxd.com"}


def stars(rating):
    if not rating:
        return ""
    r = float(rating)
    return " " + "★" * int(r) + ("½" if r % 1 else "")


def films():
    req = urllib.request.Request(FEED, headers={"User-Agent": "Mozilla/5.0 (profile README updater)"})
    with urllib.request.urlopen(req, timeout=20) as r:
        root = ET.fromstring(r.read())
    out = []
    for item in root.iter("item"):
        title = item.findtext("letterboxd:filmTitle", namespaces=NS)
        if not title:          # skips lists and other non film entries
            continue
        year = item.findtext("letterboxd:filmYear", namespaces=NS)
        rating = item.findtext("letterboxd:memberRating", namespaces=NS)
        rewatch = item.findtext("letterboxd:rewatch", namespaces=NS) == "Yes"
        link = item.findtext("link")
        line = f"* [*{title}*]({link})"
        if year:
            line += f" ({year})"
        line += stars(rating)
        if rewatch:
            line += " ↻"
        out.append(line)
        if len(out) == COUNT:
            break
    return out


def main():
    try:
        lines = films()
    except Exception as e:  # network trouble or Letterboxd blocking: keep what's there
        print(f"Could not read Letterboxd feed: {e}")
        return
    if not lines:
        print("No films found, leaving README alone")
        return
    readme = open("README.md", encoding="utf-8").read()
    block = f"{START}\n\n" + "\n".join(lines) + f"\n\n{END}"
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pattern.search(readme):
        raise SystemExit("Film markers not found in README.md")
    updated = pattern.sub(lambda _: block, readme)
    if updated != readme:
        open("README.md", "w", encoding="utf-8").write(updated)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
