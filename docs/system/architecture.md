# System Architecture

**Last Updated:** 2025-11-03
**Status:** Active - MVP Phase
**Version:** 1.0.0

## Overview

The US Veterinary Lead Generation System is a **batch processing pipeline** that automatically generates, enriches, scores, and delivers qualified veterinary practice leads to a Notion database for cold calling outreach.

**Type:** CLI application with sequential data pipeline
**Pattern:** ETL (Extract, Transform, Load) with enrichment layers
**Execution:** Local Python script with optional recurring schedule

## Architecture Goals

- **Reliability:** Retry logic ensures data completeness despite API failures
- **Cost Efficiency:** Target <$10 per run with 150+ practices (~$0.06 per lead)
- **Data Quality:** Multi-source enrichment with confidence tracking
- **Maintainability:** Modular components with clear interfaces
- **Debuggability:** Comprehensive logging and raw data retention
- **Testability:** Test mode for validation without API costs

## System Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                        USER INPUT                                     │
│  Command: python main.py --config config/config.json [--test]        │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
                                 ↓
┌──────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                                │
│  main.py - Coordinates pipeline execution                            │
│  • Load & validate configuration                                      │
│  • Initialize shared components (logger, clients)                     │
│  • Execute stages sequentially                                        │
│  • Aggregate results and costs                                        │
└────────────────────────────────┬─────────────────────────────────────┘
                                 │
         ┌───────────────────────┴───────────────────────┐
         │                                               │
         ↓                                               ↓
┌─────────────────────────┐                 ┌─────────────────────────┐
│  STAGE 1: SCRAPING      │                 │  FEAT-000: SHARED       │
│  (FEAT-001)             │                 │  INFRASTRUCTURE         │
│                         │◄────────────────│                         │
│  GoogleMapsScraper      │                 │  • ConfigLoader         │
│  ├─ Apify client        │                 │  • Logger               │
│  ├─ Search Boston vets  │                 │  • RetryHandler         │
│  ├─ 150-200 results     │                 │  • NotionClient         │
│  └─ Push to Notion      │                 │  • Data Models          │
│                         │                 │  • ErrorTracker         │
│  Output: Raw practices  │                 └─────────────────────────┘
│  in Notion with basic   │
│  data + initial score   │
└───────────┬─────────────┘
            │
            ↓
┌─────────────────────────┐
│  STAGE 2: ENRICHMENT    │
│  (FEAT-002)             │
│                         │
│  WebsiteEnrichment      │
│  ├─ Read from Notion    │
│  ├─ Crawl4AI scraping   │
│  ├─ OpenAI extraction   │
│  │  • Vet count         │
│  │  • Decision makers   │
│  │  • Services          │
│  │  • Tech features     │
│  │  • Personalization   │
│  └─ Update Notion       │
│                         │
│  Output: Enriched       │
│  practices with         │
│  decision maker info    │
└───────────┬─────────────┘
            │
            ↓
┌─────────────────────────┐
│  STAGE 3: SCORING       │
│  (FEAT-003)             │
│                         │
│  LeadScoring            │
│  ├─ Read from Notion    │
│  ├─ Calculate score     │
│  │  (0-120 points)      │
│  ├─ Classify size       │
│  │  (Solo/Small/Sweet/  │
│  │   Large/Corporate)   │
│  ├─ Assign priority     │
│  │  (Hot/Warm/Cold)     │
│  └─ Update Notion       │
│                         │
│  Output: Scored &       │
│  prioritized leads      │
└───────────┬─────────────┘
            │
            ↓
┌──────────────────────────────────────────────────────────────────────┐
│                       FINAL OUTPUT                                    │
│  • Notion database with 100+ qualified leads                         │
│  • Execution log with success/failure summary                        │
│  • Cost report (Apify + OpenAI spend)                                │
│  • Raw data backup in data/raw/ for debugging                        │
└──────────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### Layer 1: Shared Infrastructure (FEAT-000)

Located in `src/utils/` and `src/clients/`

**Purpose:** Provide reusable utilities and clients for all pipeline stages.

**Components:**

1. **ConfigLoader** (`src/utils/config_loader.py`)
   - Loads config.json and validates with Pydantic
   - Loads environment variables from .env
   - Provides typed configuration objects
   - Validates required fields at startup

2. **Logger** (`src/utils/logger.py`)
   - Structured JSON logging to file
   - Human-readable console output with colors
   - Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
   - Automatic log rotation (daily, keep 7 days)

3. **RetryHandler** (`src/utils/retry_handler.py`)
   - Exponential backoff decorator using tenacity
   - Configuration: 3 attempts, delays: 5s, 10s, 20s
   - Handles: HTTP errors, timeouts, rate limits
   - Logs retry attempts with context

