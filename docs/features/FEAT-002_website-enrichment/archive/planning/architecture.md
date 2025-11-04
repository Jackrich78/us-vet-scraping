# Architecture Decision: Website Enrichment & LLM Extraction

**Feature ID:** FEAT-002
**Decision Date:** 2025-11-03
**Status:** Accepted

## Context

FEAT-002 requires scraping veterinary practice websites to extract structured data (vet count, decision makers, services, technology indicators) using Crawl4AI and OpenAI GPT-4o-mini. The challenge is balancing data quality (multi-page scraping) with execution time, cost control (OpenAI API), and integration with FEAT-003 scoring. Constraints include $1.00 cost threshold, 12-14 minute execution time target, and re-enrichment strategy for stale data (>30 days old).

## Options Considered

### Option 1: Multi-Page Deep Crawling with Synchronous Orchestration

**Description:** Use Crawl4AI BFSDeepCrawlStrategy to scrape homepage + /about + /team pages (max 5 pages per practice), extract data using OpenAI structured outputs with tiktoken cost tracking, and update Notion records in batches with automatic FEAT-003 scoring trigger via synchronous dependency injection.

**⚠️ IMPLEMENTATION NOTE:** This architecture was validated via spike testing. All critical assumptions confirmed:
- Crawl4AI 0.7.6 BFSDeepCrawlStrategy works as specified
- tiktoken variance <1% for long texts (website content)
- OpenAI cost $0.000121 per extraction (93% under original estimate)
- Notion partial updates automatically preserve sales fields (no read-before-write needed)
- Re-enrichment query OR filter validated
See `spike-results.md` for complete validation details.

**Key Characteristics:**
- BFSDeepCrawlStrategy with URL pattern filtering (*about*, *team*, *staff*, *contact*)
- 5 concurrent practices (not 5 pages), max_depth=1, max_pages=5
- CostTracker class with tiktoken monitoring, abort at $1.00 threshold
- Synchronous scoring trigger via optional ScoringService injection
- Retry logic: failed practices retried once at end of batch
- Re-enrichment: only practices with last_enriched_date > 30 days old

**Example Implementation:**
```python
# WebsiteScraper with deep crawling
deep_crawl_strategy = BFSDeepCrawlStrategy(
    max_depth=1,
    include_external=False,
    max_pages=5,
    filter_chain=FilterChain([
        URLPatternFilter(patterns=["*about*", "*team*", "*staff*", "*contact*"])
    ])
)

# EnrichmentOrchestrator with scoring trigger
class EnrichmentOrchestrator:
    def __init__(self, ..., scoring_service: Optional[ScoringService] = None):
        self.scoring_service = scoring_service

    async def enrich_all_practices(self):
        # ... enrichment logic ...
        if self.config.auto_trigger_scoring and self.scoring_service:
            score = await self.scoring_service.calculate_icp_score(...)
            await notion_client.update_practice_score(...)
```

### Option 2: Homepage-Only Scraping with Async Event Bus

**Description:** Scrape only homepage (faster execution), use asynchronous event bus for FEAT-002 → FEAT-003 integration. Publish EnrichmentCompleted events, ScoringOrchestrator subscribes and processes asynchronously.

**Key Characteristics:**
- Single page scraping (homepage only), ~5.5 minutes execution
- Lower cost ($0.10 vs $0.40), fewer tokens per extraction
- Event bus decouples FEAT-002 and FEAT-003 components
- Asynchronous scoring (non-blocking pipeline)
- Lower data quality (misses /team pages with decision makers)

**Example Implementation:**
```python
# Event bus architecture
@dataclass
class EnrichmentCompleted:
    practice_id: str
    enrichment_data: VetPracticeExtraction

# Publisher (FEAT-002)
await event_bus.publish(EnrichmentCompleted(...))

# Subscriber (FEAT-003)
async def handle_enrichment_completed(event: EnrichmentCompleted):
    score = await scoring_service.calculate_icp_score(...)
```

### Option 3: Best-First Crawling with ML Page Scoring

