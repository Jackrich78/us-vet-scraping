# Database Schema

**Last Updated:** 2025-11-03
**Status:** Active
**Database:** Notion API (Cloud-hosted)

## Overview

This system uses **Notion** as the database for storing and managing veterinary practice leads. Notion was chosen because the client already uses it for sales workflow, enabling seamless integration with existing processes.

**Database Name:** `Veterinary Lead Pipeline - Boston`
**Database ID:** `2a0edda2a9a081d98dc9daa43c65e744`
**Total Fields:** 48 fields across 7 categories
**Expected Records:** 100-150 practices (MVP), expandable to 500+ (multi-geography)

## Database Type

**Notion Database (via API)**
- **Version:** Notion API v1 (2022-06-28)
- **Access:** Via notion-client Python library (2.2.1)
- **Authentication:** Integration token (secret_xxxx...)
- **Rate Limits:** 3 requests/second
- **Hosting:** Notion cloud infrastructure

## Complete Field Specification

### 🔵 Core Data (From Google Maps Scraping - FEAT-001)

| Field Name | Notion Type | Python Type | Required | Notes |
|------------|-------------|-------------|----------|-------|
| **Practice Name** | `title` | `str` | ✅ Yes | Primary identifier (ONE title field per database) |
| **Address** | `rich_text` | `str` | ✅ Yes | Full street address |
| **City** | `rich_text` | `str` | ✅ Yes | For filtering/sorting (e.g., "Boston", "Cambridge") |
| **State** | `rich_text` | `str` | ✅ Yes | Default: "MA", supports multi-state expansion |
| **ZIP Code** | `rich_text` | `Optional[str]` | No | Extracted from address |
| **Phone** | `phone_number` | `str` | ✅ Yes | Format: +1-XXX-XXX-XXXX |
| **Website** | `url` | `Optional[HttpUrl]` | No | Practice website (validated URL) |
| **Google Maps URL** | `url` | `HttpUrl` | ✅ Yes | Link to Google listing |
| **Google Place ID** | `rich_text` | `str` | ✅ Yes | **Unique de-duplication key** (27 chars) |
| **Google Rating** | `number` | `Optional[float]` | No | 0-5 stars, 1 decimal (e.g., 4.3) |
| **Google Review Count** | `number` | `Optional[int]` | No | Total Google reviews |
| **Business Categories** | `multi_select` | `List[str]` | No | Pre-defined options required |

**Business Categories Options:**
- Veterinarian
- Animal Hospital
- Emergency Vet
- Pet Store
- Grooming

### 🟢 Enrichment Data (From Website Scraping - FEAT-002)

| Field Name | Notion Type | Python Type | Required | Notes |
|------------|-------------|-------------|----------|-------|
| **Confirmed Vet Count - Total** | `number` | `Optional[int]` | No | Total vets across all locations |
| **Confirmed Vet Count - Per Location** | `number` | `Optional[int]` | No | Average if multiple locations |
| **Practice Size Category** | `select` | `str` | ✅ Yes | Auto-calculated from vet count |
| **Has Emergency Services** | `checkbox` | `bool` | No | 24/7 or after-hours care |
| **Has Multiple Locations** | `checkbox` | `bool` | No | More than one office |
| **Has Online Booking** | `checkbox` | `bool` | No | Digital scheduling visible |
| **Technology Features** | `multi_select` | `List[str]` | No | Tech sophistication signals |
| **Services Offered** | `multi_select` | `List[str]` | No | Service offerings |
| **Operating Hours** | `rich_text` | `Optional[str]` | No | Business hours formatted |

**Practice Size Category Options:**
- `Solo` - 1 vet
- `Small (2-3)` - 2-3 vets
- `Sweet Spot (3-5)` - 3-5 vets ⭐ TARGET ICP
- `Large (6-9)` - 6-9 vets
- `Corporate (10+)` - 10+ vets
- `Unknown` - Not determined

**Technology Features Options:**
- Modern Website
- Live Chat
- Client Portal
- Mobile App
- Email Reminders
- SMS Reminders

**Services Offered Options:**
- General Practice
- Emergency
- Surgery
- Dental
- Exotic Animals
- Boarding
- Grooming
- House Calls

