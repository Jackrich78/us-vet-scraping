# FEAT-009: Improve Vet Count Extraction & Status Tracking

**Feature ID:** FEAT-009
**Title:** Improve Vet Count Extraction & Status Tracking
**Status:** Planning Phase
**Created:** 2025-11-06
**Updated:** 2025-11-06

---

## Executive Summary

Veterinary practice vet counts are consistently missing (null) in the Notion database despite being available on practice websites. This is a critical ICP qualification metric - practice size directly impacts lead quality. The goal is to improve extraction accuracy and add transparent status tracking when vet counts cannot be determined.

---

## Problem Statement

### Current Situation
- **Vet count field population rate:** ~10% (90% are null)
- **Real-world example:** Raynham Veterinary Hospital has 3 explicit veterinarians on their public staff page, but Notion shows: `vet_count: null`
- **Impact:** Missing key qualification metric; cannot reliably filter leads by practice size

### Root Cause
- Extraction logic is overly conservative
- Data model cannot express "we searched but found no vet names"
- No distinction between "no data extracted" and "no data available"

### User Impact
Sales team cannot:
- Filter leads by practice size (1 vet vs 5+ vets are very different prospects)
- Trust the vet count field since it's mostly null
- Know if a null value means "not found" or "we didn't look"

---

## Goals & Success Metrics

### Primary Goals
1. **Increase vet count data availability** from ~10% to >70% of practices
2. **Add transparent status tracking** for when vet counts cannot be found
3. **Maintain accuracy** (no hallucinated/incorrect counts)
4. **Preserve extraction cost** (no significant API cost increases)

### Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Vet count populated (not null) | ~10% | >70% |
| Cases marked "high" confidence | <5% | >40% |
| Cases marked "not_found" status | 0% | 15-25% |
| False/hallucinated counts | Unknown | <5% |
| Extraction time per practice | ~2.5s | <3s |
| Cost per extraction | ~$0.0001 | <$0.0002 |

---

## Scope & Constraints

### In Scope
- Improving vet count extraction from team/staff pages
- Adding "not_found" and "error" status values to confidence field
- Testing extraction accuracy on 20 diverse vet practices
- Identifying and fixing root cause (prompt vs scraper vs validation)

### Out of Scope
- LinkedIn vet discovery (separate FEAT-007)
- Google Reviews mention extraction (separate FEAT-005)
- Multi-location vet count breakdown
- Extracting individual vet specialties

### Constraints
- **Notion field types:** Cannot change "Vet Count" from number type; must extend "Vet Count Confidence" select instead
- **API cost:** Cannot exceed current $0.10/lead budget
- **Extraction speed:** Must complete in <3 seconds per practice
- **Strict filtering:** Only count people with explicit DVM/Doctor/Veterinarian titles (not vet techs/assistants)

---

## Requirements

### Functional Requirements

#### FR-1: Improve Vet Count Extraction
- System shall identify veterinarians listed on practice team/staff pages
- System shall count only people with explicit DVM, Doctor, or Veterinarian titles
- System shall return a count (not null) when >80% confident in the count

#### FR-2: Add Status Tracking
- System shall distinguish between:
  - `confidence="high"`: Explicit team page with vet names
  - `confidence="medium"`: Approximate count from context
  - `confidence="low"`: Estimated from limited info
  - `confidence="not_found"`: Team page exists but no vet names visible
  - `confidence="error"`: Extraction failed due to technical error

#### FR-3: Maintain Accuracy
- Extracted vet counts shall match manually verified actual counts with >85% accuracy on test cases
- Confidence levels shall be calibrated (high confidence = correct >90% of time)
- No hallucinated counts (system should return "not_found" rather than guess)

#### FR-4: Cost Control
- Extraction cost shall remain <$0.0002 per practice
- No additional API calls required beyond current extraction pipeline
- Execution time shall remain <3 seconds per practice

### Non-Functional Requirements

#### NF-1: Data Quality
- Vet count must be within realistic range (1-50)
- Invalid counts shall be discarded and marked as "error"

#### NF-2: Backward Compatibility
- Existing extraction logic shall remain intact (no breaking changes)
- Improvements shall be additive (enhancements to prompt, not removal of existing logic)

#### NF-3: Testing
- Baseline test data created with 20 manually verified test cases
- Extraction accuracy measured before and after improvements
- Root cause analysis documented

---

## User Personas & Workflows

### Persona 1: Sales Development Rep (SDR)
**Need:** Quick filtering of leads by practice size
**Current pain:** Vet count is mostly null, can't filter reliably
**Expected outcome:** "Show me all 3+ vet practices in MA" works and returns accurate results

### Persona 2: Sales Manager
**Need:** Understand data quality and confidence in enrichment
**Current pain:** Doesn't know why vet count is missing - is it not on the website, or extraction failed?
**Expected outcome:** "3 vet practices (high confidence)" vs "Practice size unknown (not_found)" gives clear visibility

### Persona 3: Data/Ops Engineer
**Need:** Diagnostic data to understand extraction quality
**Current pain:** Can't easily diagnose why extraction failed for a practice
**Expected outcome:** "Vet Count Confidence = not_found" makes it clear we searched but found no vet names

---

## Technical Approach (High-Level)

### Phase 1: Data Model Enhancement (Low Risk)
- Extend "Vet Count Confidence" field to include `not_found` and `error` statuses
- Update Pydantic model validation pattern
- Update extraction prompt with explicit "not_found" handling
- **Effort:** 1-2 hours
- **Risk:** Low (config-only changes)

