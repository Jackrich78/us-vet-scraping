# FEAT-002 Spike Testing Session Debrief

**Date:** 2025-11-04
**Session Duration:** ~2.5 hours
**Status:** Partial completion - Critical blocker discovered

---

## Executive Summary

We completed a comprehensive spike testing plan for FEAT-002 (Website Enrichment) to validate all technical assumptions before implementation. Made significant progress on infrastructure setup and Notion schema creation, but discovered a **CRITICAL BLOCKER** with Crawl4AI that requires architectural decision before proceeding.

### Progress Summary:
- ✅ **Phase 1 Complete**: All Python packages installed (crawl4ai, openai, tiktoken, playwright)
- ✅ **Phase 2 Complete**: FEAT-000 infrastructure audited, missing components documented
- ✅ **Phase 3 Complete**: Notion schema validated - **created 20 enrichment fields programmatically**
- ❌ **Phase 4 BLOCKED**: Crawl4AI BFSDeepCrawlStrategy **does not exist in v0.3.74**
- ⏸️ **Phases 5-9**: Paused pending Crawl4AI resolution

### Critical Finding:
**Crawl4AI v0.3.74 does NOT have BFSDeepCrawlStrategy or deep crawling functionality.** The entire FEAT-002 PRD architecture is based on multi-page scraping with this feature, which doesn't exist in the installed version.

---

## What We Accomplished

### Phase 1: Dependency Installation ✅

**Completed Successfully**

Installed all required Python packages in venv:
- `crawl4ai==0.3.74` (with version conflicts resolved)
- `openai==1.54.3`
- `tiktoken==0.8.0`
- `playwright==1.55.0` (browsers installed)
- `notion-client==2.2.1`
- `pydantic==2.9.2`
- `python-dotenv` (for .env loading)

**Issues Resolved:**
- greenlet compilation failure on Python 3.13 → Installed pre-built wheel
- Version conflicts with crawl4ai dependencies → Installed manually, everything imports successfully

**Verification:**
```bash
python3 -c "import crawl4ai; import openai; import tiktoken; print('✅ All packages work')"
# Output: ✅ All packages work
```

**Files Created:**
- All packages in `venv/lib/python3.13/site-packages/`
- Playwright chromium browser in `~/Library/Caches/ms-playwright/`

---

### Phase 2: FEAT-000 Infrastructure Audit ✅

**Completed Successfully**

**Finding:** FEAT-000 shared infrastructure components **do NOT exist yet**, as expected per user confirmation.

**Missing Components:**
1. `VetPracticeExtraction` model (should be in `src/models/enrichment_models.py`)
2. `CostTracker` utility (should be in `src/utils/cost_tracker.py`)
3. `retry_api_call` decorator (should be in `src/utils/retry.py`)
4. `ErrorAggregator` utility (should be in `src/utils/error_tracker.py`)

**Existing Infrastructure (Ready to Use):**
1. ✅ `WebsiteScrapingConfig` in `src/config/config.py:63-73`
2. ✅ Logging setup in `src/utils/logging.py`
3. ✅ `NotionConfig` in `src/config/config.py:46-60`
4. ✅ `VeterinaryPractice` model in `src/models/apify_models.py:112-154` (FEAT-001 model, different from enrichment)

**Decision:** Build missing components **inline during FEAT-002 implementation**, extract to FEAT-000 later if needed.

**Implementation Strategy Documented:**
- VetPracticeExtraction: Simple Pydantic model (20 fields from PRD schema)
- CostTracker: tiktoken integration, budget monitoring with $1.00 abort threshold
- Retry: Use `tenacity` library directly (no custom decorator needed)
- Error tracking: Simple list-based tracking for MVP

**Files Created:**
- `docs/features/FEAT-002_website-enrichment/spike-phase2-findings.md` (full analysis)

---

### Phase 3: Notion Schema Validation ✅

**Completed Successfully - MAJOR WORK DONE**

**Initial Finding:** Notion database was **missing 19 out of 20 enrichment fields**. Only FEAT-001 (Google Maps) fields existed.

**Action Taken:** Created all missing fields **programmatically via Notion API**.

