# Product Requirements Document: Website Enrichment & LLM Extraction

**Feature ID:** FEAT-002
**Feature Name:** Website Enrichment & LLM Extraction
**Priority:** P0 (Critical - Core enrichment)
**Status:** Planning
**Owner:** Development Team
**Created:** 2025-11-03

## Executive Summary

Scrape veterinary practice websites using Crawl4AI deep crawling (multi-page: homepage + /about + /team), extract structured data using OpenAI GPT-4o-mini with structured outputs, and update existing Notion records with enrichment data. This feature adds critical ICP fit signals: vet count, decision makers, services, technology indicators, and personalization context. Includes cost tracking with $1.00 abort threshold and automatic triggering of FEAT-003 scoring.

**Success Metric:** 150 practices enriched with structured data within 12-14 minutes, cost ≤$0.50, with automatic ICP scoring.

## Problem Statement

Without website enrichment:
- Can't determine practice size (solo vs multi-vet)
- Can't identify decision makers (owner names, emails)
- Can't detect high-value indicators (24/7, specialties, advanced tech)
- Can't personalize outreach (no context about practice)
- Scoring based only on Google Maps data (incomplete ICP fit)

## Goals & Non-Goals

### Goals
✅ Scrape 150 practice websites with multi-page deep crawling (homepage + /about + /team pages)
✅ Use Crawl4AI BFSDeepCrawlStrategy with URL pattern filtering for targeted page discovery
✅ Extract structured data using OpenAI GPT-4o-mini with Pydantic structured outputs (100% schema compliance)
✅ Capture: vet count, decision maker info (explicitly found emails only, no guessing), services, technology, personalization context
✅ Handle extraction confidence levels (high/medium/low), accept all extractions with flagging
✅ Implement cost tracking with tiktoken, abort if exceeds $1.00 threshold
✅ Retry transient failures (timeout, rate limits) once at end of batch
✅ Update existing Notion records (preserve sales workflow fields automatically)
✅ Re-enrich only practices with last enrichment >30 days old
✅ Cache scraped HTML to `data/website_cache/` for faster development iteration
✅ Automatically trigger FEAT-003 scoring after successful enrichment (configurable)
✅ Comprehensive error tracking (timeout, LLM failures, validation errors, cost overruns)

