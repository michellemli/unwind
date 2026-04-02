"""
Feverup (feverup.com) scraper.

The city explore page at feverup.com/en/<slug> embeds an inline JSON blob
containing a 'cityPlansIds' array of integer plan IDs.

Each plan's detail page (feverup.com/m/<id>) embeds another JSON blob with
startsAtIso (date) and a JSON-LD <script type="application/ld+json"> block
of @type Product with name, venue, and city.

Because fetching one URL per event would be slow, detail pages are fetched
in parallel threads within the scraper (up to MAX_EVENTS).

Verified structure (April 2026):
    City page inline script contains:
        "cityPlansIds": [609816, 532123, ...]

    Plan detail page JSON-LD (@type Product):
        { "name": "...", "sku": "609816",
          "offers": [{ "areaServed": { "name": "Regent Theatre",
                        "address": { "addressLocality": "Boston" }},
                       "url": "https://feverup.com/m/609816" }] }

    Plan detail page inline script contains:
        "startsAtIso": "2026-05-02T18:00:00-04:00"
        "coverImage":  "https://..."

To add a new city:
    1. Find the feverup.com/en/<slug> page (test for a cityPlansIds array).
    2. Add a (url, default_city_label) entry to CITY_PAGES below.
    3. Call feverup.scrape("<key>") from scrapers/__init__.py.
"""

import json
import re
import sys
import threading
from typing import List, Optional

from config import CITY_ALIASES
from scrapers.base import fetch, fmt_date

MAX_EVENTS = 8

CITY_PAGES = {
    "boston":      ("https://feverup.com/en/boston",      "Boston, MA"),
    "nyc":         ("https://feverup.com/en/new-york",    "New York City, NY"),
    "jersey_city": ("https://feverup.com/en/jersey-city", "Jersey City, NJ"),
    "pittsburgh":  ("https://feverup.com/en/pittsburgh",  "Pittsburgh, PA"),
}


def scrape(city_key: str) -> List[dict]:
    if city_key not in CITY_PAGES:
        return []

    url, default_city = CITY_PAGES[city_key]
    html = fetch(url)
    if not html:
        return []

    plan_ids = _extract_plan_ids(html)
    if not plan_ids:
        print(f"  Feverup {city_key}: no plan IDs found", file=sys.stderr)
        return []

    plan_ids = plan_ids[:MAX_EVENTS]
    events: List[Optional[dict]] = [None] * len(plan_ids)
    lock = threading.Lock()

    def fetch_plan(i: int, plan_id: int) -> None:
        detail_url = f"https://feverup.com/m/{plan_id}"
        detail_html = fetch(detail_url)
        if detail_html:
            parsed = _parse_plan(detail_html, default_city, detail_url)
            if parsed:
                with lock:
                    events[i] = parsed

    threads = [
        threading.Thread(target=fetch_plan, args=(i, pid))
        for i, pid in enumerate(plan_ids)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=12)

    result = [e for e in events if e is not None]
    print(f"  Feverup {city_key}: {len(result)} events")
    return result


def _extract_plan_ids(html: str) -> List[int]:
    """Pull cityPlansIds array from the inline JSON blob on the city page."""
    m = re.search(r'"cityPlansIds"\s*:\s*(\[\s*[\d,\s]*\])', html)
    if not m:
        return []
    try:
        return json.loads(m.group(1))
    except Exception:
        return []


def _parse_plan(html: str, default_city: str, fallback_url: str) -> Optional[dict]:
    # --- name, venue, city from JSON-LD ---
    name = venue_name = venue_city = img = ""
    link = fallback_url

    for block in re.findall(
        r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
        html, re.DOTALL
    ):
        try:
            data = json.loads(block)
            for item in (data if isinstance(data, list) else [data]):
                if item.get("@type") != "Product":
                    continue
                name = (item.get("name") or "").strip()
                offers = item.get("offers") or []
                if isinstance(offers, dict):
                    offers = [offers]
                for offer in offers:
                    served = offer.get("areaServed") or {}
                    venue_name = (served.get("name") or "").strip()
                    addr = served.get("address") or {}
                    venue_city = (addr.get("addressLocality") or "").strip()
                    link = offer.get("url") or fallback_url
                break
        except Exception:
            continue

    if not name:
        return None

    # --- date and image from inline script ---
    date_iso = ""
    m_date = re.search(r'"startsAtIso"\s*:\s*"([^"]+)"', html)
    if m_date:
        date_iso = m_date.group(1)

    m_img = re.search(r'"coverImage"\s*:\s*"(https://[^"]+)"', html)
    if m_img:
        img = m_img.group(1)

    canonical_city = CITY_ALIASES.get(venue_city.lower()) or default_city
    if venue_name and venue_city and venue_name != venue_city:
        location_str = f"{venue_name}, {venue_city}"
    else:
        location_str = venue_city or default_city

    return {
        "title": name,
        "date": fmt_date(date_iso),
        "date_iso": date_iso,
        "location": location_str,
        "link": link,
        "img": img,
        "description": "",
        "source": "Fever",
        "city": canonical_city,
    }
