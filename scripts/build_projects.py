"""Builds assets/projects.svg with live "updated" dates from the GitHub API."""
import json, os, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OWNER = os.environ.get("GITHUB_REPOSITORY_OWNER", "hrshchouhan")
TOKEN = os.environ.get("GITHUB_TOKEN")
PROJECTS = [
    ("mcp-booking-server", "Booking tools exposed over the Model Context Protocol."),
    ("opportunity-scanner", "Nightly scan for GitHub bounties and good-first-issues."),
    ("Cataclysm-BN", "My fork, where I prepare fixes to send upstream."),
]
BG, FG, MUT, ACC = "#0a0a0a", "#f4f4f2", "#9a9a96", "#5b73ff"
W, M = 1000, 48

def info(repo):
    req = urllib.request.Request(f"https://api.github.com/repos/{OWNER}/{repo}")
    req.add_header("Accept", "application/vnd.github+json")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    except Exception as e:
        print("skip", repo, e)
        return {}

def ago(iso):
    if not iso:
        return ""
    days = (datetime.now(timezone.utc) - datetime.fromisoformat(iso.replace("Z", "+00:00"))).days
    if days <= 0: return "Updated today"
    if days == 1: return "Updated yesterday"
    if days < 60: return f"Updated {days} days ago"
    return f"Updated {days // 30} months ago"

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def build():
    css = (ROOT / "scripts" / "fonts.css").read_text()
    rows, top, pitch = [], 84, 112
    for i, (repo, desc) in enumerate(PROJECTS):
        d = info(repo)
        r = top + i * pitch
        lang = d.get("language") or ""
        rows.append(
            f'<g class="up" style="animation-delay:{.15 + i * .15}s">'
            f'<text class="n" x="{M}" y="{r + 44}" font-size="34" fill="{FG}">{esc(repo)}</text>'
            f'<text class="b" x="{M}" y="{r + 76}" style="fill:{MUT};font-size:16px">{esc(desc)}</text>'
            f'<text class="m" x="{W - M}" y="{r + 44}" text-anchor="end" style="fill:{FG}">{esc(lang)}</text>'
            f'<text class="m" x="{W - M}" y="{r + 76}" text-anchor="end">{esc(ago(d.get("pushed_at")))}</text>'
            f'<path d="M{M} {r + 104}H{W - M}" stroke="{FG}" stroke-opacity=".25"/>'
            f'<rect y="{r + 103}" width="150" height="2" x="{M}" fill="{ACC}">'
            f'<animate attributeName="x" dur="7s" begin="{i * 1.6}s" repeatCount="indefinite" values="{M};{W - M - 150};{W - M - 150}" keyTimes="0;.6;1" calcMode="spline" keySplines=".45 0 .25 1;0 0 1 1"/></rect></g>'
        )
    H = top + len(PROJECTS) * pitch + 28
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Projects">'
        f'<title>Projects</title><style>{css}'
        f".n{{font-family:'Inter Tight',Helvetica,Arial,sans-serif;font-weight:700}}"
        f".b{{font-family:Inter,Helvetica,Arial,sans-serif;font-weight:400}}"
        f".m{{font-family:Inter,Helvetica,Arial,sans-serif;font-weight:500;font-size:14px;fill:{MUT}}}"
        ".up{animation:up .9s cubic-bezier(.2,.7,.1,1) both}@keyframes up{from{opacity:0;transform:translateY(14px)}}"
        "@media (prefers-reduced-motion:reduce){.up{animation:none}}</style>"
        f'<defs><pattern id="gp" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="{FG}" stroke-opacity=".06"/>'
        '<animateTransform attributeName="patternTransform" type="translate" from="0 0" to="40 0" dur="24s" repeatCount="indefinite"/></pattern>'
        f'<clipPath id="card"><rect width="{W}" height="{H}" rx="14"/></clipPath></defs>'
        f'<g clip-path="url(#card)"><rect width="{W}" height="{H}" fill="{BG}"/><rect width="{W}" height="{H}" fill="url(#gp)"/>'
        f'<rect x="{M}" y="38" width="30" height="30" fill="{ACC}"/>'
        f'<text class="m" x="{M + 50}" y="59">Projects</text>{"".join(rows)}</g></svg>'
    )
    (ROOT / "assets" / "projects.svg").write_text(svg)
    print("wrote assets/projects.svg")

if __name__ == "__main__":
    build()
