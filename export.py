"""
Export events to a CSV file in the exports/ subdirectory.

export_csv(events) writes columns:
    Title, Date, City, Location, Category, Source, Link

Returns the path of the written file (relative to the project root).
"""

import csv
import os
from datetime import datetime

EXPORT_DIR = os.path.join(os.path.dirname(__file__), "exports")

COLUMNS = ["Title", "Date", "City", "Location", "Category", "Source", "Link"]


def _detect_category(event: dict) -> str:
    """Keyword categorisation matching the frontend detectCategory logic."""
    import re
    text = (event.get("title", "") + " " + event.get("description", "") + " " + event.get("location", "")).lower()
    if re.search(r"yoga|meditat|mindful|sound bath|breathwork|spa|wellness|reiki|pilates|stretch|relax|self.care|journaling", text):
        return "Wellness"
    if re.search(r"paint|pottery|craft|ceramics|knit|sew|sketch|drawing|watercolor|collage|candle|floral", text):
        return "Arts & Crafts"
    if re.search(r"hike|trail|outdoor|walk|run|bike|cycle|kayak|climb|fitness|bootcamp|swim", text):
        return "Outdoor & Fitness"
    if re.search(r"concert|music|jazz|band|dj|festival|show|performance|comedy|stand.up|improv|pops|symphony", text):
        return "Music & Entertainment"
    if re.search(r"cooking class|food tour|food festival|culinary|baking class|chef|mixology|cocktail class|wine dinner|cheese tasting|restaurant week|farmers market", text):
        return "Food & Drink"
    if re.search(r"wine tasting|wine|beer tasting|craft beer|cocktail|brunch|dinner|tasting|dining|coffee|market|restaurant", text):
        return "Food & Drink"
    if re.search(r"museum|gallery|exhibit|film|cinema|theater|theatre|book club|book|lecture|talk|tour|culture", text):
        return "Culture & Learning"
    if re.search(r"social|mixer|happy hour|get.together|meetup|networking|community", text):
        return "Social"
    return "Other"


def export_csv(events: list) -> str:
    """
    Write events to a timestamped CSV in exports/.
    Returns the file path relative to the project root.
    """
    os.makedirs(EXPORT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"events_{timestamp}.csv"
    filepath = os.path.join(EXPORT_DIR, filename)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for e in events:
            writer.writerow({
                "Title":    e.get("title", ""),
                "Date":     e.get("date", ""),
                "City":     e.get("city", ""),
                "Location": e.get("location", ""),
                "Category": _detect_category(e),
                "Source":   e.get("source", ""),
                "Link":     e.get("link", ""),
            })

    return os.path.join("exports", filename)
