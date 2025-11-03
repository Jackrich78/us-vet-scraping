# Product Requirements Document: Google Maps Scraping & Notion Integration

**Feature ID:** FEAT-001
**Feature Name:** Google Maps Scraping & Notion Push
**Priority:** P0 (Critical - Core data collection)
**Status:** Planning
**Owner:** Development Team
**Created:** 2025-11-03

## Executive Summary

Scrape veterinary practices from Google Maps using the Apify `compass/crawler-google-places` actor, apply hard filters (has website, 10+ reviews, open), calculate initial lead scores based on review metrics, and push de-duplicated results to Notion database. This is the primary data ingestion pipeline.

**Success Metric:** 150 qualifying MA veterinary practices in Notion database within 8 minutes.

## Problem Statement

Without automated Google Maps scraping:
- Manual research takes 20+ hours for 150 practices
- Inconsistent data quality (missing fields, typos)
- No systematic de-duplication (duplicate entries)
- No initial qualification (unfit practices included)
- No batch processing (API rate limits exceeded)

## Goals & Non-Goals

### Goals
✅ Scrape 150 MA veterinary practices from Google Maps via Apify
✅ Apply hard filters: has website, 10+ reviews, not permanently closed
✅ Calculate initial score (0-25 points) based on review count + rating
✅ De-duplicate by Google Place ID before pushing to Notion
✅ Batch upsert to Notion (10 records per batch, 0.35s delay)
✅ Test mode support (--test flag limits to 10 practices)
✅ Comprehensive error tracking and retry logic

### Non-Goals
❌ Website scraping (FEAT-002)
❌ LLM extraction (FEAT-002)
❌ Full ICP fit scoring (FEAT-003 - only baseline scoring here)
❌ LinkedIn enrichment (Phase 2)
❌ Email validation
❌ Decision maker identification

## User Stories

**As a sales team**, I need a pre-qualified list of veterinary practices so I can focus outreach on high-potential leads.

**As a developer**, I need de-duplication so re-running the pipeline doesn't create duplicate Notion records.

**As a developer**, I need test mode so I can validate the pipeline without incurring full Apify costs.

**As a business owner**, I need error tracking so I know which practices failed to scrape and why.

## Technical Specification

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ FEAT-001: Google Maps Scraping & Notion Push               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. ApifyClient.run_google_maps_scraper()                  │
│     ├─ Input: Search terms, location, max results          │
│     ├─ Actor: compass/crawler-google-places                │
│     └─ Output: List[ApifyGoogleMapsResult]                 │
│                                                             │
│  2. DataFilter.apply_hard_filters()                        │
│     ├─ Has website URL                                     │
│     ├─ ≥10 Google reviews                                  │
│     └─ Not permanently closed                              │
│                                                             │
│  3. InitialScorer.calculate_baseline_score()               │
│     ├─ Review count score (0-15 pts)                       │
│     └─ Review rating score (0-10 pts)                      │
│                                                             │
│  4. NotionClient.batch_upsert()                            │
│     ├─ De-duplicate by Place ID                            │
│     ├─ Create or update records                            │
│     └─ Batch 10 records, 0.35s delay                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Component Details

#### 1. Apify Google Maps Scraper (apify_client.py)

**Purpose:** Wrapper around Apify API to run `compass/crawler-google-places` actor

**Key Methods:**
```python
class ApifyClient:
    def run_google_maps_scraper(
        self,
        search_terms: List[str],
        location: str,
        max_results: int,
        test_mode: bool = False
    ) -> List[ApifyGoogleMapsResult]:
        """
        Run Apify Google Maps scraper and return parsed results.

        Args:
            search_terms: List of search queries (e.g., ["veterinary clinic", "animal hospital"])
            location: Location filter (e.g., "Massachusetts, USA")
            max_results: Max places per search term
            test_mode: If True, limit to 10 total results

        Returns:
            List of parsed Apify results as Pydantic models

        Raises:
            ApifyActorError: If actor run fails
            ApifyTimeoutError: If actor exceeds timeout
        """
```

