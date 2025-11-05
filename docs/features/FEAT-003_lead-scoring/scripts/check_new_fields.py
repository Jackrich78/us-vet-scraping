#!/usr/bin/env python3
"""Quick script to check if new fields were populated."""

import os
import sys
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

notion = Client(auth=os.getenv("NOTION_API_KEY"))
page_id = sys.argv[1]

page = notion.pages.retrieve(page_id=page_id)
props = page["properties"]

print("\n" + "=" * 80)
print("NEW QUICK WIN FIELDS")
print("=" * 80)

# Check Google Maps URL
gmaps = props.get("Google Maps URL", {})
gmaps_url = gmaps.get("url") if gmaps else None
print(f"  {'✅' if gmaps_url else '❌'} Google Maps URL         = {gmaps_url or '(empty)'}")

# Check Operating Hours
hours = props.get("Operating Hours", {})
hours_text = hours.get("rich_text", [])
if hours_text and len(hours_text) > 0:
    hours_content = hours_text[0].get("plain_text", "")
    print(f"  ✅ Operating Hours         = {hours_content[:50]}..." if len(hours_content) > 50 else f"  ✅ Operating Hours         = {hours_content}")
else:
    print(f"  ❌ Operating Hours         = (empty)")

# Check First Scraped Date
first_date = props.get("First Scraped Date", {})
first_date_value = first_date.get("date", {}).get("start") if first_date else None
print(f"  {'✅' if first_date_value else '❌'} First Scraped Date     = {first_date_value or '(empty)'}")

# Check Last Scraped Date
last_date = props.get("Last Scraped Date", {})
last_date_value = last_date.get("date", {}).get("start") if last_date else None
print(f"  {'✅' if last_date_value else '❌'} Last Scraped Date      = {last_date_value or '(empty)'}")

# Check Enrichment Error
enrich_error = props.get("Enrichment Error", {})
error_text = enrich_error.get("rich_text", [])
if error_text and len(error_text) > 0:
    error_content = error_text[0].get("plain_text", "")
    print(f"  ✅ Enrichment Error        = {error_content}")
else:
    print(f"  ✅ Enrichment Error        = (empty - no errors)")

print("=" * 80)

# Count populated
populated = sum([
    1 if gmaps_url else 0,
    1 if hours_text and len(hours_text) > 0 else 0,
    1 if first_date_value else 0,
    1 if last_date_value else 0,
    1  # Enrichment Error always counts as populated (empty = no errors)
])

print(f"\nSummary: {populated}/5 quick win fields populated")
print("=" * 80 + "\n")
