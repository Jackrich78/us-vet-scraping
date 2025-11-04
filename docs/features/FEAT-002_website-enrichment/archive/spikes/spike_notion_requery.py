#!/usr/bin/env python3
"""
Spike Test 8: Notion Re-enrichment Query

Tests that re-enrichment query filter returns correct practices:
- New practices (never enriched)
- Stale practices (enriched >30 days ago)
- Excludes recent practices (enriched <30 days ago)

Success Criteria:
- Query returns practices needing enrichment
- Excludes recently enriched practices
- OR filter works correctly
"""

import os
from datetime import datetime, timedelta, UTC
from notion_client import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_notion_requery():
    """Test Notion re-enrichment query filter."""

    print("="*60)
    print("NOTION RE-ENRICHMENT QUERY TEST")
    print("="*60)
    print()

    notion = Client(auth=os.getenv("NOTION_API_KEY"))
    database_id = os.getenv("NOTION_DATABASE_ID")

    # Calculate 30 days ago
    thirty_days_ago = (datetime.now(UTC) - timedelta(days=30)).isoformat()

    print("Query Configuration:")
    print(f"  30 days ago: {thirty_days_ago}")
    print()

    # Step 1: Query all practices with websites
    print("Step 1: Querying ALL practices with websites...")
    print("-"*60)

    all_practices = notion.databases.query(
        database_id=database_id,
        filter={
            "property": "Website",
            "url": {"is_not_empty": True}
        }
    )

    total_with_websites = len(all_practices["results"])
    print(f"✅ Found {total_with_websites} practices with websites")
    print()

    # Step 2: Query practices needing enrichment (new OR stale)
    print("Step 2: Querying practices needing enrichment...")
    print("-"*60)

    enrichment_query = notion.databases.query(
        database_id=database_id,
        filter={
            "and": [
                {"property": "Website", "url": {"is_not_empty": True}},
                {
                    "or": [
                        # Never enriched
                        {"property": "Enrichment Status", "select": {"does_not_equal": "Completed"}},
                        # Or enriched >30 days ago
                        {"property": "Last Enrichment Date", "date": {"before": thirty_days_ago}}
                    ]
                }
            ]
        }
    )

    needs_enrichment = len(enrichment_query["results"])
    print(f"✅ Found {needs_enrichment} practices needing enrichment")
    print()

    # Step 3: Categorize results
    print("Step 3: Categorizing results...")
    print("-"*60)

    def get_enrichment_status(page):
        """Extract enrichment status from page."""
        status_prop = page["properties"].get("Enrichment Status", {}).get("select")
        return status_prop["name"] if status_prop else None

    def get_enrichment_date(page):
        """Extract enrichment date from page."""
        date_prop = page["properties"].get("Last Enrichment Date", {}).get("date")
        return date_prop["start"] if date_prop else None

    never_enriched = []
    stale_enriched = []
    recently_enriched = []

    for page in enrichment_query["results"]:
        status = get_enrichment_status(page)
        date = get_enrichment_date(page)
        practice_name = page["properties"].get("Practice Name", {}).get("title", [{}])[0].get("plain_text", "Unknown")

        if status != "Completed":
            never_enriched.append((practice_name, status, date))
        elif date and datetime.fromisoformat(date.replace("Z", "+00:00")) < datetime.fromisoformat(thirty_days_ago):
            stale_enriched.append((practice_name, status, date))
        else:
            recently_enriched.append((practice_name, status, date))

    print(f"Never Enriched: {len(never_enriched)}")
    for name, status, date in never_enriched[:5]:  # Show first 5
        print(f"  - {name} (Status: {status})")
    if len(never_enriched) > 5:
        print(f"  ... and {len(never_enriched) - 5} more")
    print()

    print(f"Stale (>30 days): {len(stale_enriched)}")
    for name, status, date in stale_enriched[:5]:  # Show first 5
        print(f"  - {name} (Last: {date})")
    if len(stale_enriched) > 5:
        print(f"  ... and {len(stale_enriched) - 5} more")
    print()

    print(f"Recent (<30 days): {len(recently_enriched)}")
    for name, status, date in recently_enriched[:5]:  # Show first 5
        print(f"  - {name} (Last: {date})")
    if len(recently_enriched) > 5:
        print(f"  ... and {len(recently_enriched) - 5} more")
    print()

    # Step 4: Validate query excluded recent enrichments
    print("Step 4: Validating recently enriched practices excluded...")
    print("-"*60)

    # Query practices enriched recently (should be excluded from enrichment query)
    recent_query = notion.databases.query(
        database_id=database_id,
        filter={
            "and": [
                {"property": "Website", "url": {"is_not_empty": True}},
                {"property": "Enrichment Status", "select": {"equals": "Completed"}},
                {"property": "Last Enrichment Date", "date": {"on_or_after": thirty_days_ago}}
            ]
        }
    )

    excluded_count = len(recent_query["results"])
    print(f"✅ Practices enriched <30 days ago: {excluded_count}")

    # These should NOT be in enrichment_query results
    recent_page_ids = {p["id"] for p in recent_query["results"]}
    enrichment_page_ids = {p["id"] for p in enrichment_query["results"]}

    incorrectly_included = recent_page_ids & enrichment_page_ids

    if incorrectly_included:
        print(f"❌ {len(incorrectly_included)} recent practices incorrectly included in enrichment query")
    else:
        print(f"✅ No recent practices incorrectly included")
    print()

    # Summary
    print("="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total practices with websites: {total_with_websites}")
    print(f"Practices needing enrichment: {needs_enrichment}")
    print(f"  - Never enriched: {len(never_enriched)}")
    print(f"  - Stale (>30 days): {len(stale_enriched)}")
    print(f"  - Incorrectly included recent: {len(recently_enriched)}")
    print(f"Practices excluded (recent): {excluded_count}")
    print()

    print("SUCCESS CRITERIA VALIDATION:")
    print("-"*60)

    criteria = [
        ("Query returns practices needing enrichment", needs_enrichment > 0),
        ("Never enriched practices included", len(never_enriched) > 0 or total_with_websites == 0),
        ("No recent practices incorrectly included", len(incorrectly_included) == 0),
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
        print("   Re-enrichment query works correctly for FEAT-002.")
    else:
        print("\n❌ SOME CRITERIA FAILED")
        print("   Review failures above and adjust query filter.")

    print("="*60)

    return all_passed

if __name__ == "__main__":
    try:
        success = test_notion_requery()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
