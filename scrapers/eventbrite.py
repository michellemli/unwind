"""
Eventbrite scraper.

Parses the JSON-LD <script type="application/ld+json"> block embedded in
Eventbrite city search pages. The top-level object is an ItemList; each
ListItem contains an item of @type Event with name, startDate, location,
url, and image fields.

Verified structure (April 2026):
    {
      "@type": "ItemList",
      "itemListElement": [
        {
          "item": {
            "@type": "Event",
            "name": "...",
            "startDate": "2026-04-10",
            "url": "https://www.eventbrite.com/e/...",
            "image": "https://img.evbuc.com/...",
            "location": {
              "name": "Venue Name",
              "address": {
                "addressLocality": "Boston",
                "addressRegion": "MA"
              }
            }
          }
        }
      ]
    }

Two scrape modes:
  scrape(city_key)          — general city event feed
  scrape_keywords(city_key) — keyword-specific searches (paint night, book
                              club, wine tasting, etc.) that surface niche
                              social events advertised on those terms
"""

import json
import re
import sys
from typing import List, Optional
from urllib.parse import urlencode

from config import CITIES, resolve_city
from scrapers.base import fetch, fmt_date, build_location

MAX_EVENTS_PER_CITY    = 10
MAX_EVENTS_PER_KEYWORD = 5

# Keywords that surface niche/social events not well-represented in general feeds
KEYWORDS = [
    # Arts & social
    "paint night",
    "book club",
    "comedy night",
    "run club",
    "yoga",
    "pottery",
    "trivia night",
    "craft workshop",
    "dance class",
    # Food & drink
    "wine tasting",
    "cooking class",
    "food tour",
    "food festival",
    "cocktail class",
    "mixology",
    "craft beer",
    "wine dinner",
    "cheese tasting",
    "baking class",
    "culinary",
    "brunch",
    "farmers market",
    "restaurant week",
]


def scrape(city_key: str) -> List[dict]:
    """Return up to MAX_EVENTS_PER_CITY events from the general city feed."""
    city = CITIES[city_key]
    url = f"https://www.eventbrite.com/d/{city['eb_slug']}/events/"
    return _scrape_url(url, city, MAX_EVENTS_PER_CITY, city_key)


def scrape_keywords(city_key: str) -> List[dict]:
    """
    Fetch keyword-specific Eventbrite searches and return up to
    MAX_EVENTS_PER_KEYWORD results per keyword, deduplicated by URL.
    """
    city = CITIES[city_key]
    seen_urls: set = set()
    all_events: List[dict] = []

    for kw in KEYWORDS:
        url = (
            f"https://www.eventbrite.com/d/{city['eb_slug']}/events/"
            f"?{urlencode({'q': kw})}"
        )
        events = _scrape_url(url, city, MAX_EVENTS_PER_KEYWORD, f"{city_key}/{kw}")
        for e in events:
            if e["link"] not in seen_urls:
                seen_urls.add(e["link"])
                all_events.append(e)

    print(f"  Eventbrite keywords {city_key}: {len(all_events)} events")
    return all_events


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _scrape_url(url: str, city: dict, limit: int, label: str) -> List[dict]:
    html = fetch(url)
    if not html:
        return []

    events: List[dict] = []
    for block in re.findall(
        r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
        html, re.DOTALL
    ):
        try:
            data = json.loads(block)
            for obj in (data if isinstance(data, list) else [data]):
                if obj.get("@type") != "ItemList":
                    continue
                for list_item in obj.get("itemListElement", []):
                    if len(events) >= limit:
                        break
                    event = list_item.get("item", {})
                    if event.get("@type") != "Event":
                        continue
                    parsed = _parse_event(event, city, url)
                    if parsed:
                        events.append(parsed)
        except Exception as e:
            print(f"  Eventbrite parse error [{label}]: {e}", file=sys.stderr)

    return events


def _parse_event(item: dict, city: dict, fallback_url: str) -> Optional[dict]:
    name = item.get("name", "").strip()
    if not name:
        return None

    loc = item.get("location") or {}
    addr = loc.get("address") or {}
    loc_name = (loc.get("name") or addr.get("streetAddress") or "").strip()
    venue_city = addr.get("addressLocality", "").strip()
    canonical_city = resolve_city(venue_city, city["label"])

    location_str = build_location(loc_name, venue_city, city["label"])

    img = item.get("image", "") or ""
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
        "source": "Eventbrite",
        "city": canonical_city,
    }
