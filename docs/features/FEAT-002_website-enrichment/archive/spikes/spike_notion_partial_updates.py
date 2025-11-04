#!/usr/bin/env python3
"""
Spike Test 7: Notion Partial Updates

Tests that updating enrichment fields preserves sales workflow fields.

Success Criteria:
- Sales workflow fields unchanged after enrichment update
- Only enrichment fields updated
- No read-before-write needed (Notion API handles partial updates)
"""

import os
from datetime import datetime
from notion_client import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_notion_partial_updates():
    """Test Notion API partial updates preserve untouched fields."""

    print("="*60)
    print("NOTION PARTIAL UPDATES TEST")
    print("="*60)
    print()

    notion = Client(auth=os.getenv("NOTION_API_KEY"))
    database_id = os.getenv("NOTION_DATABASE_ID")

    # Step 1: Query for a practice to test with
    print("Step 1: Querying for test practice...")
    print("-"*60)

    response = notion.databases.query(
        database_id=database_id,
        filter={
            "property": "Website",
            "url": {"is_not_empty": True}
        },
        page_size=1
    )

    if not response["results"]:
        print("❌ No practices with websites found in database")
        print("   Create at least one practice with a website to run this test")
        return False

    page = response["results"][0]
    page_id = page["id"]
    practice_name = page["properties"].get("Practice Name", {}).get("title", [{}])[0].get("plain_text", "Unknown")

    print(f"✅ Found test practice: {practice_name}")
    print(f"   Page ID: {page_id}")
    print()

    # Step 2: Capture current sales workflow fields
    print("Step 2: Capturing current sales workflow fields...")
    print("-"*60)

    def get_field_value(properties, field_name, field_type):
        """Helper to extract field values safely."""
        prop = properties.get(field_name, {})
        if field_type == "select" and prop.get("select"):
            return prop["select"]["name"]
        elif field_type == "people" and prop.get("people"):
            return [p.get("name", p.get("id")) for p in prop["people"]]
        elif field_type == "rich_text" and prop.get("rich_text"):
            return prop["rich_text"][0].get("plain_text", "") if prop["rich_text"] else ""
        elif field_type == "date" and prop.get("date"):
            return prop["date"]["start"]
        return None

    before_state = {
        "Status": get_field_value(page["properties"], "Status", "select"),
        "Assigned To": get_field_value(page["properties"], "Assigned To", "people"),
        "Research Notes": get_field_value(page["properties"], "Research Notes", "rich_text"),
        "Call Notes": get_field_value(page["properties"], "Call Notes", "rich_text"),
        "Last Contact Date": get_field_value(page["properties"], "Last Contact Date", "date"),
    }

    print("Sales Workflow Fields (BEFORE):")
    for field, value in before_state.items():
        print(f"  {field}: {value}")
    print()

    # Step 3: Update ONLY enrichment fields (partial update)
    print("Step 3: Updating ONLY enrichment fields...")
    print("-"*60)

    enrichment_update = {
        "Confirmed Vet Count (Total)": {"number": 5},
        "Vet Count Confidence": {"select": {"name": "high"}},
        "Decision Maker Name": {"rich_text": [{"text": {"content": "Dr. Test Spike"}}]},
        "Decision Maker Role": {"select": {"name": "Owner"}},
        "24/7 Emergency Services": {"checkbox": True},
        "Online Booking": {"checkbox": True},
        "Enrichment Status": {"select": {"name": "Completed"}},
        "Last Enrichment Date": {"date": {"start": datetime.utcnow().isoformat()}}
    }

    print("Enrichment fields being updated:")
    for field in enrichment_update.keys():
        print(f"  - {field}")
    print()

    try:
        notion.pages.update(
            page_id=page_id,
            properties=enrichment_update
        )
        print("✅ Notion API update successful")
    except Exception as e:
        print(f"❌ Notion API update failed: {e}")
        return False

    print()

    # Step 4: Re-query the page and verify sales fields unchanged
    print("Step 4: Verifying sales workflow fields preserved...")
    print("-"*60)

    updated_page = notion.pages.retrieve(page_id=page_id)

    after_state = {
        "Status": get_field_value(updated_page["properties"], "Status", "select"),
        "Assigned To": get_field_value(updated_page["properties"], "Assigned To", "people"),
        "Research Notes": get_field_value(updated_page["properties"], "Research Notes", "rich_text"),
        "Call Notes": get_field_value(updated_page["properties"], "Call Notes", "rich_text"),
        "Last Contact Date": get_field_value(updated_page["properties"], "Last Contact Date", "date"),
    }

    print("Sales Workflow Fields (AFTER):")
    for field, value in after_state.items():
        print(f"  {field}: {value}")
    print()

    # Step 5: Validate enrichment fields were updated
    print("Step 5: Validating enrichment fields updated...")
    print("-"*60)

    enrichment_checks = []

    vet_count = updated_page["properties"].get("Confirmed Vet Count (Total)", {}).get("number")
    enrichment_checks.append(("Vet Count = 5", vet_count == 5))

    vet_confidence = get_field_value(updated_page["properties"], "Vet Count Confidence", "select")
    enrichment_checks.append(("Vet Confidence = high", vet_confidence == "high"))

    decision_maker = get_field_value(updated_page["properties"], "Decision Maker Name", "rich_text")
    enrichment_checks.append(("Decision Maker = Dr. Test Spike", decision_maker == "Dr. Test Spike"))

    emergency = updated_page["properties"].get("24/7 Emergency Services", {}).get("checkbox")
    enrichment_checks.append(("Emergency Services = True", emergency == True))

    online_booking = updated_page["properties"].get("Online Booking", {}).get("checkbox")
    enrichment_checks.append(("Online Booking = True", online_booking == True))

    enrichment_status = get_field_value(updated_page["properties"], "Enrichment Status", "select")
    enrichment_checks.append(("Enrichment Status = Completed", enrichment_status == "Completed"))

    print("Enrichment Field Updates:")
    all_enrichment_passed = True
    for check, passed in enrichment_checks:
        icon = "✅" if passed else "❌"
        print(f"  {icon} {check}")
        if not passed:
            all_enrichment_passed = False
    print()

    # Step 6: Compare before and after sales fields
    print("Step 6: Final validation...")
    print("-"*60)

    sales_fields_preserved = True
    for field in before_state.keys():
        if before_state[field] != after_state[field]:
            print(f"❌ {field} changed!")
            print(f"   Before: {before_state[field]}")
            print(f"   After: {after_state[field]}")
            sales_fields_preserved = False

    if sales_fields_preserved:
        print("✅ All sales workflow fields preserved")

    print()

    # Summary
    print("="*60)
    print("TEST SUMMARY")
    print("="*60)

    criteria = [
        ("Sales workflow fields preserved", sales_fields_preserved),
        ("Enrichment fields updated correctly", all_enrichment_passed),
    ]

    all_passed = True
    for criterion, passed in criteria:
        icon = "✅" if passed else "❌"
        print(f"{icon} {criterion}")
        if not passed:
            all_passed = False

    print("="*60)

    if all_passed:
        print("\n✅ ALL CRITERIA PASSED!")
        print("   Notion partial updates work correctly for FEAT-002.")
    else:
        print("\n❌ SOME CRITERIA FAILED")
        print("   Review failures above and adjust implementation.")

    print("="*60)

    return all_passed

if __name__ == "__main__":
    try:
        success = test_notion_partial_updates()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