### 👥 Decision Maker Information (FEAT-002 + optional FEAT-004)

| Field Name | Notion Type | Python Type | Required | Notes |
|------------|-------------|-------------|----------|-------|
| **Owner/Manager Name** | `rich_text` | `Optional[str]` | No | e.g., "Dr. Sarah Johnson" |
| **Owner/Manager Title** | `select` | `Optional[str]` | No | Leadership role |
| **Owner/Manager Email** | `email` | `Optional[str]` | No | Found or guessed |
| **Email Status** | `select` | `Optional[str]` | No | Source and confidence |
| **Decision Maker Contact Quality** | `select` | `str` | ✅ Yes | Scoring indicator |
| **LinkedIn Profile URL** | `url` | `Optional[HttpUrl]` | No | If found via LinkedIn |

**Owner/Manager Title Options:**
- Owner
- Practice Manager
- Hospital Administrator
- Veterinarian Owner
- Unknown

**Email Status Options:**
- `Verified Found` - Found on website, verified
- `Pattern Guessed` - Intelligently guessed from pattern
- `LinkedIn Found` - Found via LinkedIn scraper
- `Not Found` - No email discovered

**Decision Maker Contact Quality Options:**
- `🏆 Complete` - Name + verified email (+20 pts)
- `⭐ Strong` - Name + guessed email (+15 pts)
- `👤 Partial` - Name only (+10 pts)
- `📞 Generic` - Generic info@/contact@ only (+0 pts)

### 🎯 Personalization Context (FEAT-002 - Critical for Cold Calling)

| Field Name | Notion Type | Python Type | Required | Notes |
|------------|-------------|-------------|----------|-------|
| **Personalization Context** | `rich_text` | `Optional[str]` | No | 2-3 unique conversation openers |

**Good Examples:**
- "Recently opened 2nd location in Newton (Oct 2024)"
- "Fear-free certified practice since 2022"
- "Dr. Johnson featured in Boston Magazine 2024 'Top Vets'"
- "Specializes in exotic birds - only one in Greater Boston"
- "Family-owned for 3 generations, 50th anniversary 2025"

**Bad Examples (too generic):**
- "Family-owned practice" ❌
- "Experienced staff" ❌
- "Provides excellent care" ❌

### 📈 Scoring & Prioritization (FEAT-003)

| Field Name | Notion Type | Python Type | Required | Notes |
|------------|-------------|-------------|----------|-------|
| **Lead Score** | `number` | `int` | ✅ Yes | 0-120 points total |
| **Priority Tier** | `select` | `str` | ✅ Yes | Call priority |
| **Score Breakdown** | `rich_text` | `Optional[str]` | No | Criteria explanation |
| **Out of Scope Reason** | `select` | `Optional[str]` | No | Disqualification reason |

**Priority Tier Options:**
- `🔥 Hot (80-120)` - Call immediately
- `🌡️ Warm (50-79)` - Call soon
- `❄️ Cold (0-49)` - Research/defer
- `⛔ Out of Scope` - Don't call

**Out of Scope Reason Options:**
- `Too Large (10+ vets)`
- `Solo Practice`
- `No Website`
- `Permanently Closed`
- `Other`

### 🎯 Sales Workflow (Manually Updated - PRESERVED on Updates)

| Field Name | Notion Type | Python Type | Required | Notes |
|------------|-------------|-------------|----------|-------|
| **Status** | `select` | `str` | ✅ Yes | Default: "New" |
| **Assigned To** | `people` | `Optional[str]` | No | Dan/Jack/Remco |
| **Research Notes** | `rich_text` | `Optional[str]` | No | Pre-call research |
| **Call Notes** | `rich_text` | `Optional[str]` | No | Conversation notes |
| **Next Action** | `rich_text` | `Optional[str]` | No | Follow-up task |
| **Next Follow-Up Date** | `date` | `Optional[date]` | No | Scheduled touch |
| **Last Contact Date** | `date` | `Optional[date]` | No | Most recent contact |
| **Outreach Attempts** | `number` | `int` | No | Default: 0 |

