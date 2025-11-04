#!/usr/bin/env python3
"""
Check Notion database schema for required scoring fields.

Usage:
    python3 check_notion_schema.py

This will verify that all required fields exist for lead scoring.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from notion_client import Client

# Load environment
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    # Get credentials
    api_key = os.getenv("NOTION_API_KEY")
    database_id = os.getenv("NOTION_DATABASE_ID")

    if not api_key or not database_id:
        print("❌ Error: NOTION_API_KEY and NOTION_DATABASE_ID must be set in .env file")
        sys.exit(1)

    print(f"Checking Notion database schema...")
    print(f"Database ID: {database_id}\n")

    client = Client(auth=api_key)

    # Required fields for scoring (using actual Notion database field names)
    required_fields = {
        # Fields we READ
        "Name": "title",
        "Website": "url",
        "Google Rating": "number",  # Database has "Google Rating" not "Rating"
        "Google Review Count": "number",  # Database has "Google Review Count" not "Review Count"
        "Has Multiple Locations": "checkbox",  # Database has "Has Multiple Locations" not "Multiple Locations"
        "Vet Count": "number",
        "Vet Count Confidence": "select",
        "24/7 Emergency Services": "checkbox",  # Database has "24/7 Emergency Services" not "Emergency 24/7"
        "Online Booking": "checkbox",
        "Patient Portal": "checkbox",
        "Telemedicine": "checkbox",
        "Specialty Services": "multi_select",
        "Decision Maker Name": "rich_text",
        "Decision Maker Email": "email",
        "Enrichment Status": "select",
        # Fields we WRITE
        "Lead Score": "number",
        "Priority Tier": "select",
        "Score Breakdown": "rich_text",
        "Confidence Flags": "multi_select",
        "Scoring Status": "select",
    }

    try:
        # Retrieve database schema
        response = client.databases.retrieve(database_id=database_id)
        properties = response.get("properties", {})

        print("=" * 80)
        print("NOTION DATABASE SCHEMA CHECK")
        print("=" * 80)

        missing_fields = []
        type_mismatches = []
        existing_fields = []

        for field_name, expected_type in required_fields.items():
            if field_name not in properties:
                missing_fields.append((field_name, expected_type))
            else:
                actual_type = properties[field_name]["type"]
                if actual_type == expected_type:
                    existing_fields.append((field_name, actual_type))
                else:
                    type_mismatches.append((field_name, expected_type, actual_type))

        # Print results
        if existing_fields:
            print("\n✅ EXISTING FIELDS:")
            for field_name, field_type in sorted(existing_fields):
                print(f"   {field_name:30s} ({field_type})")

        if type_mismatches:
            print("\n⚠️  TYPE MISMATCHES:")
            for field_name, expected, actual in sorted(type_mismatches):
                print(f"   {field_name:30s} Expected: {expected}, Found: {actual}")

        if missing_fields:
            print("\n❌ MISSING FIELDS:")
            for field_name, field_type in sorted(missing_fields):
                print(f"   {field_name:30s} ({field_type})")

            print("\n" + "=" * 80)
            print("HOW TO ADD MISSING FIELDS")
            print("=" * 80)
            print("\n1. Open your Notion database in a web browser")
            print("2. Click the '+' button to add a new property")
            print("3. Add each missing field with the correct type:")

            for field_name, field_type in sorted(missing_fields):
                notion_type_map = {
                    "number": "Number",
                    "select": "Select",
                    "multi_select": "Multi-select",
                    "checkbox": "Checkbox",
                    "rich_text": "Text",
                    "email": "Email",
                    "url": "URL",
                    "title": "Title"
                }
                notion_type = notion_type_map.get(field_type, field_type)
                print(f"\n   Field: {field_name}")
                print(f"   Type: {notion_type}")

                # Special instructions for select fields
                if field_type == "select":
                    if field_name == "Priority Tier":
                        print(f"   Options: 🔥 Hot, 🌡️ Warm, ❄️ Cold, ⛔ Out of Scope, ⏳ Pending Enrichment")
                    elif field_name == "Scoring Status":
                        print(f"   Options: Scored, Failed, Not Scored")
                    elif field_name == "Vet Count Confidence":
                        print(f"   Options: high, medium, low")
                    elif field_name == "Enrichment Status":
                        print(f"   Options: New, In Progress, Completed, Failed, Partial")

        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total Required: {len(required_fields)}")
        print(f"✅ Existing: {len(existing_fields)}")
        print(f"⚠️  Type Mismatches: {len(type_mismatches)}")
        print(f"❌ Missing: {len(missing_fields)}")

        if missing_fields or type_mismatches:
            print("\n⚠️  Database schema is INCOMPLETE")
            print("   Please add/fix the fields listed above before running scoring.")
            sys.exit(1)
        else:
            print("\n✅ Database schema is COMPLETE and ready for scoring!")
            sys.exit(0)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
