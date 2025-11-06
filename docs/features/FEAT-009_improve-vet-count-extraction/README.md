# FEAT-009: Improve Vet Count Extraction & Status Tracking

## Overview

This feature improves the extraction and tracking of veterinary practice vet counts - a critical data point for lead qualification. Currently, vet counts are null in ~90% of practices even though the data exists on their websites.

## Documents in This Folder

### Core Planning Documents

- **`prd.md`** - Product Requirements Document
  - Executive summary and problem statement
  - Goals, metrics, and success criteria
  - Acceptance criteria and timeline
  - **Start here for business overview**

- **`analysis.md`** - Deep Technical Analysis
  - Verified real-world test case (Raynham Vet: 3 vets, system shows null)
  - Root cause investigation with 3 hypotheses
  - Data model limitations and constraints
  - **Read this to understand the technical problem**

- **`recommendations.md`** - Implementation Plan
  - 3-part solution approach with risk/effort trade-offs
  - 3 conditional improvement paths (A, B, C)
  - Immediate actions you can take now
  - **Use this to plan implementation**

## Quick Start

### What's the Problem?
Practice vet counts are consistently null in Notion despite being on their websites.
- **Real example:** Raynham Veterinary Hospital has 3 vets, system shows `null`
- **Impact:** Can't filter leads by practice size; missing key ICP metric

### What's the Solution?
- Improve LLM extraction with better prompts
- Add "not_found" status so we know when we searched but found nothing
- Test on 20 real practices to measure accuracy

### What Do I Do First?
1. **Read** `prd.md` (5 minutes)
2. **Read** `analysis.md` (10 minutes)
3. **Review** `recommendations.md` (10 minutes)
4. **Approve** the 3-phase approach
5. **Execute** Phase 1: Update data model (1-2 hours)

## Key Files to Reference

### Feature Documentation
- **README.md** - This file, overview
- **prd.md** - Full requirements and acceptance criteria
- **analysis.md** - Technical deep-dive and root cause
- **recommendations.md** - Implementation plan with 3 paths
- **EXECUTION_CHECKLIST.md** - Step-by-step execution guide

### Code & Config Files
- **Data Model:** `/src/models/enrichment_models.py` (Pydantic validation)
- **Extraction Prompt:** `/config/website_extraction_prompt.txt`
- **Extractor Code:** `/src/enrichment/llm_extractor.py`

### Test Fixtures & Data
- **Test Case Data:** `/tests/fixtures/vet_count_test_cases.json` ⭐ **START HERE FOR BASELINE**
  - 1 completed example: Raynham Veterinary Hospital (3 vets)
  - Template for 19 more test cases (needs manual verification)
  - Instructions for what to include in each case

## Notion Schema Change Required

**Before implementation, update Notion:**

Field: "Vet Count Confidence"
- Current options: `high`, `medium`, `low`
- **Add options:** `not_found`, `error`

Why?
- `not_found` = "We searched but found no vet names visible"
- `error` = "Extraction failed due to technical error"

This allows distinguishing between "no data extracted" (null+null) and "data searched but not available" (null+not_found).

## Effort Estimate

### Phase 1: Setup & Discovery (1-2 hours)
- Update data model + Notion schema
- Low risk, can do immediately

### Phase 2: Baseline Testing (5-7 hours)
- Manually audit 20 vet websites
- Run extraction on each
- Analyze results

### Phase 3: Implementation (2-10 hours)
- Depends on root cause found in Phase 2
- Path A (Prompt fix): 2-4 hours
- Path B (Scraper improvement): 4-8 hours
- Path C (Validation layer): 6-10 hours

## Success Metrics

Before → After

- Vet count populated: ~10% → >70%
- High confidence cases: <5% → >40%
- Accuracy on test cases: Unknown → >85%

## Key Decision Points

1. **Notion schema:** Can we extend select field? YES ✅
2. **Strict filtering:** Only count DVM/Doctor titles? YES ✅
3. **Fallback for "not found":** Use confidence="not_found"? YES ✅
4. **No new columns:** Use existing Vet Count Confidence field? YES ✅

## Next Steps

1. **Stakeholder Review** - Confirm problem & approach
2. **Phase 1 Execution** - Update data model (1-2 hours)
3. **Phase 2 Execution** - Build test data (5-7 hours)
4. **Phase 3 Decision** - Choose improvement path based on findings

---

**Status:** Ready for Planning Phase
**Created:** 2025-11-06
**Last Updated:** 2025-11-06

