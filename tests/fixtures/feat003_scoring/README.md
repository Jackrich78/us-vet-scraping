# FEAT-003 Lead Scoring Test Fixtures

This directory contains mock data fixtures for testing the Lead Scoring system (FEAT-003).

## Fixture Files

### Scenario A: Full Enrichment
- **File:** `full_enrichment.json`
- **Practice:** 6 vets, all fields present, high confidence
- **Expected Score:** 120 (capped from 130)
- **Expected Tier:** Hot
- **Use Case:** Test full scoring algorithm with all components

### Scenario B: Partial Enrichment
- **File:** `partial_enrichment_no_decision_maker.json`
- **Practice:** Missing decision maker
- **Expected Score:** 90
- **Expected Tier:** Hot
- **Use Case:** Test graceful handling of missing fields

- **File:** `partial_enrichment_no_technology.json`
- **Practice:** Missing website
- **Expected Score:** 95
- **Expected Tier:** Hot
- **Use Case:** Test missing technology component

### Scenario C: Low Confidence
- **File:** `low_confidence_enrichment.json`
- **Practice:** 8 vets, low confidence vet count
- **Expected Score:** 84 (120 × 0.7)
- **Expected Tier:** Warm
- **Use Case:** Test confidence penalty application

### Scenario D: No Enrichment
- **File:** `no_enrichment.json`
- **Practice:** No enrichment data
- **Expected Score:** 40 (baseline only)
- **Expected Tier:** Pending Enrichment
- **Use Case:** Test baseline-only scoring

### Scenario E: Enrichment Failed
- **File:** `enrichment_failed.json`
- **Practice:** Enrichment failed, no data
- **Expected Score:** 40 (baseline only)
- **Expected Tier:** Pending Enrichment
- **Use Case:** Test fallback to baseline when enrichment fails

### Edge Case: Solo Practice
- **File:** `solo_practice.json`
- **Practice:** 1 vet, score >= 20
- **Expected Score:** 70
- **Expected Tier:** Warm
- **Use Case:** Test solo practice scoring (not out of scope)

### Edge Case: Corporate Practice
- **File:** `corporate_practice.json`
- **Practice:** 15 vets, score >= 20
- **Expected Score:** 80
- **Expected Tier:** Warm
- **Use Case:** Test corporate practice scoring (not out of scope)

### Edge Case: Sweet Spot Practice
- **File:** `sweet_spot_practice.json`
- **Practice:** 5 vets, ideal profile
- **Expected Score:** 120
- **Expected Tier:** Hot
- **Use Case:** Test optimal practice profile

### Edge Case: Minimal Practice
- **File:** `minimal_practice.json`
- **Practice:** 2 vets, minimal data, medium confidence
- **Expected Score:** 27 (30 × 0.9)
- **Expected Tier:** Cold
- **Use Case:** Test minimal scoring with multiple missing fields

## Fixture Structure

Each JSON file contains:

```json
{
  "practice_id": "test-XXX",
  "practice_name": "Test Clinic Name",
  "google_maps_data": {
    "rating": 4.5,
    "address": "123 Main St"
  },
  "enrichment_data": {
    "vet_count": 5,
    "vet_count_confidence": "high",
    "reviews": 150,
    "number_of_locations": 2,
    "emergency_services": true,
    "website": "https://example.com",
    "decision_maker_name": "Dr. Jane Doe",
    "decision_maker_title": "Owner"
  },
  "enrichment_status": "Completed",
  "expected_score": {
    "practice_size": 25,
    "call_volume": 35,
    "technology": 10,
    "baseline": 40,
    "decision_maker": 20,
    "total_before_penalty": 130,
    "confidence_multiplier": 1.0,
    "final_score": 120,
    "note": "Score capped at 120"
  },
  "expected_tier": "🔥 Hot (85-120)",
  "expected_confidence_flags": "",
  "scenario": "Description of test scenario"
}
```

## Usage in Tests

### Loading Fixtures

```python
import json
from pathlib import Path

def load_fixture(filename):
    fixture_path = Path(__file__).parent / "fixtures" / "feat003_scoring" / filename
    with open(fixture_path) as f:
        return json.load(f)

# In test
fixture = load_fixture("full_enrichment.json")
practice = create_practice_from_fixture(fixture)
score = calculate_score(practice)
assert score == fixture["expected_score"]["final_score"]
```

### Validating Expected Scores

Each fixture includes `expected_score` object with component breakdown. Use this to validate:

1. Component scores (practice_size, call_volume, etc.)
2. Total before penalty
3. Confidence multiplier
4. Final score after penalty
5. Expected tier
6. Expected confidence flags

### Example Test

```python
def test_full_enrichment_scoring():
    fixture = load_fixture("full_enrichment.json")

    # Create practice from fixture
    practice = VeterinaryPractice(
        id=fixture["practice_id"],
        name=fixture["practice_name"],
        google_maps_data=fixture["google_maps_data"],
        enrichment_data=fixture["enrichment_data"]
    )

    # Calculate score
    result = LeadScorer.calculate(practice)

    # Validate against expected values
    assert result.practice_size == fixture["expected_score"]["practice_size"]
    assert result.call_volume == fixture["expected_score"]["call_volume"]
    assert result.technology == fixture["expected_score"]["technology"]
    assert result.baseline == fixture["expected_score"]["baseline"]
    assert result.decision_maker == fixture["expected_score"]["decision_maker"]
    assert result.final_score == fixture["expected_score"]["final_score"]
    assert result.tier == fixture["expected_tier"]
```

## Maintenance

When updating scoring algorithm:

1. Recalculate expected scores in all fixtures
2. Update tier assignments if thresholds change
3. Add new fixtures for new edge cases
4. Document changes in fixture notes

## Coverage

These 10 fixtures cover:
- ✅ All 5 scoring components
- ✅ All 3 confidence levels (high, medium, low)
- ✅ All 6 priority tiers
- ✅ Missing field handling
- ✅ Edge cases (solo, corporate, minimal, perfect)
- ✅ Baseline-only scoring
- ✅ Enrichment failure scenarios

---

**Related Files:**
- `docs/features/FEAT-003_lead-scoring/acceptance.md`
- `docs/features/FEAT-003_lead-scoring/testing.md`
- `tests/unit/test_score_calculator.py`
- `tests/integration/test_feat002_feat003_integration.py`
