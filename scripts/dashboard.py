#!/usr/bin/env python3
"""Visual growth dashboard for latam-data-mcp.

Fetches live metrics (GitHub via `gh`, PyPI via pypistats, the MCP registry),
appends a daily snapshot to a local history file, renders a self-contained HTML
dashboard, and opens it in the browser.

    python scripts/dashboard.py
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

REPO = "svkbogislav/latam-data-mcp"
PYPI = "latam-data-mcp"
ROOT = Path(__file__).resolve().parent.parent
HISTORY = ROOT / ".metrics-history.jsonl"
OUT = ROOT / "dashboard.html"
LOGO = ROOT / "assets" / "logo-256.png"


def gh(path: str):
    try:
        r = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=30)
        return json.loads(r.stdout) if r.returncode == 0 else None
    except Exception:
        return None


def get_json(url: str, timeout: int = 25):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "latam-mcp-dashboard"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


def collect() -> dict:
    repo = gh(f"repos/{REPO}") or {}
    views = gh(f"repos/{REPO}/traffic/views") or {}
    clones = gh(f"repos/{REPO}/traffic/clones") or {}
    referrers = gh(f"repos/{REPO}/traffic/popular/referrers") or []
    pypi = get_json(f"https://pypistats.org/api/packages/{PYPI}/recent") or {}
    pd = pypi.get("data", {})

    def pr_state(repo_slug, num):
        d = gh(f"repos/{repo_slug}/pulls/{num}")
        if not d:
            return "?"
        return "merged" if d.get("merged_at") else d.get("state", "?")

    return {
        "date": date.today().isoformat(),
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "stars": repo.get("stargazers_count", 0),
        "forks": repo.get("forks_count", 0),
        "watchers": repo.get("subscribers_count", 0),
        "issues": repo.get("open_issues_count", 0),
        "views": views.get("count", 0),
        "views_unique": views.get("uniques", 0),
        "clones": clones.get("count", 0),
        "clones_unique": clones.get("uniques", 0),
        "referrers": [{"referrer": r.get("referrer"), "count": r.get("count"),
                       "uniques": r.get("uniques")} for r in referrers[:8]],
        "pypi_day": pd.get("last_day"),
        "pypi_week": pd.get("last_week"),
        "pypi_month": pd.get("last_month"),
        "pr_punkpeye": pr_state("punkpeye/awesome-mcp-servers", 10033),
        "pr_tensorblock": pr_state("TensorBlock/awesome-mcp-servers", 1203),
    }


def load_history() -> list[dict]:
    if not HISTORY.exists():
        return []
    out = []
    for line in HISTORY.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def save_snapshot(snap: dict, hist: list[dict]) -> list[dict]:
    hist = [h for h in hist if h.get("date") != snap["date"]]  # replace today
    hist.append({k: snap[k] for k in
                 ("date", "stars", "forks", "views_unique", "clones_unique",
                  "pypi_day", "pypi_week")})
    hist.sort(key=lambda h: h.get("date", ""))
    with HISTORY.open("w") as f:
        for h in hist:
            f.write(json.dumps(h) + "\n")
    return hist


def sparkline(points: list[float], w: int = 260, h: int = 56, color: str = "#34d399") -> str:
    vals = [p for p in points if p is not None]
    if len(vals) < 2:
        return ('<div class="spark-empty">— la tendencia aparece tras unos días —</div>')
    lo, hi = min(vals), max(vals)
    rng = (hi - lo) or 1
    n = len(vals)
    pts = []
    for i, v in enumerate(vals):
        x = round(i / (n - 1) * (w - 8) + 4, 1)
        y = round(h - 6 - (v - lo) / rng * (h - 12), 1)
        pts.append(f"{x},{y}")
    poly = " ".join(pts)
    last_x, last_y = pts[-1].split(",")
    return (f'<svg viewBox="0 0 {w} {h}" width="100%" height="{h}" preserveAspectRatio="none">'
            f'<polyline points="{poly}" fill="none" stroke="{color}" stroke-width="2.5" '
            f'stroke-linejoin="round" stroke-linecap="round"/>'
            f'<circle cx="{last_x}" cy="{last_y}" r="3.5" fill="{color}"/></svg>')


def card(label, value, sub="", accent=False):
    cls = "card accent" if accent else "card"
    sub = f'<div class="sub">{sub}</div>' if sub else ""
    return f'<div class="{cls}"><div class="label">{label}</div><div class="value">{value}</div>{sub}</div>'


def delta(hist, key):
    if len(hist) < 2:
        return ""
    a, b = hist[-2].get(key), hist[-1].get(key)
    if a is None or b is None:
        return ""
    d = b - a
    if d == 0:
        return '<span class="d flat">±0</span>'
    sign = "+" if d > 0 else ""
    cls = "up" if d > 0 else "down"
    return f'<span class="d {cls}">{sign}{d}</span>'


def render(snap: dict, hist: list[dict]) -> str:
    logo_b64 = base64.b64encode(LOGO.read_bytes()).decode() if LOGO.exists() else ""
    stars_hist = [h.get("stars") for h in hist]
    dl_hist = [h.get("pypi_week") for h in hist]

    # referrers
    ref_rows = ""
    channels = {"reddit.com": "Reddit", "glama.ai": "Glama", "mcp.so": "mcp.so",
                "pulsemcp.com": "PulseMCP", "news.ycombinator.com": "Hacker News"}
    for r in snap["referrers"]:
        name = r["referrer"] or "?"
        hot = any(c in (name or "") for c in channels)
        badge = ' <span class="hot">canal 🔥</span>' if hot else ""
        ref_rows += (f'<tr><td>{name}{badge}</td><td>{r["uniques"]}</td>'
                     f'<td>{r["count"]}</td></tr>')
    if not ref_rows:
        ref_rows = '<tr><td colspan="3" class="muted">sin referrers aún</td></tr>'

    # signals
    week = snap["pypi_week"]
    reddit_seen = any("reddit" in (r["referrer"] or "") for r in snap["referrers"])
    sig_downloads = ("✅ tráfico sostenido" if (week and week > 200)
                     else "⏳ esperando tendencia real (ojo: día 1 son bots)")
    sig_reddit = "✅ detectado" if reddit_seen else "⏳ no aún"
    sig_issues = (f"⚠️ {snap['issues']} abiertos — ¡revísalos!" if snap["issues"] else "0")
    monet = ("🟢 posible señal de compra — revisa issues/descargas"
             if (snap["issues"] > 0 or (week and week > 200)) else
             "⚪ aún no — gatillo: descargas semanales reales sostenidas o alguien pidiendo hosted")

    pr_badge = lambda s: (f'<span class="pill ok">{s}</span>' if s == "merged"
                          else f'<span class="pill open">{s}</span>' if s == "open"
                          else f'<span class="pill">{s}</span>')

    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LatAm Data MCP — Dashboard</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,"SF Pro Text",system-ui,sans-serif;
  background:radial-gradient(800px 500px at 20% -5%,rgba(16,185,129,.14),transparent 60%),#0a1220;
  color:#e6edf3;padding:28px;max-width:1080px;margin:0 auto;line-height:1.4}}
.head{{display:flex;align-items:center;gap:16px;margin-bottom:6px}}
.head img{{width:52px;height:52px;border-radius:13px}}
h1{{font-size:24px;font-weight:800;letter-spacing:-.5px}}
h1 span{{color:#34d399}}
.ts{{color:#8b98a5;font-size:13px;margin-bottom:22px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;margin-bottom:24px}}
.card{{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);
  border-radius:16px;padding:16px 18px}}
.card.accent{{border-color:rgba(52,211,153,.35);background:rgba(16,185,129,.07)}}
.label{{font-size:12px;color:#8b98a5;text-transform:uppercase;letter-spacing:.6px;font-weight:600}}
.value{{font-size:34px;font-weight:800;letter-spacing:-1px;margin-top:4px}}
.sub{{font-size:12px;color:#8b98a5;margin-top:3px}}
.d{{font-size:14px;font-weight:700;margin-left:6px}}
.d.up{{color:#34d399}}.d.down{{color:#f87171}}.d.flat{{color:#8b98a5}}
.row{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:22px}}
@media(max-width:720px){{.row{{grid-template-columns:1fr}}}}
.panel{{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);
  border-radius:16px;padding:18px 20px}}
.panel h2{{font-size:13px;text-transform:uppercase;letter-spacing:.6px;color:#8b98a5;
  margin-bottom:14px;font-weight:700}}
.spark-empty{{color:#5b6672;font-size:13px;padding:16px 0;text-align:center}}
table{{width:100%;border-collapse:collapse;font-size:14px}}
td,th{{text-align:left;padding:7px 4px;border-bottom:1px solid rgba(255,255,255,.06)}}
th{{color:#8b98a5;font-size:11px;text-transform:uppercase;letter-spacing:.5px}}
td:nth-child(2),td:nth-child(3),th:nth-child(2),th:nth-child(3){{text-align:right}}
.hot{{color:#34d399;font-weight:700;font-size:12px}}
.muted{{color:#5b6672;text-align:center}}
.pill{{padding:2px 9px;border-radius:20px;font-size:12px;font-weight:700;
  background:rgba(255,255,255,.08);color:#c9d3dd}}
.pill.ok{{background:rgba(52,211,153,.18);color:#34d399}}
.pill.open{{background:rgba(96,165,250,.16);color:#93c5fd}}
.sig{{display:flex;justify-content:space-between;padding:9px 0;
  border-bottom:1px solid rgba(255,255,255,.06);font-size:14px}}
.sig b{{color:#e6edf3}}
.note{{background:rgba(251,191,36,.08);border:1px solid rgba(251,191,36,.2);
  border-radius:12px;padding:12px 16px;font-size:13px;color:#d9c48a;margin-top:8px}}
.foot{{color:#5b6672;font-size:12px;margin-top:26px;text-align:center}}
</style></head><body>
<div class="head">
  {'<img src="data:image/png;base64,'+logo_b64+'">' if logo_b64 else ''}
  <div><h1>LatAm Data <span>MCP</span> · Dashboard</h1></div>
</div>
<div class="ts">Actualizado: {snap['ts']} · {len(hist)} día(s) de historial</div>

<div class="grid">
  {card("⭐ Stars", str(snap['stars']) + delta(hist,'stars'), "personas a las que les importó", accent=True)}
  {card("📦 PyPI / semana", snap['pypi_week'] if snap['pypi_week'] is not None else "sin datos", "incluye bots/mirrors")}
  {card("👁️ Views únicos (14d)", str(snap['views_unique']) + delta(hist,'views_unique'), "gente mirando el repo")}
  {card("🍴 Forks", str(snap['forks']), "")}
  {card("🐛 Issues", str(snap['issues']), "feedback / leads")}
</div>

<div class="row">
  <div class="panel"><h2>Tendencia · Stars</h2>{sparkline(stars_hist)}</div>
  <div class="panel"><h2>Tendencia · Descargas semana</h2>{sparkline(dl_hist,color='#60a5fa')}</div>
</div>

<div class="row">
  <div class="panel">
    <h2>Referrers (de dónde llega la gente)</h2>
    <table><tr><th>Fuente</th><th>Únicos</th><th>Total</th></tr>{ref_rows}</table>
  </div>
  <div class="panel">
    <h2>Señales</h2>
    <div class="sig"><span>Tráfico Reddit</span><b>{sig_reddit}</b></div>
    <div class="sig"><span>Descargas reales</span><b>{sig_downloads}</b></div>
    <div class="sig"><span>Issues (leads)</span><b>{sig_issues}</b></div>
    <div class="sig"><span>PR punkpeye</span>{pr_badge(snap['pr_punkpeye'])}</div>
    <div class="sig"><span>PR TensorBlock</span>{pr_badge(snap['pr_tensorblock'])}</div>
    <div class="sig"><span>💰 Señal monetización</span><b style="font-size:12px">{monet}</b></div>
  </div>
</div>

<div class="note">⚠️ Las descargas de PyPI de un paquete nuevo son en su mayoría
mirrors/bots automáticos, no personas. Juzga por la <b>tendencia sostenida</b> y por
las señales humanas: stars, referrers de Reddit, e issues.</div>

<div class="foot">latam-data-mcp · corre <code>python scripts/dashboard.py</code> para refrescar ·
<a href="https://github.com/{REPO}" style="color:#60a5fa">GitHub</a> ·
<a href="https://pypi.org/project/{PYPI}/" style="color:#60a5fa">PyPI</a></div>
</body></html>"""


def main():
    print("Recolectando métricas…")
    snap = collect()
    hist = save_snapshot(snap, load_history())
    OUT.write_text(render(snap, hist))
    print(f"Dashboard generado: {OUT}")
    if os.environ.get("NO_OPEN") != "1":
        subprocess.run(["open", str(OUT)], check=False)


if __name__ == "__main__":
    main()