**Status Options:**
- `New` - Just scraped
- `Researching` - Under review
- `Contact Ready` - Ready for outreach
- `Contacted` - Initial outreach made
- `Qualified` - Confirmed ICP fit
- `Pitched` - Demo/proposal sent
- `Closed Won` - Customer acquired
- `Closed Lost` - Opportunity lost
- `Not a Fit` - Disqualified

**CRITICAL:** All sales workflow fields are **PRESERVED** during scraping updates to protect manual work.

### 🔧 Metadata (Tracking - Updated Each Run)

| Field Name | Notion Type | Python Type | Required | Notes |
|------------|-------------|-------------|----------|-------|
| **First Scraped Date** | `date` | `date` | ✅ Yes | Never updated after initial |
| **Last Scraped Date** | `date` | `date` | ✅ Yes | Updated every run |
| **Scrape Run ID** | `rich_text` | `str` | ✅ Yes | e.g., "BOS-2025-11-03-01" |
| **Data Sources** | `multi_select` | `List[str]` | ✅ Yes | Where data came from |
| **Times Scraped** | `number` | `int` | ✅ Yes | Incremented each run |
| **Data Completeness** | `select` | `Optional[str]` | No | Percentage populated |

**Data Sources Options:**
- `Google Maps`
- `Website`
- `LinkedIn`

**Data Completeness Options:**
- `High (80%+)`
- `Medium (50-79%)`
- `Low (<50%)`

## Python Type Mappings

### Notion Property Types → Python/Pydantic Types

| Notion Type | Python Type | Pydantic Annotation | Example |
|-------------|-------------|---------------------|---------|
| `title` | `str` | `Field(..., min_length=1)` | "Boston Vet Clinic" |
| `rich_text` | `str` | `Field(default="")` | "123 Main St" |
| `number` | `int` or `float` | `Field(ge=0, le=120)` | 85 |
| `select` | `str` | `Literal["Opt1", "Opt2"]` | "Hot" |
| `multi_select` | `List[str]` | `Field(default_factory=list)` | ["Emergency", "Surgery"] |
| `checkbox` | `bool` | `Field(default=False)` | True |
| `url` | `str` | `HttpUrl` (Pydantic) | "https://example.com" |
| `email` | `str` | `EmailStr` (Pydantic) | "owner@vet.com" |
| `phone_number` | `str` | `str` (custom validator) | "+1-617-555-0100" |
| `date` | `datetime.date` | `date` | "2025-11-03" |
| `people` | `str` | `Optional[str]` | UUID |

### Notion API Property Format Examples

**Title Field:**
```python
{
    "Practice Name": {
        "title": [{"text": {"content": "Boston Veterinary Clinic"}}]
    }
}
```

**Rich Text Field:**
```python
{
    "Address": {
        "rich_text": [{"text": {"content": "123 Main St, Boston, MA"}}]
    }
}
```

**Number Field:**
```python
{
    "Lead Score": {
        "number": 85
    }
}
```

**Select Field:**
```python
{
    "Priority Tier": {
        "select": {"name": "🔥 Hot (80-120)"}
    }
}
```

**Multi-Select Field:**
```python
{
    "Services Offered": {
        "multi_select": [
            {"name": "Emergency"},
            {"name": "Surgery"},
            {"name": "Dental"}
        ]
    }
}
```

**Checkbox Field:**
```python
{
    "Has Emergency Services": {
        "checkbox": True
    }
}
```

**URL Field:**
```python
{
    "Website": {
        "url": "https://bostonvetclinic.com"
    }
}
```

**Email Field:**
```python
{
    "Owner/Manager Email": {
        "email": "owner@bostonvetclinic.com"
    }
}
```

**Date Field:**
```python
{
    "First Scraped Date": {
        "date": {"start": "2025-11-03"}
    }
}
```

## De-Duplication Logic

### Primary Key: Google Place ID

**Why Place ID?**
- Guaranteed unique per Google Maps location
- Stable across scraping runs (never changes)
- Format: 27-character alphanumeric (e.g., `ChIJN1t_tDeuEmsRUsoyG83frY4`)

### Query-Before-Upsert Pattern

