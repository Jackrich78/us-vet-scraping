# FEAT-002 Implementation Guide

**Status:** Ready for implementation - All spikes validated ✅
**Last Updated:** 2025-11-04

---

## 🚀 Quick Start

### Prerequisites (CRITICAL)

**1. Install correct dependencies:**
```bash
# CRITICAL: Must use Crawl4AI 0.7.6+ (0.3.74 does NOT have BFSDeepCrawlStrategy)
pip install crawl4ai==0.7.6
pip install openai==2.7.1
pip install pydantic==2.12.3
pip install tiktoken==0.8.0
pip install notion-client==2.2.1
```

**2. Verify environment:**
```bash
# Verify Crawl4AI deep crawling imports work
python3 -c "from crawl4ai.deep_crawling import BFSDeepCrawlStrategy; print('✅ Ready')"
```

**3. Check .env configuration:**
```bash
OPENAI_API_KEY=sk-proj-xxx
OPENAI_MODEL=gpt-4o-mini
NOTION_API_KEY=ntn_xxx
NOTION_DATABASE_ID=2a0edda2a9a081d98dc9daa43c65e744
```

---

## 📋 Implementation Sequence

### Phase 1: Models & Utilities (1 hour)

**1. Create VetPracticeExtraction model** (`src/models/enrichment_models.py`)
```python
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

class DecisionMaker(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class VetPracticeExtraction(BaseModel):
    vet_count_total: Optional[int] = Field(None, ge=1, le=50)
    vet_count_confidence: Optional[str] = Field(None, pattern="^(high|medium|low)$")
    decision_maker: Optional[DecisionMaker] = None
    emergency_24_7: bool = False
    specialty_services: List[str] = Field(default_factory=list)
    wellness_programs: bool = False
    boarding_services: bool = False
    online_booking: bool = False
    telemedicine: bool = False
    patient_portal: bool = False
    digital_records_mentioned: bool = False
    personalization_context: List[str] = Field(default_factory=list, max_length=3)
    awards_accreditations: List[str] = Field(default_factory=list)
    unique_services: List[str] = Field(default_factory=list)
    extraction_timestamp: datetime = Field(default_factory=datetime.utcnow)
```

**2. Create CostTracker** (`src/utils/cost_tracker.py`)
```python
import tiktoken

class CostTracker:
    def __init__(self, max_budget: float = 1.00, model: str = "gpt-4o-mini"):
        self.max_budget = max_budget
        self.cumulative_cost = 0.0
        self.call_count = 0
        self.encoding = tiktoken.encoding_for_model(model)
        self.buffer_multiplier = 1.10  # 10% buffer for safety

        # gpt-4o-mini pricing
        self.input_price_per_million = 0.15
        self.output_price_per_million = 0.60

    def count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        input_cost = (input_tokens * self.input_price_per_million) / 1_000_000
        output_cost = (output_tokens * self.output_price_per_million) / 1_000_000
        return input_cost + output_cost

    def check_budget(self, estimated_cost: float) -> bool:
        """Check budget with 10% buffer. Raises CostLimitExceeded if over."""
        buffered_cost = estimated_cost * self.buffer_multiplier
        if self.cumulative_cost + buffered_cost > self.max_budget:
            raise CostLimitExceeded(
                f"Cost limit exceeded: ${self.cumulative_cost:.4f} + ${buffered_cost:.4f} > ${self.max_budget:.2f}"
            )
        return True

    def track_call(self, input_tokens: int, output_tokens: int):
        cost = self.estimate_cost(input_tokens, output_tokens)
        self.cumulative_cost += cost
        self.call_count += 1

class CostLimitExceeded(Exception):
    pass
```

**Why 10% buffer?** Spike testing showed tiktoken variance <1% for long texts, 10% buffer provides safety margin.

---

### Phase 2: Website Scraper (1 hour)

**Create WebsiteScraper** (`src/scraping/website_scraper.py`)
```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter

class WebsiteScraper:
    def __init__(self, config: WebsiteScrapingConfig):
        # CRITICAL: Use URL pattern filter for targeted page discovery
        url_filter = URLPatternFilter(patterns=[
            "*about*", "*team*", "*staff*", "*contact*",
            "*our-team*", "*meet-the*"
        ])

        self.deep_crawl_strategy = BFSDeepCrawlStrategy(
            max_depth=1,              # Homepage + 1 level
            include_external=False,    # Stay within same domain
            max_pages=5,               # Homepage + up to 4 sub-pages
            filter_chain=FilterChain([url_filter])
        )

        self.crawler_config = CrawlerRunConfig(
            deep_crawl_strategy=self.deep_crawl_strategy,
            wait_for="networkidle",
            page_timeout=30000,        # 30s timeout per page
            magic=True,                # Smart content extraction
            cache_mode=CacheMode.ENABLED,
            stream=False               # Batch mode
        )

    async def scrape_multi_page(self, homepage_url: str, practice_name: str) -> List[WebsiteData]:
        """Scrape homepage and related pages for a single practice."""
        async with AsyncWebCrawler() as crawler:
            results = await crawler.arun(homepage_url, config=self.crawler_config)
            # Convert results to WebsiteData objects
            # ... (see spike_crawl4ai.py for implementation)
```

