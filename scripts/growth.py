#!/usr/bin/env python3
"""Growth dashboard for latam-data-mcp — one glance at every adoption signal.

Pulls live numbers from GitHub (via the `gh` CLI, using your existing auth),
PyPI (pypistats), and the official MCP registry. No secrets stored here.

Usage:  python scripts/growth.py
"""

from __future__ import annotations

import json
import subprocess
import urllib.request

REPO = "svkbogislav/latam-data-mcp"
PYPI = "latam-data-mcp"
REGISTRY_NAME = "io.github.svkbogislav/latam-data-mcp"


def gh(path: str):
    try:
        out = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=30)
        if out.returncode != 0:
            return None
        return json.loads(out.stdout)
    except Exception:
        return None


def get_json(url: str, timeout: int = 30):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "latam-data-mcp-growth"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception:
        return None


def line(label: str, value) -> None:
    print(f"  {label:<28} {value}")


def main() -> None:
    print("\n📊  latam-data-mcp — growth dashboard\n" + "=" * 44)

    print("\n⭐ GitHub")
    repo = gh(f"repos/{REPO}")
    if repo:
        line("stars", repo.get("stargazers_count"))
        line("forks", repo.get("forks_count"))
        line("watchers", repo.get("subscribers_count"))
        line("open issues", repo.get("open_issues_count"))
    else:
        line("(unavailable)", "check `gh auth status`")

    views = gh(f"repos/{REPO}/traffic/views")
    clones = gh(f"repos/{REPO}/traffic/clones")
    if views:
        line("views (14d)", f"{views.get('count')} total / {views.get('uniques')} unique")
    if clones:
        line("clones (14d)", f"{clones.get('count')} total / {clones.get('uniques')} unique")
    refs = gh(f"repos/{REPO}/traffic/popular/referrers")
    if refs:
        top = ", ".join(f"{r['referrer']} ({r['count']})" for r in refs[:3]) or "none yet"
        line("top referrers", top)

    print("\n📦 PyPI downloads")
    recent = get_json(f"https://pypistats.org/api/packages/{PYPI}/recent")
    if recent and "data" in recent:
        d = recent["data"]
        line("last day", d.get("last_day"))
        line("last week", d.get("last_week"))
        line("last month", d.get("last_month"))
    else:
        line("(not indexed yet)", "new packages take ~1-2 days to report")

    print("\n🏛️ Official MCP registry")
    reg = get_json(f"https://registry.modelcontextprotocol.io/v0/servers?search=latam-data-mcp", 40)
    found = None
    if reg:
        for s in reg.get("servers", []):
            srv = s.get("server", s)
            if srv.get("name") == REGISTRY_NAME:
                found = srv
                meta = s.get("_meta", {}).get("io.modelcontextprotocol.registry/official", {})
                line("listed", f"yes — v{srv.get('version')} ({meta.get('status', '?')})")
    if not found:
        line("listed", "not returned (API may be slow; confirmed active earlier)")

    print("\n☁️ FastMCP Cloud (hosted)")
    line("usage dashboard", "horizon.prefect.io → latamdata → latam-data → Usage")
    line("(per-tool calls & users)", "view in the Horizon UI — no public API")
    print()


if __name__ == "__main__":
    main()
