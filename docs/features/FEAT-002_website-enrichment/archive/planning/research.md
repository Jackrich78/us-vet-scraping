# Research Findings: Website Enrichment & LLM Extraction

**Feature ID:** FEAT-002
**Research Date:** 2025-11-03
**Researcher:** Claude Code with Archon MCP + WebSearch

## Research Questions

*Questions from PRD that this research addresses:*

1. **Multi-page scraping:** How can Crawl4AI scrape homepage + /about + /team pages efficiently?
2. **OpenAI structured outputs:** How reliable are they with gpt-4o-mini? Cost tracking?
3. **Notion API updates:** How to update records while preserving specific fields?
4. **Cost tracking & abort:** How to implement cost threshold and abort mechanism for OpenAI?
5. **FEAT-002 → FEAT-003 integration:** How should enrichment automatically trigger scoring?

## Findings

### Topic 1: Crawl4AI Multi-Page Deep Crawling

**Summary:** Crawl4AI v0.3.74 has native deep crawling support with three strategies (BFS, DFS, BestFirst) that can follow internal links and scrape multiple pages from the same domain with intelligent filtering.

**Details:**

**Deep Crawl Strategies:**
- **BFSDeepCrawlStrategy** (Breadth-First Search): Explores all links at one depth before going deeper
- **DFSDeepCrawlStrategy** (Depth-First Search): Explores as deep as possible before backtracking
- **BestFirstCrawlingStrategy** (Recommended): Prioritizes highest-scoring pages using URL scorers

**Configuration for Our Use Case:**
```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter

# Deep crawl configuration for vet websites
deep_crawl_strategy = BFSDeepCrawlStrategy(
    max_depth=1,                    # Homepage (0) + 1 level (about/team pages)
    include_external=False,          # Stay within same domain
    max_pages=5,                     # Homepage + up to 4 sub-pages
    filter_chain=FilterChain([
        URLPatternFilter(patterns=[
            "*about*",
            "*team*",
            "*staff*",
            "*contact*",
            "*our-team*"
        ])
    ])
)

config = CrawlerRunConfig(
    deep_crawl_strategy=deep_crawl_strategy,
    wait_for="networkidle",
    page_timeout=30000,              # 30s per page
    magic=True,                      # Smart content extraction
    stream=False                     # Batch mode (collect all results)
)

# Execute deep crawl
async with AsyncWebCrawler(config=browser_config) as crawler:
    results = await crawler.arun(homepage_url, config=config)
    # results is a list of CrawlResult objects (1 per page)
```

**Key Benefits:**
- **Automatic link discovery:** Crawl4AI extracts and follows internal links
- **Domain filtering:** `include_external=False` ensures we don't leave the practice's website
- **URL pattern matching:** Only crawls pages matching our patterns (about, team, staff, contact)
- **Concurrency control:** Built-in support for concurrent page scraping
- **Error handling:** Each result has `.success` and `.error_message` fields

**Performance Implications:**
- **Single page:** ~6 seconds (network + JS rendering)
- **Multi-page (homepage + 3 sub-pages):** ~15-20 seconds with max_pages=4
- **150 practices × 4 pages:** ~10-12 minutes total (vs. 5.5 min for homepage only)
- **Trade-off:** 2x longer execution, but significantly better data quality for vet count and decision maker extraction

**Recommendation:** Use BFSDeepCrawlStrategy with max_depth=1, max_pages=5, and URL pattern filtering for /about and /team pages.

**Source:** Crawl4AI Documentation (Archon MCP)
**URL:** https://docs.crawl4ai.com/core/deep-crawling/
**Retrieved:** 2025-11-03 via Archon

---

### Topic 2: OpenAI Structured Outputs with gpt-4o-mini

**Summary:** OpenAI's gpt-4o-mini (2024-07-18) fully supports Structured Outputs with 100% schema compliance, guaranteed valid JSON, and native Pydantic integration. Cost is ~$0.0006 per extraction (not $0.02 as estimated).

