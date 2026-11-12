"""Count the languages across Dhyan's repos and write a stats block into README.md.

Runs in GitHub Actions. With a LANGS_TOKEN secret it includes private repos;
without one it falls back to public repos only.
"""
import json
import os
import re
import urllib.request

OWNER = "dhyansuresh"
EXCLUDE = {OWNER, "devfest-florida-2026-webxr-voice-workshop"}  # profile repo + workshop starter code
TOP_N = 8
BAR = 25
START, END = "<!--LANGS:START-->", "<!--LANGS:END-->"

private_token = os.environ.get("LANGS_TOKEN", "").strip()
token = private_token or os.environ.get("GITHUB_TOKEN", "")


def get(url):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-language-stats",
    })
    with urllib.request.urlopen(req) as r:
        return json.load(r), r.headers.get("Link", "")


def paged(url):
    out = []
    while url:
        data, link = get(url)
        out += data
        m = re.search(r'<([^>]+)>;\s*rel="next"', link)
        url = m.group(1) if m else None
    return out


def build(repos, lang_by_repo, include_private):
    totals = {}
    for name in repos:
        for lang, n in lang_by_repo[name].items():
            totals[lang] = totals.get(lang, 0) + n
    total = sum(totals.values()) or 1
    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    top, rest = ranked[:TOP_N], ranked[TOP_N:]
    if rest:
        top.append(("Other", sum(n for _, n in rest)))
    scope = "public + private" if include_private else "public"
    lines = [f"Languages across {len(repos)} repos ({scope})", ""]
    for lang, n in top:
        pct = n / total * 100
        filled = max(1, round(pct / 100 * BAR)) if n else 0
        lines.append(f"{lang:<14}{'█' * filled}{'░' * (BAR - filled)}   {pct:5.2f} %")
    return "\n".join(lines)


def write_readme(block, path="README.md"):
    readme = open(path, encoding="utf-8").read()
    new = f"{START}\n```text\n{block}\n```\n{END}"
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pattern.search(readme):
        raise SystemExit("Markers not found in README.md")
    updated = pattern.sub(lambda _: new, readme)
    if updated != readme:
        open(path, "w", encoding="utf-8").write(updated)
        print("README updated")
    else:
        print("No change")


def main():
    if private_token:
        repos = paged("https://api.github.com/user/repos?affiliation=owner&per_page=100")
    else:
        repos = paged(f"https://api.github.com/users/{OWNER}/repos?per_page=100")
    repos = [r for r in repos
             if r["owner"]["login"] == OWNER and not r["fork"] and r["name"] not in EXCLUDE]
    langs = {r["name"]: get(r["languages_url"])[0] for r in repos}
    names = [n for n in langs if langs[n]]
    block = build(names, langs, bool(private_token))
    print(block)
    write_readme(block)


if __name__ == "__main__":
    main()
