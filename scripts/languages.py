import json
import os
import re
import urllib.request

OWNER = "dhyansuresh"
TOP_N = 8
# exclude
SKIP = {"Shell", "CSS", "TeX", "HTML", "SCSS", "Makefile", "Dockerfile",
        "Batchfile", "PowerShell", "Procfile", "CMake"}
MIN_PCT = 1.0   # hide languages that make up less than this share of your code
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
            if lang not in SKIP:
                totals[lang] = totals.get(lang, 0) + n
    total = sum(totals.values()) or 1
    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    top = ranked[:TOP_N]
    lines = ["Most used languages:", ""]
    for lang, n in top:
        pct = n / total * 100
        filled = max(1, round(pct / 100 * BAR)) if n else 0
        lines.append(f"{lang:<14}{'█' * filled}{'░' * (BAR - filled)}   {pct:5.2f} %")
    return "\n".join(lines)


def save_json(repos, lang_by_repo, path="data/languages.json"):
    totals = {}
    for name in repos:
        for lang, n in lang_by_repo[name].items():
            if lang not in SKIP:
                totals[lang] = totals.get(lang, 0) + n
    total = sum(totals.values()) or 1
    totals = {k: v for k, v in totals.items() if v / total * 100 >= MIN_PCT}
    total = sum(totals.values()) or 1
    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    top = ranked[:TOP_N]
    data = {"repos": len(repos),
            "languages": [{"name": k, "pct": round(v / total * 100, 2)} for k, v in top]}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def write_readme(block, path="README.md"):
    readme = open(path, encoding="utf-8").read()
    new = f"{START}\n```text\n{block}\n```\n{END}"
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pattern.search(readme):
        return
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
    save_json(names, langs)


if __name__ == "__main__":
    main()