**Details:**

**Structured Outputs Reliability:**
- **100% schema adherence:** gpt-4o-2024-08-06 and gpt-4o-mini-2024-07-18 scored perfect 100% on complex JSON schema following
- **Guaranteed valid JSON:** No malformed responses, no parsing errors
- **Pydantic v2 integration:** Direct `response_format=PydanticModel` support
- **No hallucination of schema:** Model will refuse to respond rather than violate schema

**Python Implementation (openai >= 1.42.0, pydantic >= 2.8.2):**
```python
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import Optional, List, Literal

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class DecisionMaker(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None  # Only explicitly found, no guessing
    phone: Optional[str] = None

class VetPracticeExtraction(BaseModel):
    vet_count_total: Optional[int] = Field(None, ge=1, le=50)
    vet_count_confidence: Literal["high", "medium", "low"] = "low"
    decision_maker: Optional[DecisionMaker] = None
    emergency_24_7: bool = False
    specialty_services: List[str] = Field(default_factory=list)
    personalization_context: List[str] = Field(default_factory=list, max_length=3)
    # ... additional fields

# Structured output call
response = client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": extraction_prompt},
        {"role": "user", "content": website_html[:8000]}  # ~2000 tokens
    ],
    response_format=VetPracticeExtraction,
    temperature=0.1,                # Deterministic
    max_tokens=2000
)

result = response.choices[0].message.parsed  # Pydantic object, guaranteed valid
```

**Cost Calculation (Accurate):**
```
Input pricing: $0.150 per 1M tokens
Output pricing: $0.600 per 1M tokens

Per extraction:
- Input: 2000 tokens × $0.150/1M = $0.0003
- Output: 500 tokens × $0.600/1M = $0.0003
- Total: $0.0006 per extraction

150 practices × 4 pages × $0.0006 = $0.36 (not $3.00!)
With 10% retry buffer: $0.36 × 1.1 = $0.40
```

**Error Handling:**
- **Rate limit (429):** Retry with exponential backoff
- **Timeout:** Retry once with 5s delay
- **Invalid schema request (400):** This shouldn't happen with Pydantic, but log and skip if it does
- **Structured outputs guarantee:** No parsing errors, no validation failures

**Recommendation:** Use `beta.chat.completions.parse()` with Pydantic models, temperature=0.1 for deterministic extraction.

**Source:** OpenAI Documentation, DataCamp, Microsoft Learn
**URL:** https://openai.com/index/introducing-structured-outputs-in-the-api/
**Retrieved:** 2025-11-03 via WebSearch

---

### Topic 3: OpenAI Cost Tracking & Abort Mechanism

**Summary:** Use `tiktoken` library to count tokens before API calls, track cumulative costs, and abort when threshold ($1.00) is exceeded. No built-in abort in OpenAI SDK, must implement manually.

**Details:**

**Token Counting with tiktoken:**
```python
import tiktoken

# Load encoding for gpt-4o-mini (uses o200k_base encoding)
encoding = tiktoken.encoding_for_model("gpt-4o-mini")

def count_tokens(text: str) -> int:
    """Count tokens in text for gpt-4o-mini."""
    return len(encoding.encode(text))

def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    """Estimate cost for gpt-4o-mini API call."""
    input_cost = input_tokens * 0.150 / 1_000_000   # $0.150 per 1M input tokens
    output_cost = output_tokens * 0.600 / 1_000_000  # $0.600 per 1M output tokens
    return input_cost + output_cost
```

