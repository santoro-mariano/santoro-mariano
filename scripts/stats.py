"""Render dist/stats-{light,dark}.svg from the GitHub GraphQL API.

Needs GH_TOKEN (the workflow passes GITHUB_TOKEN) and GH_USER.
"""

import json
import os
import urllib.request
from collections import Counter
from pathlib import Path

import svgtext
from theme import THEMES

OUT = Path(__file__).resolve().parent.parent / "dist"

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar { totalContributions }
      totalCommitContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      restrictedContributionsCount
      commitContributionsByRepository(maxRepositories: 100) {
        repository { primaryLanguage { name } }
        contributions { totalCount }
      }
    }
  }
}
"""

W, X = 1000, 0
TOP_LANGUAGES = 4


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


def render(c, collection):
    figures = [
        (collection["contributionCalendar"]["totalContributions"], "contributions"),
        (collection["totalCommitContributions"], "commits"),
        (collection["totalPullRequestContributions"], "pull requests"),
        (collection["totalPullRequestReviewContributions"], "code reviews"),
    ]
    parts = []
    col = (W - 2 * X) / len(figures)
    for i, (value, label) in enumerate(figures):
        x = X + i * col
        parts.append(f'<path d="{svgtext.path(f"{value:,}", "Figure", 40, x, 52)}" fill="{c["ink"]}"/>')
        parts.append(f'<path d="{svgtext.path(label, "Text", 15, x, 78)}" fill="{c["muted"]}"/>')

    parts.append(f'<path d="M{X} 108 H{W - X}" stroke="{c["rule"]}" stroke-width="1"/>')
    parts.append(f'<path d="{svgtext.path("Languages in repositories I committed to, last 12 months", "Text", 15, X, 140)}" fill="{c["muted"]}"/>')

    langs = languages(collection)
    bar_x, bar_max = X + 150, W - 2 * X - 150 - 60
    for i, (name, share) in enumerate(langs):
        y = 172 + i * 30
        w = max(share / langs[0][1] * bar_max, 4)
        parts.append(f'<path d="{svgtext.path(name, "Text", 16, X, y + 5)}" fill="{c["ink"]}"/>')
        parts.append(f'<rect x="{bar_x}" y="{y - 6}" width="{w:.1f}" height="10" rx="4" fill="{c["accent"]}"/>')
        parts.append(f'<path d="{svgtext.path(f"{share:.0%}", "Text", 15, bar_x + w + 10, y + 4)}" fill="{c["muted"]}"/>')

    h = 172 + len(langs) * 30
    summary = ", ".join(f"{v:,} {l}" for v, l in figures)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" '
            f'aria-label="Last 12 months: {summary}.">\n<title>GitHub activity, last 12 months</title>\n'
            + "\n".join(parts) + "\n</svg>\n")


if __name__ == "__main__":
    collection = fetch(os.environ["GH_USER"], os.environ["GH_TOKEN"])
    OUT.mkdir(exist_ok=True)
    for mode, colors in THEMES.items():
        (OUT / f"stats-{mode}.svg").write_text(render(colors, collection))
