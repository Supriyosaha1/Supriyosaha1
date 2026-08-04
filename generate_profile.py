#!/usr/bin/env python3
"""Generate a borderless GitHub profile card with a real ASCII portrait."""

from __future__ import annotations

import datetime as dt
import html
import json
import os
import urllib.request
from collections import Counter
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parent
PORTRAIT = ROOT / "assets" / "profile.png"
PORTRAIT_MASK = ROOT / "assets" / "portrait_mask.png"
USERNAME = "Supriyosaha1"

# Deliberately modest resolution: the face stays recognizable while every
# character remains visible when GitHub scales the card down.
ASCII_WIDTH = 58
ASCII_HEIGHT = 43
ASCII_RAMP = " .:-=+*#%@"


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
    """Fetch public profile statistics, with graceful fallbacks."""
    stats = {
        "repos": "19",
        "followers": "7",
        "stars": "1",
        "languages": "Jupyter Notebook, Python, HTML, C",
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
            stats["languages"] = ", ".join(name for name, _ in languages.most_common(4))
    except Exception as exc:
        print(f"GitHub API warning: {exc}")

    return stats


def ascii_portrait() -> list[str]:
    """Convert the real photo into large, low-detail ASCII characters."""
    image = Image.open(PORTRAIT).convert("L")
    image = ImageOps.autocontrast(image, cutoff=1)
    image = ImageEnhance.Contrast(image).enhance(1.18)
    edges = image.filter(ImageFilter.FIND_EDGES)

    image = image.resize((ASCII_WIDTH, ASCII_HEIGHT), Image.Resampling.LANCZOS)
    edges = edges.resize((ASCII_WIDTH, ASCII_HEIGHT), Image.Resampling.LANCZOS)
    mask = Image.open(PORTRAIT_MASK).convert("L").resize(
        (ASCII_WIDTH, ASCII_HEIGHT), Image.Resampling.LANCZOS
    )

    lines: list[str] = []
    for row in range(ASCII_HEIGHT):
        characters: list[str] = []
        for column in range(ASCII_WIDTH):
            coverage = mask.getpixel((column, row)) / 255
            if coverage < 0.16:
                characters.append(" ")
                continue

            darkness = 1 - image.getpixel((column, row)) / 255
            edge = edges.getpixel((column, row)) / 255
            tone = min(1.0, darkness * 0.78 + edge * 0.42)
            # Keep bright skin visible as sparse punctuation, while hair,
            # glasses, eyes, and clothing use denser characters.
            tone = max(0.12, tone) * min(1.0, coverage * 1.4)
            index = round(tone * (len(ASCII_RAMP) - 1))
            characters.append(ASCII_RAMP[index])
        lines.append("".join(characters).rstrip())
    return lines


def svg_document(theme: dict[str, str], stats: dict[str, str]) -> str:
    line_height = 13
    portrait_x = 30
    portrait_y = 53
    portrait_spans = "\n".join(
        f'<tspan x="{portrait_x}" y="{portrait_y + index * line_height}">'
        f"{html.escape(line)}</tspan>"
        for index, line in enumerate(ascii_portrait())
    )

    rows = [
        ("Role", "Integrated PhD Student"),
        ("Institute", "TIFR Mumbai"),
        ("Field", "Cosmology & Astrophysics"),
        ("Research", "Lyα Emitters & Reionization"),
        ("Simulations", "RAMSES, RASCAS, MP-Gadget"),
        ("Languages", "Python, C++, Bash"),
        ("Interests", "Radiative Transfer, ML, JWST"),
        ("Outreach", "50 Shades of Science"),
    ]
    stat_rows = [
        ("Public repos", stats["repos"]),
        ("Stars earned", stats["stars"]),
        ("Followers", stats["followers"]),
        ("Top languages", stats["languages"]),
        ("Updated", dt.datetime.now(dt.timezone.utc).strftime("%d %b %Y UTC")),
    ]

    def make_rows(items: list[tuple[str, str]], start_y: int) -> str:
        parts: list[str] = []
        for index, (key, value) in enumerate(items):
            y = start_y + index * 31
            parts.append(
                f'<text x="510" y="{y}" class="key">{html.escape(key)}</text>'
                f'<text x="655" y="{y}" class="dots">................</text>'
                f'<text x="805" y="{y}" class="value">{html.escape(value)}</text>'
            )
        return "\n".join(parts)

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="650" viewBox="0 0 1200 650" role="img" aria-labelledby="title description">
  <title id="title">Supriyo Saha GitHub profile card</title>
  <desc id="description">Real ASCII portrait, cosmology research interests, and live GitHub statistics.</desc>
  <style>
    .mono {{ font-family: "JetBrains Mono", "Cascadia Code", Consolas, monospace; }}
    .portrait {{ font-family: "Courier New", monospace; font-size: 10px; font-weight: 700; fill: {theme['portrait']}; white-space: pre; }}
    .heading {{ font-family: "JetBrains Mono", Consolas, monospace; font-size: 25px; font-weight: 700; fill: {theme['heading']}; }}
    .section {{ font-family: "JetBrains Mono", Consolas, monospace; font-size: 17px; font-weight: 700; fill: {theme['section']}; }}
    .key {{ font-family: "JetBrains Mono", Consolas, monospace; font-size: 15px; font-weight: 700; fill: {theme['key']}; }}
    .dots {{ font-family: "JetBrains Mono", Consolas, monospace; font-size: 15px; fill: {theme['dots']}; }}
    .value {{ font-family: "JetBrains Mono", Consolas, monospace; font-size: 15px; fill: {theme['value']}; }}
  </style>

  <!-- Intentionally borderless and transparent: GitHub supplies the background. -->
  <circle cx="28" cy="27" r="6" fill="#ff5f56"/>
  <circle cx="48" cy="27" r="6" fill="#ffbd2e"/>
  <circle cx="68" cy="27" r="6" fill="#27c93f"/>
  <text x="600" y="32" text-anchor="middle" class="mono" font-size="13" fill="{theme['muted']}">supriyo@cosmos: ~</text>
  <line x1="475" y1="53" x2="475" y2="616" stroke="{theme['border']}" stroke-width="2"/>
  <text class="portrait" xml:space="preserve">{portrait_spans}</text>
  <text x="510" y="82" class="heading">Supriyo Saha</text>
  <text x="510" y="108" class="mono" font-size="14" fill="{theme['muted']}">cosmologist · researcher · science communicator</text>
  <line x1="510" y1="129" x2="1155" y2="129" stroke="{theme['border']}" stroke-width="2"/>
  {make_rows(rows, 163)}
  <text x="510" y="431" class="section">GitHub statistics</text>
  <line x1="510" y1="446" x2="1155" y2="446" stroke="{theme['border']}" stroke-width="2"/>
  {make_rows(stat_rows, 479)}
</svg>
'''


def main() -> None:
    stats = github_stats()
    themes = {
        "dark_mode.svg": {
            "border": "#30363d",
            "portrait": "#b7c2d0",
            "heading": "#f0f6fc",
            "section": "#d2a8ff",
            "key": "#ffa657",
            "dots": "#484f58",
            "value": "#79c0ff",
            "muted": "#8b949e",
        },
        "light_mode.svg": {
            "border": "#d0d7de",
            "portrait": "#334155",
            "heading": "#1f2328",
            "section": "#8250df",
            "key": "#953800",
            "dots": "#afb8c1",
            "value": "#0969da",
            "muted": "#656d76",
        },
    }

    for filename, theme in themes.items():
        (ROOT / filename).write_text(svg_document(theme, stats), encoding="utf-8")
        print(f"Generated {filename}")

    # A changing URL prevents GitHub's image proxy from showing an old card.
    cache_key = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d%H%M%S")
    readme = f'''<a href="https://github.com/{USERNAME}">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./dark_mode.svg?v={cache_key}">
    <source media="(prefers-color-scheme: light)" srcset="./light_mode.svg?v={cache_key}">
    <img alt="Supriyo Saha — cosmologist and researcher" src="./light_mode.svg?v={cache_key}" width="100%">
  </picture>
</a>
'''
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    print(f"Updated README.md cache key: {cache_key}")


if __name__ == "__main__":
    main()
