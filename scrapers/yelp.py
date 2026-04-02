"""
Yelp Events scraper.

Yelp's event browse page (yelp.com/events/<city>/browse) is server-side
rendered HTML with event card links. Each card links to a detail page
(yelp.com/events/<slug>) that embeds HTML microdata (itemprop attributes)
with title, date, and address.

Because the listing page has no dates and the detail pages have all the
data, detail pages are fetched in parallel (up to MAX_EVENTS per page).

Verified structure (April 2026):
    Browse page card:
        <a href="/events/<slug>"> (inside card elements — excludes /create, /login, etc.)

    Detail page microdata:
        <meta itemprop="name"          content="Event Title">
        <meta itemprop="startDate"     content="2026-04-04T10:00:00-04:00">
        <span itemprop="streetAddress">250 Devonshire St</span>
        <span itemprop="addressLocality">Boston</span>
        <meta itemprop="description"   content="...">

Working city browse URLs (April 2026):
    boston, manhattan, brooklyn, pittsburgh
    (cambridge, new-york, jersey-city, newark all 404)

NJ has no working Yelp Events city page and is skipped.

To add a new city:
    1. Verify yelp.com/events/<slug>/browse returns 200.
    2. Add (url, default_city_label) tuples to CITY_PAGES below.
    3. Call yelp.scrape("<key>") from scrapers/__init__.py.
"""

import re
import sys
import threading
from typing import List, Optional

from config import resolve_city
from scrapers.base import fetch, fmt_date

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

MAX_EVENTS = 8

# Maps city_key → list of (browse_url, default_city_label) tuples.
# NYC spans Manhattan + Brooklyn; both are fetched and merged.
CITY_PAGES = {
    "boston":     [("https://www.yelp.com/events/boston/browse",     "Boston, MA")],
    "nyc":        [
        ("https://www.yelp.com/events/manhattan/browse", "New York City, NY"),
        ("https://www.yelp.com/events/brooklyn/browse",  "New York City, NY"),
    ],
    "pittsburgh": [("https://www.yelp.com/events/pittsburgh/browse", "Pittsburgh, PA")],
}

# Slugs that appear in event card hrefs but are not event pages
_SLUG_BLOCKLIST = {"create", "login", "signup", "search", "biz"}


def scrape(city_key: str) -> List[dict]:
    if not HAS_BS4:
        print("  Yelp: beautifulsoup4 not installed, skipping", file=sys.stderr)
        return []

    pages = CITY_PAGES.get(city_key, [])
    events = []
    for url, default_city in pages:
        events.extend(_scrape_page(url, default_city, city_key))
    return events


def _scrape_page(browse_url: str, default_city: str, label: str) -> List[dict]:
    html = fetch(browse_url)
    if not html:
        return []

    slugs = _extract_slugs(html)
    if not slugs:
        print(f"  Yelp {label}: no event slugs found", file=sys.stderr)
        return []

    slugs = slugs[:MAX_EVENTS]
    events: List[Optional[dict]] = [None] * len(slugs)
    lock = threading.Lock()

    def fetch_event(i: int, slug: str) -> None:
        detail_url = f"https://www.yelp.com/events/{slug}"
        detail_html = fetch(detail_url)
        if detail_html:
            parsed = _parse_event(detail_html, default_city, detail_url)
            if parsed:
                with lock:
                    events[i] = parsed

    threads = [
        threading.Thread(target=fetch_event, args=(i, slug))
        for i, slug in enumerate(slugs)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=12)

    result = [e for e in events if e is not None]
    print(f"  Yelp {label} ({browse_url.split('/')[-2]}): {len(result)} events")
    return result


def _extract_slugs(html: str) -> List[str]:
    """Pull /events/<slug> hrefs from the browse page, excluding non-event paths."""
    seen: set = set()
    slugs = []
    for href in re.findall(r'href="/events/([^"?#/]+)"', html):
        if href in _SLUG_BLOCKLIST:
            continue
        # City-level pages are bare city names (no hyphens with digits)
        if re.fullmatch(r'[a-z\-]+', href) and '-' not in href:
            continue
        if href not in seen:
            seen.add(href)
            slugs.append(href)
    return slugs


def _parse_event(html: str, default_city: str, fallback_url: str) -> Optional[dict]:
    soup = BeautifulSoup(html, "html.parser")

    def itemprop(name: str) -> str:
        tag = soup.find(attrs={"itemprop": name})
        if not tag:
            return ""
        return (tag.get("content") or tag.get_text()).strip()

    # The site <meta itemprop="name"> comes before the event <h1 itemprop="name">
    # so we look specifically for the h1 first.
    name_tag = soup.find("h1", attrs={"itemprop": "name"})
    name = name_tag.get_text().strip() if name_tag else itemprop("name")
    if not name:
        return None

    date_iso   = itemprop("startDate")
    street     = itemprop("streetAddress")
    venue_city = itemprop("addressLocality")
    description = itemprop("description")

    img_tag = soup.find("meta", property="og:image")
    img = img_tag["content"] if img_tag and img_tag.get("content") else ""

    canonical_city = resolve_city(venue_city, default_city)
    location_str = (
        f"{street}, {venue_city}" if street and venue_city
        else venue_city or default_city
    )

    return {
        "title": name,
        "date": fmt_date(date_iso),
        "date_iso": date_iso,
        "location": location_str,
        "link": fallback_url,
        "img": img,
        "description": description,
        "source": "Yelp Events",
        "city": canonical_city,
    }
