# Product Requirements Document: Website Enrichment & LLM Extraction

**Feature ID:** FEAT-002
**Feature Name:** Website Enrichment & LLM Extraction
**Priority:** P0 (Critical - Core enrichment)
**Status:** Planning
**Owner:** Development Team
**Created:** 2025-11-03

## Executive Summary

Scrape veterinary practice websites using Crawl4AI (async, 5 concurrent), extract structured data using OpenAI GPT-4o-mini with structured outputs, and update existing Notion records with enrichment data. This feature adds critical ICP fit signals: vet count, decision makers, services, technology indicators, and personalization context.

**Success Metric:** 150 practices enriched with structured data within 8 minutes, cost ≤$0.30.

## Problem Statement

Without website enrichment:
- Can't determine practice size (solo vs multi-vet)
- Can't identify decision makers (owner names, emails)
- Can't detect high-value indicators (24/7, specialties, advanced tech)
- Can't personalize outreach (no context about practice)
- Scoring based only on Google Maps data (incomplete ICP fit)

## Goals & Non-Goals

### Goals
✅ Scrape 150 practice websites asynchronously (5 concurrent tabs, 5.5 min total)
✅ Extract structured data using OpenAI GPT-4o-mini with Pydantic schemas
✅ Capture: vet count, decision maker info, services, technology, personalization context
✅ Handle extraction confidence levels (high/medium/low)
✅ Retry transient failures (timeout, rate limits) 3x with exponential backoff
✅ Update existing Notion records (preserve sales workflow fields)
✅ Comprehensive error tracking (timeout, LLM failures, validation errors)

### Non-Goals
❌ ICP fit scoring (FEAT-003)
❌ LinkedIn enrichment (Phase 2)
❌ Email validation/verification
❌ Deep link analysis (scrape only homepage + about/team pages)
❌ Image analysis (OCR, logo extraction)
❌ Review sentiment analysis

## User Stories

**As a sales rep**, I need to know how many vets work at a practice so I can tailor my pitch to practice size.

**As a sales rep**, I need decision maker names and emails so I can personalize outreach.

**As a sales rep**, I need to know if they have 24/7 emergency services so I can highlight relevant product features.

**As a developer**, I need confidence levels on extracted data so I can flag uncertain information for human review.

**As a business owner**, I need error tracking so I know which websites failed to scrape and why.

## Technical Specification

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ FEAT-002: Website Enrichment & LLM Extraction              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Query Notion for practices with websites                │
│     └─ Filter: website != null, enrichment_status != done  │
│                                                             │
│  2. Crawl4AI: Async website scraping                        │
│     ├─ 5 concurrent browser tabs                           │
│     ├─ Magic mode (smart content extraction)               │
│     ├─ 30s timeout per site                                │
│     └─ Extract: HTML, cleaned text, metadata               │
│                                                             │
│  3. OpenAI GPT-4o-mini: Structured extraction               │
│     ├─ Input: Website text + extraction prompt             │
│     ├─ Output: Pydantic VetPracticeExtraction model        │
│     ├─ Structured outputs (guaranteed valid JSON)          │
│     └─ Extract: vets, decision maker, services, tech       │
│                                                             │
│  4. Update Notion records                                   │
│     ├─ Map extracted data to Notion properties             │
│     ├─ Set enrichment_status = "completed"                 │
│     └─ Preserve sales workflow fields                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Component Details

#### 1. Website Scraper (website_scraper.py)

**Purpose:** Async scraping of practice websites using Crawl4AI

**Key Class:**
```python
class WebsiteScraper:
    def __init__(self, config: WebsiteScrapingConfig):
        self.browser_config = BrowserConfig(
            browser_type="chromium",
            headless=True,
            viewport_width=1920,
            viewport_height=1080,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        self.crawler_config = CrawlerRunConfig(
            wait_for="networkidle",
            page_timeout=30000,  # 30s timeout
            delay_before_return_html=2.0,
            magic=True,  # Smart content extraction
            cache_mode="enabled"
        )
        self.max_concurrent = 5

    async def scrape_batch(
        self,
        websites: List[HttpUrl]
    ) -> List[WebsiteData]:
        """
        Scrape multiple websites concurrently.

        Args:
            websites: List of website URLs to scrape

        Returns:
            List of WebsiteData objects with HTML, text, metadata

        Raises:
            WebsiteTimeoutError: If site exceeds 30s timeout
            WebsiteConnectionError: If site unreachable
        """
```

