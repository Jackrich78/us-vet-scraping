#!/usr/bin/env python3
"""
Spike Test: Validate Notion Database Schema

Checks that all 20 enrichment fields exist in the Notion database
with correct types and configurations.
"""

import os
import json
from notion_client import Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Required enrichment fields
REQUIRED_FIELDS = {
    "Confirmed Vet Count (Total)": "number",
    "Vet Count Confidence": "select",
    "Decision Maker Name": "rich_text",
    "Decision Maker Role": "select",
    "Decision Maker Email": "email",
    "Decision Maker Phone": "phone_number",
    "24/7 Emergency Services": "checkbox",
    "Specialty Services": "multi_select",
    "Wellness Programs": "checkbox",
    "Boarding Services": "checkbox",
    "Online Booking": "checkbox",
    "Telemedicine": "checkbox",
    "Patient Portal": "checkbox",
    "Digital Records Mentioned": "checkbox",
    "Personalization Context (Multi)": "multi_select",
    "Awards/Accreditations": "multi_select",
    "Unique Services": "multi_select",
    "Enrichment Status": "select",
    "Last Enrichment Date": "date",
    "Enrichment Error": "rich_text"
}

# Required select options
REQUIRED_SELECT_OPTIONS = {
    "Vet Count Confidence": ["high", "medium", "low"],
    "Decision Maker Role": ["Owner", "Practice Manager", "Medical Director"],
    "Enrichment Status": ["Pending", "Completed", "Failed"]
}

def validate_notion_schema():
    """Validate Notion database schema against FEAT-002 requirements."""

    client = Client(auth=os.getenv("NOTION_API_KEY"))
    database_id = os.getenv("NOTION_DATABASE_ID")

    print("="*60)
    print("NOTION SCHEMA VALIDATION")
    print("="*60)
    print(f"Database ID: {database_id}")
    print()

    # Retrieve database schema
    try:
        db = client.databases.retrieve(database_id)
    except Exception as e:
        print(f"❌ Failed to retrieve database: {e}")
        return False

    properties = db["properties"]
    print(f"✅ Database retrieved successfully")
    print(f"   Total properties: {len(properties)}")
    print()

    # Check each required field
    print("Checking required fields...")
    print("-"*60)

    missing_fields = []
    incorrect_types = []
    missing_options = []

    for field_name, expected_type in REQUIRED_FIELDS.items():
        if field_name not in properties:
            missing_fields.append(field_name)
            print(f"❌ MISSING: {field_name} ({expected_type})")
        else:
            actual_type = properties[field_name]["type"]
            if actual_type != expected_type:
                incorrect_types.append((field_name, expected_type, actual_type))
                print(f"⚠️  TYPE MISMATCH: {field_name}")
                print(f"   Expected: {expected_type}, Actual: {actual_type}")
            else:
                # Check select options if applicable
                if expected_type == "select" and field_name in REQUIRED_SELECT_OPTIONS:
                    expected_options = REQUIRED_SELECT_OPTIONS[field_name]
                    actual_options = [opt["name"] for opt in properties[field_name]["select"]["options"]]

                    missing_opts = [opt for opt in expected_options if opt not in actual_options]
                    if missing_opts:
                        missing_options.append((field_name, missing_opts))
                        print(f"⚠️  MISSING OPTIONS: {field_name}")
                        print(f"   Missing: {', '.join(missing_opts)}")
                    else:
                        print(f"✅ {field_name} ({expected_type}) - Options OK")
                else:
                    print(f"✅ {field_name} ({expected_type})")

    print()
    print("="*60)
    print("VALIDATION SUMMARY")
    print("="*60)

    if missing_fields:
        print(f"\n❌ MISSING FIELDS ({len(missing_fields)}):")
        for field in missing_fields:
            print(f"   - {field} ({REQUIRED_FIELDS[field]})")

    if incorrect_types:
        print(f"\n❌ INCORRECT TYPES ({len(incorrect_types)}):")
        for field, expected, actual in incorrect_types:
            print(f"   - {field}: expected {expected}, got {actual}")

    if missing_options:
        print(f"\n⚠️  MISSING SELECT OPTIONS ({len(missing_options)}):")
        for field, opts in missing_options:
            print(f"   - {field}: {', '.join(opts)}")

    all_valid = not (missing_fields or incorrect_types or missing_options)

    if all_valid:
        print("\n✅ ALL VALIDATION CHECKS PASSED!")
        print("   Notion schema is ready for FEAT-002 implementation.")
    else:
        print(f"\n❌ VALIDATION FAILED")
        print(f"   {len(missing_fields)} missing fields")
        print(f"   {len(incorrect_types)} incorrect types")
        print(f"   {len(missing_options)} fields with missing options")
        print("\n   ACTION REQUIRED:")
        if missing_fields:
            print("   1. Create missing fields in Notion database")
        if incorrect_types:
            print("   2. Fix field types in Notion database")
        if missing_options:
            print("   3. Add missing select options in Notion database")

    print("="*60)

    return all_valid

if __name__ == "__main__":
    try:
        success = validate_notion_schema()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
