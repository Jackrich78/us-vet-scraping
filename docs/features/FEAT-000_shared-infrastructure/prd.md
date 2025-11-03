# Product Requirements Document: Shared Infrastructure

**Feature ID:** FEAT-000
**Feature Name:** Shared Infrastructure & Foundation
**Priority:** P0 (Critical - Required for all other features)
**Status:** Planning
**Owner:** Development Team
**Created:** 2025-11-03

## Executive Summary

Build the foundational utilities, clients, and data models that all pipeline features depend on. This includes configuration management, logging, retry logic, API clients, and error tracking. No business logic - purely infrastructure.

**Success Metric:** All components tested and ready for FEAT-001 to consume.

## Problem Statement

Without shared infrastructure:
- Each feature duplicates error handling, logging, and API client code
- No consistent configuration management (secrets exposed, no validation)
- No retry logic for transient failures (data loss, pipeline failures)
- No structured error tracking (debugging nightmares)
- No type safety (runtime errors from typos)

## Goals & Non-Goals

### Goals
✅ Type-safe configuration loading with Pydantic validation
✅ Dual logging (JSON to file, colorized to console)
✅ Reusable retry decorators with exponential backoff
✅ Notion API client wrapper with rate limiting
✅ Pydantic data models for all entities
✅ Error aggregation for final reporting
✅ Test mode support (--test flag for 10 practices)

### Non-Goals
❌ Business logic (scoring, filtering, extraction)
❌ API integration code (Apify, OpenAI implementations)
❌ Data processing logic (those belong in feature modules)

## User Stories

**As a developer**, I need validated configuration so I catch typos before running expensive pipelines.

**As a developer**, I need structured logs so I can debug failures with context.

**As a developer**, I need automatic retries so transient network errors don't fail the entire pipeline.

**As a developer**, I need a Notion client wrapper so I don't repeat rate limiting logic everywhere.

**As a developer**, I need error aggregation so I get a summary of all failures at the end.

## Technical Specification

### Architecture

```
src/
├── config/
│   └── settings.py          # Pydantic models + load_full_config()
├── utils/
│   ├── logger.py            # Dual logging setup
│   ├── retry_handler.py     # Tenacity retry decorators
│   └── error_tracker.py     # Error aggregation
├── clients/
│   └── notion_client.py     # Notion API wrapper
└── models/
    ├── practice.py          # VeterinaryPractice model
    ├── apify_models.py      # ApifyPlace, LinkedInEmployee
    ├── website_models.py    # WebsiteData, VetPracticeExtraction
    └── scoring_models.py    # LeadScore, PriorityTier
```

### Component Details

#### 1. Configuration Management (settings.py)

**Purpose:** Load and validate config.json + .env with Pydantic

**Key Classes:**
- `VetScrapingConfig` (main config)
- `TargetConfig`, `ApifyConfig`, `WebsiteScrapingConfig`
- `NotionConfig`, `ScoringConfig`, `FilteringConfig`
- `EnvironmentSettings` (loads .env)
- `load_full_config()` function

**Validation Rules:**
- API keys: Validate format (apify_api_, secret_, sk-)
- Notion database ID: 32 hex chars
- Scoring weights: Max total <= 120 points
- File paths: extraction prompt file must exist
- Search terms: At least one non-empty term

**Dependencies:** pydantic 2.9.2, pydantic-settings, python-dotenv

**Uncertainty:**
- ❓ Should we validate API connectivity during config load or defer to feature code?
- ❓ Test mode override: Should --test flag be in config or command-line only?

#### 2. Logging (logger.py)

**Purpose:** Dual logging (JSON to file, colorized to console)

**Features:**
- Structured JSON logs to `data/logs/scraper_YYYY-MM-DD_HH-MM-SS.log`
- Colorized console output (DEBUG=cyan, INFO=green, WARNING=yellow, ERROR=red)
- Support for extra fields (practice_name, cost, scrape_run_id)
- Log rotation: Daily, keep 7 days
- Cleanup function for old logs

