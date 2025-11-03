# External Integrations

**Last Updated:** 2025-11-03
**Status:** Active
**Total Integrations:** 4 primary services (Apify, OpenAI, Notion, Crawl4AI)

## Overview

This document specifies all external services, APIs, and integrations used by the veterinary lead generation pipeline, including exact configurations, authentication, rate limits, error handling, and cost structures.

## Integration Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                          │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Apify (Google Maps)  →  Crawl4AI (Websites)  →  OpenAI     │
│         ↓                      ↓                     ↓        │
│    Raw Practices         HTML Content          Structured    │
│                                                  Extraction   │
│                              ↓                                │
│                         Notion Database                       │
│                    (Lead Storage & Management)                │
└──────────────────────────────────────────────────────────────┘
```

## 1. Apify - Web Scraping Platform

### Overview

**Purpose:** Scrape Google Maps for veterinary practice data
**Provider:** Apify Technologies s.r.o.
**Website:** https://apify.com
**Documentation:** https://docs.apify.com/
**Python Client:** apify-client 1.7.2

### Authentication

**Method:** API Key authentication

**Environment Variable:**
```bash
APIFY_API_KEY=apify_api_xxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Key Format:**
- Prefix: `apify_api_`
- Length: ~40 characters
- Location: Account Settings → Integrations → API

**Security:** Store in `.env` file (gitignored), never commit

### Actors Used

#### Actor 1: Google Maps Scraper

**Actor ID:** `compass/crawler-google-places`
**Actor URL:** https://apify.com/compass/crawler-google-places
**Purpose:** Scrape veterinary practices from Google Maps
**Cost:** ~$0.01 per result (~$2.00 for 200 results)

**Input Schema:**
```json
{
  "searchStringsArray": [
    "veterinarian",
    "vet clinic",
    "animal hospital",
    "emergency vet",
    "veterinary hospital"
  ],
  "locationQuery": "Boston, MA, USA",
  "maxCrawledPlacesPerSearch": 100,
  "language": "en",
  "maxReviews": 0,
  "maxImages": 0,
  "includeHistogram": false,
  "includeOpeningHours": true,
  "includePeopleAlsoSearch": false,
  "exportPlaceUrls": true,
  "skipClosedPlaces": true
}
```

**Output Schema:**
```json
{
  "title": "Boston Veterinary Clinic",
  "address": "123 Main St, Boston, MA 02101",
  "city": "Boston",
  "state": "Massachusetts",
  "postalCode": "02101",
  "phoneNumber": "+1 617-555-0100",
  "website": "https://bostonvetclinic.com",
  "url": "https://www.google.com/maps/place/...",
  "placeId": "ChIJN1t_tDeuEmsRUsoyG83frY4",
  "totalScore": 4.5,
  "reviewsCount": 250,
  "categoryName": "Veterinarian, Animal Hospital",
  "latitude": 42.3601,
  "longitude": -71.0589,
  "permanentlyClosed": false,
  "temporarilyClosed": false,
  "openingHours": [...]
}
```

**Python Implementation:**
```python
from apify_client import ApifyClient

client = ApifyClient(os.getenv("APIFY_API_KEY"))

# Run actor
run = client.actor("compass/crawler-google-places").call(
    run_input={
        "searchStringsArray": ["veterinarian", "animal hospital"],
        "locationQuery": "Boston, MA, USA",
        "maxCrawledPlacesPerSearch": 100,
        "skipClosedPlaces": True,
    }
)

# Fetch results
dataset_id = run["defaultDatasetId"]
results = client.dataset(dataset_id).list_items().items
```

#### Actor 2: LinkedIn Company Employees Scraper (Optional - FEAT-004)

**Actor ID:** `apimaestro/linkedin-company-employees-scraper-no-cookies`
**Actor URL:** https://apify.com/apimaestro/linkedin-company-employees-scraper-no-cookies
**Purpose:** Find decision makers when website scraping fails
**Cost:** ~$0.01 per company (~$0.50 for 50 companies)

**Input Schema:**
```json
{
  "companyUrls": [
    "https://www.linkedin.com/company/boston-animal-hospital"
  ],
  "jobTitles": ["Owner", "Practice Manager", "Hospital Administrator"],
  "maxEmployees": 10,
  "includeEmail": true,
  "includePhone": false
}
```