**Crawl4AI Configuration:**
- **Browser:** Chromium (headless)
- **Concurrency:** 5 tabs (150 sites ÷ 5 = 30 batches × 11s per batch = 5.5 min)
- **Timeout:** 30s per site
- **Magic mode:** Smart content extraction (removes nav, footer, ads)
- **Cache:** Enabled (avoid re-scraping during dev)

**Output Model:**
```python
class WebsiteData(BaseModel):
    url: HttpUrl
    practice_name: str
    html_content: str
    cleaned_text: str  # Magic mode output
    success: bool
    error_message: Optional[str]
    scraped_at: datetime
    page_title: Optional[str]
    meta_description: Optional[str]
```

**Retry Logic:**
- Use `@retry_scraping()` decorator from FEAT-000
- Max 2 attempts with 5s, 10s wait
- Retry on: Timeout, connection error, 503
- Don't retry: 404, 403, SSL errors (log and continue)
- Log estimated time cost on retry

**Error Handling:**
- Timeout (>30s) → Retry once, then skip
- 404/403 → Log warning, mark as failed, continue
- SSL error → Log warning, mark as failed, continue
- Connection refused → Retry once, then skip
- Invalid HTML → Log warning, mark as failed, continue

**Performance:**
- **5 concurrent tabs:** Optimal balance (CPU, memory, rate limiting)
- **30s timeout:** Most sites load in <10s, but allow buffer
- **Total time:** 150 sites ÷ 5 concurrent × 11s avg = **5.5 minutes**

**Dependencies:**
- `crawl4ai==0.3.74`
- `FEAT-000` ConfigLoader, Logger, RetryHandler
- `FEAT-000` WebsiteData model

**Uncertainty:**
- ❓ Should we scrape only homepage or also /about and /team pages? (Recommendation: Homepage only for MVP)
- ❓ Should we cache scraped HTML to disk? (Recommendation: Yes, in data/website_cache/)
- ❓ Should we handle JavaScript-heavy sites differently? (Recommendation: Magic mode handles most cases)

#### 2. LLM Extractor (llm_extractor.py)

**Purpose:** Extract structured data from website HTML using OpenAI GPT-4o-mini

**Key Class:**
```python
class LLMExtractor:
    def __init__(self, config: WebsiteScrapingConfig):
        self.client = OpenAI(api_key=config.openai_api_key)
        self.model = "gpt-4o-mini"
        self.extraction_prompt = self._load_extraction_prompt()

    @retry_api_call()
    def extract_practice_data(
        self,
        website_data: WebsiteData
    ) -> VetPracticeExtraction:
        """
        Extract structured data from website using OpenAI structured outputs.

        Args:
            website_data: Scraped website HTML and text

        Returns:
            VetPracticeExtraction Pydantic model (guaranteed valid)

        Raises:
            LLMExtractionError: If extraction fails after retries
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.extraction_prompt},
                {"role": "user", "content": website_data.cleaned_text}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "vet_practice_extraction",
                    "schema": VetPracticeExtraction.model_json_schema()
                }
            },
            temperature=0.1,
            max_tokens=2000
        )
        return VetPracticeExtraction.model_validate_json(response.choices[0].message.content)
```

**OpenAI Configuration:**
- **Model:** `gpt-4o-mini` (cheap, fast, sufficient for extraction)
- **Method:** Structured Outputs (Pydantic schema → JSON schema)
- **Temperature:** 0.1 (deterministic extraction)
- **Max tokens:** 2000 (sufficient for structured output)
- **Cost:** $0.15/1M input + $0.60/1M output ≈ $0.001 per extraction

