#!/usr/bin/env python3
"""Live growth dashboard — a small local server that refreshes with fresh data.

    python scripts/dashboard_live.py

Starts a local server, opens http://localhost:7788, and the page auto-refreshes
pulling current numbers each time. Leave it running (a terminal tab, or in the
background) and keep the browser tab open — no commands to re-run.

Note: GitHub traffic and PyPI downloads only update ~daily at the source, so those
move slowly; stars and issues reflect within a refresh. Ctrl+C to stop.
"""

from __future__ import annotations

import http.server
import os
import socketserver
import sys
import threading
import webbrowser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashboard  # reuse collect / render / history

PORT = int(os.environ.get("DASH_PORT", "7788"))
REFRESH = int(os.environ.get("DASH_REFRESH", "120"))


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/", "/index.html"):
            self.send_response(204)
            self.end_headers()
            return
        try:
            snap = dashboard.collect()
            hist = dashboard.save_snapshot(snap, dashboard.load_history())
            html = dashboard.render(snap, hist, refresh=REFRESH)
        except Exception as e:  # never crash the page
            html = f"<body style='font-family:sans-serif;padding:40px'><h2>error recolectando métricas</h2><pre>{e}</pre></body>"
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # keep the terminal quiet
        pass


def main():
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", PORT), Handler) as httpd:
        url = f"http://localhost:{PORT}"
        print(f"📊 Dashboard EN VIVO: {url}")
        print(f"   auto-refresca cada {REFRESH}s · déjalo corriendo · Ctrl+C para parar")
        if os.environ.get("NO_OPEN") != "1":
            threading.Timer(1.0, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 dashboard detenido")


if __name__ == "__main__":
    main()
