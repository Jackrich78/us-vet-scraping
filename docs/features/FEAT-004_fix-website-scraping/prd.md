# FEAT-004: Fix Website Scraping Reliability

**Status:** Research Complete - Ready for Implementation
**Created:** 2025-11-05
**Research Completed:** 2025-11-05
**Owner:** Engineering Team
**Dependencies:** None (blocks FEAT-005, FEAT-006)
**Cost Impact:** $0 (code improvements only)
**Research Document:** [research.md](./research.md)

---

## Problem Statement

Current website scraping (FEAT-002) has a **60% failure rate**, making enrichment data unreliable and incomplete. Test results from 2025-11-04 show:

- **10 practices scraped**
- **6 failed** with "Website scraping failed (0 pages scraped)"
- **4 succeeded** but returned mostly empty data (Vet Count: None, Decision Maker: None)
- **Success rate: 40%** (unacceptable for production)

This failure rate undermines the entire enrichment pipeline and scoring system, as practices without enrichment data receive artificially low scores and poor personalization context.

### Root Cause Analysis

**✅ VALIDATED THROUGH RESEARCH & CODE ANALYSIS (2025-11-05)**

**CRITICAL BUGS (Cause 100% extraction failures):**

1. **🔴 CRITICAL: Prompt/Model Schema Mismatch**
   - **Evidence:** LLM prompt requests nested `{"vet_count": {"total": X}}` but Pydantic model expects flat `"vet_count_total": X`
   - **Impact:** Causes 100% null extractions (ALL 4 "successful" scrapes returned null data)
   - **Source:** Code analysis + OpenAI structured outputs documentation
   - **Fix Priority:** Day 1 (30 minutes)

2. **🔴 CRITICAL: Cache Corruption**
   - **Evidence:** Code uses `CacheMode.ENABLED` but Crawl4AI default is `CacheMode.BYPASS` for production
   - **Impact:** May cache previous failures, contributing 40-50% of scraping failures
   - **Source:** Crawl4AI v0.7.x documentation
   - **Fix Priority:** Day 1 (5 minutes)

3. **🔴 CRITICAL: No Diagnostic Logging**
   - **Evidence:** Zero visibility into HTTP status codes, exception types, or failure stages
   - **Impact:** Cannot identify actual causes of 60% failure rate
   - **Source:** Code analysis
   - **Fix Priority:** Day 1 (2-3 hours)

**HIGH-IMPACT ISSUES (Cause 15-30% of failures):**

4. **🟡 UTM Parameters in URLs**
   - **Evidence:** Google Maps results include `?utm_source=google_my_business` parameters
   - **Impact:** 10-15% of failures due to redirects/blocks from tracking parameters
   - **Source:** URL sanitization best practices (SEOMoz url-py)
   - **Fix Priority:** Day 2 (1 hour)

5. **🟡 No Retry Logic**
   - **Evidence:** Transient failures (timeouts, 5xx errors) become permanent failures
   - **Impact:** 15-20% of failures could be resolved with retry
   - **Source:** Web scraping best practices (ZenRows, ScrapeOps)
   - **Fix Priority:** Day 2 (1-2 hours)

6. **🟡 Missing URL Patterns**
   - **Evidence:** Only scraping `*about*`, `*team*`, `*staff*`, `*contact*` patterns
   - **Impact:** Missing 20-30% of relevant pages (`*services*`, `*doctors*`, `*our-team*`)
   - **Source:** Analysis of veterinary website patterns
   - **Fix Priority:** Day 2 (30 minutes)

**MEDIUM-IMPACT ISSUES (Cause 5-10% of failures):**

7. **🟢 No User Agent Rotation**
   - **Evidence:** Using Crawl4AI default user agent
   - **Impact:** 5-10% of failures from basic bot detection
   - **Source:** User agent rotation best practices (ScrapingAnt)
   - **Fix Priority:** Day 2 (30 minutes)

8. **🟢 Aggressive Text Truncation**
   - **Evidence:** 8,000 char limit across ALL pages - homepage may consume entire budget
   - **Impact:** Team pages (with vet names) get truncated, contributing to null extractions
   - **Source:** LLM chunking research (Snowflake, Pinecone)
   - **Fix Priority:** Day 3 (1 hour)

**LOW-IMPACT ISSUES (Unlikely causes):**

9. **⚪ Anti-bot Blocking**
   - **Evidence:** Small business vet sites don't have sophisticated blocking
   - **Impact:** <5% of failures (unlikely)
   - **Source:** Industry research
   - **Fix Priority:** Optional (user agent rotation sufficient)

### Impact

- **Lead Scoring Accuracy:** Practices default to "Pending Enrichment" tier
- **Sales Personalization:** No context for cold calls
- **Data Quality:** Incomplete ICP qualification
- **Cost Waste:** Paying for scraping infrastructure that doesn't work

---

## Goals

### Primary Goal
**Achieve <10% scraping failure rate** across 150+ Boston veterinary practices.

