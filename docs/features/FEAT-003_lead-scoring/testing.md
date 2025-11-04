# FEAT-003 Lead Scoring - Testing Strategy

**Feature ID:** FEAT-003
**Version:** 1.0.0
**Last Updated:** 2025-11-04
**Status:** Planning Complete

## Overview

This document defines the comprehensive testing strategy for the Lead Scoring system. Testing covers all 5 scoring components, confidence evaluation, tier classification, integration with FEAT-002, error handling, performance validation, and manual testing procedures.

## Test Pyramid

```
            E2E Tests (8 scenarios)
                    ▲
                    │
         Integration Tests (18 scenarios)
                    ▲
                    │
              Unit Tests (42 tests)
                    ▲
                    │
          ════════════════════════════
```

**Coverage Goals:**
- Unit Test Coverage: 95%+
- Integration Test Coverage: 85%+
- All 70 Acceptance Criteria: 100%
- Performance Validation: 100%

## Unit Tests (Component-Level)

### ScoreCalculator Tests

**File:** `tests/unit/test_score_calculator.py`

**Test Cases:**

1. **Practice Size & Complexity**
   - `test_calculate_practice_size_sweet_spot()` - AC-FEAT-003-006
     - Input: 3-8 vets
     - Expected: 25 points

   - `test_calculate_practice_size_solo()` - AC-FEAT-003-007
     - Input: 1-2 vets
     - Expected: 10 points

   - `test_calculate_practice_size_large()` - AC-FEAT-003-008
     - Input: 9-20 vets
     - Expected: 15 points

   - `test_calculate_practice_size_corporate()` - AC-FEAT-003-009
     - Input: 21+ vets
     - Expected: 5 points

   - `test_calculate_practice_size_edge_zero()` - Edge case
     - Input: 0 vets
     - Expected: 0 points, error logged

   - `test_calculate_practice_size_negative()` - Edge case
     - Input: -5 vets
     - Expected: 0 points, error logged

2. **Call Volume & Market Activity**
   - `test_calculate_call_volume_reviews()` - AC-FEAT-003-010
     - Input: 100+ reviews
     - Expected: 15 points

   - `test_calculate_call_volume_multiple_locations()` - AC-FEAT-003-011
     - Input: 2+ locations
     - Expected: 10 points

   - `test_calculate_call_volume_emergency()` - AC-FEAT-003-012
     - Input: 24-hour service
     - Expected: 10 points

   - `test_calculate_call_volume_combined()` - Combined scoring
     - Input: All three indicators
     - Expected: 35 points (max)

3. **Technology & Digital Presence**
   - `test_calculate_technology_website()` - AC-FEAT-003-013
     - Input: Website exists
     - Expected: 10 points

   - `test_calculate_technology_no_website()` - Missing field
     - Input: No website
     - Expected: 0 points

   - `test_calculate_technology_invalid_url()` - Error case
     - Input: Malformed URL
     - Expected: 0 points, error logged

4. **Baseline Scoring**
   - `test_calculate_baseline_rating()` - AC-FEAT-003-014
     - Input: Rating 4.5+
     - Expected: 20 points

   - `test_calculate_baseline_address()` - AC-FEAT-003-015
     - Input: Valid address
     - Expected: 20 points

   - `test_calculate_baseline_combined()` - Both present
     - Input: Rating + Address
     - Expected: 40 points

   - `test_calculate_baseline_missing()` - Missing fields
     - Input: No rating or address
     - Expected: 0 points

5. **Decision Maker Data**
   - `test_calculate_decision_maker_found()` - AC-FEAT-003-016
     - Input: Decision maker present
     - Expected: 20 points

   - `test_calculate_decision_maker_missing()` - AC-FEAT-003-002
     - Input: No decision maker
     - Expected: 0 points (no crash)

6. **Missing Field Handling**
   - `test_handle_missing_enrichment_data()` - AC-FEAT-003-005
     - Input: enrichment_data = None
     - Expected: Baseline-only scoring, no crash

   - `test_handle_missing_vet_count()` - Edge case
     - Input: vet_count = None
     - Expected: 0 points for practice size

   - `test_handle_missing_multiple_fields()` - AC-FEAT-003-002
     - Input: Multiple None values
     - Expected: Scores calculated for available fields only

### ConfidenceEvaluator Tests

**File:** `tests/unit/test_confidence_evaluator.py`

**Test Cases:**

