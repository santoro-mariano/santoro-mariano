"""Turn text into SVG path data so the images look the same everywhere.

GitHub serves README images as <img>, which cannot load web fonts, so every
glyph is converted to an outline using the Archivo instances in ../fonts.
"""

from functools import lru_cache
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

FONTS = Path(__file__).resolve().parent.parent / "fonts"


@lru_cache
def _font(name):
    return TTFont(FONTS / f"Archivo-{name}.ttf")


def width(text, font, size, tracking=0.0):
    f = _font(font)
    cmap, hmtx = f.getBestCmap(), f["hmtx"]
    scale = size / f["head"].unitsPerEm
    advance = sum(hmtx[cmap[ord(c)]][0] for c in text) * scale
    return advance + tracking * size * max(len(text) - 1, 0)


def path(text, font, size, x, y, anchor="start", tracking=0.0):
    """Return path data for `text` with its baseline at (x, y)."""
    f = _font(font)
    cmap, hmtx, glyphs = f.getBestCmap(), f["hmtx"], f.getGlyphSet()
    scale = size / f["head"].unitsPerEm
    if anchor == "end":
        x -= width(text, font, size, tracking)
    elif anchor == "middle":
        x -= width(text, font, size, tracking) / 2

    pen = SVGPathPen(glyphs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
    for c in text:
        name = cmap[ord(c)]
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x, y)))
        x += hmtx[name][0] * scale + tracking * size
    return pen.getCommands()
