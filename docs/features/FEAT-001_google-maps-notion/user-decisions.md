# User Decisions for FEAT-001: Google Maps & Notion Integration

**Decision Date:** 2025-11-03
**Decided By:** User (Project Owner)
**Status:** Approved for Implementation

---

## Decision Summary

All open questions from PRD and research have been resolved with clear decisions. Ready to proceed to `/plan FEAT-001`.

---

## Decisions on Open Questions

### 1. Cost Increase Acceptance ✅ APPROVED
**Question:** Actual Apify cost is $1.08 per run (not $0.90). Accept 20% increase?
**Decision:** YES - Acceptable so long as total stays below $3 per full run
**Rationale:** Filter charges ($0.36) are necessary for quality filtering
**Impact:** Update PRD and budget documentation

### 2. Partial Results Handling ✅ APPROVED
**Question:** Accept <150 practices or fail pipeline?
**Decision:** ACCEPT PARTIAL with de-duplication
**Rationale:** MA may not have 150 qualifying practices, can re-run and expand if necessary
**Impact:** Log warning, don't fail, ensure de-duplication works on re-runs

### 3. Configurable Filter Thresholds ✅ APPROVED
**Question:** Make min_reviews, require_website configurable in config.json?
**Decision:** YES - Add to config.json
**Requirements:**
- Add `filtering.min_reviews` (default: 10)
- Add `filtering.require_website` (default: true)
- Add `target.location` to support multi-geography (default: "Massachusetts, USA")
**Impact:** Create FilteringConfig and TargetConfig in Pydantic models

### 4. Test Mode Behavior ✅ APPROVED
**Question:** Should test mode use different area or just limit results?
**Decision:** KEEP SAME AREA (Massachusetts) - Just limit to 10 results
**Rationale:** More realistic testing with actual target geography
**Impact:** `--test` flag limits max_results to 10, same search area

### 5. Apify Result Caching ✅ APPROVED
**Question:** Cache Apify results during development to save costs?
**Decision:** YES - Simple JSON cache with timestamp (development only)
**Requirements:**
- File-based cache: `data/raw/apify_cache_{location}_{date}.json`
- 24-hour TTL (Time To Live)
- Bypass cache with `--no-cache` flag
- Disabled in production
**Impact:** Saves $5-10 during development iterations

### 6. Temporarily Closed Practices ✅ APPROVED
**Question:** Filter out temporarily closed practices?
**Decision:** KEEP THEM - They may reopen
**Rationale:** Worth tracking for future outreach when they reopen
**Impact:** Only filter permanently closed, mark temporarily closed in Notion

---

## Additional Implementation Requirements

### Configuration Changes Required

Update `config/config.json` with:

```json
{
  "target": {
    "location": "Massachusetts, USA",  // NEW: Configurable location
    "search_terms": [
      "veterinary clinic in Massachusetts",
      "animal hospital in Massachusetts",
      "vet clinic in Massachusetts"
    ],
    "search_radius_miles": null,
    "excluded_cities": []
  },
  "filtering": {
    "min_reviews": 10,              // NEW: Configurable threshold
    "require_website": true,        // NEW: Configurable requirement
    "exclude_closed": true
  },
  "apify": {
    "cache_enabled": true,          // NEW: Development cache
    "cache_directory": "data/raw",   // NEW: Cache location
    "cache_ttl_hours": 24            // NEW: Cache expiration
  }
}
```

### Cost Budget Constraints

**Hard Limit:** $3.00 per full run
**Current Estimate:** $1.08 per run (within budget)
**Buffer:** $1.92 remaining (180% headroom)

**Cost Breakdown:**
- Apify base: $0.72 (180 places × $0.004)
- Apify filters: $0.36 (180 × $0.001 × 2 filters)
- Notion: $0.00 (free tier)
- **Total: $1.08**

### Test Mode Requirements

**Test Mode Specifications:**
- Trigger: `--test` flag OR `TEST_MODE=true` env var
- Behavior: Limit to 10 practices
- Location: Same as production (Massachusetts)
- Estimated cost: $0.05 (21× cheaper than full run)
- Use for: Development, CI/CD, integration testing

### Development Cache Requirements

**Cache Implementation:**
- Location: `data/raw/apify_cache/`
- Filename: `{location_slug}_{date}.json`
- Example: `massachusetts_2025-11-03.json`
- TTL: 24 hours (auto-expire)
- Bypass: `--no-cache` flag
- Environment: Development only (disabled in production)