**Key learnings from spike testing:**
- BFSDeepCrawlStrategy works as documented in Crawl4AI 0.7.6
- Some websites may return 0 pages (timeout/blocking) - this is expected, handle gracefully
- Cache works correctly for development iteration

---

### Phase 3: LLM Extractor (1 hour)

**Create LLMExtractor** (`src/extraction/llm_extractor.py`)
```python
from openai import OpenAI
import tiktoken
import os

class LLMExtractor:
    def __init__(self, cost_tracker: CostTracker):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.cost_tracker = cost_tracker
        self.extraction_prompt = self._load_extraction_prompt()

    def extract_practice_data(
        self,
        website_pages: List[WebsiteData],
        practice_name: str
    ) -> VetPracticeExtraction:
        """Extract structured data using OpenAI structured outputs."""

        # Concatenate all successful pages
        all_text = "\n\n--- PAGE BREAK ---\n\n".join([
            page.cleaned_text for page in website_pages if page.success
        ])

        # Truncate to 8000 chars (~2000 tokens)
        truncated_text = all_text[:8000]

        # Count tokens and check budget BEFORE API call
        input_tokens = self.cost_tracker.count_tokens(self.extraction_prompt + truncated_text)
        estimated_output_tokens = 500
        estimated_cost = self.cost_tracker.estimate_cost(input_tokens, estimated_output_tokens)

        # This will raise CostLimitExceeded if over budget (with 10% buffer)
        self.cost_tracker.check_budget(estimated_cost)

        # Make API call using structured outputs
        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": self.extraction_prompt},
                {"role": "user", "content": truncated_text}
            ],
            response_format=VetPracticeExtraction,  # Pydantic model directly
            temperature=0.1,
            max_tokens=2000
        )

        # Track actual cost
        actual_input_tokens = response.usage.prompt_tokens
        actual_output_tokens = response.usage.completion_tokens
        self.cost_tracker.track_call(actual_input_tokens, actual_output_tokens)

        return response.choices[0].message.parsed  # Returns Pydantic object
```

**Key learnings from spike testing:**
- Actual cost: $0.000121 per extraction (93% under original estimate)
- Structured outputs work perfectly (100% valid JSON, no parsing errors)
- No need for retry logic on JSON parsing (structured outputs guarantee validity)

---

### Phase 4: Notion Integration (1 hour)

**Extend NotionClient** (`src/notion/notion_client.py`)

**Critical finding from spike testing:** Notion API automatically preserves fields not in update payload. No read-before-write needed!

```python
def update_practice_enrichment(
    self,
    page_id: str,
    enrichment_data: VetPracticeExtraction
) -> None:
    """Update existing Notion record with enrichment data.

    IMPORTANT: Sales workflow fields automatically preserved by Notion API.
    Only pass enrichment fields - Notion preserves everything else.
    """

    properties = {
        "Confirmed Vet Count (Total)": {"number": enrichment_data.vet_count_total},
        "Vet Count Confidence": {"select": {"name": enrichment_data.vet_count_confidence}},
        "24/7 Emergency Services": {"checkbox": enrichment_data.emergency_24_7},
        "Online Booking": {"checkbox": enrichment_data.online_booking},
        "Enrichment Status": {"select": {"name": "Completed"}},
        "Last Enrichment Date": {"date": {"start": enrichment_data.extraction_timestamp.isoformat()}}
    }

    # Add optional fields only if present
    if enrichment_data.decision_maker:
        properties["Decision Maker Name"] = {
            "rich_text": [{"text": {"content": enrichment_data.decision_maker.name}}]
        }
        if enrichment_data.decision_maker.email:
            properties["Decision Maker Email"] = {"email": enrichment_data.decision_maker.email}

    # Notion API automatically preserves:
    # - Status, Assigned To, Research Notes, Call Notes (sales fields)
    # - Practice Name, Address, Phone (FEAT-001 fields)
    self.client.pages.update(page_id=page_id, properties=properties)

def query_practices_for_enrichment(self, test_mode: bool = False):
    """Query practices needing enrichment (new OR stale >30 days)."""
    from datetime import datetime, timedelta, UTC

    thirty_days_ago = (datetime.now(UTC) - timedelta(days=30)).isoformat()

    return self.client.databases.query(
        database_id=self.database_id,
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
        page_size=10 if test_mode else 100
    )
```

