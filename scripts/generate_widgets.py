#!/usr/bin/env python3
"""Generate the SVG widgets used by the profile README."""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.request
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
USERNAME = "Yrashka200"
KYIV = ZoneInfo("Europe/Kyiv")


def github_request(path: str) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(f"https://api.github.com{path}", headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def fetch_repositories() -> list[dict]:
    repos = github_request(
        f"/users/{USERNAME}/repos?sort=updated&direction=desc&per_page=100"
    )
    return [
        repo
        for repo in repos
        if not repo["fork"] and repo["name"].lower() != USERNAME.lower()
    ][:6]


def fetch_profile() -> dict:
    return github_request(f"/users/{USERNAME}")


def truncate(value: str, limit: int) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "…"


def write_stats() -> None:
    user = fetch_profile()
    repos = github_request(f"/users/{USERNAME}/repos?per_page=100&type=owner")

    public_repos = user.get("public_repos", 0)
    followers = user.get("followers", 0)
    following = user.get("following", 0)

    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    total_forks = sum(r.get("forks_count", 0) for r in repos)

    lang_counter: dict[str, int] = {}
    for repo in repos:
        lang = repo.get("language")
        if lang:
            lang_counter[lang] = lang_counter.get(lang, 0) + 1
    top_language = max(lang_counter, key=lang_counter.get) if lang_counter else "—"

    created = datetime.strptime(user["created_at"], "%Y-%m-%dT%H:%M:%SZ")
    years = (datetime.utcnow() - created).days // 365
    joined = created.strftime("%b %Y")

    now = datetime.now(KYIV).strftime("%d %b %Y")

    tiles = [
        ("REPOSITORIES", public_repos),
        ("TOTAL STARS", total_stars),
        ("TOTAL FORKS", total_forks),
        ("FOLLOWERS", followers),
        ("FOLLOWING", following),
        ("TOP LANGUAGE", top_language),
        ("YEARS ON GITHUB", years),
        ("JOINED", joined),
    ]

    tile_w, tile_h = 196, 92
    pad_x, pad_y = 16, 24
    gap = 12
    cols = 4
    rows = (len(tiles) + cols - 1) // cols
    width = pad_x * 2 + cols * tile_w + (cols - 1) * gap
    height = 64 + rows * tile_h + (rows - 1) * gap + pad_y

    tiles_svg = []
    for i, (label, value) in enumerate(tiles):
        col = i % cols
        row = i // cols
        x = pad_x + col * (tile_w + gap)
        y = 52 + row * (tile_h + gap)
        tiles_svg.append(
            f"""  <g>
    <rect x="{x}" y="{y}" width="{tile_w}" height="{tile_h}" rx="14" fill="#141a2d" stroke="#29304a"/>
    <text x="{x + 18}" y="{y + 26}" fill="#a5abc2" font-family="Segoe UI,Arial,sans-serif" font-size="10" font-weight="700" letter-spacing="1.5">{escape(label)}</text>
    <text x="{x + 18}" y="{y + 68}" fill="#f4f1ff" font-family="Segoe UI,Arial,sans-serif" font-size="30" font-weight="700">{escape(str(value))}</text>
  </g>"""
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">
  <title id="title">GitHub stats for {USERNAME}</title>
  <desc id="description">Repositories, stars, forks, followers, top language and join date. Refreshed daily.</desc>
  <rect width="{width}" height="{height}" rx="20" fill="#101426"/>
  <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="19" fill="none" stroke="#29304a"/>
  <circle cx="28" cy="28" r="6" fill="#9e8cff"/>
  <text x="44" y="33" fill="#f4f1ff" font-family="Segoe UI,Arial,sans-serif" font-size="15" font-weight="700">GitHub Stats</text>
  <text x="{width - 18}" y="33" text-anchor="end" fill="#777f9b" font-family="Segoe UI,Arial,sans-serif" font-size="11">UPDATED {now.upper()}</text>
  <line x1="{pad_x}" y1="44" x2="{width - pad_x}" y2="44" stroke="#29304a"/>
{chr(10).join(tiles_svg)}
</svg>
"""
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "github-stats.svg").write_text(svg, encoding="utf-8")
    print(
        f"Updated GitHub stats widget: {public_repos} repos, "
        f"{total_stars} stars, {followers} followers."
    )


def write_projects() -> None:
    repos = fetch_repositories()
    now = datetime.now(KYIV).strftime("%d %b %Y")
    cards = []

    for index, repo in enumerate(repos):
        column = index % 2
        row = index // 2
        x = 12 + column * 418
        y = 44 + row * 104
        name = escape(truncate(repo["name"], 36))
        description = escape(truncate(repo.get("description") or "No description yet", 58))
        language = escape(repo.get("language") or "Project")
        stars = repo["stargazers_count"]
        forks = repo["forks_count"]
        cards.append(
            f"""  <g>
    <rect x="{x}" y="{y}" width="406" height="92" rx="14" fill="#141a2d" stroke="#29304a"/>
    <circle cx="{x + 22}" cy="{y + 23}" r="4" fill="#9e8cff"/>
    <text x="{x + 36}" y="{y + 28}" fill="#f4f1ff" font-family="Segoe UI,Arial,sans-serif" font-size="15" font-weight="700">{name}</text>
    <text x="{x + 20}" y="{y + 54}" fill="#a5abc2" font-family="Segoe UI,Arial,sans-serif" font-size="12">{description}</text>
    <text x="{x + 20}" y="{y + 76}" fill="#9e8cff" font-family="Segoe UI,Arial,sans-serif" font-size="11">{language}</text>
    <text x="{x + 390}" y="{y + 76}" text-anchor="end" fill="#a5abc2" font-family="Segoe UI,Arial,sans-serif" font-size="11">★ {stars}  ·  Forks {forks}</text>
  </g>"""
        )

    height = 52 + max(1, (len(repos) + 1) // 2) * 104
    if not cards:
        cards.append(
            '  <text x="24" y="103" fill="#a5abc2" font-family="Segoe UI,Arial,sans-serif" font-size="14">No public repositories found.</text>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="860" height="{height}" viewBox="0 0 860 {height}" role="img" aria-labelledby="title description">
  <title id="title">Latest GitHub projects by {USERNAME}</title>
  <desc id="description">Recently updated public repositories, refreshed daily.</desc>
  <rect width="860" height="{height}" rx="20" fill="#101426"/>
  <rect x="1" y="1" width="858" height="{height - 2}" rx="19" fill="none" stroke="#29304a"/>
  <text x="18" y="29" fill="#a5abc2" font-family="Segoe UI,Arial,sans-serif" font-size="11" font-weight="700" letter-spacing="2">LATEST REPOSITORIES</text>
  <text x="839" y="29" text-anchor="end" fill="#777f9b" font-family="Segoe UI,Arial,sans-serif" font-size="11">UPDATED {now.upper()}</text>
{chr(10).join(cards)}
</svg>
"""
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "latest-projects.svg").write_text(svg, encoding="utf-8")
    print(f"Updated project widget with {len(repos)} repositories.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("widget", choices=("stats", "projects", "all"))
    widget = parser.parse_args().widget

    if widget in ("stats", "all"):
        write_stats()
    if widget in ("projects", "all"):
        write_projects()


if __name__ == "__main__":
    main()