---

## Research Validation Status

### ✅ All Research Questions Answered

| Question # | Topic | Confidence | Status |
|------------|-------|------------|--------|
| 1 | Apify actor capabilities | High | ✅ Validated |
| 2 | Apify caching | High | ✅ Decided (YES) |
| 3 | Partial results handling | High | ✅ Decided (ACCEPT) |
| 4 | Cost validation | High | ✅ Validated ($1.08) |
| 5 | Configurable filters | High | ✅ Decided (YES) |
| 6 | Temporarily closed | High | ✅ Decided (KEEP) |
| 7 | De-duplication strategy | High | ✅ Validated |
| 8 | Batch size | High | ✅ Validated (10, 0.35s) |
| 9 | Schema validation | High | ✅ Decided (Basic + fields) |
| 10 | Field preservation | High | ✅ Validated (auto-preserve) |
| 11 | Retry logic | High | ✅ Validated (exponential + jitter) |
| 12 | Rate limit handling | High | ✅ Validated (0.35s delay) |

### ✅ Deep Dive Edge Cases Researched

| Topic # | Edge Case Category | Confidence | Status |
|---------|-------------------|------------|--------|
| 7 | Apify output edge cases | High | ✅ Documented |
| 8 | Notion type conversion | High | ✅ Documented |
| 9 | Place ID reliability | High | ✅ Fallback strategy |
| 10 | Rate limit behavior | High | ✅ Adaptive pattern |
| 11 | Error recovery | High | ✅ DLQ pattern |
| 12 | Config validation | High | ✅ Pre-flight checks |

---

## Implementation Readiness Checklist

### Planning Phase Prerequisites ✅

- [x] All open questions answered with high confidence
- [x] Cost validated and within budget ($1.08 < $3.00)
- [x] User decisions documented
- [x] Edge cases researched and patterns identified
- [x] Configuration schema defined
- [x] De-duplication strategy validated
- [x] Rate limiting strategy confirmed
- [x] Error handling patterns specified
- [x] Cache strategy approved
- [x] Test mode requirements defined

### Ready for `/plan FEAT-001` ✅

**Documentation Complete:**
- ✅ PRD: `docs/features/FEAT-001_google-maps-notion/prd.md`
- ✅ Research: `docs/features/FEAT-001_google-maps-notion/research.md` (12 topics)
- ✅ User Decisions: `docs/features/FEAT-001_google-maps-notion/user-decisions.md` (this file)

**Next Step:** Run `/plan FEAT-001` to create:
- `architecture.md` - Detailed technical architecture
- `acceptance.md` - Acceptance criteria (appended to `/AC.md`)
- `testing.md` - Comprehensive test strategy
- `manual-test.md` - Manual testing procedures

---

## Notes for Planning Phase

### Key Implementation Considerations

1. **Composite Key Fallback:** Place ID can be obsolete (>12 months), implement multi-level de-duplication:
   - Level 1: Google Place ID (primary)
   - Level 2: Phone number (normalized to E.164)
   - Level 3: Website URL (normalized, no www/https)
   - Level 4: Name + Address hash (last resort)

2. **Adaptive Rate Limiting:** Start with 0.35s delay, adjust based on 429 responses:
   - 0 hits → maintain 0.35s
   - 1-3 hits → increase to 0.5s
   - 4+ hits → increase to 1.0s
   - Reset after 100 successful requests

3. **Dead Letter Queue (DLQ):** Failed records go to `data/failed/notion_dlq_{timestamp}.json`
   - Retry transient errors only (max 3 attempts)
   - Permanent failures (validation errors) → skip, log reason
   - DLQ can be manually reviewed and reprocessed

4. **Pre-Flight Checks:**
   - Validate Apify API token (test call)
   - Validate Notion integration access (retrieve database)
   - Check required Notion fields exist (Practice Name, Address, Phone, Google Place ID)
   - Validate config.json schema (Pydantic)
   - Check location string format (not empty, reasonable length)

5. **Edge Case Handling:**
   - Missing Place ID → use composite key
   - Invalid URL → attempt sanitization, skip if fails
   - Null vs 0 review count → distinguish (null = no data, 0 = verified zero)
   - Incomplete address → parse ZIP from full address string
   - International phone → normalize to E.164 format

---

**Approved for Implementation:** ✅
**Date:** 2025-11-03
**Next Action:** `/plan FEAT-001`
