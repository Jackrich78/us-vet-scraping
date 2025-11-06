# FEAT-009 Execution Checklist

**Status:** Ready for Phase 1 Execution
**Created:** 2025-11-06
**Last Updated:** 2025-11-06

---

## Phase 1: Data Model Enhancement (1-2 hours, LOW RISK)

### Step 1.1: Update Pydantic Model
**File:** `/src/models/enrichment_models.py`
**Change:** Line 86 - Extend confidence field pattern

```python
# CURRENT:
vet_count_confidence: Optional[str] = Field(
    None,
    pattern="^(high|medium|low)$",
    description="Confidence level: high (explicit list), medium (approximate), low (guessed)"
)

# CHANGE TO:
vet_count_confidence: Optional[str] = Field(
    None,
    pattern="^(high|medium|low|not_found|error)$",
    description="Confidence level: high (explicit), medium (approx), low (estimated), not_found (searched but none found), error (extraction failed)"
)
```

**Validation:**
- [ ] Pattern regex accepts all 5 values
- [ ] Field docstring is clear
- [ ] No other files reference the old pattern

### Step 1.2: Update Extraction Prompt
**File:** `/config/website_extraction_prompt.txt`
**Change:** Add clarification for "not_found" and "error" cases

Insert after line 82 (current vet count instructions):

```
CRITICAL INSTRUCTIONS FOR vet_count_total AND vet_count_confidence:

For HIGH confidence:
- Team/staff page found with explicit veterinarian names + DVM/Doctor titles
- Example: "Dr. Sarah Johnson, DVM" or "Dr. Johnson - Veterinarian"
- Return: vet_count_total = <number>, vet_count_confidence = "high"

For MEDIUM confidence:
- Explicit count mentioned in text but not all individual names listed
- Example: "Our team of 3 veterinarians includes..."
- Return: vet_count_total = <number>, vet_count_confidence = "medium"

For LOW confidence:
- Incomplete information or indirect evidence
- Example: Team page with only owner listed + multiple examining rooms visible
- Return: vet_count_total = <estimated>, vet_count_confidence = "low"

For NOT_FOUND (NEW):
- Team/staff page EXISTS but contains NO names with DVM/Doctor/Veterinarian titles
- Example: Team page shows "John Smith (Practice Manager)" and "Sarah Davis (Receptionist)"
- Return: vet_count_total = null, vet_count_confidence = "not_found"

For ERROR (NEW):
- Extraction failed due to technical issue
- Example: Unable to parse page content or API error
- Return: vet_count_total = null, vet_count_confidence = "error"

DO NOT:
- Count vet techs, assistants, or receptionists
- Guess at counts without explicit evidence
- Return low confidence when should be not_found
```

**Validation:**
- [ ] Instructions are clear and unambiguous
- [ ] New values (not_found, error) explicitly documented
- [ ] Examples provided for each confidence level

### Step 1.3: Update Notion Schema
**Access:** https://www.notion.so (your database)
**Database:** Veterinary Practice Lead Generation
**Field:** "Vet Count Confidence"

**Current Configuration:**
```
Field Type: Select
Options: high, medium, low
```

**New Configuration:**
```
Field Type: Select (unchanged)
Options: high, medium, low, not_found, error
```

**Steps:**
1. Go to Notion database settings
2. Find "Vet Count Confidence" field
3. Click field → Edit options
4. Add option: `not_found` (description: "Team page searched but no vet names found")
5. Add option: `error` (description: "Extraction failed or error occurred")
6. Save

**Validation:**
- [ ] Both new options appear in field
- [ ] Descriptions are visible in Notion UI
- [ ] Existing records with null are unaffected

### Step 1.4: Verify Changes
**Run this to ensure no validation errors:**

```bash
cd /Users/builder/dev/us_vet_scraping

# Test that model validates all confidence values
python3 -c "
from src.models.enrichment_models import VetPracticeExtraction
import json

test_cases = [
    {'vet_count_total': 3, 'vet_count_confidence': 'high'},
    {'vet_count_total': 3, 'vet_count_confidence': 'medium'},
    {'vet_count_total': 3, 'vet_count_confidence': 'low'},
    {'vet_count_total': None, 'vet_count_confidence': 'not_found'},
    {'vet_count_total': None, 'vet_count_confidence': 'error'},
]

for case in test_cases:
    try:
        model = VetPracticeExtraction(**case)
        print(f'✓ {case}')
    except Exception as e:
        print(f'✗ {case}: {e}')
"
```