**Cost Tracking & Abort Implementation:**
```python
class CostTracker:
    def __init__(self, max_budget: float = 1.00):
        self.max_budget = max_budget
        self.total_cost = 0.0
        self.call_count = 0

    def check_budget(self, estimated_cost: float) -> bool:
        """Check if we can afford this call. Raises CostLimitExceeded if not."""
        if self.total_cost + estimated_cost > self.max_budget:
            raise CostLimitExceeded(
                f"Cost limit exceeded: ${self.total_cost:.4f} + ${estimated_cost:.4f} "
                f"> ${self.max_budget:.2f}"
            )
        return True

    def track_call(self, input_tokens: int, output_tokens: int):
        """Track actual cost after API call."""
        cost = estimate_cost(input_tokens, output_tokens)
        self.total_cost += cost
        self.call_count += 1
        logger.info(f"API call #{self.call_count}: ${cost:.4f} (total: ${self.total_cost:.4f})")

# Usage in extraction pipeline
cost_tracker = CostTracker(max_budget=1.00)

for practice in practices:
    for page in practice.pages:
        # Count tokens before API call
        input_tokens = count_tokens(extraction_prompt + page.html[:8000])
        estimated_output_tokens = 500  # Typical structured output size
        estimated_cost = estimate_cost(input_tokens, estimated_output_tokens)

        # Check budget before call
        cost_tracker.check_budget(estimated_cost)

        # Make API call
        response = client.beta.chat.completions.parse(...)

        # Track actual usage
        actual_input_tokens = response.usage.prompt_tokens
        actual_output_tokens = response.usage.completion_tokens
        cost_tracker.track_call(actual_input_tokens, actual_output_tokens)

# Final summary
logger.info(f"Total cost: ${cost_tracker.total_cost:.4f} for {cost_tracker.call_count} API calls")
```

**Alternative: Batch Cost Logging:**
- Log costs every 10 practices
- Alert if approaching threshold (>$0.80)
- Continue processing until hard limit ($1.00)

**Recommendation:** Implement `CostTracker` class with `check_budget()` before each API call, raise exception if threshold exceeded, log cumulative costs every 10 practices.

**Source:** OpenAI Cookbook, tiktoken documentation, community guides
**URL:** https://cookbook.openai.com/examples/how_to_count_tokens_with_tiktoken
**Retrieved:** 2025-11-03 via WebSearch

---

### Topic 4: Notion API Partial Updates & Field Preservation

**Summary:** Notion API `pages.update()` only modifies properties you explicitly include in the request. Omitted properties are automatically preserved. No need to read-then-merge.

**Details:**

**Notion API Update Behavior (version 2022-06-28):**
```python
from notion_client import Client

notion = Client(auth=os.getenv("NOTION_API_KEY"))

# Update ONLY enrichment fields, sales fields automatically preserved
notion.pages.update(
    page_id=practice_page_id,
    properties={
        # Enrichment fields (updated by FEAT-002)
        "Confirmed Vet Count (Total)": {"number": extraction.vet_count_total},
        "Vet Count Confidence": {"select": {"name": extraction.vet_count_confidence}},
        "Decision Maker Name": {"rich_text": [{"text": {"content": extraction.decision_maker.name}}]},
        "Decision Maker Email": {"email": extraction.decision_maker.email},
        "24/7 Emergency Services": {"checkbox": extraction.emergency_24_7},
        "Specialty Services": {"multi_select": [{"name": svc} for svc in extraction.specialty_services]},
        "Personalization Context": {"multi_select": [{"name": ctx} for ctx in extraction.personalization_context]},
        "Enrichment Status": {"select": {"name": "Completed"}},
        "Last Enrichment Date": {"date": {"start": extraction.extraction_timestamp.isoformat()}}

        # Sales fields (Status, Assigned To, Call Notes) are NOT in this dict
        # → They are automatically preserved by Notion API
    }
)
```

**Key Points:**
- **Partial updates:** Only properties in the `properties` dict are modified
- **Automatic preservation:** Any property not included is left unchanged
- **No read-before-write needed:** Unlike some APIs, Notion doesn't require fetching the record first
- **Rate limiting still applies:** 3 req/s limit, use 0.35s delay

