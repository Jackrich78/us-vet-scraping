#!/usr/bin/env python3
"""
Spike Test: Create Missing Notion Enrichment Fields

Creates all 20 required enrichment fields for FEAT-002 in the Notion database.
"""

import os
from notion_client import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_enrichment_fields():
    """Create all missing enrichment fields in Notion database."""

    client = Client(auth=os.getenv("NOTION_API_KEY"))
    database_id = os.getenv("NOTION_DATABASE_ID")

    print("="*60)
    print("CREATING NOTION ENRICHMENT FIELDS")
    print("="*60)
    print(f"Database ID: {database_id}")
    print()

    # Define all enrichment fields with their schemas
    fields_to_create = {
        "Confirmed Vet Count (Total)": {
            "number": {
                "format": "number"
            }
        },
        "Vet Count Confidence": {
            "select": {
                "options": [
                    {"name": "high", "color": "green"},
                    {"name": "medium", "color": "yellow"},
                    {"name": "low", "color": "red"}
                ]
            }
        },
        "Decision Maker Name": {
            "rich_text": {}
        },
        "Decision Maker Role": {
            "select": {
                "options": [
                    {"name": "Owner", "color": "blue"},
                    {"name": "Practice Manager", "color": "purple"},
                    {"name": "Medical Director", "color": "green"}
                ]
            }
        },
        "Decision Maker Email": {
            "email": {}
        },
        "Decision Maker Phone": {
            "phone_number": {}
        },
        "24/7 Emergency Services": {
            "checkbox": {}
        },
        "Specialty Services": {
            "multi_select": {
                "options": [
                    {"name": "Surgery", "color": "blue"},
                    {"name": "Dental", "color": "green"},
                    {"name": "Oncology", "color": "red"},
                    {"name": "Cardiology", "color": "purple"},
                    {"name": "Dermatology", "color": "yellow"},
                    {"name": "Ophthalmology", "color": "orange"},
                    {"name": "Orthopedics", "color": "pink"},
                    {"name": "Internal Medicine", "color": "brown"}
                ]
            }
        },
        "Wellness Programs": {
            "checkbox": {}
        },
        "Boarding Services": {
            "checkbox": {}
        },
        "Online Booking": {
            "checkbox": {}
        },
        "Telemedicine": {
            "checkbox": {}
        },
        "Patient Portal": {
            "checkbox": {}
        },
        "Digital Records Mentioned": {
            "checkbox": {}
        },
        "Awards/Accreditations": {
            "multi_select": {
                "options": [
                    {"name": "AAHA Accredited", "color": "blue"},
                    {"name": "Fear Free Certified", "color": "green"},
                    {"name": "Cat Friendly Practice", "color": "purple"}
                ]
            }
        },
        "Unique Services": {
            "multi_select": {
                "options": []
            }
        },
        "Enrichment Status": {
            "select": {
                "options": [
                    {"name": "Pending", "color": "yellow"},
                    {"name": "Completed", "color": "green"},
                    {"name": "Failed", "color": "red"}
                ]
            }
        },
        "Last Enrichment Date": {
            "date": {}
        },
        "Enrichment Error": {
            "rich_text": {}
        }
    }

    # Fix existing "Personalization Context" field (change from rich_text to multi_select)
    print("Step 1: Fixing 'Personalization Context' field type...")
    print("-"*60)

    # Note: Notion API doesn't support changing field types directly
    # We'll need to create it as a new field or manually fix it
    print("⚠️  'Personalization Context' exists as rich_text but should be multi_select")
    print("   This field needs to be manually converted in Notion UI, or:")
    print("   1. Rename existing field to 'Personalization Context (Old)'")
    print("   2. Create new 'Personalization Context' as multi_select")
    print()

    # Create all missing fields
    print("Step 2: Creating missing enrichment fields...")
    print("-"*60)

    created_count = 0
    failed_count = 0

    for field_name, field_schema in fields_to_create.items():
        try:
            # Update database schema to add the new property
            client.databases.update(
                database_id=database_id,
                properties={
                    field_name: field_schema
                }
            )
            print(f"✅ Created: {field_name}")
            created_count += 1

        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"⚠️  Already exists: {field_name}")
            else:
                print(f"❌ Failed to create '{field_name}': {e}")
                failed_count += 1

    print()
    print("="*60)
    print("CREATION SUMMARY")
    print("="*60)
    print(f"✅ Created: {created_count} fields")
    print(f"⚠️  Failed: {failed_count} fields")
    print()

    if failed_count == 0:
        print("✅ ALL FIELDS CREATED SUCCESSFULLY!")
        print()
        print("NEXT STEPS:")
        print("1. Manually fix 'Personalization Context' field in Notion UI:")
        print("   - Change type from 'Text' to 'Multi-select'")
        print("   - Or rename old field and create new multi_select field")
        print("2. Re-run schema validation: python3 spike_notion_schema.py")
    else:
        print(f"❌ {failed_count} fields failed to create")
        print("   Review errors above and retry")

    print("="*60)

    return failed_count == 0

if __name__ == "__main__":
    try:
        success = create_enrichment_fields()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