**Extraction Prompt (config/website_extraction_prompt.txt):**
```
You are a veterinary practice data extraction expert. Extract structured information from the website text below.

Focus on:
1. Number of veterinarians (search for "Our Team", "Meet the Vets", staff lists)
2. Decision maker (owner, practice manager, medical director)
3. Services (emergency, specialty, wellness, surgery, dental, boarding)
4. Technology indicators (online booking, telemedicine, patient portal, digital records)
5. Personalization context (unique services, awards, community involvement, specialties)

Rules:
- If information is not found, return null or empty array (DO NOT GUESS)
- For vet_count_total, provide your confidence level (high/medium/low)
- For decision maker, extract name and role; search common patterns
- For services, list all explicitly mentioned services
- For technology, note any modern tech features
- For personalization, extract 2-3 unique facts about the practice

Return ONLY valid JSON matching the schema. No additional commentary.
```

**Extraction Schema:**
```python
class DecisionMaker(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None  # "Owner", "Practice Manager", "Medical Director"
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class VetPracticeExtraction(BaseModel):
    # Vet Count
    vet_count_total: Optional[int] = Field(None, ge=1, le=50)
    vet_count_confidence: Literal["high", "medium", "low"] = "low"

    # Decision Maker
    decision_maker: Optional[DecisionMaker] = None

    # Services (multi-select)
    emergency_24_7: bool = False
    specialty_services: List[str] = Field(default_factory=list)  # ["Surgery", "Dental", "Oncology"]
    wellness_programs: bool = False
    boarding_services: bool = False

    # Technology Indicators
    online_booking: bool = False
    telemedicine: bool = False
    patient_portal: bool = False
    digital_records_mentioned: bool = False

    # Personalization Context
    personalization_context: List[str] = Field(default_factory=list)  # Max 3 items
    awards_accreditations: List[str] = Field(default_factory=list)
    unique_services: List[str] = Field(default_factory=list)

    # Metadata
    extraction_timestamp: datetime = Field(default_factory=datetime.utcnow)
```

**Structured Outputs Benefits:**
- **Guaranteed valid JSON:** No malformed responses
- **Type safety:** Pydantic validates all fields
- **No retry for format:** Only retry on API errors, not parsing errors
- **Deterministic:** Same input → same output (temperature=0.1)

**Cost Calculation:**
```python
# Average website: 8000 chars cleaned text
# Tokens: 8000 chars ÷ 4 chars/token ≈ 2000 tokens input
# Output: ~500 tokens (structured JSON)

# Cost per extraction:
input_cost = 2000 tokens × $0.15 / 1M = $0.0003
output_cost = 500 tokens × $0.60 / 1M = $0.0003
total_per_extraction = $0.0006

# 150 practices:
150 × $0.0006 = $0.09

# With retries (10% fail → 15 retries):
165 × $0.0006 = $0.10 total
```

**Retry Logic:**
- Use `@retry_api_call()` decorator from FEAT-000
- Max 2 attempts with 5s fixed wait
- Retry on: Rate limit (429), timeout, network error
- Don't retry: Invalid API key (401), quota exceeded (429 with specific message)
- Log estimated cost on retry

**Error Handling:**
- Rate limit (429) → Wait 5s, retry
- Timeout → Retry once, then fail
- Invalid response (should never happen with structured outputs) → Log error, skip
- Validation error → Log error, skip

**Dependencies:**
- `openai==1.54.3`
- `tiktoken==0.8.0` (token counting)
- `FEAT-000` RetryHandler (@retry_api_call)
- `FEAT-000` VetPracticeExtraction model