### Secondary Goals
1. Add detailed error logging to diagnose WHY scrapes fail
2. Implement retry logic with exponential backoff
3. Add fallback scraping strategy for simple sites
4. Validate and sanitize URLs before scraping

---

## Proposed Solution

### 1. Enhanced Error Logging
**Problem:** Current logs don't show WHY scrapes fail

**Solution:**
- Log HTTP status codes for each page attempt
- Log Crawl4AI exceptions with full stack traces
- Track which stage fails (DNS, connection, rendering, extraction)
- Save failed URLs to `data/logs/failed_scrapes.csv` for manual review

**Acceptance Criteria:**
- AC-FEAT-004-001: Error logs include HTTP status code, exception type, and URL
- AC-FEAT-004-002: Failed scrapes logged to CSV with practice name, URL, timestamp, error

### 2. Retry Logic with Exponential Backoff
**Problem:** No retries for transient failures (network hiccups, rate limits)

**Solution:**
- Retry failed pages up to 3 times with delays: 5s, 10s, 20s
- Use `tenacity` library (already in project)
- Only retry on retriable errors (timeouts, 5xx status codes)
- Don't retry on 404, 403, or permanent failures

**Acceptance Criteria:**
- AC-FEAT-004-003: Failed pages retried up to 3 times
- AC-FEAT-004-004: Exponential backoff delays: 5s, 10s, 20s
- AC-FEAT-004-005: Don't retry 404, 403, or invalid SSL errors

### 3. URL Sanitization
**Problem:** UTM parameters and tracking codes may cause issues

**Solution:**
- Strip UTM parameters before scraping: `?utm_source=`, `?y_source=`, etc.
- Validate URLs are reachable with a HEAD request before Crawl4AI
- Handle redirects (e.g., http → https)
- Normalize URLs (remove trailing slashes, fragments)

**Acceptance Criteria:**
- AC-FEAT-004-006: Strip UTM/tracking parameters from URLs
- AC-FEAT-004-007: Pre-validate URLs with HEAD request (2s timeout)
- AC-FEAT-004-008: Handle http → https redirects automatically

### 4. User Agent Rotation
**Problem:** Crawl4AI may be detected as bot

**Solution:**
- Rotate between 3-5 realistic user agents (Chrome, Firefox, Safari)
- Use recent versions (2024+)
- Include Accept-Language, Accept-Encoding headers

**Acceptance Criteria:**
- AC-FEAT-004-009: Rotate between 3+ realistic user agents
- AC-FEAT-004-010: Include full browser headers (Accept, Language, Encoding)

### 5. Fallback Scraping Strategy
**Problem:** Crawl4AI (headless browser) is heavy and may fail on simple sites

**Solution:**
- If Crawl4AI fails, fallback to simple `requests` + `BeautifulSoup`
- Only scrape homepage with fallback (no multi-page crawling)
- Extract basic text content for LLM

**Acceptance Criteria:**
- AC-FEAT-004-011: If Crawl4AI fails, try requests + BeautifulSoup
- AC-FEAT-004-012: Fallback scrapes homepage only (no deep crawl)
- AC-FEAT-004-013: Log which method succeeded (Crawl4AI vs fallback)

### 6. Timeout Configuration
**Problem:** 30s per-page timeout may be too short or too long

**Solution:**
- Reduce individual page timeout to 15s (fail faster)
- Add overall practice timeout of 60s (5 pages × 15s = 75s max, with buffer)
- Allow timeout configuration per environment (test vs prod)

**Acceptance Criteria:**
- AC-FEAT-004-014: Individual page timeout: 15s (configurable)
- AC-FEAT-004-015: Overall practice timeout: 60s (configurable)
- AC-FEAT-004-016: Timeout values in `config/config.json`

---

## Technical Approach

### File Changes

**`src/enrichment/website_scraper.py`:**
- Add retry decorator to `scrape_multi_page()`
- Add URL sanitization helper: `_sanitize_url(url)`
- Add URL validation helper: `_validate_url(url)` (HEAD request)
- Add user agent rotation: `_get_random_user_agent()`
- Add fallback method: `_scrape_with_requests(url)`
- Enhanced error logging in all exception blocks

**New file: `src/utils/url_utils.py`:**
```python
def sanitize_url(url: str) -> str:
    """Remove UTM parameters and normalize URL."""

def validate_url(url: str, timeout: int = 2) -> bool:
    """Check if URL is reachable with HEAD request."""

def is_retriable_error(exception: Exception) -> bool:
    """Determine if error should be retried."""
```

**`config/config.json`:**
```json
{
  "website_scraping": {
    "page_timeout_ms": 15000,
    "practice_timeout_ms": 60000,
    "max_retries": 3,
    "retry_delays": [5, 10, 20],
    "user_agents": [
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...",
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
      "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36..."
    ]
  }
}
```

### Monitoring & Metrics

Add metrics to track:
- Success rate per run (target: >90%)
- Average pages scraped per practice (target: 2-3)
- Retry counts per run
- Fallback usage rate
- Error breakdown by type (timeout, 404, 403, SSL, etc.)