**Description:** Use Crawl4AI BestFirstCrawlingStrategy with ML-based URL scorers to prioritize highest-value pages (e.g., /team scores higher than /contact). Dynamically adjust crawl depth based on page importance.

**Key Characteristics:**
- BestFirstCrawlingStrategy with custom URL scorers
- Adaptive crawling (stops when diminishing returns)
- Requires training ML model to score URLs
- More complex implementation, longer development time
- Potentially better data quality, but unpredictable execution time

**Example Implementation:**
```python
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy

# Custom URL scorer
def url_scorer(url: str) -> float:
    if "team" in url.lower(): return 1.0
    if "about" in url.lower(): return 0.8
    if "contact" in url.lower(): return 0.3
    return 0.1

strategy = BestFirstCrawlingStrategy(
    url_scorer=url_scorer,
    max_pages=5,
    score_threshold=0.5
)
```

## Comparison Matrix

| Criteria | Option 1: Multi-Page + Sync | Option 2: Homepage + Events | Option 3: Best-First ML |
|----------|----------|----------|----------|
| **Feasibility** | ✅ Easy with Crawl4AI | ✅ Simple implementation | ❌ Requires ML model training |
| **Performance** | ⚠️ 12-14 min (acceptable) | ✅ 5.5 min (fast) | ⚠️ Unpredictable time |
| **Maintainability** | ✅ Simple, readable | ⚠️ Event bus adds complexity | ❌ ML model maintenance |
| **Cost** | ⚠️ $0.40 per 150 practices | ✅ $0.10 per 150 practices | ⚠️ Similar to Option 1 |
| **Complexity** | ✅ Low (built-in Crawl4AI) | ⚠️ Medium (event bus) | ❌ High (ML training) |
| **Community/Support** | ✅ Well-documented BFS | ✅ Standard pattern | ⚠️ Advanced Crawl4AI feature |
| **Integration** | ✅ Clean dependency injection | ✅ Decoupled via events | ⚠️ Same as Option 1 |

### Criteria Definitions

- **Feasibility:** Can we implement this with current resources/skills/timeline?
- **Performance:** Will it meet performance requirements (speed, scale, resource usage)?
- **Maintainability:** How easy will it be to modify, debug, and extend over time?
- **Cost:** Financial cost (licenses, services, infrastructure)?
- **Complexity:** Implementation and operational complexity?
- **Community/Support:** Quality of documentation, community, and ecosystem?
- **Integration:** How well does it integrate with existing systems?

## Recommendation

**Chosen Approach:** Option 1 - Multi-Page Deep Crawling with Synchronous Orchestration

**Rationale:**
Multi-page scraping with BFSDeepCrawlStrategy provides 2-3x better decision maker detection rate (critical for sales outreach) at acceptable cost and time trade-offs. Synchronous scoring trigger is simple, testable, and meets user requirement for automated workflow. tiktoken cost tracking with $1.00 abort prevents runaway costs. Homepage-only scraping misses critical /team pages, and event bus adds unnecessary complexity for MVP.

### Why Not Other Options?

