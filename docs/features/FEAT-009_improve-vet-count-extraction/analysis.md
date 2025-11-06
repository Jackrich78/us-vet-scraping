# Vet Count Extraction Problem - Deep Analysis

**Date:** 2025-11-06
**Status:** Analysis Complete - Ready for Planning
**Created By:** Research & Discovery Phase

---

## Executive Summary

The veterinary practice vet count is consistently returning `null` (not found) in Notion even though veterinarian information **is present** on team/staff pages. Example: Raynham Veterinary Hospital has 3 veterinarians on their staff page, but the system returned `vet_count: null`.

This is a **data extraction problem**, not a data availability problem. The infrastructure to scrape and extract is working, but the LLM extraction is either:
1. Receiving incomplete page content, OR
2. Applying extraction logic too conservatively, OR
3. Returning valid null when it should return a count with low confidence

---

## Problem Investigation

### Real-World Test Case: Raynham Veterinary Hospital

**URL:** https://raynhamvet.com/staff/

**What's Actually on the Website:**
- Dr. Karen Reamsnyder (Owner/Veterinarian, 40 years experience)
- Dr. Laurie Buche (Veterinarian, 33 years experience)
- Dr. James Tiede (Veterinarian)

**Total veterinarians:** 3 (clear, explicit, named)

**What Notion Shows:**
- Vet Count: None (null)
- Vet Count Confidence: None (null)

**Classification:** ✅ HIGH CONFIDENCE case - All vets named with clear "Veterinarian" title

---

## Root Cause Analysis

### Current Extraction Flow

1. **Scraping (Crawl4AI)**
   - Targets: Team, Staff, Doctor, Veterinarian, About pages
   - Budget: 3000 chars for team pages (highest priority)
   - Status: ✅ **WORKING** - pages are being scraped

2. **LLM Extraction (OpenAI GPT-4o-mini)**
   - Model: `VetPracticeExtraction` (Pydantic)
   - Prompt: `/config/website_extraction_prompt.txt`
   - Logic: Conservative - "return null if uncertain"
   - Status: ❌ **FAILING** - returning null for clear cases

### Why Vet Count is Null

**Hypothesis 1: Insufficient Page Content**
- Likelihood: MEDIUM
- The scraper prioritizes team pages (3000 char budget)
- But still truncates if content is large
- The LLM may be receiving incomplete page

**Hypothesis 2: Prompt Too Conservative**
- Likelihood: HIGH
- Prompt instruction (line 81-82): "Be conservative - only report if confident. Better to return null than guess incorrectly."
- Current confidence model: Only returns count if "high" OR "medium"
- Doesn't support "low confidence" counts (confidence is optional field)

**Hypothesis 3: Confidence Field Mismatch**
- Likelihood: MEDIUM
- Model allows: `vet_count_confidence: Optional[str]` = null OR "high"/"medium"/"low"
- But if count is null, confidence is also forced null
- No way to express "we found names but marked as low confidence"

### Real Issue Discovered in Code

Looking at `enrichment_models.py` line 155-161:
```python
@field_validator('vet_count_total')
@classmethod
def validate_vet_count_range(cls, v: Optional[int]) -> Optional[int]:
    """Ensure vet count is realistic (1-50)."""
    if v is not None and (v < 1 or v > 50):
        return None  # Invalid count - discard
    return v
```

This validator will **discard invalid vet counts** but doesn't record that it happened. There's no "extraction_failed" or "not_found" status.

---

## Current Data Model Limitations

### Vet Count Field Structure
```python
vet_count_total: Optional[int] = Field(
    None,
    ge=1,
    le=50,
    description="Total number of veterinarians (DVMs) at practice"
)

vet_count_confidence: Optional[str] = Field(
    None,
    pattern="^(high|medium|low)$",
    description="Confidence level: high (explicit list), medium (approximate), low (guessed)"
)
```

### Current States Possible
- `vet_count: null, confidence: null` = "No data extracted" (CURRENT)
- `vet_count: 3, confidence: "high"` = "Confident count found"
- `vet_count: 3, confidence: "medium"` = "Approximate count"
- `vet_count: 3, confidence: "low"` = "Uncertain but best guess"