**Apify Actor Configuration:**
- **Actor ID:** `compass/crawler-google-places`
- **Actor Stats:** 193K users, 4.8★ rating (validated via web search)
- **Pricing:** $5 per 1000 results (estimated $0.75 for 150 practices)

**Input Schema:**
```json
{
  "searchStringsArray": [
    "veterinary clinic in Massachusetts",
    "animal hospital in Massachusetts",
    "vet clinic in Massachusetts"
  ],
  "locationQuery": "Massachusetts, USA",
  "maxCrawledPlacesPerSearch": 50,
  "language": "en",
  "includeReviews": false,
  "includeImages": false,
  "includePeopleAlsoSearch": false,
  "includeOpeningHours": true
}
```

**Output Schema (mapped to ApifyGoogleMapsResult model):**
```python
class ApifyGoogleMapsResult(BaseModel):
    title: str                                    # Practice name
    place_id: str = Field(..., alias="placeId")   # Google Place ID (27 chars)
    address: str
    city: Optional[str]
    state: Optional[str]
    postal_code: Optional[str] = Field(None, alias="postalCode")
    phone: Optional[str]
    website: Optional[HttpUrl]
    url: HttpUrl                                  # Google Maps URL
    rating: Optional[float] = Field(None, ge=0.0, le=5.0)
    reviews_count: Optional[int] = Field(0, alias="reviewsCount")
    category_name: Optional[str] = Field(None, alias="categoryName")
    categories: List[str] = Field(default_factory=list)
    permanently_closed: bool = Field(False, alias="permanentlyClosed")
    temporarily_closed: bool = Field(False, alias="temporarilyClosed")
```

**Retry Logic:**
- Use `@retry_api_call()` decorator from FEAT-000
- Max 2 attempts with 5s fixed wait
- Don't retry: Actor validation errors, quota exceeded
- Log estimated cost on retry

**Error Handling:**
- Apify actor not found → Fail fast with clear error
- Actor timeout (>5 min) → Retry once, then fail
- Quota exceeded → Log error, fail gracefully
- Invalid results → Log warning, continue with valid records

**Dependencies:**
- `apify-client==1.7.2`
- `FEAT-000` ConfigLoader, Logger, RetryHandler
- `FEAT-000` ApifyGoogleMapsResult model

**Uncertainty:**
- ❓ Should we cache Apify results to disk to avoid re-scraping? (Recommendation: No for MVP, yes for Phase 2)
- ❓ What if Apify returns <150 results? Accept partial or fail? (Recommendation: Accept partial, log warning)

#### 2. Hard Filters (data_filter.py)

**Purpose:** Filter out practices that don't meet baseline qualification criteria

**Key Method:**
```python
class DataFilter:
    def apply_hard_filters(
        self,
        practices: List[ApifyGoogleMapsResult]
    ) -> Tuple[List[ApifyGoogleMapsResult], Dict[str, int]]:
        """
        Apply hard filters to Apify results.

        Filters:
        - Has website URL (not None)
        - ≥10 Google reviews
        - Not permanently closed

        Returns:
            Tuple of (filtered_practices, filter_stats)
            filter_stats = {"passed": X, "no_website": Y, "low_reviews": Z, "closed": W}
        """
```

**Filter Criteria:**

1. **Has Website:** `practice.website is not None`
   - **Rationale:** Can't enrich without a website (FEAT-002 depends on this)
   - **Expected rejection rate:** ~5% (most established practices have websites)

2. **Minimum Reviews:** `practice.reviews_count >= 10`
   - **Rationale:** Too few reviews = likely new/inactive practice
   - **Expected rejection rate:** ~15% (filter out very new practices)

3. **Not Closed:** `practice.permanently_closed == False`
   - **Rationale:** No point pursuing closed businesses
   - **Expected rejection rate:** ~2% (rare for Google Maps to list closed)

