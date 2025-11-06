# Vet Count Extraction - Recommendations & Implementation Plan

**Date:** 2025-11-06
**Status:** Ready for Feature Planning
**Audience:** Implementation team + Product owner

---

## Problem Statement (Verified)

Veterinary practice vet counts are consistently null in Notion despite being available on team/staff pages.

**Real test case:**
- Practice: Raynham Veterinary Hospital
- Staff page: https://raynhamvet.com/staff/
- Actual vets: 3 (Dr. Karen Reamsnyder, Dr. Laurie Buche, Dr. James Tiede)
- Notion shows: null

**Impact:** Missing critical ICP qualification metric - practice size is a key decision-making factor.

---

## Root Cause (Determined)

### Not a Scraping Problem
✅ The Crawl4AI scraper successfully identifies and scrapes team/staff pages.
- Team pages get highest priority (3000 character budget)
- Pages matching `*team*`, `*staff*`, `*doctors*` patterns are being captured

### Likely Extraction Problem
❌ The LLM extraction prompt/model is too conservative or receiving incomplete data.

**Evidence:**
- Model has validator that discards counts outside 1-50 range
- Confidence field allows "high/medium/low" but current extraction returns null+null when uncertain
- No "searched but not found" status available
- Prompt instruction: "Be conservative - only report if confident. Better to return null than guess incorrectly."

### Data Model Missing State
The current model cannot express: "We found no vet names on this page even though we searched"

---

## Recommended Solution (3-Part Approach)

### Part 1: Data Model Enhancement (NO CODE - Config Only)

**Change:** Extend Notion "Vet Count Confidence" field to include status values

**Current options:** `high`, `medium`, `low`
**New options:** `high`, `medium`, `low`, `not_found`, `error`

**When to use each:**
- `high`: Team page with explicit vet names and DVM/Doctor titles (e.g., "Dr. Smith, DVM")
- `medium`: Vet count mentioned in text but not all names listed (e.g., "Our 3 veterinarians serve...")
- `low`: Estimated count from incomplete info (e.g., partial team page with only some vets named)
- `not_found`: **NEW** - Team page exists but no vet names visible (e.g., page lists only manager names)
- `error`: **NEW** - Extraction failed due to technical error

**Implementation:**
1. Open Notion database
2. Edit "Vet Count Confidence" field properties
3. Add options: `not_found`, `error`
4. Save

**Code changes needed:**
- `/src/models/enrichment_models.py` line 86: Update pattern from `^(high|medium|low)$` to `^(high|medium|low|not_found|error)$`
- `/config/website_extraction_prompt.txt` line 82: Add clarity about "not_found" case

---

### Part 2: Baseline Testing (NO CODE - Research Only)

**Goal:** Understand current extraction accuracy before making improvements

**What to do:**
1. Identify 20 diverse Boston-area vet clinics
2. Manually visit their staff pages
3. Count actual veterinarians (strict criteria: DVM/Doctor/Veterinarian titles)
4. Record their extraction result (what the system currently returns)
5. Analyze patterns of mismatches

**Strict Criteria (Your Requirement):**
- ✅ Count: "Dr. Sarah Johnson, DVM"
- ✅ Count: "Dr. Johnson - Veterinarian"
- ✅ Count: "Dr. Johnson (Owner)" on a team page
- ❌ Don't count: "Sarah Johnson, Vet Tech"
- ❌ Don't count: "Johnson, Practice Manager"

**Expected findings:**
- Baseline accuracy: ~20-40% (many nulls on valid practices)
- Confidence calibration: Are "high" ones actually correct?
- Failure patterns: Too conservative? Missing pages? Hallucinating on some?

**Deliverable:** `/tests/fixtures/vet_count_test_cases.json` (created, needs 19 more entries)

---

### Part 3: Extraction Improvement (CODE - After Testing)

**Decision point:** Based on baseline test results, choose improvement path:

#### Path A: If >70% of nulls are on pages with visible vet names
**Root cause:** LLM prompt too conservative
**Solution:** Rewrite prompt to be more explicit about doctor name extraction
**Effort:** 2-4 hours
**Risk:** Low (prompt-only change, no architecture change)

**New prompt approach:**
```
1. Look for any mention of "Dr. " followed by a name on team/staff pages
2. Check if the title or context includes: DVM, veterinarian, doctor, vet
3. Extract and count matching names
4. Confidence = "high" if explicitly titled veterinarian
5. Confidence = "low" if inferred from "Dr. " prefix without explicit vet title
6. If no matches found, return null + confidence="not_found"
```

#### Path B: If >50% of nulls are due to missing/incomplete pages
**Root cause:** Scraper not capturing all team pages
**Solution:** Add more URL patterns, increase character budget, implement fallback scraping
**Effort:** 4-8 hours
**Risk:** Medium (scraper changes could affect other extractions)

**Approach:**
- Add patterns: `*people*`, `*practitioners*`, `*our-doctors*`, `*veterinarians*`
- Increase team page budget from 3000 to 4000+ chars
- Implement fallback: if /team fails, try /staff, /doctors, /about

#### Path C: If hallucinations/errors are common
**Root cause:** LLM is guessing when unsure
**Solution:** More structured extraction, additional validation
**Effort:** 6-10 hours
**Risk:** Higher (requires new validation logic)

**Approach:**
- Use function calling or structured extraction for more determinism
- Validate extracted count against page content length/team page structure
- Add semantic validation: "Does this vet count make sense given the website size?"

---

## Immediate Actions (Can Start Now)

### Action 1: Update Data Model (1 hour)

**File:** `/src/models/enrichment_models.py`

