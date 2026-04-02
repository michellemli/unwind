#!/usr/bin/env python3
"""
Local Pulse — events dashboard HTTP server.

Serves the static frontend from public/ and exposes two API endpoints:

    GET  /api/events         — return events (from cache if fresh)
    POST /api/events/refresh — bust cache and re-scrape immediately

Run:
    python3 server.py

Requires:
    pip install requests beautifulsoup4
"""

import json
import os
import sys
import threading
from datetime import datetime, date, timedelta
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

from config import PORT
from export import export_csv
from scrapers import scrape_all, invalidate_cache, cache_info

LAST_REFRESH_FILE = os.path.join(os.path.dirname(__file__), "exports", ".last_refresh")


def _read_last_refresh_date():
    try:
        with open(LAST_REFRESH_FILE) as f:
            return date.fromisoformat(f.read().strip())
    except Exception:
        return None


def _write_last_refresh_date(d: date):
    os.makedirs(os.path.dirname(LAST_REFRESH_FILE), exist_ok=True)
    with open(LAST_REFRESH_FILE, "w") as f:
        f.write(d.isoformat())


def _do_daily_refresh():
    """Invalidate cache, scrape, and export CSV. Called once per day."""
    print(f"[scheduler] Daily refresh started at {datetime.now().strftime('%H:%M:%S')}")
    invalidate_cache()
    events = scrape_all()
    path = export_csv(events)
    _write_last_refresh_date(date.today())
    print(f"[scheduler] Done — {len(events)} events → {path}")


def _seconds_until_midnight():
    now = datetime.now()
    midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return (midnight - now).total_seconds()


def _schedule_loop():
    """Run daily refresh now if needed, then repeat every day at midnight."""
    if _read_last_refresh_date() != date.today():
        _do_daily_refresh()
    # Sleep until next midnight, then loop
    while True:
        time.sleep(_seconds_until_midnight() + 5)  # +5s past midnight
        _do_daily_refresh()


import time  # noqa: E402 (after the functions that reference it)


class Handler(SimpleHTTPRequestHandler):
    """Thin HTTP handler: routes /api/* requests; serves public/ for everything else."""

    _public_dir = os.path.join(os.path.dirname(__file__), "public")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=self._public_dir, **kwargs)

    # ------------------------------------------------------------------
    # Logging — only print API requests, suppress static-file noise
    # ------------------------------------------------------------------
    def log_message(self, fmt, *args):
        if "/api/" in str(args[0]):
            print(f"  {self.address_string()}  {args[0]}  {args[1]}")

    # ------------------------------------------------------------------
    # API routes
    # ------------------------------------------------------------------
    def do_GET(self):
        if urlparse(self.path).path == "/api/events":
            events = scrape_all()
            self._send_json({
                "events": events,
                "scraped_at": datetime.utcnow().isoformat() + "Z",
                "cache": cache_info(),
            })
        else:
            super().do_GET()

    def do_POST(self):
        self._send_json({"error": "Not found"}, status=404)

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _send_json(self, payload: dict, status: int = 200):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")


if __name__ == "__main__":
    try:
        import requests  # noqa: F401
        from bs4 import BeautifulSoup  # noqa: F401
    except ImportError:
        print("Missing dependencies. Run:  pip3 install requests beautifulsoup4\n")
        sys.exit(1)

    t = threading.Thread(target=_schedule_loop, daemon=True)
    t.start()

    httpd = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Girls Just Want to Have Fun → http://localhost:{PORT}")
    print("Ctrl+C to stop.\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