4. **NotionClient** (`src/clients/notion_client.py`)
   - Wrapper around notion-client SDK
   - Batch operations (10 records per call)
   - Rate limit handling (3 req/s)
   - Retry logic for transient failures
   - Methods: create_practice(), update_practice(), query_practices()

5. **Data Models** (`src/models/`)
   - Pydantic schemas for all data types
   - Practice, ApifyPlace, WebsiteData, LeadScore
   - Input validation and type safety
   - Serialization for Notion API

6. **ErrorTracker** (`src/utils/error_tracker.py`)
   - Aggregates errors across pipeline
   - Generates summary report at end
   - Tracks: failed websites, LLM extraction failures, API errors

### Layer 2: Scraping (FEAT-001)

Located in `src/scrapers/google_maps.py`

**Purpose:** Acquire raw veterinary practice data from Google Maps via Apify.

**Responsibilities:**
- Configure Apify actor with search terms and geography
- Execute Google Maps search for Boston veterinarians
- Receive 150-200 raw practice records
- Apply hard filters (has website, 10+ reviews, open)
- De-duplicate by Google Place ID
- Calculate initial score (review count + rating)
- Batch push to Notion database (10 per call)

**Technology:** apify-client, notion-client, pydantic

**Data Contract:**
- **Input:** config.json (search terms, filters)
- **Output:** Notion database records with fields:
  - Practice Name, Address, City, State, Zip
  - Phone, Website, Google Maps URL
  - Place ID (unique identifier)
  - Rating, Review Count
  - Categories, Hours
  - Lead Score (initial: 0-20)
  - Status: "New"

### Layer 3: Enrichment (FEAT-002)

Located in `src/scrapers/website_scraper.py` and `src/extractors/llm_extractor.py`

**Purpose:** Enrich practices with website data and extract decision maker information.

**Responsibilities:**
- Query Notion for practices with websites
- For each practice:
  - Scrape website (homepage, team page, about page) using Crawl4AI
  - Extract HTML content with JavaScript rendering
  - Send to OpenAI GPT-4o-mini with structured extraction prompt
  - Parse JSON response with confidence levels
  - Update Notion record with enriched data
- Retry 3x with exponential backoff on failures
- Accept all confidence levels (high/medium/low), flag in Notion
- Log failed extractions for manual review

**Technology:** crawl4ai, openai, beautifulsoup4, pydantic

**Data Contract:**
- **Input:** Notion records with website field populated
- **Output:** Updated Notion records with:
  - Vet Count (total + per location) + confidence
  - Decision Maker (name + title + email) + confidence
  - Services (emergency, specialty, boarding, etc.)
  - Technology Features (online booking, client portal, live chat, telehealth)
  - Personalization Context (2-3 unique facts about practice)
  - Data Completeness score (0-100%)
  - Data Sources (website URL)

### Layer 4: Scoring (FEAT-003)

Located in `src/scoring/lead_scorer.py` and `src/scoring/classifier.py`

**Purpose:** Calculate ICP fit scores and prioritize leads for outreach.

**Responsibilities:**
- Query all practices from Notion
- For each practice:
  - Calculate Lead Score (0-120 points):
    - Practice Size (40 pts): 3-5 vets = 25 pts, emergency = +15 pts
    - Call Volume (30 pts): 100+ reviews = 20 pts, multiple locations = +10 pts
    - Technology (20 pts): online booking = 10 pts, portal/chat = +5 pts
    - Baseline (10 pts): 3.5+ rating = 5 pts, has website = +5 pts
    - Decision Maker Bonus (20 pts): email verified = 20 pts, name only = 10 pts
  - Classify Practice Size: Solo (1), Small (2), Sweet Spot (3-5), Large (6-9), Corporate (10+)
  - Assign Priority Tier:
    - Hot (80-120): Call immediately
    - Warm (50-79): Call soon
    - Cold (0-49): Research or defer
    - Out of Scope: Don't call (solo or 10+ vets)
  - Generate Score Breakdown (which criteria met/missed)
  - Update Notion record
- No external API calls (pure computation)

**Technology:** Python standard library, pydantic

**Data Contract:**
- **Input:** Notion records with enriched data
- **Output:** Updated Notion records with:
  - Lead Score (0-120)
  - Practice Size Classification
  - Priority Tier (Hot/Warm/Cold/Out of Scope)
  - Score Breakdown (explanation text)
  - Ready for outreach (boolean)

## Data Flow

### Sequential Pipeline Execution

