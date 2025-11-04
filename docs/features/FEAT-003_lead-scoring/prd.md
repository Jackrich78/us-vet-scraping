# Product Requirements Document: ICP Fit Lead Scoring

**Feature ID:** FEAT-003
**Feature Name:** ICP Fit Lead Scoring & Prioritization
**Priority:** P0 (Critical - Sales prioritization)
**Status:** Planning
**Owner:** Development Team
**Created:** 2025-11-03
**Updated:** 2025-11-04

## Executive Summary

Calculate a 0-120 point ICP (Ideal Customer Profile) fit score for each veterinary practice based on practice size, call volume indicators, technology adoption, and decision maker availability. This feature implements a **dual scoring system** (initial_score from FEAT-001 baseline + lead_score from enrichment) with **graceful degradation** for partial/missing enrichment data. Supports both **auto-trigger** integration with FEAT-002 and **manual CLI rescore** command.

**Key Capabilities:**
- Dual scoring: initial_score (Google Maps baseline) + lead_score (enrichment-based)
- Auto-triggered after FEAT-002 enrichment completes
- Manual rescore via CLI command
- Graceful handling of incomplete/low-confidence/missing enrichment data
- Score breakdown with confidence flags
- No blocking on enrichment failures

**Success Metric:** 150 practices scored within 30 seconds with accurate 0-120 scores, even with partial data.

## Problem Statement