**Implementation:**
- Custom `JSONFormatter` for file logs
- Custom `ColorizedFormatter` for console
- `setup_logging()` function configures both handlers

**Dependencies:** Python logging (stdlib), no external dependencies needed

**Uncertainty:**
- ❓ Should we use colorlog library or custom ANSI codes? (Recommendation: custom for no deps)
- ❓ Log level: DEBUG in test mode, INFO in production? (Needs env var override)

#### 3. Retry Logic (retry_handler.py)

**Purpose:** Exponential backoff retry decorators for all external APIs

**Decorators:**
- `retry_scraping()` - For website scraping (2 attempts, 5s/10s)
- `retry_api_call()` - For paid APIs (2 attempts, 5s fixed)
- `retry_notion()` - For Notion API (3 attempts, 1s/2s/4s exponential)

**Configuration:**
- Max attempts: 2-3 depending on service cost
- Wait strategy: Exponential with jitter for Apify/Notion, fixed for OpenAI
- Exceptions: Network errors, timeouts, rate limits (429)
- Don't retry: Client errors (400, 401, 403, 404)

**Dependencies:** tenacity 9.0.0

**Uncertainty:**
- ❓ Should we implement circuit breaker pattern now or defer to Phase 2?
- ❓ Cost tracking: Log estimated cost per retry? (Recommendation: yes)

#### 4. Notion Client (notion_client.py)

**Purpose:** Wrapper around notion-client SDK with rate limiting and batch operations

**Key Methods:**
- `create_practice(properties: Dict) -> str` - Create single record
- `update_practice(page_id: str, properties: Dict)` - Update single record
- `upsert_practice(practice_data: Dict) -> str` - Create or update with de-dup
- `query_by_place_id(place_id: str) -> Optional[Dict]` - Find existing
- `query_all_practices() -> List[Dict]` - Fetch all with pagination
- `batch_upsert(practices: List[Dict]) -> Dict[str, int]` - Batch with rate limiting

**Features:**
- Automatic rate limiting (0.35s delay between requests)
- Batch processing (10 records per batch)
- De-duplication by Google Place ID
- Preserve sales workflow fields on update
- Retry logic integrated (via retry_notion decorator)

**Dependencies:** notion-client 2.2.1

**Uncertainty:**
- ❓ Cache Place IDs in memory during batch operations? (Recommendation: yes for performance)
- ❓ Should we validate Notion schema on startup or trust it exists? (Recommendation: validate)

#### 5. Error Tracking (error_tracker.py)

**Purpose:** Aggregate errors across pipeline for final summary report

**Key Class: `ErrorAggregator`**
- `log_error(category: str, message: str, practice_name: str)` - Record error
- `get_error_count() -> int` - Total errors
- `get_errors_by_category() -> Dict[str, List[str]]` - Grouped errors
- `print_summary()` - Display at pipeline end

**Categories:**
- `apify_scraping` - Apify actor failures
- `website_timeout` - Website scraping timeouts
- `llm_extraction` - OpenAI extraction failures
- `notion_push` - Notion API errors
- `validation` - Data validation failures

**Output Format:**
```
========================================
ERROR SUMMARY
========================================
Total Errors: 23
  website_timeout: 15 errors
    - bostonvetclinic.com: Timeout after 30s
    - cambridgeanimalhospital.com: Connection refused
    ... (show first 3, then "and X more")
  llm_extraction: 8 errors
    - brooklinevet.com: Invalid JSON response
    ...
========================================
```

**Uncertainty:**
- ❓ Should errors be persisted to file or just in-memory? (Recommendation: in-memory, already in logs)

#### 6. Data Models (models/)

**Purpose:** Pydantic schemas for type safety and validation