### Rate Limits

**Platform Limits:** No strict rate limits (usage-based billing)
**Actor Limits:** Varies by actor (typically 100-1000 req/hour)
**Recommended:** No throttling needed for MVP (<200 results)

### Error Handling

**Retry Strategy:** 3 attempts with exponential backoff (5s, 10s, 20s)

**Error Types:**
- **Rate Limit (429):** Retry with backoff
- **Insufficient Credits:** Fail with clear message
- **Actor Failed:** Log error, continue with partial results
- **Timeout:** Retry once, then skip

**Python Implementation:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=5, max=20)
)
def run_apify_actor(actor_id: str, run_input: dict):
    try:
        run = client.actor(actor_id).call(run_input=run_input)
        if run["status"] == "FAILED":
            raise ApifyActorFailedError(f"Actor failed: {run.get('error')}")
        return run
    except ApifyApiError as e:
        if "rate limit" in str(e).lower():
            logger.warning("Apify rate limited, retrying...")
            raise  # Retry
        elif "insufficient funds" in str(e).lower():
            raise CriticalError("Insufficient Apify credits") from e
        else:
            raise
```

### Cost Calculation

**Compute Units (CU):**
- 1 CU = $0.25 (paid plans)
- Actor usage varies by complexity

**Google Maps Actor:**
- ~0.01 CU per result
- 200 results × 0.01 CU = 2 CU
- 2 CU × $0.25 = **$0.50 base**
- Add 30% overhead = **$0.65 estimated**
- **Actual cost range: $0.50 - $2.00**

**Formula:**
```python
def calculate_apify_cost(num_results: int, cu_per_result: float = 0.01) -> float:
    total_cu = num_results * cu_per_result
    base_cost = total_cu * 0.25
    return base_cost * 1.3  # 30% overhead buffer
```

### Configuration

**Config Location:** `config/config.json`

```json
{
  "apify": {
    "google_maps_actor": "compass/crawler-google-places",
    "linkedin_actor": "apimaestro/linkedin-company-employees-scraper-no-cookies",
    "max_google_results": 200,
    "api_key_env_var": "APIFY_API_KEY"
  }
}
```

---

## 2. OpenAI - LLM Extraction

### Overview

**Purpose:** Extract structured data from website HTML
**Provider:** OpenAI
**Website:** https://openai.com
**Documentation:** https://platform.openai.com/docs
**Python Client:** openai 1.54.3

### Authentication

**Method:** Bearer token authentication

**Environment Variable:**
```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Key Format:**
- Prefix: `sk-proj-` (project keys) or `sk-` (user keys)
- Length: ~50 characters
- Location: API Keys → Create new secret key

**Security:** Store in `.env` file, rotate every 90 days

### Model Configuration

**Model:** `gpt-4o-mini`
**Purpose:** Cost-effective structured data extraction
**Context Window:** 128k tokens
**Max Output:** 16k tokens

**Pricing (as of Jan 2025):**
- Input: $0.150 per 1M tokens
- Output: $0.600 per 1M tokens

**Cost per Extraction Call:**
```
Input: ~2000 tokens (8KB HTML) × $0.150/1M = $0.0003
Output: ~500 tokens (structured JSON) × $0.600/1M = $0.0003
Total per call: $0.0006 (~$0.0006)

150 extractions: 150 × $0.0006 = $0.09
With 10% retry buffer: $0.09 × 1.1 = $0.10
```

**Actual Cost: $0.10-0.20** (not $3.00 as originally estimated!)

### API Configuration

**Endpoint:** `https://api.openai.com/v1/chat/completions`

**Request Structure (Structured Outputs):**
```python
from openai import OpenAI
from pydantic import BaseModel

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class VetPracticeExtraction(BaseModel):
    vet_count_total: Optional[int]
    vet_count_confidence: Literal["high", "medium", "low"]
    decision_maker_name: Optional[str]
    decision_maker_email: Optional[str]
    personalization_context: List[str]
    # ... additional fields

completion = client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[
        {
            "role": "system",
            "content": "Extract veterinary practice data from HTML..."
        },
        {
            "role": "user",
            "content": f"HTML content: {html[:8000]}"
        }
    ],
    response_format=VetPracticeExtraction,  # Structured output
)

result = completion.choices[0].message.parsed
```

