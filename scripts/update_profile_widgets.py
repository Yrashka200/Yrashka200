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


def write_clock() -> None:
    now = datetime.now(KYIV)
    time_label = now.strftime("%H:%M")
    date_label = now.strftime("%A, %d %B %Y")
    timezone_label = now.tzname() or "Europe/Kyiv"
    hour_angle = (now.hour % 12 + now.minute / 60) * 30
    minute_angle = now.minute * 6

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="860" height="150" viewBox="0 0 860 150" role="img" aria-labelledby="title description">
  <title id="title">Time in Kyiv: {time_label}</title>
  <desc id="description">{escape(date_label)} · {escape(timezone_label)} · refreshes every five minutes</desc>
  <rect width="860" height="150" rx="20" fill="#101426"/>
  <rect x="1" y="1" width="858" height="148" rx="19" fill="none" stroke="#29304a"/>
  <circle cx="82" cy="75" r="43" fill="#191f36" stroke="#343c5e" stroke-width="2"/>
  <circle cx="82" cy="75" r="3" fill="#b3a5ff"/>
  <path d="M82 75 L82 48" stroke="#f4f1ff" stroke-width="4" stroke-linecap="round" transform="rotate({hour_angle:.1f} 82 75)"/>
  <path d="M82 75 L82 40" stroke="#9e8cff" stroke-width="2.5" stroke-linecap="round" transform="rotate({minute_angle:.1f} 82 75)"/>
  <text x="155" y="49" fill="#a5abc2" font-family="Segoe UI,Arial,sans-serif" font-size="13" font-weight="700" letter-spacing="2">LOCAL TIME · KYIV, UKRAINE</text>
  <text x="151" y="105" fill="#f4f1ff" font-family="Segoe UI,Arial,sans-serif" font-size="48" font-weight="700">{time_label}</text>
  <text x="330" y="101" fill="#a5abc2" font-family="Segoe UI,Arial,sans-serif" font-size="15">{escape(timezone_label)} · {escape(date_label)}</text>
  <rect x="710" y="57" width="116" height="36" rx="18" fill="#211e3b"/>
  <circle cx="728" cy="75" r="4" fill="#8f7bff"/>
  <text x="741" y="80" fill="#c6bdff" font-family="Segoe UI,Arial,sans-serif" font-size="11" font-weight="700" letter-spacing="1">UTC{now.strftime('%z')[:3]}</text>
</svg>
"""
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "kyiv-clock.svg").write_text(svg, encoding="utf-8")
    print(f"Updated Kyiv clock: {time_label} {timezone_label}")


def fetch_repositories() -> list[dict]:
    url = f"https://api.github.com/users/{USERNAME}/repos?sort=updated&direction=desc&per_page=100"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        repos = json.load(response)

    return [
        repo
        for repo in repos
        if not repo["fork"] and repo["name"].lower() != USERNAME.lower()
    ][:6]


def truncate(value: str, limit: int) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "…"


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
    parser.add_argument("widget", choices=("clock", "projects", "all"))
    widget = parser.parse_args().widget

    if widget in ("clock", "all"):
        write_clock()
    if widget in ("projects", "all"):
        write_projects()


if __name__ == "__main__":
    main()