**Fields Created Successfully (19):**
1. Confirmed Vet Count (Total) - number
2. Vet Count Confidence - select (high/medium/low)
3. Decision Maker Name - rich_text
4. Decision Maker Role - select (Owner/Practice Manager/Medical Director)
5. Decision Maker Email - email
6. Decision Maker Phone - phone_number
7. 24/7 Emergency Services - checkbox
8. Specialty Services - multi_select (Surgery, Dental, Oncology, etc.)
9. Wellness Programs - checkbox
10. Boarding Services - checkbox
11. Online Booking - checkbox
12. Telemedicine - checkbox
13. Patient Portal - checkbox
14. Digital Records Mentioned - checkbox
15. Awards/Accreditations - multi_select (AAHA, Fear Free, Cat Friendly)
16. Unique Services - multi_select
17. Enrichment Status - select (Pending/Completed/Failed)
18. Last Enrichment Date - date
19. Enrichment Error - rich_text

**Field with Issue (1):**
20. **Personalization Context** - Existed as `rich_text` but needed to be `multi_select`
    - **Solution:** Created new field "Personalization Context (Multi)" as multi_select
    - **Note:** FEAT-002 will use "Personalization Context (Multi)" field

**Final Validation:**
```bash
python3 spike_notion_schema.py
# Output: ✅ ALL VALIDATION CHECKS PASSED!
#         Notion schema is ready for FEAT-002 implementation.
```

**Files Created:**
- `spike_notion_schema.py` - Schema validation script (reusable)
- `spike_notion_create_fields.py` - Field creation script

**Environment Variables Confirmed:**
- `OPENAI_API_KEY=sk-proj-***` (working)
- `NOTION_API_KEY=ntn_***` (working)
- `NOTION_DATABASE_ID=2a0edda2a9a081d98dc9daa43c65e744` (working)

---

### Phase 4: Crawl4AI Deep Crawling Test ❌ BLOCKED

**Status:** CRITICAL BLOCKER DISCOVERED

**The Problem:**

Crawl4AI v0.3.74 does **NOT** have the following features that the FEAT-002 PRD relies on:
- ❌ `BFSDeepCrawlStrategy` class (does not exist)
- ❌ `DFSDeepCrawlStrategy` class (does not exist)
- ❌ `BestFirstCrawlingStrategy` class (does not exist)
- ❌ `CrawlerRunConfig` class (does not exist)
- ❌ Deep crawling module (`crawl4ai.deep_crawling`) (does not exist)
- ❌ URL filtering (`URLPatternFilter`, `FilterChain`) (does not exist)

**What Actually Exists in v0.3.74:**

```python
# Available in crawl4ai v0.3.74:
from crawl4ai import AsyncWebCrawler, CacheMode, CrawlResult

# AsyncWebCrawler.arun() signature:
async def arun(
    self,
    url: str,
    word_count_threshold=1,
    extraction_strategy=None,
    chunking_strategy=RegexChunking(),
    content_filter=None,
    cache_mode: Optional[CacheMode] = None,
    bypass_cache: bool = False,
    css_selector: str = None,
    screenshot: bool = False,
    user_agent: str = None,
    verbose=True,
    **kwargs
) -> CrawlResult
```

**Key Observation:** The installed Crawl4AI v0.3.74 is a **simple single-page crawler** with no multi-page/deep crawling capabilities.

**Archon Documentation Mismatch:**

The Archon knowledge base (source_id: `21ece81541cd5527`) contains Crawl4AI documentation that shows BFSDeepCrawlStrategy and deep crawling examples. However, this documentation appears to be for a **different/newer version** of Crawl4AI than v0.3.74.

**Evidence:**
- Archon docs show: `from crawl4ai.deep_crawling import BFSDeepCrawlStrategy`
- Actual v0.3.74: `ImportError: cannot import name 'BFSDeepCrawlStrategy'`
- Checked actual installed package: No `deep_crawling` module exists

**Files Created:**
- `spike_crawl4ai.py` - Test script (fails with ImportError)

---

## Critical Decision Required: Multi-Page Scraping Approach

### The Core Requirement (from PRD):

FEAT-002 **requires** multi-page scraping to achieve quality targets:
- Homepage + `/about` + `/team` pages (2-4 pages per practice)
- Multi-page scraping provides **2-3x better decision maker detection** vs homepage-only
- User Decision #1 explicitly chose multi-page over homepage-only (quality > speed)

### Three Options to Proceed:

#### Option A: Revise Architecture - Single Page Only (Simplest, Lower Quality)

**Approach:** Scrape only homepage, abandon multi-page requirement