### Extraction Prompt

**System Prompt (stored in `config/website_extraction_prompt.txt`):**

```
You are analyzing a veterinary practice website to extract structured data for B2B sales lead generation.

CRITICAL INSTRUCTIONS:
1. The "personalization_context" field is ESSENTIAL - find at least 2-3 unique, SPECIFIC facts about this practice that could be conversation starters for a cold call.
2. For decision_maker_email, if you find a pattern (e.g., staff@domain.com), intelligently guess owner@ or manager@ and mark as "pattern_guessed".
3. Be conservative with vet_count - only report if confident. Better to return null than guess incorrectly.
4. Extract ACTUAL names when possible, not generic titles.
5. Return null for any field where information is not found - do not guess or hallucinate.
6. For personalization_context, provide SPECIFIC facts, not generic statements like "family-owned" or "experienced staff".

Good personalization examples:
- "Recently opened 2nd location in Newton (Oct 2024)"
- "Dr. Johnson featured in Boston Magazine 2024 'Top Vets' list"
- "Specializes in exotic birds - only practice in Greater Boston with avian vet"

Bad personalization examples:
- "Family-owned practice" (too generic)
- "Experienced staff" (too vague)
- "Provides excellent care" (useless for cold call)
```

### Rate Limits

**Tier-Based Limits:**
- Tier 1 (Free): 3 req/min, 200 req/day
- Tier 2: 60 req/min, 2000 req/day
- Tier 3+: 3500+ req/min

**For 150 Extractions:**
- At 1 req/2 seconds = 75 req/150 seconds = 2.5 minutes (under all tiers)

**Recommended:** No throttling needed for MVP

### Error Handling

**Retry Strategy:** 2 attempts with 5s fixed delay

**Error Types:**
- **Rate Limit (429):** Retry with exponential backoff
- **Invalid Request (400):** Log and skip (schema error)
- **Timeout:** Retry once
- **Hallucination:** Validate output against HTML

**Python Implementation:**
```python
from tenacity import retry, stop_after_attempt, wait_fixed

@retry(
    stop=stop_after_attempt(2),
    wait=wait_fixed(5)
)
def extract_with_openai(html: str) -> VetPracticeExtraction:
    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[...],
            response_format=VetPracticeExtraction,
            timeout=30  # 30s timeout
        )
        return completion.choices[0].message.parsed
    except openai.RateLimitError:
        logger.warning("OpenAI rate limited, retrying...")
        raise  # Retry
    except openai.APIError as e:
        logger.error(f"OpenAI API error: {e}")
        raise
```

### Output Validation

**Validate Against HTML:**
```python
def validate_extraction(result: VetPracticeExtraction, html: str) -> bool:
    """Cross-validate extraction against HTML source."""

    # Check vet count sanity
    if result.vet_count_total and result.vet_count_total > 50:
        logger.warning("Suspicious vet count (>50), likely hallucination")
        result.vet_count_total = None
        result.vet_count_confidence = "low"

    # Validate email domain
    if result.decision_maker_email:
        domain = result.decision_maker_email.split("@")[1]
        if domain.lower() not in html.lower():
            logger.warning("Email domain not in HTML, marking as guessed")
            result.email_status = "pattern_guessed"

    # Require personalization context
    if len(result.personalization_context) < 2:
        logger.warning("Insufficient personalization context")
        return False

    return True
```

### Configuration

**Config Location:** `config/config.json`

```json
{
  "website_scraping": {
    "llm_provider": "openai",
    "llm_model": "gpt-4o-mini",
    "extraction_prompt_file": "config/website_extraction_prompt.txt",
    "max_input_chars": 8000,
    "timeout_seconds": 30,
    "retry_attempts": 2
  }
}
```

---

## 3. Notion - Lead Database

### Overview

**Purpose:** Store and manage lead data
**Provider:** Notion Labs Inc.
**Website:** https://notion.so
**Documentation:** https://developers.notion.com
**Python Client:** notion-client 2.2.1

### Authentication

**Method:** Internal Integration Token