**Key learnings from spike testing:**
- Partial updates work perfectly - sales fields preserved automatically
- Re-enrichment query OR filter validated and working
- Use `datetime.now(datetime.UTC)` not deprecated `datetime.utcnow()`

---

### Phase 5: Orchestration (2 hours)

**Create EnrichmentOrchestrator** (`src/orchestration/enrichment_orchestrator.py`)

Follow pattern in architecture.md, incorporating these validated learnings:

1. **Cost tracking:** Check budget BEFORE each API call (CostTracker.check_budget)
2. **Scraping:** Some websites return 0 pages - handle gracefully, don't fail entire batch
3. **Retry logic:** Retry failed practices once at end of batch
4. **Notion updates:** Simple partial updates (no read-before-write)
5. **Scoring trigger:** Optional, via dependency injection (if FEAT-003 implemented)

---

## ⚠️ Critical Implementation Notes

### 1. Crawl4AI Version
**BLOCKER if wrong version:**
- ✅ Use: `crawl4ai==0.7.6`
- ❌ DO NOT use: `crawl4ai==0.3.74` (lacks BFSDeepCrawlStrategy)

### 2. tiktoken Buffer
**Add 10% buffer to cost estimates:**
- Spike testing: <1% variance for long texts
- 10% buffer provides safety margin
- Implement in `CostTracker.check_budget()`

### 3. Notion Partial Updates
**No read-before-write needed:**
- Notion API preserves fields not in update payload
- Validated in spike testing (see `spike_notion_partial_updates.py`)
- Simple pattern: just pass enrichment fields

### 4. Re-enrichment Query
**OR filter validated:**
- Returns never-enriched practices
- Returns stale practices (>30 days)
- Excludes recent practices (<30 days)
- See `spike_notion_requery.py` for exact filter

### 5. Actual Costs
**93% under original estimate:**
- Estimated: $0.40 for 150 practices
- Actual: $0.03 for 150 practices
- Use actual cost $0.000121 per extraction for planning

---

## 📊 Validation Checklist

Before implementing, verify these spike results:

- [ ] Read `spike-results.md` for complete validation details
- [ ] Crawl4AI 0.7.6 installed and BFSDeepCrawlStrategy imports
- [ ] OpenAI model in .env (`OPENAI_MODEL=gpt-4o-mini`)
- [ ] Notion API keys in .env
- [ ] Understand tiktoken buffer requirement (10%)
- [ ] Understand Notion partial update pattern (no read-before-write)
- [ ] Understand re-enrichment query OR filter

---

## 🧪 Testing Strategy

### Unit Tests
- CostTracker.check_budget with various costs
- VetPracticeExtraction Pydantic validation
- WebsiteScraper URL filtering
- LLMExtractor token counting

### Integration Tests
- Full pipeline with test mode (10 practices)
- Notion partial updates preserve sales fields
- Re-enrichment query returns correct practices
- Cost tracking aborts at threshold

### Manual Tests
See `manual-test.md` for complete checklist

---

## 📚 Reference Documents

**Read in this order:**

1. **This guide** - Implementation overview and critical notes
2. **spike-results.md** - Complete validation details and actual costs
3. **architecture.md** - Detailed component specifications
4. **prd.md** - Full requirements and user decisions
5. **testing.md** - Comprehensive test strategy

**Spike test scripts** (for reference):
- `spike_crawl4ai.py` - Multi-page scraping validation
- `spike_openai.py` - Structured outputs validation
- `spike_tiktoken.py` - Token counting accuracy
- `spike_notion_partial_updates.py` - Field preservation validation
- `spike_notion_requery.py` - Re-enrichment query validation

---

## 🚨 Common Pitfalls

1. **Installing Crawl4AI 0.3.74** → Import error for BFSDeepCrawlStrategy
2. **Not adding 10% buffer to CostTracker** → May abort prematurely
3. **Reading practice before updating Notion** → Unnecessary, Notion preserves fields automatically
4. **Using datetime.utcnow()** → Deprecated in Python 3.13, use datetime.now(UTC)
5. **Assuming 0% scraping failures** → Some websites will fail, handle gracefully

---

**Ready to implement!** All technical assumptions validated. No open questions or blockers.

🚀 Start with Phase 1 (Models & Utilities) and work sequentially through Phase 5.