**practice.py:**
```python
class VeterinaryPractice(BaseModel):
    # Core Data (FEAT-001)
    practice_name: str
    address: str
    city: str
    state: str = "MA"
    zip_code: Optional[str]
    phone: str
    website: Optional[HttpUrl]
    google_maps_url: HttpUrl
    google_place_id: str
    google_rating: Optional[float] = Field(None, ge=0.0, le=5.0)
    google_review_count: Optional[int] = Field(None, ge=0)
    business_categories: List[str] = Field(default_factory=list)

    # Enrichment Data (FEAT-002)
    confirmed_vet_count_total: Optional[int] = Field(None, ge=1, le=50)
    decision_maker_name: Optional[str]
    decision_maker_email: Optional[EmailStr]
    personalization_context: List[str] = Field(default_factory=list)
    # ... additional fields

    # Scoring (FEAT-003)
    lead_score: int = Field(0, ge=0, le=120)
    priority_tier: str

    # Metadata
    first_scraped_date: date
    scrape_run_id: str
```

**apify_models.py:**
```python
class ApifyGoogleMapsResult(BaseModel):
    title: str
    place_id: str = Field(..., alias="placeId")
    address: str
    city: Optional[str]
    # ... all Apify output fields
```

**website_models.py:**
```python
class VetPracticeExtraction(BaseModel):
    vet_count_total: Optional[int]
    vet_count_confidence: Literal["high", "medium", "low"]
    decision_maker: DecisionMaker
    personalization_context: List[str]
    # ... LLM extraction schema
```

**Uncertainty:**
- ❓ Should models include Notion field name mappings or keep separate? (Recommendation: separate mapper)

### Data Flow

```
1. load_full_config()
   → Loads config.json
   → Merges .env secrets
   → Validates with Pydantic
   → Returns VetScrapingConfig

2. setup_logging()
   → Creates log directory
   → Configures JSON + console handlers
   → Returns logger instance

3. NotionClient(config.notion)
   → Validates database connection
   → Returns ready-to-use client

4. ErrorAggregator()
   → Instantiated once per run
   → Passed to all features
   → print_summary() at end
```

### Configuration

**config.json:** See docs/system/configuration.md for complete schema

**.env:**
```bash
APIFY_API_KEY=apify_api_xxx
OPENAI_API_KEY=sk-proj-xxx
NOTION_API_KEY=secret_xxx
NOTION_DATABASE_ID=2a0edda2a9a081d98dc9daa43c65e744
LOG_LEVEL=INFO
TEST_MODE=false
```

**Validation on Startup:**
```python
# main.py
config = load_full_config("config/config.json")
logger = setup_logging(log_level=config.log_level)
notion = NotionClient(config.notion)
error_tracker = ErrorAggregator()

# Validate connections
validate_config_on_startup(config)  # Tests API connectivity
```

### Testing Strategy

**Unit Tests:**
- ✅ Config loading with valid/invalid JSON
- ✅ Config validation (missing keys, wrong formats)
- ✅ Pydantic model validation (field constraints)
- ✅ Retry decorator behavior (success, retry, fail)
- ✅ Error aggregator categorization
- ✅ Logging output format

**Integration Tests:**
- ✅ Notion client connection (real API)
- ✅ Full config load with .env file
- ✅ End-to-end: load config → setup logging → create Notion client

**Test Mode:**
- `--test` flag should be propagated to all features
- Config overrides: max_google_results = 10

### Acceptance Criteria

1. ✅ Configuration loads from config.json + .env without errors
2. ✅ All Pydantic models validate sample data
3. ✅ Logs appear in both console (colorized) and file (JSON)
4. ✅ Retry decorators retry on transient errors, fail on client errors
5. ✅ Notion client successfully creates and updates test records
6. ✅ Error tracker aggregates multiple errors and prints summary
7. ✅ Test mode (--test) reduces max_google_results to 10
8. ✅ All dependencies installable via pip (no version conflicts)

### Dependencies

**Python Packages:**
```
pydantic==2.9.2
pydantic-settings==2.5.2
python-dotenv==1.0.1
notion-client==2.2.1
tenacity==9.0.0
```

**No External Services:** This feature is pure utility code.

### Cost

**$0** - No API calls, just local code.

### Timeline Estimate

**3-4 hours** to implement and test all components.