```python
def find_existing_by_place_id(place_id: str) -> Optional[Dict]:
    """Query Notion for existing record."""
    response = notion.databases.query(
        database_id=DATABASE_ID,
        filter={
            "property": "Google Place ID",
            "rich_text": {"equals": place_id}
        }
    )
    return response["results"][0] if response["results"] else None

def upsert_practice(practice_data: Dict) -> str:
    """Create or update practice. Returns 'CREATED' or 'UPDATED'."""
    place_id = practice_data["google_place_id"]
    existing = find_existing_by_place_id(place_id)

    if existing:
        # UPDATE: Merge new data, preserve sales fields
        update_props = build_update_properties(practice_data, existing)
        notion.pages.update(page_id=existing["id"], properties=update_props)
        return "UPDATED"
    else:
        # CREATE: New record
        create_props = build_create_properties(practice_data)
        notion.pages.create(
            parent={"database_id": DATABASE_ID},
            properties=create_props
        )
        return "CREATED"
```

### Fields PRESERVED on Update

**Sales Workflow Fields (NEVER overwritten):**
- Status
- Assigned To
- Research Notes
- Call Notes
- Next Action
- Next Follow-Up Date
- Last Contact Date
- Outreach Attempts

**Metadata Fields (Conditionally updated):**
- First Scraped Date (never changed)
- Last Scraped Date (always updated to today)
- Times Scraped (incremented)

### Multi-Key Fallback Strategy

If Place ID missing (rare edge case):

```python
# Fallback 1: Normalized Website URL
if website:
    normalized_url = website.lower().replace("https://", "").replace("www.", "").rstrip("/")
    query_by_website(normalized_url)

# Fallback 2: Normalized Phone
elif phone:
    digits_only = ''.join(c for c in phone if c.isdigit())
    query_by_phone(digits_only)

# Fallback 3: Name + Address
else:
    query_by_name_and_address(name.lower(), address.lower())
```

## Batch Operations

### Rate Limiting Strategy

**Constraint:** 3 requests/second (Notion API limit)

**Strategy:**
- Batch size: 10 records
- Delay between requests: 0.35 seconds (2.86 req/s, under limit)
- Delay between batches: 1.0 seconds (safety buffer)

**Timing for 150 Records:**
```
Query existing Place IDs: ~1 second (paginated query)
Process 150 records: 150 × 0.35s = 52.5 seconds
Total: ~54 seconds (~1 minute)
```

### Batch Upsert Implementation

```python
import time
from typing import List, Dict

def batch_upsert_practices(
    practices: List[Dict],
    batch_size: int = 10
) -> Dict[str, int]:
    """Upsert practices with rate limiting."""
    results = {"created": 0, "updated": 0, "failed": 0}

    for i in range(0, len(practices), batch_size):
        batch = practices[i:i+batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}: {len(batch)} practices")

        for practice in batch:
            try:
                result = upsert_practice(practice)
                results[result.lower()] += 1
                time.sleep(0.35)  # Rate limit
            except Exception as e:
                logger.error(f"Failed: {practice['practice_name']}: {e}")
                results["failed"] += 1

        # Safety pause between batches
        if i + batch_size < len(practices):
            time.sleep(1.0)

    return results
```

## Query Patterns

### Query All Practices (with Pagination)

```python
def query_all_practices() -> List[Dict]:
    """Query all practices, handling pagination."""
    all_results = []
    has_more = True
    start_cursor = None

    while has_more:
        response = notion.databases.query(
            database_id=DATABASE_ID,
            start_cursor=start_cursor,
            page_size=100  # Max allowed
        )

        all_results.extend(response["results"])
        has_more = response["has_more"]
        start_cursor = response.get("next_cursor")

        time.sleep(0.35)  # Rate limit

    return all_results
```

### Filter by Practice Size (Sweet Spot)

```python
def query_sweet_spot_practices() -> List[Dict]:
    """Query 3-5 vet practices (ICP)."""
    response = notion.databases.query(
        database_id=DATABASE_ID,
        filter={
            "property": "Practice Size Category",
            "select": {"equals": "Sweet Spot (3-5)"}
        },
        sorts=[
            {"property": "Lead Score", "direction": "descending"}
        ]
    )
    return response["results"]
```