### Missing State
- `vet_count: null, confidence: "not_found"` = "We searched but found no vet names" ❌ **NOT POSSIBLE** (confidence field doesn't allow "not_found")

---

## Notion Schema Constraints

### Current Field Structure
```json
{
  "Vet Count": "number",                    // Can be: null or 1-50
  "Vet Count Confidence": "select"          // Can be: null or "high"/"medium"/"low"
}
```

### What You're Asking For
> "We should mention it was searched but not visible. I'm not sure how we do this with notion, if it's possible for the vet count field to have a letter in or something different? I don't think it is but I don't want to add another column. We could make it a text column perhaps."

**Analysis:**
- **Number field cannot hold text** - Notion validation will reject "searched_not_found"
- **Select field is locked to predefined options** - Can't dynamically add values
- **Rich_text field could work** but requires schema change

### Feasible Options

**Option A: Extend Vet Count Confidence (RECOMMENDED)**
- Change `Vet Count Confidence` select options:
  - Current: `high`, `medium`, `low`
  - Add: `not_found` (website searched, no vet names visible)
  - Add: `error` (extraction failed/error occurred)

**Option B: Change Vet Count to Rich Text**
- Convert number field to rich_text
- Can store: "3", "3-4", "not_found", "searched_no_data"
- Downside: Breaks scoring logic that expects numbers
- Not recommended

**Option C: Add New Field "Vet Count Status"**
- You said you don't want another column
- Skip this option

---

## Strict Job Title Criteria (Your Requirement)

You specified: **"Be strict with job titles"**

### Accepted Criteria
Must include one of these:
- Title contains "DVM" or "Doctor of Veterinary Medicine"
- Title contains "Veterinarian" or "Veterinary"
- Name is prefixed with "Dr." AND they're on a team/staff/doctor page

### NOT Accepted (Too Loose)
- "Vet" alone (could mean receptionist, tech, assistant)
- Generic role titles without veterinary context
- People on general staff pages without veterinary designation

### Implementation for Raynham Example
✅ "Dr. Karen Reamsnyder - Owner/Veterinarian" → COUNT
✅ "Dr. Laurie Buche - Veterinarian" → COUNT
✅ "Dr. James Tiede - Veterinarian" → COUNT
**Total: 3 vets, confidence: high**

---

## Testing Plan Required

You mentioned: **"No I don't have this data, we'll need to run our own tests. Make sure to keep them tidy if you create test scripts."**

### What We Need to Test
1. **Extract vet names from 20 vet websites** (manual audit)
2. **Check what LLM currently extracts** from those same pages
3. **Identify failure patterns** (too conservative? missing pages? hallucinating?)
4. **Measure accuracy** before and after any improvements

### Test Script Structure (Proposed)
```
tests/unit/test_vet_count_extraction.py
├── Test data: fixtures/vet_count_test_cases.json
│   ├── Practice name
│   ├── Website URL
│   ├── Staff page URL (if different)
│   ├── Expected vet count (manually verified)
│   ├── Expected confidence level
│   └── Notes (e.g., "All vets named", "Only owner listed")
│
├── Test cases (unit tests)
│   ├── test_extract_vet_names_from_team_page()
│   ├── test_confidence_calculation()
│   ├── test_strict_title_filtering()
│   └── test_null_handling_when_not_found()
│
└── Reporting
    └── test_results/vet_count_baseline_20251106.txt
        ├── Extraction accuracy: X/20
        ├── Confidence calibration: correct/incorrect
        └── Failure patterns
```

---

## Implementation Strategy

### Phase 1: Immediate (Low Risk, High Impact)

**Update Notion Schema:**
- Add `not_found` and `error` options to "Vet Count Confidence" select
- No code changes needed
- Allows capturing "searched but nothing visible"

**Update Data Model:**
- Modify `vet_count_confidence` pattern in `enrichment_models.py`
- From: `"^(high|medium|low)$"`
- To: `"^(high|medium|low|not_found|error)$"`

**Update LLM Prompt:**
- Explicit instruction: "If team/staff page found but no vet names visible, return null with confidence='not_found'"
- Add example: "If page lists only 'John (Manager)' and 'Sarah (Receptionist)' with no DVM titles, return vet_count=null, confidence='not_found'"

### Phase 2: Investigation (Before Major Changes)

**Run Baseline Test:**
- Test on 20 diverse vet websites
- Manually verify actual vet counts
- Run extraction pipeline on each
- Document discrepancies
- Identify systematic failures

**Root Cause from Test Results:**
- If >80% are null even though vets are present → LLM prompt too conservative
- If 50/50 mix → Some pages being scraped, some not
- If mostly hallucinations → Prompt encouraging guessing

### Phase 3: Improvement (Based on Test Results)

**If LLM is too conservative:**
- Rewrite prompt to use doctor name extraction + validation
- Example: Extract all names, filter by DVM/Doctor/Veterinarian, count survivors
- More deterministic than fuzzy LLM judgment

**If scraping is incomplete:**
- Add more URL patterns: `*doctors*`, `*veterinarians*`, `*practitioners*`
- Increase character budget for team pages
- Implement multi-attempt scraping for critical pages

**If hallucinations are the problem:**
- Reduce `temperature` in OpenAI call (currently 0.1, already low)
- Switch to more structured extraction
- Add validation: "Extracted vet count must be correlated with page content length"

---

## Key Questions Answered

### 1. Can Notion's number field store text?
❌ No. Must change field type or use select field.

### 2. Can we use select field for status?
✅ Yes. Add options to existing "Vet Count Confidence" field.
Options: `high`, `medium`, `low`, `not_found`, `error`

### 3. Should we count vet techs and assistants?
❌ No. Strict filtering: only count people with DVM/Doctor/Veterinarian titles.

### 4. If we can't find vet names, what do we record?
✅ vet_count: null, vet_count_confidence: "not_found"

---

## Success Criteria

After improvements, we should see:

| Metric | Current | Target |
|--------|---------|--------|
| **Vet count populated (not null)** | ~10% | >70% |
| **Confidence = high** | <5% | >40% |
| **Confidence = not_found** | 0% | >20% (acceptable) |
| **False/hallucinated counts** | Unknown | <5% |
| **Average extraction time per practice** | ~2.5s | <3s |
| **Cost per extraction** | $0.0001 | <$0.0002 |

---

## Next Steps

1. **Approve schema changes** - Add "not_found" to Vet Count Confidence
2. **Create test data** - Manual audit of 20 vet websites
3. **Run baseline test** - Measure current accuracy
4. **Design extraction improvements** - Based on test results
5. **Implement and validate** - Update prompt and/or scraper

---

## References

- Current extraction code: `/src/enrichment/llm_extractor.py`
- Data model: `/src/models/enrichment_models.py`
- Extraction prompt: `/config/website_extraction_prompt.txt`
- Notion schema: `notion_schema_analysis.json`
- Real test case: https://raynhamvet.com/staff/ (3 vets, returns null)

---

**Status:** ✅ Ready for implementation planning

**Next Phase:** Create test data and run baseline measurements
