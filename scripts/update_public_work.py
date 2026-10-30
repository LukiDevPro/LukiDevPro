"""Rebuild the "Public work" section of README.md from the user's public repos.

Configuration lives in scripts/public_work.json:
  exclude   - repo names that never show up
  overrides - per-repo title / text / tags written by hand
"""
import json
import os
import re
import urllib.request
from pathlib import Path

USER = "LukiDevPro"
ROOT = Path(__file__).resolve().parent.parent
START, END = "<!-- PUBLIC-WORK:START -->", "<!-- PUBLIC-WORK:END -->"


def fetch_repos():
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-readme"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    repos, page = [], 1
    while True:
        url = f"https://api.github.com/users/{USER}/repos?type=owner&per_page=100&page={page}"
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as r:
            chunk = json.load(r)
        repos += chunk
        if len(chunk) < 100:
            return repos
        page += 1


def card(repo, cfg):
    over = cfg["overrides"].get(repo["name"], {})
    title = over.get("title", repo["name"])
    text = over.get("text") or repo.get("description") or "No description yet."
    tags = over.get("tags") or (f"`{repo['language']}`" if repo.get("language") else "")
    body = f"### [{title}]({repo['html_url']})\n\n{text}\n"
    if tags:
        body += f"\n{tags}\n"
    return body


def build(repos, cfg):
    shown = [
        r for r in repos
        if not r["private"] and not r["fork"] and not r["archived"]
        and r["name"] not in cfg["exclude"]
    ]
    shown.sort(key=lambda r: r["pushed_at"], reverse=True)
    if not shown:
        return "_Nothing public yet._"
    rows = []
    for i in range(0, len(shown), 2):
        cells = [card(r, cfg) for r in shown[i:i + 2]]
        tds = "\n".join(f'<td width="50%" valign="top">\n\n{c}\n</td>' for c in cells)
        rows.append(f"<tr>\n{tds}\n</tr>")
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def main():
    cfg = json.loads((ROOT / "scripts" / "public_work.json").read_text(encoding="utf-8"))
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    block = f"{START}\n{build(fetch_repos(), cfg)}\n{END}"
    new, n = re.subn(re.escape(START) + r".*?" + re.escape(END), lambda _: block, text, flags=re.S)
    if n != 1:
        raise SystemExit("PUBLIC-WORK markers not found exactly once in README.md")
    readme.write_text(new, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
