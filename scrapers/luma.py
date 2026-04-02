"""
Luma (lu.ma) scraper.

Luma city pages are Next.js server-side rendered. Event data is embedded in
an inline <script> tag as JSON matching the Next.js page props shape.

Verified path (April 2026):
    props.pageProps.initialData.data.events[]
      .event.name          — event title
      .event.start_at      — ISO 8601 datetime (UTC)
      .event.url           — short slug, prepend "https://lu.ma/"
      .event.cover_url     — banner image URL (may be null)
      .event.geo_address_info
          .full_address    — "Venue, Street, City, State ZIP, Country"
          .city            — city name string
      .calendar.name       — organizer / group name

To add a new city:
    1. Find the lu.ma/<slug> city page (not all cities have one).
    2. Verify the data path is still initialData.data.events[].
    3. Add a (url, default_city_label) tuple to CITY_PAGES below.
    4. Call scrape("<slug>") from scrapers/__init__.py.
"""

import json
import sys
from typing import List, Optional

from config import CITY_ALIASES
from scrapers.base import fetch, fmt_date

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

# (page_url, default_city_label) — default is used when geo_address_info is absent
CITY_PAGES = {
    "boston": ("https://lu.ma/boston", "Boston, MA"),
    "nyc":    ("https://lu.ma/nyc",    "New York City, NY"),
}


def scrape(city_slug: str) -> List[dict]:
    """
    Scrape the Luma city page for city_slug (e.g. 'boston', 'nyc').
    Returns [] if the city is not in CITY_PAGES or the fetch fails.
    """
    if city_slug not in CITY_PAGES:
        return []
    if not HAS_BS4:
        print("  Luma: beautifulsoup4 not installed, skipping", file=sys.stderr)
        return []

    url, default_city = CITY_PAGES[city_slug]
    html = fetch(url)
    if not html:
        return []

    events = []
    for script in BeautifulSoup(html, "html.parser").find_all("script"):
        t = script.string or ""
        if '"events"' not in t or "pageProps" not in t or len(t) < 500:
            continue
        try:
            data = json.loads(t)
            evt_list = data["props"]["pageProps"]["initialData"]["data"]["events"]
            for wrapper in evt_list:
                parsed = _parse_event(wrapper, default_city, url)
                if parsed:
                    events.append(parsed)
        except Exception as e:
            print(f"  Luma parse error [{url}]: {e}", file=sys.stderr)
        break  # only the first matching script contains page data

    print(f"  Luma {city_slug}: {len(events)} events")
    return events


def _parse_event(wrapper: dict, default_city: str, fallback_url: str) -> Optional[dict]:
    ev = wrapper.get("event", {})
    cal = wrapper.get("calendar", {})
    name = ev.get("name", "").strip()
    if not name:
        return None

    geo = ev.get("geo_address_info") or {}
    venue_city = geo.get("city", "").strip()
    canonical_city = CITY_ALIASES.get(venue_city.lower()) or default_city

    full_addr = geo.get("full_address", "").strip()
    if full_addr:
        parts = [p.strip() for p in full_addr.split(",")]
        location_str = ", ".join(parts[:3]) if len(parts) >= 3 else full_addr
    else:
        location_str = venue_city or canonical_city

    slug = ev.get("url", "")
    organizer = cal.get("name", "")

    return {
        "title": name,
        "date": fmt_date(ev.get("start_at", "")),
        "date_iso": ev.get("start_at", ""),
        "location": location_str,
        "link": f"https://lu.ma/{slug}" if slug else fallback_url,
        "img": ev.get("cover_url") or "",
        "description": organizer,
        "source": f"Luma{' · ' + organizer[:25] if organizer else ''}",
        "city": canonical_city,
    }