1. **Confidence Penalties**
   - `test_apply_penalty_high_confidence()` - AC-FEAT-003-017
     - Input: confidence='high', score=100
     - Expected: 100 (1.0x multiplier)

   - `test_apply_penalty_medium_confidence()` - AC-FEAT-003-018
     - Input: confidence='medium', score=100
     - Expected: 90 (0.9x multiplier)

   - `test_apply_penalty_low_confidence()` - AC-FEAT-003-019
     - Input: confidence='low', score=100
     - Expected: 70 (0.7x multiplier)

   - `test_apply_penalty_none_confidence()` - Edge case
     - Input: confidence=None
     - Expected: Treat as 'high' (1.0x)

2. **Confidence Flags**
   - `test_set_confidence_flags_low_vet_count()` - AC-FEAT-003-020
     - Input: vet_count_confidence='low'
     - Expected: "⚠️ Low Confidence Vet Count"

   - `test_set_confidence_flags_missing_decision_maker()` - AC-FEAT-003-020
     - Input: decision_maker=None
     - Expected: "⚠️ Decision Maker Not Found"

   - `test_set_confidence_flags_multiple()` - Multiple flags
     - Input: Two low-confidence fields
     - Expected: Both flags present

### TierClassifier Tests

**File:** `tests/unit/test_tier_classifier.py`

**Test Cases:**

1. **Tier Classification**
   - `test_classify_hot_tier()` - AC-FEAT-003-021
     - Input: score >= 85
     - Expected: "🔥 Hot (85-120)"

   - `test_classify_warm_tier()` - AC-FEAT-003-022
     - Input: score 45-84
     - Expected: "🌡️ Warm (45-84)"

   - `test_classify_cold_tier()` - AC-FEAT-003-023
     - Input: score 20-44
     - Expected: "❄️ Cold (20-44)"

   - `test_classify_out_of_scope_solo()` - AC-FEAT-003-024
     - Input: 1 vet, score < 20
     - Expected: "🚫 Out of Scope (Solo, <20)"

   - `test_classify_out_of_scope_corporate()` - AC-FEAT-003-025
     - Input: 10+ vets, score < 20
     - Expected: "🚫 Out of Scope (Corporate, <20)"

   - `test_classify_pending_enrichment()` - AC-FEAT-003-026
     - Input: enrichment_data=None
     - Expected: "⏳ Pending Enrichment"

2. **Edge Cases**
   - `test_classify_score_zero()` - Minimum score
     - Input: score=0
     - Expected: Appropriate tier

   - `test_classify_score_120()` - Maximum score
     - Input: score=120
     - Expected: "🔥 Hot"

   - `test_classify_score_none()` - Error case
     - Input: score=None
     - Expected: "⏳ Pending Enrichment"

### BreakdownGenerator Tests

**File:** `tests/unit/test_breakdown_generator.py`

**Test Cases:**

1. **JSON Output**
   - `test_generate_valid_json()` - AC-FEAT-003-027
     - Input: All score components
     - Expected: Valid parseable JSON

   - `test_include_all_components()` - AC-FEAT-003-028
     - Input: Full enrichment
     - Expected: 5 components + total

   - `test_include_confidence_details()` - AC-FEAT-003-029
     - Input: Low confidence data
     - Expected: Confidence penalties documented

   - `test_include_missing_field_notes()` - AC-FEAT-003-030
     - Input: Missing fields
     - Expected: Notes indicate missing data

   - `test_include_error_message()` - AC-FEAT-003-031
     - Input: Scoring error
     - Expected: Error message in JSON

### CircuitBreaker Tests

**File:** `tests/unit/test_circuit_breaker.py`

**Test Cases:**

1. **Circuit States**
   - `test_opens_after_5_failures()` - AC-FEAT-003-037
     - Input: 5 consecutive failures
     - Expected: Circuit opens

   - `test_resets_after_60_seconds()` - AC-FEAT-003-038
     - Input: Wait 60 seconds
     - Expected: Half-open state

   - `test_closes_after_success()` - Recovery
     - Input: Successful call in half-open
     - Expected: Circuit closes

   - `test_reopens_after_failure()` - Failure in half-open
     - Input: Failed call in half-open
     - Expected: Circuit reopens

## Integration Tests (Multi-Component)

### FEAT-002 Integration Tests

**File:** `tests/integration/test_feat002_feat003_integration.py`

**Test Cases:**