### Non-Goals
❌ ICP fit scoring calculation (FEAT-003 handles this, but FEAT-002 triggers it)
❌ LinkedIn enrichment (Phase 2)
❌ Email validation/verification (no SMTP checks)
❌ Email pattern guessing (only explicitly found emails)
❌ Deep link analysis beyond /about and /team pages
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
│  1. Query Notion for practices needing enrichment           │
│     ├─ Filter: website != null                             │
│     └─ AND (enrichment_status != done OR last_enriched >30d│
│                                                             │
│  2. Crawl4AI: Multi-page deep crawling                      │
│     ├─ BFSDeepCrawlStrategy (max_depth=1, max_pages=5)     │
│     ├─ URL pattern filter: *about*, *team*, *contact*      │
│     ├─ 5 concurrent browser tabs                           │
│     ├─ 30s timeout per page                                │
│     ├─ Magic mode (smart content extraction)               │
│     ├─ Cache to data/website_cache/                        │
│     └─ Output: List[WebsiteData] per practice              │
│                                                             │
│  3. OpenAI GPT-4o-mini: Structured extraction               │
│     ├─ CostTracker checks budget before each call          │
│     ├─ tiktoken counts tokens (input + estimated output)   │
│     ├─ Abort if cumulative cost > $1.00                    │
│     ├─ Input: All pages concatenated + extraction prompt   │
│     ├─ Output: Pydantic VetPracticeExtraction (100% valid) │
│     ├─ Temperature=0.1 for deterministic extraction        │
│     └─ Extract: vets, decision maker, services, tech, etc. │
│                                                             │
│  4. Update Notion records                                   │
│     ├─ Partial update (only enrichment fields)             │
│     ├─ Sales fields auto-preserved by Notion API           │
│     └─ Set enrichment_status = "Completed"                 │
│                                                             │
│  5. Retry failures (end of batch)                           │
│     ├─ Retry all scrape/LLM failures once                  │
│     └─ Log persistent failures to Notion                   │
│                                                             │
│  6. Trigger FEAT-003 scoring (if enabled)                   │
│     ├─ For each successfully enriched practice             │
│     ├─ Call ScoringService.calculate_icp_score()           │
│     └─ Update Notion with ICP score (0-120 points)         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Component Details

#### 1. Website Scraper (website_scraper.py)

**Purpose:** Multi-page async scraping of practice websites using Crawl4AI deep crawling

**Key Class:**
```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter

class WebsiteScraper:
    def __init__(self, config: WebsiteScrapingConfig):
        self.browser_config = BrowserConfig(
            browser_type="chromium",
            headless=True,
            viewport_width=1920,
            viewport_height=1080,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )

        # Deep crawl strategy for multi-page scraping
        self.deep_crawl_strategy = BFSDeepCrawlStrategy(
            max_depth=1,                    # Homepage (0) + 1 level (sub-pages)
            include_external=False,          # Stay within same domain
            max_pages=5,                     # Homepage + up to 4 sub-pages
            filter_chain=FilterChain([
                URLPatternFilter(patterns=[
                    "*about*",
                    "*team*",
                    "*staff*",
                    "*contact*",
                    "*our-team*",
                    "*meet-the*"
                ])
            ])
        )

        self.crawler_config = CrawlerRunConfig(
            deep_crawl_strategy=self.deep_crawl_strategy,
            wait_for="networkidle",
            page_timeout=30000,              # 30s timeout per page
            delay_before_return_html=2.0,
            magic=True,                      # Smart content extraction
            cache_mode=CacheMode.ENABLED,    # Cache to data/website_cache/
            stream=False                     # Batch mode (collect all results)
        )
        self.max_concurrent = 5

    async def scrape_multi_page(
        self,
        homepage_url: HttpUrl,
        practice_name: str
    ) -> List[WebsiteData]:
        """
        Scrape homepage and related pages (about, team) for a single practice.

        Args:
            homepage_url: Practice website homepage
            practice_name: Practice name for logging

        Returns:
            List of WebsiteData objects (1 per page scraped, typically 2-4 pages)

        Raises:
            WebsiteTimeoutError: If any page exceeds 30s timeout
            WebsiteConnectionError: If site unreachable
        """
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            results = await crawler.arun(homepage_url, config=self.crawler_config)

            # Convert CrawlResult objects to WebsiteData
            website_data_list = []
            for result in results:
                if result.success:
                    website_data_list.append(WebsiteData(
                        url=result.url,
                        practice_name=practice_name,
                        html_content=result.html,
                        cleaned_text=result.cleaned_html or result.markdown,
                        success=True,
                        scraped_at=datetime.utcnow(),
                        page_title=result.metadata.get("title"),
                        meta_description=result.metadata.get("description"),
                        depth=result.metadata.get("depth", 0)
                    ))
                else:
                    website_data_list.append(WebsiteData(
                        url=result.url,
                        practice_name=practice_name,
                        success=False,
                        error_message=result.error_message,
                        scraped_at=datetime.utcnow()
                    ))

            return website_data_list
```

**Crawl4AI Deep Crawling Configuration:**
- **Strategy:** BFSDeepCrawlStrategy (Breadth-First Search)
- **max_depth:** 1 (homepage + 1 level of internal links)
- **max_pages:** 5 (homepage + up to 4 sub-pages: about, team, contact, etc.)
- **include_external:** False (stay within practice's domain)
- **URL pattern filter:** `*about*`, `*team*`, `*staff*`, `*contact*`, `*our-team*`, `*meet-the*`
- **Browser:** Chromium (headless)
- **Concurrency:** 5 concurrent practices (not 5 pages, 5 entire practice websites)
- **Timeout:** 30s per page
- **Magic mode:** Smart content extraction (removes nav, footer, ads)
- **Cache mode:** ENABLED (cache to `data/website_cache/` for dev iteration)
- **Stream mode:** False (batch mode, collect all pages before returning)

**Output Model:**
```python
class WebsiteData(BaseModel):
    url: HttpUrl
    practice_name: str
    html_content: str = ""
    cleaned_text: str = ""  # Magic mode output
    success: bool
    error_message: Optional[str] = None
    scraped_at: datetime
    page_title: Optional[str] = None
    meta_description: Optional[str] = None
    depth: int = 0  # 0=homepage, 1=sub-page
```

**Retry Logic:**
- **Individual page failures:** Continue with other pages (don't fail entire practice)
- **Entire practice failure:** Collect in failed_practices list
- **End-of-batch retry:** Retry all failed practices once
- **Persistent failures:** Log to Notion with error message

**Error Handling:**
- Timeout (>30s) → Mark page as failed, continue with other pages
- 404/403 → Log warning, mark as failed, continue
- SSL error → Log warning, mark as failed, continue
- Connection refused → Mark practice as failed, retry at end
- Invalid HTML → Log warning, mark as failed, continue

**Performance:**
- **Single practice:** ~15-20 seconds (homepage + 2-3 sub-pages)
- **5 concurrent practices:** 5 practices × 15s = 75s per batch
- **150 practices:** 150 ÷ 5 = 30 batches × 75s = **37.5 minutes** (but with parallelization, ~10-12 min)
- **Pages per practice:** Average 2.5 pages (homepage + 1-2 sub-pages found)
- **Total pages scraped:** ~375 pages for 150 practices

**Dependencies:**
- `crawl4ai==0.3.74`
- `FEAT-000` ConfigLoader, Logger, RetryHandler
- `FEAT-000` WebsiteData model (updated with `depth` field)

**User Decisions Implemented:**
- ✅ Multi-page scraping (Decision #1: homepage + /about + /team)
- ✅ Caching enabled (Decision #5: cache to data/website_cache/)
- ✅ Flexible with partial failures (Decision #6: continue if some pages fail)

#### 2. LLM Extractor (llm_extractor.py)

**Purpose:** Extract structured data from website HTML using OpenAI GPT-4o-mini

**Key Class:**
```python
import tiktoken
from openai import OpenAI

class LLMExtractor:
    def __init__(self, config: WebsiteScrapingConfig, cost_tracker: CostTracker):
        self.client = OpenAI(api_key=config.openai_api_key)
        self.model = "gpt-4o-mini"
        self.extraction_prompt = self._load_extraction_prompt()
        self.cost_tracker = cost_tracker
        self.encoding = tiktoken.encoding_for_model("gpt-4o-mini")  # o200k_base encoding

    def count_tokens(self, text: str) -> int:
        """Count tokens in text for gpt-4o-mini."""
        return len(self.encoding.encode(text))

    @retry_api_call()
    def extract_practice_data(
        self,
        website_pages: List[WebsiteData],
        practice_name: str
    ) -> VetPracticeExtraction:
        """
        Extract structured data from website pages using OpenAI structured outputs.

        Args:
            website_pages: List of scraped pages (homepage + sub-pages)
            practice_name: Practice name for logging

        Returns:
            VetPracticeExtraction Pydantic model (guaranteed valid)

        Raises:
            LLMExtractionError: If extraction fails after retries
            CostLimitExceeded: If cumulative cost exceeds threshold
        """
        # Concatenate all successful pages
        all_text = "\n\n--- PAGE BREAK ---\n\n".join([
            page.cleaned_text for page in website_pages if page.success
        ])

        # Truncate to 8000 chars (~2000 tokens) to avoid excessive costs
        truncated_text = all_text[:8000]

        # Count tokens and check budget BEFORE API call
        input_tokens = self.count_tokens(self.extraction_prompt + truncated_text)
        estimated_output_tokens = 500  # Typical structured output size
        estimated_cost = self.cost_tracker.estimate_cost(input_tokens, estimated_output_tokens)

        # Check budget - raises CostLimitExceeded if over threshold
        self.cost_tracker.check_budget(estimated_cost)

        # Make API call using beta.chat.completions.parse (structured outputs)
        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": self.extraction_prompt},
                {"role": "user", "content": truncated_text}
            ],
            response_format=VetPracticeExtraction,  # Pydantic model directly
            temperature=0.1,                         # Deterministic extraction
            max_tokens=2000
        )

        # Track actual cost
        actual_input_tokens = response.usage.prompt_tokens
        actual_output_tokens = response.usage.completion_tokens
        self.cost_tracker.track_call(actual_input_tokens, actual_output_tokens)

        logger.info(
            f"Extracted {practice_name}: "
            f"{actual_input_tokens} input + {actual_output_tokens} output tokens, "
            f"cost: ${self.cost_tracker.last_call_cost:.4f} "
            f"(total: ${self.cost_tracker.total_cost:.4f})"
        )

        return response.choices[0].message.parsed  # Returns Pydantic object
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

You will receive text from multiple pages (homepage, about, team) separated by "--- PAGE BREAK ---".
Analyze ALL pages together to extract the most complete information.

Focus on:
1. Number of veterinarians (search for "Our Team", "Meet the Vets", "Staff", team pages, bios)
2. Decision maker (owner, practice manager, medical director - name, role, contact info)
3. Services (emergency, specialty, wellness, surgery, dental, boarding)
4. Technology indicators (online booking, telemedicine, patient portal, digital records)
5. Personalization context (unique services, awards, community involvement, specialties)

CRITICAL RULES:
- If information is not found, return null or empty array (DO NOT GUESS OR HALLUCINATE)
- For vet_count_total, provide your confidence level (high/medium/low) based on evidence
- For decision maker email: ONLY include if explicitly shown on website (e.g., "Contact Dr. Smith at drsmith@clinic.com")
  - DO NOT guess email patterns (e.g., owner@domain.com, info@domain.com) - return null instead
- For decision maker phone: ONLY if explicitly associated with the person, not general clinic phone
- For personalization context:
  - Prefer SPECIFIC facts (e.g., "Opened 2nd location in Newton Oct 2024")
  - Accept 1-2 generic facts if that's all available (e.g., "Family-owned since 1985")
  - Return empty array if no useful context found
- For services, list all explicitly mentioned services (not assumed)
- For technology, note any modern tech features mentioned

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

**Design Decisions:**
- **No streaming:** Structured outputs don't support streaming (requires full response)
- **Structured outputs over function calling:** Guaranteed valid JSON, no parsing errors
- **Confidence validation:** Flag low-confidence extractions for human review (stored in Notion)

#### 3. Enrichment Orchestrator (enrichment_orchestrator.py)

**Purpose:** Coordinate multi-page scraping, LLM extraction, cost tracking, Notion updates, retry logic, and automatic scoring trigger

**Key Class:**
```python
from typing import Optional

class EnrichmentOrchestrator:
    def __init__(
        self,
        website_scraper: WebsiteScraper,
        llm_extractor: LLMExtractor,
        notion_client: NotionClient,
        error_tracker: ErrorAggregator,
        cost_tracker: CostTracker,
        scoring_service: Optional[ScoringService] = None,  # FEAT-003 dependency
        config: EnrichmentConfig
    ):
        self.website_scraper = website_scraper
        self.llm_extractor = llm_extractor
        self.notion_client = notion_client
        self.error_tracker = error_tracker
        self.cost_tracker = cost_tracker
        self.scoring_service = scoring_service
        self.config = config

    async def enrich_all_practices(self, test_mode: bool = False) -> Dict[str, Any]:
        """
        Enrich all practices with website data, with cost tracking and optional scoring.

        Process:
        1. Query Notion for practices needing enrichment (new or >30 days old)
        2. Scrape websites with multi-page deep crawling (5 concurrent practices)
        3. Extract data with LLM (with cost tracking and abort at $1.00)
        4. Update Notion records with enrichment data
        5. Retry all failures once at end of batch
        6. Trigger FEAT-003 scoring (if enabled and scoring_service provided)
        7. Generate error summary

        Args:
            test_mode: If True, limit to 10 practices

        Returns:
            {
                "total": 150,
                "scraped_successfully": 142,
                "scrape_failed_initial": 8,
                "scrape_failed_after_retry": 3,
                "extracted_successfully": 140,
                "extraction_failed": 2,
                "notion_updated": 140,
                "scored": 140,
                "total_cost": 0.38,
                "duration_minutes": 12.5
            }

        Raises:
            CostLimitExceeded: If cumulative cost exceeds $1.00 threshold
        """
```

**Orchestration Flow:**

1. **Query Notion for practices needing enrichment:**
```python
from datetime import datetime, timedelta

thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()

# Get practices with websites that need enrichment (new or stale)
practices = notion_client.query_practices_for_enrichment(
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
    },
    limit=10 if test_mode else None
)
# Returns ~150 practices (or 10 in test mode)
```

2. **Multi-page scraping (5 concurrent practices):**
```python
import asyncio

# Scrape 5 practices concurrently
scrape_results = {}
failed_practices = []

async def scrape_practice(practice):
    try:
        pages = await website_scraper.scrape_multi_page(practice.website, practice.name)
        return (practice, pages)
    except Exception as e:
        logger.error(f"Failed to scrape {practice.name}: {e}")
        return (practice, None)

# Process in batches of 5
for i in range(0, len(practices), 5):
    batch = practices[i:i+5]
    tasks = [scrape_practice(p) for p in batch]
    results = await asyncio.gather(*tasks)

    for practice, pages in results:
        if pages and any(p.success for p in pages):
            scrape_results[practice.page_id] = (practice, pages)
        else:
            failed_practices.append(practice)

# Total time: 150 ÷ 5 × ~2.5min per batch = ~12 minutes
```

3. **Extract data with LLM (with cost tracking):**
```python
extracted_data = []

for page_id, (practice, pages) in scrape_results.items():
    try:
        # Cost check happens inside extract_practice_data()
        extraction = llm_extractor.extract_practice_data(pages, practice.name)
        extraction.notion_page_id = page_id
        extracted_data.append(extraction)

    except CostLimitExceeded as e:
        logger.error(f"Cost limit exceeded: {e}")
        raise  # Abort entire pipeline

    except LLMExtractionError as e:
        error_tracker.log_error("llm_extraction", str(e), practice.name)
        failed_practices.append(practice)

# Log cost summary every 10 practices
if len(extracted_data) % 10 == 0:
    logger.info(f"Cost update: ${cost_tracker.total_cost:.4f} / ${cost_tracker.max_budget:.2f}")
```

4. **Update Notion records:**
```python
for extraction in extracted_data:
    try:
        notion_client.update_practice_enrichment(
            page_id=extraction.notion_page_id,
            enrichment_data=extraction
        )
    except NotionAPIError as e:
        error_tracker.log_error("notion_update", str(e), extraction.practice_name)
# Total time: 150 × 0.35s (rate limit) = ~1 minute
```

5. **Retry failures once:**
```python
if failed_practices:
    logger.info(f"Retrying {len(failed_practices)} failed practices...")

    retry_results = []
    for practice in failed_practices:
        try:
            pages = await website_scraper.scrape_multi_page(practice.website, practice.name)
            if pages and any(p.success for p in pages):
                extraction = llm_extractor.extract_practice_data(pages, practice.name)
                extraction.notion_page_id = practice.page_id
                retry_results.append(extraction)
        except Exception as e:
            # Log persistent failures to Notion
            notion_client.log_enrichment_failure(practice.page_id, str(e))
            error_tracker.log_error("persistent_failure", str(e), practice.name)

    # Update Notion with retry successes
    for extraction in retry_results:
        notion_client.update_practice_enrichment(extraction.notion_page_id, extraction)
```

6. **Trigger FEAT-003 scoring (if enabled):**
```python
if self.config.auto_trigger_scoring and self.scoring_service:
    scored_count = 0

    for extraction in extracted_data:
        try:
            score = await self.scoring_service.calculate_icp_score(
                practice_id=extraction.notion_page_id,
                enrichment_data=extraction
            )
            await notion_client.update_practice_score(extraction.notion_page_id, score)
            scored_count += 1
            logger.info(f"Scored {extraction.practice_name}: {score.total_score}/120")

        except ScoringError as e:
            logger.error(f"Scoring failed for {extraction.practice_name}: {e}")
            # Continue with next practice (don't fail entire pipeline)

    logger.info(f"Scoring complete: {scored_count}/{len(extracted_data)} practices scored")
```

7. **Total pipeline time:**
   - Scraping: ~10-12 minutes (multi-page, 5 concurrent)
   - LLM extraction: ~2 minutes (150 practices × 0.8s avg)
   - Notion updates: ~1 minute
   - Retry: ~1-2 minutes
   - Scoring: ~30 seconds (if enabled)
   - **Total: ~12-14 minutes**

**Error Recovery:**
- Individual page failures: Continue with other pages for same practice
- Practice-level failures: Collect and retry once at end
- LLM failures: Continue with remaining practices
- Cost limit exceeded: Abort immediately with clear error message
- Scoring failures: Log and continue (don't block enrichment)
- LLM failures: Continue with remaining practices
- Notion failures: Retry 3x, then continue
- Final error summary shows all categorized failures

**Dependencies:**
- `FEAT-000` NotionClient, ErrorAggregator, Logger
- `FEAT-001` (Notion database must have practices)

**Design Decisions:**
- **No checkpointing:** Pipeline is fast (12-14 min), can re-run if needed (defer to Phase 2)
- **No batch LLM calls:** OpenAI doesn't support batch structured outputs API limitation

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

**Execution & Performance:**
1. ✅ 150 practices enriched within 12-14 minutes (or 10 in test mode within 2 minutes)
2. ✅ Multi-page scraping: Average 2.5 pages per practice (homepage + 1-2 sub-pages)
3. ✅ Scraping success rate ≥95% after retry (≤8 total failures out of 150)
4. ✅ LLM extraction success rate ≥97% (≤5 failures)
5. ✅ Notion updates succeed for all extracted data

**Data Quality:**
6. ✅ Vet count detected for ≥60% of practices (multi-page improves from ~40%)
7. ✅ Decision maker name found for ≥50% of practices
8. ✅ Decision maker email found for ≥50% of practices (explicitly found only, no guessing)
9. ✅ Personalization context found for ≥70% of practices (1-3 facts, specific or generic)
10. ✅ Confidence levels captured for all vet_count extractions (high/medium/low)
11. ✅ Low-confidence extractions accepted and flagged (not rejected)

**System Behavior:**
12. ✅ Sales workflow fields preserved on update (Status, Assigned To, Call Notes, etc.)
13. ✅ Test mode (`--test` flag) limits to first 10 practices from Notion query
14. ✅ Re-enrichment only for practices with last_enriched_date > 30 days old
15. ✅ Caching enabled: Scraped HTML saved to `data/website_cache/`
16. ✅ Cost tracking: tiktoken counts tokens before each API call
17. ✅ Cost abort: Pipeline aborts if cumulative cost exceeds $1.00 threshold
18. ✅ Cost logging: Log cumulative cost every 10 practices
19. ✅ Retry logic: Failed practices retried once at end of batch
20. ✅ Persistent failures logged to Notion with error message

**Integration:**
21. ✅ Automatic scoring trigger: If `auto_trigger_scoring=true` and `scoring_service` provided, trigger FEAT-003 for each enriched practice
22. ✅ Scoring failures don't block enrichment: Log error and continue with next practice

**Error Handling:**
23. ✅ Error tracking aggregates: website failures, LLM failures, Notion failures, cost overruns
24. ✅ Individual page failures don't fail entire practice (continue with other pages)
25. ✅ Cost limit exceeded: Clear error message with total cost and practices enriched

**Cost:**
26. ✅ OpenAI cost: ≤$0.40 for 150 practices (actual cost, not original $0.10 estimate)
27. ✅ Total cost: ≤$0.50 including retries and buffer

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
- **Optional dependency:** FEAT-003 (automatic scoring trigger if enabled)
- **Depended on by:** FEAT-003 (uses enrichment data for scoring)

### FEAT-003 Integration (Automatic Scoring Trigger)

**Architecture:** Synchronous trigger with optional dependency injection

**Purpose:** After enriching a practice, automatically calculate and update its ICP fit score without requiring a separate pipeline run.

**Implementation Pattern:**

```python
from typing import Optional
from src.scoring.lead_scorer import ScoringService, ScoringError

class EnrichmentOrchestrator:
    def __init__(
        self,
        website_scraper: WebsiteScraper,
        llm_extractor: LLMExtractor,
        notion_client: NotionClient,
        error_tracker: ErrorAggregator,
        cost_tracker: CostTracker,
        scoring_service: Optional[ScoringService] = None,  # FEAT-003 integration
        config: EnrichmentConfig
    ):
        self.scoring_service = scoring_service
        self.config = config

    async def enrich_all_practices(self, test_mode: bool = False):
        # ... enrichment logic ...

        # 6. Trigger FEAT-003 scoring (if enabled)
        if self.config.auto_trigger_scoring and self.scoring_service:
            logger.info("Auto-triggering FEAT-003 scoring for enriched practices...")
            scored_count = 0
            scoring_failures = 0

            for extraction in extracted_data:
                try:
                    score = await self.scoring_service.calculate_icp_score(
                        practice_id=extraction.notion_page_id,
                        enrichment_data=extraction
                    )
                    await notion_client.update_practice_score(
                        extraction.notion_page_id,
                        score
                    )
                    scored_count += 1

                except ScoringError as e:
                    logger.error(f"Scoring failed for {extraction.practice_name}: {e}")
                    scoring_failures += 1
                    # Continue with next practice (don't fail entire pipeline)

            logger.info(f"Scoring complete: {scored_count} scored, {scoring_failures} failures")
        else:
            logger.info("Auto-scoring disabled or ScoringService not available")
```

**Configuration Flag:**

```json
// config/config.json
{
  "enrichment": {
    "auto_trigger_scoring": true  // Set to false to disable auto-scoring
  }
}
```

**Error Handling:**
- Scoring failures for individual practices don't block enrichment pipeline
- Failed scoring attempts logged to error tracker with `scoring_trigger` category
- Enrichment Status still set to "Completed" even if scoring fails
- Scoring can be re-run manually via FEAT-003 pipeline

**Benefits:**
- **Streamlined workflow:** Enrichment → Scoring → Ready for outreach happens automatically
- **No manual steps:** Sales team sees scored leads immediately
- **Graceful degradation:** Works with or without FEAT-003 implemented

**Trade-offs:**
- **Execution time:** Adds ~0.9 minutes to pipeline (total 13-15 minutes)
- **Dependency coupling:** Makes FEAT-002 dependent on FEAT-003 (mitigated by optional injection)
- **Error complexity:** Scoring failures need separate error handling

**Phase 1 Implementation:**
- First implementation of FEAT-002 won't have auto-trigger ready (FEAT-003 not implemented yet)
- `scoring_service=None` and `auto_trigger_scoring=false` by default
- Add auto-trigger in FEAT-002 v2 after FEAT-003 is complete

**Future Enhancement (Phase 2):**
- Refactor to asynchronous event bus if needed
- Publish "enrichment_completed" events, FEAT-003 subscribes
- Enables decoupling and horizontal scaling

### Cost

**Crawl4AI:** $0 (local, no API costs)

**OpenAI:** $0.15/1M input + $0.60/1M output (gpt-4o-mini)
- Multi-page scraping: ~2.5 pages per practice, ~4000 input tokens per extraction
- 150 practices × 4000 input tokens × $0.15/1M = $0.090
- 150 practices × 500 output tokens × $0.60/1M = $0.045
- Retries (5%): +$0.007
- Buffer (10%): +$0.014
- **Total:** **$0.40** (was $0.10 for homepage-only)

**Notion:** $0 (free tier)

**Total Cost:** **$0.50** (including buffer)
**Cost Threshold:** $1.00 (abort if exceeded)

### Timeline Estimate

**6 hours** to implement and test (updated from 4 hours due to multi-page scraping complexity):
- Hour 1-2: WebsiteScraper + Crawl4AI deep crawling + URL filtering
- Hour 2-3: LLMExtractor + structured outputs + CostTracker integration
- Hour 3-4: EnrichmentOrchestrator + retry logic + cost abort
- Hour 4-5: Notion updates + re-enrichment query + FEAT-003 trigger
- Hour 5-6: Integration testing + error handling + cost tracking validation

## User Decisions Resolved ✅

All implementation decisions have been made and documented. This feature is ready for `/plan FEAT-002` workflow.

**Decision Documentation:**
- **10 clarifying questions answered:** See `docs/features/FEAT-002_website-enrichment/user-decisions.md`
- **Technical research completed:** See `docs/features/FEAT-002_website-enrichment/research.md`
- **PRD updated to reflect scope:** This document (all sections updated)

**Key Decisions Summary:**

1. **Multi-page scraping** (homepage + /about + /team) - Quality over speed ✅
2. **Accept all extractions** - Flag with confidence level ✅
3. **No email guessing** - Only explicitly found emails ✅
4. **Flexible personalization** - Accept 1-2 generic facts if needed ✅
5. **Cache enabled** - Store to `data/website_cache/` for faster iteration ✅
6. **Retry failures** - One retry at end of batch, then log to Notion ✅
7. **Re-enrichment strategy** - Only practices > 30 days old ✅
8. **Test mode** - First 10 practices from Notion query ✅
9. **Cost tracking with abort** - $1.00 threshold, tiktoken monitoring ✅
10. **Auto-trigger scoring** - Synchronous FEAT-003 integration (optional) ✅

**Impact on Specifications:**
- **Execution time:** 12-14 minutes (was 8 minutes)
- **Cost:** $0.50 total (was $0.10)
- **Data quality:** 2-3x better decision maker detection
- **Email capture:** 50% rate (100% verified, no guessing)
- **Architecture:** BFSDeepCrawlStrategy, CostTracker, retry logic, scoring trigger

**No Open Questions Remaining** - All uncertainties resolved through research and user decisions.

## Implementation Notes

### Critical Path
1. **CostTracker class** (src/utils/cost_tracker.py) - Budget tracking with tiktoken
2. **WebsiteScraper + BFSDeepCrawlStrategy** - Multi-page crawling with URL filtering
3. **VetPracticeExtraction Pydantic model** (in FEAT-000 models/) - Updated for multi-page
4. **LLMExtractor with CostTracker** - Structured outputs + pre/post API cost checks
5. **EnrichmentOrchestrator** - Wire all components + retry + scoring trigger
6. **NotionClient.update_practice_enrichment()** - Re-enrichment query + field preservation

### Sequence
```
Day 1 (6 hours):
  Hour 1-2: CostTracker + WebsiteScraper + BFSDeepCrawlStrategy + URL filtering
  Hour 2-3: LLMExtractor + structured outputs + cost integration
  Hour 3-4: EnrichmentOrchestrator + retry logic + cost abort
  Hour 4-5: Notion query update + FEAT-003 trigger + field preservation
  Hour 5-6: Integration testing + cost tracking validation + error handling
```

### Gotchas
1. **Crawl4AI async:** Must use `async/await`, not synchronous code
2. **OpenAI structured outputs:** Requires Pydantic v2, not v1
3. **Token counting BEFORE API call:** Use tiktoken, check budget, then call API
4. **Cost abort is hard stop:** Pipeline aborts immediately at $1.00 threshold
5. **Multi-page concatenation:** Join pages with "--- PAGE BREAK ---" separator
6. **URL pattern filtering:** Use wildcards (*about*, *team*) not exact matches
7. **Re-enrichment query:** Must use OR condition (never enriched OR >30 days)
8. **Notion field preservation:** Automatic with partial updates, no read needed
9. **Confidence levels:** Must be captured and stored in Notion select field
10. **Scoring failures don't block:** Continue enrichment even if scoring fails

## Success Metrics

**Definition of Done:**
- 150 practices enriched within 12-14 minutes (or 10 in test mode within 1-2 min)
- Multi-page scraping: Average 2.5 pages per practice
- Scraping success rate ≥95% after retry
- LLM extraction success rate ≥97%
- All Notion records updated correctly with re-enrichment filter
- Sales workflow fields preserved (automatic partial updates)
- Confidence levels captured in Notion
- Cost tracking operational with $1.00 abort threshold
- FEAT-003 scoring trigger functional (if enabled)
- Test mode functional
- Error tracking shows categorized failures (scrape, LLM, notion, cost, scoring)
- Cost ≤$0.50

**Quality Bar:**
- 80%+ test coverage on core logic
- Integration test passes with real APIs
- Multi-page scraping tested with various site structures
- Cost tracking tested with mock token counts
- Cost abort tested (simulated threshold breach)
- Retry logic tested with mock failures
- Scoring trigger tested with mock ScoringService
- No unhandled exceptions

## Future Enhancements (Phase 2+)

- **Image analysis:** OCR for vet names on team photos, logo extraction
- **Review sentiment analysis:** Analyze Google reviews for pain points
- **Asynchronous event bus:** Decouple FEAT-002 and FEAT-003 with pub/sub
- **Deeper crawling:** max_depth=2 for larger sites (with cost controls)
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