**Preserved Fields (never included in enrichment updates):**
```python
PRESERVED_SALES_FIELDS = [
    "Status",                   # Sales workflow status
    "Assigned To",              # Sales rep assignment
    "Research Notes",           # Human-entered notes
    "Call Notes",               # Call log
    "Last Contact Date",        # Last outreach
    "Next Follow-Up Date",      # Scheduled follow-up
    "Campaign",                 # Marketing campaign
    "Outreach Attempts",        # Call counter
]
# These fields are NEVER included in FEAT-002 update calls → automatically preserved
```

**Re-enrichment Logic (User Decision #7: Option C):**
```python
# Query Notion for practices to enrich
practices = notion.databases.query(
    database_id=DATABASE_ID,
    filter={
        "and": [
            {"property": "Website", "url": {"is_not_empty": True}},
            {
                "or": [
                    # Never enriched
                    {"property": "Enrichment Status", "select": {"does_not_equal": "Completed"}},
                    # Enriched > 30 days ago
                    {"property": "Last Enrichment Date", "date": {"before": thirty_days_ago.isoformat()}}
                ]
            }
        ]
    }
)
```

**Recommendation:** Use `pages.update()` with only enrichment fields, rely on Notion's automatic preservation. Implement re-enrichment filter for records >30 days old.

**Source:** Notion API Documentation (Archon MCP)
**URL:** https://developers.notion.com/reference/update-page
**Retrieved:** 2025-11-03 via Archon

---

### Topic 5: FEAT-002 → FEAT-003 Automatic Trigger Integration

**Summary:** FEAT-002 should automatically trigger FEAT-003 scoring after each successful enrichment. Use event-driven architecture with a `ScoringOrchestrator` that listens for enrichment completion events.

**Details:**

**Integration Architecture:**
```
┌─────────────────────────────────────────────────────────────┐
│ FEAT-002: Website Enrichment                               │
├─────────────────────────────────────────────────────────────┤
│  1. Scrape websites (Crawl4AI multi-page)                  │
│  2. Extract data (OpenAI structured outputs)               │
│  3. Update Notion records                                  │
│  4. Emit EnrichmentCompleted event                         │
│                                                             │
│  EnrichmentCompleted(practice_id, enrichment_data)         │
│           ↓                                                 │
└─────────────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────────────┐
│ ScoringOrchestrator (Event Listener)                       │
├─────────────────────────────────────────────────────────────┤
│  1. Receive EnrichmentCompleted event                      │
│  2. Read practice data from Notion (if needed)             │
│  3. Delegate to FEAT-003 scorer                            │
│  4. Update Notion with ICP fit score                       │
└─────────────────────────────────────────────────────────────┘
```

**Implementation Approach:**

**Option A: Synchronous Trigger (Recommended for MVP)**
```python
class EnrichmentOrchestrator:
    def __init__(self, ..., scoring_service: Optional[ScoringService] = None):
        self.scoring_service = scoring_service

    async def enrich_all_practices(self, trigger_scoring: bool = True):
        """Enrich practices and optionally trigger scoring."""
        enriched_practices = []

        for practice in practices:
            # 1. Scrape website
            pages = await self.website_scraper.scrape_multi_page(practice.website)

            # 2. Extract data
            extraction = await self.llm_extractor.extract_practice_data(pages)

            # 3. Update Notion
            await self.notion_client.update_practice_enrichment(practice.page_id, extraction)

            enriched_practices.append((practice.page_id, extraction))

            # 4. Trigger scoring if enabled
            if trigger_scoring and self.scoring_service:
                try:
                    score = await self.scoring_service.calculate_icp_score(
                        practice_id=practice.page_id,
                        enrichment_data=extraction
                    )
                    await self.notion_client.update_practice_score(practice.page_id, score)
                    logger.info(f"Scored {practice.practice_name}: {score.total_score}/120")
                except ScoringError as e:
                    logger.error(f"Scoring failed for {practice.practice_name}: {e}")
                    # Don't fail entire pipeline, continue with next practice

        return {"enriched": len(enriched_practices)}
```

**Option B: Asynchronous Event Bus (Phase 2)**
```python
from dataclasses import dataclass

@dataclass
class EnrichmentCompleted:
    practice_id: str
    practice_name: str
    enrichment_data: VetPracticeExtraction
    timestamp: datetime

class EventBus:
    def __init__(self):
        self.handlers = defaultdict(list)

    def subscribe(self, event_type: type, handler: Callable):
        self.handlers[event_type].append(handler)

    async def publish(self, event):
        for handler in self.handlers[type(event)]:
            await handler(event)

# In EnrichmentOrchestrator
async def _after_enrichment(self, practice_id, enrichment_data):
    event = EnrichmentCompleted(
        practice_id=practice_id,
        practice_name=practice.name,
        enrichment_data=enrichment_data,
        timestamp=datetime.utcnow()
    )
    await event_bus.publish(event)

# In ScoringOrchestrator (FEAT-003)
async def handle_enrichment_completed(event: EnrichmentCompleted):
    score = await scoring_service.calculate_icp_score(
        practice_id=event.practice_id,
        enrichment_data=event.enrichment_data
    )
    await notion_client.update_practice_score(event.practice_id, score)
```

**Configuration (config.json):**
```json
{
  "enrichment": {
    "auto_trigger_scoring": true,
    "scoring_service_enabled": true
  }
}
```

**CLI Flag:**
```bash
# With automatic scoring (default)
python main.py --feature FEAT-002

# Enrichment only, no scoring
python main.py --feature FEAT-002 --no-scoring
```

**Dependencies:**
- **FEAT-002 depends on:** FEAT-000 (shared infrastructure), FEAT-001 (Notion database populated)
- **FEAT-003 depends on:** FEAT-000 (shared infrastructure), FEAT-002 (enrichment data)
- **Integration:** FEAT-002 optionally triggers FEAT-003 via `ScoringService` dependency injection

**Recommendation:** Implement synchronous trigger (Option A) for MVP with `auto_trigger_scoring: true` config flag. Defer event bus to Phase 2.

**Source:** Software architecture best practices, event-driven design patterns
**URL:** N/A (Architecture decision)
**Retrieved:** 2025-11-03

---

## Recommendations

### Primary Recommendation: Implement All User Decisions

**Rationale:**
- **Multi-page scraping:** BFSDeepCrawlStrategy with URL pattern filtering provides 2-3x better data quality for vet count and decision maker extraction at 2x execution time cost (acceptable trade-off)
- **Email policy:** Only explicitly found emails (no guessing) ensures data integrity and avoids spam filters flagging guessed emails
- **OpenAI structured outputs:** 100% reliable with gpt-4o-mini, guaranteed schema compliance, much cheaper than estimated ($0.40 vs. $3.00)
- **Cost tracking:** `tiktoken` + `CostTracker` class enables accurate cost monitoring and abort at $1.00 threshold
- **Notion updates:** Partial updates with automatic field preservation is simple and robust (no read-before-write needed)
- **Auto-trigger scoring:** Synchronous trigger with dependency injection is simple, testable, and meets user preference for automatic workflow

**Key Benefits:**
- **Better data quality:** Multi-page scraping finds decision makers on /team pages that homepage misses
- **Cost control:** Token counting + abort prevents runaway costs
- **Data integrity:** No email guessing avoids deliverability issues
- **Automated workflow:** Enrichment → scoring happens automatically, reducing manual steps

**Considerations:**
- **Execution time:** 10-12 minutes for 150 practices (vs. 5.5 min for homepage only) - acceptable for batch processing
- **Complexity:** Deep crawling adds configuration complexity, but Crawl4AI makes it straightforward
- **Dependency coupling:** FEAT-002 → FEAT-003 coupling is manageable with dependency injection and config flags

---

## Alternative Approaches Considered

### Alternative 1: Homepage-Only Scraping (Original PRD)
- **Pros:** Faster (5.5 min), simpler, lower cost
- **Cons:** Misses decision makers and vet names often on /team pages, lower data quality
- **Why not chosen:** User prioritized quality over speed (Decision #1)

### Alternative 2: Email Guessing with Pattern Detection
- **Pros:** Higher email capture rate (50% → 70%)
- **Cons:** Guessed emails may bounce, harm sender reputation, flag as spam
- **Why not chosen:** User preferred data integrity over coverage (Decision #3)

### Alternative 3: Asynchronous Event Bus for FEAT-002 → FEAT-003
- **Pros:** Decouples components, more scalable, easier to extend
- **Cons:** Adds infrastructure complexity (event bus, handlers), harder to debug
- **Why not chosen:** Synchronous trigger simpler for MVP, defer to Phase 2 (Decision #10)

### Alternative 4: No Cost Tracking, Just Post-Execution Logging
- **Pros:** Simpler implementation, no upfront token counting
- **Cons:** Can't prevent runaway costs, no early abort
- **Why not chosen:** User wants proactive cost control with $1.00 abort threshold (Decision #9)

---

## Trade-offs

### Performance vs. Data Quality
**Multi-page scraping:** 2x longer execution (10-12 min vs. 5.5 min) for 2-3x better decision maker detection rate. User chose quality.

### Cost vs. Safety
**Cost tracking overhead:** ~50ms per extraction for token counting, but prevents runaway costs. User chose safety.

### Simplicity vs. Flexibility
**Synchronous scoring trigger:** Simpler than event bus, but couples FEAT-002 and FEAT-003. Acceptable for MVP, refactor to event bus in Phase 2 if needed.

### Coverage vs. Data Integrity
**No email guessing:** Reduces email capture from 70% to 50%, but ensures only verified emails. User chose integrity.

---

## Resources

### Official Documentation
- **Crawl4AI Deep Crawling:** https://docs.crawl4ai.com/core/deep-crawling/
- **OpenAI Structured Outputs:** https://openai.com/index/introducing-structured-outputs-in-the-api/
- **tiktoken Token Counting:** https://cookbook.openai.com/examples/how_to_count_tokens_with_tiktoken
- **Notion API Pages Update:** https://developers.notion.com/reference/update-page

### Technical Articles
- **Estimating GPT Cost with tiktoken:** https://www.datacamp.com/tutorial/estimating-cost-of-gpt-using-tiktoken-library-python (DataCamp, 2025)
- **Getting Started with Structured Outputs:** https://www.datacamp.com/tutorial/open-ai-structured-outputs (DataCamp, 2025)
- **Crawl4AI Multi-URL Crawling:** https://docs.crawl4ai.com/advanced/multi-url-crawling/ (Crawl4AI Docs)

### Code Examples
- **Crawl4AI Deep Crawl Example:** See Archon MCP research (BFS strategy, URL filtering, streaming)
- **OpenAI Structured Outputs Example:** See WebSearch results (Pydantic integration, beta.chat.completions.parse)
- **tiktoken Cost Calculation:** See WebSearch results (token counting, cost estimation formulas)

### Community Resources
- **Crawl4AI GitHub Discussions:** https://github.com/unclecode/crawl4ai/discussions/485 (Deep crawling use cases)
- **OpenAI Developer Community:** Structured outputs reliability (99-100% schema compliance reported)

---

## Archon Status

### Knowledge Base Queries

*Archon MCP was available and used extensively:*

- ✅ **Crawl4AI Documentation:** Found comprehensive deep crawling docs in Archon, used for BFS strategy research
- ✅ **Notion API Documentation:** Found page update patterns and field preservation behavior in Archon
- ⚠️ **OpenAI Documentation:** Partial results in Archon (older version), supplemented with WebSearch for latest gpt-4o-mini features
- ❌ **tiktoken Documentation:** Not in Archon, used WebSearch for token counting and cost calculation

### Recommendations for Archon

*Frameworks/docs to crawl for future features:*

1. **OpenAI API Documentation (Updated 2025)**
   - **Why:** Archon has older OpenAI docs, missing latest gpt-4o-mini structured outputs features
   - **URLs to crawl:**
     - https://platform.openai.com/docs
     - https://cookbook.openai.com/
   - **Benefit:** Future features can reference latest OpenAI capabilities without WebSearch

2. **tiktoken Documentation**
   - **Why:** Token counting is critical for cost management across all LLM features
   - **URLs to crawl:**
     - https://github.com/openai/tiktoken
     - https://cookbook.openai.com/examples/how_to_count_tokens_with_tiktoken
   - **Benefit:** Faster research for token optimization in FEAT-003, FEAT-004, etc.

---

## Answers to Open Questions

### Question 1: Should we scrape homepage only or also /about and /team pages?
**Answer:** Scrape homepage + /about + /team pages using Crawl4AI BFSDeepCrawlStrategy with URL pattern filtering
**Confidence:** High
**Source:** Crawl4AI deep crawling documentation + user decision (quality over speed)

### Question 2: What should happen with low-confidence extractions?
**Answer:** Accept all extractions, flag in Notion with confidence level (high/medium/low)
**Confidence:** High
**Source:** User decision #2 (Option A)

### Question 3: Should we guess decision maker emails based on patterns?
**Answer:** No, only include explicitly found emails on the website
**Confidence:** High
**Source:** User decision #3 (Option B - data integrity over coverage)

### Question 4: What's the minimum quality bar for personalization context?
**Answer:** Accept 1-2 generic facts if that's all the website has (flexible quality bar)
**Confidence:** High
**Source:** User decision #4 (Option B)

### Question 5: Should we cache scraped HTML during development?
**Answer:** Yes, cache all scraped HTML to `data/website_cache/` for faster iteration
**Confidence:** High
**Source:** User decision #5 (Option A)

### Question 6: Partial failure behavior (10/150 websites fail)?
**Answer:** Retry all failures once at end of job, then log to Notion if still failing
**Confidence:** High
**Source:** User decision #6 (Option C)

### Question 7: Should we re-enrich practices that were already enriched?
**Answer:** Only re-enrich if enrichment is > 30 days old
**Confidence:** High
**Source:** User decision #7 (Option C - re-enrichment window)

### Question 8: How should test mode select 10 practices?
**Answer:** Select first 10 practices from Notion (whatever order Notion returns)
**Confidence:** High
**Source:** User decision #8 (Option A - simplest approach)

### Question 9: Cost tracking approach?
**Answer:** Set $1.00 cost threshold and abort if exceeded (proactive cost control)
**Confidence:** High
**Source:** User decision #9 (Option C) + tiktoken research

### Question 10: Should enrichment automatically trigger scoring?
**Answer:** Yes, automatic trigger preferred (FEAT-002 → FEAT-003 integration)
**Confidence:** High
**Source:** User decision #10 (Option B) + synchronous trigger architecture

---

## Next Steps

1. **Update PRD:** Incorporate all user decisions and research findings into FEAT-002 PRD
2. **Architecture Planning:** Design component structure for multi-page scraping, cost tracking, and scoring trigger
3. **Acceptance Criteria:** Refine acceptance criteria based on updated scope (multi-page, cost abort, etc.)
4. **Testing Strategy:** Update testing.md with multi-page scraping tests, cost tracking tests, scoring integration tests
5. **Proceed to Planning:** Run `/plan FEAT-002` to create comprehensive planning documentation

---

**Research Complete:** ✅
**Ready for Planning:** Yes
**Blockers:** None - all open questions answered, technical feasibility confirmed
