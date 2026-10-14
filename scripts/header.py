"""Render assets/header-{light,dark}.svg: the name printed in layer lines."""

from pathlib import Path

import svgtext
from theme import THEMES

OUT = Path(__file__).resolve().parent.parent / "assets"

NAME = "Mariano Santoro"
TAGLINE = "Software engineer at Wolfware. Electronics and 3D printing after hours."

W, H, Y = 1000, 204, -16  # Y lifts the whole layout to trim empty space above the name
X = 6
NAME_SIZE = 86
NAME_BASE = 122 + Y
LAYER = 5            # one printed layer: 3.6px of filament, 1.4px gap
BUILD_SECONDS = 2.4


def render(c):
    name_w = svgtext.width(NAME, "Display", NAME_SIZE, tracking=-0.02)
    top = NAME_BASE - NAME_SIZE * 0.74          # cap height of Archivo
    bottom = NAME_BASE + 2
    layers = int((bottom - top) // LAYER) + 1
    name = svgtext.path(NAME, "Display", NAME_SIZE, X, NAME_BASE, tracking=-0.02)
    tagline = svgtext.path(TAGLINE, "Text", 21, X + 62, 196 + Y)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{NAME}. {TAGLINE}">
<title>{NAME}</title>
<style>
  .build {{ animation: build {BUILD_SECONDS}s steps({layers}, end) both; }}
  .head  {{ animation: rise {BUILD_SECONDS}s steps({layers}, end) both, fade .4s {BUILD_SECONDS}s both; }}
  .sweep {{ animation: sweep {BUILD_SECONDS / layers * 2:.3f}s linear {layers // 2} alternate both; }}
  @keyframes build {{ from {{ clip-path: inset(100% 0 0 0); }} to {{ clip-path: inset(0 0 0 0); }} }}
  @keyframes rise  {{ from {{ transform: translateY(0); }} to {{ transform: translateY({-(bottom - top):.1f}px); }} }}
  @keyframes sweep {{ from {{ transform: translateX(0); }} to {{ transform: translateX({name_w:.0f}px); }} }}
  @keyframes fade  {{ to {{ opacity: 0; }} }}
  @media (prefers-reduced-motion: reduce) {{
    .build, .head, .sweep {{ animation: none; }}
    .head {{ opacity: 0; }}
  }}
</style>
<defs>
  <pattern id="layers" width="8" height="{LAYER}" patternUnits="userSpaceOnUse" y="{bottom:.1f}">
    <rect width="8" height="3.6" rx="1.2" fill="{c['ink']}"/>
  </pattern>
  <clipPath id="name"><path d="{name}"/></clipPath>
</defs>
<g class="build">
  <rect x="{X - 4}" y="{top - 4:.1f}" width="{name_w + 8:.0f}" height="{bottom - top + 8:.1f}" fill="url(#layers)" clip-path="url(#name)"/>
</g>
<g class="head"><g class="sweep">
  <path d="M{X - 6} {bottom - 14:.1f} h12 v6 l-6 7 l-6 -7 z" fill="{c['accent']}"/>
</g></g>
<g fill="none" stroke="{c['accent']}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="{X + 6}" cy="{158 + Y}" r="5.5"/>
  <path d="M{X + 11.5} {158 + Y} h8 l30 30"/>
</g>
<path d="{tagline}" fill="{c['muted']}" transform="translate(0 -1)"/>
</svg>
"""


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for mode, colors in THEMES.items():
        (OUT / f"header-{mode}.svg").write_text(render(colors))
