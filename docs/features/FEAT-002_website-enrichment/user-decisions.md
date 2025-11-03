# User Decisions: FEAT-002 Website Enrichment

**Feature ID:** FEAT-002
**Decision Date:** 2025-11-03
**Decision Maker:** User
**Status:** Final

## Overview

This document captures all user decisions made during the exploration phase of FEAT-002. These decisions resolve ambiguities in the PRD and guide implementation.

---

## Decision 1: Scraping Scope & Strategy

**Question:** Should we scrape homepage only, or also /about and /team pages?

**Options:**
- A. Homepage ONLY (faster, simpler, lower cost - originally recommended in PRD)
- B. Homepage + `/about` + `/team` pages (more data, higher accuracy, 3x longer execution time)

**Decision:** **Option B** - Multi-page scraping (homepage + /about + /team pages)

**Rationale:** User prioritizes **quality over speed**. Decision makers and vet names are often found on /team pages that homepage misses.

**Impact:**
- **Execution time:** 10-12 minutes for 150 practices (vs. 5.5 min for homepage only)
- **Data quality:** 2-3x better decision maker detection rate
- **Cost:** ~$0.40 for OpenAI (vs. $0.10 for homepage only)
- **Implementation:** Use Crawl4AI BFSDeepCrawlStrategy with URL pattern filtering

---

## Decision 2: Extraction Confidence & Human Review

**Question:** What should happen with low-confidence extractions (e.g., vet count confidence = "low")?