```
1. User executes: python main.py --config config/config.json [--test]
   ↓
2. main.py loads configuration and initializes components
   ↓
3. STAGE 1: GoogleMapsScraper.scrape()
   • Calls Apify actor
   • Receives 150-200 practices
   • Filters: has website, 10+ reviews, open
   • De-duplicates by Place ID
   • Pushes to Notion (10 per batch)
   • Returns: 100-150 practices in Notion
   ↓
4. STAGE 2: WebsiteEnrichment.enrich()
   • Queries Notion for practices with websites
   • For each practice (with 3-5s delay):
     - Scrape website with Crawl4AI
     - Extract with OpenAI GPT-4o-mini
     - Update Notion record
   • Retry 3x on failures
   • Returns: 80%+ practices enriched
   ↓
5. STAGE 3: LeadScoring.score()
   • Queries all practices from Notion
   • Calculates scores (0-120)
   • Classifies sizes and priorities
   • Updates Notion records
   • Returns: All practices scored
   ↓
6. main.py aggregates results:
   • Total practices: X
   • Enriched: Y (Z%)
   • Decision makers found: A (B%)
   • Hot leads: C
   • Warm leads: D
   • Total cost: $E
   • Execution time: F minutes
```

### Test Mode (--test flag)

- Limit Google Maps scraping to 10 practices
- All subsequent stages process only those 10
- Validates pipeline without $10 spend
- Recommended for development and debugging

## Integration Points

### External Services

**Apify - Google Maps Scraping**
- **Actor:** compass/crawler-google-places
- **Purpose:** Acquire raw practice data
- **Authentication:** API key via APIFY_API_KEY env var
- **Rate Limits:** None (usage-based billing)
- **Cost:** ~$2 for 150 practices
- **Documentation:** https://apify.com/compass/crawler-google-places
- **Configuration:** See [integrations.md](integrations.md)

**OpenAI - LLM Extraction**
- **Endpoint:** https://api.openai.com/v1/chat/completions
- **Model:** gpt-4o-mini
- **Purpose:** Extract structured data from website HTML
- **Authentication:** Bearer token via OPENAI_API_KEY env var
- **Rate Limits:** Tier-based (verify before full run)
- **Cost:** ~$3 for 150 practices (~$0.02 per call)
- **Documentation:** https://platform.openai.com/docs
- **Configuration:** See [integrations.md](integrations.md)

**Notion - Lead Database**
- **API:** https://api.notion.com/v1/
- **Database ID:** 2a0edda2a9a081d98dc9daa43c65e744
- **Purpose:** Store and update lead data
- **Authentication:** Integration token via NOTION_API_KEY env var
- **Rate Limits:** 3 requests/second
- **Cost:** Free (up to 1000 blocks)
- **Documentation:** https://developers.notion.com/
- **Configuration:** See [integrations.md](integrations.md) and [database.md](database.md)

**Crawl4AI - Website Scraping**
- **Type:** Local library (no external API)
- **Purpose:** Scrape websites with JavaScript rendering
- **Technology:** Playwright-based browser automation
- **Cost:** Free (local execution)
- **Documentation:** https://crawl4ai.com/docs
- **Configuration:** Headless Chromium, 30s timeout

## Security Architecture

### Authentication
- **No user authentication:** CLI tool run by single operator
- **API Keys:** Stored in .env file (gitignored)
- **Permissions:** Minimal scopes (Notion database access only, not workspace admin)

### Authorization
- **Apify:** Execute actors only (no account modification)
- **OpenAI:** API calls only (no org admin access)
- **Notion:** Integration with specific database (not full workspace)

### Data Protection
- **At Rest:** Raw data stored locally in `data/raw/` (not shared)
- **In Transit:** HTTPS for all API calls
- **Secrets:** Environment variables only (never hardcoded)
- **Scraping Ethics:** 3-5s delays, respect robots.txt, user agent identification

### Secrets Management
- **Tool:** python-dotenv
- **Storage:** .env file (gitignored)
- **Example:** .env.example (checked in without actual keys)
- **Production:** Environment variables in scheduler/CI

## Scalability

### Current Scale
- **Target:** 150-200 practices per run (Boston only)
- **Execution Time:** ~2 hours
- **Cost:** <$10 per run
- **Frequency:** One-time MVP, recurring weekly (future)

### Scale Limits
- **Notion Rate Limit:** 3 req/s (handles 180 practices/minute)
- **OpenAI Rate Limit:** Tier-based (verify account before full run)
- **Website Scraping:** Respectful delays (3-5s) → ~12-20 sites/minute
- **Local Execution:** Single-threaded (no parallelization in MVP)

### Future Scaling (Phase 2+)
- **Multi-Geography:** Expand beyond Boston (reuse pipeline)
- **Parallelization:** Async website scraping (10x faster)
- **Caching:** Store website content, skip re-scraping
- **Cloud Deployment:** AWS Lambda or GCP Cloud Run
- **Recurring Runs:** Cron job with de-duplication

## Error Handling & Resilience

### Retry Strategy
- **All external API calls** wrapped with RetryHandler
- **Configuration:** 3 attempts, exponential backoff (5s, 10s, 20s)
- **Exceptions:** HTTP errors, timeouts, rate limits
- **Logging:** Each retry logged with context