### Phase 2: Baseline Testing (Research Only)
- Manually audit 20 Boston-area vet clinics (actual vet counts)
- Run extraction pipeline on each practice
- Compare actual vs extracted counts
- Identify patterns (systematic failures, hallucinations, etc.)
- **Effort:** 5-7 hours
- **Risk:** None (discovery phase)

### Phase 3: Root Cause Improvement (Based on Findings)
Three possible improvement paths based on baseline results:

**Path A: LLM Prompt Enhancement** (if too conservative)
- Rewrite extraction prompt for more explicit doctor name extraction
- Add examples of "not_found" cases
- Validate extracted names against page content
- **Effort:** 2-4 hours
- **Risk:** Low

**Path B: Scraper Enhancement** (if missing pages)
- Add more URL patterns for team pages
- Increase character budget for team/staff pages
- Implement fallback scraping strategies
- **Effort:** 4-8 hours
- **Risk:** Medium

**Path C: Validation Layer** (if hallucinations common)
- Add semantic validation of extracted counts
- Cross-reference with page structure (team size)
- Implement confidence scoring based on evidence quality
- **Effort:** 6-10 hours
- **Risk:** Medium-High

**Decision:** Based on Phase 2 findings, select the path that addresses the actual root cause.

---

## Acceptance Criteria

### Must Have (MVP)
- [ ] Data model updated to support `not_found` and `error` confidence values
- [ ] Notion schema updated with new field options
- [ ] Baseline test data created with 20 manually verified test cases
- [ ] Root cause identified via baseline testing
- [ ] Vet count populated in >70% of practices (up from ~10%)
- [ ] Extraction accuracy >85% on test cases

### Should Have
- [ ] Confidence levels properly calibrated (high = correct >90%)
- [ ] False positives eliminated (<5% hallucinated counts)
- [ ] Documentation updated with extraction methodology
- [ ] Sales team feedback on data quality

### Nice to Have
- [ ] Performance optimizations (reduce extraction time)
- [ ] Multi-location vet count breakdown
- [ ] Extraction metrics dashboard
- [ ] Automated accuracy monitoring

---

## Risk Assessment

### Risk 1: Extraction Accuracy Not Improving
**Likelihood:** MEDIUM
**Impact:** HIGH (feature doesn't deliver value)
**Mitigation:** Baseline testing will identify root cause; choose improvement path accordingly

### Risk 2: Notion Schema Cannot Support New Values
**Likelihood:** LOW
**Impact:** HIGH (feature blocked)
**Mitigation:** Confirmed Notion allows extending select field options

### Risk 3: Scraper Changes Break Other Extractions
**Likelihood:** LOW (if Path B chosen)
**Impact:** MEDIUM (must fix FEAT-004 regression)
**Mitigation:** Test on 10-practice sample before full rollout

### Risk 4: LLM Hallucinating Counts
**Likelihood:** MEDIUM
**Impact:** MEDIUM (false leads)
**Mitigation:** Validate against page content; prefer "not_found" over guessing

---

## Dependencies & Blockers

### Hard Dependencies
- **Notion schema must be updated first** - Add `not_found` and `error` options to "Vet Count Confidence"
- **Data model must be updated first** - Extend pattern validation in `/src/models/enrichment_models.py`

### Related Features
- **FEAT-004:** Fix Website Scraping Reliability (may need to coordinate if scraper enhancement needed)
- **FEAT-006:** Improve LLM Extraction (overlapping prompt improvements)

### No Code Blockers
- Improvements can be made within existing architecture
- No breaking changes to other features required

---

## Open Questions & Decisions

### Question 1: How strict on job titles?
**Decision:** Strict - Only count if title explicitly contains DVM, Doctor, Veterinarian (or Dr. prefix with veterinary context)

### Question 2: How to handle "searched but not found"?
**Decision:** Return `vet_count: null, confidence: "not_found"` - No extra Notion column needed

### Question 3: What if page lists vets but we're uncertain of count?
**Decision:** Return approximate count with `confidence: "low"` rather than null (more useful than null)

---

## Timeline & Effort Estimate

**Total Effort:** 10-18 hours over 2-3 weeks

### Week 1: Setup & Discovery
- Day 1-2: Update data model (1-2 hours)
- Day 3-5: Manual audit of 20 vet practices (5-7 hours)

### Week 2: Analysis & Planning
- Day 1-2: Baseline extraction testing (2 hours)
- Day 3-5: Root cause analysis + choose improvement path (2 hours)

### Week 3: Implementation (Conditional)
- Path A (Prompt fix): 2-4 hours
- Path B (Scraper): 4-8 hours
- Path C (Validation): 6-10 hours

---

## Success Criteria Validation

### How We'll Measure Success
1. **Vet count field coverage:** Run count query in Notion before/after
2. **Extraction accuracy:** Compare 20 test cases to ground truth
3. **Confidence calibration:** Check if "high" confidence matches actual accuracy
4. **No false positives:** Manual spot-check for hallucinated counts
5. **Performance:** Monitor extraction time and cost per practice

---

## Questions for Stakeholders

1. **Priority:** Is improving vet count a priority for lead qualification? If so, when is it needed?
2. **Budget:** Is $0.10/lead budget acceptable for all extraction improvements?
3. **Sales feedback:** What would sales team find most valuable - higher coverage or higher accuracy?

---

## References & Resources

- **Problem Analysis:** `analysis.md` (detailed technical investigation)
- **Recommendations:** `recommendations.md` (3-path implementation plan)
- **Test Data Template:** `/tests/fixtures/vet_count_test_cases.json` (baseline test cases)
- **Real Example:** https://raynhamvet.com/staff/ (3 vets, system shows null)

---

## Sign-Off

**Document Status:** Ready for Review
**Next Phase:** Stakeholder approval → Phase 1 execution (data model update)