**Output:**
- Filtered list of qualifying practices
- Filter statistics for logging: `{"passed": 128, "no_website": 8, "low_reviews": 22, "closed": 3}`

**Dependencies:**
- `FEAT-000` Logger (log filter stats)
- `FEAT-000` ApifyGoogleMapsResult model

**Uncertainty:**
- ❓ Should we make filter thresholds configurable in config.json? (Recommendation: Yes, add FilteringConfig)
- ❓ Should "temporarily_closed" practices be filtered out? (Recommendation: No, they may reopen)

#### 3. Initial Scoring (initial_scorer.py)

**Purpose:** Calculate baseline lead score (0-25 points) based on Google Maps data only

**Scoring Algorithm:**

**Review Count Score (0-15 points):**
```python
def score_review_count(reviews_count: int) -> int:
    """
    0-49 reviews:    5 points  (Low social proof)
    50-149 reviews:  10 points (Medium social proof)
    150+ reviews:    15 points (High social proof)
    """
    if reviews_count >= 150:
        return 15
    elif reviews_count >= 50:
        return 10
    else:
        return 5
```

**Review Rating Score (0-10 points):**
```python
def score_review_rating(rating: float) -> int:
    """
    <3.5 stars:  0 points  (Quality concern)
    3.5-3.9:     3 points  (Below average)
    4.0-4.4:     6 points  (Average)
    4.5+:        10 points (Excellent)
    """
    if rating >= 4.5:
        return 10
    elif rating >= 4.0:
        return 6
    elif rating >= 3.5:
        return 3
    else:
        return 0
```

**Total Initial Score:** `review_count_score + review_rating_score = 0-25 points`

**Note:** This is NOT the final ICP fit score (0-120 points). FEAT-003 will add:
- Practice size scoring (40 pts)
- Call volume indicators (30 pts)
- Technology indicators (20 pts)
- Decision maker bonus (20 pts)
- Baseline score from FEAT-001 (10 pts of 120)

**Output:**
- Each practice gets `lead_score: int` field (0-25 range for now)
- Priority tier set to "Cold" (will be updated by FEAT-003)

**Dependencies:**
- `FEAT-000` VeterinaryPractice model

**Uncertainty:**
- ❓ Should initial score be 0-25 or normalize to 0-10 for consistency? (Recommendation: Keep 0-25, document partial)

#### 4. Notion Batch Upsert (notion_client.py - extends FEAT-000)

**Purpose:** De-duplicate and batch push practices to Notion database

**Key Method:**
```python
class NotionClient:
    def batch_upsert(
        self,
        practices: List[VeterinaryPractice]
    ) -> Dict[str, Any]:
        """
        Batch upsert practices to Notion with de-duplication.

        Process:
        1. Query all existing Place IDs from Notion (cache in memory)
        2. For each practice:
           - If Place ID exists: UPDATE (preserve sales workflow fields)
           - If Place ID new: CREATE
        3. Batch 10 records per API call
        4. Add 0.35s delay between batches (rate limiting)

        Returns:
            {
                "created": 142,
                "updated": 8,
                "failed": 0,
                "total_time": 54.2,
                "errors": []
            }
        """
```

**De-duplication Strategy:**

1. **Pre-query existing Place IDs:**
```python
# Query Notion database once at start
existing_place_ids = self._query_all_place_ids()  # Returns Set[str]
```

2. **Classify each practice:**
```python
for practice in practices:
    if practice.google_place_id in existing_place_ids:
        # UPDATE path
        update_queue.append(practice)
    else:
        # CREATE path
        create_queue.append(practice)
```

3. **Preserve sales workflow fields on UPDATE:**
```python
PRESERVE_FIELDS = [
    "Status",
    "Assigned To",
    "Research Notes",
    "Call Notes",
    "Last Contact Date",
    "Next Follow-Up Date",
    "Campaign"
]

def build_update_properties(practice, existing_record):
    # Only update enrichment fields, preserve sales fields
    props = practice.to_notion_properties()
    for field in PRESERVE_FIELDS:
        if field in existing_record["properties"]:
            props[field] = existing_record["properties"][field]
    return props
```