### Partial Failure Handling
- **Philosophy:** Log and continue (don't block pipeline)
- **Example:** If website scraping fails for 50/150 practices:
  - Log failures with URLs and error messages
  - Continue with 100 successfully enriched practices
  - Mark failed practices with "Needs Manual Research"
  - Final report shows success rate (100/150 = 67%)

### Confidence Tracking
- **LLM Extraction:** high/medium/low confidence per field
- **Strategy:** Accept all confidence levels, flag in Notion
- **Manual Review:** Low-confidence extractions flagged for validation

### Data Quality Gates
- **Input Validation:** Pydantic models reject malformed data
- **Output Validation:** Verify Notion schema before push
- **Cross-Validation:** Sanity checks (vet count 1-50, email format, etc.)

## Deployment

### MVP Deployment
- **Platform:** Local execution (developer machine)
- **Trigger:** Manual command: `python main.py`
- **Monitoring:** Console output + log file
- **Alerting:** None (manual review of results)

### Future Deployment (Phase 3)
- **Platform:** AWS Lambda or GCP Cloud Run
- **Trigger:** Cron schedule (weekly runs)
- **Monitoring:** CloudWatch or GCP Logging
- **Alerting:** Email/Slack on failure or cost threshold

## Performance Characteristics

### Execution Time Breakdown
| Stage | Duration | Bottleneck |
|-------|----------|------------|
| Google Maps Scraping | 5 minutes | Apify actor execution time |
| Website Enrichment | 1.5 hours | 3-5s delay per site, LLM API calls |
| Scoring | < 1 minute | Pure computation (fast) |
| Notion Push | 1 minute | Batched API calls |
| **Total** | **~2 hours** | Website enrichment dominates |

### Cost Breakdown
| Service | Unit Cost | Quantity | Total |
|---------|-----------|----------|-------|
| Apify (Google Maps) | $0.01/result | 150 | $1.50 |
| OpenAI (gpt-4o-mini) | $0.02/call | 150 | $3.00 |
| Notion API | Free | 150 | $0.00 |
| Crawl4AI | Free | 150 | $0.00 |
| **Total** | | | **$4.50** |

**Note:** Actual costs may vary (±50%) based on Apify actor pricing and OpenAI token usage.

## Testing Strategy

### Test Mode
- **Flag:** `--test`
- **Behavior:** Limit to 10 practices (all stages)
- **Purpose:** Validate pipeline without full cost
- **Cost:** ~$0.50 (10 practices)

### Unit Tests
- **Framework:** pytest
- **Coverage:** Scorers, classifiers, data transformers
- **Mocking:** External API calls (avoid costs)
- **Location:** `tests/unit/`

### Integration Tests
- **Approach:** Full pipeline with test mode
- **Validation:** End-to-end data flow
- **Fixtures:** Sample Apify/LLM responses
- **Location:** `tests/integration/`

## Monitoring & Observability

### Logging
- **Console:** Human-readable with colors (INFO level)
- **File:** Structured JSON logs (DEBUG level)
- **Location:** `data/logs/scraper_YYYY-MM-DD_HH-MM-SS.log`
- **Retention:** 7 days

### Metrics Tracked
- Total practices scraped
- Enrichment success rate
- Decision maker discovery rate
- Hot/Warm/Cold lead distribution
- API call counts and costs
- Execution time per stage
- Error counts by type

### Final Report
```
========================================
PIPELINE EXECUTION SUMMARY
========================================
Practices Scraped: 152
Practices Enriched: 127 (83.6%)
Decision Makers Found: 94 (74.0%)
Hot Leads: 18
Warm Leads: 45
Cold Leads: 64
Out of Scope: 25
Total Cost: $4.73
Execution Time: 1h 48m
Errors: 25 (see log for details)
========================================
```

## Maintenance & Evolution

### Phase 1 (MVP) - Complete
- ✅ FEAT-000: Shared infrastructure
- ✅ FEAT-001: Google Maps scraping
- ✅ FEAT-002: Website enrichment
- ✅ FEAT-003: Lead scoring

### Phase 2 (Enhancements)
- FEAT-004: LinkedIn decision maker fallback
- FEAT-005: De-duplication for recurring scrapes
- Email verification (SMTP checks)
- Multi-geography support

### Phase 3 (Production)
- Cloud deployment (AWS Lambda / GCP)
- Recurring execution (cron schedule)
- Monitoring dashboard
- Alerting and notifications
- CI/CD pipeline

---

**See Also:**
- [stack.md](stack.md) - Technology details
- [database.md](database.md) - Notion schema
- [integrations.md](integrations.md) - API configurations
- [configuration.md](configuration.md) - Config schema
- [../sop/git-workflow.md](../sop/git-workflow.md) - Development workflow