**Options:**
- A. Accept all extractions, just flag them in Notion with confidence level
- B. Skip low-confidence practices entirely (don't update Notion)
- C. Set a specific field like "Needs Manual Review" = true for confidence < "high"

**Decision:** **Option A** - Accept all extractions, flag with confidence level

**Rationale:** Maximize coverage, let sales team decide whether to use low-confidence data. Better to have uncertain data than no data.

**Impact:**
- **Coverage:** All 150 practices enriched (no skips)
- **Notion field:** "Vet Count Confidence" shows high/medium/low
- **Sales workflow:** Reps can filter by confidence level if needed

---

## Decision 3: Decision Maker Email Pattern Guessing

**Question:** Should we "intelligently guess" emails like `owner@domain.com` if we find a pattern like `staff@domain.com`?

**Options:**
- A. Yes, guess emails based on patterns and mark as "pattern_guessed"
- B. No, only include emails explicitly found on the website
- C. Guess, but validate them in a future feature (SMTP check)

**Decision:** **Option B** - Only include explicitly found emails

**Rationale:** Data integrity over coverage. Guessed emails may bounce, harm sender reputation, or flag as spam.

**Impact:**
- **Email capture rate:** ~50% (vs. ~70% with guessing)
- **Data quality:** 100% verified emails (found on website)
- **Deliverability:** No risk of guessed emails bouncing
- **PRD update:** Remove "pattern_guessed" logic from extraction prompt

---

## Decision 4: Personalization Context Quality Bar

**Question:** What's the minimum quality bar for personalization context (e.g., require 2 specific facts or accept generic facts)?

**Options:**
- A. Require at least 2 specific facts (current PRD), fail extraction if can't find them
- B. Accept 1-2 generic facts if that's all the website has
- C. Allow empty personalization context, mark for manual research

**Decision:** **Option B** - Accept 1-2 generic facts if that's all available

**Rationale:** Be flexible with quality bar. Some small practices have minimal website content. Generic facts are better than no facts.

**Impact:**
- **Coverage:** Higher success rate for small practice websites
- **Quality:** May include generic facts like "family-owned" or "serving community since 1985"
- **Sales workflow:** Reps can use generic facts as conversation starters
- **Extraction prompt:** Update to accept flexible quality

---

## Decision 5: Caching Strategy During Development

**Question:** Should we cache scraped HTML to disk for faster iteration during development?

**Options:**
- A. Cache all scraped HTML to disk (helpful for dev/debugging, uses disk space)
- B. No caching (re-scrape every time, slower iteration)
- C. Cache only during `--test` mode

**Decision:** **Option A** - Cache all scraped HTML to `data/website_cache/`

**Rationale:** Faster iteration during development and debugging. Disk space is cheap. Can disable cache for production runs.

**Impact:**
- **Development speed:** ~10x faster iteration (no re-scraping during LLM prompt tuning)
- **Disk usage:** ~150 MB for 150 practices × 4 pages × 250 KB per page
- **Implementation:** Use Crawl4AI `cache_mode="enabled"` config
- **Production:** Can set `cache_mode="bypass"` or `cache_mode="disabled"` for production runs

---

## Decision 6: Error Handling for Partial Failures

**Question:** If 10/150 websites fail (timeouts, 404s), what happens?

**Options:**
- A. Continue with 140 successful scrapes, log the 10 failures
- B. Fail the entire job if > 5% fail
- C. Retry all failures once at the end of the job

**Decision:** **Option C** - Retry failures once at end, then log to Notion if still failing

**Rationale:** Maximize success rate with retry, but don't block pipeline on transient failures.

**Impact:**
- **Success rate:** ~95-98% (retry recovers ~50% of transient failures)
- **Execution time:** +1-2 minutes for retry batch
- **Error tracking:** Failed practices logged to Notion with error reason
- **Notion field:** "Enrichment Status" = "Failed" + "Enrichment Error" field for error message

---

## Decision 7: Notion Update Strategy (Re-enrichment)

**Question:** What if a practice was already enriched (enrichment_status = "Completed")? Should we re-enrich?

**Options:**
- A. Skip it entirely (don't re-enrich)
- B. Re-enrich and overwrite existing enrichment data
- C. Only re-enrich if enrichment is > 30 days old

**Decision:** **Option C** - Only re-enrich if > 30 days old

**Rationale:** Website data changes over time (new vets, new services). Re-enrich periodically, but not every run.

**Impact:**
- **Notion query filter:**
  ```python
  {
      "or": [
          {"property": "Enrichment Status", "select": {"does_not_equal": "Completed"}},
          {"property": "Last Enrichment Date", "date": {"before": "30_days_ago"}}
      ]
  }
  ```
- **Recurring runs:** Can re-run pipeline monthly to refresh stale data
- **Cost:** Only pay for re-enrichment if data is stale (not every practice every run)

---

## Decision 8: Test Mode Scope

**Question:** How should test mode (`--test` flag) select the 10 practices to enrich?

**Options:**
- A. Select the first 10 practices from Notion (whatever order Notion returns)
- B. Select 10 practices randomly for better test coverage
- C. Select specific practices by Place ID (hardcode known-good test cases)

**Decision:** **Option A** - Select first 10 practices from Notion query

**Rationale:** Simplest implementation. No need for random selection or hardcoded IDs for MVP.

**Impact:**
- **Implementation:** `limit=10` in Notion query when `--test` flag is set
- **Test coverage:** Tests whatever practices happen to be first in Notion database
- **Determinism:** Same 10 practices every run (unless Notion database changes)

---

## Decision 9: Cost Monitoring & Alerts

**Question:** How should we track OpenAI costs? Passive logging or active monitoring with abort?

**Options:**
- A. Log estimated costs at the end (passive tracking)
- B. Log costs per batch (10 practices) during execution
- C. Set a cost threshold and abort if exceeded (e.g., >$1.00)

**Decision:** **Option C** - Set $1.00 cost threshold and abort if exceeded

**Rationale:** Proactive cost control prevents runaway costs from bugs or misconfiguration.

**Impact:**
- **Cost threshold:** $1.00 hard limit
- **Implementation:** Use `tiktoken` to count tokens before each API call, track cumulative cost, raise exception if threshold exceeded
- **Execution:** Pipeline aborts immediately when $1.00 limit reached
- **Error message:** Clear error message with total cost and practices enriched before abort
- **Configuration:** Make threshold configurable in `config.json` (default: $1.00)

---

## Decision 10: Integration with FEAT-003 (Lead Scoring)

**Question:** Should enrichment automatically trigger scoring, or should scoring happen separately?

**Options:**
- A. FEAT-002 only enriches, scoring happens separately when you run FEAT-003
- B. FEAT-002 automatically triggers scoring after enrichment
- C. FEAT-002 calculates a preliminary score (0-100), FEAT-003 refines it

**Decision:** **Option B** - Automatic trigger preferred

**Rationale:** Streamlined workflow. Enrichment → scoring → ready for outreach happens automatically without manual steps.

**Impact:**
- **Dependency:** FEAT-002 depends on FEAT-003 (scoring service must be implemented)
- **Implementation order:** FEAT-003 must be implemented before FEAT-002 can auto-trigger (or make trigger optional)
- **Configuration:** `auto_trigger_scoring: true` in `config.json` (can be disabled for testing)
- **Architecture:** Use synchronous trigger with dependency injection (simple for MVP)
- **Phase 2:** Refactor to asynchronous event bus if needed

**Note:** First implementation of FEAT-002 won't have auto-trigger ready (FEAT-003 not implemented yet). Add auto-trigger in FEAT-002 v2 after FEAT-003 is complete.

---

## Summary of Impacts

### Execution Time
- **Original estimate:** 5.5 minutes (homepage only)
- **New estimate:** 10-12 minutes (multi-page scraping) + 1-2 min (retry) = **~12-14 minutes total**

### Cost
- **Original estimate:** $0.10 (OpenAI)
- **New estimate:** $0.40 (OpenAI for 150 practices × 4 pages) + buffer = **$0.50 total**
- **Cost threshold:** $1.00 hard limit (abort if exceeded)

### Data Quality
- **Decision maker emails:** 50% capture rate (explicitly found only, no guessing)
- **Vet count accuracy:** 2-3x better (multi-page scraping finds /team pages)
- **Personalization context:** Flexible quality (accept generic facts if needed)

### Coverage
- **Re-enrichment:** Only practices > 30 days old (not every practice every run)
- **Low-confidence extractions:** Accept all, flag with confidence level
- **Failed scrapes:** Retry once, then log to Notion with error message

### Architecture
- **Caching:** Enabled for development (faster iteration)
- **Auto-trigger scoring:** Synchronous trigger with dependency injection (FEAT-002 → FEAT-003)
- **Test mode:** First 10 practices from Notion query

---

## PRD Updates Required

Based on these decisions, the following sections of the PRD must be updated:

1. **Architecture:** Add BFSDeepCrawlStrategy for multi-page scraping
2. **Component Details → WebsiteScraper:** Update to use deep crawling, max_pages=5, URL pattern filtering
3. **Component Details → LLMExtractor:** Remove email guessing logic, update personalization quality bar
4. **Component Details → EnrichmentOrchestrator:** Add retry logic for failed scrapes, cost tracking with $1.00 abort
5. **Notion Enrichment Update:** Add re-enrichment filter (> 30 days old)
6. **Configuration:** Add caching, cost threshold, auto_trigger_scoring flags
7. **Testing Strategy:** Update for multi-page scraping tests, cost tracking tests
8. **Acceptance Criteria:** Update for new execution time (12-14 min), cost ($0.50), and data quality targets
9. **Cost:** Update total cost to $0.50 (was $0.10)
10. **Timeline Estimate:** Update to 6 hours (was 4 hours) due to multi-page scraping + cost tracking complexity
11. **Integration:** Add synchronous trigger to FEAT-003 (auto-trigger scoring)

---

**Decisions Finalized:** ✅
**PRD Update Required:** Yes
**Next Step:** Update PRD, then proceed to `/plan FEAT-002`