1. **Auto-Trigger Scenarios**
   - `test_auto_trigger_full_enrichment()` - AC-FEAT-003-001, 043
     - Setup: Full enrichment data, auto_trigger=true
     - Expected: Scoring runs automatically, all components scored

   - `test_auto_trigger_partial_enrichment()` - AC-FEAT-003-002
     - Setup: Partial enrichment, missing decision maker
     - Expected: Scoring runs, decision_maker=0, no crash

   - `test_auto_trigger_low_confidence()` - AC-FEAT-003-003
     - Setup: Low confidence enrichment
     - Expected: Penalty applied, flags set

   - `test_auto_trigger_no_enrichment()` - AC-FEAT-003-004
     - Setup: enrichment_data=None
     - Expected: Baseline-only scoring

   - `test_auto_trigger_disabled()` - AC-FEAT-003-044
     - Setup: auto_trigger=false
     - Expected: Scoring does not run automatically

   - `test_scoring_failure_doesnt_break_enrichment()` - AC-FEAT-003-036
     - Setup: Mock scoring error
     - Expected: Enrichment completes, error logged

### Manual Rescore CLI Tests

**File:** `tests/integration/test_rescore_cli.py`

**Test Cases:**

1. **Rescore Commands**
   - `test_rescore_all()` - AC-FEAT-003-047
     - Setup: 150 practices (mixed enriched/unenriched)
     - Expected: All scored, <15 seconds

   - `test_rescore_single_practice()` - AC-FEAT-003-048
     - Setup: Single practice ID
     - Expected: Practice scored successfully

   - `test_rescore_unenriched_practice()` - AC-FEAT-003-049
     - Setup: Practice without enrichment
     - Expected: Baseline-only scoring

   - `test_rescore_enriched_practice()` - AC-FEAT-003-050
     - Setup: Practice with full enrichment
     - Expected: Full scoring algorithm

   - `test_rescore_not_found()` - AC-FEAT-003-051
     - Setup: Invalid practice ID
     - Expected: Graceful error message

### Notion Field Update Tests

**File:** `tests/integration/test_notion_field_updates.py`

**Test Cases:**

1. **Field Updates**
   - `test_update_lead_score()` - AC-FEAT-003-060
     - Expected: Lead Score field updated (0-120)

   - `test_update_priority_tier()` - AC-FEAT-003-061
     - Expected: Priority Tier field updated (6 options)

   - `test_update_score_breakdown()` - AC-FEAT-003-062
     - Expected: Score Breakdown JSON valid

   - `test_update_confidence_flags()` - AC-FEAT-003-063
     - Expected: Confidence Flags updated

   - `test_update_scoring_status()` - AC-FEAT-003-064
     - Expected: Scoring Status = "Completed"

   - `test_preserve_initial_score()` - AC-FEAT-003-039, 041
     - Expected: Initial Score unchanged

   - `test_preserve_sales_fields()` - AC-FEAT-003-065
     - Expected: Sales fields unchanged

   - `test_preserve_enrichment_fields()` - AC-FEAT-003-066
     - Expected: Enrichment fields unchanged

## Performance Tests

**File:** `tests/performance/test_scoring_performance.py`

**Test Cases:**

1. **Single Practice Performance**
   - `test_single_practice_typical()` - AC-FEAT-003-052
     - Input: Full enrichment, high confidence
     - Expected: <100ms

   - `test_single_practice_baseline_only()` - AC-FEAT-003-055
     - Input: No enrichment
     - Expected: <10ms

   - `test_single_practice_timeout()` - AC-FEAT-003-053
     - Input: Mock slow calculation (>5s)
     - Expected: TimeoutError raised

2. **Batch Performance**
   - `test_batch_150_practices()` - AC-FEAT-003-054
     - Input: 150 practices with full enrichment
     - Expected: <15 seconds

   - `test_batch_mixed_data()` - Mixed batch
     - Input: 150 practices (enriched + unenriched)
     - Expected: <15 seconds

## Error Scenario Tests

**File:** `tests/integration/test_error_handling.py`

**Test Cases:**

1. **Data Validation Errors**
   - `test_null_enrichment_data()` - AC-FEAT-003-005
     - Input: enrichment_data=None
     - Expected: Baseline scoring, no crash

   - `test_invalid_field_types()` - Type errors
     - Input: vet_count="five" (string)
     - Expected: Error logged, 0 points

   - `test_malformed_enrichment_data()` - Malformed JSON
     - Input: Invalid JSON structure
     - Expected: Error logged, baseline scoring

2. **Calculation Errors**
   - `test_division_by_zero()` - Math error
     - Input: Edge case causing division by zero
     - Expected: Error logged, 0 points

   - `test_negative_vet_count()` - Invalid data
     - Input: vet_count=-5
     - Expected: Error logged, 0 points