**Uncertainty:**
- ❓ Should we implement streaming for large websites? (Recommendation: No, structured outputs don't support streaming)
- ❓ Should we use function calling instead of structured outputs? (Recommendation: No, structured outputs are newer and better)
- ❓ Should we validate extraction quality (e.g., confidence threshold)? (Recommendation: Yes, flag low-confidence for human review)

#### 3. Enrichment Orchestrator (enrichment_orchestrator.py)

**Purpose:** Coordinate website scraping, LLM extraction, and Notion updates

**Key Class:**
```python
class EnrichmentOrchestrator:
    def __init__(
        self,
        website_scraper: WebsiteScraper,
        llm_extractor: LLMExtractor,
        notion_client: NotionClient,
        error_tracker: ErrorAggregator
    ):
        self.website_scraper = website_scraper
        self.llm_extractor = llm_extractor
        self.notion_client = notion_client
        self.error_tracker = error_tracker

    async def enrich_all_practices(self, test_mode: bool = False) -> Dict[str, int]:
        """
        Enrich all practices with website data.

        Process:
        1. Query Notion for practices with websites (enrichment_status != "completed")
        2. Batch scrape websites (5 concurrent)
        3. Extract data with LLM for each successful scrape
        4. Update Notion records with enrichment data
        5. Track errors and generate summary

        Args:
            test_mode: If True, limit to 10 practices

        Returns:
            {
                "total": 150,
                "scraped": 145,
                "scrape_failed": 5,
                "extracted": 142,
                "extraction_failed": 3,
                "notion_updated": 142,
                "notion_failed": 0
            }
        """
```

**Orchestration Flow:**

1. **Query Notion for practices to enrich:**
```python
# Get all practices with websites that haven't been enriched
practices = notion_client.query_practices_for_enrichment(
    filter={
        "and": [
            {"property": "Website", "url": {"is_not_empty": True}},
            {"property": "Enrichment Status", "select": {"does_not_equal": "Completed"}}
        ]
    }
)
# Returns ~150 practices (or 10 in test mode)
```

2. **Batch scrape websites:**
```python
# Split into batches of 5 (concurrent limit)
website_batches = [practices[i:i+5] for i in range(0, len(practices), 5)]

all_scraped_data = []
for batch in website_batches:
    scraped = await website_scraper.scrape_batch([p.website for p in batch])
    all_scraped_data.extend(scraped)
# Total time: 150 ÷ 5 × 11s = 5.5 minutes
```

3. **Extract data with LLM:**
```python
extracted_data = []
for website_data in all_scraped_data:
    if not website_data.success:
        error_tracker.log_error("website_timeout", website_data.error_message, website_data.practice_name)
        continue

    try:
        extraction = llm_extractor.extract_practice_data(website_data)
        extracted_data.append(extraction)
    except LLMExtractionError as e:
        error_tracker.log_error("llm_extraction", str(e), website_data.practice_name)
# Total time: 150 × 0.5s (LLM latency) = 75s = 1.25 minutes
```

4. **Update Notion records:**
```python
for extraction in extracted_data:
    try:
        notion_client.update_practice_enrichment(
            practice_id=extraction.notion_page_id,
            enrichment_data=extraction
        )
    except NotionAPIError as e:
        error_tracker.log_error("notion_push", str(e), extraction.practice_name)
# Total time: 150 × 0.35s (rate limit) = 52.5s
```

5. **Total pipeline time:** 5.5 min (scraping) + 1.25 min (LLM) + 0.9 min (Notion) = **7.65 minutes**

**Error Recovery:**
- Scrape failures: Continue with remaining practices
- LLM failures: Continue with remaining practices
- Notion failures: Retry 3x, then continue
- Final error summary shows all categorized failures

**Dependencies:**
- `FEAT-000` NotionClient, ErrorAggregator, Logger
- `FEAT-001` (Notion database must have practices)

**Uncertainty:**
- ❓ Should we implement checkpointing (resume from failure)? (Recommendation: Phase 2, not critical for 8-minute pipeline)
- ❓ Should we batch LLM calls to OpenAI? (Recommendation: No, OpenAI doesn't support batch structured outputs yet)

#### 4. Notion Enrichment Update (extends NotionClient)

**Purpose:** Update existing Notion records with enrichment data

**New Method:**
```python
class NotionClient:
    def update_practice_enrichment(
        self,
        page_id: str,
        enrichment_data: VetPracticeExtraction
    ) -> None:
        """
        Update existing Notion record with enrichment data.

        Preserves:
        - All sales workflow fields (Status, Assigned To, etc.)
        - Core data from FEAT-001 (Practice Name, Address, etc.)
        - Scoring data (will be updated by FEAT-003)

        Updates:
        - Vet count fields
        - Decision maker fields
        - Service fields
        - Technology fields
        - Personalization context
        - Enrichment status → "Completed"
        """
```

**Field Mappings (VetPracticeExtraction → Notion):**

| Extracted Field | Notion Property | Type |
|----------------|----------------|------|
| `vet_count_total` | "Confirmed Vet Count (Total)" | number |
| `vet_count_confidence` | "Vet Count Confidence" | select |
| `decision_maker.name` | "Decision Maker Name" | rich_text |
| `decision_maker.role` | "Decision Maker Role" | select |
| `decision_maker.email` | "Decision Maker Email" | email |
| `decision_maker.phone` | "Decision Maker Phone" | phone_number |
| `emergency_24_7` | "24/7 Emergency Services" | checkbox |
| `specialty_services` | "Specialty Services" | multi_select |
| `wellness_programs` | "Wellness Programs" | checkbox |
| `boarding_services` | "Boarding Services" | checkbox |
| `online_booking` | "Online Booking" | checkbox |
| `telemedicine` | "Telemedicine" | checkbox |
| `patient_portal` | "Patient Portal" | checkbox |
| `digital_records_mentioned` | "Digital Records Mentioned" | checkbox |
| `personalization_context` | "Personalization Context" | multi_select |
| `awards_accreditations` | "Awards/Accreditations" | multi_select |
| `unique_services` | "Unique Services" | multi_select |
| `extraction_timestamp` | "Last Enrichment Date" | date |
| N/A | "Enrichment Status" | select → "Completed" |

**Preserved Fields (Never Overwrite):**
```python
PRESERVE_FIELDS = [
    "Status",
    "Assigned To",
    "Research Notes",
    "Call Notes",
    "Last Contact Date",
    "Next Follow-Up Date",
    "Campaign",
    "Practice Name",  # From FEAT-001
    "Address",        # From FEAT-001
    "Phone",          # From FEAT-001
    "Google Place ID" # From FEAT-001
]
```

**Dependencies:**
- `FEAT-000` NotionClient base class
- `FEAT-000` VetPracticeExtraction model
- `notion-client==2.2.1`

### Data Flow

```
1. Query Notion for Unenriched Practices
   notion_client = NotionClient(config.notion)
   practices = notion_client.query_practices_for_enrichment(test_mode=test_mode)
   # Returns 150 practices with websites (or 10 in test mode)

2. Scrape Websites (Async, 5 Concurrent)
   website_scraper = WebsiteScraper(config.website_scraping)
   scraped_data = await website_scraper.scrape_batch([p.website for p in practices])
   # Returns 145 successful scrapes, 5 timeouts (5.5 minutes)

3. Extract Data with LLM
   llm_extractor = LLMExtractor(config.website_scraping)
   extracted_data = []
   for website_data in scraped_data:
       if website_data.success:
           extraction = llm_extractor.extract_practice_data(website_data)
           extracted_data.append(extraction)
   # Returns 142 successful extractions, 3 LLM failures (1.25 minutes)

4. Update Notion Records
   for extraction in extracted_data:
       notion_client.update_practice_enrichment(
           page_id=extraction.notion_page_id,
           enrichment_data=extraction
       )
   # Updates 142 records, 0 failures (0.9 minutes)

5. Error Summary
   error_tracker.print_summary()
   # Shows: 5 website timeouts, 3 LLM failures
```

### Configuration

**config.json additions:**
```json
{
  "website_scraping": {
    "max_concurrent": 5,
    "timeout_seconds": 30,
    "retry_attempts": 2,
    "extraction_prompt_file": "config/website_extraction_prompt.txt",
    "cache_enabled": true,
    "cache_directory": "data/website_cache"
  }
}
```

**.env additions:**
```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxx
```

### Testing Strategy

**Unit Tests:**
- ✅ WebsiteScraper parses HTML correctly
- ✅ LLMExtractor validates Pydantic schema
- ✅ Extraction prompt produces expected output (mock OpenAI)
- ✅ NotionClient updates enrichment fields correctly
- ✅ Error tracking categorizes failures

**Integration Tests:**
- ✅ Full pipeline: Scrape → Extract → Update Notion (test mode, 10 practices)
- ✅ Error handling: Mock timeout, verify retry logic
- ✅ Confidence levels: Verify high/medium/low flagged correctly

**Mock Data:**
```python
# tests/fixtures/website_sample.html
<html>
  <body>
    <h1>Boston Veterinary Clinic</h1>
    <h2>Our Team</h2>
    <ul>
      <li>Dr. Jane Smith, DVM (Owner)</li>
      <li>Dr. John Doe, DVM</li>
      <li>Dr. Mary Johnson, DVM</li>
    </ul>
    <p>We offer 24/7 emergency services...</p>
    <p>Book appointments online...</p>
  </body>
</html>
```

**Manual Testing Checklist:**
1. Run with `--test` flag, verify exactly 10 practices enriched
2. Check Notion records for correct field mappings
3. Verify sales workflow fields not overwritten
4. Check error summary shows categorized failures
5. Verify low-confidence extractions flagged

### Acceptance Criteria

1. ✅ 150 practices enriched within 8 minutes (or 10 in test mode)
2. ✅ Scraping success rate ≥95% (≤7 timeouts)
3. ✅ LLM extraction success rate ≥97% (≤5 failures)
4. ✅ Notion updates succeed for all extracted data
5. ✅ Sales workflow fields preserved (Status, Assigned To, etc.)
6. ✅ Confidence levels captured (high/medium/low)
7. ✅ Test mode (`--test` flag) limits to 10 practices
8. ✅ Error tracking aggregates website, LLM, and Notion failures
9. ✅ Cost: ≤$0.30 (OpenAI $0.10 + buffer)

### Dependencies

**Python Packages:**
```
crawl4ai==0.3.74
openai==1.54.3
tiktoken==0.8.0
notion-client==2.2.1
pydantic==2.9.2
tenacity==9.0.0
```

**External APIs:**
- OpenAI: gpt-4o-mini with structured outputs
- Notion: Database `2a0edda2a9a081d98dc9daa43c65e744`

**Feature Dependencies:**
- **Depends on:** FEAT-000 (Models, RetryHandler, Logger, ErrorTracker), FEAT-001 (Notion database populated)
- **Depended on by:** FEAT-003 (uses enrichment data for scoring)

### Cost

**Crawl4AI:** $0 (local, no API costs)

**OpenAI:** $0.15/1M input + $0.60/1M output
- 150 practices × 2000 input tokens × $0.15/1M = $0.045
- 150 practices × 500 output tokens × $0.60/1M = $0.045
- Retries (10%): +$0.009
- **Total:** **$0.10**

**Notion:** $0 (free tier)

**Total Cost:** **$0.10**

### Timeline Estimate

**4 hours** to implement and test:
- Hour 1: WebsiteScraper + Crawl4AI integration
- Hour 2: LLMExtractor + structured outputs
- Hour 3: EnrichmentOrchestrator + Notion updates
- Hour 4: Integration testing + error handling

## Open Questions & Uncertainties

### Website Scraping
- ❓ **Scrape depth?** Homepage only or also /about and /team pages?
  - **Recommendation:** Homepage only for MVP (most info is there)
  - **Rationale:** Reduces complexity, time, cost

- ❓ **Cache scraped HTML?** Save to disk to avoid re-scraping?
  - **Recommendation:** Yes, in `data/website_cache/`
  - **Rationale:** Helpful during development, negligible storage cost

- ❓ **JavaScript-heavy sites?** Special handling needed?
  - **Recommendation:** Crawl4AI magic mode handles most cases
  - **Rationale:** Modern sites render in headless browser

### LLM Extraction
- ❓ **Streaming?** Use streaming for large websites?
  - **Recommendation:** No, structured outputs don't support streaming
  - **Rationale:** Structured outputs require full response

- ❓ **Function calling?** Use function calling instead of structured outputs?
  - **Recommendation:** No, structured outputs are newer and better
  - **Rationale:** Guaranteed valid JSON, no parsing errors

- ❓ **Quality validation?** Validate extraction quality (confidence threshold)?
  - **Recommendation:** Yes, flag low-confidence for human review
  - **Rationale:** Business may want to double-check uncertain data

### Orchestration
- ❓ **Checkpointing?** Resume from failure mid-pipeline?
  - **Recommendation:** Phase 2 (not critical for 8-minute pipeline)
  - **Rationale:** Adds complexity, pipeline is fast enough to re-run

- ❓ **Batch LLM calls?** Send multiple extractions per API call?
  - **Recommendation:** No, OpenAI doesn't support batch structured outputs
  - **Rationale:** API limitation

### Notion
- ❓ **Enrichment status field?** Add "Pending", "In Progress", "Completed" states?
  - **Recommendation:** Yes, helps track pipeline progress
  - **Rationale:** Easy to query for incomplete enrichments

## Implementation Notes

### Critical Path
1. WebsiteScraper + Crawl4AI integration (depends on FEAT-000 RetryHandler)
2. VetPracticeExtraction Pydantic model (in FEAT-000 models/)
3. LLMExtractor + OpenAI structured outputs
4. NotionClient.update_practice_enrichment() (extends FEAT-000)
5. EnrichmentOrchestrator (wire all components)

### Sequence
```
Day 1 (4 hours):
  Hour 1: WebsiteScraper + Crawl4AI
  Hour 2: LLMExtractor + structured outputs
  Hour 3: Orchestrator + Notion updates
  Hour 4: Testing + error handling
```

### Gotchas
1. **Crawl4AI async:** Must use `async/await`, not synchronous code
2. **OpenAI structured outputs:** Requires Pydantic v2, not v1
3. **Token counting:** Use tiktoken for accurate cost estimation
4. **Notion rate limiting:** Still applies to updates, not just creates
5. **Confidence levels:** Must be captured, not ignored (flag for review)
6. **Sales field preservation:** Must read existing record before update

## Success Metrics

**Definition of Done:**
- 150 practices enriched within 8 minutes (or 10 in test mode)
- Scraping success rate ≥95%
- LLM extraction success rate ≥97%
- All Notion records updated correctly
- Sales workflow fields preserved
- Confidence levels captured
- Test mode functional
- Error tracking shows categorized failures
- Cost ≤$0.30

**Quality Bar:**
- 80%+ test coverage on core logic
- Integration test passes with real APIs
- Retry logic tested with mock failures
- No unhandled exceptions

## Future Enhancements (Phase 2+)

- Scrape /about and /team pages for more data
- Image analysis (OCR for vet names, logo extraction)
- Review sentiment analysis
- Email validation/verification
- Deep link analysis (services pages)
- Checkpointing (resume from failure)
- Advanced caching strategies
- Quality scoring (confidence thresholds)

---

**Dependencies:**
- **Depends on:** FEAT-000 (Shared Infrastructure), FEAT-001 (Notion database populated)
- **Depended on by:** FEAT-003 (Lead Scoring uses enrichment data)

**Related Documents:**
- [FEAT-000 PRD](../FEAT-000_shared-infrastructure/prd.md) - Shared infrastructure
- [FEAT-001 PRD](../FEAT-001_google-maps-notion/prd.md) - Google Maps scraping
- [docs/system/integrations.md](../../system/integrations.md) - OpenAI, Crawl4AI details
- [docs/system/database.md](../../system/database.md) - Notion schema
- [docs/system/architecture.md](../../system/architecture.md) - Pipeline architecture
