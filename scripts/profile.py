"""Render dist/profile.svg: the whole profile as one blueprint sheet.

Pulls the last 12 months of activity from the GitHub GraphQL API.
Needs GH_TOKEN (the workflow passes GITHUB_TOKEN) and GH_USER.
"""

import json
import math
import os
import urllib.request
from collections import Counter
from pathlib import Path

import svgtext
from blueprint import LINE, dimension, outline, sheet, text, title_block

OUT = Path(__file__).resolve().parent.parent / "dist"

NAME = "Mariano Santoro"
W, H, X = 1000, 680, 40
TOP_LANGUAGES = 3

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar { totalContributions }
      totalCommitContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      totalIssueContributions
      totalRepositoriesWithContributedCommits
      commitContributionsByRepository(maxRepositories: 100) {
        repository { primaryLanguage { name } }
        contributions { totalCount }
      }
    }
  }
}
"""


def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        body = json.load(resp)
    if "errors" in body:
        raise SystemExit(f"GraphQL error: {body['errors']}")
    return body["data"]["user"]["contributionsCollection"]


def languages(collection):
    counts = Counter()
    for item in collection["commitContributionsByRepository"]:
        lang = item["repository"]["primaryLanguage"]
        if lang and item["contributions"]["totalCount"]:
            counts[lang["name"]] += item["contributions"]["totalCount"]
    total = sum(counts.values()) or 1
    top = [(name, n / total) for name, n in counts.most_common(TOP_LANGUAGES)]
    return [(name, share) for name, share in top if share >= 0.01]


def name_block():
    x, base, size = 64, 150, 78
    x2 = x + svgtext.width(NAME, "Figure", size)
    cap_y = base - size * 0.74
    cx, cy, r = 892, 92, 30
    return f"""
<g fill="none" stroke="{LINE}" stroke-opacity=".4" stroke-width="1" stroke-dasharray="6 5">
  <path d="M30 {base}H{W - 30}"/>
  <path d="M30 {cap_y:.1f}H{x2 + 40:.0f}"/>
</g>
{text("baseline", 11, W - 34, base - 6, "end", opacity=.6)}
{dimension(x, x2, cap_y - 34, "0x62756E6E79", ext_from=cap_y - 8)}
{outline(NAME, size, x, base)}
<g fill="none" stroke="{LINE}" stroke-width="1">
  <circle cx="{cx}" cy="{cy}" r="{r}"/>
  <circle cx="{cx}" cy="{cy}" r="{r * .45:.1f}" stroke-opacity=".7"/>
  <path stroke-opacity=".6" stroke-dasharray="10 3 2 3" d="M{cx - r - 12} {cy}H{cx + r + 12}M{cx} {cy - r - 12}V{cy + r + 12}"/>
  <path d="M{cx - r * .707:.1f} {cy + r * .707:.1f}L{cx - 64} {cy + 64}H{cx - 96}"/>
  <path stroke-opacity=".7" d="M{cx + r + 18} {cy}A{r + 18} {r + 18} 0 0 1 {cx + (r + 18) * .707:.1f} {cy + (r + 18) * .707:.1f}"/>
