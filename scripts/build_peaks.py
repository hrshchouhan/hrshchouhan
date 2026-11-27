"""Builds the animated sky-lantern profile and Aurora Year graph."""
import json, math, os, random, urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
A = ROOT / "assets"
OWNER = os.environ.get("GITHUB_REPOSITORY_OWNER", "hrshchouhan")
TOKEN = os.environ.get("GITHUB_TOKEN")
OFFLINE = os.environ.get("OFFLINE") == "1"
PROJECTS = [("mcp-booking-server", "Java"), ("opportunity-scanner", "Python"), ("Cataclysm-BN", "C++")]
PLACE = "INDIA"   # shown under your name; edit or delete
ROSE, TEAL, VIOLET = "#ff6b8b", "#7fd6c2", "#8b7bff"
FONTS = (ROOT / "scripts" / "fonts.css").read_text()

ANIM_CSS = """
@keyframes bob{
  0%,100%{transform:translate(0px,0px) rotate(-1.1deg)}
  33%{transform:translate(2.5px,-7px) rotate(0.9deg)}
  68%{transform:translate(-2px,-3.5px) rotate(1.3deg)}
}
@keyframes sway{
  0%,100%{transform:rotate(-2.4deg)}
  45%{transform:rotate(2.6deg)}
  75%{transform:rotate(-1.2deg)}
}
@keyframes flame{
  0%,100%{opacity:.86;transform:scale(1)}
  14%{opacity:1;transform:scale(1.03)}
  29%{opacity:.90;transform:scale(.98)}
  48%{opacity:.99;transform:scale(1.02)}
  63%{opacity:.84;transform:scale(.97)}
  81%{opacity:.96;transform:scale(1.01)}
}
@keyframes ember{
  0%{transform:translate(0px,0px) scale(.8);opacity:0}
  18%{opacity:.75}
  80%{opacity:.35}
  100%{transform:translate(var(--ex,8px),-48px) scale(.3);opacity:0}
}
@keyframes glint{
  0%,76%,100%{opacity:.35;transform:scale(.85)}
  88%{opacity:1;transform:scale(1.22)}
}
@keyframes shoot{
  0%,91%{transform:translate(0px,0px);opacity:0}
  93%{opacity:.9}
  98%{transform:translate(-190px,76px);opacity:0}
  100%{transform:translate(-190px,76px);opacity:0}
}
@keyframes moonBreathe{
  0%,100%{opacity:.78;transform:scale(1)}
  50%{opacity:1;transform:scale(1.07)}
}
@keyframes driftA{0%,100%{transform:translateX(-11px)}50%{transform:translateX(11px)}}
@keyframes driftB{0%,100%{transform:translateX(9px)}50%{transform:translateX(-9px)}}
@keyframes driftC{0%,100%{transform:translateX(-7px)}50%{transform:translateX(12px)}}
.bob{animation:bob 11.3s ease-in-out infinite}
.sw{animation:sway 11.3s ease-in-out infinite}
.fl{animation:flame 4.1s ease-in-out infinite}
.em{animation:ember 7.9s ease-out infinite}
.sg{animation:glint 15s ease-in-out infinite}
.sh{animation:shoot 26s linear infinite}
.mg{animation:moonBreathe 17s ease-in-out infinite;transform-origin:880px 100px}
.mg2{animation:moonBreathe 23s ease-in-out infinite reverse;transform-origin:880px 100px}
.au1{animation:driftA 17s ease-in-out infinite}
.au2{animation:driftB 23s ease-in-out infinite}
.au3{animation:driftC 29s ease-in-out infinite}
"""

BASE = (FONTS + ".n{font-family:'Inter Tight',Helvetica,Arial,sans-serif;font-weight:700}"
        ".b{font-family:Inter,Helvetica,Arial,sans-serif;font-weight:400}"
        ".m{font-family:Inter,Helvetica,Arial,sans-serif;font-weight:500}" + ANIM_CSS)