**Batch Processing:**
- Batch size: 10 records
- Delay: 0.35s between batches (2.86 req/s, under 3 req/s limit)
- Total time: 150 records ÷ 10 per batch × 0.35s = 5.25s + query time ≈ 8s

**Error Handling:**
- Notion API errors: Retry 3x with exponential backoff (via `@retry_notion()`)
- Rate limit (429): Wait 1s, retry (handled by decorator)
- Invalid property: Log error, skip record, continue
- Network timeout: Retry with backoff

**Field Mappings (VeterinaryPractice → Notion):**

| Python Field | Notion Property | Type |
|--------------|----------------|------|
| `practice_name` | "Practice Name" | title |
| `address` | "Address" | rich_text |
| `city` | "City" | rich_text |
| `state` | "State" | select |
| `zip_code` | "Zip Code" | rich_text |
| `phone` | "Phone" | phone_number |
| `website` | "Website" | url |
| `google_maps_url` | "Google Maps URL" | url |
| `google_place_id` | "Google Place ID" | rich_text |
| `google_rating` | "Google Rating" | number |
| `google_review_count` | "Google Review Count" | number |
| `business_categories` | "Business Categories" | multi_select |
| `lead_score` | "Lead Score" | number |
| `priority_tier` | "Priority Tier" | select |
| `first_scraped_date` | "First Scraped Date" | date |
| `scrape_run_id` | "Scrape Run ID" | rich_text |

**Dependencies:**
- `FEAT-000` NotionClient base class
- `FEAT-000` VeterinaryPractice model
- `FEAT-000` RetryHandler (@retry_notion)
- `notion-client==2.2.1`

**Uncertainty:**
- ❓ Should we validate Notion database schema on startup? (Recommendation: Yes, check database exists and accessible)
- ❓ Should we implement incremental backups of Notion data? (Recommendation: Phase 2)

### Data Flow

```
1. Load Configuration
   config = load_full_config("config/config.json")
   test_mode = config.test_mode or args.test

2. Run Apify Scraper
   apify_client = ApifyClient(config.apify)
   raw_practices = apify_client.run_google_maps_scraper(
       search_terms=config.target.search_terms,
       location=config.target.location,
       max_results=config.apify.max_google_results,
       test_mode=test_mode
   )
   # Returns 150-200 practices (or 10 in test mode)

3. Apply Hard Filters
   data_filter = DataFilter()
   filtered_practices, filter_stats = data_filter.apply_hard_filters(raw_practices)
   logger.info(f"Filtered: {filter_stats}")
   # Returns ~128 practices (or ~8 in test mode)

4. Calculate Initial Scores
   scorer = InitialScorer()
   for practice in filtered_practices:
       practice.lead_score = scorer.calculate_baseline_score(
           reviews_count=practice.google_review_count,
           rating=practice.google_rating
       )
       practice.priority_tier = "Cold"  # Placeholder, updated by FEAT-003
       practice.first_scraped_date = date.today()
       practice.scrape_run_id = generate_run_id()

5. Push to Notion
   notion_client = NotionClient(config.notion)
   result = notion_client.batch_upsert(filtered_practices)
   logger.info(f"Notion push complete: {result}")
   # Returns {"created": 120, "updated": 8, "failed": 0}

6. Error Summary
   error_tracker.print_summary()
```

### Configuration

**config.json additions:**
```json
{
  "target": {
    "location": "Massachusetts, USA",
    "search_terms": [
      "veterinary clinic in Massachusetts",
      "animal hospital in Massachusetts",
      "vet clinic in Massachusetts"
    ],
    "search_radius_miles": null,
    "excluded_cities": []
  },
  "apify": {
    "max_google_results": 50,
    "timeout_seconds": 300,
    "include_reviews": false,
    "include_images": false
  },
  "filtering": {
    "min_reviews": 10,
    "require_website": true,
    "exclude_closed": true
  }
}
```

