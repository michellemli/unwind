"""
Scraper orchestrator.

scrape_all() runs all enabled scrapers in parallel threads, deduplicates
results by title, sorts them (in-person first, then by city), and returns
the merged list.

Adding a new scraper:
    1. Create scrapers/<name>.py with a scrape(city_key) function.
    2. Import it here and add calls to the `tasks` list in scrape_all().
"""

import threading
from datetime import datetime

from cache import Cache
from typing import List, Optional
from config import CITIES, CACHE_TTL
from scrapers import eventbrite, meetup, luma, allevents, feverup, yelp, ra

_cache = Cache(ttl=CACHE_TTL)

# City display order in the sorted output
_CITY_ORDER = {label: i for i, label in enumerate([
    "Boston, MA", "Cambridge, MA", "New York City, NY",
    "Jersey City, NJ", "Hoboken, NJ", "Newark, NJ", "Pittsburgh, PA",
])}


def scrape_all() -> List[dict]:
    """
    Return the full merged event list, served from cache when still fresh.
    Thread-safe; safe to call from concurrent HTTP handlers.
    """
    cached = _cache.get()
    if cached is not None:
        print("  [cache hit]")
        return cached

    print("Scraping live events…")
    results = []  # type: List[dict]
    lock = threading.Lock()

    def run(fn, *args):
        evts = fn(*args)
        with lock:
            results.extend(evts)

    tasks = [
        # Eventbrite — general city feed
        *[(eventbrite.scrape, k) for k in CITIES],
        # Eventbrite — keyword searches (paint night, book club, wine tasting, etc.)
        *[(eventbrite.scrape_keywords, k) for k in CITIES],
        # Meetup — Boston-area only (see scrapers/meetup.py for why)
        *[(meetup.scrape, k) for k in CITIES],
        # Allevents.in — all cities
        *[(allevents.scrape, k) for k in CITIES],
        # Luma — Boston and NYC city pages only
        (luma.scrape, "boston"),
        (luma.scrape, "nyc"),
        # Feverup — experiences, paint nights, wine tastings, shows
        *[(feverup.scrape, k) for k in feverup.CITY_PAGES],
        # Yelp Events — local community events, social, cultural
        *[(yelp.scrape, k) for k in yelp.CITY_PAGES],
        # Resident Advisor — concerts, DJ nights, cultural events
        *[(ra.scrape, k) for k in CITIES],
    ]

    threads = [threading.Thread(target=run, args=(fn, *args)) for fn, *args in tasks]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=25)

    unique = _deduplicate(results)
    unique.sort(key=_sort_key)
    print(f"  Total unique events: {len(unique)}")

    _cache.set(unique)
    return unique


def invalidate_cache() -> None:
    _cache.invalidate()


def cache_info() -> dict:
    return {"age_seconds": round(_cache.age_seconds()), "is_fresh": _cache.is_fresh}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _deduplicate(events: List[dict]) -> List[dict]:
    seen: set[str] = set()
    unique = []
    for e in events:
        key = e["title"].lower().replace(" ", "")[:40]
        if key not in seen:
            seen.add(key)
            unique.append(e)
    return unique


def _sort_key(e: dict) -> tuple:
    online = 1 if e.get("location", "").lower() == "online" else 0
    # Normalise to a plain date prefix for lexicographic sort; missing dates sort last
    iso = (e.get("date_iso") or "")[:19].replace("Z", "")
    return (online, iso or "9999")