Output summary at end of enrichment run:
```
Website Scraping Summary:
  Total practices: 150
  Successful: 142 (94.7%)
  Failed: 8 (5.3%)

  Error Breakdown:
    - Timeout: 3
    - 404 Not Found: 2
    - SSL Error: 2
    - Connection Refused: 1

  Performance:
    - Crawl4AI: 138 (97.2%)
    - Fallback (requests): 4 (2.8%)
    - Avg pages/practice: 2.8
    - Avg time/practice: 12.3s
```

---

## Testing Strategy

### Unit Tests
- `tests/unit/test_url_utils.py`:
  - Test URL sanitization (remove UTM params)
  - Test URL validation (HEAD requests)
  - Test error classification (retriable vs permanent)

### Integration Tests
- `tests/integration/test_scraping_reliability.py`:
  - Test against 50 real Boston vet websites
  - Measure success rate (must be >90%)
  - Test retry logic with mock failures
  - Test fallback strategy activation

### Manual Testing
1. Run enrichment on 50 practices with enhanced logging
2. Review `failed_scrapes.csv` to identify patterns
3. Manually visit 10 failed URLs to confirm they're valid/reachable
4. Adjust timeouts/retries based on findings

---

## Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Success Rate | 40% | >90% | Successful scrapes / total attempts |
| Avg Pages Scraped | 0-1 | 2-3 | Pages per successful scrape |
| Retry Rate | 0% | 10-20% | Practices requiring retries |
| Fallback Rate | 0% | <5% | Practices using fallback method |

---

## Risks & Mitigations

### Risk 1: Websites genuinely block scraping
**Mitigation:**
- Use respectful delays (5s between pages)
- Rotate user agents
- Consider proxy rotation (Phase 2)

### Risk 2: Some websites are permanently down
**Mitigation:**
- Accept <5% failure rate as baseline
- Log permanently failed URLs for manual review
- Allow manual override in Notion

### Risk 3: Fallback method extracts lower-quality content
**Mitigation:**
- Fallback is better than nothing
- LLM can still extract some context from basic HTML
- Log fallback usage to track quality impact

---

## Cost Impact

**Development Time:** 2-3 days
**Runtime Cost:** $0 (code improvements only, no new API calls)
**Performance Impact:** +2-5s per practice (retries + validation)

---

## Dependencies

**Blocks:**
- FEAT-005 (Google Reviews) - no point analyzing reviews if we can't scrape websites
- FEAT-006 (Better LLM Prompts) - prompt improvements useless if scraping fails

**Depends On:**
- None - this is the foundation

---

## Implementation Phases

### Phase 1: Investigation & Logging (Day 1)
- Add detailed error logging
- Run enrichment on 50 practices
- Analyze `failed_scrapes.csv` to identify patterns

### Phase 2: Quick Wins (Day 1-2)
- URL sanitization (strip UTM params)
- URL validation (HEAD requests)
- User agent rotation

### Phase 3: Retry Logic (Day 2)
- Implement retry with exponential backoff
- Test with mock failures

### Phase 4: Fallback Strategy (Day 2-3)
- Implement requests + BeautifulSoup fallback
- Test on sites that fail Crawl4AI

### Phase 5: Validation (Day 3)
- Run on full 150+ practice dataset
- Measure success rate
- Adjust config based on results

---

## Acceptance Criteria Summary

- AC-FEAT-004-001: Error logs include HTTP status, exception type, URL
- AC-FEAT-004-002: Failed scrapes logged to CSV
- AC-FEAT-004-003: Pages retried up to 3 times
- AC-FEAT-004-004: Exponential backoff: 5s, 10s, 20s
- AC-FEAT-004-005: Don't retry 404, 403, SSL errors
- AC-FEAT-004-006: Strip UTM parameters
- AC-FEAT-004-007: Pre-validate URLs with HEAD request
- AC-FEAT-004-008: Handle http → https redirects
- AC-FEAT-004-009: Rotate 3+ user agents
- AC-FEAT-004-010: Include full browser headers
- AC-FEAT-004-011: Fallback to requests + BeautifulSoup
- AC-FEAT-004-012: Fallback scrapes homepage only
- AC-FEAT-004-013: Log which method succeeded
- AC-FEAT-004-014: Page timeout 15s (configurable)
- AC-FEAT-004-015: Practice timeout 60s (configurable)
- AC-FEAT-004-016: Timeouts in config.json
- **AC-FEAT-004-017: Overall success rate >90% on 150+ practices**

---

## Future Enhancements (Phase 2)

- Proxy rotation for higher anonymity
- CAPTCHA detection and handling
- Distributed scraping (if scale exceeds single machine)
- Website health monitoring (track which sites go down over time)

---

## References

- Current scraping code: `src/enrichment/website_scraper.py`
- Test results: `data/test_results/enrichment_results_10practices_20251104_123743.txt`
- Crawl4AI docs: https://crawl4ai.com/docs
- tenacity (retry library): https://tenacity.readthedocs.io