### Filter by Priority + Status

```python
def query_hot_leads_ready_for_outreach() -> List[Dict]:
    """Query hot leads ready to call."""
    response = notion.databases.query(
        database_id=DATABASE_ID,
        filter={
            "and": [
                {
                    "property": "Priority Tier",
                    "select": {"equals": "🔥 Hot (80-120)"}
                },
                {
                    "property": "Status",
                    "select": {"equals": "Contact Ready"}
                }
            ]
        },
        sorts=[
            {"property": "Lead Score", "direction": "descending"}
        ]
    )
    return response["results"]
```

## Data Validation

### Required Field Validation

```python
from pydantic import BaseModel, Field, HttpUrl, validator

class VeterinaryPractice(BaseModel):
    """Validate practice data before Notion push."""

    # Required fields
    practice_name: str = Field(..., min_length=1)
    address: str = Field(..., min_length=5)
    city: str = Field(..., min_length=2)
    state: str = Field(..., min_length=2, max_length=2)
    phone: str = Field(..., pattern=r'^\+?1?\d{10,11}$')
    google_maps_url: HttpUrl
    google_place_id: str = Field(..., min_length=27, max_length=27)

    # Optional fields
    zip_code: Optional[str] = Field(None, pattern=r'^\d{5}(-\d{4})?$')
    website: Optional[HttpUrl] = None
    google_rating: Optional[float] = Field(None, ge=0.0, le=5.0)
    google_review_count: Optional[int] = Field(None, ge=0)

    @validator("google_place_id")
    def validate_place_id_format(cls, v):
        """Ensure Place ID is alphanumeric."""
        if not v.isalnum():
            raise ValueError("Place ID must be alphanumeric")
        return v
```

### Data Completeness Calculation

```python
def calculate_data_completeness(practice: Dict) -> str:
    """Calculate completeness percentage."""
    total_fields = 48
    non_null_fields = sum(
        1 for v in practice.values()
        if v is not None and v != "" and v != []
    )

    percentage = (non_null_fields / total_fields) * 100

    if percentage >= 80:
        return "High (80%+)"
    elif percentage >= 50:
        return "Medium (50-79%)"
    else:
        return "Low (<50%)"
```

## Common Pitfalls & Solutions

### Pitfall 1: Multi-Select Options Not Pre-Defined

**Problem:** 400 error if option doesn't exist.

**Solution:** Pre-create ALL options during database setup. Cannot dynamically add via API.

### Pitfall 2: Empty Rich Text

**Problem:** `{"rich_text": ""}` causes error.

**Solution:** Use `{"rich_text": []}` for empty:

```python
def format_rich_text(text: Optional[str]) -> Dict:
    if not text:
        return {"rich_text": []}
    return {"rich_text": [{"text": {"content": text}}]}
```

### Pitfall 3: Date Format

**Problem:** Notion expects ISO 8601 strings.

**Solution:** Use `.isoformat()`:

```python
from datetime import date
{"date": {"start": date.today().isoformat()}}  # "2025-11-03"
```

### Pitfall 4: Rate Limit Violations

**Problem:** 429 errors exceeding 3 req/s.

**Solution:** `time.sleep(0.35)` between ALL API calls.

### Pitfall 5: Title Field Confusion

**Problem:** Multiple title fields cause errors.

**Solution:** Only ONE title field per database (Practice Name). All others are `rich_text`.

## Performance Characteristics

### Query Performance
- Single query by Place ID: ~350ms
- Batch query (100 records): ~500ms per page
- Full scan (150 records): ~1 second

### Write Performance
- Single create: ~350ms
- Single update: ~350ms
- Batch 150 records: ~54 seconds

### Optimization Tips
1. Cache Place IDs in memory during batch ops
2. Use pagination efficiently (100 per page)
3. Batch 10 records with 1s pause
4. Only update changed fields

---

**See Also:**
- [architecture.md](architecture.md) - NotionClient implementation
- [integrations.md](integrations.md) - Notion API configuration
- [stack.md](stack.md) - notion-client version
- [configuration.md](configuration.md) - API credentials