**.env additions:**
```bash
APIFY_API_KEY=apify_api_xxxxxxxxxx
```

**Test Mode Override:**
```bash
# Command line flag (recommended)
python main.py --test  # Limits to 10 practices

# Or environment variable
TEST_MODE=true python main.py
```

### Testing Strategy

**Unit Tests:**
- ✅ ApifyClient parses actor output correctly
- ✅ DataFilter applies all three hard filters
- ✅ InitialScorer calculates correct scores for edge cases
- ✅ NotionClient de-duplicates by Place ID
- ✅ Notion property mapping (Python → Notion types)

**Integration Tests:**
- ✅ Full pipeline: Apify → Filter → Score → Notion (test mode, 10 practices)
- ✅ De-duplication: Re-run pipeline, verify no duplicates created
- ✅ Error handling: Mock Apify failure, verify retry logic

**Mock Data:**
```python
# tests/fixtures/apify_google_maps_sample.json
[
  {
    "title": "Boston Veterinary Clinic",
    "placeId": "ChIJAQAAAAAAAAARDgGT_2SBCbI",
    "address": "123 Main St, Boston, MA 02108",
    "rating": 4.7,
    "reviewsCount": 234,
    "website": "https://bostonvet.com",
    "permanentlyClosed": false
  }
]
```

**Manual Testing Checklist:**
1. Run with `--test` flag, verify exactly 10 practices
2. Check Notion database for correct field mappings
3. Re-run pipeline, verify no duplicates created
4. Intentionally close Notion tab, verify retry logic works
5. Check error summary shows categorized failures

### Acceptance Criteria

1. ✅ Apify scraper returns 150 MA veterinary practices (or 10 in test mode)
2. ✅ Hard filters reduce results by ~20% (no website, low reviews, closed)
3. ✅ Initial scores calculated correctly (0-25 point range)
4. ✅ All practices pushed to Notion within 10 seconds
5. ✅ De-duplication works: Re-running pipeline updates existing, doesn't duplicate
6. ✅ Sales workflow fields preserved on update (Status, Assigned To, etc.)
7. ✅ Test mode (`--test` flag) limits to 10 practices
8. ✅ Error tracking aggregates Apify and Notion failures
9. ✅ Cost: ≤$1.00 (Apify $0.75 + buffer)

### Dependencies

**Python Packages:**
```
apify-client==1.7.2
notion-client==2.2.1
pydantic==2.9.2
tenacity==9.0.0
python-dotenv==1.0.1
```

**External APIs:**
- Apify: `compass/crawler-google-places` actor
- Notion: Database `2a0edda2a9a081d98dc9daa43c65e744`

**Feature Dependencies:**
- **Depends on:** FEAT-000 (ConfigLoader, Logger, RetryHandler, NotionClient, Models)
- **Depended on by:** FEAT-002 (reads practices from Notion to enrich)

### Cost

**Apify:** $5 per 1000 Google Maps results
- 150 practices × 1.2 (over-scraping buffer) = 180 scrapes
- 180 ÷ 1000 × $5 = **$0.90**

**Notion:** Free tier (no cost for API calls)

**Total:** **$0.90**

### Timeline Estimate

**3 hours** to implement and test:
- Hour 1: ApifyClient + ApifyGoogleMapsResult model
- Hour 2: DataFilter + InitialScorer
- Hour 3: NotionClient batch_upsert + integration testing

## Open Questions & Uncertainties

### Apify Integration
- ❓ **Cache Apify results?** Save raw Apify output to disk to avoid re-scraping during development
  - **Recommendation:** Phase 2 feature (not critical for MVP)
  - **Rationale:** Adds complexity, Apify cost is low ($0.90)