THEMES = {
    "night": dict(sky=("#05080f", "#0e1a24", "#2b1b27"), name="#f2efe8", mut="#9aa6a8", orb="#f2efe8",
                  card="#0d1113", line="#ffffff", stars=True, aur=.9, lop=.8,
                  au_bg=("#090b12", "#14101b")),
    "day": dict(sky=("#a9cfe2", "#e9dfd4", "#ffd0bb"), name="#14202a", mut="#4a5d66", orb="#fff1c4",
                card="#f3efe9", line="#000000", stars=False, aur=.35, lop=.5,
                au_bg=("#e6eef2", "#f4ebe4")),
}

def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def get(url):
    req = urllib.request.Request(url if url.startswith("http") else "https://api.github.com" + url)
    req.add_header("Accept", "application/vnd.github+json")
    if TOKEN: req.add_header("Authorization", f"Bearer {TOKEN}")
    try:
        with urllib.request.urlopen(req, timeout=20) as r: return json.load(r)
    except Exception as e:
        print("skip", url, e); return None

def get_yearly_weeks():
    """Fetches 52 weeks of contribution totals via GitHub GraphQL; falls back cleanly offline."""
    fallback = [2,0,4,1,0,0,3,6,2,1,0,0,0,2,5,3,1,0,0,0,4,2,1,0,0,1,3,7,4,2,0,0,1,2,0,0,5,8,6,4,7,9,5,6,8,11,7,5,6,9,12,8]
    if OFFLINE or not TOKEN:
        return fallback
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            weeks { contributionDays { contributionCount } }
          }
        }
      }
    }"""
    body = json.dumps({"query": query, "variables": {"login": OWNER}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, method="POST")
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            res = json.load(r)
        weeks = res["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
        return [sum(d["contributionCount"] for d in w["contributionDays"]) for w in weeks][-52:]
    except Exception as e:
        print("skip graphql", e)
        return fallback

def load():
    default = ([("Java", .34), ("C++", .28), ("Python", .18), ("JavaScript", .12)], 24, dict(PROJECTS), get_yearly_weeks())
    if OFFLINE: return default
    w = Counter()
    for r in get(f"/users/{OWNER}/repos?per_page=100&type=owner") or []:
        if r.get("language"): w[r["language"]] += 0.5 if r.get("fork") else 1.0
    total = sum(w.values())
    langs = [(n, v / total) for n, v in w.most_common(4)] if total else default[0]
    since = datetime.now(timezone.utc) - timedelta(days=30); commits = 0
    for e in get(f"/users/{OWNER}/events/public?per_page=100") or []:
        if e.get("type") == "PushEvent" and datetime.fromisoformat(e["created_at"].replace("Z", "+00:00")) > since:
            commits += e.get("payload", {}).get("size", 1)
    plang = {n: ((get(f"/repos/{OWNER}/{n}") or {}).get("language")) or fb for n, fb in PROJECTS}
    return langs, commits, plang, get_yearly_weeks()

def defs(T):
    d = ""
    for n, c in (("rose", ROSE), ("teal", TEAL), ("violet", VIOLET)):
        d += f'<radialGradient id="g_{n}"><stop offset="0" stop-color="{c}" stop-opacity=".5"/><stop offset="1" stop-color="{c}" stop-opacity="0"/></radialGradient>'
    d += f'<radialGradient id="orb"><stop offset="0" stop-color="{T["orb"]}" stop-opacity=".45"/><stop offset="1" stop-color="{T["orb"]}" stop-opacity="0"/></radialGradient>'
    d += f'<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{T["sky"][0]}"/><stop offset=".55" stop-color="{T["sky"][1]}"/><stop offset="1" stop-color="{T["sky"][2]}"/></linearGradient>'
    return d

def wrap(w, h, aria, T, body, extra=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{esc(aria)}"><title>{esc(aria)}</title>'
            f'<style>{BASE}</style><defs>{defs(T)}{extra}<clipPath id="card"><rect width="{w}" height="{h}" rx="18"/></clipPath></defs><g clip-path="url(#card)">{body}</g></svg>')

def blob(cx, cy, r, name, dx, dy, dur, op=1.0, begin=0):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#g_{name})" opacity="{op}"><animateTransform attributeName="transform" type="translate" values="0 0;{dx} {dy};0 0" keyTimes="0;.5;1" dur="{dur}s" begin="-{begin}s" repeatCount="indefinite" calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1"/></circle>')

COLS = ["#ff9a5c", "#ffd88a", "#ff6b8b", "#ffb86b"]
SLOTS = [(690, 400), (890, 290), (470, 470), (260, 490)]
PRIME_DURS = [11.3, 8.7, 13.1, 9.7]

def lantern(i, cx, cy, bh, col, name, pct, projects, T):
    bw = bh * .85; gid = f"lg{i}"
    dur = PRIME_DURS[i % len(PRIME_DURS)]
    delay = round(-i * 2.3, 1)
    g = f'<radialGradient id="{gid}"><stop offset="0" stop-color="{col}" stop-opacity="{T["lop"]}"/><stop offset="1" stop-color="{col}" stop-opacity="0"/></radialGradient>'
    embers = ""
    for j, (dx, edur, edel) in enumerate(((-10, 6.7, -1.1), (7, 8.3, -4.2), (14, 10.1, -2.7))):
        ex = cx + dx * 0.8
        ey = cy - bh * 0.45
        embers += f'<circle class="em" style="--ex:{dx}px;animation-duration:{edur}s;animation-delay:{edel - i:.1f}s" cx="{ex:.1f}" cy="{ey:.1f}" r="1.3" fill="#ffd88a"/>'
    o = (embers
         + f'<circle class="fl" style="transform-origin:{cx}px {cy}px;animation-delay:{-i * .9:.1f}s" cx="{cx}" cy="{cy}" r="{bh * 1.3:.0f}" fill="url(#{gid})"/>'
         + f'<rect x="{cx - bw * .2:.1f}" y="{cy - bh / 2 - 8:.1f}" width="{bw * .4:.1f}" height="10" rx="3" fill="{col}"/>'
         + f'<rect x="{cx - bw / 2:.1f}" y="{cy - bh / 2:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="{bw * .28:.1f}" fill="{col}"/>'
         + f'<rect class="fl" style="transform-origin:{cx}px {cy}px;animation-delay:{-i * .9:.1f}s" x="{cx - bw * .36:.1f}" y="{cy - bh * .38:.1f}" width="{bw * .72:.1f}" height="{bh * .76:.1f}" rx="{bw * .2:.1f}" fill="#fff4dc" fill-opacity=".82"/>'
         + f'<path d="M{cx - bw * .12:.1f} {cy - bh * .38:.1f}V{cy + bh * .38:.1f}M{cx + bw * .12:.1f} {cy - bh * .38:.1f}V{cy + bh * .38:.1f}" stroke="{col}" stroke-opacity=".55" stroke-width="1.4"/>'
         + f'<rect x="{cx - bw * .2:.1f}" y="{cy + bh / 2 - 2:.1f}" width="{bw * .4:.1f}" height="7" rx="3" fill="{col}"/>'
         + f'<text class="m" x="{cx}" y="{cy - bh / 2 - 36:.0f}" text-anchor="middle" font-size="18" fill="{T["name"]}">{esc(name)}</text>'
         + f'<text class="b" x="{cx}" y="{cy - bh / 2 - 16:.0f}" text-anchor="middle" font-size="14" fill="{T["mut"]}">{pct}%</text>')
    if projects:
        anchor_y = cy + bh / 2 + 5
        last = cy + bh / 2 + 16 + (len(projects) - 1) * 28
        tg = f'<path d="M{cx} {anchor_y:.1f}V{last:.1f}" stroke="{col}" stroke-opacity=".8" stroke-width="1.2"/>'
        for k, pn in enumerate(projects):
            tw = len(pn) * 6.4 + 22; ty = cy + bh / 2 + 16 + k * 28
            tg += (f'<rect x="{cx - tw / 2:.1f}" y="{ty:.1f}" width="{tw:.1f}" height="21" rx="6" fill="{ROSE}"/>'
                   f'<text class="m" x="{cx}" y="{ty + 14.5:.1f}" text-anchor="middle" font-size="11" fill="#0d1113">{esc(pn)}</text>')
        o += f'<g class="sw" style="transform-origin:{cx}px {anchor_y:.1f}px;animation-duration:{dur}s;animation-delay:{delay + 0.55:.2f}s">{tg}</g>'
    return f'<defs>{g}</defs><g class="bob" style="transform-origin:{cx}px {cy}px;animation-duration:{dur}s;animation-delay:{delay}s">{o}</g>'

def hero(theme, data):
    T = THEMES[theme]; W, H = 1000, 600
    langs, commits, plang, _ = data; rnd = random.Random(7)
    o = f'<rect width="{W}" height="{H}" fill="url(#sky)"/>'
    o += (blob(820, 190, 300, "rose", -70, 30, 30, T["aur"]) + blob(300, 120, 260, "teal", 80, 20, 36, T["aur"], 9) + blob(560, 50, 240, "violet", -50, 40, 42, T["aur"], 17))
    if T["stars"]:
        for k in range(min(120, 40 + commits * 2)):
            x, y, r = rnd.uniform(8, 992), rnd.uniform(8, 400), rnd.uniform(.7, 1.6)
            if k % 11 == 0:
                gdur = rnd.uniform(13.0, 19.0)
                gdel = rnd.uniform(0, 15.0)
                spark = f'<path d="M{x - 5:.0f} {y:.0f}H{x + 5:.0f}M{x:.0f} {y - 5:.0f}V{y + 5:.0f}" stroke="#fff" stroke-width=".85" stroke-linecap="round"/>'
                o += f'<g class="sg" style="transform-origin:{x:.0f}px {y:.0f}px;animation-duration:{gdur:.1f}s;animation-delay:-{gdel:.1f}s"><circle cx="{x:.0f}" cy="{y:.0f}" r="{r * 3.4:.1f}" fill="#fff" opacity=".18"/><circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="#fff"/>{spark}</g>'
            else:
                o += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="#fff" opacity="{rnd.uniform(.28, .78):.2f}"/>'
        # One rare shooting star across the upper-right sky
        o += '<line class="sh" x1="810" y1="36" x2="862" y2="15" stroke="url(#shootGrad)" stroke-width="1.3" stroke-linecap="round"/>'
    else:
        for cx, cy, sc, dur in ((200, 120, 1.0, 60), (620, 90, .8, 80), (760, 150, 1.0, 70)):
            o += (f'<g opacity=".7"><ellipse cx="{cx}" cy="{cy}" rx="{70 * sc}" ry="{14 * sc}" fill="#fff"/><ellipse cx="{cx + 40 * sc}" cy="{cy - 8 * sc}" rx="{44 * sc}" ry="{12 * sc}" fill="#fff"/>'
                  f'<animateTransform attributeName="transform" type="translate" values="-30 0;30 0;-30 0" dur="{dur}s" repeatCount="indefinite"/></g>')
    o += (f'<g class="mg"><circle cx="880" cy="100" r="124" fill="url(#orb)"/></g><g class="mg2"><circle cx="880" cy="100" r="58" fill="url(#orb)"/></g>'
          f'<circle cx="880" cy="100" r="24" fill="{T["orb"]}"/><circle cx="872" cy="94" r="5" fill="#000" fill-opacity=".07"/><circle cx="889" cy="108" r="3.5" fill="#000" fill-opacity=".07"/>')
    o += (f'<text class="n" x="52" y="170" font-size="92" letter-spacing="-3" fill="{T["name"]}">Harshvardhan</text>'
          f'<text class="n" x="52" y="262" font-size="92" letter-spacing="-3" fill="{T["name"]}">Chouhan</text>'
          f'<text class="m" x="56" y="306" font-size="13" letter-spacing="6" fill="{T["mut"]}">AI   ·   BACKEND SYSTEMS   ·   DATA</text>'
          + (f'<text class="m" x="56" y="334" font-size="13" letter-spacing="6" fill="{T["mut"]}">{PLACE}</text>' if PLACE else ""))
    tags = {}
    for pn, pl in plang.items():
        idx = next((i for i, (n, _) in enumerate(langs[:4]) if n.lower() == (pl or "").lower()), 0)
        tags.setdefault(idx, []).append(pn)
    maxs = langs[0][1]
    for i, (n, s) in enumerate(langs[:4]):
        cx, cy = SLOTS[i]
        o += lantern(i, cx, cy, 70 + 50 * s / maxs, COLS[i], n, round(s * 100), tags.get(i, []), T)
    o += f'<text class="b" x="44" y="{H - 20}" font-size="12" fill="{T["mut"]}">lanterns are languages, tags are projects, stars are commits   ·   {commits} commits in the last 30 days</text>'
    extra = '<linearGradient id="shootGrad" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity=".95"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
    (A / f"hero-{theme}.svg").write_text(wrap(W, H, "Harshvardhan Chouhan. AI, backend systems and data. Glowing sky lanterns where each lantern is a language, tags are projects and stars are commits.", T, o, extra))

def smooth_curtain(pts, H):
    """Builds a smooth closed cubic Bezier ribbon anchored to the bottom edge."""
    d = f"M{pts[0][0]:.1f} {H} L{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]; x1, y1 = pts[i + 1]
        mx = (x0 + x1) / 2
        d += f" C{mx:.1f} {y0:.1f},{mx:.1f} {y1:.1f},{x1:.1f} {y1:.1f}"
    return d + f" L{pts[-1][0]:.1f} {H} Z"

def aurora(theme, weeks):
    T = THEMES[theme]; W, H = 1000, 260
    mx = max(max(weeks), 1)
    n = len(weeks)
    extra = (f'<linearGradient id="aubg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{T["au_bg"][0]}"/><stop offset="1" stop-color="{T["au_bg"][1]}"/></linearGradient>'
             f'<linearGradient id="cur1" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{VIOLET}" stop-opacity=".75"/><stop offset=".65" stop-color="{VIOLET}" stop-opacity=".22"/><stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></linearGradient>'
             f'<linearGradient id="cur2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{TEAL}" stop-opacity=".68"/><stop offset=".65" stop-color="{TEAL}" stop-opacity=".18"/><stop offset="1" stop-color="{TEAL}" stop-opacity="0"/></linearGradient>'
             f'<linearGradient id="cur3" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{ROSE}" stop-opacity=".65"/><stop offset=".65" stop-color="{ROSE}" stop-opacity=".18"/><stop offset="1" stop-color="{ROSE}" stop-opacity="0"/></linearGradient>'
             f'<linearGradient id="shimmer" x1="0" y1="1" x2="0" y2="0">'
             f'<animate attributeName="y1" values="1.4;-0.4;1.4" dur="14s" repeatCount="indefinite"/>'
             f'<animate attributeName="y2" values="0.6;-1.2;0.6" dur="14s" repeatCount="indefinite"/>'
             f'<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".14"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')
    o = f'<rect width="{W}" height="{H}" fill="url(#aubg)"/>'
    if T["stars"]:
        rnd = random.Random(42)
        for _ in range(18):
            o += f'<circle cx="{rnd.uniform(24, 976):.0f}" cy="{rnd.uniform(14, 110):.0f}" r="{rnd.uniform(.9, 1.6):.1f}" fill="#fff" opacity="{rnd.uniform(.35, .85):.2f}"/>'
    base_y = H - 24
    # Three slightly offset curtains driven by the same yearly commit data
    for cls, fill, x_off, scale in (("au1", "url(#cur1)", -14, 1.0), ("au2", "url(#cur2)", 0, 0.92), ("au3", "url(#cur3)", 14, 0.86)):
        pts = []
        for idx, c in enumerate(weeks):
            x = -20 + (W + 40) * idx / max(n - 1, 1) + x_off
            amp = math.pow(c / mx, 0.72) * 168 * scale
            y = base_y - amp
            pts.append((x, y))
        path_d = smooth_curtain(pts, H)
        o += f'<g class="{cls}"><path d="{path_d}" fill="{fill}"/><path d="{path_d}" fill="url(#shimmer)"/></g>'
    total_year = sum(weeks)
    o += f'<text class="b" x="28" y="{H - 12}" font-size="11" fill="{T["mut"]}">aurora year   ·   {total_year} contributions across 52 weeks</text>'
    o += f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="18" fill="none" stroke="{T["line"]}" stroke-opacity=".1"/>'
    (A / f"aurora-{theme}.svg").write_text(wrap(W, H, f"Aurora year: {total_year} GitHub contributions across 52 weeks.", T, o, extra))

def notes(theme):
    T = THEMES[theme]; W, H = 1000, 200
    cols = [("NOW", ["Third year of CS. Backend in Java", "and Spring Boot, plus data and AI."]),
            ("FREELANCE", ["Made websites for local businesses.", "Handshake AI × Google participant."]),
            ("OPEN SOURCE", ["Sending fixes to Cataclysm-BN,", "an open source C++ roguelike."])]
    o = (f'<rect width="{W}" height="{H}" fill="{T["card"]}"/>' + blob(120, 200, 220, "rose", 50, -20, 30, .6 if theme == "night" else .3) + blob(900, 0, 220, "teal", -40, 30, 36, .5 if theme == "night" else .25, 7))
    for i, (lb, ls) in enumerate(cols):
        x = 44 + i * 328
        o += f'<text class="m" x="{x}" y="58" font-size="11" letter-spacing="4" fill="{T["mut"]}">{lb}</text>'
        o += "".join(f'<text class="b" x="{x}" y="{100 + k * 28}" font-size="16" fill="{T["name"]}">{esc(t)}</text>' for k, t in enumerate(ls))
        if i: o += f'<path d="M{x - 24} 40V160" stroke="{T["line"]}" stroke-opacity=".12"/>'
    o += f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="18" fill="none" stroke="{T["line"]}" stroke-opacity=".1"/>'
    (A / f"notes-{theme}.svg").write_text(wrap(W, H, "Now: third year of CS, backend in Java and Spring Boot. Freelance: websites for local businesses. Open source: fixes for Cataclysm-BN.", T, o))

def button(fname, label, c1, c2):
    spin = '<animateTransform attributeName="gradientTransform" type="rotate" from="0 .5 .5" to="360 .5 .5" dur="8s" repeatCount="indefinite"/>'
    d = f'<linearGradient id="bg1" x1="0" y1="0" x2="1" y2="1">{spin}<stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient>'
    body = (f'<rect x="6" y="6" width="158" height="44" rx="22" fill="none" stroke="url(#bg1)" stroke-width="5" stroke-opacity=".28"/>'
            f'<rect x="6" y="6" width="158" height="44" rx="22" fill="#101516" stroke="url(#bg1)" stroke-width="1.4"/>'
            f'<text class="m" x="85" y="33" text-anchor="middle" font-size="15" fill="#ece9e1">{label}</text>')
    (A / fname).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 170 56" width="170" height="56" role="img" aria-label="{label}"><title>{label}</title><style>{BASE}</style><defs>{d}</defs>{body}</svg>')

if __name__ == "__main__":
    A.mkdir(exist_ok=True); data = load()
    for t in THEMES:
        hero(t, data)
        notes(t)
        aurora(t, data[3])
    button("btn-repos.svg", "Repositories", "#ece9e1", "#8a918b")
    button("btn-email.svg", "Email me", ROSE, VIOLET)
    print("built", [(n, round(s, 2)) for n, s in data[0]], "commits30", data[1], "year", sum(data[3]))