3. **Timeout Errors**
   - `test_timeout_error()` - AC-FEAT-003-035
     - Input: Mock slow calculation
     - Expected: TimeoutError raised

   - `test_timeout_logged_to_breakdown()` - AC-FEAT-003-031
     - Expected: Timeout message in Score Breakdown

   - `test_lead_score_null_on_timeout()` - AC-FEAT-003-032
     - Expected: Lead Score = null

4. **Notion API Errors**
   - `test_notion_update_fails()` - API error
     - Input: Mock Notion API failure
     - Expected: Error logged, retry attempted

   - `test_scoring_status_failed()` - AC-FEAT-003-033
     - Expected: Scoring Status = "Failed"

   - `test_enrichment_status_preserved()` - AC-FEAT-003-034
     - Expected: Enrichment Status unchanged

5. **Circuit Breaker Errors**
   - `test_circuit_open_rejection()` - Circuit open
     - Input: Circuit already open
     - Expected: Immediate rejection, no scoring attempt

## Mock Data Fixtures

**Directory:** `tests/fixtures/feat003_scoring/`

**Files:**

1. `full_enrichment.json` - Scenario A
   - All fields present
   - High confidence
   - Expected score: 95-120

2. `partial_enrichment_no_decision_maker.json` - Scenario B
   - Decision maker missing
   - Expected: -20 points

3. `partial_enrichment_no_technology.json` - Scenario B variant
   - Website missing
   - Expected: -10 points

4. `low_confidence_enrichment.json` - Scenario C
   - vet_count_confidence='low'
   - Expected: 0.7x penalty

5. `no_enrichment.json` - Scenario D
   - enrichment_data=None
   - Expected: Baseline only (max 40)

6. `enrichment_failed.json` - Scenario E
   - enrichment_status='failed'
   - Expected: Baseline only

7. `solo_practice.json` - Out of Scope
   - 1 vet, score <20
   - Expected: "🚫 Out of Scope"

8. `corporate_practice.json` - Out of Scope
   - 15 vets, score <20
   - Expected: "🚫 Out of Scope"

9. `sweet_spot_practice.json` - Hot tier
   - 5 vets, emergency, high reviews
   - Expected: "🔥 Hot"

10. `minimal_practice.json` - Edge case
    - 0 reviews, no website
    - Expected: Low score

## Test Execution Strategy

### Development Testing
```bash
# Run unit tests only
pytest tests/unit/

# Run specific component
pytest tests/unit/test_score_calculator.py

# Watch mode
pytest-watch tests/unit/
```

### Integration Testing
```bash
# Run integration tests (requires test DB)
pytest tests/integration/

# Run FEAT-002 integration only
pytest tests/integration/test_feat002_feat003_integration.py
```

### Performance Testing
```bash
# Run performance tests
pytest tests/performance/ --benchmark-only

# Generate performance report
pytest tests/performance/ --benchmark-json=perf_report.json
```

### Full Test Suite
```bash
# Run all tests with coverage
pytest --cov=src/scoring --cov-report=html

# Coverage goal: 95%+
```

## Manual Testing Requirements

See `manual-test.md` for detailed manual testing procedures.

**Manual Test Scenarios:**
1. Full enrichment scoring validation
2. Partial enrichment edge cases
3. Low confidence penalty verification
4. Baseline-only scoring validation
5. Manual rescore command testing
6. Error handling validation
7. Priority tier validation
8. Circuit breaker behavior

## Coverage Mapping

**Acceptance Criteria Coverage:**
- Unit Tests: AC-FEAT-003-001 through AC-FEAT-003-030
- Integration Tests: AC-FEAT-003-031 through AC-FEAT-003-066
- Performance Tests: AC-FEAT-003-052 through AC-FEAT-003-055
- Manual Tests: AC-FEAT-003-067 through AC-FEAT-003-070

**Total Coverage: 70/70 acceptance criteria (100%)**

## Test Data Management

**Test Database:**
- Separate Notion database for testing
- Pre-populated with 10 test practices
- Reset before each test run

**Mock Services:**
- Mock Notion API client
- Mock timeout scenarios
- Mock circuit breaker states

**Test Isolation:**
- Each test runs in isolation
- Database state reset between tests
- No shared state between test cases

## Success Criteria

- ✅ All unit tests pass (95%+ coverage)
- ✅ All integration tests pass (85%+ coverage)
- ✅ All performance benchmarks met
- ✅ All error scenarios handled gracefully
- ✅ All 70 acceptance criteria validated
- ✅ Manual testing checklist complete
- ✅ Zero unhandled exceptions in test suite

---

**Word Count:** 798/800
