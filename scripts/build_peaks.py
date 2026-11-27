"""Builds the sky-lantern profile: lanterns are languages, tags are projects, stars are commits."""
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
BASE = (FONTS + ".n{font-family:'Inter Tight',Helvetica,Arial,sans-serif;font-weight:700}"
        ".b{font-family:Inter,Helvetica,Arial,sans-serif;font-weight:400}.m{font-family:Inter,Helvetica,Arial,sans-serif;font-weight:500}")
THEMES = {
    "night": dict(sky=("#05080f", "#0e1a24", "#2b1b27"), name="#f2efe8", mut="#9aa6a8", orb="#f2efe8", back2="#0c141b", back="#101b23",
                  mid="#18262e", snow="#dfe7e4", snow_op=.55, shade=.28, front="#070b0e", mist="#9fb4b8", mist_op=.08,
                  lab="#e3ebe8", pct="#93a5a7", cap="#7f8d8f", card="#0d1113", line="#ffffff", stars=True, aur=.9, lop=.8),
    "day": dict(sky=("#a9cfe2", "#e9dfd4", "#ffd0bb"), name="#14202a", mut="#4a5d66", orb="#fff1c4", back2="#c3d6df", back="#a5bfcb",
                mid="#6f8d9a", snow="#ffffff", snow_op=.95, shade=.16, front="#1f2f38", mist="#ffffff", mist_op=.4,
                lab="#ffffff", pct="#e3eef2", cap="#dbe6ea", card="#f3efe9", line="#000000", stars=False, aur=.35, lop=.5),
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

def load():
    default = ([("Java", .34), ("C++", .28), ("Python", .18), ("JavaScript", .12)], 24, dict(PROJECTS))
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
    return langs, commits, plang

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

def ridge(rnd, base, lo, hi, step, color):
    pts, x = [], 0
    while x <= 1000 + step:
        pts.append((x, rnd.uniform(lo, hi))); x += step
    d = f"M0 600L0 {pts[0][1]:.0f}" + "".join(f"L{x:.0f} {y:.0f}" for x, y in pts[1:]) + "L1000 600Z"
    return f'<path d="{d}" fill="{color}"/>'

def peak(i, cx, top, base, T, name, pct):
    h = base - top; w = h * .95; r = random.Random(i * 11 + 3)
    def side(t, sgn): return cx + sgn * w * t + r.uniform(-.05, .05) * w, top + h * t
    L = [side(.3, -1), side(.62, -1)]; R = [side(.34, 1), side(.66, 1)]
    pts = [(cx - w, base + 4)] + L[::-1] + [(cx, top)] + R + [(cx + w, base + 4)]
    d = "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z"
    zig = "".join(f"L{cx + w - k * w / 4:.1f} {top + h * (.17 + (.07 if k % 2 else 0) + r.uniform(0, .03)):.1f}" for k in range(9))
    snow = f"M{cx - w:.1f} {top - 2:.1f}L{cx + w:.1f} {top - 2:.1f}" + zig + "Z"
    face = f"M{cx} {top}L{cx + w:.1f} {base}L{cx + w * .08:.1f} {base}Z"
    ly = top + h * .5
    return (f'<clipPath id="pk{i}"><path d="{d}"/></clipPath><path d="{d}" fill="{T["mid"]}"/>'
            f'<g clip-path="url(#pk{i})"><path d="{face}" fill="#000" fill-opacity="{T["shade"]}"/><path d="{snow}" fill="{T["snow"]}" fill-opacity="{T["snow_op"]}"/></g>'
            f'<text class="m" x="{cx}" y="{ly:.0f}" text-anchor="middle" font-size="18" fill="{T["lab"]}">{esc(name)}</text>'
            f'<text class="b" x="{cx}" y="{ly + 22:.0f}" text-anchor="middle" font-size="14" fill="{T["pct"]}">{pct}%</text>'), w

def flag(x, y, label, col, left=False):
    up = 34
    p = lambda a, b: f"{x},{y - up} {x + a},{y - up + 6 + b} {x},{y - up + 12}"
    return (f'<path d="M{x} {y}V{y - up}" stroke="{col}" stroke-opacity=".85" stroke-width="1.6"/>'
            f'<polygon fill="{ROSE}" points="{p(22, 0)}"><animate attributeName="points" dur="2.6s" repeatCount="indefinite" values="{p(22, 0)};{p(19, 3)};{p(22, 0)}"/></polygon>'
            f'<text class="m" x="{x - 8 if left else x + 30}" y="{y - up + 15}" text-anchor="{"end" if left else "start"}" font-size="11" fill="{col}" fill-opacity=".95">{esc(label)}</text>')

COLS = ["#ff9a5c", "#ffd88a", "#ff6b8b", "#ffb86b"]
SLOTS = [(690, 400), (890, 290), (470, 470), (260, 490)]

def lantern(i, cx, cy, bh, col, name, pct, projects, T):
    bw = bh * .85; gid = f"lg{i}"
    g = f'<radialGradient id="{gid}"><stop offset="0" stop-color="{col}" stop-opacity="{T["lop"]}"/><stop offset="1" stop-color="{col}" stop-opacity="0"/></radialGradient>'
    o = (f'<circle class="fl" style="animation-delay:{-i * .7:.1f}s" cx="{cx}" cy="{cy}" r="{bh * 1.3:.0f}" fill="url(#{gid})"/>'
         f'<rect x="{cx - bw * .2:.1f}" y="{cy - bh / 2 - 8:.1f}" width="{bw * .4:.1f}" height="10" rx="3" fill="{col}"/>'
         f'<rect x="{cx - bw / 2:.1f}" y="{cy - bh / 2:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="{bw * .28:.1f}" fill="{col}"/>'
         f'<rect x="{cx - bw * .36:.1f}" y="{cy - bh * .38:.1f}" width="{bw * .72:.1f}" height="{bh * .76:.1f}" rx="{bw * .2:.1f}" fill="#fff4dc" fill-opacity=".8"/>'
         f'<path d="M{cx - bw * .12:.1f} {cy - bh * .38:.1f}V{cy + bh * .38:.1f}M{cx + bw * .12:.1f} {cy - bh * .38:.1f}V{cy + bh * .38:.1f}" stroke="{col}" stroke-opacity=".55" stroke-width="1.4"/>'
         f'<rect x="{cx - bw * .2:.1f}" y="{cy + bh / 2 - 2:.1f}" width="{bw * .4:.1f}" height="7" rx="3" fill="{col}"/>'
         f'<text class="m" x="{cx}" y="{cy - bh / 2 - 36:.0f}" text-anchor="middle" font-size="18" fill="{T["name"]}">{esc(name)}</text>'
         f'<text class="b" x="{cx}" y="{cy - bh / 2 - 16:.0f}" text-anchor="middle" font-size="14" fill="{T["mut"]}">{pct}%</text>')
    if projects:
        last = cy + bh / 2 + 16 + (len(projects) - 1) * 28
        tg = f'<path d="M{cx} {cy + bh / 2 + 5:.1f}V{last:.1f}" stroke="{col}" stroke-opacity=".8" stroke-width="1.2"/>'
        for k, pn in enumerate(projects):
            tw = len(pn) * 6.4 + 22; ty = cy + bh / 2 + 16 + k * 28
            tg += (f'<rect x="{cx - tw / 2:.1f}" y="{ty:.1f}" width="{tw:.1f}" height="21" rx="6" fill="{ROSE}"/>'
                   f'<text class="m" x="{cx}" y="{ty + 14.5:.1f}" text-anchor="middle" font-size="11" fill="#0d1113">{esc(pn)}</text>')
        o += f'<g class="sw" style="animation-delay:{-i * .9:.1f}s">{tg}</g>'
    return f'<defs>{g}</defs><g class="bob" style="animation-duration:{5.4 + i * .8:.1f}s;animation-delay:{-i * 1.4:.1f}s">{o}</g>'

def hero(theme, data):
    T = THEMES[theme]; W, H = 1000, 600
    langs, commits, plang = data; rnd = random.Random(7)
    o = f'<rect width="{W}" height="{H}" fill="url(#sky)"/>'
    o += (blob(820, 190, 300, "rose", -70, 30, 30, T["aur"]) + blob(300, 120, 260, "teal", 80, 20, 36, T["aur"], 9) + blob(560, 50, 240, "violet", -50, 40, 42, T["aur"], 17))
    if T["stars"]:
        for k in range(min(120, 40 + commits * 2)):
            x, y, r = rnd.uniform(8, 992), rnd.uniform(8, 400), rnd.uniform(.7, 1.6)
            st = f'style="animation-duration:{rnd.uniform(2.2, 5.5):.1f}s;animation-delay:-{rnd.uniform(0, 6):.1f}s"'
            spark = f'<path d="M{x - 5:.0f} {y:.0f}H{x + 5:.0f}M{x:.0f} {y - 5:.0f}V{y + 5:.0f}" stroke="#fff" stroke-width=".8" stroke-linecap="round"/>' if k % 9 == 0 else ""
            o += f'<g class="s" {st}><circle cx="{x:.0f}" cy="{y:.0f}" r="{r * 3.4:.1f}" fill="#fff" opacity=".16"/><circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="#fff"/>{spark}</g>'
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
    (A / f"hero-{theme}.svg").write_text(wrap(W, H, "Harshvardhan Chouhan. AI, backend systems and data. Glowing sky lanterns where each lantern is a language, tags are projects and stars are commits.", T, o))

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
    (A / f"notes-{theme}.svg").write_text(wrap(W, H, "Now: third year of CS, backend in Java and Spring Boot. Freelance: made websites for local businesses and participated in Handshake AI x Google. Open source: fixes for Cataclysm-BN.", T, o))

def button(fname, label, c1, c2):
    spin = '<animateTransform attributeName="gradientTransform" type="rotate" from="0 .5 .5" to="360 .5 .5" dur="8s" repeatCount="indefinite"/>'
    d = f'<linearGradient id="bg1" x1="0" y1="0" x2="1" y2="1">{spin}<stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient>'
    body = (f'<rect x="6" y="6" width="158" height="44" rx="22" fill="none" stroke="url(#bg1)" stroke-width="5" stroke-opacity=".28"/>'
            f'<rect x="6" y="6" width="158" height="44" rx="22" fill="#101516" stroke="url(#bg1)" stroke-width="1.4"/>'
            f'<text class="m" x="85" y="33" text-anchor="middle" font-size="15" fill="#ece9e1">{label}</text>')
    (A / fname).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 170 56" width="170" height="56" role="img" aria-label="{label}"><title>{label}</title><style>{BASE}</style><defs>{d}</defs>{body}</svg>')

if __name__ == "__main__":
    A.mkdir(exist_ok=True); data = load()
    for t in THEMES: hero(t, data); notes(t)
    button("btn-repos.svg", "Repositories", "#ece9e1", "#8a918b"); button("btn-email.svg", "Email me", ROSE, VIOLET)
    print("built", [(n, round(s, 2)) for n, s in data[0]], "commits30", data[1])
