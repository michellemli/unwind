"""
Resident Advisor (ra.co) scraper.

RA's HTML pages are protected by DataDome bot detection and cannot be
scraped directly. However, their public GraphQL API at ra.co/graphql
is unprotected and returns structured event data.

Verified query (April 2026): eventListings with an area filter.

Example response shape:
    data.eventListings.data[] = {
      "listingDate": "2026-04-02T00:00:00.000Z",
      "event": {
        "title": "KEEP ON - Trip Report / Joe Tagessian",
        "date":  "2026-04-02T00:00:00.000Z",
        "startTime": "2026-04-02T22:00:00.000Z",
        "contentUrl": "/events/2408314",
        "flyerFront": "https://...",
        "venue":   { "name": "Middlesex" },
        "area":    { "name": "Boston" },
        "artists": [{ "name": "Trip Report" }]
      }
    }

RA skews toward electronic music / nightlife — useful for concerts,
DJ nights, and cultural events in this demographic.

Area IDs (from ra.co/graphql area() query, April 2026):
    Boston: 530   New York City: 8   Pittsburgh: 531   New Jersey: 48

To add a new city:
    1. Query: { area(areaUrlName: "<slug>", countryUrlCode: "us") { id name } }
    2. Add the area ID to AREA_IDS below.
    3. Call ra.scrape("<key>") from scrapers/__init__.py.
"""

import json
import sys
from datetime import datetime, timezone
from typing import List, Optional

from config import CITIES, resolve_city
from scrapers.base import fetch, fmt_date, build_location

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

GRAPHQL_URL = "https://ra.co/graphql"
MAX_EVENTS   = 10

AREA_IDS = {
    "boston":      "530",
    "cambridge":   "530",  # Cambridge shares Boston's RA area
    "nyc":         "8",
    "pittsburgh":  "531",
    "jersey_city": "48",   # NJ area — CITY_ALIASES routes to Jersey City/Hoboken/Newark by venue
    # hoboken and newark intentionally omitted: same RA area as jersey_city (deduplication)
}

_QUERY = """
{
  eventListings(
    filters: {
      areas: { eq: %s },
      listingDate: { gte: "%s" }
    },
    page: 1,
    pageSize: %d,
    sort: { listingDate: { priority: 1, order: ASCENDING } }
  ) {
    data {
      listingDate
      event {
        title
        startTime
        contentUrl
        flyerFront
        venue  { name }
        area   { name }
        artists { name }
      }
    }
  }
}
"""


def scrape(city_key: str) -> List[dict]:
    area_id = AREA_IDS.get(city_key)
    if not area_id:
        return []
    if not HAS_REQUESTS:
        print("  RA: requests not installed, skipping", file=sys.stderr)
        return []

    today = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00")
    query = _QUERY % (area_id, today, MAX_EVENTS)

    try:
        resp = requests.post(
            GRAPHQL_URL,
            json={"query": query},
            headers={
                "Content-Type": "application/json",
                "Origin": "https://ra.co",
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            },
            timeout=12,
        )
        resp.raise_for_status()
        listings = resp.json()["data"]["eventListings"]["data"]
    except Exception as e:
        print(f"  RA {city_key}: fetch error: {e}", file=sys.stderr)
        return []

    events = []
    for listing in listings:
        parsed = _parse_listing(listing, city_key)
        if parsed:
            events.append(parsed)

    print(f"  RA {city_key}: {len(events)} events")
    return events


def _parse_listing(listing: dict, city_key: str) -> Optional[dict]:
    ev = listing.get("event") or {}
    title = (ev.get("title") or "").strip()
    if not title:
        return None

    area_name  = (ev.get("area") or {}).get("name", "")
    venue_name = (ev.get("venue") or {}).get("name", "")
    default_city = CITIES.get(city_key, {}).get("label", area_name)
    canonical_city = resolve_city(area_name, default_city)

    location_str = build_location(venue_name, area_name, area_name or venue_name)

    content_url = ev.get("contentUrl") or ""
    link = f"https://ra.co{content_url}" if content_url else "https://ra.co"

    start_time = ev.get("startTime") or listing.get("listingDate") or ""

    artists = ev.get("artists") or []
    artist_names = ", ".join(a["name"] for a in artists[:3] if a.get("name"))
    description = artist_names

    return {
        "title": title,
        "date": fmt_date(start_time),
        "date_iso": start_time,
        "location": location_str,
        "link": link,
        "img": ev.get("flyerFront") or "",
        "description": description,
        "source": "Resident Advisor",
        "city": canonical_city,
    }
