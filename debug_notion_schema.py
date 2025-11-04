#!/usr/bin/env python3
"""
Debug script to inspect Notion database schema.
Shows what properties exist and their types.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config.config import VetScrapingConfig
from notion_client import Client

def main():
    config = VetScrapingConfig()

    print("=" * 80)
    print("NOTION DATABASE SCHEMA INSPECTOR")
    print("=" * 80)
    print(f"Database ID: {config.notion.database_id}")
    print()

    try:
        client = Client(auth=config.notion.api_key)
        database = client.databases.retrieve(database_id=config.notion.database_id)

        print(f"Database Title: {database.get('title', [{}])[0].get('plain_text', 'N/A')}")
        print()
        print("EXISTING PROPERTIES:")
        print("-" * 80)

        properties = database.get("properties", {})

        if not properties:
            print("❌ No properties found in database!")
        else:
            for name, prop in sorted(properties.items()):
                prop_type = prop.get("type", "unknown")
                print(f"  • {name:30} → {prop_type}")

        print()
        print("REQUIRED PROPERTIES FOR FEAT-001:")
        print("-" * 80)

        required = {
            "Name": "title",
            "Google Place ID": "rich_text",
            "Address": "rich_text",
            "Phone": "phone_number",
            "Website": "url",
            "Google Review Count": "number",
            "Google Rating": "number",
            "Lead Score": "number",
            "Status": "select",
        }

        for name, expected_type in sorted(required.items()):
            if name in properties:
                actual_type = properties[name].get("type")
                if actual_type == expected_type:
                    print(f"  ✓ {name:30} → {expected_type}")
                else:
                    print(f"  ⚠ {name:30} → Expected: {expected_type}, Got: {actual_type}")
            else:
                print(f"  ✗ {name:30} → MISSING (needs {expected_type})")

        print()
        print("=" * 80)

        # Summary
        existing_names = set(properties.keys())
        required_names = set(required.keys())
        missing = required_names - existing_names

        if missing:
            print(f"❌ VALIDATION FAILED: Missing {len(missing)} properties")
            print(f"   Missing: {sorted(missing)}")
        else:
            print("✓ All required properties exist")

            # Check types
            type_errors = []
            for name, expected_type in required.items():
                actual_type = properties[name].get("type")
                if actual_type != expected_type:
                    type_errors.append(f"{name} (expected {expected_type}, got {actual_type})")

            if type_errors:
                print(f"⚠ Type mismatches: {type_errors}")
            else:
                print("✓ All property types match")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
