"""Builds assets/orrery.svg from real GitHub data: languages, projects, commits."""
import json, math, os, urllib.request, zlib
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OWNER = os.environ.get("GITHUB_REPOSITORY_OWNER", "hrshchouhan")
TOKEN = os.environ.get("GITHUB_TOKEN")
OFFLINE = os.environ.get("OFFLINE") == "1"   # use placeholder data
STATIC = os.environ.get("STATIC") == "1"     # still frame, for previews only
PROJECTS = [("mcp-booking-server", "Java"), ("opportunity-scanner", "Python"), ("Cataclysm-BN", "C++")]
BG, FG, MUT, ACC = "#0f1412", "#e9e6dc", "#8a918b", "#ff6b8b"
PCOL = ["#7fd6c2", "#e9e6dc", "#ff9db3", "#8a918b"]
W, H, CX, CY, TILT = 1000, 560, 680, 268, 0.55
RAD, BELT, DUR = [81, 142, 232, 270], 188, [26, 44, 70, 100]

def get(url):
    req = urllib.request.Request(url if url.startswith("http") else "https://api.github.com" + url)
    req.add_header("Accept", "application/vnd.github+json")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    except Exception as e:
        print("skip", url, e)
        return None

def load():
    default = ([("Java", .34), ("C++", .28), ("Python", .18), ("JavaScript", .12)], 24, dict(PROJECTS))
    if OFFLINE:
        return default
    sums = Counter()
    for r in get(f"/users/{OWNER}/repos?per_page=100&type=owner") or []:
        if not r.get("fork"):
            sums.update(get(r["languages_url"]) or {})
    total = sum(sums.values())
    langs = [(n, b / total) for n, b in sums.most_common(4)] if total else default[0]
    since = datetime.now(timezone.utc) - timedelta(days=30)
    commits = 0
    for e in get(f"/users/{OWNER}/events/public?per_page=100") or []:
        if e.get("type") == "PushEvent" and datetime.fromisoformat(e["created_at"].replace("Z", "+00:00")) > since:
            commits += e.get("payload", {}).get("size", 1)
    plang = {}
    for name, fallback in PROJECTS:
        plang[name] = ((get(f"/repos/{OWNER}/{name}") or {}).get("language")) or fallback
    return langs, commits, plang

def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
def ell(cx, cy, rx, ry):
    return f"M{cx - rx:.1f} {cy}a{rx:.1f} {ry:.1f} 0 1 0 {2 * rx:.1f} 0a{rx:.1f} {ry:.1f} 0 1 0 {-2 * rx:.1f} 0"