**Implementation:**
```python
from crawl4ai import AsyncWebCrawler, CacheMode

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(url, cache_mode=CacheMode.ENABLED)
    # Process result.cleaned_html
```

**Pros:**
- ✅ Works immediately with installed Crawl4AI v0.3.74
- ✅ Simplest implementation (5-10 lines of code)
- ✅ No additional research needed

**Cons:**
- ❌ **Violates User Decision #1** (chose multi-page for quality)
- ❌ **Lower data quality**: Misses 60-70% of decision makers on /team pages
- ❌ **PRD estimates invalid**: Based on multi-page assumptions
- ❌ Acceptance criteria would need major revision

**Recommendation:** ❌ Do NOT choose this option unless user explicitly accepts lower quality

---

#### Option B: Research & Use Correct Crawl4AI Version (Unknown Complexity)

**Approach:** Find the Crawl4AI version that actually has BFSDeepCrawlStrategy and test it

**Steps Required:**
1. **Web search** for Crawl4AI deep crawling documentation (https://docs.crawl4ai.com/core/deep-crawling/)
2. **Identify correct version** that has deep crawling (likely v0.4+)
3. **Update requirements.txt** to use newer version
4. **Reinstall** and test for breaking changes
5. **Validate** BFSDeepCrawlStrategy works as documented

**Pros:**
- ✅ Matches original PRD architecture
- ✅ Leverages library features (don't reinvent wheel)
- ✅ Archon docs provide examples (if version matches)

**Cons:**
- ⚠️ **Unknown version compatibility** with Python 3.13
- ⚠️ **May have breaking API changes** from v0.3.74
- ⚠️ **Greenlet dependency** may cause issues again
- ⚠️ **Time unknown** (could be 30 min or 3 hours)

**Recommendation:** ⚠️ Research required before committing

---

#### Option C: Custom Playwright Multi-Page Crawler (Moderate Complexity, Full Control)

**Approach:** Implement custom multi-page crawler using Playwright directly (no Crawl4AI deep crawling)

**Implementation Strategy:**
```python
from playwright.async_api import async_playwright
import re

async def scrape_multi_page_vet_website(url: str, max_pages: int = 5):
    """
    Custom multi-page crawler for vet websites.

    1. Visit homepage
    2. Extract all internal links
    3. Filter links matching patterns: *about*, *team*, *staff*, *contact*
    4. Visit up to max_pages total
    5. Return combined content from all pages
    """

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        visited_urls = []
        pages_content = []

        # Visit homepage
        await page.goto(url, timeout=30000)
        homepage_content = await page.content()
        pages_content.append({"url": url, "content": homepage_content, "depth": 0})
        visited_urls.append(url)

        # Extract all internal links
        links = await page.eval_on_selector_all(
            'a[href]',
            '(elements) => elements.map(e => e.href)'
        )

        # Filter links by pattern
        patterns = ['about', 'team', 'staff', 'contact']
        filtered_links = [
            link for link in links
            if any(pattern in link.lower() for pattern in patterns)
            and link.startswith(url)  # Same domain
            and link not in visited_urls
        ]

        # Visit filtered links (up to max_pages)
        for link in filtered_links[:max_pages-1]:  # -1 for homepage
            try:
                await page.goto(link, timeout=30000)
                content = await page.content()
                pages_content.append({"url": link, "content": content, "depth": 1})
                visited_urls.append(link)
            except Exception as e:
                print(f"Failed to scrape {link}: {e}")

        await browser.close()

        return pages_content
```

**Pros:**
- ✅ **Full control** over scraping logic
- ✅ **Playwright already installed** and working
- ✅ **Simple to implement** (~50-100 lines of code)
- ✅ **Matches PRD requirements** exactly (homepage + filtered sub-pages)
- ✅ **No version compatibility issues**
- ✅ **Can add caching** with simple file-based approach

**Cons:**
- ⚠️ **Custom code to maintain** (not using library feature)
- ⚠️ **Need to implement caching** (but simple: save HTML to `data/website_cache/{hash}.html`)
- ⚠️ **Need to handle errors/timeouts** (but straightforward with try/except)

**Complexity Estimate:** 1-2 hours to implement and test

**Recommendation:** ✅ **RECOMMENDED** - Best balance of simplicity, control, and meeting requirements

---

### Recommended Path Forward: Option C (Custom Playwright Crawler)

**Rationale:**
1. **Meets all PRD requirements** (multi-page, URL filtering, 2-4 pages per practice)
2. **Simple implementation** (Playwright is well-documented, we have it installed)
3. **No unknown dependencies** (no version compatibility risks)
4. **Full control** (can optimize for vet website patterns)
5. **User Decision #1 honored** (multi-page for quality)

**Implementation Plan:**
1. Create `src/scraping/playwright_multi_page_scraper.py`
2. Implement `scrape_multi_page()` function (homepage + filtered links)
3. Add simple file-based caching (`data/website_cache/{url_hash}.json`)
4. Test with 3 real vet websites (same as original spike plan)
5. Measure: pages scraped, execution time, cache effectiveness

**Alternative (If User Prefers):**
- Research Option B first (30-60 min) - Try to find correct Crawl4AI version
- If research fails or breaks, fall back to Option C

---

## Phases 5-9: Not Yet Started (Paused)

### Phase 5: OpenAI Structured Outputs Test ⏸️

**Status:** Script created, not yet run

**File:** `spike_openai.py` (ready to run)

**What It Tests:**
- `beta.chat.completions.parse()` with gpt-4o-mini
- Pydantic model validation (VetPracticeExtraction)
- Cost per extraction (target: ≤$0.001)
- Structured output accuracy with 3 sample vet websites

**Expected Runtime:** 30 seconds

**Command to run:**
```bash
source venv/bin/activate && python3 spike_openai.py
```

**Success Criteria:**
- ✅ All responses are valid Pydantic objects
- ✅ No JSON parsing errors
- ✅ Average cost ≤$0.001 per extraction

---

### Phase 6: tiktoken Token Counting Test ⏸️

**Status:** Not yet created

**What It Tests:**
- tiktoken token counting accuracy for gpt-4o-mini (o200k_base encoding)
- Compare estimated tokens vs actual API usage
- Validate cost calculations

**Expected Runtime:** 2 minutes (requires 3-5 OpenAI API calls)

**Success Criteria:**
- ✅ tiktoken estimates within 5% of actual API usage
- ✅ Cost calculations accurate

---

### Phase 7: Notion Partial Updates Test ⏸️

**Status:** Not yet created

**What It Tests:**
- Notion API partial updates preserve sales workflow fields
- Update only enrichment fields, verify Status/Assigned To/Call Notes unchanged
- Re-enrichment query filter (new + >30 days old)

**Expected Runtime:** 1 minute

**Success Criteria:**
- ✅ Sales fields preserved after enrichment update
- ✅ Re-enrichment query returns correct practices

---

### Phase 8: Re-enrichment Query Test ⏸️

**Status:** Not yet created

**What It Tests:**
- Notion query with OR filter: `enrichment_status != "Completed" OR last_enriched_date > 30 days ago`
- Verify correct practices returned (new + stale, exclude recent)

**Expected Runtime:** 30 seconds

**Success Criteria:**
- ✅ Query returns practices needing enrichment
- ✅ Excludes recently enriched practices (<30 days)

---

### Phase 9: Document Findings & Implementation Plan ⏸️

**Status:** Partial (this debrief document)

**Remaining Work:**
- Consolidate all spike results into `spike-results.md`
- Update PRD if necessary (scraping approach)
- Create implementation roadmap based on spike findings
- Document any descoped features

**Expected Runtime:** 15 minutes

---

## Key Learnings

### 1. Always Validate Library APIs Before Architectural Decisions

**Lesson:** Documentation (even in knowledge bases like Archon) may not match installed library versions.

**Impact:** FEAT-002 PRD was written assuming BFSDeepCrawlStrategy exists, but it doesn't in v0.3.74.

**Prevention:** Always check `pip show <package>` version and verify imports before writing PRD.

---

### 2. Notion API Allows Programmatic Schema Creation

**Lesson:** We successfully created 19 database fields via `client.databases.update()` in seconds.

**Impact:** Massive time saver vs manually clicking in Notion UI.

**Reusable Pattern:**
```python
client.databases.update(
    database_id=database_id,
    properties={
        "Field Name": {
            "select": {
                "options": [{"name": "Option 1", "color": "blue"}]
            }
        }
    }
)
```

---

### 3. Python 3.13 Has Compatibility Issues

**Lesson:** greenlet (crawl4ai dependency) doesn't compile on Python 3.13 easily.

**Solution:** Install pre-built wheel: `pip install --only-binary :all: greenlet`

**Future:** Consider Python 3.11 or 3.12 for better package compatibility.

---

### 4. FEAT-000 "Nice to Have" Components Can Be Built Inline

**Lesson:** CostTracker, retry decorators, error aggregators can be implemented inline (50-100 lines each) without dedicated FEAT-000 infrastructure.

**Impact:** Unblocks FEAT-002 implementation, can extract later if reused.

---

## Files Created This Session

### Spike Test Scripts:
- `spike_notion_schema.py` - Notion schema validation (✅ working)
- `spike_notion_create_fields.py` - Notion field creation (✅ working)
- `spike_crawl4ai.py` - Crawl4AI test (❌ blocked by API mismatch)
- `spike_openai.py` - OpenAI structured outputs test (⏸️ ready to run)

### Documentation:
- `docs/features/FEAT-002_website-enrichment/spike-phase2-findings.md` - FEAT-000 audit results
- `docs/features/FEAT-002_website-enrichment/spike-session-debrief.md` - This document

### Configuration:
- Updated `.env` with all API keys (verified working)
- Notion database schema now has 20 enrichment fields

---

## Next Session Action Items

### Immediate Priority: Resolve Crawl4AI Blocker

**Decision Required:** Choose scraping approach (Options A/B/C above)

#### If Option B (Research Crawl4AI):
1. ⏰ **30 min**: Web search https://docs.crawl4ai.com/core/deep-crawling/ for correct version
2. ⏰ **15 min**: Identify version with BFSDeepCrawlStrategy (likely v0.4+)
3. ⏰ **20 min**: Test install newer version, check for breaking changes
4. ⏰ **30 min**: Run spike test with BFSDeepCrawlStrategy
5. **If successful**: Continue with Phases 5-9
6. **If fails**: Fall back to Option C

#### If Option C (Custom Playwright - RECOMMENDED):
1. ⏰ **60 min**: Implement `PlaywrightMultiPageScraper` class
   - Homepage scraping
   - Link extraction & filtering (*about*, *team*, *staff*, *contact*)
   - Multi-page visiting (max 5 pages)
   - Simple file-based caching
2. ⏰ **30 min**: Test with 3 real vet websites
   - Measure: pages scraped, execution time, content quality
3. ⏰ **15 min**: Document findings, update PRD if needed
4. ✅ **Proceed to Phases 5-9**

---

### Secondary Priority: Complete Remaining Spikes (2 hours)

**Phase 5: OpenAI Structured Outputs**
- ⏰ **5 min**: Run `python3 spike_openai.py`
- ⏰ **10 min**: Review results, validate cost/accuracy
- ⏰ **5 min**: Document findings

**Phase 6: tiktoken Token Counting**
- ⏰ **20 min**: Create `spike_tiktoken.py`
- ⏰ **10 min**: Run with 5 sample texts, compare to actual API usage
- ⏰ **5 min**: Document findings

**Phase 7: Notion Partial Updates**
- ⏰ **20 min**: Create `spike_notion_partial_updates.py`
- ⏰ **5 min**: Test: create record, update enrichment fields, verify sales fields preserved
- ⏰ **5 min**: Document findings

**Phase 8: Re-enrichment Query**
- ⏰ **15 min**: Create `spike_notion_requery.py`
- ⏰ **5 min**: Test query filter with mixed practice dates
- ⏰ **5 min**: Document findings

**Phase 9: Final Documentation**
- ⏰ **30 min**: Consolidate all spike results into `spike-results.md`
- ⏰ **15 min**: Update FEAT-002 PRD if needed (scraping approach, cost estimates)
- ⏰ **10 min**: Create implementation roadmap

---

## Environment Setup Verification (For Next Session)

### Quick Start Commands:

```bash
# Activate venv
cd /Users/builder/dev/us_vet_scraping
source venv/bin/activate

# Verify packages
python3 -c "import crawl4ai, openai, tiktoken, notion_client; print('✅ All imports work')"

# Check environment variables
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print('OPENAI_API_KEY:', 'SET' if os.getenv('OPENAI_API_KEY') else 'MISSING'); print('NOTION_API_KEY:', 'SET' if os.getenv('NOTION_API_KEY') else 'MISSING'); print('NOTION_DATABASE_ID:', 'SET' if os.getenv('NOTION_DATABASE_ID') else 'MISSING')"

# Validate Notion schema
python3 spike_notion_schema.py
# Expected: ✅ ALL VALIDATION CHECKS PASSED!

# Run remaining spike tests (after resolving Crawl4AI)
python3 spike_openai.py  # Phase 5
# ... (create and run phases 6-8)
```

### Environment State:
- Python: 3.13.5
- venv: `/Users/builder/dev/us_vet_scraping/venv/`
- Working directory: `/Users/builder/dev/us_vet_scraping/`
- Git branch: `main` (clean)

---

## Critical Context for Next Session

### **DO NOT FORGET:**

1. **Crawl4AI v0.3.74 does NOT have BFSDeepCrawlStrategy** - Must choose Option B (research) or Option C (custom Playwright) before proceeding

2. **Notion database now has 20 enrichment fields** - Use "Personalization Context (Multi)" not "Personalization Context"

3. **FEAT-000 components don't exist** - Build CostTracker, VetPracticeExtraction, retry logic inline during FEAT-002 implementation

4. **All API keys are configured and working** - OPENAI_API_KEY, NOTION_API_KEY, NOTION_DATABASE_ID in `.env`

5. **User decisions from PRD:**
   - Multi-page scraping chosen over homepage-only (quality > speed)
   - Accept low-confidence extractions, flag with confidence level
   - No email pattern guessing (explicit only)
   - Flexible personalization quality bar (accept generic facts)
   - Cost threshold: $1.00 hard abort

6. **Test mode:** First 10 practices, target execution ≤2 min, cost ≤$0.01

---

## Recommended Next Session Flow

### Option 1: Research-First Approach (If User Wants to Try Crawl4AI Deep Crawling)

```
1. [30 min] Research Crawl4AI versions with deep crawling
   - Web search https://docs.crawl4ai.com/
   - Check GitHub releases
   - Find BFSDeepCrawlStrategy version

2. [20 min] Test install newer version
   - Update requirements.txt
   - pip install
   - Check for breaking changes

3. [30 min] Run Crawl4AI spike test
   - Test BFSDeepCrawlStrategy with real vet websites
   - Validate URL filtering works
   - Measure execution time and pages scraped

4. If successful → Continue to Phases 5-9
   If fails → Fall back to Custom Playwright (Option C)
```

### Option 2: Direct Implementation (RECOMMENDED)

```
1. [60 min] Implement custom Playwright multi-page scraper
   - Create PlaywrightMultiPageScraper class
   - Test with 3 vet websites
   - Validate meets PRD requirements

2. [2 hours] Complete remaining spike tests (Phases 5-9)
   - OpenAI structured outputs
   - tiktoken accuracy
   - Notion partial updates
   - Re-enrichment query
   - Final documentation

3. [30 min] Update PRD/architecture with final decisions

4. ✅ Ready for `/build FEAT-002` implementation
```

---

## Success Criteria for Spike Completion

**All spikes must pass before proceeding to `/build FEAT-002`:**

- ✅ Phase 1: Packages installed and importing
- ✅ Phase 2: FEAT-000 dependencies documented
- ✅ Phase 3: Notion schema validated (20 fields)
- ⏸️ Phase 4: Multi-page scraping working (Crawl4AI OR custom Playwright)
- ⏸️ Phase 5: OpenAI structured outputs returning valid Pydantic objects
- ⏸️ Phase 6: tiktoken estimates within 5% of actual usage
- ⏸️ Phase 7: Notion partial updates preserve sales fields
- ⏸️ Phase 8: Re-enrichment query returns correct practices
- ⏸️ Phase 9: All findings documented, PRD updated

**Estimated Remaining Time:** 3-4 hours (depending on Crawl4AI decision)

---

## Questions to Resolve Next Session

1. **Scraping Approach:** Option B (research Crawl4AI) or Option C (custom Playwright)?
2. **If Option B fails:** Are we okay falling back to Option C?
3. **Test websites:** Should we use the 3 suggested vet websites (angell.org, bostonveterinaryclinic.com, theveterinaryclinicofnewton.com) or different ones?
4. **Descoping:** If we hit more blockers, are we okay descoping some features (e.g., caching, retry logic) for MVP?

---

**End of Debrief - Ready to Copy into Next Session** 🚀
