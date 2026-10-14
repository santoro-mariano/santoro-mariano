"""Drawing primitives shared by every blueprint sheet.

Each sheet carries its own background, so the same image works on GitHub's
light and dark themes.
"""

import math
from html import escape

import svgtext

PAPER = "#164a78"
LINE = "#e8f1fa"


def text(s, size, x, y, anchor="start", font="Text", opacity=0.8):
    return f'<path d="{svgtext.path(s, font, size, x, y, anchor)}" fill="{LINE}" fill-opacity="{opacity}"/>'


def outline(s, size, x, y, font="Figure", stroke=1.6):
    return (f'<path d="{svgtext.path(s, font, size, x, y)}" fill="none" stroke="{LINE}" '
            f'stroke-width="{stroke}" stroke-linejoin="round"/>')


def wrap(s, size, max_width, font="Text"):
    lines, line = [], ""
    for word in s.split():
        trial = f"{line} {word}".strip()
        if line and svgtext.width(trial, font, size) > max_width:
            lines.append(line)
            line = word
        else:
            line = trial
    return lines + [line] if line else lines


def arrow(x, y, angle):
    """Filled arrowhead with its tip at (x, y), pointing along `angle` degrees."""
    a = math.radians(angle)
    pts = [x, y]
    for side in (-1, 1):
        b = a + math.pi + side * math.radians(16)
        pts += [x + 9 * math.cos(b), y + 9 * math.sin(b)]
    return '<path d="M{:.1f} {:.1f} L{:.1f} {:.1f} L{:.1f} {:.1f}Z" fill="{}"/>'.format(*pts, LINE)


def dimension(x1, x2, y, label, ext_from=None):
    """Horizontal dimension line from x1 to x2 with a label in a gap at the centre."""
    parts = []
    if ext_from is not None:
        parts.append(f'<path d="M{x1:.1f} {ext_from:.1f}V{y - 10:.1f}M{x2:.1f} {ext_from:.1f}V{y - 10:.1f}" '
                     f'stroke="{LINE}" stroke-width="1"/>')
    mid = (x1 + x2) / 2
    gap = svgtext.width(label, "Figure", 13) / 2 + 12
    parts.append(f'<path d="M{x1:.1f} {y:.1f}H{mid - gap:.1f}M{mid + gap:.1f} {y:.1f}H{x2:.1f}" stroke="{LINE}" stroke-width="1"/>')
    parts += [arrow(x1, y, 180), arrow(x2, y, 0), text(label, 13, mid, y + 4.5, "middle", "Figure", 0.9)]
    return "\n".join(parts)


def title_block(x, y, cells, height=58):
    """Engineering title block: a row of (width, label, value) cells."""
    total = sum(w for w, _, _ in cells)
    parts = [f'<rect x="{x}" y="{y}" width="{total}" height="{height}" fill="{PAPER}" stroke="{LINE}" stroke-opacity=".6"/>']
    cx = x
    for i, (w, label, value) in enumerate(cells):
        if i:
            parts.append(f'<path d="M{cx} {y}v{height}" stroke="{LINE}" stroke-opacity=".6"/>')
        parts.append(text(label, 10, cx + 10, y + 20, opacity=0.55))
        parts.append(text(value, 15, cx + 10, y + 42, "start", "Figure", 0.9))
        cx += w
    return "\n".join(parts)


def sheet(w, h, body, label, title=None):
    """Wrap `body` in a sheet: paper, grid, inner frame."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(label)}">
<title>{escape(title or label)}</title>
<defs>
  <pattern id="minor" width="10" height="10" patternUnits="userSpaceOnUse">
    <path d="M10 0H0V10" fill="none" stroke="{LINE}" stroke-opacity=".07" stroke-width="1"/>
  </pattern>
  <pattern id="major" width="50" height="50" patternUnits="userSpaceOnUse">
    <rect width="50" height="50" fill="url(#minor)"/>
    <path d="M50 0H0V50" fill="none" stroke="{LINE}" stroke-opacity=".14" stroke-width="1"/>
  </pattern>
</defs>
<rect width="{w}" height="{h}" rx="8" fill="{PAPER}"/>
<rect width="{w}" height="{h}" rx="8" fill="url(#major)"/>
<rect x="10" y="10" width="{w - 20}" height="{h - 20}" fill="none" stroke="{LINE}" stroke-opacity=".5" stroke-width="1"/>
{body}
</svg>
"""