</g>
{text("Detail A", 12, cx - 96, cy + 58, opacity=.85)}
{text("45°", 12, cx + r + 22, cy + 34, opacity=.85)}
"""


def activity(collection):
    figures = [
        (collection["contributionCalendar"]["totalContributions"], "contributions"),
        (collection["totalCommitContributions"], "commits"),
        (collection["totalPullRequestContributions"], "pull requests"),
        (collection["totalPullRequestReviewContributions"], "code reviews"),
    ]
    parts = [text("Last 12 months", 20, X, 262, font="Figure", opacity=.95)]
    for i, (value, label) in enumerate(figures):
        x, y = X + (i % 2) * 230, 324 + (i // 2) * 78
        parts.append(text(f"{value:,}", 36, x, y, font="Figure", opacity=.97))
        parts.append(text(label, 14, x, y + 22, opacity=.65))

    parts.append(text("Languages in repositories I committed to", 14, X, 486, opacity=.65))
    langs = languages(collection)
    bar_x, bar_max = X + 110, 250
    for i, (name, share) in enumerate(langs):
        y = 518 + i * 30
        w = max(share / langs[0][1] * bar_max, 6)
        parts.append(text(name, 15, X, y + 5, opacity=.9))
        parts.append(f'<rect x="{bar_x}" y="{y - 7}" width="{w:.1f}" height="12" fill="url(#hatch)" stroke="{LINE}" stroke-width="1.2"/>')
        parts.append(text(f"{share:.0%}", 13, bar_x + w + 10, y + 4, opacity=.7))
    return "\n".join(parts), figures, langs


def radar(collection):
    axes = [
        ("Commits", collection["totalCommitContributions"]),
        ("Pull requests", collection["totalPullRequestContributions"]),
        ("Code reviews", collection["totalPullRequestReviewContributions"]),
        ("Issues", collection["totalIssueContributions"]),
        ("Repositories", collection["totalRepositoriesWithContributedCommits"]),
    ]
    cx, cy, r, decades = 745, 420, 120, 4      # rings at 10, 100, 1K, 10K

    def at(i, frac):
        a = -math.pi / 2 + i * 2 * math.pi / len(axes)
        return cx + r * frac * math.cos(a), cy + r * frac * math.sin(a)

    parts = []
    for d in range(1, decades + 1):
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (at(i, d / decades) for i in range(len(axes))))
        dash = "none" if d == decades else "5 4"
        parts.append(f'<polygon points="{pts}" fill="none" stroke="{LINE}" stroke-opacity="{.5 if d == decades else .28}" stroke-dasharray="{dash}"/>')
        parts.append(text(["10", "100", "1K", "10K"][d - 1], 10, cx + 6, cy - r * d / decades + 12, opacity=.5))
    for i, (label, value) in enumerate(axes):
        a = -math.pi / 2 + i * 2 * math.pi / len(axes)
        ex, ey = at(i, 1)
        parts.append(f'<path d="M{cx} {cy}L{ex:.1f} {ey:.1f}" stroke="{LINE}" stroke-opacity=".35"/>')
        lx, ly = at(i, (r + 24) / r)
        anchor = "middle" if abs(math.cos(a)) < .3 else ("start" if math.cos(a) > 0 else "end")
        ly += -8 if math.sin(a) < -.5 else (12 if math.sin(a) > .5 else 0)
        parts.append(text(label, 14, lx, ly, anchor, opacity=.75))
        parts.append(text(f"{value:,}", 14, lx, ly + 18, anchor, "Figure", .95))
    pts = [at(i, min(math.log10(max(v, 1)) / decades, 1)) for i, (_, v) in enumerate(axes)]
    parts.append(f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="url(#hatch-light)" '
                 f'stroke="{LINE}" stroke-width="1.8" stroke-linejoin="round"/>')
    parts += [f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{LINE}"/>' for x, y in pts]
    return "\n".join(parts), axes


def render(collection):
    stats, figures, langs = activity(collection)
    profile, axes = radar(collection)
    defs = "".join(
        f'<pattern id="{pid}" width="{s}" height="{s}" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        f'<path d="M0 0V{s}" stroke="{LINE}" stroke-opacity="{o}" stroke-width="1.5"/></pattern>'
        for pid, s, o in (("hatch", 6, .7), ("hatch-light", 7, .35)))
    body = "\n".join([
        f"<defs>{defs}</defs>",
        name_block(),
        f'<path d="M{X} 210H{W - X}" stroke="{LINE}" stroke-opacity=".35" stroke-dasharray="6 5"/>',
        stats,
        profile,
        text("Polar chart on a log scale: each ring is ten times the one inside it.", 12, X, H - 40, opacity=.55),
        title_block(W - 20 - 330, H - 20 - 58,
                    [(120, "Drawn by", "M. Santoro"), (130, "Approved by", "The dogs"), (80, "Sheet", "1 of 1")]),
    ])
    summary = ", ".join(f"{v:,} {l}" for v, l in figures)
    langs_text = ", ".join(f"{n} {s:.0%}" for n, s in langs)
    extra = ", ".join(f"{v:,} {l.lower()}" for l, v in axes[3:])
    return sheet(W, H, body, f"{NAME}. Last 12 months on GitHub: {summary}, {extra}. Languages: {langs_text}.", NAME)


if __name__ == "__main__":
    collection = fetch(os.environ["GH_USER"], os.environ["GH_TOKEN"])
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.svg"):
        old.unlink()
    (OUT / "profile.svg").write_text(render(collection))
