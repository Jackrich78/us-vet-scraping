# Product Requirements Document: ICP Fit Lead Scoring

**Feature ID:** FEAT-003
**Feature Name:** ICP Fit Lead Scoring & Prioritization
**Priority:** P0 (Critical - Sales prioritization)
**Status:** Planning
**Owner:** Development Team
**Created:** 2025-11-03

## Executive Summary

Calculate a 0-120 point ICP (Ideal Customer Profile) fit score for each veterinary practice based on practice size, call volume indicators, technology adoption, and decision maker availability. Classify practices by size (Solo/Small/Sweet Spot/Large/Corporate) and assign priority tiers (Hot/Warm/Cold/Out of Scope). Generate score breakdown explanations for sales context.

**Success Metric:** 150 practices scored and prioritized within 30 seconds, ready for sales outreach.

## Problem Statement

Without systematic ICP fit scoring:
- Sales reps waste time on low-fit prospects (e.g., solo practitioners)
- High-potential practices (Sweet Spot) buried in unqualified leads
- No consistent prioritization criteria (subjective gut feel)
- No score explanations (why is this practice Hot vs Warm?)
- No automated lead routing (who should work which leads?)

## Goals & Non-Goals

### Goals
✅ Calculate 0-120 point ICP fit score based on 4 dimensions + bonus
✅ Classify practice size: Solo, Small, Sweet Spot, Large, Corporate
✅ Assign priority tier: Hot (80-120), Warm (50-79), Cold (0-49), Out of Scope
✅ Generate score breakdown (which factors contributed most)
✅ Update Notion records with scoring data
✅ Support score recalculation (re-run after manual data corrections)

