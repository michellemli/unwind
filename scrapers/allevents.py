"""
Allevents.in scraper.

Allevents.in is a server-side rendered event aggregator. Each city page
embeds 50-60 events as JSON-LD <script type="application/ld+json"> blocks
with @type "Event" or "MusicEvent".

Verified structure (April 2026):
    {
      "@type": "Event",
      "name": "...",
      "startDate": "2026-04-04",
      "url": "https://allevents.in/<city>/<slug>/<id>",
      "image": "https://...",
      "location": {
        "name": "Venue Name",
        "address": {
          "@type": "PostalAddress",
          "streetAddress": "...",
          "addressLocality": "Boston"
        }
      }
    }

Notes:
  - NJ has no single city page; Jersey City and Newark are scraped separately
    and merged.
  - The Cambridge page uses the slug "cambridge-ma" to avoid ambiguity with
    Cambridge, UK.
  - allevents.in/new-york-city/ and allevents.in/new-jersey/ both redirect to
    a generic /events/ page with no data — use the slugs listed below instead.

To add a new city:
    1. Find the correct allevents.in/<slug>/ URL (test for 200 + JSON-LD events).
    2. Add a CITIES entry in config.py.
    3. Add a list of (url, default_label) tuples to CITY_PAGES below.
"""

import json
import re
import sys
from typing import List, Optional

from config import CITIES, CITY_ALIASES
from scrapers.base import fetch, fmt_date

MAX_EVENTS_PER_PAGE = 12

# Maps city_key → list of (url, default_city_label) tuples.
# Multiple URLs are fetched and merged (used for NJ which spans two cities).
CITY_PAGES = {
    "boston":      [("https://allevents.in/boston/",       "Boston, MA")],
    "cambridge":   [("https://allevents.in/cambridge-ma/", "Cambridge, MA")],
    "nyc":         [("https://allevents.in/new-york/",     "New York City, NY")],
    "jersey_city": [("https://allevents.in/jersey-city/",  "Jersey City, NJ")],
    "newark":      [("https://allevents.in/newark/",       "Newark, NJ")],
    "pittsburgh":  [("https://allevents.in/pittsburgh/",   "Pittsburgh, PA")],
}


def scrape(city_key: str) -> List[dict]:
    """Fetch and merge all pages for city_key."""
    pages = CITY_PAGES.get(city_key, [])
    events = []
    for url, default_city in pages:
        events.extend(_scrape_page(url, default_city))
    return events


def _scrape_page(url: str, default_city: str) -> List[dict]:
    html = fetch(url)
    if not html:
        return []

    events = []
    for block in re.findall(
        r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
        html, re.DOTALL
    ):
        try:
            data = json.loads(block)
            for item in (data if isinstance(data, list) else [data]):
                if item.get("@type") not in ("Event", "MusicEvent"):
                    continue
                if len(events) >= MAX_EVENTS_PER_PAGE:
                    break
                parsed = _parse_event(item, default_city, url)
                if parsed:
                    events.append(parsed)
        except Exception as e:
            print(f"  Allevents parse error [{url}]: {e}", file=sys.stderr)

    print(f"  Allevents {url}: {len(events)} events")
    return events


def _parse_event(item: dict, default_city: str, fallback_url: str) -> Optional[dict]:
    name = (item.get("name") or "").strip()
    if not name:
        return None

    loc = item.get("location") or {}
    loc_name = (loc.get("name") or "").strip()
    addr = loc.get("address") or {}
    venue_city = (addr.get("addressLocality") or "").strip()
    canonical_city = CITY_ALIASES.get(venue_city.lower()) or default_city

    location_str = (
        f"{loc_name}, {venue_city}" if loc_name and venue_city and loc_name != venue_city
        else venue_city or default_city
    )

    img = item.get("image") or ""
    if isinstance(img, list):
        img = img[0] if img else ""

    return {
        "title": name,
        "date": fmt_date(item.get("startDate", "")),
        "date_iso": item.get("startDate", ""),
        "location": location_str,
        "link": item.get("url", fallback_url),
        "img": img,
        "description": item.get("description", ""),
        "source": "Allevents",
        "city": canonical_city,
    }
