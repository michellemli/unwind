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
    "boston":       "Boston, MA",
    "somerville":   "Boston, MA",
    "brookline":    "Boston, MA",
    "newton":       "Boston, MA",
    "quincy":       "Boston, MA",
    "malden":       "Boston, MA",
    "medford":      "Boston, MA",
    "waltham":      "Boston, MA",
    "everett":      "Boston, MA",
    "watertown":    "Boston, MA",
    "brighton":     "Boston, MA",
    "allston":      "Boston, MA",
    "salem":        "Boston, MA",
    "danvers":      "Boston, MA",
    "revere":       "Boston, MA",
    "chelsea":      "Boston, MA",
    "lynn":         "Boston, MA",
    "dedham":       "Boston, MA",
    "needham":      "Boston, MA",
    "milton":       "Boston, MA",
    # Cambridge
    "cambridge":    "Cambridge, MA",
    "belmont":      "Cambridge, MA",
    "arlington":    "Cambridge, MA",
    # New York City
    "new york":          "New York City, NY",
    "new york city":     "New York City, NY",
    "manhattan":         "New York City, NY",
    "brooklyn":          "New York City, NY",
    "queens":            "New York City, NY",
    "bronx":             "New York City, NY",
    "the bronx":         "New York City, NY",
    "staten island":     "New York City, NY",
    "astoria":           "New York City, NY",
    "long island city":  "New York City, NY",
    "flushing":          "New York City, NY",
    "harlem":            "New York City, NY",
    "williamsburg":      "New York City, NY",
    "bushwick":          "New York City, NY",
    "crown heights":     "New York City, NY",
    "park slope":        "New York City, NY",
    "fort greene":       "New York City, NY",
    "jackson heights":   "New York City, NY",
    "sunnyside":         "New York City, NY",
    "forest hills":      "New York City, NY",
    "flatbush":          "New York City, NY",
    "ridgewood":         "New York City, NY",
    "jamaica":           "New York City, NY",
    "bedford-stuyvesant":"New York City, NY",
    "bed-stuy":          "New York City, NY",
    "greenpoint":        "New York City, NY",
    "upper west side":   "New York City, NY",
    "upper east side":   "New York City, NY",
    "lower east side":   "New York City, NY",
    "east village":      "New York City, NY",
    "west village":      "New York City, NY",
    "chelsea":           "New York City, NY",
    "midtown":           "New York City, NY",
    "soho":              "New York City, NY",
    "tribeca":           "New York City, NY",
    # Jersey City, NJ
    "new jersey":    "Jersey City, NJ",  # generic NJ fallback
    "jersey city":   "Jersey City, NJ",
    "secaucus":      "Jersey City, NJ",
    "edgewater":     "Jersey City, NJ",
    "kearny":        "Jersey City, NJ",
    "bayonne":       "Jersey City, NJ",
    "north bergen":  "Jersey City, NJ",
    "harrison":      "Jersey City, NJ",
    # Hoboken, NJ
    "hoboken":       "Hoboken, NJ",
    "weehawken":     "Hoboken, NJ",
    "union city":    "Hoboken, NJ",
    "guttenberg":    "Hoboken, NJ",
    "west new york": "Hoboken, NJ",
    "fort lee":      "Hoboken, NJ",
    # Newark, NJ
    "newark":        "Newark, NJ",
    "east orange":   "Newark, NJ",
    "bloomfield":    "Newark, NJ",
    "belleville":    "Newark, NJ",
    "irvington":     "Newark, NJ",
    "nutley":        "Newark, NJ",
    "montclair":     "Newark, NJ",
    "maplewood":     "Newark, NJ",
    "south orange":  "Newark, NJ",
    "orange":        "Newark, NJ",
    "elizabeth":     "Newark, NJ",
    # Pittsburgh metro
    "pittsburgh":    "Pittsburgh, PA",
    "allegheny":     "Pittsburgh, PA",
    "penn hills":    "Pittsburgh, PA",
    "monroeville":   "Pittsburgh, PA",
    "shadyside":     "Pittsburgh, PA",
    "squirrel hill": "Pittsburgh, PA",
    "lawrenceville": "Pittsburgh, PA",
    "bloomfield":    "Pittsburgh, PA",
    "east liberty":  "Pittsburgh, PA",
    "south side":    "Pittsburgh, PA",
    "north side":    "Pittsburgh, PA",
    "oakland":       "Pittsburgh, PA",
    "mt. lebanon":   "Pittsburgh, PA",
    "mt lebanon":    "Pittsburgh, PA",
    "carnegie":      "Pittsburgh, PA",
    "bethel park":   "Pittsburgh, PA",
}


def resolve_city(venue_city: str, fallback: str) -> str:
    """
    Resolve a raw venue city string to a canonical city label.
    Tries exact match first, then strips a trailing ', ST' state suffix.
    Returns fallback if no match is found.
    """
    key = venue_city.lower().strip()
    if key in CITY_ALIASES:
        return CITY_ALIASES[key]
    # Handle "City, ST" or "City, State" formats from structured address fields
    if "," in key:
        city_part = key.split(",")[0].strip()
        if city_part in CITY_ALIASES:
            return CITY_ALIASES[city_part]
    return fallback