**Expected Output:**
```
✓ {'vet_count_total': 3, 'vet_count_confidence': 'high'}
✓ {'vet_count_total': 3, 'vet_count_confidence': 'medium'}
✓ {'vet_count_total': 3, 'vet_count_confidence': 'low'}
✓ {'vet_count_total': None, 'vet_count_confidence': 'not_found'}
✓ {'vet_count_total': None, 'vet_count_confidence': 'error'}
```

---

## Phase 2: Baseline Testing (5-7 hours, RESEARCH ONLY)

**Test Data File:** `/tests/fixtures/vet_count_test_cases.json` ⭐ **This is where you record results**

### Step 2.1: Research & Manual Audit
**Goal:** Find 20 Boston-area vet clinics with diverse website/staff page structures
**Record location:** `/tests/fixtures/vet_count_test_cases.json` (has 1 completed example: Raynham Vet)

**Sources:**
- Google Maps: Search "veterinary clinic Boston MA"
- Yelp: Filter to veterinary clinics
- Local listings: Boston Veterinary Medical Association
- Directories: VCA, Banfield, independent clinics

**Diversity Targets (aim for mix):**
- [ ] 5 practices with 1 vet (owner-operated)
- [ ] 7 practices with 2-3 vets
- [ ] 5 practices with 4+ vets
- [ ] 3 practices with no visible staff page or vet names
- [ ] Various website types: modern, outdated, simple

### Step 2.2: Manual Verification
**For each practice:**

1. Visit website and find staff/team page
2. Manually count veterinarians using STRICT criteria:
   - ✅ Count: "Dr. Sarah Johnson, DVM"
   - ✅ Count: "Dr. Johnson - Veterinarian"
   - ✅ Count: "Dr. Johnson (Owner)" on team page
   - ❌ Don't count: "Sarah Johnson, Vet Tech"
   - ❌ Don't count: "Johnson, Practice Manager"

3. Record in `/tests/fixtures/vet_count_test_cases.json`:
   ```json
   {
     "id": "test_XXX",
     "practice_name": "Practice Name",
     "website_url": "https://...",
     "staff_page_url": "https://.../staff",
     "expected_vet_count": 3,
     "expected_confidence": "high",
     "veterinarians": [
       {"name": "Dr. Sarah Johnson", "title": "Owner/Veterinarian", "notes": ""}
     ]
   }
   ```

**Validation:**
- [ ] 20 diverse test cases collected
- [ ] Each has manually verified vet count
- [ ] Vet count is ACCURATE (no guesses)
- [ ] Notes explain any edge cases

### Step 2.3: Run Baseline Extraction
**Create test script:** `/tests/unit/test_vet_count_baseline.py`

```python
import asyncio
import json
from pathlib import Path
from src.enrichment.llm_extractor import LLMExtractor
from src.config.config import VetScrapingConfig

async def baseline_test():
    """Extract vet counts for all 20 test cases and compare."""

    # Load test cases
    test_file = Path('tests/fixtures/vet_count_test_cases.json')
    with open(test_file) as f:
        data = json.load(f)

    results = {
        'total': len(data['test_cases']),
        'matches': 0,
        'mismatches': [],
        'coverage': {'null': 0, 'populated': 0}
    }

    # Run extraction on each
    for test_case in data['test_cases']:
        if test_case['status'] != 'ready_to_test':
            continue

        # Scrape website (using existing pipeline)
        # Extract data (using existing extractor)
        # Compare actual vs expected
        # Record mismatch if differs

        # TODO: Implement extraction call
        pass

    return results

# Run and save results
if __name__ == '__main__':
    results = asyncio.run(baseline_test())

    # Save report
    report_path = Path('data/test_results/vet_count_baseline.json')
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)

    # Print summary
    print(f"\nBaseline Test Results:")
    print(f"Total: {results['total']}")
    print(f"Matches: {results['matches']}")
    print(f"Accuracy: {results['matches']/results['total']*100:.1f}%")
```

**Run:**
```bash
cd /Users/builder/dev/us_vet_scraping
python3 -m pytest tests/unit/test_vet_count_baseline.py -v
```

**Output:** `/data/test_results/vet_count_baseline.json`

### Step 2.4: Analyze Results
**Document findings:**