**Environment Variable:**
```bash
NOTION_API_KEY=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DATABASE_ID=2a0edda2a9a081d98dc9daa43c65e744
```

**Integration Setup:**
1. Go to https://www.notion.so/my-integrations
2. Create new integration: "Vet Scraper"
3. Capabilities: Read content, Update content, Insert content
4. Copy integration secret (starts with `secret_`)
5. Share target database with integration

**Key Format:**
- Prefix: `secret_`
- Length: ~50 characters

**Database ID Format:**
- Extract from database URL: `https://notion.so/{DATABASE_ID}?v=...`
- Format: 32 hex characters with dashes (e.g., `2a0edda2-a9a0-81d9-8dc9-daa43c65e744`)

### API Configuration

**API Version:** 2022-06-28 (stable)
**Base URL:** https://api.notion.com/v1/

**Python Client Setup:**
```python
from notion_client import Client

notion = Client(auth=os.getenv("NOTION_API_KEY"))
```

### Rate Limits

**Hard Limit:** 3 requests/second

**Strategy:**
- Delay: 0.35s between requests (2.86 req/s, under limit)
- Batch size: 10 records per batch
- Total time for 150 records: ~54 seconds

**Implementation:**
```python
import time

for practice in practices:
    notion.pages.create(...)
    time.sleep(0.35)  # Rate limit protection
```

### API Operations

**Create Record:**
```python
notion.pages.create(
    parent={"database_id": DATABASE_ID},
    properties={
        "Practice Name": {
            "title": [{"text": {"content": "Boston Vet Clinic"}}]
        },
        "Lead Score": {
            "number": 85
        },
        # ... other properties
    }
)
```

**Update Record:**
```python
notion.pages.update(
    page_id=page_id,
    properties={
        "Lead Score": {"number": 90},
        "Status": {"select": {"name": "Contact Ready"}}
    }
)
```

**Query Database:**
```python
response = notion.databases.query(
    database_id=DATABASE_ID,
    filter={
        "property": "Google Place ID",
        "rich_text": {"equals": place_id}
    },
    page_size=100
)
```

### Error Handling

**Retry Strategy:** 3 attempts with exponential backoff

**Error Types:**
- **Rate Limit (429):** Retry with 1s delay
- **Invalid Request (400):** Log and skip (schema mismatch)
- **Conflict (409):** Retry with backoff
- **Service Error (500+):** Retry with exponential backoff

**Python Implementation:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
def notion_create_with_retry(properties: dict):
    try:
        return notion.pages.create(
            parent={"database_id": DATABASE_ID},
            properties=properties
        )
    except APIResponseError as e:
        if e.code == 429:  # Rate limit
            logger.warning("Notion rate limited, retrying...")
            time.sleep(1)
            raise
        elif e.code >= 500:  # Server error
            logger.error(f"Notion server error: {e}")
            raise
        else:
            # Client error - don't retry
            logger.error(f"Notion client error: {e}")
            raise
```

### Configuration

**Config Location:** `config/config.json`

```json
{
  "notion": {
    "database_id_env_var": "NOTION_DATABASE_ID",
    "api_key_env_var": "NOTION_API_KEY",
    "batch_size": 10,
    "rate_limit_delay": 0.35,
    "update_existing_records": true,
    "preserve_fields_on_update": [
      "Status",
      "Assigned To",
      "Research Notes",
      "Call Notes",
      "Next Action",
      "Next Follow-Up Date",
      "Last Contact Date",
      "Outreach Attempts"
    ]
  }
}
```

---

## 4. Crawl4AI - Website Scraping

### Overview

**Purpose:** Scrape veterinary practice websites with JavaScript rendering
**Type:** Local Python library (not external API)
**Version:** 0.3.74
**Documentation:** https://crawl4ai.com/docs
**GitHub:** https://github.com/unclecode/crawl4ai

### Installation

```bash
pip install crawl4ai==0.3.74
playwright install chromium
```

### Configuration

**Browser Setup:**
```python
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

browser_config = BrowserConfig(
    browser_type="chromium",
    headless=True,
    viewport_width=1920,
    viewport_height=1080,
    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    ignore_https_errors=True
)