**Current (line 84-88):**
```python
vet_count_confidence: Optional[str] = Field(
    None,
    pattern="^(high|medium|low)$",
    description="Confidence level: high (explicit list), medium (approximate), low (guessed)"
)
```

**Change to:**
```python
vet_count_confidence: Optional[str] = Field(
    None,
    pattern="^(high|medium|low|not_found|error)$",
    description="Confidence level: high (explicit), medium (approx), low (estimated), not_found (searched but none found), error (extraction failed)"
)
```

**File:** `/config/website_extraction_prompt.txt`

**Add to line 81-82 instructions:**
```
If team/staff page exists but contains NO names with DVM, Doctor, or Veterinarian titles:
  → Return vet_count_total: null
  → Return vet_count_confidence: "not_found"

If extraction fails due to error:
  → Return vet_count_total: null
  → Return vet_count_confidence: "error"
```

**Notion:** Add `not_found` and `error` options to "Vet Count Confidence" select field (manual action)

### Action 2: Create Test Framework (2-3 hours)

**File:** `/tests/unit/test_vet_count_extraction.py` (create new)

**Structure:**
```python
import pytest
from src.enrichment.llm_extractor import LLMExtractor

class TestVetCountExtraction:
    """Baseline tests for vet count extraction accuracy."""

    @pytest.mark.parametrize("practice_id,expected_count,expected_confidence", [
        ("test_001", 3, "high"),  # Raynham - 3 explicit vets
        ("test_002", None, "not_found"),  # No vets on page
        ("test_003", 2, "medium"),  # 2 vets mentioned but not all named
    ])
    def test_vet_count_accuracy(self, practice_id, expected_count, expected_confidence):
        """Test extraction against known good data."""
        # Load test case from fixture
        # Run extraction
        # Compare actual vs expected
        # Report mismatch
        pass
```

**Test data:** `/tests/fixtures/vet_count_test_cases.json` (created, needs population)

---

## Timeline & Effort Estimate

### Week 1: Setup & Baseline
- **Day 1-2:** Update data model (1 hour), Create test framework (2 hours)
- **Day 3-5:** Manual audit of 20 vet websites (4-5 hours)
  - Research Boston vet clinics
  - Visit staff pages
  - Record actual counts
  - Document in test_cases.json

**Deliverable:** Baseline test data + discovery report

### Week 2: Analysis & Planning
- **Day 1-2:** Run extraction pipeline on all 20 test cases (1 hour automated, 1 hour analysis)
- **Day 3:** Analyze results and identify improvement path (A, B, or C)
- **Day 4-5:** Create detailed improvement plan with examples

**Deliverable:** Root cause diagnosis + specific improvement recommendations

### Week 3+: Implementation (Conditional)
Based on baseline findings, implement Path A, B, or C
- **Path A (prompt fix):** 2-4 hours
- **Path B (scraper improvement):** 4-8 hours
- **Path C (validation layer):** 6-10 hours

---

## Success Metrics

### Before Improvement
- Vet count populated (not null): ~10%
- Null rate on practices with visible vets: >70%
- Confidence = high: <5%
- Confidence = not_found: 0%

### After Improvement (Target)
- Vet count populated: >70%
- Accuracy on test cases: >85%
- Confidence = high: >40%
- Confidence = not_found: 15-25%
- False/hallucinated counts: <5%

---

## Risk Assessment

### Risk 1: Changing extraction prompt breaks other fields
**Likelihood:** MEDIUM
**Mitigation:** Test on small sample (10 practices) before full rollout; compare all fields, not just vet count

### Risk 2: Not finding enough test data
**Likelihood:** LOW
**Mitigation:** Boston has 300+ vet clinics; easy to find 20 diverse examples

### Risk 3: LLM hallucinations on low-confidence cases
**Likelihood:** MEDIUM
**Mitigation:** Validate extracted count against page structure; use "not_found" liberally

### Risk 4: Scraper changes break existing functionality
**Likelihood:** LOW if Path B needed
**Mitigation:** Only extend patterns, don't change existing ones; test on full existing database

---

## Open Questions Answered

**Q: Can Notion number field store text?**
A: No. Use select field with predefined options instead.

**Q: Do we need a new column for status?**
A: No. Extend existing "Vet Count Confidence" field with new options (not_found, error).

**Q: How strict on job titles?**
A: Strict. Only count if title contains DVM, Doctor, or Veterinarian (or Dr. prefix with vet context).

**Q: What if page says "searched but not found"?**
A: Return vet_count: null, confidence: "not_found"

---

## Dependencies & Blockers

### Notion Schema (Blocking)
- Must add `not_found` and `error` options to "Vet Count Confidence" field before testing

### Test Data (Blocking)
- Must populate 20 test cases with manual verification before baseline run

### No code blockers identified
- All improvements can be made to extraction prompt or scraper
- No architectural changes needed

---

## Next Steps

1. **Approve this approach** - Confirm 3-part plan makes sense
2. **Execute Part 1** - Update data model + Notion schema (1 hour, low risk)
3. **Execute Part 2** - Run baseline testing (5-7 hours, research only)
4. **Review findings** - Identify root cause and choose improvement path
5. **Execute Part 3** - Implement specific improvements (2-10 hours depending on path)

---

## Reference Documents

- **Problem Analysis:** `/docs/features/VET_COUNT_PROBLEM_ANALYSIS.md`
- **Test Data:** `/tests/fixtures/vet_count_test_cases.json`
- **Extraction Code:** `/src/enrichment/llm_extractor.py`
- **Data Model:** `/src/models/enrichment_models.py`
- **Current Prompt:** `/config/website_extraction_prompt.txt`

---

**Created:** 2025-11-06
**Status:** Ready for approval and execution
**Next Phase:** Stakeholder review and timeline confirmation
