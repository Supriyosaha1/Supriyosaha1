#!/usr/bin/env python3
"""Generate a Neofetch-style GitHub card with a polished ASCII portrait."""

from __future__ import annotations

import base64
import datetime as dt
import html
import json
import os
import urllib.request
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ASCII_PORTRAIT = ROOT / "assets" / "ascii_portrait_clean.png"
USERNAME = "Supriyosaha1"


def request_json(url: str) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{USERNAME}-profile-card",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def github_stats() -> dict[str, str]:
    stats = {
        "repos": "19",
        "followers": "7",
        "stars": "1",
        "languages": "Jupyter Notebook · Python · HTML · C",
    }
    try:
        user = request_json(f"https://api.github.com/users/{USERNAME}")
        assert isinstance(user, dict)
        stats["repos"] = str(user.get("public_repos", stats["repos"]))
        stats["followers"] = str(user.get("followers", stats["followers"]))

        repos: list[dict] = []
        for page in range(1, 6):
            result = request_json(
                f"https://api.github.com/users/{USERNAME}/repos"
                f"?per_page=100&page={page}&sort=updated"
            )
            if not isinstance(result, list) or not result:
                break
            repos.extend(item for item in result if isinstance(item, dict))
            if len(result) < 100:
                break

        owned = [repo for repo in repos if not repo.get("fork")]
        stats["stars"] = str(sum(int(repo.get("stargazers_count", 0)) for repo in owned))
        languages = Counter(
            str(repo["language"])
            for repo in owned
            if repo.get("language")
        )
        if languages:
            stats["languages"] = " · ".join(name for name, _ in languages.most_common(4))
    except Exception as exc:
        print(f"GitHub API warning: {exc}")
    return stats