Without systematic ICP fit scoring:
- Sales reps waste time on low-fit prospects (e.g., solo practitioners)
- High-potential practices (Sweet Spot: 3-8 vets) buried in unqualified leads
- No consistent prioritization criteria (subjective gut feel)
- No score explanations (why is this practice Hot vs Warm?)
- Enrichment data inconsistencies block scoring (when they shouldn't)
- No way to re-score practices after manual data corrections

## Goals & Non-Goals

### Goals
✅ Calculate 0-120 point ICP fit score with 5 dimensions
✅ Classify practice size: Solo (1), Small (2), Sweet Spot (3-8), Large (9-19), Corporate (20+)
✅ Assign priority tier: Hot (80-120), Warm (50-79), Cold (0-49), Out of Scope, Pending Enrichment
✅ Generate score breakdown with confidence flags
✅ Update Notion records with dual scoring (initial_score + lead_score)
✅ Auto-trigger scoring after FEAT-002 enrichment
✅ Support manual rescore via CLI command
✅ Gracefully handle partial/missing/low-confidence enrichment data
✅ Score practices with baseline-only data (no enrichment)
✅ Log errors in Score Breakdown field without blocking

### Non-Goals
❌ Predictive scoring (ML models, conversion probability)
❌ Lead routing automation (assigning to specific reps)
❌ Score decay over time (time-based deprioritization)
❌ Manual score overrides (sales reps can't adjust scores)
❌ Competitive analysis (nearby practices comparison)
❌ Blocking enrichment on scoring failures
❌ Immediate retries on enrichment errors
❌ Score versioning/history tracking
❌ Manual score adjustments by sales team

## User Stories

**As a sales rep**, I need practices ranked by ICP fit so I focus on high-potential leads first.

**As a sales manager**, I need to see why a practice is scored 95 points (with confidence flags) so I can validate prioritization logic.

**As a sales rep**, I need to know if a practice is "Sweet Spot" (3-8 vets) so I tailor my pitch.

**As a developer**, I need to recalculate scores after manual data corrections via CLI command.

**As a business owner**, I need Out of Scope practices flagged so we don't waste time on unfit prospects.

**As a developer**, I need scoring to continue even when enrichment data is incomplete/missing so the pipeline doesn't block.

## Data Availability Scenarios

### Scenario A: Full Enrichment
**Condition:** All FEAT-002 fields populated, high confidence on critical fields

**Behavior:**
- Calculate full 0-120 score using all dimensions
- No confidence penalty applied (high confidence = 1.0x multiplier)
- Priority tier assigned based on score
- Score breakdown shows all components

**Example:**
```json
{
  "vet_count_total": 4,
  "vet_count_confidence": "high",
  "emergency_24_7": true,
  "google_review_count": 234,
  "boarding_services": true,
  "online_booking": true,
  "patient_portal": true,
  "decision_maker": {"name": "Dr. Smith", "role": "Owner", "email": "smith@example.com"}
}
```
**Result:** 115 pts (Hot tier), no confidence flags

---

### Scenario B: Partial Enrichment
**Condition:** Some FEAT-002 fields missing (e.g., no decision maker found), high/medium confidence on available fields

**Behavior:**
- Calculate score with missing components = 0 pts
- No penalty for missing data (graceful degradation)
- Confidence penalty applied if available fields have medium confidence
- Score breakdown shows which dimensions contributed

**Example:**
```json
{
  "vet_count_total": 5,
  "vet_count_confidence": "medium",
  "emergency_24_7": false,
  "google_review_count": 120,
  "boarding_services": null,  // Missing
  "online_booking": true,
  "patient_portal": false,
  "decision_maker": null  // Missing
}
```
**Calculation:**
- Practice Size: 25 pts (Sweet Spot, medium confidence → 25 × 0.9 = 22.5 pts)
- Call Volume: 20 pts (100+ reviews)
- Technology: 10 pts (online booking)
- Baseline: 6 pts (Google Maps reputation)
- Decision Maker: 0 pts (missing)
**Result:** 58.5 pts (Warm tier), confidence flag: "⚠️ Medium Confidence on Vet Count"

---

### Scenario C: Low-Confidence Enrichment
**Condition:** FEAT-002 completed but vet_count_confidence='low' (scraper uncertain, made best guess)

**Behavior:**
- Calculate score with confidence penalty applied
- Confidence penalty: high=1.0x, medium=0.9x, low=0.7x
- Flag with "⚠️ Low Confidence" in Confidence Flags field
- Score breakdown explains penalty applied

**Example:**
```json
{
  "vet_count_total": 3,
  "vet_count_confidence": "low",  // Website text unclear
  "emergency_24_7": true,
  "google_review_count": 200,
  "decision_maker": {"name": "Dr. Jones", "role": "Owner"}
}
```
**Calculation:**
- Practice Size: 25 pts × 0.7 = 17.5 pts (low confidence penalty)
- Call Volume: 30 pts (emergency + 200 reviews)
- Technology: 0 pts
- Baseline: 10 pts
- Decision Maker: 5 pts (name + role only)
**Result:** 62.5 pts (Warm tier), confidence flag: "⚠️ Low Confidence on Vet Count"

---

### Scenario D: No Enrichment
**Condition:** Practice has not been enriched yet (FEAT-002 not run or skipped)

**Behavior:**
- Calculate baseline-only score (max 20 pts: reviews + rating + has_website + multiple_locations)
- Priority Tier = "Pending Enrichment"
- Score breakdown shows "Enrichment pending" in Practice Size/Technology dimensions
- No error logged (this is expected state)

**Example:**
```json
{
  "google_review_count": 150,
  "google_rating": 4.6,
  "website_url": "https://example.com",
  "multiple_locations": true,
  "enrichment_status": null  // Not enriched
}
```
**Calculation:**
- Practice Size: N/A (pending enrichment)
- Call Volume: 10 pts (150 reviews from Google Maps)
- Technology: N/A (pending enrichment)
- Baseline: 10 pts (4.6 rating + has website)
- Decision Maker: N/A (pending enrichment)
**Result:** 20 pts, Priority Tier = "Pending Enrichment"

---

### Scenario E: Enrichment Failed
**Condition:** FEAT-002 attempted but failed (timeout, LLM error, website unreachable)

**Behavior:**
- Treat same as Scenario D (baseline-only scoring)
- Enrichment Status = "Completed" (preserves FEAT-002 state)
- Lead Score = null (scoring failed due to missing data)
- Error logged in Score Breakdown field (JSON structure with error key)
- No blocking, no retries

**Example:**
```json
{
  "enrichment_status": "Completed",
  "enrichment_error": "LLM timeout after 45s",
  "vet_count_total": null,
  "vet_count_confidence": null
}
```
**Score Breakdown (JSON):**
```json
{
  "total_score": null,
  "error": "Enrichment failed: LLM timeout after 45s. Scoring with baseline only.",
  "baseline_score": 15,
  "priority_tier": "Pending Enrichment"
}
```
**Result:** Lead Score = null, Enrichment Status preserved, error logged

---

## Scoring Algorithm

### 0-120 Point System

#### 1. Practice Size & Complexity (40 points)
**Updated Sweet Spot Definition: 3-8 vets (broader than previous 3-5)**

```python
def score_practice_size(vet_count: int, confidence: str) -> Dict[str, Any]:
    """
    Score based on practice size (vet count).

    Sweet Spot: 3-8 vets (multi-vet, not too large)
    - 3-8 vets: 25 points (ideal size - UPDATED)
    - 2 or 9 vets: 15 points
    - 10+ vets or 1 vet: 5 points

    Confidence penalty (applied after base score):
    - Low confidence: score × 0.7
    - Medium confidence: score × 0.9
    - High confidence: score × 1.0 (no penalty)
    """
    base_score = 0

    if vet_count >= 10:
        base_score = 5  # Corporate territory
    elif vet_count == 9:
        base_score = 15  # Edge of Sweet Spot
    elif 3 <= vet_count <= 8:
        base_score = 25  # SWEET SPOT (updated from 3-5)
    elif vet_count == 2:
        base_score = 15  # Small multi-vet
    else:  # 1 vet
        base_score = 5  # Solo practice

    # Apply confidence penalty
    if confidence == "low":
        base_score = base_score * 0.7
    elif confidence == "medium":
        base_score = base_score * 0.9

    return {
        "score": round(base_score, 1),
        "max": 40,
        "reason": f"{vet_count} vets (confidence: {confidence})"
    }
```

**Emergency Services Bonus:**
- 24/7 Emergency: +15 points (high call volume)

---

#### 2. Call Volume Indicators (40 points)
**Updated to include Multiple Locations**

```python
def score_call_volume_indicators(practice: VeterinaryPractice) -> Dict[str, Any]:
    """
    Score based on indicators of high call volume.

    Indicators:
    - 100+ Google reviews: 20 points (busy practice)
    - 50-99 reviews: 12 points
    - 20-49 reviews: 5 points
    - Multiple locations: +10 points (ADDED per user decision)
    - High boarding/specialty services: +10 points

    Max: 40 points
    """
    score = 0
    reasons = []

    # Review count (proxy for call volume)
    if practice.google_review_count >= 100:
        score += 20
        reasons.append(f"{practice.google_review_count} reviews (20 pts)")
    elif practice.google_review_count >= 50:
        score += 12
        reasons.append(f"{practice.google_review_count} reviews (12 pts)")
    elif practice.google_review_count >= 20:
        score += 5
        reasons.append(f"{practice.google_review_count} reviews (5 pts)")

    # Multiple locations (call volume indicator)
    if practice.multiple_locations:
        score += 10
        reasons.append("Multiple locations (10 pts)")

    # Boarding/specialty services
    if practice.boarding_services or practice.specialty_services:
        score += 10
        reasons.append("Boarding/specialty services (10 pts)")

    return {
        "score": min(score, 40),  # Cap at 40
        "max": 40,
        "reason": ", ".join(reasons) if reasons else "No call volume indicators"
    }
```

---

#### 3. Technology Sophistication (20 points)

```python
def score_technology_adoption(practice: VeterinaryPractice) -> Dict[str, Any]:
    """
    Score based on technology adoption (readiness for product).

    Indicators:
    - Online booking: 10 points (tech-forward)
    - Patient portal OR telemedicine: 5 points
    - Digital records mentioned: 5 points

    Max: 20 points
    """
    score = 0
    reasons = []

    if practice.online_booking:
        score += 10
        reasons.append("Online booking (10 pts)")

    if practice.patient_portal or practice.telemedicine:
        score += 5
        reasons.append("Patient portal/telemedicine (5 pts)")

    if practice.digital_records_mentioned:
        score += 5
        reasons.append("Digital records (5 pts)")

    return {
        "score": min(score, 20),
        "max": 20,
        "reason": ", ".join(reasons) if reasons else "No technology indicators"
    }
```

---

#### 4. Baseline Quality (10 points - Recalculated from Google Maps)

**Note:** This recalculates baseline from Google Maps data, aware of initial_scorer.py logic.

```python
def score_baseline(practice: VeterinaryPractice) -> Dict[str, Any]:
    """
    Recalculate baseline from Google Maps data (not reusing initial_score).

    Components:
    - Rating 4.5+: 6 points
    - Rating 4.0-4.4: 4 points
    - Rating 3.5-3.9: 2 points
    - Has website: +4 points

    Max: 10 points
    """
    score = 0
    reasons = []

    # Rating score
    if practice.google_rating >= 4.5:
        score += 6
        reasons.append(f"{practice.google_rating}★ rating (6 pts)")
    elif practice.google_rating >= 4.0:
        score += 4
        reasons.append(f"{practice.google_rating}★ rating (4 pts)")
    elif practice.google_rating >= 3.5:
        score += 2
        reasons.append(f"{practice.google_rating}★ rating (2 pts)")

    # Has website
    if practice.website_url:
        score += 4
        reasons.append("Has website (4 pts)")

    return {
        "score": score,
        "max": 10,
        "reason": ", ".join(reasons) if reasons else "Low baseline quality"
    }
```

---

#### 5. Decision Maker Bonus (+10 points)

```python
def score_decision_maker_bonus(practice: VeterinaryPractice) -> Dict[str, Any]:
    """
    Bonus points for having decision maker information.

    Scoring:
    - Owner/PM name + email: +10 points (can reach directly)
    - Owner/PM name only: +5 points (can research email)
    - Generic contact only: 0 points

    Max: 10 points
    """
    dm = practice.decision_maker
    if not dm or not dm.name:
        return {"score": 0, "max": 10, "reason": "No decision maker info"}

    score = 0
    reasons = []

    if dm.name and dm.email:
        score = 10
        reasons.append(f"{dm.role or 'Contact'} with email (10 pts)")
    elif dm.name:
        score = 5
        reasons.append(f"{dm.role or 'Contact'} name only (5 pts)")

    return {
        "score": score,
        "max": 10,
        "reason": ", ".join(reasons)
    }
```

---

### Confidence Penalty (Applied After Calculation)

```python
CONFIDENCE_MULTIPLIERS = {
    "high": 1.0,    # No penalty
    "medium": 0.9,  # 10% penalty
    "low": 0.7      # 30% penalty
}

# Applied to practice_size_score only (most critical field)
final_practice_size_score = base_practice_size_score * CONFIDENCE_MULTIPLIERS[confidence]
```

---

### Priority Tiers

```python
def assign_tier(total_score: int, enrichment_status: str) -> str:
    """
    Assign priority tier based on ICP fit score.

    Tiers:
    - Hot (80-120 pts): 🔥 3-8 vets + decision maker + high volume
    - Warm (50-79 pts): 🌡️ Good signals, some unknowns
    - Cold (0-49 pts): ❄️ Weak signals, needs research
    - Out of Scope: ⛔ Solo (1 vet) OR Corporate (10+ vets) with <20 pts
    - Pending Enrichment: ⏳ Not yet enriched (baseline only)
    """
    if enrichment_status != "Completed":
        return "Pending Enrichment"

    if total_score >= 80:
        return "Hot"
    elif total_score >= 50:
        return "Warm"
    elif total_score >= 20:
        return "Cold"
    else:
        return "Out of Scope"
```

---

## State Machine

```
┌─────────────────────────────────────────────────────────────┐
│ LEAD SCORING STATE MACHINE                                  │
└─────────────────────────────────────────────────────────────┘

[Practice Created]
        ↓
[Google Maps Scraped] (FEAT-001)
        ↓
    initial_score calculated (0-25)
        ↓
        ├─→ [Enrichment Skipped] → Baseline-Only Scoring (Scenario D)
        │                              ↓
        │                          Priority = "Pending Enrichment"
        │
        └─→ [Enrichment Started] (FEAT-002)
                ↓
                ├─→ [Enrichment Succeeded] → Full Scoring (Scenario A/B/C)
                │       ↓                        ↓
                │   Auto-trigger FEAT-003     lead_score calculated (0-120)
                │       ↓                        ↓
                │   Calculate with full/partial data
                │       ↓
                │   Confidence penalty applied (if low/medium)
                │       ↓
                │   Priority tier assigned
                │       ↓
                │   [Scoring Complete]
                │
                └─→ [Enrichment Failed] → Baseline-Only Scoring (Scenario E)
                        ↓
                    Auto-trigger FEAT-003
                        ↓
                    lead_score = null
                        ↓
                    Error logged in Score Breakdown
                        ↓
                    Enrichment Status preserved
                        ↓
                    [Scoring Complete (with error)]

[Manual Rescore Triggered]
        ↓
    Re-read practice data from Notion
        ↓
    Recalculate lead_score
        ↓
    Update Notion with new score
        ↓
    [Scoring Complete]
```

---

## Integration with FEAT-002

### Auto-Trigger Architecture

```python
# In FEAT-002 enrichment flow:
async def enrich_practice(practice_id: str) -> None:
    """
    Enrich practice and auto-trigger scoring.
    """
    try:
        # Enrich practice
        enriched_data = await website_enricher.enrich(practice_id)
        await notion_client.update_enrichment(practice_id, enriched_data)

        # Auto-trigger FEAT-003 scoring (with timeout)
        try:
            await asyncio.wait_for(
                score_practice(practice_id),
                timeout=5.0  # 5 second timeout per practice
            )
        except asyncio.TimeoutError:
            logger.warning(f"Scoring timeout for {practice_id}")
            # Log error in Score Breakdown, don't block enrichment
            await notion_client.update_score_breakdown(
                practice_id,
                {"error": "Scoring timeout after 5s", "total_score": null}
            )
        except Exception as e:
            logger.error(f"Scoring failed for {practice_id}: {e}")
            # Log error, don't block enrichment
            await notion_client.update_score_breakdown(
                practice_id,
                {"error": f"Scoring error: {str(e)}", "total_score": null}
            )

    except Exception as e:
        logger.error(f"Enrichment failed for {practice_id}: {e}")
        # Still try to score with baseline data
        try:
            await score_practice(practice_id)  # Scenario E
        except Exception as score_error:
            logger.error(f"Baseline scoring also failed: {score_error}")
```

### Error Handling in Integration

**Timeout Behavior:**
- Scoring has 5 second timeout per practice
- If timeout exceeded, log error in Score Breakdown
- Lead Score = null
- Enrichment Status = "Completed" (preserved)
- No retry, no blocking

**Enrichment Failure Behavior:**
- FEAT-002 marks Enrichment Status = "Completed" (even if failed)
- FEAT-003 auto-triggered
- Scores with baseline-only data (Scenario E)
- Lead Score = null
- Error logged in Score Breakdown

**Notion State After Errors:**
```json
{
  "enrichment_status": "Completed",
  "enrichment_error": "LLM timeout after 45s",
  "lead_score": null,
  "score_breakdown": {
    "error": "Enrichment failed, scoring with baseline only",
    "baseline_score": 15,
    "priority_tier": "Pending Enrichment"
  }
}
```

### Performance Requirements

- **Typical latency:** <100ms per practice (pure calculation)
- **Timeout:** 5000ms (5 seconds) per practice
- **Batch processing:** 150 practices in <30 seconds (parallel execution)

---

## Manual Rescore Command

### CLI Usage

```bash
# Rescore all practices
python src/scoring/rescore_leads.py --all

# Rescore specific practice
python src/scoring/rescore_leads.py --practice-id abc123

# Rescore by filter
python src/scoring/rescore_leads.py --tier "Hot"
python src/scoring/rescore_leads.py --enrichment-status "Completed"

# Dry run (show what would be rescored)
python src/scoring/rescore_leads.py --all --dry-run
```

### Behavior with Unenriched Practices

**If practice not enriched:**
- Calculate baseline-only score (Scenario D)
- Priority Tier = "Pending Enrichment"
- No error logged (expected state)

**If practice enrichment failed:**
- Calculate baseline-only score (Scenario E)
- Lead Score = null
- Error logged in Score Breakdown

**If practice manually corrected:**
- Re-read latest data from Notion
- Recalculate full score
- Update Notion with new lead_score
- Preserve enrichment_status and enrichment_error (don't overwrite)

---

## Dual Scoring System

### Why Both initial_score and lead_score?

**initial_score (FEAT-001):**
- **Purpose:** Quick triage during Google Maps scraping
- **Range:** 0-25 points
- **Dimensions:** Google reviews + rating
- **Usage:** Identify practices worth enriching
- **When:** Calculated immediately after Google Maps scrape
- **Preserved:** Never overwritten, historical record

**lead_score (FEAT-003):**
- **Purpose:** Comprehensive ICP fit after enrichment
- **Range:** 0-120 points
- **Dimensions:** Practice size, call volume, technology, baseline, decision maker
- **Usage:** Prioritize sales outreach
- **When:** Calculated after enrichment (auto-trigger or manual rescore)
- **Updated:** Recalculated on manual rescore

### How They Coexist in Notion

**Notion Schema:**
```
Practice Table:
  - Initial Score (number, 0-25)         ← FEAT-001, never changes
  - Lead Score (number, 0-120)           ← FEAT-003, recalculated on rescore
  - Priority Tier (select)               ← Based on lead_score
  - Score Breakdown (rich_text, JSON)    ← Explains lead_score components
```

**Example Record:**
```json
{
  "practice_name": "Boston Vet Clinic",
  "initial_score": 23,           // From FEAT-001 (strong Google reputation)
  "lead_score": 115,              // From FEAT-003 (full enrichment)
  "priority_tier": "Hot",
  "score_breakdown": {
    "total_score": 115,
    "practice_size": {"score": 25, "reason": "4 vets (confidence: high)"},
    "call_volume": {"score": 30, "reason": "234 reviews, multiple locations"},
    "technology": {"score": 10, "reason": "Online booking"},
    "baseline": {"score": 10, "reason": "4.8★ rating, has website"},
    "decision_maker": {"score": 10, "reason": "Owner with email"}
  }
}
```

---

## Configuration

**config.json additions:**
```json
{
  "scoring": {
    "auto_trigger": true,          // Auto-trigger after FEAT-002 enrichment
    "timeout_seconds": 5,          // Timeout per practice

    "confidence_penalties": {
      "high": 1.0,
      "medium": 0.9,
      "low": 0.7
    },

    "practice_size": {
      "sweet_spot_min": 3,         // Updated from 3
      "sweet_spot_max": 8,         // Updated from 5
      "sweet_spot_points": 25,
      "small_multivet_points": 15,
      "solo_points": 5,
      "corporate_threshold": 10,
      "emergency_bonus": 15
    },

    "call_volume": {
      "review_high_threshold": 100,
      "review_high_points": 20,
      "review_medium_threshold": 50,
      "review_medium_points": 12,
      "review_low_threshold": 20,
      "review_low_points": 5,
      "multiple_locations_points": 10,    // ADDED
      "boarding_specialty_points": 10
    },

    "technology": {
      "online_booking_points": 10,
      "portal_telemedicine_points": 5,
      "digital_records_points": 5,
      "max_tech_score": 20
    },

    "baseline": {
      "rating_high_threshold": 4.5,
      "rating_high_points": 6,
      "rating_medium_threshold": 4.0,
      "rating_medium_points": 4,
      "rating_low_threshold": 3.5,
      "rating_low_points": 2,
      "has_website_points": 4
    },

    "decision_maker": {
      "name_email_points": 10,
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

---

## Error Handling

### Error Categories

**1. Enrichment Data Missing (Scenario D)**
- **Cause:** Practice not enriched yet
- **Recovery:** Score with baseline-only data
- **Notion State:** lead_score = calculated baseline, priority = "Pending Enrichment"
- **Log:** Info level, no error

**2. Enrichment Failed (Scenario E)**
- **Cause:** FEAT-002 timeout, LLM error, website unreachable
- **Recovery:** Score with baseline-only data
- **Notion State:** lead_score = null, error logged in Score Breakdown
- **Log:** Error level with full context

**3. Scoring Timeout**
- **Cause:** Scoring takes >5 seconds
- **Recovery:** Log error, set lead_score = null
- **Notion State:** Enrichment Status preserved, error logged
- **Log:** Warning level

**4. Notion API Failure**
- **Cause:** Network error, rate limit, invalid page ID
- **Recovery:** Retry with exponential backoff (3 attempts)
- **Notion State:** No update (preserves previous state)
- **Log:** Error level with retry count

**5. Invalid Data**
- **Cause:** vet_count = null but vet_count_confidence = "high"
- **Recovery:** Treat as missing data (Scenario D)
- **Notion State:** lead_score = baseline only
- **Log:** Warning level with data inconsistency details

### Error Log Format (Score Breakdown Field)

```json
{
  "total_score": null,
  "error": "Enrichment failed: LLM timeout after 45s",
  "error_type": "EnrichmentFailed",
  "timestamp": "2025-11-04T15:30:00Z",
  "baseline_score": 15,
  "priority_tier": "Pending Enrichment",
  "retry_count": 0
}
```

---

## Testing Strategy

### Unit Tests

**test_lead_scorer.py:**
- ✅ Scenario A: Full enrichment scoring (all fields, high confidence)
- ✅ Scenario B: Partial enrichment scoring (missing decision maker, medium confidence)
- ✅ Scenario C: Low confidence penalty application (vet_count_confidence='low')
- ✅ Scenario D: Baseline-only scoring (no enrichment data)
- ✅ Scenario E: Enrichment failed scoring (error logged, baseline only)
- ✅ Sweet spot detection (3-8 vets, not 3-5)
- ✅ Multiple locations bonus (+10 pts)
- ✅ Confidence multipliers (high=1.0x, medium=0.9x, low=0.7x)
- ✅ Edge cases: solo (1 vet), corporate (10+ vets)

**test_practice_classifier.py:**
- ✅ All size categories: Solo, Small, Sweet Spot, Large, Corporate
- ✅ Sweet spot range: 3-8 vets (not 3-5)

**test_priority_tier_assigner.py:**
- ✅ All tiers: Hot, Warm, Cold, Out of Scope, Pending Enrichment
- ✅ Enrichment status handling

**test_score_breakdown.py:**
- ✅ Valid JSON generation
- ✅ Confidence flags included
- ✅ Error logging format

### Integration Tests

**test_scoring_pipeline.py:**
- ✅ Auto-trigger after FEAT-002 enrichment
- ✅ Manual rescore command
- ✅ Timeout handling (5 second limit)
- ✅ Error state preservation in Notion
- ✅ Dual scoring (initial_score + lead_score) coexistence

**test_notion_integration.py:**
- ✅ Update lead_score without overwriting initial_score
- ✅ Preserve enrichment_status on scoring errors
- ✅ Score breakdown JSON serialization

### Mock Data

**tests/fixtures/scoring_samples.py:**
```python
# Scenario A: Full enrichment
FULL_ENRICHMENT = {
    "vet_count_total": 5,
    "vet_count_confidence": "high",
    "emergency_24_7": True,
    "google_review_count": 200,
    "multiple_locations": True,
    "boarding_services": True,
    "online_booking": True,
    "patient_portal": False,
    "decision_maker": {"name": "Dr. Smith", "email": "smith@example.com"},
    "google_rating": 4.7,
    "website_url": "https://example.com"
}
# Expected: 25 + 30 + 10 + 10 + 10 = 85 pts (Hot)

# Scenario B: Partial enrichment
PARTIAL_ENRICHMENT = {
    "vet_count_total": 4,
    "vet_count_confidence": "medium",
    "emergency_24_7": False,
    "google_review_count": 80,
    "multiple_locations": False,
    "boarding_services": None,  # Missing
    "online_booking": True,
    "patient_portal": False,
    "decision_maker": None,  # Missing
    "google_rating": 4.2,
    "website_url": "https://example.com"
}
# Expected: (25 × 0.9) + 12 + 10 + 8 + 0 = 52.5 pts (Warm)

# Scenario C: Low confidence
LOW_CONFIDENCE = {
    "vet_count_total": 6,
    "vet_count_confidence": "low",
    "emergency_24_7": True,
    "google_review_count": 150,
    "decision_maker": {"name": "Dr. Jones"},
    "google_rating": 4.5,
    "website_url": "https://example.com"
}
# Expected: (25 × 0.7) + 35 + 0 + 10 + 5 = 67.5 pts (Warm), confidence flag

# Scenario D: No enrichment
NO_ENRICHMENT = {
    "vet_count_total": None,
    "enrichment_status": None,
    "google_review_count": 100,
    "google_rating": 4.3,
    "website_url": "https://example.com",
    "multiple_locations": False
}
# Expected: 20 pts baseline, Priority = "Pending Enrichment"

# Scenario E: Enrichment failed
ENRICHMENT_FAILED = {
    "enrichment_status": "Completed",
    "enrichment_error": "LLM timeout",
    "vet_count_total": None,
    "google_review_count": 120,
    "google_rating": 4.6,
    "website_url": "https://example.com"
}
# Expected: lead_score = null, error logged, baseline calculated
```

---

## Acceptance Criteria

1. ✅ 150 practices scored within 30 seconds (parallel execution)
2. ✅ ICP fit scores accurate (0-120 range) for all scenarios (A-E)
3. ✅ Sweet Spot defined as 3-8 vets (not 3-5)
4. ✅ Multiple locations bonus applied (+10 pts)
5. ✅ Confidence penalties applied correctly (high=1.0x, medium=0.9x, low=0.7x)
6. ✅ Dual scoring system works (initial_score preserved, lead_score calculated)
7. ✅ Auto-trigger after FEAT-002 enrichment
8. ✅ Manual rescore command works
9. ✅ Baseline-only scoring for unenriched practices (Scenario D)
10. ✅ Graceful error handling for enrichment failures (Scenario E)
11. ✅ Error logging in Score Breakdown field (JSON format)
12. ✅ Enrichment Status preserved on scoring errors
13. ✅ Timeout enforced (5 seconds per practice)
14. ✅ Priority tiers assigned correctly (including "Pending Enrichment")
15. ✅ Score breakdown JSON valid and human-readable
16. ✅ Cost: $0 (pure calculation, no API calls)

---

## Dependencies

**Python Packages:**
```
pydantic==2.9.2
notion-client==2.2.1
```

**Feature Dependencies:**
- **Depends on:** FEAT-000 (Models, Logger, NotionClient), FEAT-001 (initial scores), FEAT-002 (enrichment data, auto-trigger)
- **Depended on by:** None (final pipeline stage)

---

## Cost

**$0** - Pure calculation, no API calls

---

## Timeline Estimate

**3 hours** to implement and test:
- Hour 1: LeadScorer + updated algorithm (sweet spot, multiple locations, confidence penalties)
- Hour 2: Dual scoring integration + auto-trigger + error handling
- Hour 3: Manual rescore command + comprehensive testing (Scenarios A-E)

---

## Open Questions & Uncertainties

### Scoring Logic
- ❓ **Adjust sweet spot range dynamically?** Allow business to change 3-8 to 4-10 via config?
  - **Recommendation:** Yes, already configurable in ScoringConfig
  - **Rationale:** Business may refine ICP based on conversion data

### Error Recovery
- ❓ **Automatic retry on scoring timeout?** Retry failed scoring after enrichment completes?
  - **Recommendation:** No (Phase 2)
  - **Rationale:** Manual rescore command sufficient for MVP, avoids retry complexity

### Confidence Penalties
- ❓ **Apply confidence penalty to other dimensions?** Currently only applied to practice_size_score
  - **Recommendation:** Monitor and evaluate (Phase 2)
  - **Rationale:** Vet count is most critical field, other fields less confidence-sensitive

---

## Implementation Notes

### Critical Path
1. Update LeadScorer with new algorithm (sweet spot 3-8, multiple locations, confidence penalties)
2. Implement dual scoring (preserve initial_score, calculate lead_score)
3. Add auto-trigger integration with FEAT-002
4. Implement error handling for Scenarios D & E
5. Create manual rescore CLI command
6. Comprehensive testing (all scenarios)

### Sequence
```
Day 1 (3 hours):
  Hour 1: Update scoring algorithm + confidence penalties
  Hour 2: Dual scoring + auto-trigger + error handling
  Hour 3: Manual rescore command + testing
```

### Gotchas
1. **Sweet spot range:** 3-8 vets (not 3-5) - update all references
2. **Multiple locations:** +10 pts in call_volume dimension
3. **Confidence penalty:** Applied to practice_size_score only (not total score)
4. **Dual scoring:** Preserve initial_score, never overwrite
5. **Auto-trigger timeout:** 5 seconds per practice, log error if exceeded
6. **Error state:** lead_score = null, Enrichment Status preserved
7. **Baseline recalculation:** Don't reuse initial_score, recalculate from Google Maps data
8. **Pending Enrichment tier:** Separate from Out of Scope (different meaning)

---

## Success Metrics

**Definition of Done:**
- 150 practices scored within 30 seconds
- All scenarios (A-E) handled correctly
- Dual scoring system works (initial_score + lead_score)
- Auto-trigger integration complete
- Manual rescore command functional
- Error handling comprehensive (no blocking)
- Confidence penalties applied correctly
- Sweet spot range updated (3-8 vets)
- Multiple locations bonus applied
- Score breakdown includes confidence flags
- Notion updates preserve enrichment state
- Cost: $0

**Quality Bar:**
- 90%+ test coverage on scoring logic
- Integration tests pass (all scenarios)
- No unhandled exceptions
- Error logs comprehensive and actionable

---

## Future Enhancements (Phase 2+)

- Automatic retry on scoring timeout
- Score history tracking (changes over time)
- Confidence penalty applied to all dimensions (not just practice_size)
- Custom scoring formulas (ML models)
- Manual tier overrides
- Tier expiry (time-based deprioritization)
- Personalized email snippets
- Competitive analysis (nearby practices)
- Predictive scoring (conversion likelihood)
- Lead routing automation (assign to reps)

---

**Dependencies:**
- **Depends on:** FEAT-000 (Shared Infrastructure), FEAT-001 (Initial Scores), FEAT-002 (Enrichment Data, Auto-Trigger)
- **Depended on by:** None (final pipeline stage)

**Related Documents:**
- [FEAT-000 PRD](../FEAT-000_shared-infrastructure/prd.md) - Shared infrastructure
- [FEAT-001 PRD](../FEAT-001_google-maps-notion/prd.md) - Initial scoring (initial_score)
- [FEAT-002 PRD](../FEAT-002_website-enrichment/prd.md) - Enrichment data (auto-trigger source)
- [docs/system/database.md](../../system/database.md) - Notion schema
- [docs/system/architecture.md](../../system/architecture.md) - Pipeline architecture