- ❓ **Partial results?** What if Apify returns <150 practices?
  - **Recommendation:** Accept partial, log warning
  - **Rationale:** MA may not have 150 qualifying practices, don't fail

### Filtering
- ❓ **Configurable thresholds?** Make `min_reviews`, `require_website` configurable in config.json
  - **Recommendation:** Yes, add to FilteringConfig in FEAT-000
  - **Rationale:** Business may want to adjust criteria without code changes

- ❓ **Temporarily closed?** Should temporarily closed practices be filtered out?
  - **Recommendation:** No, keep them
  - **Rationale:** They may reopen, worth tracking

### Scoring
- ❓ **Initial score range?** Keep 0-25 or normalize to 0-10?
  - **Recommendation:** Keep 0-25, document as partial score
  - **Rationale:** FEAT-003 will expand to 0-120, easier to add than rescale

### Notion
- ❓ **Schema validation?** Check Notion database schema on startup?
  - **Recommendation:** Basic check (database exists, accessible)
  - **Rationale:** Full schema validation is brittle, just test connection

- ❓ **Incremental backups?** Export Notion data periodically?
  - **Recommendation:** Phase 2
  - **Rationale:** Not critical for MVP, Notion has built-in history

### Test Mode
- ❓ **Test mode location?** CLI flag vs config.json vs environment variable?
  - **Recommendation:** CLI flag `--test` (highest priority) or env var `TEST_MODE=true`
  - **Rationale:** More flexible, doesn't require editing config file

## Implementation Notes

### Critical Path
1. ApifyClient wrapper (depends on FEAT-000 ConfigLoader, RetryHandler)
2. ApifyGoogleMapsResult Pydantic model (in FEAT-000 models/)
3. DataFilter (simple filtering logic)
4. InitialScorer (simple scoring logic)
5. NotionClient.batch_upsert() (extends FEAT-000 base client)
6. Integration: Wire all components in main pipeline script

### Sequence
```
Day 1 (3 hours):
  Hour 1: ApifyClient + model
  Hour 2: Filters + scoring
  Hour 3: Notion batch upsert + testing
```

### Gotchas
1. **Apify actor ID:** Must be `compass/crawler-google-places`, not `compass-crawler-google-places`
2. **Place ID caching:** Must query all Place IDs once at start, not per-record
3. **Notion rate limiting:** 0.35s delay is critical, not optional
4. **Sales field preservation:** Must read existing record before update to preserve fields
5. **Test mode:** Must override `max_google_results` in Apify input, not just limit output
6. **Review count alias:** Apify uses `reviewsCount` (camelCase), map to `reviews_count` in model

## Success Metrics

**Definition of Done:**
- Apify scraper returns 150 practices (or 10 in test mode)
- All hard filters applied correctly
- Initial scores calculated (0-25 range)
- All practices in Notion database
- De-duplication works (no duplicates on re-run)
- Test mode functional
- Error tracking shows categorized failures
- Cost ≤$1.00

**Quality Bar:**
- 80%+ test coverage on core logic
- Integration test passes with real APIs
- Retry logic tested with mock failures
- No unhandled exceptions

## Future Enhancements (Phase 2+)

- Cache Apify results to disk (avoid re-scraping)
- Incremental scraping (only new practices since last run)
- Multi-region support (expand beyond MA)
- Advanced filters (exclude chains, franchise locations)
- Review sentiment analysis
- Competitive analysis (nearby practices)

---

**Dependencies:**
- **Depends on:** FEAT-000 (Shared Infrastructure)
- **Depended on by:** FEAT-002 (Website Enrichment), FEAT-003 (Lead Scoring)

**Related Documents:**
- [FEAT-000 PRD](../FEAT-000_shared-infrastructure/prd.md) - Shared infrastructure
- [docs/system/integrations.md](../../system/integrations.md) - Apify API details
- [docs/system/database.md](../../system/database.md) - Notion schema
- [docs/system/architecture.md](../../system/architecture.md) - Pipeline architecture
