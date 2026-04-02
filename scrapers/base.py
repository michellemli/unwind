"""
Shared utilities for all scrapers: HTTP fetch and date formatting.
"""

import sys
from datetime import datetime
from typing import Optional

from config import HTTP_HEADERS

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    import urllib.request


def fetch(url: str, timeout: int = 12) -> Optional[str]:
    """
    Fetch a URL and return the response body as a string.
    Returns None on any error so callers can safely check for falsy results.
    """
    try:
        if HAS_REQUESTS:
            r = requests.get(url, headers=HTTP_HEADERS, timeout=timeout)
            r.raise_for_status()
            return r.text
        else:
            req = urllib.request.Request(url, headers=HTTP_HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  fetch failed [{url[:70]}]: {e}", file=sys.stderr)
        return None


def fmt_date(iso_str: str) -> str:
    """
    Convert an ISO 8601 date/datetime string to a human-readable label.

    Examples:
        "2026-04-10"                  → "Fri, Apr 10"
        "2026-04-10T18:00:00-04:00"  → "Fri, Apr 10 · 6:00 PM"
        "2026-04-10T18:00:00Z"       → "Fri, Apr 10 · 6:00 PM"
    """
    if not iso_str:
        return ""
    try:
        iso = iso_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(iso)
        if "T" in iso_str:
            return dt.strftime("%a, %b %-d · %-I:%M %p")
        return dt.strftime("%a, %b %-d")
    except Exception:
        return iso_str[:16].replace("T", " ")