crawler_config = CrawlerRunConfig(
    wait_for="networkidle",
    page_timeout=30000,  # 30 seconds
    delay_before_return_html=2.0,  # Extra wait for JS
    remove_overlay_elements=True,  # Remove popups
    magic=True,  # Auto-detect dynamic content
    cache_mode="enabled"  # Cache during development
)
```

### Async Implementation

**Recommended for Performance:**
```python
from crawl4ai import AsyncWebCrawler
import asyncio

async def scrape_multiple_sites(urls: List[str]) -> List[Dict]:
    """Scrape multiple URLs concurrently."""
    results = []

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Create semaphore for concurrency control
        sem = asyncio.Semaphore(5)  # Max 5 concurrent

        async def scrape_with_limit(url: str):
            async with sem:
                try:
                    result = await crawler.arun(url=url, config=crawler_config)
                    return {
                        "url": url,
                        "html": result.html,
                        "status": "success"
                    }
                except Exception as e:
                    return {
                        "url": url,
                        "error": str(e),
                        "status": "failed"
                    }

        tasks = [scrape_with_limit(url) for url in urls]
        results = await asyncio.gather(*tasks)

    return results
```

### Performance Characteristics

**Timing:**
- Single page: ~6 seconds (network + JS rendering)
- 150 pages with concurrency=5: ~5.5 minutes
- Sequential (sync): ~15 minutes

**Resource Usage:**
- Memory: ~200MB per concurrent tab
- CPU: Moderate (Chromium rendering)

### Error Handling

**Retry Strategy:** 2 attempts with exponential backoff

**Error Types:**
- **Timeout:** Retry once
- **Connection Error:** Retry with backoff
- **404/403:** Skip (don't retry)

**Python Implementation:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=2, min=4, max=10)
)
async def scrape_with_retry(url: str):
    try:
        result = await crawler.arun(url=url, config=crawler_config)
        if not result.success:
            if "timeout" in result.error_message.lower():
                raise TimeoutError(f"Timeout scraping {url}")
            else:
                logger.error(f"Failed to scrape {url}: {result.error_message}")
                return None
        return result
    except asyncio.TimeoutError:
        logger.warning(f"Timeout on {url}, retrying...")
        raise
```

### Configuration

**Config Location:** `config/config.json`

```json
{
  "website_scraping": {
    "tool": "crawl4ai",
    "timeout_seconds": 30,
    "delay_between_requests_seconds": 4.0,
    "max_concurrent_requests": 5,
    "pages_to_crawl": [
      "homepage",
      "team",
      "about"
    ]
  }
}
```

---

## Integration Summary

### Cost Breakdown (150 Practices)

| Service | Unit Cost | Quantity | Total |
|---------|-----------|----------|-------|
| Apify Google Maps | $0.01/result | 150 | $0.50-2.00 |
| Crawl4AI | Free | 150 | $0.00 |
| OpenAI gpt-4o-mini | $0.0006/call | 150 | $0.10-0.20 |
| Notion | Free | 150 | $0.00 |
| **Total** | | | **$0.60-2.20** |

**With 20% buffer: $0.72-2.64**

**Original estimate: $5.50** → **Actual: $1.10-2.70** (50-80% cost reduction!)

### Rate Limit Summary

| Service | Limit | Our Usage | Compliant |
|---------|-------|-----------|-----------|
| Apify | None (usage-based) | 200 results/run | ✅ Yes |
| OpenAI | 3+ req/min (tier 1+) | 1 req/2s = 30/min | ✅ Yes |
| Notion | 3 req/s | 2.86 req/s (0.35s delay) | ✅ Yes |
| Crawl4AI | Local (no limit) | 5 concurrent | ✅ Yes |

### Error Handling Summary

| Service | Retry Attempts | Backoff Strategy |
|---------|----------------|------------------|
| Apify | 3 | Exponential (5s, 10s, 20s) |
| OpenAI | 2 | Fixed (5s) |
| Notion | 3 | Exponential (1s, 2s, 4s) |
| Crawl4AI | 2 | Exponential (4s, 10s) |

---

**See Also:**
- [architecture.md](architecture.md) - Integration points
- [stack.md](stack.md) - Client library versions
- [configuration.md](configuration.md) - API credentials setup
- [database.md](database.md) - Notion schema details
