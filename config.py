"""
Shared configuration: cities, venue aliases, and HTTP constants.

To add a new city:
  1. Add an entry to CITIES with a unique key, label, state, and Eventbrite slug.
  2. Add the city's neighbourhoods/suburbs to CITY_ALIASES.
  3. Add a Luma city page to scrapers/luma.py  (CITY_PAGES) if one exists.
  4. Add Allevents.in URL(s) to scrapers/allevents.py (CITY_PAGES).
  5. Add a city pill to public/index.html and a badge colour to public/css/style.css.
"""

import os
PORT = int(os.environ.get("PORT", 3456))
CACHE_TTL = 300  # seconds — how long scraped results are reused before a live refresh

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# Canonical city registry.
# key        — internal identifier used by scrapers
# label      — display name shown in the UI (city + state)
# state      — two-letter state abbreviation
# eb_slug    — Eventbrite city slug (eventbrite.com/d/<eb_slug>/events/)
CITIES = {
    "boston":       {"label": "Boston, MA",        "state": "MA", "eb_slug": "ma--boston"},
    "cambridge":    {"label": "Cambridge, MA",      "state": "MA", "eb_slug": "ma--cambridge"},
    "nyc":          {"label": "New York City, NY",  "state": "NY", "eb_slug": "ny--new-york-city"},
    "jersey_city":  {"label": "Jersey City, NJ",   "state": "NJ", "eb_slug": "nj--jersey-city"},
    "hoboken":      {"label": "Hoboken, NJ",        "state": "NJ", "eb_slug": "nj--hoboken"},
    "newark":       {"label": "Newark, NJ",         "state": "NJ", "eb_slug": "nj--newark"},
    "pittsburgh":   {"label": "Pittsburgh, PA",     "state": "PA", "eb_slug": "pa--pittsburgh"},
}

# Maps a venue city string (lowercased) → canonical city label.
# Used to correctly label events when a scraper returns a nearby suburb.
# Add entries here when a new city or suburb produces misclassified events.
CITY_ALIASES = {
    # Boston metro
    "boston":     "Boston, MA",
    "somerville": "Boston, MA",
    "brookline":  "Boston, MA",
    "newton":     "Boston, MA",
    "quincy":     "Boston, MA",
    "malden":     "Boston, MA",
    "medford":    "Boston, MA",
    "waltham":    "Boston, MA",
    "everett":    "Boston, MA",
    "watertown":  "Boston, MA",
    "brighton":   "Boston, MA",
    "allston":    "Boston, MA",
    "salem":      "Boston, MA",
    "danvers":    "Boston, MA",
    # Cambridge
    "cambridge":  "Cambridge, MA",
    # Pittsburgh metro
    "pittsburgh": "Pittsburgh, PA",
    "allegheny":  "Pittsburgh, PA",
    "penn hills": "Pittsburgh, PA",
    "monroeville":"Pittsburgh, PA",
    # New York City
    "new york":        "New York City, NY",
    "new york city":   "New York City, NY",
    "manhattan":       "New York City, NY",
    "brooklyn":        "New York City, NY",
    "queens":          "New York City, NY",
    "bronx":           "New York City, NY",
    "staten island":   "New York City, NY",
    "astoria":         "New York City, NY",
    "long island city":"New York City, NY",
    "new york city, ny":"New York City, NY",
    # Jersey City, NJ
    "new jersey":  "Jersey City, NJ",  # generic NJ fallback
    "jersey city": "Jersey City, NJ",
    "secaucus":    "Jersey City, NJ",
    "edgewater":   "Jersey City, NJ",
    "kearny":      "Jersey City, NJ",
    # Hoboken, NJ
    "hoboken":    "Hoboken, NJ",
    "weehawken":  "Hoboken, NJ",
    "union city": "Hoboken, NJ",
    # Newark, NJ
    "newark":         "Newark, NJ",
    "east orange":    "Newark, NJ",
    "bloomfield":     "Newark, NJ",
    "belleville":     "Newark, NJ",
    "irvington":      "Newark, NJ",
}