```markdown
## Baseline Test Results

**Test Date:** [DATE]
**Sample Size:** 20 practices
**Manual Accuracy:** X/20 correct (Y%)

### Coverage Analysis
- Populated (not null): X%
- Null: Y%

### Accuracy Analysis
- High confidence accuracy: X%
- Medium confidence accuracy: Y%
- False positives: X%
- False negatives: Y%

### Failure Patterns
- [Pattern 1]: X practices failed because...
- [Pattern 2]: Y practices failed because...

### Root Cause Diagnosis
Evidence suggests the root cause is:
- [ ] Path A: LLM too conservative (return "not_found" instead of count)
- [ ] Path B: Scraper missing pages (not finding /team, /staff pages)
- [ ] Path C: Hallucinations (returning incorrect counts)

### Recommended Improvement Path
Based on findings, recommend: **Path [A/B/C]**
```

Save to: `/docs/features/FEAT-009_improve-vet-count-extraction/baseline-results.md`

**Validation:**
- [ ] All 20 test cases compared
- [ ] Accuracy percentage calculated
- [ ] Root cause identified
- [ ] Recommended path chosen

---

## Phase 3: Implementation (2-10 hours, CONDITIONAL)

### Step 3.1: Choose Improvement Path

Based on Phase 2 baseline results:

#### If Path A (LLM Prompt Fix): 2-4 hours
- [ ] Rewrite extraction prompt to be more explicit about doctor name extraction
- [ ] Add validation: extracted names must match page content
- [ ] Test on 10-practice sample
- [ ] Review extraction results for false positives
- [ ] Full rollout to all practices

#### If Path B (Scraper Enhancement): 4-8 hours
- [ ] Add more URL patterns: `*people*`, `*practitioners*`, `*our-doctors*`
- [ ] Increase team page character budget from 3000 to 4000+
- [ ] Implement fallback scraping if /team fails
- [ ] Test on 10-practice sample
- [ ] Monitor for regressions in other extractions

#### If Path C (Validation Layer): 6-10 hours
- [ ] Add semantic validation of extracted vet counts
- [ ] Cross-reference with practice size indicators
- [ ] Implement confidence scoring based on evidence quality
- [ ] Add unit tests for validation logic
- [ ] Test on 10-practice sample

---

## Phase 1 Immediate Actions (Can Do Now)

### Immediate Action #1: Update Pydantic Model
**Time:** 15 minutes
**Risk:** NONE (backward compatible)

```bash
# Edit /src/models/enrichment_models.py line 86
# Change pattern from "^(high|medium|low)$" to "^(high|medium|low|not_found|error)$"
```

### Immediate Action #2: Update Extraction Prompt
**Time:** 15 minutes
**Risk:** LOW (better documentation, same extraction)

```bash
# Edit /config/website_extraction_prompt.txt
# Add clarification for "not_found" and "error" cases
```

### Immediate Action #3: Update Notion Schema
**Time:** 5 minutes
**Risk:** NONE (just UI change)

```
Notion → Database → Vet Count Confidence Field
Add options: "not_found", "error"
```

### Immediate Action #4: Verify Changes
**Time:** 5 minutes
**Risk:** NONE (validation only)

```bash
python3 -c "from src.models.enrichment_models import VetPracticeExtraction; ..."
```

**Total Time:** 40 minutes
**Total Risk:** NONE

---

## Post-Implementation Validation

### Validation 1: Unit Tests Pass
```bash
python3 -m pytest tests/unit/test_vet_count_extraction.py -v
```
Expected: All tests pass ✅

### Validation 2: Existing Tests Don't Break
```bash
python3 -m pytest tests/ -v --tb=short
```
Expected: No regressions ✅

### Validation 3: Production Extraction Works
```bash
python3 main.py --limit 5
```
Expected: 5 practices enriched with new confidence values ✅

### Validation 4: Notion Field Updates Work
Open Notion → Check one practice record
Expected: Vet Count Confidence shows "not_found" or "error" if applicable ✅

---

## Rollback Plan (If Needed)

If Phase 3 implementation causes issues:

1. **Revert code changes:**
   ```bash
   git checkout src/models/enrichment_models.py
   git checkout config/website_extraction_prompt.txt
   ```

2. **Revert Notion schema:**
   - Remove `not_found` and `error` options
   - Mark records with those values as null

3. **Resume Phase 2 analysis:**
   - Investigate what went wrong
   - Adjust improvement approach
   - Try different Path (A → B, B → C, etc.)

---

## Stakeholder Sign-Off

**Phase 1 Approval (Data Model):** _______________
**Phase 2 Approval (Test Results):** _______________
**Phase 3 Approval (Implementation):** _______________

---

## Notes & Comments

```
[Space for implementation notes, issues, findings]
```

---

**Document Version:** 1.0
**Last Updated:** 2025-11-06
**Next Review:** After Phase 1 completion
