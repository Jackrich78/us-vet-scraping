#!/usr/bin/env python3
"""
Validate all Notion fields for a practice.

Shows which fields are populated and validates their values.
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from notion_client import Client

# Load environment
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def validate_practice_fields(practice_id: str):
    """Validate all fields for a practice."""

    notion_api_key = os.getenv("NOTION_API_KEY")
    notion_database_id = os.getenv("NOTION_DATABASE_ID")

    if not notion_api_key or not notion_database_id:
        print("❌ Missing NOTION_API_KEY or NOTION_DATABASE_ID in .env")
        return

    client = Client(auth=notion_api_key)

    # Fetch the practice
    try:
        page = client.pages.retrieve(page_id=practice_id)
    except Exception as e:
        print(f"❌ Failed to fetch practice: {e}")
        return

    properties = page.get("properties", {})

    # Extract name
    name_prop = properties.get("Name", {})
    name = ""
    if name_prop.get("title"):
        name = name_prop["title"][0]["plain_text"]

    print("=" * 80)
    print(f"NOTION FIELD VALIDATION: {name}")
    print(f"Practice ID: {practice_id}")
    print("=" * 80)
    print()

    # Define expected fields by feature
    fields_by_feature = {
        "FEAT-001 (Google Maps → Notion)": [
            ("Name", "title", lambda p: p.get("title", [{}])[0].get("plain_text") if p.get("title") else None),
            ("Google Place ID", "rich_text", lambda p: p.get("rich_text", [{}])[0].get("plain_text") if p.get("rich_text") else None),
            ("Website", "url", lambda p: p.get("url")),
            ("Google Rating", "number", lambda p: p.get("number")),
            ("Google Review Count", "number", lambda p: p.get("number")),
        ],
        "FEAT-002 (Website Enrichment)": [
            ("Vet Count", "number", lambda p: p.get("number")),
            ("Vet Count Confidence", "select", lambda p: p.get("select", {}).get("name") if p.get("select") else None),
            ("Decision Maker Name", "rich_text", lambda p: p.get("rich_text", [{}])[0].get("plain_text") if p.get("rich_text") else None),
            ("Decision Maker Email", "email", lambda p: p.get("email")),
            ("24/7 Emergency Services", "checkbox", lambda p: p.get("checkbox")),
            ("Online Booking", "checkbox", lambda p: p.get("checkbox")),
            ("Patient Portal", "checkbox", lambda p: p.get("checkbox")),
            ("Telemedicine", "checkbox", lambda p: p.get("checkbox")),
            ("Specialty Services", "multi_select", lambda p: [s.get("name") for s in p.get("multi_select", [])] if p.get("multi_select") else []),
            ("Enrichment Status", "select", lambda p: p.get("select", {}).get("name") if p.get("select") else None),
        ],
        "FEAT-003 (Lead Scoring)": [
            ("Lead Score", "number", lambda p: p.get("number")),
            ("Priority Tier", "select", lambda p: p.get("select", {}).get("name") if p.get("select") else None),
            ("Score Breakdown", "rich_text", lambda p: p.get("rich_text", [{}])[0].get("plain_text") if p.get("rich_text") else None),
            ("Confidence Flags", "multi_select", lambda p: [s.get("name") for s in p.get("multi_select", [])] if p.get("multi_select") else []),
            ("Scoring Status", "select", lambda p: p.get("select", {}).get("name") if p.get("select") else None),
        ]
    }

    # Validate each feature's fields
    for feature, fields in fields_by_feature.items():
        print(f"{'─' * 80}")
        print(f"{feature}")
        print(f"{'─' * 80}")

        feature_populated = 0
        feature_total = len(fields)

        for field_name, field_type, extractor in fields:
            prop = properties.get(field_name, {})

            try:
                value = extractor(prop)

                # Check if populated
                is_populated = False
                if value is not None:
                    if isinstance(value, list):
                        is_populated = len(value) > 0
                    elif isinstance(value, bool):
                        is_populated = True  # Checkbox can be False but still populated
                    elif isinstance(value, (str, int, float)):
                        is_populated = value != "" and value != 0
                    else:
                        is_populated = True

                if is_populated:
                    feature_populated += 1

                    # Format value for display
                    if isinstance(value, list):
                        display_value = f"[{', '.join(str(v) for v in value)}]" if value else "[]"
                    elif isinstance(value, bool):
                        display_value = "✓" if value else "✗"
                    elif value is None:
                        display_value = "None"
                    else:
                        display_value = str(value)

                    # Truncate long values
                    if len(display_value) > 60:
                        display_value = display_value[:57] + "..."

                    print(f"  ✅ {field_name:30} = {display_value}")
                else:
                    print(f"  ❌ {field_name:30} = (empty)")

            except Exception as e:
                print(f"  ⚠️  {field_name:30} = ERROR: {e}")

        print()
        print(f"  Summary: {feature_populated}/{feature_total} fields populated ({feature_populated/feature_total*100:.0f}%)")
        print()

    print("=" * 80)

    # Overall summary
    total_fields = sum(len(fields) for fields in fields_by_feature.values())
    populated_fields = 0
    for fields in fields_by_feature.values():
        for field_name, field_type, extractor in fields:
            prop = properties.get(field_name, {})
            try:
                value = extractor(prop)
                if value is not None:
                    if isinstance(value, list):
                        if len(value) > 0:
                            populated_fields += 1
                    elif isinstance(value, bool):
                        populated_fields += 1
                    elif isinstance(value, (str, int, float)):
                        if value != "" and value != 0:
                            populated_fields += 1
                    else:
                        populated_fields += 1
            except:
                pass

    print(f"OVERALL: {populated_fields}/{total_fields} fields populated ({populated_fields/total_fields*100:.0f}%)")
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_notion_fields.py <practice_id>")
        print("\nExample:")
        print("  python validate_notion_fields.py 2a1edda2-a9a0-8100-8091-ecaf3ad75d8f")
        sys.exit(1)

    practice_id = sys.argv[1]
    validate_practice_fields(practice_id)