**Option 2 (Homepage + Events):**
- Misses 60-70% of decision makers found on /team pages (unacceptable data quality loss)
- Event bus is over-engineering for MVP (can refactor in Phase 2 if needed)
- User prioritized quality over speed (Decision #1)

**Option 3 (Best-First ML):**
- Requires training ML model to score URLs (significant upfront work)
- Unpredictable execution time (violates 12-14 min target)
- Complexity not justified by marginal gains over BFS strategy

### Trade-offs Accepted

- **Trade-off 1: Execution time (12-14 min vs 5.5 min)** - Acceptable because batch processing runs overnight, quality improvement worth 2x time cost
- **Trade-off 2: Cost ($0.40 vs $0.10 per 150 practices)** - Acceptable because still well under $1.00 threshold, better data drives more conversions
- **Trade-off 3: FEAT-002 depends on FEAT-003 (tight coupling)** - Acceptable with dependency injection and config flag (auto_trigger_scoring=false disables coupling)

## Spike Plan

### Step 1: Validate Crawl4AI BFSDeepCrawlStrategy
- **Action:** Test BFSDeepCrawlStrategy on 3 vet websites with varying structures (simple, complex, multi-level navigation)
- **Success Criteria:** Successfully scrapes 2-4 pages per site (homepage + /about + /team), URL pattern filter works correctly
- **Time Estimate:** 30 minutes

### Step 2: Validate tiktoken Cost Tracking
- **Action:** Count tokens for 10 sample website pages, compare to actual OpenAI API usage after extraction
- **Success Criteria:** tiktoken estimates within 5% of actual API usage, CostTracker correctly aborts at threshold
- **Time Estimate:** 20 minutes

### Step 3: Validate OpenAI Structured Outputs
- **Action:** Extract data from 5 sample websites using beta.chat.completions.parse with VetPracticeExtraction Pydantic model
- **Success Criteria:** 100% valid JSON responses (no parsing errors), confidence levels captured correctly
- **Time Estimate:** 30 minutes

### Step 4: Validate Notion Partial Updates
- **Action:** Update 3 test Notion records with only enrichment fields, verify sales fields (Status, Assigned To) preserved
- **Success Criteria:** Sales fields unchanged after update, enrichment fields updated correctly
- **Time Estimate:** 15 minutes

### Step 5: Validate Re-enrichment Query
- **Action:** Query Notion for practices with last_enriched_date > 30 days old OR enrichment_status != "Completed"
- **Success Criteria:** Query returns correct subset of practices (new + stale), excludes recently enriched practices
- **Time Estimate:** 15 minutes

**Total Spike Time:** 110 minutes (~2 hours)

## Implementation Notes

### Architecture Diagram
```
┌─────────────────────────────────────────────────────────────┐
│ EnrichmentOrchestrator (Main Pipeline)                     │
├─────────────────────────────────────────────────────────────┤
│  1. Query Notion for practices needing enrichment           │
│     (new OR last_enriched > 30 days ago)                    │
│                                                             │
│  2. WebsiteScraper (Crawl4AI BFSDeepCrawlStrategy)          │
│     ├─ 5 concurrent practices                              │
│     ├─ max_depth=1, max_pages=5                            │
│     ├─ URL pattern: *about*, *team*, *staff*, *contact*    │
│     └─ Output: List[WebsiteData] per practice              │
│                                                             │
│  3. LLMExtractor (OpenAI GPT-4o-mini)                       │
│     ├─ CostTracker checks budget before each call          │
│     ├─ tiktoken counts tokens (input + estimated output)   │
│     ├─ Abort if cumulative cost > $1.00                    │
│     ├─ beta.chat.completions.parse (structured outputs)    │
│     └─ Output: VetPracticeExtraction (Pydantic)            │
│                                                             │
│  4. NotionClient.update_practice_enrichment()               │
│     ├─ Partial update (only enrichment fields)             │
│     ├─ Sales fields auto-preserved                         │
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
└─────────────────────────────────────────────────────────────┘
```

### Key Components
- **EnrichmentOrchestrator:** Coordinates multi-page scraping, LLM extraction, cost tracking, Notion updates, retry logic, and scoring trigger
- **WebsiteScraper:** Crawl4AI wrapper with BFSDeepCrawlStrategy, handles async multi-page scraping with URL filtering
- **LLMExtractor:** OpenAI client with structured outputs, tiktoken cost tracking, and CostTracker integration
- **CostTracker:** Monitors cumulative OpenAI costs, aborts pipeline if threshold ($1.00) exceeded
- **NotionClient:** Extended with update_practice_enrichment() method for partial updates with field preservation

### Data Flow
1. **Query Notion:** Filter for practices with website != null AND (enrichment_status != "Completed" OR last_enriched_date > 30 days ago)
2. **Multi-page scraping:** Crawl4AI scrapes homepage + /about + /team pages (2-4 pages avg), 5 concurrent practices, ~12 minutes for 150 practices
3. **LLM extraction:** Concatenate all pages, truncate to 8000 chars, count tokens with tiktoken, check budget, call OpenAI, track actual cost
4. **Notion update:** Partial update with only enrichment fields, sales fields auto-preserved by Notion API
5. **Retry:** Collect all failed practices, retry once at end, log persistent failures to Notion
6. **Scoring trigger:** If auto_trigger_scoring=true and scoring_service provided, trigger FEAT-003 for each enriched practice
7. **Error summary:** Aggregate and categorize all failures (scrape, LLM, notion, cost, scoring)

### Technical Dependencies
- **crawl4ai:** 0.7.6 ⚠️ **CRITICAL - Must be 0.7.6+** (0.3.74 lacks BFSDeepCrawlStrategy)
- **openai:** 2.7.1 (structured outputs via beta.chat.completions.parse)
- **tiktoken:** 0.8.0 (token counting for gpt-4o-mini with o200k_base encoding)
- **notion-client:** 2.2.1 (Notion API integration)
- **pydantic:** 2.12.3 (data validation and structured outputs schema)
- **tenacity:** 9.0.0 (retry logic with exponential backoff)

**Version Notes:**
- Crawl4AI upgraded 0.3.74 → 0.7.6 during spike testing (BFSDeepCrawlStrategy added in 0.7.x)
- OpenAI, Pydantic upgraded as dependencies of Crawl4AI 0.7.6
- See `spike-results.md` for complete dependency list and upgrade impact

### Configuration Required
- **config.json additions:**
  ```json
  {
    "website_scraping": {
      "max_concurrent": 5,
      "timeout_seconds": 30,
      "retry_attempts": 2,
      "extraction_prompt_file": "config/website_extraction_prompt.txt",
      "cache_enabled": true,
      "cache_directory": "data/website_cache"
    },
    "enrichment": {
      "auto_trigger_scoring": true,
      "cost_threshold": 1.00,
      "re_enrichment_days": 30
    }
  }
  ```
- **Environment variables:** OPENAI_API_KEY (OpenAI API key for GPT-4o-mini)

## Risks & Mitigation

### Risk 1: Cost Runaway (OpenAI API)
- **Impact:** High (could exceed budget if token counting fails)
- **Likelihood:** Low (tiktoken validated <1% variance for long texts, CostTracker has hard abort)
- **Mitigation:** Token counting happens BEFORE each API call, hard abort at $1.00, 10% buffer in CostTracker, log cumulative cost every 10 practices
- **Spike Result:** ✅ tiktoken variance <1% for website-length texts, actual cost $0.000121 per extraction (93% under estimate)

### Risk 2: Multi-Page Scraping Failures
- **Impact:** Medium (reduces data quality if many pages fail)
- **Likelihood:** Medium (some sites have poor HTML, slow load times)
- **Mitigation:** Individual page failures don't fail entire practice, retry failed practices once at end, 30s timeout per page prevents hanging

### Risk 3: FEAT-003 Dependency Blocking
- **Impact:** Medium (FEAT-002 can't auto-score if FEAT-003 not implemented)
- **Likelihood:** High (FEAT-003 not yet implemented)
- **Mitigation:** Dependency injection with Optional[ScoringService], auto_trigger_scoring=false by default, FEAT-002 works standalone, add auto-trigger in v2

## References

- [Research findings]: `docs/features/FEAT-002_website-enrichment/research.md`
- [User decisions]: `docs/features/FEAT-002_website-enrichment/user-decisions.md`
- [PRD]: `docs/features/FEAT-002_website-enrichment/prd.md`
- [Crawl4AI Deep Crawling]: https://docs.crawl4ai.com/core/deep-crawling/
- [OpenAI Structured Outputs]: https://openai.com/index/introducing-structured-outputs-in-the-api/
- [tiktoken Documentation]: https://cookbook.openai.com/examples/how_to_count_tokens_with_tiktoken

---

**Decision Status:** Accepted
**Next Steps:** Proceed to acceptance criteria and testing strategy
