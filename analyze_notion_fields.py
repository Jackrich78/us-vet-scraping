#!/usr/bin/env python3
"""
Analyze ALL Notion database fields and compare with feature requirements.

This will show:
1. All existing fields in Notion
2. Fields required by each feature (FEAT-001, FEAT-002, FEAT-003)
3. Naming inconsistencies
4. Unused/duplicate fields
5. Recommendations for consolidation
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from notion_client import Client
import json

# Load environment
load_dotenv()

def main():
    # Get credentials
    api_key = os.getenv("NOTION_API_KEY")
    database_id = os.getenv("NOTION_DATABASE_ID")

    if not api_key or not database_id:
        print("❌ Error: NOTION_API_KEY and NOTION_DATABASE_ID must be set")
        sys.exit(1)

    client = Client(auth=api_key)

    try:
        # Retrieve database schema
        response = client.databases.retrieve(database_id=database_id)
        properties = response.get("properties", {})

        print("=" * 100)
        print("COMPLETE NOTION DATABASE FIELD ANALYSIS")
        print("=" * 100)
        print(f"\nDatabase ID: {database_id}")
        print(f"Total Fields: {len(properties)}\n")

        # Group fields by type
        fields_by_type = {}
        for name, prop in properties.items():
            field_type = prop["type"]
            if field_type not in fields_by_type:
                fields_by_type[field_type] = []
            fields_by_type[field_type].append(name)

        print("\n" + "=" * 100)
        print("ALL EXISTING FIELDS (Grouped by Type)")
        print("=" * 100)

        for field_type in sorted(fields_by_type.keys()):
            fields = sorted(fields_by_type[field_type])
            print(f"\n{field_type.upper()} ({len(fields)} fields):")
            for field in fields:
                # Get additional info for select/multi-select
                field_data = properties[field]
                if field_type == "select" and "select" in field_data:
                    options = field_data["select"].get("options", [])
                    if options:
                        option_names = [opt["name"] for opt in options]
                        print(f"  • {field:40s} Options: {', '.join(option_names)}")
                    else:
                        print(f"  • {field}")
                elif field_type == "multi_select" and "multi_select" in field_data:
                    options = field_data["multi_select"].get("options", [])
                    if options:
                        option_names = [opt["name"] for opt in options]
                        print(f"  • {field:40s} Options: {', '.join(option_names[:3])}{'...' if len(option_names) > 3 else ''}")
                    else:
                        print(f"  • {field}")
                else:
                    print(f"  • {field}")

        # Feature requirements
        print("\n" + "=" * 100)
        print("FEATURE REQUIREMENTS ANALYSIS")
        print("=" * 100)

        feat001_fields = {
            "READS": [],
            "WRITES": [
                ("Name", "title", "Practice name"),
                ("Address", "rich_text", "Full street address"),
                ("City", "rich_text", "City name"),
                ("State", "select", "State (MA, etc.)"),
                ("Zip", "rich_text", "Zip code"),
                ("Phone", "phone_number", "Primary phone"),
                ("Website", "url", "Practice website"),
                ("Google Maps URL", "url", "Google Maps listing URL"),
                ("Place ID", "rich_text", "Unique Google Place ID"),
                ("Rating", "number", "Google rating 0-5"),
                ("Review Count", "number", "Number of Google reviews"),
                ("Categories", "multi_select", "Google business categories"),
                ("Hours", "rich_text", "Operating hours"),
                ("Initial Score", "number", "0-25 baseline score from Google data"),
                ("Status", "select", "Lead status (New, Contacted, etc.)"),
            ]
        }

        feat002_fields = {
            "READS": [
                ("Name", "title", "To identify practice"),
                ("Website", "url", "To scrape for enrichment"),
                ("Place ID", "rich_text", "Unique identifier"),
            ],
            "WRITES": [
                ("Vet Count", "number", "Total veterinarians"),
                ("Vet Count Confidence", "select", "high/medium/low"),
                ("Vet Count Per Location", "rich_text", "Breakdown by location"),
                ("Emergency 24/7", "checkbox", "Has 24/7 emergency services"),
                ("Online Booking", "checkbox", "Has online appointment booking"),
                ("Patient Portal", "checkbox", "Has client portal"),
                ("Telemedicine", "checkbox", "Offers telemedicine/virtual care"),
                ("Specialty Services", "multi_select", "Surgery, Dentistry, etc."),
                ("Decision Maker Name", "rich_text", "Name of practice owner/manager"),
                ("Decision Maker Role", "rich_text", "Job title"),
                ("Decision Maker Email", "email", "Contact email"),
                ("Decision Maker Phone", "phone_number", "Contact phone"),
                ("Personalization Context", "rich_text", "2-3 unique facts"),
                ("Awards Accreditations", "multi_select", "Certifications, awards"),
                ("Enrichment Status", "select", "New/In Progress/Completed/Failed"),
                ("Last Enrichment Date", "date", "When enrichment last ran"),
                ("Data Completeness", "number", "0-100% data quality score"),
                ("Data Sources", "rich_text", "URLs scraped"),
            ]
        }

        feat003_fields = {
            "READS": [
                ("Rating", "number", "Google rating for baseline"),
                ("Review Count", "number", "Google reviews for call volume & baseline"),
                ("Website", "url", "For baseline scoring"),
                ("Multiple Locations", "checkbox", "For call volume & baseline"),
                ("Vet Count", "number", "For practice size scoring"),
                ("Vet Count Confidence", "select", "For confidence penalty"),
                ("Emergency 24/7", "checkbox", "For practice size bonus"),
                ("Online Booking", "checkbox", "For technology scoring"),
                ("Patient Portal", "checkbox", "For technology scoring"),
                ("Telemedicine", "checkbox", "For technology scoring"),
                ("Specialty Services", "multi_select", "For call volume scoring"),
                ("Decision Maker Name", "rich_text", "For decision maker bonus"),
                ("Decision Maker Email", "email", "For decision maker bonus"),
                ("Enrichment Status", "select", "To check if enrichment completed"),
            ],
            "WRITES": [
                ("Lead Score", "number", "0-120 ICP fit score"),
                ("Priority Tier", "select", "Hot/Warm/Cold/Out of Scope/Pending"),
                ("Score Breakdown", "rich_text", "JSON with component scores"),
                ("Confidence Flags", "multi_select", "Warnings about data quality"),
                ("Scoring Status", "select", "Scored/Failed/Not Scored"),
            ]
        }

        # Analyze each feature
        for feat_name, feat_data in [("FEAT-001", feat001_fields), ("FEAT-002", feat002_fields), ("FEAT-003", feat003_fields)]:
            print(f"\n{feat_name} (Google Maps Scraping)" if feat_name == "FEAT-001" else
                  f"\n{feat_name} (Website Enrichment)" if feat_name == "FEAT-002" else
                  f"\n{feat_name} (Lead Scoring)")
            print("-" * 100)

            for operation in ["READS", "WRITES"]:
                if not feat_data[operation]:
                    continue

                print(f"\n  {operation}:")
                for field_name, field_type, description in feat_data[operation]:
                    exists = field_name in properties
                    if exists:
                        actual_type = properties[field_name]["type"]
                        type_match = actual_type == field_type
                        status = "✅" if type_match else f"⚠️ (type mismatch: {actual_type})"
                    else:
                        status = "❌ MISSING"

                    print(f"    {status} {field_name:35s} ({field_type:15s}) - {description}")

        # Find naming inconsistencies
        print("\n" + "=" * 100)
        print("NAMING PATTERN ANALYSIS")
        print("=" * 100)

        # Look for common patterns
        potential_duplicates = []
        field_names = list(properties.keys())

        # Check for similar names
        print("\nPotential Naming Issues:")
        if "Rating" not in properties and "Google Rating" in properties:
            potential_duplicates.append(("Rating", "Google Rating", "Different names for same field"))
        if "Review Count" not in properties and "Google Review Count" in properties:
            potential_duplicates.append(("Review Count", "Google Review Count", "Different names for same field"))
        if "Multiple Locations" not in properties and "Has Multiple Locations" in properties:
            potential_duplicates.append(("Multiple Locations", "Has Multiple Locations", "Different names for same field"))
        if "Emergency 24/7" not in properties and "Has Emergency Services" in properties:
            potential_duplicates.append(("Emergency 24/7", "Has Emergency Services", "Different names for same field"))

        if potential_duplicates:
            for expected, actual, reason in potential_duplicates:
                print(f"  • Expected: '{expected}' but found: '{actual}' - {reason}")
        else:
            print("  ✅ No obvious naming inconsistencies found")

        # Recommendations
        print("\n" + "=" * 100)
        print("RECOMMENDATIONS FOR SCHEMA CONSOLIDATION")
        print("=" * 100)

        print("\n1. STANDARDIZE NAMING CONVENTIONS:")
        print("   • Use simple, clear names without prefixes")
        print("   • Example: 'Rating' not 'Google Rating'")
        print("   • Example: 'Emergency 24/7' not 'Has Emergency Services'")

        print("\n2. MISSING FIELDS TO ADD:")
        all_missing = set()
        for feat_name, feat_data in [("FEAT-001", feat001_fields), ("FEAT-002", feat002_fields), ("FEAT-003", feat003_fields)]:
            for operation in ["READS", "WRITES"]:
                for field_name, field_type, description in feat_data[operation]:
                    if field_name not in properties:
                        all_missing.add((field_name, field_type, feat_name))

        if all_missing:
            for field_name, field_type, needed_by in sorted(all_missing):
                print(f"   • {field_name:35s} ({field_type:15s}) - Needed by {needed_by}")

        print("\n3. FIELDS TO RENAME (If Different):")
        print("   Check if these exist with different names:")
        for expected, actual, reason in potential_duplicates:
            print(f"   • '{actual}' → '{expected}'")

        print("\n4. UNUSED FIELDS (Not referenced by any feature):")
        feature_fields = set()
        for feat_data in [feat001_fields, feat002_fields, feat003_fields]:
            for operation in ["READS", "WRITES"]:
                for field_name, _, _ in feat_data[operation]:
                    feature_fields.add(field_name)

        unused = []
        for field_name in properties.keys():
            if field_name not in feature_fields:
                unused.append(field_name)

        if unused:
            for field in sorted(unused):
                print(f"   • {field:35s} ({properties[field]['type']})")
        else:
            print("   ✅ All fields are used by at least one feature")

        print("\n" + "=" * 100)
        print("NEXT STEPS")
        print("=" * 100)
        print("\n1. Review existing fields and identify which ones match requirements")
        print("2. Rename fields for consistency (if needed)")
        print("3. Add missing fields")
        print("4. Update feature code to use actual field names")
        print("5. Re-run schema check to verify")

        # Export to JSON for detailed analysis
        output_file = "notion_schema_analysis.json"
        analysis_data = {
            "database_id": database_id,
            "total_fields": len(properties),
            "existing_fields": {name: prop["type"] for name, prop in properties.items()},
            "feature_requirements": {
                "FEAT-001": feat001_fields,
                "FEAT-002": feat002_fields,
                "FEAT-003": feat003_fields
            },
            "missing_fields": list(all_missing),
            "potential_duplicates": potential_duplicates,
            "unused_fields": unused
        }

        with open(output_file, 'w') as f:
            json.dump(analysis_data, f, indent=2)

        print(f"\n📄 Detailed analysis exported to: {output_file}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