def portrait_data_uri() -> str:
    encoded = base64.b64encode(ASCII_PORTRAIT.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def svg_document(theme: dict[str, str], stats: dict[str, str]) -> str:
    portrait = portrait_data_uri()
    updated = dt.datetime.now(dt.timezone.utc).strftime("%d %b %Y")

    rows = [
        ("ROLE", "Integrated PhD student"),
        ("INSTITUTE", "TIFR Mumbai"),
        ("RESEARCH", "Lyα emitters · cosmic reionization"),
        ("METHODS", "Radiative transfer · simulations"),
        ("TOOLS", "Python · RASCAS · RAMSES · MP-Gadget"),
    ]
    row_svg: list[str] = []
    for index, (label, value) in enumerate(rows):
        y = 150 + index * 39
        row_svg.append(
            f'<text x="438" y="{y}" class="label">{html.escape(label)}</text>'
            f'<text x="553" y="{y}" class="value">{html.escape(value)}</text>'
        )

    stat_items = [
        ("PUBLIC REPOS", stats["repos"]),
        ("STARS", stats["stars"]),
        ("FOLLOWERS", stats["followers"]),
    ]
    stat_svg: list[str] = []
    for index, (label, value) in enumerate(stat_items):
        x = 438 + index * 151
        stat_svg.append(
            f'<rect x="{x}" y="349" width="135" height="64" rx="10" fill="{theme["chip"]}" stroke="{theme["border"]}"/>'
            f'<text x="{x + 13}" y="371" class="stat-label">{label}</text>'
            f'<text x="{x + 13}" y="399" class="stat-value">{html.escape(value)}</text>'
        )

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="1050" height="510" viewBox="0 0 1050 510" role="img"
     aria-labelledby="title description">
  <title id="title">Supriyo Saha — ASCII GitHub profile</title>
  <desc id="description">A terminal-style ASCII portrait with cosmology research details and GitHub statistics.</desc>
  <defs>
    <linearGradient id="accentLine" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{theme['accent']}"/>
      <stop offset="1" stop-color="{theme['accent2']}"/>
    </linearGradient>
  </defs>
  <style>
    .mono {{ font-family: "JetBrains Mono", "Cascadia Code", Consolas, monospace; }}
    .name {{ font: 700 29px "JetBrains Mono", "Cascadia Code", Consolas, monospace; fill: {theme['heading']}; }}
    .tagline {{ font: 14px "JetBrains Mono", "Cascadia Code", Consolas, monospace; fill: {theme['muted']}; }}
    .label {{ font: 700 12px "JetBrains Mono", "Cascadia Code", Consolas, monospace; letter-spacing: .7px; fill: {theme['key']}; }}
    .value {{ font: 15px "JetBrains Mono", "Cascadia Code", Consolas, monospace; fill: {theme['value']}; }}
    .stat-label {{ font: 700 10px "JetBrains Mono", "Cascadia Code", Consolas, monospace; letter-spacing: .7px; fill: {theme['muted']}; }}
    .stat-value {{ font: 700 21px "JetBrains Mono", "Cascadia Code", Consolas, monospace; fill: {theme['heading']}; }}
  </style>

  <rect x="2" y="2" width="1046" height="506" rx="18" fill="{theme['background']}" stroke="{theme['border']}" stroke-width="3"/>
  <rect x="3" y="3" width="1044" height="43" rx="16" fill="{theme['titlebar']}"/>
  <rect x="3" y="30" width="1044" height="17" fill="{theme['titlebar']}"/>
  <circle cx="25" cy="24" r="6" fill="#ff5f56"/>
  <circle cx="45" cy="24" r="6" fill="#ffbd2e"/>
  <circle cx="65" cy="24" r="6" fill="#27c93f"/>
  <text x="525" y="29" text-anchor="middle" class="mono" font-size="12" fill="{theme['muted']}">supriyo@cosmos: ~/profile</text>

  <image x="20" y="52" width="382" height="445" preserveAspectRatio="xMidYMid meet"
         href="{portrait}" xlink:href="{portrait}"/>
  <line x1="412" y1="65" x2="412" y2="478" stroke="{theme['border']}" stroke-width="2"/>

  <text x="438" y="84" class="name">Supriyo Saha</text>
  <text x="438" y="108" class="tagline">cosmologist · researcher · science communicator</text>
  <rect x="438" y="120" width="577" height="3" rx="2" fill="url(#accentLine)"/>
  {''.join(row_svg)}

  <text x="438" y="331" class="mono" font-size="12" fill="{theme['muted']}">GITHUB STATISTICS</text>
  {''.join(stat_svg)}
  <text x="438" y="444" class="mono" font-size="11" fill="{theme['muted']}">TOP LANGUAGES  ·  {html.escape(stats['languages'])}</text>
  <text x="438" y="482" class="mono" font-size="12" fill="{theme['accent']}">$ studying light from the first galaxies_</text>
  <text x="1015" y="482" text-anchor="end" class="mono" font-size="10" fill="{theme['muted']}">updated {updated}</text>
</svg>
'''


def main() -> None:
    stats = github_stats()
    themes = {
        "dark_mode.svg": {
            "background": "#0d1117",
            "titlebar": "#111923",
            "chip": "#111923",
            "border": "#303b49",
            "portrait": "#c9d1d9",
            "heading": "#f0f6fc",
            "key": "#f0a45d",
            "value": "#b9d9f5",
            "muted": "#8491a1",
            "accent": "#7dd3fc",
            "accent2": "#c084fc",
        },
        "light_mode.svg": {
            "background": "#ffffff",
            "titlebar": "#f6f8fa",
            "chip": "#f6f8fa",
            "border": "#d0d7de",
            "portrait": "#334155",
            "heading": "#1f2328",
            "key": "#9a4d00",
            "value": "#0969da",
            "muted": "#656d76",
            "accent": "#0969da",
            "accent2": "#8250df",
        },
    }
    for filename, theme in themes.items():
        (ROOT / filename).write_text(svg_document(theme, stats), encoding="utf-8")
        print(f"Generated {filename}")


if __name__ == "__main__":
    main()
