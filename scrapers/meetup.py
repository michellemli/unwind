"""
Meetup scraper.

Meetup embeds a Next.js Apollo GraphQL cache in the page's __NEXT_DATA__
<script> tag. Events are stored as flat objects keyed by "Event:<id>" inside
__APOLLO_STATE__. Venue details are stored separately as "Venue:<id>" and
referenced via __ref pointers.

Verified structure (April 2026):
    __NEXT_DATA__.props.pageProps.__APOLLO_STATE__ = {
      "Event:310409615": {
        "title": "...",
        "dateTime": "2026-04-30T18:00:00-04:00",
        "eventType": "PHYSICAL" | "ONLINE",
        "eventUrl": "https://www.meetup.com/.../events/310409615/",
        "venue": { "__ref": "Venue:12345" },
        "group": { "__ref": "Group:67890" }
      },
      "Venue:12345": { "name": "...", "city": "Boston", "state": "MA" },
      "Group:67890": { "name": "Boston Tech Meetup" }
    }

Known limitation: Meetup's location filter only returns reliable results
for Boston-area cities. Queries for NYC, NJ, or Pittsburgh return the same
popular Boston-area events. Only Boston, Cambridge, and Pittsburgh are enabled.
"""

import json
import re
import sys
from typing import List, Optional

from config import CITIES, resolve_city
from scrapers.base import fetch, fmt_date

MAX_EVENTS_PER_CITY = 10

# Cities where Meetup's location filter works reliably.
# Remove a key here to disable Meetup for that city.
ENABLED_CITIES = {"boston", "cambridge", "pittsburgh"}


def scrape(city_key: str) -> List[dict]:
    """Return up to MAX_EVENTS_PER_CITY events. Returns [] for disabled cities."""
    if city_key not in ENABLED_CITIES:
        return []

    city = CITIES[city_key]
    encoded_loc = city["label"].replace(" ", "%20") + "%2C%20" + city["state"]
    url = f"https://www.meetup.com/find/?location={encoded_loc}&source=EVENTS"
    html = fetch(url)
    if not html:
        return []

    m = re.search(r'id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not m:
        print(f"  Meetup {city_key}: no __NEXT_DATA__", file=sys.stderr)
        return []

    try:
        apollo = (
            json.loads(m.group(1))
            .get("props", {})
            .get("pageProps", {})
            .get("__APOLLO_STATE__", {})
        )
    except Exception as e:
        print(f"  Meetup {city_key}: parse error: {e}", file=sys.stderr)
        return []

    if not apollo:
        print(f"  Meetup {city_key}: __APOLLO_STATE__ is empty", file=sys.stderr)
        return []

    events = []
    for key, evt in apollo.items():
        if not key.startswith("Event:"):
            continue
        if len(events) >= MAX_EVENTS_PER_CITY:
            break
        parsed = _parse_event(evt, apollo, city)
        if parsed:
            events.append(parsed)

    print(f"  Meetup {city_key}: {len(events)} events")
    return events


def _parse_event(evt: dict, apollo: dict, city: dict) -> Optional[dict]:
    title = evt.get("title", "").strip()
    if not title:
        return None

    event_type = evt.get("eventType", "")

    venue = evt.get("venue", {})
    if isinstance(venue, dict) and "__ref" in venue:
        venue = apollo.get(venue["__ref"], {})

    if not isinstance(venue, dict):
        return None

    v_name = venue.get("name", "").strip()
    v_city = venue.get("city", "").strip()
    v_state = venue.get("state", "").strip()

    if event_type == "ONLINE":
        location_str = "Online"
        canonical_city = city["label"]
    else:
        canonical_city = resolve_city(v_city, "")
        if not canonical_city:
            return None  # venue not in a tracked city
        if v_name and v_name.lower() != "online event" and v_city:
            location_str = f"{v_name}, {v_city}"
        else:
            location_str = f"{v_city}, {v_state}" if v_state else v_city or canonical_city

    group = evt.get("group", {})
    if isinstance(group, dict) and "__ref" in group:
        group = apollo.get(group["__ref"], {})
    group_name = (group.get("name", "") if isinstance(group, dict) else "") or "Meetup"

    return {
        "title": title,
        "date": fmt_date(evt.get("dateTime", "")),
        "date_iso": evt.get("dateTime", ""),
        "location": location_str,
        "link": evt.get("eventUrl", ""),
        "img": "",
        "description": "",
        "source": f"Meetup · {group_name[:30]}",
        "city": canonical_city,
    }
