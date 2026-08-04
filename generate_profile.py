#!/usr/bin/env python3
"""Generate a terminal-style GitHub card with a clean ASCII portrait."""

from __future__ import annotations

import datetime as dt
import html
import json
import os
import urllib.request
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parent
PORTRAIT = ROOT / "assets" / "profile.jpg"
USERNAME = "Supriyosaha1"

ASCII_WIDTH = 48
ASCII_HEIGHT = 38
ASCII_RAMP = "@%#*+=-:. "


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


def ascii_portrait() -> list[str]:
    """Create a background-masked portrait with a small, readable character set."""
    image = Image.open(PORTRAIT).convert("L")
    image = ImageOps.autocontrast(image, cutoff=1)
    image = ImageEnhance.Contrast(image).enhance(1.22)
    image = image.filter(ImageFilter.UnsharpMask(radius=1.2, percent=115, threshold=3))

    width, height = image.size
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse(
        (0.12 * width, -0.03 * height, 0.88 * width, 0.78 * height),
        fill=255,
    )
    draw.ellipse(
        (-0.13 * width, 0.55 * height, 1.13 * width, 1.25 * height),
        fill=255,
    )

    image = image.resize((ASCII_WIDTH, ASCII_HEIGHT), Image.Resampling.LANCZOS)
    mask = mask.resize((ASCII_WIDTH, ASCII_HEIGHT), Image.Resampling.LANCZOS)

    lines: list[str] = []
    for y in range(ASCII_HEIGHT):
        line: list[str] = []
        for x in range(ASCII_WIDTH):
            if mask.getpixel((x, y)) < 110:
                line.append(" ")
                continue
            brightness = image.getpixel((x, y))
            index = round(brightness / 255 * (len(ASCII_RAMP) - 1))
            line.append(ASCII_RAMP[index])
        lines.append("".join(line).rstrip())
    return lines


def svg_document(theme: dict[str, str], stats: dict[str, str]) -> str:
    portrait_x = 37
    portrait_y = 60
    line_height = 12.1
    portrait_spans = "\n".join(
        f'<tspan x="{portrait_x}" y="{portrait_y + row * line_height:.1f}">'
        f"{html.escape(line)}</tspan>"
        for row, line in enumerate(ascii_portrait())
    )

    rows = [
        ("ROLE", "Integrated PhD student"),
        ("INSTITUTE", "TIFR Mumbai"),
        ("RESEARCH", "Lyα emitters · cosmic reionization"),
        ("METHODS", "Radiative transfer · simulations"),
        ("TOOLS", "Python · RASCAS · RAMSES · MP-Gadget"),
    ]
    row_svg: list[str] = []
    for index, (label, value) in enumerate(rows):
        y = 151 + index * 39
        row_svg.append(
            f'<text x="460" y="{y}" class="label">{html.escape(label)}</text>'
            f'<text x="575" y="{y}" class="value">{html.escape(value)}</text>'
        )

    stat_items = [
        ("PUBLIC REPOS", stats["repos"]),
        ("STARS", stats["stars"]),
        ("FOLLOWERS", stats["followers"]),
    ]
    stat_svg: list[str] = []
    for index, (label, value) in enumerate(stat_items):
        x = 460 + index * 151
        stat_svg.append(
            f'<rect x="{x}" y="352" width="135" height="64" rx="10" fill="{theme["chip"]}" stroke="{theme["border"]}"/>'
            f'<text x="{x + 13}" y="374" class="stat-label">{label}</text>'
            f'<text x="{x + 13}" y="402" class="stat-value">{html.escape(value)}</text>'
        )

    updated = dt.datetime.now(dt.timezone.utc).strftime("%d %b %Y")

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="520" viewBox="0 0 1080 520" role="img" aria-labelledby="title description">
  <title id="title">Supriyo Saha — ASCII GitHub profile</title>
  <desc id="description">ASCII portrait, cosmology research information, and public GitHub statistics.</desc>
  <defs>
    <linearGradient id="accentLine" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{theme['accent']}"/>
      <stop offset="1" stop-color="{theme['accent2']}"/>
    </linearGradient>
  </defs>
  <style>
    .mono {{ font-family: "JetBrains Mono", "Cascadia Code", Consolas, monospace; }}
    .portrait {{ font-family: "Courier New", monospace; font-size: 11px; font-weight: 700; fill: {theme['portrait']}; white-space: pre; }}
    .name {{ font: 700 28px "JetBrains Mono", "Cascadia Code", Consolas, monospace; fill: {theme['heading']}; }}
    .tagline {{ font: 14px "JetBrains Mono", "Cascadia Code", Consolas, monospace; fill: {theme['muted']}; }}
    .label {{ font: 700 12px "JetBrains Mono", "Cascadia Code", Consolas, monospace; letter-spacing: .7px; fill: {theme['key']}; }}
    .value {{ font: 15px "JetBrains Mono", "Cascadia Code", Consolas, monospace; fill: {theme['value']}; }}
    .stat-label {{ font: 700 10px "JetBrains Mono", "Cascadia Code", Consolas, monospace; letter-spacing: .7px; fill: {theme['muted']}; }}
    .stat-value {{ font: 700 21px "JetBrains Mono", "Cascadia Code", Consolas, monospace; fill: {theme['heading']}; }}
  </style>

  <rect x="2" y="2" width="1076" height="516" rx="18" fill="{theme['background']}" stroke="{theme['border']}" stroke-width="3"/>
  <rect x="3" y="3" width="1074" height="43" rx="16" fill="{theme['titlebar']}"/>
  <rect x="3" y="30" width="1074" height="17" fill="{theme['titlebar']}"/>
  <circle cx="25" cy="24" r="6" fill="#ff5f56"/>
  <circle cx="45" cy="24" r="6" fill="#ffbd2e"/>
  <circle cx="65" cy="24" r="6" fill="#27c93f"/>
  <text x="540" y="29" text-anchor="middle" class="mono" font-size="12" fill="{theme['muted']}">supriyo@cosmos: ~/profile</text>

  <text class="portrait" xml:space="preserve">{portrait_spans}</text>
  <line x1="426" y1="64" x2="426" y2="485" stroke="{theme['border']}" stroke-width="2"/>

  <text x="460" y="86" class="name">Supriyo Saha</text>
  <text x="460" y="110" class="tagline">cosmologist · researcher · science communicator</text>
  <rect x="460" y="121" width="575" height="3" rx="2" fill="url(#accentLine)"/>
  {''.join(row_svg)}

  <text x="460" y="334" class="mono" font-size="12" fill="{theme['muted']}">GITHUB STATISTICS</text>
  {''.join(stat_svg)}
  <text x="460" y="447" class="mono" font-size="11" fill="{theme['muted']}">TOP LANGUAGES  ·  {html.escape(stats['languages'])}</text>
  <text x="460" y="491" class="mono" font-size="12" fill="{theme['accent']}">$ studying light from the first galaxies_</text>
  <text x="1035" y="491" text-anchor="end" class="mono" font-size="10" fill="{theme['muted']}">updated {updated}</text>
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
            "portrait": "#c4ccd6",
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