def build():
    css = (ROOT / "scripts" / "fonts.css").read_text()
    langs, commits, plang = load()
    other = max(0.0, 1 - sum(s for _, s in langs))
    o = []
    # orbit rings + commit belt
    for R in RAD:
        o.append(f'<ellipse cx="{CX}" cy="{CY}" rx="{R}" ry="{R * TILT:.1f}" fill="none" stroke="{FG}" stroke-opacity=".14"/>')
    p = max(4.5, 14 - commits / 6)
    k = max(1, round(120 / p))
    o.append(f'<ellipse cx="{CX}" cy="{CY}" rx="{BELT}" ry="{BELT * TILT:.1f}" fill="none" stroke="{FG}" stroke-opacity=".55" stroke-width="2.2" stroke-linecap="round" stroke-dasharray="0.1 {p:.1f}">'
             f'<animate attributeName="stroke-dashoffset" from="0" to="{-p * k:.1f}" dur="30s" repeatCount="indefinite"/></ellipse>')
    # sun
    o.append(f'<circle cx="{CX}" cy="{CY}" r="30" fill="{ACC}" fill-opacity=".18"><animate attributeName="r" dur="4s" repeatCount="indefinite" values="30;38;30"/></circle><circle cx="{CX}" cy="{CY}" r="13" fill="{ACC}"/>')
    # planets, moons
    for i, (name, share) in enumerate(langs):
        R, dur, col = RAD[i], DUR[i], PCOL[i]
        r = 4.5 + 11 * math.sqrt(share)
        off = zlib.crc32(name.encode()) % dur
        moons = [pn for pn, pl in plang.items() if (pl or "").lower() == name.lower() or (i == 0 and (pl or "").lower() not in [n.lower() for n, _ in langs])]
        inner = ""
        for m, pn in enumerate(moons):
            mr = r + 10 + m * 6
            inner += (f'<circle r="2.8" fill="{ACC if m % 2 == 0 else FG}">' +
                      (f'<animateMotion dur="{5 + 2 * m}s" repeatCount="indefinite" path="{ell(0, 0, mr, mr * TILT)}"/>' if not STATIC else "") + '</circle>')
        circ = (f'<circle r="{r:.1f}" fill="{col}">' +
                (f'<animate attributeName="r" dur="{dur}s" begin="-{off}s" repeatCount="indefinite" values="{r:.1f};{r * 1.25:.1f};{r:.1f};{r * .8:.1f};{r:.1f}" keyTimes="0;.25;.5;.75;1"/>' if not STATIC else "") + '</circle>')
        label = f'<text x="{r + 8:.1f}" y="{-r - 3:.1f}" class="b" style="font-weight:500;font-size:14px">{esc(name)}</text>'
        if STATIC:
            a = 2 * math.pi * (off / dur) + math.pi / 2
            g = f'<g transform="translate({CX + R * math.cos(a):.1f} {CY + R * TILT * math.sin(a):.1f})">{circ}{inner}{label}</g>'
        else:
            g = f'<g><animateMotion dur="{dur}s" begin="-{off}s" repeatCount="indefinite" path="{ell(CX, CY, R, R * TILT)}"/>{circ}{inner}{label}</g>'
        o.append(g)
    planets = "".join(o)
    # left column
    left = (f'<g fill="{FG}"><rect x="48" y="44" width="8" height="50"/><rect x="86" y="44" width="8" height="50"/><rect x="56" y="64" width="30" height="7"/></g>'
            f'<rect x="56" y="64" width="10" height="7" fill="{ACC}">' + ('' if STATIC else '<animate attributeName="x" dur="4s" repeatCount="indefinite" values="56;76;56" keyTimes="0;.5;1" calcMode="spline" keySplines=".5 0 .2 1;.5 0 .2 1"/>') + '</rect>'
            f'<text class="n" x="46" y="190" font-size="52" letter-spacing="-1.5" fill="{FG}">Harshvardhan</text>'
            f'<text class="n" x="46" y="248" font-size="52" letter-spacing="-1.5" fill="{FG}">Chouhan</text>'
            f'<text class="b" x="48" y="286" style="fill:{MUT};font-size:17px">AI, backend systems and data</text>')
    rows = [(n, s, PCOL[i]) for i, (n, s) in enumerate(langs)] + [("Other", other, "#3a423d")]
    for j, (n, s, c) in enumerate(rows):
        y = 346 + j * 30
        left += (f'<circle cx="54" cy="{y - 5}" r="6" fill="{c}"/><text class="b" x="72" y="{y}" style="font-weight:500;font-size:15px">{esc(n)}</text>'
                 f'<text class="b" x="250" y="{y}" style="fill:{MUT};font-size:15px">{round(s * 100)}%</text>')
    left += (f'<circle cx="54" cy="{H - 44}" r="4.5" fill="{ACC}">' + ('' if STATIC else '<animate attributeName="opacity" dur="3s" repeatCount="indefinite" values="1;.3;1"/>') + '</circle>'
             f'<text class="b" x="68" y="{H - 39}" style="font-size:15px">Open to freelance</text>'
             f'<text class="b" x="{CX}" y="{H - 24}" text-anchor="middle" style="fill:{MUT};font-size:12px">planets are languages, moons are projects, the belt is commits</text>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Harshvardhan Chouhan. AI, backend systems and data. An orrery where languages orbit as planets, projects as moons, commits as a belt.">'
           f'<title>Harshvardhan Chouhan</title><style>{css}'
           f".n{{font-family:'Inter Tight',Helvetica,Arial,sans-serif;font-weight:700}}"
           f".b{{font-family:Inter,Helvetica,Arial,sans-serif;font-weight:400;fill:{FG}}}</style>"
           f'<defs><clipPath id="card"><rect width="{W}" height="{H}" rx="16"/></clipPath></defs>'
           f'<g clip-path="url(#card)"><rect width="{W}" height="{H}" fill="{BG}"/>{planets}{left}</g></svg>')
    (ROOT / "assets" / "orrery.svg").write_text(svg)
    print("wrote assets/orrery.svg", "langs", [(n, round(s, 2)) for n, s in langs], "commits30", commits)

if __name__ == "__main__":
    build()
