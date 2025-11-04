#!/usr/bin/env python3
"""
Helper script to list practices from Notion database.

Usage:
    python3 list_notion_practices.py [--limit 20]

This will show you Notion page IDs that you can use with score_leads.py
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
    import argparse
    parser = argparse.ArgumentParser(description='List practices from Notion database')
    parser.add_argument('--limit', type=int, default=20, help='Number of practices to list')
    args = parser.parse_args()

    # Get credentials
    api_key = os.getenv("NOTION_API_KEY")
    database_id = os.getenv("NOTION_DATABASE_ID")

    if not api_key or not database_id:
        print("❌ Error: NOTION_API_KEY and NOTION_DATABASE_ID must be set in .env file")
        sys.exit(1)

    print(f"Connecting to Notion database {database_id[:8]}...")
    client = Client(auth=api_key)

    # Query database
    try:
        response = client.databases.query(
            database_id=database_id,
            page_size=min(args.limit, 100)
        )

        practices = response.get("results", [])

        if not practices:
            print("\n⚠️  No practices found in database")
            print("   Run the Google Maps scraper first: python main.py --test")
            return

        print(f"\nFound {len(practices)} practices:\n")
        print("=" * 100)

        for i, page in enumerate(practices, 1):
            props = page["properties"]
            page_id = page["id"]

            # Extract fields
            name = "Unknown"
            if "Name" in props:
                title = props["Name"].get("title", [])
                if title:
                    name = title[0].get("plain_text", "Unknown")

            website = "No website"
            if "Website" in props:
                url = props["Website"].get("url")
                if url:
                    website = url

            vet_count = "?"
            if "Vet Count" in props:
                count = props["Vet Count"].get("number")
                if count is not None:
                    vet_count = str(count)

            rating = "?"
            if "Rating" in props:
                r = props["Rating"].get("number")
                if r is not None:
                    rating = f"{r:.1f}"

            reviews = "?"
            if "Review Count" in props:
                rv = props["Review Count"].get("number")
                if rv is not None:
                    reviews = str(rv)

            lead_score = "Not scored"
            if "Lead Score" in props:
                ls = props["Lead Score"].get("number")
                if ls is not None:
                    lead_score = f"{ls}/120"

            enrichment_status = "?"
            if "Enrichment Status" in props:
                status = props["Enrichment Status"].get("select")
                if status:
                    enrichment_status = status.get("name", "?")

            print(f"{i}. {name}")
            print(f"   Page ID: {page_id}")
            print(f"   Vets: {vet_count} | Rating: {rating}★ | Reviews: {reviews}")
            print(f"   Enrichment: {enrichment_status} | Lead Score: {lead_score}")
            print(f"   Website: {website}")
            print()

        print("=" * 100)
        print(f"\nTo score a practice, use:")
        print(f"  python3 score_leads.py --practice-id <PAGE_ID>")
        print(f"\nExample:")
        if practices:
            first_id = practices[0]["id"]
            print(f"  python3 score_leads.py --practice-id {first_id}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