### Non-Goals
❌ Predictive scoring (ML models, conversion probability)
❌ Lead routing automation (assigning to specific reps)
❌ Score decay over time (time-based deprioritization)
❌ Manual score overrides (sales reps can't adjust scores)
❌ Competitive analysis (nearby practices comparison)

## User Stories

**As a sales rep**, I need practices ranked by ICP fit so I focus on high-potential leads first.

**As a sales manager**, I need to see why a practice is scored 95 points so I can validate prioritization logic.

**As a sales rep**, I need to know if a practice is "Sweet Spot" (multi-vet, not too large) so I tailor my pitch.

**As a developer**, I need to recalculate scores after manual data corrections without re-scraping.

**As a business owner**, I need Out of Scope practices flagged so we don't waste time on unfit prospects.

## Technical Specification

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ FEAT-003: ICP Fit Lead Scoring & Prioritization            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Query Notion for all practices (enriched)               │
│     └─ Filter: enrichment_status == "Completed"            │
│                                                             │
│  2. LeadScorer.calculate_icp_fit_score()                   │
│     ├─ Practice Size Score (0-40 pts)                      │
│     ├─ Call Volume Indicators (0-30 pts)                   │
│     ├─ Technology Adoption (0-20 pts)                      │
│     ├─ Baseline Score (0-10 pts)                           │
│     └─ Decision Maker Bonus (+0-20 pts)                    │
│                                                             │
│  3. PracticeClassifier.classify_practice_size()            │
│     └─ Solo / Small / Sweet Spot / Large / Corporate       │
│                                                             │
│  4. PriorityTierAssigner.assign_tier()                     │
│     └─ Hot / Warm / Cold / Out of Scope                    │
│                                                             │
│  5. Update Notion records with scoring data                 │
│     ├─ Lead Score (0-120)                                  │
│     ├─ Practice Size Classification                        │
│     ├─ Priority Tier                                       │
│     └─ Score Breakdown (JSON explanation)                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Component Details

#### 1. ICP Fit Scoring Algorithm (lead_scorer.py)

**Purpose:** Calculate 0-120 point ICP fit score based on enrichment data

**Scoring Dimensions:**

##### **1. Practice Size Score (0-40 points)**

**Vet Count Scoring:**
```python
def score_practice_size(vet_count: int, confidence: str) -> Dict[str, Any]:
    """
    Score based on practice size (vet count).

    Sweet Spot: 3-8 vets (multi-vet, not too large)
    - 3-5 vets: 40 points (ideal size)
    - 6-8 vets: 35 points (still good)
    - 9-12 vets: 25 points (getting large)
    - 13-20 vets: 15 points (corporate-ish)
    - 20+ vets: 5 points (too large, likely corporate)
    - 2 vets: 30 points (small multi-vet)
    - 1 vet: 10 points (solo practice, low fit)

    Confidence penalty:
    - Low confidence: -10 points
    - Medium confidence: -5 points
    - High confidence: No penalty
    """
    base_score = 0
    if vet_count >= 20:
        base_score = 5
    elif vet_count >= 13:
        base_score = 15
    elif vet_count >= 9:
        base_score = 25
    elif vet_count >= 6:
        base_score = 35
    elif vet_count >= 3:
        base_score = 40  # Sweet Spot
    elif vet_count == 2:
        base_score = 30
    else:  # 1 vet
        base_score = 10

    # Apply confidence penalty
    if confidence == "low":
        base_score = max(0, base_score - 10)
    elif confidence == "medium":
        base_score = max(0, base_score - 5)

    return {
        "score": base_score,
        "max": 40,
        "reason": f"{vet_count} vets (confidence: {confidence})"
    }
```

**Rationale:**
- **Sweet Spot (3-8 vets):** Large enough to benefit from product, small enough to be approachable
- **Solo (1 vet):** Low priority (less call volume, budget constraints)
- **Corporate (20+ vets):** Complex decision-making, longer sales cycles

##### **2. Call Volume Indicators (0-30 points)**

**High Call Volume Signals:**
```python
def score_call_volume_indicators(practice: VeterinaryPractice) -> Dict[str, Any]:
    """
    Score based on indicators of high call volume.

    Indicators:
    - 24/7 Emergency Services: 15 points (high call volume)
    - High review count (150+): 10 points (busy practice)
    - Boarding services: 5 points (additional call drivers)

    Max: 30 points
    """
    score = 0
    reasons = []

    if practice.emergency_24_7:
        score += 15
        reasons.append("24/7 emergency services (15 pts)")

    if practice.google_review_count >= 150:
        score += 10
        reasons.append(f"{practice.google_review_count} reviews (10 pts)")

    if practice.boarding_services:
        score += 5
        reasons.append("Boarding services (5 pts)")

    return {
        "score": score,
        "max": 30,
        "reason": ", ".join(reasons) if reasons else "No high call volume indicators"
    }
```

**Rationale:**
- **24/7 Emergency:** Highest call volume, most pain with missed calls
- **High reviews:** Proxy for busy practice (more patients = more calls)
- **Boarding:** Additional call drivers beyond medical appointments

##### **3. Technology Adoption Score (0-20 points)**

**Tech Readiness Signals:**
```python
def score_technology_adoption(practice: VeterinaryPractice) -> Dict[str, Any]:
    """
    Score based on technology adoption (readiness for product).

    Indicators:
    - Online booking: 8 points (tech-forward)
    - Patient portal: 7 points (tech-forward)
    - Telemedicine: 5 points (innovative)
    - Digital records mentioned: 3 points (basic tech)

    Max: 20 points (cap at 20 even if sum exceeds)
    """
    score = 0
    reasons = []

    if practice.online_booking:
        score += 8
        reasons.append("Online booking (8 pts)")

    if practice.patient_portal:
        score += 7
        reasons.append("Patient portal (7 pts)")

    if practice.telemedicine:
        score += 5
        reasons.append("Telemedicine (5 pts)")

    if practice.digital_records_mentioned:
        score += 3
        reasons.append("Digital records (3 pts)")

    # Cap at 20 points
    score = min(score, 20)

    return {
        "score": score,
        "max": 20,
        "reason": ", ".join(reasons) if reasons else "No technology indicators"
    }
```

**Rationale:**
- **Online booking/portals:** Tech-forward practices, easier adoption
- **Telemedicine:** Innovative, open to new tech
- **Digital records:** Baseline tech adoption

##### **4. Baseline Score (0-10 points)**

**From FEAT-001 Initial Scoring:**
```python
def score_baseline(practice: VeterinaryPractice) -> Dict[str, Any]:
    """
    Normalize FEAT-001 initial score (0-25) to 0-10 range.

    FEAT-001 scoring:
    - Review count: 0-15 pts
    - Review rating: 0-10 pts
    - Total: 0-25 pts

    Normalize to 0-10:
    - 0-6 pts → 0 pts (very low)
    - 7-12 pts → 3 pts (low)
    - 13-18 pts → 6 pts (medium)
    - 19-25 pts → 10 pts (high)
    """
    initial_score = practice.lead_score  # From FEAT-001

    if initial_score >= 19:
        normalized = 10
    elif initial_score >= 13:
        normalized = 6
    elif initial_score >= 7:
        normalized = 3
    else:
        normalized = 0

    return {
        "score": normalized,
        "max": 10,
        "reason": f"Google Maps reputation ({initial_score}/25 initial score)"
    }
```

**Rationale:**
- Carries forward Google Maps reputation score from FEAT-001
- Normalized to 0-10 to fit overall 120-point scale

##### **5. Decision Maker Bonus (0-20 points)**

**Bonus for Decision Maker Availability:**
```python
def score_decision_maker_bonus(practice: VeterinaryPractice) -> Dict[str, Any]:
    """
    Bonus points for having decision maker information.

    Scoring:
    - Name + Email + Role: 20 points (full contact info)
    - Name + Email: 15 points (can reach directly)
    - Name + Role: 10 points (can research email)
    - Name only: 5 points (partial info)
    - No decision maker: 0 points

    Max: 20 points (bonus, doesn't count toward 120 base)
    """
    dm = practice.decision_maker
    if not dm or not dm.name:
        return {"score": 0, "max": 20, "reason": "No decision maker info"}

    score = 0
    reasons = []

    if dm.name and dm.email and dm.role:
        score = 20
        reasons.append(f"{dm.role} with email")
    elif dm.name and dm.email:
        score = 15
        reasons.append("Name and email")
    elif dm.name and dm.role:
        score = 10
        reasons.append(f"{dm.role} identified")
    else:
        score = 5
        reasons.append("Name only")

    return {
        "score": score,
        "max": 20,
        "reason": ", ".join(reasons)
    }
```

**Rationale:**
- Direct contact info dramatically increases conversion likelihood
- Easier to personalize outreach with role/name

##### **Total ICP Fit Score: 0-120 points**

```python
class LeadScorer:
    def calculate_icp_fit_score(self, practice: VeterinaryPractice) -> LeadScore:
        """
        Calculate comprehensive ICP fit score.

        Returns:
            LeadScore object with total score (0-120) and breakdown
        """
        practice_size = self.score_practice_size(practice.vet_count_total, practice.vet_count_confidence)
        call_volume = self.score_call_volume_indicators(practice)
        technology = self.score_technology_adoption(practice)
        baseline = self.score_baseline(practice)
        decision_maker = self.score_decision_maker_bonus(practice)

        total_score = (
            practice_size["score"] +
            call_volume["score"] +
            technology["score"] +
            baseline["score"] +
            decision_maker["score"]
        )

        return LeadScore(
            total_score=total_score,
            max_score=120,
            practice_size_score=practice_size,
            call_volume_score=call_volume,
            technology_score=technology,
            baseline_score=baseline,
            decision_maker_bonus=decision_maker
        )
```

**Score Distribution:**
```python
# Example: Boston Veterinary Clinic
# - 4 vets (high confidence): 40 pts
# - 24/7 emergency + 234 reviews + boarding: 30 pts
# - Online booking + patient portal: 15 pts
# - Strong Google reputation: 10 pts
# - Owner name + email: 20 pts
# Total: 115 pts (Hot tier)
```

**Dependencies:**
- `FEAT-000` VeterinaryPractice model
- `FEAT-000` LeadScore model

**Uncertainty:**
- ❓ Should scoring weights be configurable in config.json? (Recommendation: Yes, add ScoringConfig)
- ❓ Should we support custom scoring formulas? (Recommendation: Phase 2)

#### 2. Practice Size Classification (practice_classifier.py)

**Purpose:** Classify practices into size categories based on vet count

**Classification Logic:**
```python
class PracticeClassifier:
    def classify_practice_size(self, vet_count: int) -> str:
        """
        Classify practice by size.

        Categories:
        - Solo: 1 vet
        - Small: 2 vets
        - Sweet Spot: 3-8 vets (ideal for product)
        - Large: 9-19 vets
        - Corporate: 20+ vets

        Args:
            vet_count: Number of veterinarians

        Returns:
            Classification string
        """
        if vet_count >= 20:
            return "Corporate"
        elif vet_count >= 9:
            return "Large"
        elif vet_count >= 3:
            return "Sweet Spot"
        elif vet_count == 2:
            return "Small"
        else:
            return "Solo"
```

**Classification Distribution (Expected):**
```python
# Of 150 MA practices:
# Solo: ~30 (20%)
# Small: ~25 (17%)
# Sweet Spot: ~70 (47%)  ← Primary target
# Large: ~20 (13%)
# Corporate: ~5 (3%)
```

**Dependencies:**
- `FEAT-000` VeterinaryPractice model

**Uncertainty:**
- ❓ Should classification thresholds be configurable? (Recommendation: Yes, in ScoringConfig)

#### 3. Priority Tier Assignment (priority_tier_assigner.py)

**Purpose:** Assign priority tier based on total ICP fit score

**Tier Logic:**
```python
class PriorityTierAssigner:
    def assign_tier(self, total_score: int, practice_size: str) -> str:
        """
        Assign priority tier based on ICP fit score.

        Tiers:
        - Hot: 80-120 pts (high-priority, contact ASAP)
        - Warm: 50-79 pts (qualified, contact within week)
        - Cold: 20-49 pts (low-priority, contact if time)
        - Out of Scope: 0-19 pts (unqualified, skip)

        Special rule: Solo practices (<20 pts) → Out of Scope
        """
        if total_score >= 80:
            return "Hot"
        elif total_score >= 50:
            return "Warm"
        elif total_score >= 20:
            return "Cold"
        else:
            return "Out of Scope"
```

**Tier Distribution (Expected):**
```python
# Of 150 MA practices:
# Hot: ~35 (23%)       ← Focus here first
# Warm: ~55 (37%)      ← Contact within week
# Cold: ~40 (27%)      ← Low priority
# Out of Scope: ~20 (13%)  ← Skip
```

**Dependencies:**
- `FEAT-000` VeterinaryPractice model

**Uncertainty:**
- ❓ Should tier thresholds be configurable? (Recommendation: Yes, in ScoringConfig)
- ❓ Should we support manual tier overrides? (Recommendation: Phase 2)

#### 4. Score Breakdown Generator (score_breakdown.py)

**Purpose:** Generate human-readable score explanation for sales context

**Output Format:**
```python
class ScoreBreakdown(BaseModel):
    """JSON structure stored in Notion 'Score Breakdown' field."""

    total_score: int
    max_score: int
    practice_size_classification: str
    priority_tier: str

    breakdown: Dict[str, Dict[str, Any]]
    # Example:
    # {
    #   "practice_size": {"score": 40, "max": 40, "reason": "4 vets (confidence: high)"},
    #   "call_volume": {"score": 30, "max": 30, "reason": "24/7 emergency, 234 reviews, boarding"},
    #   "technology": {"score": 15, "max": 20, "reason": "Online booking, patient portal"},
    #   "baseline": {"score": 10, "max": 10, "reason": "Strong Google reputation"},
    #   "decision_maker": {"score": 20, "max": 20, "reason": "Owner with email"}
    # }

    top_fit_reasons: List[str]
    # Example: ["Sweet Spot practice (4 vets)", "24/7 emergency services", "Owner email available"]

    concerns: List[str]
    # Example: ["No online booking", "Low vet count confidence"]
```

**Usage in Sales Context:**
```python
# Notion record shows:
# Lead Score: 115
# Priority Tier: Hot
# Score Breakdown: (expandable JSON)
#   Practice Size: 40/40 - 4 vets (confidence: high)
#   Call Volume: 30/30 - 24/7 emergency, 234 reviews, boarding
#   Technology: 15/20 - Online booking, patient portal
#   Baseline: 10/10 - Strong Google reputation
#   Decision Maker: 20/20 - Owner with email
#
# Top Fit Reasons:
#   1. Sweet Spot practice (4 vets)
#   2. 24/7 emergency services (high call volume)
#   3. Owner email available for direct outreach
#
# Concerns: None
```

**Dependencies:**
- `FEAT-000` LeadScore model

**Uncertainty:**
- ❓ Should we generate personalized email snippets? (Recommendation: Phase 2)

#### 5. Notion Scoring Update (extends NotionClient)

**Purpose:** Update Notion records with scoring data

**New Method:**
```python
class NotionClient:
    def update_practice_scoring(
        self,
        page_id: str,
        lead_score: LeadScore,
        practice_size: str,
        priority_tier: str,
        score_breakdown: ScoreBreakdown
    ) -> None:
        """
        Update existing Notion record with scoring data.

        Preserves:
        - All sales workflow fields (Status, Assigned To, etc.)
        - Core data from FEAT-001 (Practice Name, Address, etc.)
        - Enrichment data from FEAT-002 (Vet count, decision maker, etc.)

        Updates:
        - Lead Score (0-120)
        - Practice Size Classification
        - Priority Tier
        - Score Breakdown (JSON)
        - Last Scored Date
        """
```

**Field Mappings (LeadScore → Notion):**

| Scoring Field | Notion Property | Type |
|--------------|----------------|------|
| `total_score` | "Lead Score" | number |
| `practice_size_classification` | "Practice Size" | select |
| `priority_tier` | "Priority Tier" | select |
| `score_breakdown` (JSON) | "Score Breakdown" | rich_text (JSON string) |
| `datetime.now()` | "Last Scored Date" | date |

**Preserved Fields (Never Overwrite):**
```python
PRESERVE_FIELDS = [
    "Status",
    "Assigned To",
    "Research Notes",
    "Call Notes",
    "Last Contact Date",
    "Next Follow-Up Date",
    "Campaign",
    "Practice Name",           # From FEAT-001
    "Address",                 # From FEAT-001
    "Confirmed Vet Count",     # From FEAT-002
    "Decision Maker Name",     # From FEAT-002
    "24/7 Emergency Services", # From FEAT-002
    # ... all enrichment fields
]
```

**Dependencies:**
- `FEAT-000` NotionClient base class
- `FEAT-000` LeadScore, ScoreBreakdown models
- `notion-client==2.2.1`

### Data Flow

```
1. Query Notion for Enriched Practices
   notion_client = NotionClient(config.notion)
   practices = notion_client.query_enriched_practices()
   # Returns 150 practices (enrichment_status == "Completed")

2. Calculate ICP Fit Scores
   lead_scorer = LeadScorer(config.scoring)
   scored_practices = []
   for practice in practices:
       lead_score = lead_scorer.calculate_icp_fit_score(practice)
       practice_size = practice_classifier.classify_practice_size(practice.vet_count_total)
       priority_tier = priority_tier_assigner.assign_tier(lead_score.total_score, practice_size)
       score_breakdown = generate_score_breakdown(lead_score, practice_size, priority_tier)
       scored_practices.append({
           "practice": practice,
           "lead_score": lead_score,
           "practice_size": practice_size,
           "priority_tier": priority_tier,
           "score_breakdown": score_breakdown
       })
   # Total time: 150 × 0.001s = 0.15 seconds (pure calculation)

3. Update Notion Records
   for scored in scored_practices:
       notion_client.update_practice_scoring(
           page_id=scored["practice"].notion_page_id,
           lead_score=scored["lead_score"],
           practice_size=scored["practice_size"],
           priority_tier=scored["priority_tier"],
           score_breakdown=scored["score_breakdown"]
       )
   # Total time: 150 × 0.35s (rate limit) = 52.5s

4. Generate Scoring Summary Report
   report = generate_scoring_report(scored_practices)
   logger.info(f"Scoring complete:\n{report}")
   # Example:
   # Hot: 35 (23%)
   # Warm: 55 (37%)
   # Cold: 40 (27%)
   # Out of Scope: 20 (13%)
   # Average score: 62.3
   # Top practice: Boston Vet Clinic (115 pts)

5. Total Pipeline Time: 0.15s (scoring) + 52.5s (Notion) = 52.65 seconds
```

### Configuration

**config.json additions:**
```json
{
  "scoring": {
    "practice_size": {
      "sweet_spot_min": 3,
      "sweet_spot_max": 8,
      "corporate_threshold": 20,
      "confidence_penalty_low": 10,
      "confidence_penalty_medium": 5
    },
    "call_volume": {
      "emergency_24_7_points": 15,
      "high_review_threshold": 150,
      "high_review_points": 10,
      "boarding_points": 5
    },
    "technology": {
      "online_booking_points": 8,
      "patient_portal_points": 7,
      "telemedicine_points": 5,
      "digital_records_points": 3,
      "max_tech_score": 20
    },
    "decision_maker": {
      "full_contact_points": 20,
      "name_email_points": 15,
      "name_role_points": 10,
      "name_only_points": 5
    },
    "tiers": {
      "hot_threshold": 80,
      "warm_threshold": 50,
      "cold_threshold": 20
    }
  }
}
```

### Testing Strategy

**Unit Tests:**
- ✅ LeadScorer calculates correct scores for edge cases (solo, corporate, sweet spot)
- ✅ PracticeClassifier classifies all size categories correctly
- ✅ PriorityTierAssigner assigns tiers correctly
- ✅ ScoreBreakdown generates valid JSON
- ✅ NotionClient updates scoring fields correctly

**Integration Tests:**
- ✅ Full pipeline: Query → Score → Update Notion (test mode, 10 practices)
- ✅ Score recalculation: Update practice data, re-score, verify new scores

**Mock Data:**
```python
# tests/fixtures/scoring_samples.py
SWEET_SPOT_PRACTICE = {
    "vet_count_total": 4,
    "vet_count_confidence": "high",
    "emergency_24_7": True,
    "google_review_count": 234,
    "boarding_services": True,
    "online_booking": True,
    "patient_portal": True,
    "decision_maker": {"name": "Dr. Smith", "role": "Owner", "email": "smith@example.com"},
    "lead_score": 23  # From FEAT-001
}
# Expected: 40 + 30 + 15 + 10 + 20 = 115 pts (Hot)

SOLO_PRACTICE = {
    "vet_count_total": 1,
    "vet_count_confidence": "high",
    "emergency_24_7": False,
    "google_review_count": 45,
    "boarding_services": False,
    "online_booking": False,
    "patient_portal": False,
    "decision_maker": None,
    "lead_score": 10  # From FEAT-001
}
# Expected: 10 + 5 + 0 + 3 + 0 = 18 pts (Out of Scope)
```

**Manual Testing Checklist:**
1. Run scoring on all practices, verify tiers match expectations
2. Check Notion records for correct field updates
3. Verify score breakdown JSON is valid and readable
4. Test score recalculation (change vet count, re-score)
5. Verify sales workflow fields not overwritten

### Acceptance Criteria

1. ✅ 150 practices scored within 60 seconds
2. ✅ ICP fit scores accurate (0-120 range)
3. ✅ Practice size classifications correct (Solo/Small/Sweet Spot/Large/Corporate)
4. ✅ Priority tiers assigned correctly (Hot/Warm/Cold/Out of Scope)
5. ✅ Score breakdown JSON valid and human-readable
6. ✅ Notion records updated with scoring data
7. ✅ Sales workflow fields preserved (Status, Assigned To, etc.)
8. ✅ Scoring summary report generated (tier distribution, avg score)
9. ✅ Score recalculation works (re-run after data changes)
10. ✅ Cost: $0 (pure calculation, no API calls)

### Dependencies

**Python Packages:**
```
pydantic==2.9.2
notion-client==2.2.1
```

**Feature Dependencies:**
- **Depends on:** FEAT-000 (Models, Logger, NotionClient), FEAT-001 (initial scores), FEAT-002 (enrichment data)
- **Depended on by:** None (final pipeline stage)

### Cost

**$0** - Pure calculation, no API calls

### Timeline Estimate

**2 hours** to implement and test:
- Hour 1: LeadScorer + PracticeClassifier + PriorityTierAssigner
- Hour 2: ScoreBreakdown + NotionClient.update_practice_scoring() + testing

## Open Questions & Uncertainties

### Scoring Logic
- ❓ **Configurable weights?** Make scoring weights editable in config.json?
  - **Recommendation:** Yes, add to ScoringConfig
  - **Rationale:** Business may want to adjust priorities without code changes

- ❓ **Custom formulas?** Support custom scoring formulas (e.g., ML models)?
  - **Recommendation:** Phase 2
  - **Rationale:** Adds complexity, rule-based scoring sufficient for MVP

### Practice Classification
- ❓ **Configurable thresholds?** Make size classification thresholds editable?
  - **Recommendation:** Yes, add to ScoringConfig
  - **Rationale:** "Sweet Spot" may vary by business

### Priority Tiers
- ❓ **Manual overrides?** Allow sales reps to manually adjust tier?
  - **Recommendation:** Phase 2
  - **Rationale:** Adds complexity, trust algorithm first

- ❓ **Tier expiry?** Demote Hot → Warm after X days with no contact?
  - **Recommendation:** Phase 2
  - **Rationale:** Requires time-based logic, not critical for MVP

### Score Breakdown
- ❓ **Personalized snippets?** Generate email snippets based on score breakdown?
  - **Recommendation:** Phase 2
  - **Rationale:** Nice-to-have, not critical for prioritization

## Implementation Notes

### Critical Path
1. LeadScorer + scoring dimensions (depends on FEAT-000 models, FEAT-002 enrichment)
2. PracticeClassifier (simple classification logic)
3. PriorityTierAssigner (tier thresholds)
4. ScoreBreakdown generator (JSON formatting)
5. NotionClient.update_practice_scoring() (extends FEAT-000)

### Sequence
```
Day 1 (2 hours):
  Hour 1: LeadScorer + classification + tier assignment
  Hour 2: Score breakdown + Notion updates + testing
```

### Gotchas
1. **Confidence penalty:** Must apply to practice size score, not total score
2. **Decision maker bonus:** Counts toward 120 total, not separate
3. **Baseline normalization:** FEAT-001 score (0-25) must normalize to 0-10
4. **JSON serialization:** Score breakdown must be valid JSON for Notion
5. **Sales field preservation:** Must read existing record before update
6. **Tier distribution:** Expected ~23% Hot, validate this holds

## Success Metrics

**Definition of Done:**
- 150 practices scored within 60 seconds
- ICP fit scores accurate (0-120)
- Practice size classifications correct
- Priority tiers assigned correctly
- Score breakdown JSON valid
- Notion records updated
- Sales workflow fields preserved
- Scoring summary report generated
- Score recalculation works
- Cost: $0

**Quality Bar:**
- 80%+ test coverage on scoring logic
- Integration test passes (full pipeline)
- Score distribution matches expectations (~23% Hot, ~37% Warm)
- No unhandled exceptions

## Future Enhancements (Phase 2+)

- Configurable scoring weights (no code changes)
- Custom scoring formulas (ML models)
- Manual tier overrides
- Tier expiry (time-based deprioritization)
- Personalized email snippets
- Competitive analysis (nearby practices)
- Predictive scoring (conversion likelihood)
- Lead routing automation (assign to reps)
- Score history tracking (changes over time)

---

**Dependencies:**
- **Depends on:** FEAT-000 (Shared Infrastructure), FEAT-001 (Initial Scores), FEAT-002 (Enrichment Data)
- **Depended on by:** None (final pipeline stage)

**Related Documents:**
- [FEAT-000 PRD](../FEAT-000_shared-infrastructure/prd.md) - Shared infrastructure
- [FEAT-001 PRD](../FEAT-001_google-maps-notion/prd.md) - Initial scoring
- [FEAT-002 PRD](../FEAT-002_website-enrichment/prd.md) - Enrichment data
- [docs/system/database.md](../../system/database.md) - Notion schema
- [docs/system/architecture.md](../../system/architecture.md) - Pipeline architecture