## Open Questions & Uncertainties

### Configuration
- ❓ **API connectivity validation:** Validate during config load or defer to feature code?
  - **Recommendation:** Add `validate_config_on_startup()` function, call from main.py
  - **Rationale:** Fail fast if credentials invalid

- ❓ **Test mode location:** --test as CLI flag or in config.json?
  - **Recommendation:** CLI flag that overrides config
  - **Rationale:** More flexible, doesn't require editing config file

### Logging
- ❓ **External library vs custom:** Use colorlog or custom ANSI codes?
  - **Recommendation:** Custom (no dependencies)
  - **Rationale:** Simpler, one less dependency

- ❓ **Log level in test mode:** Auto-switch to DEBUG?
  - **Recommendation:** Yes, if --test then log_level = DEBUG
  - **Rationale:** More visibility during development

### Retry Logic
- ❓ **Circuit breaker:** Implement now or Phase 2?
  - **Recommendation:** Phase 2
  - **Rationale:** MVP doesn't need it, adds complexity

- ❓ **Cost tracking per retry:** Log estimated cost?
  - **Recommendation:** Yes, log estimated cost in retry warning
  - **Rationale:** Helps monitor budget, minimal effort

### Notion Client
- ❓ **Place ID caching:** Cache in memory during batch operations?
  - **Recommendation:** Yes, dict cache during single run
  - **Rationale:** Reduces API calls (150 Place ID queries → 1 paginated query)

- ❓ **Schema validation:** Check Notion database schema on startup?
  - **Recommendation:** Basic check (database exists, accessible)
  - **Rationale:** Full schema validation is brittle, just test connection

### Error Tracking
- ❓ **Error persistence:** Write errors to separate file?
  - **Recommendation:** No, already in main log file
  - **Rationale:** Duplication, can parse logs if needed

### Data Models
- ❓ **Notion field mapping:** Include in models or separate?
  - **Recommendation:** Separate `notion_mapper.py` utility
  - **Rationale:** Models stay clean, mapper handles Notion-specific format

## Implementation Notes

### Critical Path
1. Config management (required first)
2. Logging (needed for debugging)
3. Pydantic models (needed by all features)
4. Notion client (FEAT-001 depends on it)
5. Retry decorators (apply to all API calls)
6. Error tracker (can be added last)

### Sequence
```
Day 1 (4 hours):
  Hour 1: Config management + Pydantic models
  Hour 2: Logging setup + testing
  Hour 3: Notion client wrapper + rate limiting
  Hour 4: Retry decorators + Error tracker + testing
```

### Gotchas
1. **Pydantic v2 syntax:** Use `model_config`, not `Config` class
2. **Notion rate limiting:** Must add 0.35s delay, not just batch size
3. **Environment variables:** Call `load_dotenv()` before accessing os.getenv()
4. **Retry exceptions:** Only retry on specific exception types, not all errors
5. **Log file paths:** Create `data/logs/` directory if it doesn't exist

## Success Metrics

**Definition of Done:**
- All 6 components implemented and unit tested
- Integration test passes (config → logging → Notion client)
- Documentation complete (docstrings on all public functions)
- No external API calls (except Notion connection test)
- Ready for FEAT-001 to import and use

**Quality Bar:**
- 80%+ test coverage on core logic
- All Pydantic validators working
- Retry logic tested with mock failures
- Logs properly formatted (JSON + colorized)

## Future Enhancements (Phase 2+)

- Circuit breaker pattern for API failures
- Prometheus metrics export
- Configuration hot-reload (no restart needed)
- Advanced caching strategies
- Health check endpoints

---

**Dependencies:**
- **Depends on:** Nothing (foundation)
- **Depended on by:** FEAT-001, FEAT-002, FEAT-003

**Related Documents:**
- [docs/system/stack.md](../../system/stack.md) - Dependency versions
- [docs/system/configuration.md](../../system/configuration.md) - Complete Pydantic models
- [docs/system/architecture.md](../../system/architecture.md) - Component architecture
