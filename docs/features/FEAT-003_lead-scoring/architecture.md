# FEAT-003: Lead Scoring - Architecture Document

**Feature ID:** FEAT-003
**Feature Name:** Lead Scoring
**Version:** 1.0.0
**Last Updated:** 2025-11-04
**Status:** Planning

## 1. Context & Problem Statement

### Business Context

FEAT-003 implements an intelligent lead scoring system that evaluates veterinary practices across multiple dimensions to prioritize sales outreach efforts. The system must handle varying levels of data quality and completeness while maintaining system reliability and performance.

### Core Challenges

1. **Variable Data Quality:** Practices may have complete, partial, or no enrichment data from FEAT-002
2. **Auto-Trigger Integration:** Scoring automatically fires after enrichment, requiring robust error isolation
3. **Dual Scoring System:**
   - `initial_score` (FEAT-001): Quick Google Maps metrics, never changes
   - `lead_score` (FEAT-003): Comprehensive ICP score with enrichment data
4. **Performance Constraints:** Must score 150 practices in <15 seconds with individual timeouts at 5 seconds
5. **Error Isolation:** Scoring failures cannot propagate back to FEAT-002 enrichment workflow

### Success Criteria

- Score practices with 0-120 point scale based on 5 weighted components
- Classify into priority tiers: Hot (80-120), Warm (50-79), Cold (0-49), Pending Enrichment
- Handle partial/missing enrichment data gracefully with appropriate confidence penalties
- Maintain <100ms typical scoring time, enforce <5000ms timeout
- Prevent cascading failures through circuit breaker pattern
- Preserve all existing Notion data during score updates

## 2. System Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    FEAT-002 Enrichment                          │
│                  (Auto-Trigger on Complete)                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ScoringOrchestrator                           │
│                   (Error Boundary Root)                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ asyncio.wait_for(timeout=5.0s)                           │  │
│  │ try/except boundary                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└────┬────────────────────────────────────────────────────────────┘
     │
     ├──► CircuitBreaker (pybreaker)
     │    └─► State: CLOSED/OPEN/HALF_OPEN
     │
     ├──► DataValidator
     │    ├─► Check enrichment_data availability
     │    ├─► Validate enrichment_confidence level
     │    └─► Apply data quality defaults
     │
     ├──► ScoreCalculator
     │    ├─► Practice Size Component (0-30 pts)
     │    ├─► Call Volume Component (0-30 pts)
     │    ├─► Technology Stack Component (0-30 pts)
     │    ├─► Baseline Metrics Component (0-20 pts)
     │    └─► Decision Maker Component (0-10 pts)
     │
     ├──► ConfidenceEvaluator
     │    ├─► Assess enrichment confidence
     │    ├─► Apply multiplicative penalties
     │    └─► Generate confidence flags
     │
     ├──► TierClassifier
     │    ├─► Assign priority tier
     │    ├─► Handle "Pending Enrichment" state
     │    └─► Add confidence flags to tier
     │
     ├──► BreakdownGenerator
     │    ├─► Generate JSON score explanation
     │    ├─► Include component details
     │    └─► Document data quality issues
     │
     └──► NotionUpdater
          ├─► Update lead_score field
          ├─► Update priority_tier field
          ├─► Update score_breakdown field
          ├─► Update confidence_flags multi-select
          ├─► Update scoring_status field
          └─► Preserve all other fields
```

### Component Responsibilities

**ScoringOrchestrator**
- Main entry point for scoring workflow
- Enforces timeout with `asyncio.wait_for()`
- Root error boundary with try/except
- Coordinates all sub-components
- Logs all scoring events and errors
- Returns structured `ScoringOutput`

**CircuitBreaker**
- Wraps scoring operations with `pybreaker.CircuitBreaker`
- Prevents cascading failures after repeated errors
- Configuration: `fail_max=5`, `reset_timeout=60s`
- States: CLOSED (normal), OPEN (failing), HALF_OPEN (testing recovery)

**DataValidator**
- Validates `enrichment_data` presence and structure
- Checks `enrichment_confidence` level
- Applies defaults for missing optional fields
- Returns validation result with data quality flags

**ScoreCalculator**
- Calculates weighted score from 5 components
- Handles partial data (missing components = 0 points)
- Baseline-only mode for practices without enrichment
- Returns component breakdown and total score

**ConfidenceEvaluator**
- Assesses overall data confidence
- Applies multiplicative penalties for low confidence:
  - High confidence: 1.0x (no penalty)
  - Medium confidence: 0.9x (10% penalty)
  - Low confidence: 0.8x (20% penalty)
- Generates confidence flags for UI display

**TierClassifier**
- Assigns priority tier based on final score:
  - Hot: 80-120 points
  - Warm: 50-79 points
  - Cold: 0-49 points
  - Pending Enrichment: No enrichment data
- Attaches confidence flags to tier

**BreakdownGenerator**
- Creates JSON explanation of score
- Documents each component's contribution
- Notes missing data or low confidence
- Includes human-readable summary

**NotionUpdater**
- Updates score fields in Notion database
- Preserves all non-score fields
- Handles API errors gracefully
- Returns update status

## 3. Data Flow Diagrams

### Flow A: Full Enrichment (Happy Path)

```
FEAT-002 Enrichment Complete
  enrichment_status = "Completed"
  enrichment_confidence = "high"
  enrichment_data = VetPracticeExtraction{...all fields}
        │
        ▼
Auto-Trigger (if auto_trigger_scoring = true)
        │
        ▼
ScoringOrchestrator.calculate_icp_score(practice_id)
  ├─► Load practice from Notion
  ├─► Extract google_maps_data, enrichment_data
  └─► Start timeout timer (5000ms)
        │
        ▼
CircuitBreaker.call(score_practice)
  └─► State: CLOSED (normal operation)
        │
        ▼
DataValidator.validate(enrichment_data)
  ├─► enrichment_data exists ✓
  ├─► enrichment_confidence = "high" ✓
  ├─► vet_count present ✓
  ├─► phone_numbers present ✓
  ├─► technologies present ✓
  └─► decision_maker present ✓
        │
        ▼
ScoreCalculator.calculate_components()
  ├─► Practice Size: vet_count=5 → 20 pts (sweet spot)
  ├─► Call Volume: phone_count=3 → 25 pts (high)
  ├─► Technology: emr_system="Cornerstone" → 30 pts (top tier)
  ├─► Baseline: reviews=45, rating=4.5, website=true → 18 pts
  ├─► Decision Maker: owner_info found → 10 pts
  └─► Total: 103 pts
        │
        ▼
ConfidenceEvaluator.evaluate(confidence="high")
  ├─► Confidence multiplier: 1.0x
  ├─► Final score: 103 × 1.0 = 103 pts
  └─► Confidence flags: []
        │
        ▼
TierClassifier.classify(score=103)
  └─► Priority Tier: "Hot" (80-120 range)
        │
        ▼
BreakdownGenerator.generate(components)
  └─► JSON: {
        "total_score": 103,
        "confidence": "high",
        "components": {
          "practice_size": {"score": 20, "detail": "5 vets (sweet spot)"},
          "call_volume": {"score": 25, "detail": "3 phone numbers"},
          "technology": {"score": 30, "detail": "Cornerstone EMR"},
          "baseline": {"score": 18, "detail": "45 reviews, 4.5★"},
          "decision_maker": {"score": 10, "detail": "Owner identified"}
        }
      }
        │
        ▼
NotionUpdater.update_scores(practice_id, output)
  ├─► Update "Lead Score": 103
  ├─► Update "Priority Tier": "Hot"
  ├─► Update "Score Breakdown": JSON string
  ├─► Update "Confidence Flags": []
  ├─► Update "Scoring Status": "Scored"
  ├─► Preserve "Initial Score": 72 (unchanged)
  ├─► Preserve "Enrichment Status": "Completed" (unchanged)
  └─► Preserve all sales workflow fields
        │
        ▼
Success: Scoring Status = "Scored"
Elapsed time: 87ms
```

### Flow B: Partial Enrichment (Missing Decision Maker)

```
FEAT-002 Enrichment Partial
  enrichment_status = "Partial"
  enrichment_confidence = "high"
  enrichment_data.decision_maker = None
        │
        ▼
ScoringOrchestrator.calculate_icp_score(practice_id)
        │
        ▼
DataValidator.validate(enrichment_data)
  ├─► enrichment_data exists ✓
  ├─► enrichment_confidence = "high" ✓
  ├─► vet_count present ✓
  ├─► phone_numbers present ✓
  ├─► technologies present ✓
  └─► decision_maker MISSING ✗
        │
        ▼
ScoreCalculator.calculate_components()
  ├─► Practice Size: 20 pts
  ├─► Call Volume: 25 pts
  ├─► Technology: 30 pts
  ├─► Baseline: 18 pts
  ├─► Decision Maker: 0 pts (missing field)
  └─► Total: 93 pts (max 110 instead of 120)
        │
        ▼
ConfidenceEvaluator.evaluate(confidence="high")
  ├─► Confidence multiplier: 1.0x (no penalty, present data is high quality)
  ├─► Final score: 93 pts
  └─► Confidence flags: []
        │
        ▼
TierClassifier.classify(score=93)
  └─► Priority Tier: "Hot" (still in 80-120 range)
        │
        ▼
BreakdownGenerator.generate(components)
  └─► JSON: {
        "total_score": 93,
        "confidence": "high",
        "components": {
          "practice_size": {"score": 20, "detail": "5 vets"},
          "call_volume": {"score": 25, "detail": "3 phone numbers"},
          "technology": {"score": 30, "detail": "Cornerstone EMR"},
          "baseline": {"score": 18, "detail": "45 reviews, 4.5★"},
          "decision_maker": {"score": 0, "detail": "Not found"}
        }
      }
        │
        ▼
NotionUpdater.update_scores(practice_id, output)
  ├─► Update "Lead Score": 93
  ├─► Update "Priority Tier": "Hot"
  └─► Update "Scoring Status": "Scored"
        │
        ▼
Success: Scoring completed with partial data
```

### Flow C: Low Confidence Enrichment

```
FEAT-002 Enrichment Complete
  enrichment_status = "Completed"
  enrichment_confidence = "low" (vet count guessed from reviews)
  enrichment_data = VetPracticeExtraction{...}
        │
        ▼
DataValidator.validate(enrichment_data)
  ├─► enrichment_data exists ✓
  ├─► enrichment_confidence = "low" ⚠
  └─► All fields present ✓
        │
        ▼
ScoreCalculator.calculate_components()
  └─► Total: 95 pts (before confidence penalty)
        │
        ▼
ConfidenceEvaluator.evaluate(confidence="low")
  ├─► Confidence multiplier: 0.8x (20% penalty)
  ├─► Final score: 95 × 0.8 = 76 pts
  └─► Confidence flags: ["Low Confidence Vet Count"]
        │
        ▼
TierClassifier.classify(score=76)
  └─► Priority Tier: "Warm" (50-79 range, dropped from Hot)
        │
        ▼
BreakdownGenerator.generate(components)
  └─► JSON: {
        "total_score": 76,
        "confidence": "low",
        "confidence_penalty": "20%",
        "components": {...},
        "warnings": ["Vet count estimated from reviews"]
      }
        │
        ▼
NotionUpdater.update_scores(practice_id, output)
  ├─► Update "Lead Score": 76
  ├─► Update "Priority Tier": "Warm"
  ├─► Update "Confidence Flags": ["Low Confidence Vet Count"]
  └─► Update "Scoring Status": "Scored"
        │
        ▼
Success: Scored with confidence warning
```

### Flow D: No Enrichment (Baseline Only)

```
FEAT-002 Enrichment Failed or Skipped
  enrichment_status = "Failed" or "Not Started"
  enrichment_data = None
        │
        ▼
DataValidator.validate(enrichment_data)
  ├─► enrichment_data is None ✗
  └─► Enter baseline-only mode
        │
        ▼
ScoreCalculator.calculate_baseline_only()
  ├─► Practice Size: 0 pts (no enrichment)
  ├─► Call Volume: 0 pts (no enrichment)
  ├─► Technology: 0 pts (no enrichment)
  ├─► Baseline:
  │     - reviews: 45 → 20 pts
  │     - rating: 4.5 → 6 pts
  │     - has_website: true → 4 pts
  │     - multiple_locations: true → 10 pts
  ├─► Decision Maker: 0 pts (no enrichment)
  └─► Total: 40 pts (max baseline score)
        │
        ▼
ConfidenceEvaluator.evaluate(confidence=None)
  ├─► No confidence penalty (baseline data is reliable)
  ├─► Final score: 40 pts
  └─► Confidence flags: []
        │
        ▼
TierClassifier.classify(score=40, enrichment_data=None)
  └─► Priority Tier: "Pending Enrichment" (special tier)
        │
        ▼
BreakdownGenerator.generate(components)
  └─► JSON: {
        "total_score": 40,
        "mode": "baseline_only",
        "components": {
          "baseline": {"score": 40, "detail": "Google Maps metrics only"}
        },
        "note": "Awaiting FEAT-002 enrichment for full score"
      }
        │
        ▼
NotionUpdater.update_scores(practice_id, output)
  ├─► Update "Lead Score": 40
  ├─► Update "Priority Tier": "Pending Enrichment"
  └─► Update "Scoring Status": "Scored"
        │
        ▼
Success: Baseline score assigned, awaiting enrichment
```

### Flow E: Scoring Timeout

```
ScoringOrchestrator.calculate_icp_score(practice_id)
        │
        ▼
asyncio.wait_for(score_practice(), timeout=5.0)
        │
        ▼
ScoreCalculator.calculate_components()
  └─► External API call hangs (e.g., Notion slow response)
        │
        ▼ (after 5 seconds)
        │
asyncio.TimeoutError raised
        │
        ▼
ScoringOrchestrator catches TimeoutError
  ├─► Log error: "Scoring timeout for {practice_id} after 5000ms"
  ├─► CircuitBreaker.record_failure()
  └─► Generate error output
        │
        ▼
BreakdownGenerator.generate_error()
  └─► JSON: {
        "error": "Scoring timeout",
        "detail": "Calculation exceeded 5000ms limit",
        "timestamp": "2025-11-04T10:32:15Z"
      }
        │
        ▼
NotionUpdater.update_scores(practice_id, error_output)
  ├─► Update "Lead Score": null
  ├─► Update "Priority Tier": null
  ├─► Update "Score Breakdown": error JSON
  ├─► Update "Scoring Status": "Failed"
  ├─► Preserve "Enrichment Status": "Completed" (unchanged)
  └─► Preserve all other fields
        │
        ▼
FEAT-002 workflow continues (error isolated)
Return to caller: ScoringOutput(scoring_status="Failed")
```

### Flow F: Scoring Exception (Calculation Error)

```
ScoreCalculator.calculate_components()
  └─► Raises ValueError: "Invalid vet_count: -1"
        │
        ▼
ScoringOrchestrator catches Exception
  ├─► Log error with traceback
  ├─► CircuitBreaker.record_failure()
  └─► Generate error output
        │
        ▼
BreakdownGenerator.generate_error(exception)
  └─► JSON: {
        "error": "Calculation error",
        "detail": "Invalid vet_count: -1",
        "type": "ValueError",
        "timestamp": "2025-11-04T10:33:22Z"
      }
        │
        ▼
NotionUpdater.update_scores(practice_id, error_output)
  ├─► Update "Lead Score": null
  ├─► Update "Scoring Status": "Failed"
  └─► Update "Score Breakdown": error JSON
        │
        ▼
Return: ScoringOutput(scoring_status="Failed")
FEAT-002 continues normally
```

### Flow G: Circuit Breaker Open

```
CircuitBreaker.call(score_practice)
  └─► Current state: OPEN (too many recent failures)
        │
        ▼
pybreaker.CircuitBreakerError raised
  └─► "Circuit breaker is OPEN"
        │
        ▼
ScoringOrchestrator catches CircuitBreakerError
  ├─► Log warning: "Circuit breaker OPEN, skipping scoring"
  └─► Generate circuit breaker error output
        │
        ▼
BreakdownGenerator.generate_error()
  └─► JSON: {
        "error": "Circuit breaker open",
        "detail": "Too many recent scoring failures, temporarily disabled",
        "retry_after": "60s",
        "timestamp": "2025-11-04T10:35:00Z"
      }
        │
        ▼
NotionUpdater.update_scores(practice_id, error_output)
  ├─► Update "Lead Score": null
  ├─► Update "Scoring Status": "Failed"
  └─► Update "Score Breakdown": circuit breaker JSON
        │
        ▼
Return: ScoringOutput(scoring_status="Failed")
Auto-retry after circuit breaker reset (60s)
```

## 4. Integration Contracts

### FEAT-002 → FEAT-003 Contract

```python
from dataclasses import dataclass
from typing import Optional, Literal, List
from datetime import datetime

@dataclass
class VeterinaryPractice:
    """Google Maps data structure (from FEAT-001)"""
    name: str
    address: str
    phone: Optional[str]
    website: Optional[str]
    rating: Optional[float]
    reviews_count: Optional[int]
    place_id: str
    has_multiple_locations: bool

@dataclass
class VetPracticeExtraction:
    """Enrichment data structure (from FEAT-002)"""
    # Practice size
    vet_count: Optional[int]  # May be None if not found
    vet_count_confidence: Literal["high", "medium", "low"]

    # Contact information
    phone_numbers: List[str]  # May be empty list
    email_addresses: List[str]  # May be empty list

    # Technology stack
    emr_system: Optional[str]  # "Cornerstone", "Avimark", "IDEXX", etc.
    has_online_booking: bool
    has_telemedicine: bool
    technologies: List[str]  # Additional tech indicators

    # Decision maker
    decision_maker: Optional[dict]  # May be None
    # Format: {"name": str, "title": str, "linkedin": str}

    # Metadata
    extraction_timestamp: datetime
    extraction_method: Literal["structured", "llm", "hybrid"]

@dataclass
class ScoringInput:
    """Input contract for FEAT-003 scoring"""
    practice_id: str  # Notion page ID
    google_maps_data: VeterinaryPractice  # Always present (from FEAT-001)
    enrichment_data: Optional[VetPracticeExtraction]  # May be None
    enrichment_status: Literal["Completed", "Partial", "Failed", "Not Started"]
    enrichment_confidence: Optional[Literal["high", "medium", "low"]]  # None if no enrichment

    # Trigger context
    triggered_by: Literal["auto", "manual", "rescore"]
    trigger_timestamp: datetime

@dataclass
class ScoringOutput:
    """Output contract for FEAT-003 scoring"""
    practice_id: str

    # Scoring results
    lead_score: Optional[int]  # 0-120, None if scoring failed
    priority_tier: Optional[str]  # "Hot"/"Warm"/"Cold"/"Pending Enrichment", None if failed
    score_breakdown: str  # JSON string with component details or error message
    confidence_flags: List[str]  # ["Low Confidence Vet Count", etc.]

    # Metadata
    scoring_status: Literal["Scored", "Failed"]
    scoring_timestamp: datetime
    scoring_duration_ms: int

    # Error details (if scoring_status = "Failed")
    error_type: Optional[str]  # "timeout", "calculation_error", "circuit_breaker", etc.
    error_message: Optional[str]

# Error Handling Contract
# 1. FEAT-003 MUST NOT raise exceptions that propagate to FEAT-002
# 2. All exceptions caught and logged internally with full traceback
# 3. Timeout enforced at 5 seconds via asyncio.wait_for()
# 4. Circuit breaker tracks failure rate and opens after 5 consecutive failures
# 5. Circuit breaker auto-resets after 60 seconds in OPEN state
# 6. All errors return ScoringOutput with scoring_status="Failed"
```

### FEAT-003 → Notion Contract

```python
# Notion Database Field Mappings

# Fields Updated by FEAT-003
NOTION_SCORE_FIELDS = {
    "lead_score": {
        "property_name": "Lead Score",
        "property_type": "number",
        "range": [0, 120],
        "nullable": True,  # None if scoring failed
    },
    "priority_tier": {
        "property_name": "Priority Tier",
        "property_type": "select",
        "options": ["Hot", "Warm", "Cold", "Pending Enrichment"],
        "nullable": True,  # None if scoring failed
    },
    "score_breakdown": {
        "property_name": "Score Breakdown",
        "property_type": "rich_text",
        "format": "JSON string",
        "max_length": 2000,  # Notion rich_text limit
    },
    "confidence_flags": {
        "property_name": "Confidence Flags",
        "property_type": "multi_select",
        "options": [
            "Low Confidence Vet Count",
            "Missing Decision Maker",
            "Limited Technology Data",
            "Partial Enrichment",
        ],
    },
    "scoring_status": {
        "property_name": "Scoring Status",
        "property_type": "select",
        "options": ["Not Scored", "Scored", "Failed"],
    },
}

# Fields Preserved by FEAT-003 (NEVER modified)
NOTION_PRESERVED_FIELDS = {
    "initial_score": "Initial Score",  # From FEAT-001, read-only
    "enrichment_status": "Enrichment Status",  # From FEAT-002, read-only
    "status": "Status",  # Sales workflow status
    "assigned_to": "Assigned To",  # Sales rep assignment
    "call_notes": "Call Notes",  # Sales activity
    "last_contact": "Last Contact",  # Sales activity
    "tags": "Tags",  # User-defined tags
    # All other custom fields
}

# Update API Contract
async def update_scoring_fields(
    practice_id: str,
    scoring_output: ScoringOutput,
) -> NotionUpdateResult:
    """
    Update scoring fields in Notion database.

    Args:
        practice_id: Notion page ID
        scoring_output: Scoring results

    Returns:
        NotionUpdateResult with success/failure status

    Error Handling:
        - Retries up to 3 times on transient errors (rate limit, network)
        - Exponential backoff: 1s, 2s, 4s
        - Logs error and returns failure status if all retries exhausted
        - NEVER raises exceptions to caller

    Preservation Guarantee:
        - Only updates fields in NOTION_SCORE_FIELDS
        - Reads existing page properties first
        - Merges updates with existing data
        - Never overwrites fields in NOTION_PRESERVED_FIELDS
    """
    pass

@dataclass
class NotionUpdateResult:
    success: bool
    practice_id: str
    updated_fields: List[str]  # Names of fields updated
    error_message: Optional[str]  # If success=False
    retry_count: int
    duration_ms: int
```

## 5. Class Design

### Core Classes

```python
# src/scoring/orchestrator.py

import asyncio
import logging
from typing import Optional
from datetime import datetime
from pybreaker import CircuitBreaker, CircuitBreakerError

from .models import ScoringInput, ScoringOutput
from .validator import DataValidator
from .calculator import ScoreCalculator
from .confidence import ConfidenceEvaluator
from .classifier import TierClassifier
from .breakdown import BreakdownGenerator
from .notion_updater import NotionUpdater
from ..config import ScoringConfig

logger = logging.getLogger(__name__)


class ScoringOrchestrator:
    """
    Main orchestrator for lead scoring workflow.

    Responsibilities:
    - Coordinate all scoring components
    - Enforce timeout with asyncio.wait_for()
    - Root error boundary with comprehensive exception handling
    - Circuit breaker integration
    - Performance monitoring and logging
    """

    def __init__(self, config: ScoringConfig):
        self.config = config

        # Initialize components
        self.validator = DataValidator()
        self.calculator = ScoreCalculator(config)
        self.confidence_evaluator = ConfidenceEvaluator(config)
        self.classifier = TierClassifier(config)
        self.breakdown_generator = BreakdownGenerator()
        self.notion_updater = NotionUpdater(config)

        # Circuit breaker configuration
        self.circuit_breaker = CircuitBreaker(
            fail_max=config.circuit_breaker_fail_max,  # 5 failures
            reset_timeout=config.circuit_breaker_reset_timeout,  # 60 seconds
            exclude=[asyncio.TimeoutError],  # Don't count timeouts as circuit failures
        )

    async def calculate_icp_score(
        self,
        scoring_input: ScoringInput
    ) -> ScoringOutput:
        """
        Calculate ICP score for a practice with comprehensive error handling.

        Args:
            scoring_input: Practice data and enrichment results

        Returns:
            ScoringOutput with score or error details

        Error Handling:
            - Catches ALL exceptions (never propagates to caller)
            - Enforces 5-second timeout
            - Circuit breaker prevents cascading failures
            - Logs all errors with full context
            - Returns ScoringOutput with scoring_status="Failed" on error
        """
        start_time = datetime.now()
        practice_id = scoring_input.practice_id

        logger.info(
            f"Starting scoring for practice {practice_id}",
            extra={
                "practice_id": practice_id,
                "enrichment_status": scoring_input.enrichment_status,
                "triggered_by": scoring_input.triggered_by,
            }
        )

        try:
            # Enforce timeout with asyncio.wait_for
            scoring_output = await asyncio.wait_for(
                self._score_practice_with_circuit_breaker(scoring_input),
                timeout=self.config.scoring_timeout_seconds  # 5.0 seconds
            )

            # Update Notion with results
            await self.notion_updater.update_scoring_fields(
                practice_id,
                scoring_output
            )

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            logger.info(
                f"Scoring completed for practice {practice_id}",
                extra={
                    "practice_id": practice_id,
                    "lead_score": scoring_output.lead_score,
                    "priority_tier": scoring_output.priority_tier,
                    "duration_ms": duration_ms,
                }
            )

            return scoring_output

        except asyncio.TimeoutError:
            # Timeout error (>5 seconds)
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(
                f"Scoring timeout for practice {practice_id} after {duration_ms}ms",
                extra={
                    "practice_id": practice_id,
                    "timeout_ms": self.config.scoring_timeout_seconds * 1000,
                }
            )

            error_output = self._create_error_output(
                practice_id=practice_id,
                error_type="timeout",
                error_message=f"Scoring exceeded {self.config.scoring_timeout_seconds * 1000}ms limit",
                duration_ms=int(duration_ms),
            )

            # Update Notion with error
            await self.notion_updater.update_scoring_fields(
                practice_id,
                error_output
            )

            return error_output

        except CircuitBreakerError:
            # Circuit breaker is OPEN
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            logger.warning(
                f"Circuit breaker OPEN, skipping scoring for practice {practice_id}",
                extra={
                    "practice_id": practice_id,
                    "circuit_state": "OPEN",
                }
            )

            error_output = self._create_error_output(
                practice_id=practice_id,
                error_type="circuit_breaker",
                error_message="Too many recent scoring failures, temporarily disabled",
                duration_ms=int(duration_ms),
            )

            # Update Notion with circuit breaker error
            await self.notion_updater.update_scoring_fields(
                practice_id,
                error_output
            )

            return error_output

        except Exception as e:
            # Catch-all for unexpected errors
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            logger.exception(
                f"Unexpected error scoring practice {practice_id}",
                extra={
                    "practice_id": practice_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                }
            )

            error_output = self._create_error_output(
                practice_id=practice_id,
                error_type="unexpected_error",
                error_message=f"{type(e).__name__}: {str(e)}",
                duration_ms=int(duration_ms),
            )

            # Update Notion with error
            await self.notion_updater.update_scoring_fields(
                practice_id,
                error_output
            )

            return error_output

    async def _score_practice_with_circuit_breaker(
        self,
        scoring_input: ScoringInput
    ) -> ScoringOutput:
        """
        Score practice with circuit breaker protection.

        Raises:
            CircuitBreakerError: If circuit breaker is OPEN
            Exception: Any scoring calculation error
        """
        return await self.circuit_breaker.call_async(
            self._score_practice_internal,
            scoring_input
        )

    async def _score_practice_internal(
        self,
        scoring_input: ScoringInput
    ) -> ScoringOutput:
        """
        Internal scoring logic (wrapped by circuit breaker).

        Raises:
            ValueError: Invalid data
            Exception: Calculation errors
        """
        # Step 1: Validate data
        validation_result = self.validator.validate(
            enrichment_data=scoring_input.enrichment_data,
            enrichment_confidence=scoring_input.enrichment_confidence,
        )

        # Step 2: Calculate component scores
        component_scores = self.calculator.calculate_components(
            google_maps_data=scoring_input.google_maps_data,
            enrichment_data=scoring_input.enrichment_data,
            validation_result=validation_result,
        )

        # Step 3: Apply confidence penalty
        confidence_result = self.confidence_evaluator.evaluate(
            component_scores=component_scores,
            enrichment_confidence=scoring_input.enrichment_confidence,
        )

        # Step 4: Classify into tier
        tier_result = self.classifier.classify(
            final_score=confidence_result.final_score,
            confidence_flags=confidence_result.confidence_flags,
            has_enrichment=scoring_input.enrichment_data is not None,
        )

        # Step 5: Generate breakdown
        breakdown_json = self.breakdown_generator.generate(
            component_scores=component_scores,
            confidence_result=confidence_result,
            tier_result=tier_result,
        )

        # Step 6: Create output
        return ScoringOutput(
            practice_id=scoring_input.practice_id,
            lead_score=confidence_result.final_score,
            priority_tier=tier_result.tier,
            score_breakdown=breakdown_json,
            confidence_flags=confidence_result.confidence_flags,
            scoring_status="Scored",
            scoring_timestamp=datetime.now(),
            scoring_duration_ms=0,  # Updated by caller
            error_type=None,
            error_message=None,
        )

    def _create_error_output(
        self,
        practice_id: str,
        error_type: str,
        error_message: str,
        duration_ms: int,
    ) -> ScoringOutput:
        """Create ScoringOutput for error cases"""
        error_breakdown = self.breakdown_generator.generate_error(
            error_type=error_type,
            error_message=error_message,
        )

        return ScoringOutput(
            practice_id=practice_id,
            lead_score=None,
            priority_tier=None,
            score_breakdown=error_breakdown,
            confidence_flags=[],
            scoring_status="Failed",
            scoring_timestamp=datetime.now(),
            scoring_duration_ms=duration_ms,
            error_type=error_type,
            error_message=error_message,
        )
```

```python
# src/scoring/calculator.py

from typing import Optional
from dataclasses import dataclass

from .models import VeterinaryPractice, VetPracticeExtraction
from .validator import ValidationResult
from ..config import ScoringConfig


@dataclass
class ComponentScores:
    """Individual component scores with details"""
    practice_size: int  # 0-30 pts
    practice_size_detail: str

    call_volume: int  # 0-30 pts
    call_volume_detail: str

    technology: int  # 0-30 pts
    technology_detail: str

    baseline: int  # 0-20 pts
    baseline_detail: str

    decision_maker: int  # 0-10 pts
    decision_maker_detail: str

    total: int  # Sum of all components


class ScoreCalculator:
    """
    Calculate weighted scores from practice data.

    Responsibilities:
    - Calculate 5 component scores
    - Handle missing/partial data gracefully
    - Apply sweet spot bonuses for practice size
    - Baseline-only mode for practices without enrichment
    """

    def __init__(self, config: ScoringConfig):
        self.config = config

    def calculate_components(
        self,
        google_maps_data: VeterinaryPractice,
        enrichment_data: Optional[VetPracticeExtraction],
        validation_result: ValidationResult,
    ) -> ComponentScores:
        """
        Calculate all component scores.

        Args:
            google_maps_data: Google Maps metrics (always present)
            enrichment_data: Enrichment data (may be None)
            validation_result: Data validation results

        Returns:
            ComponentScores with all components and details

        Raises:
            ValueError: If data is invalid (negative values, etc.)
        """
        if enrichment_data is None:
            # Baseline-only mode
            return self._calculate_baseline_only(google_maps_data)

        # Component 1: Practice Size (0-30 pts)
        practice_size_score, practice_size_detail = self._calculate_practice_size(
            enrichment_data.vet_count
        )

        # Component 2: Call Volume (0-30 pts)
        call_volume_score, call_volume_detail = self._calculate_call_volume(
            len(enrichment_data.phone_numbers)
        )

        # Component 3: Technology Stack (0-30 pts)
        technology_score, technology_detail = self._calculate_technology(
            emr_system=enrichment_data.emr_system,
            has_online_booking=enrichment_data.has_online_booking,
            has_telemedicine=enrichment_data.has_telemedicine,
            technologies=enrichment_data.technologies,
        )

        # Component 4: Baseline Metrics (0-20 pts)
        baseline_score, baseline_detail = self._calculate_baseline(
            google_maps_data
        )

        # Component 5: Decision Maker (0-10 pts)
        decision_maker_score, decision_maker_detail = self._calculate_decision_maker(
            enrichment_data.decision_maker
        )

        total = (
            practice_size_score +
            call_volume_score +
            technology_score +
            baseline_score +
            decision_maker_score
        )

        return ComponentScores(
            practice_size=practice_size_score,
            practice_size_detail=practice_size_detail,
            call_volume=call_volume_score,
            call_volume_detail=call_volume_detail,
            technology=technology_score,
            technology_detail=technology_detail,
            baseline=baseline_score,
            baseline_detail=baseline_detail,
            decision_maker=decision_maker_score,
            decision_maker_detail=decision_maker_detail,
            total=total,
        )

    def _calculate_practice_size(
        self,
        vet_count: Optional[int]
    ) -> tuple[int, str]:
        """
        Calculate practice size score with sweet spot bonus.

        Scoring:
        - 0 vets: 0 pts (data missing)
        - 1-2 vets: 5 pts (too small)
        - 3-4 vets: 15 pts (good size)
        - 5-7 vets: 30 pts (sweet spot!)
        - 8-10 vets: 20 pts (larger)
        - 11+ vets: 10 pts (too large, complex)
        """
        if vet_count is None or vet_count <= 0:
            return 0, "Vet count not available"

        if vet_count <= 2:
            return 5, f"{vet_count} vets (small practice)"
        elif vet_count <= 4:
            return 15, f"{vet_count} vets (good size)"
        elif vet_count <= 7:
            return 30, f"{vet_count} vets (sweet spot!)"
        elif vet_count <= 10:
            return 20, f"{vet_count} vets (larger practice)"
        else:
            return 10, f"{vet_count} vets (large practice)"

    def _calculate_call_volume(
        self,
        phone_count: int
    ) -> tuple[int, str]:
        """
        Calculate call volume score.

        Scoring:
        - 0 phones: 0 pts
        - 1 phone: 10 pts
        - 2 phones: 20 pts
        - 3+ phones: 30 pts
        """
        if phone_count == 0:
            return 0, "No phone numbers found"
        elif phone_count == 1:
            return 10, "1 phone number"
        elif phone_count == 2:
            return 20, "2 phone numbers"
        else:
            return 30, f"{phone_count} phone numbers (high volume)"

    def _calculate_technology(
        self,
        emr_system: Optional[str],
        has_online_booking: bool,
        has_telemedicine: bool,
        technologies: list[str],
    ) -> tuple[int, str]:
        """
        Calculate technology stack score.

        Scoring:
        - Top EMRs (Cornerstone, IDEXX): 15 pts
        - Mid EMRs (Avimark, eVetPractice): 10 pts
        - Other EMR: 5 pts
        - No EMR: 0 pts
        - Online booking: +10 pts
        - Telemedicine: +5 pts
        - Max: 30 pts
        """
        score = 0
        details = []

        # EMR scoring
        if emr_system:
            emr_upper = emr_system.upper()
            if any(top in emr_upper for top in ["CORNERSTONE", "IDEXX"]):
                score += 15
                details.append(f"{emr_system} EMR (top tier)")
            elif any(mid in emr_upper for mid in ["AVIMARK", "EVETPRACTICE"]):
                score += 10
                details.append(f"{emr_system} EMR (mid tier)")
            else:
                score += 5
                details.append(f"{emr_system} EMR")

        # Online booking
        if has_online_booking:
            score += 10
            details.append("Online booking")

        # Telemedicine
        if has_telemedicine:
            score += 5
            details.append("Telemedicine")

        # Cap at 30
        score = min(score, 30)

        detail_str = ", ".join(details) if details else "No technology data"
        return score, detail_str

    def _calculate_baseline(
        self,
        google_maps_data: VeterinaryPractice
    ) -> tuple[int, str]:
        """
        Calculate baseline metrics score from Google Maps data.

        Scoring:
        - Reviews: 0-20 pts (linear: 1pt per 10 reviews, max 200 reviews)
        - Rating: 0-6 pts (4.0=2pts, 4.5=4pts, 5.0=6pts)
        - Has website: +4 pts
        - Multiple locations: +10 pts
        - Max: 40 pts
        """
        score = 0
        details = []

        # Reviews scoring
        reviews = google_maps_data.reviews_count or 0
        reviews_pts = min(int(reviews / 10), 20)
        score += reviews_pts
        details.append(f"{reviews} reviews ({reviews_pts} pts)")

        # Rating scoring
        rating = google_maps_data.rating or 0.0
        if rating >= 5.0:
            rating_pts = 6
        elif rating >= 4.5:
            rating_pts = 4
        elif rating >= 4.0:
            rating_pts = 2
        else:
            rating_pts = 0
        score += rating_pts
        details.append(f"{rating:.1f}★ ({rating_pts} pts)")

        # Website
        if google_maps_data.website:
            score += 4
            details.append("Has website (+4)")

        # Multiple locations
        if google_maps_data.has_multiple_locations:
            score += 10
            details.append("Multiple locations (+10)")

        detail_str = ", ".join(details)
        return score, detail_str

    def _calculate_decision_maker(
        self,
        decision_maker: Optional[dict]
    ) -> tuple[int, str]:
        """
        Calculate decision maker score.

        Scoring:
        - Decision maker found: 10 pts
        - Not found: 0 pts
        """
        if decision_maker and decision_maker.get("name"):
            name = decision_maker["name"]
            title = decision_maker.get("title", "Unknown")
            return 10, f"{name} ({title})"
        else:
            return 0, "Decision maker not found"

    def _calculate_baseline_only(
        self,
        google_maps_data: VeterinaryPractice
    ) -> ComponentScores:
        """
        Calculate baseline-only score when no enrichment data.

        Returns:
            ComponentScores with only baseline component populated
        """
        baseline_score, baseline_detail = self._calculate_baseline(
            google_maps_data
        )

        return ComponentScores(
            practice_size=0,
            practice_size_detail="Awaiting enrichment",
            call_volume=0,
            call_volume_detail="Awaiting enrichment",
            technology=0,
            technology_detail="Awaiting enrichment",
            baseline=baseline_score,
            baseline_detail=baseline_detail,
            decision_maker=0,
            decision_maker_detail="Awaiting enrichment",
            total=baseline_score,
        )
```

### Supporting Classes

```python
# src/scoring/confidence.py

from dataclasses import dataclass
from typing import Optional, List, Literal

from .calculator import ComponentScores
from ..config import ScoringConfig


@dataclass
class ConfidenceResult:
    """Result of confidence evaluation"""
    original_score: int
    confidence_multiplier: float
    final_score: int
    confidence_flags: List[str]


class ConfidenceEvaluator:
    """
    Evaluate data confidence and apply penalties.

    Responsibilities:
    - Assess overall enrichment confidence
    - Apply multiplicative penalties for low confidence
    - Generate confidence flags for UI display
    """

    def __init__(self, config: ScoringConfig):
        self.config = config

    def evaluate(
        self,
        component_scores: ComponentScores,
        enrichment_confidence: Optional[Literal["high", "medium", "low"]],
    ) -> ConfidenceResult:
        """
        Evaluate confidence and apply penalty.

        Confidence Multipliers:
        - high: 1.0x (no penalty)
        - medium: 0.9x (10% penalty)
        - low: 0.8x (20% penalty)
        - None: 1.0x (baseline-only, no penalty)
        """
        confidence_flags = []

        if enrichment_confidence is None:
            # Baseline-only scoring, no penalty
            return ConfidenceResult(
                original_score=component_scores.total,
                confidence_multiplier=1.0,
                final_score=component_scores.total,
                confidence_flags=[],
            )

        # Determine multiplier
        if enrichment_confidence == "high":
            multiplier = 1.0
        elif enrichment_confidence == "medium":
            multiplier = 0.9
            confidence_flags.append("Medium Confidence Data")
        elif enrichment_confidence == "low":
            multiplier = 0.8
            confidence_flags.append("Low Confidence Vet Count")
        else:
            multiplier = 1.0

        # Apply penalty
        final_score = int(component_scores.total * multiplier)

        return ConfidenceResult(
            original_score=component_scores.total,
            confidence_multiplier=multiplier,
            final_score=final_score,
            confidence_flags=confidence_flags,
        )
```

```python
# src/scoring/classifier.py

from dataclasses import dataclass
from typing import List

from ..config import ScoringConfig


@dataclass
class TierResult:
    """Result of tier classification"""
    tier: str
    confidence_flags: List[str]


class TierClassifier:
    """
    Classify practices into priority tiers.

    Responsibilities:
    - Assign tier based on final score
    - Handle "Pending Enrichment" special tier
    - Attach confidence flags
    """

    def __init__(self, config: ScoringConfig):
        self.config = config

    def classify(
        self,
        final_score: int,
        confidence_flags: List[str],
        has_enrichment: bool,
    ) -> TierResult:
        """
        Classify practice into priority tier.

        Tier Ranges:
        - Hot: 80-120 pts
        - Warm: 50-79 pts
        - Cold: 0-49 pts
        - Pending Enrichment: No enrichment data (special case)
        """
        if not has_enrichment:
            return TierResult(
                tier="Pending Enrichment",
                confidence_flags=[],
            )

        if final_score >= 80:
            tier = "Hot"
        elif final_score >= 50:
            tier = "Warm"
        else:
            tier = "Cold"

        return TierResult(
            tier=tier,
            confidence_flags=confidence_flags,
        )
```

## 6. Configuration

```python
# src/config.py

from dataclasses import dataclass
from typing import Literal


@dataclass
class ScoringConfig:
    """Configuration for FEAT-003 lead scoring"""

    # Auto-trigger settings
    auto_trigger_scoring: bool = True  # Auto-score after FEAT-002 enrichment
    auto_trigger_on_partial: bool = True  # Score even with partial enrichment

    # Timeout settings
    scoring_timeout_seconds: float = 5.0  # Hard timeout per practice
    target_scoring_time_ms: int = 100  # Performance target

    # Circuit breaker settings
    circuit_breaker_fail_max: int = 5  # Open after 5 consecutive failures
    circuit_breaker_reset_timeout: int = 60  # Reset after 60 seconds

    # Confidence penalty weights
    confidence_multipliers: dict[str, float] = None  # Set in __post_init__

    # Sweet spot thresholds
    practice_size_sweet_spot_min: int = 5  # Min vets for sweet spot
    practice_size_sweet_spot_max: int = 7  # Max vets for sweet spot

    # Tier thresholds
    hot_tier_min: int = 80
    warm_tier_min: int = 50

    # Notion integration
    notion_api_key: str = ""  # Set from environment
    notion_database_id: str = ""  # Set from environment
    notion_retry_max: int = 3
    notion_retry_backoff: list[int] = None  # [1, 2, 4] seconds

    def __post_init__(self):
        if self.confidence_multipliers is None:
            self.confidence_multipliers = {
                "high": 1.0,
                "medium": 0.9,
                "low": 0.8,
            }

        if self.notion_retry_backoff is None:
            self.notion_retry_backoff = [1, 2, 4]

    @classmethod
    def from_env(cls) -> "ScoringConfig":
        """Load configuration from environment variables"""
        import os

        return cls(
            auto_trigger_scoring=os.getenv("AUTO_TRIGGER_SCORING", "true").lower() == "true",
            scoring_timeout_seconds=float(os.getenv("SCORING_TIMEOUT_SECONDS", "5.0")),
            circuit_breaker_fail_max=int(os.getenv("CIRCUIT_BREAKER_FAIL_MAX", "5")),
            notion_api_key=os.getenv("NOTION_API_KEY", ""),
            notion_database_id=os.getenv("NOTION_DATABASE_ID", ""),
        )

    def validate(self) -> None:
        """Validate configuration at startup"""
        assert self.scoring_timeout_seconds > 0, "Timeout must be positive"
        assert self.circuit_breaker_fail_max > 0, "Circuit breaker fail_max must be positive"
        assert self.notion_api_key, "NOTION_API_KEY environment variable required"
        assert self.notion_database_id, "NOTION_DATABASE_ID environment variable required"
        assert 0 < self.confidence_multipliers["medium"] <= 1.0
        assert 0 < self.confidence_multipliers["low"] <= 1.0
```

## 7. Error Handling Strategy

### Error Categories

**1. Data Validation Errors**

```python
# Detection
class DataValidationError(Exception):
    """Raised when enrichment data is invalid"""
    pass

# Example scenarios
- Missing required fields (vet_count, phone_numbers)
- Invalid data types (vet_count = "five")
- Out-of-range values (vet_count = -1)
- Malformed decision_maker dict

# Recovery action
- Log validation error with field details
- Return ComponentScores with 0 for invalid components
- Continue scoring with valid components only
- Add "Data Validation Error" to confidence_flags

# Logging format
logger.error(
    "Data validation error",
    extra={
        "practice_id": practice_id,
        "error": "Invalid vet_count",
        "value": vet_count,
        "expected": "int >= 0",
    }
)
```

**2. Calculation Errors**

```python
# Detection
- Division by zero
- Type errors (None + int)
- Index out of range
- KeyError on dict access

# Recovery action
- Catch exception in ScoringOrchestrator
- Log full traceback
- Create error ScoringOutput
- Update Notion with error details
- Don't propagate to FEAT-002

# Logging format
logger.exception(
    "Calculation error during scoring",
    extra={
        "practice_id": practice_id,
        "component": "practice_size",
        "vet_count": vet_count,
    }
)
```

**3. Timeout Errors**

```python
# Detection
asyncio.TimeoutError from asyncio.wait_for()

# Recovery action
- Log timeout with elapsed time
- Record in circuit breaker (but don't count as failure)
- Create timeout error ScoringOutput
- Update Notion with timeout message
- Suggest manual rescore

# Logging format
logger.error(
    "Scoring timeout",
    extra={
        "practice_id": practice_id,
        "timeout_ms": 5000,
        "elapsed_ms": actual_elapsed_ms,
    }
)
```

**4. Notion API Errors**

```python
# Detection
- HTTP 429 (rate limit)
- HTTP 500 (server error)
- Network errors
- Authentication errors

# Recovery action
- Retry up to 3 times with exponential backoff
- Log each retry attempt
- If all retries fail, log error and continue
- Don't block scoring workflow
- Return NotionUpdateResult with success=False

# Logging format
logger.warning(
    "Notion API error, retrying",
    extra={
        "practice_id": practice_id,
        "status_code": 429,
        "retry_attempt": 2,
        "backoff_seconds": 2,
    }
)
```

**5. Circuit Breaker Open**

```python
# Detection
CircuitBreakerError from pybreaker

# Recovery action
- Log circuit breaker state
- Create circuit breaker error ScoringOutput
- Update Notion with retry_after message
- Auto-retry after reset_timeout (60s)
- Monitor circuit breaker state in metrics

# Logging format
logger.warning(
    "Circuit breaker OPEN",
    extra={
        "practice_id": practice_id,
        "state": "OPEN",
        "fail_count": 5,
        "reset_in_seconds": 60,
    }
)
```

### Error Propagation Rules

```
NEVER propagate exceptions to FEAT-002:
  ✅ Catch ALL exceptions in ScoringOrchestrator
  ✅ Return ScoringOutput with scoring_status="Failed"
  ✅ Log errors with full context
  ✅ Update Notion with error details

ALWAYS preserve FEAT-002 state:
  ✅ Don't modify enrichment_status field
  ✅ Don't modify enrichment_data fields
  ✅ Only update scoring fields

ALWAYS maintain observability:
  ✅ Log every error with practice_id
  ✅ Include error type and message
  ✅ Add structured extra fields for querying
  ✅ Write error details to Notion
```

## 8. Performance Considerations

### Performance Targets

**Per-Practice Timing:**
- **Target:** <100ms typical case (full enrichment, no errors)
- **Timeout:** 5000ms hard limit (enforced by asyncio.wait_for)
- **Baseline-only:** <10ms (no enrichment, simple calculation)

**Batch Timing:**
- **Target:** 150 practices in <15 seconds
- **Average:** 100ms per practice
- **Parallelization:** Process up to 10 practices concurrently

### Performance Optimizations

**1. Fast-Path for Baseline-Only**
```python
# Skip expensive operations when no enrichment
if enrichment_data is None:
    return self._calculate_baseline_only(google_maps_data)  # <10ms
```

**2. Circuit Breaker Prevents Resource Exhaustion**
```python
# Stop attempting scoring after repeated failures
# Prevents wasting resources on broken external dependencies
# Auto-recovers after 60 seconds
```

**3. Async I/O for Notion Updates**
```python
# Don't block scoring workflow on Notion API
async def update_scoring_fields(...):
    # Non-blocking HTTP requests
    # Concurrent updates for batch scoring
```

**4. Minimal Logging in Hot Path**
```python
# Only log on entry, exit, and errors
# Use structured logging with extra fields
# Avoid expensive string formatting
```

### Performance Monitoring

**Metrics to Track:**
- `scoring_duration_ms` (p50, p95, p99)
- `timeout_rate` (% of practices hitting 5s limit)
- `circuit_breaker_state` (CLOSED/OPEN/HALF_OPEN)
- `failure_rate` (% of practices with scoring_status="Failed")
- `batch_throughput` (practices per second)

**Alerting Thresholds:**
- p95 scoring time > 500ms (investigate slow practices)
- Timeout rate > 5% (investigate timeout causes)
- Circuit breaker OPEN for >5 minutes (investigate cascading failures)
- Failure rate > 10% (investigate data quality issues)

## 9. Deployment Considerations

### Dependencies

```toml
# pyproject.toml

[tool.poetry.dependencies]
pybreaker = "^1.3.0"  # Circuit breaker pattern
notion-client = "^2.2.1"  # Notion API
pydantic = "^2.5.0"  # Data validation
structlog = "^24.1.0"  # Structured logging
```

### Configuration Validation

```python
# src/main.py

def startup():
    """Validate configuration at application startup"""
    config = ScoringConfig.from_env()

    try:
        config.validate()
    except AssertionError as e:
        logger.error(f"Configuration validation failed: {e}")
        sys.exit(1)

    logger.info(
        "Scoring configuration loaded",
        extra={
            "auto_trigger": config.auto_trigger_scoring,
            "timeout_seconds": config.scoring_timeout_seconds,
            "circuit_breaker_fail_max": config.circuit_breaker_fail_max,
        }
    )
```

### Monitoring & Observability

**Required Monitoring:**
1. **Timeout Rate Dashboard**
   - Track % of practices hitting 5s timeout
   - Alert if >5% for 10 minutes
   - Investigate slow Notion API or calculation logic

2. **Failure Rate Dashboard**
   - Track % of practices with scoring_status="Failed"
   - Break down by error_type
   - Alert if >10% for 10 minutes

3. **Circuit Breaker State**
   - Current state (CLOSED/OPEN/HALF_OPEN)
   - State transitions over time
   - Alert on OPEN state

4. **Performance Metrics**
   - p50, p95, p99 scoring duration
   - Batch throughput (practices/second)
   - Notion API latency

**Logging Strategy:**
```python
# Use structured logging for queryability
logger.info(
    "Scoring completed",
    extra={
        "practice_id": practice_id,
        "lead_score": lead_score,
        "priority_tier": priority_tier,
        "duration_ms": duration_ms,
        "enrichment_status": enrichment_status,
        "enrichment_confidence": enrichment_confidence,
    }
)

# Query examples (assuming JSON logs)
# - Find all timeouts: error_type="timeout"
# - Find low-confidence scores: enrichment_confidence="low"
# - Find slow practices: duration_ms > 1000
```

### Rollback Strategy

**If Auto-Trigger Causes Issues:**

```python
# Emergency rollback via environment variable
AUTO_TRIGGER_SCORING=false

# Disable auto-trigger without code deployment
# Manually trigger scoring for specific practices
# Investigate root cause while system continues

# Re-enable after fix verified
AUTO_TRIGGER_SCORING=true
```

**Manual Rescore Command:**
```python
# CLI tool for manual rescore
python -m src.scoring.cli rescore --practice-id <NOTION_PAGE_ID>
python -m src.scoring.cli rescore --batch --tier "Pending Enrichment"
```

## 10. Trade-offs & Alternatives

### Chosen Architecture vs Alternatives

**1. Circuit Breaker vs Simple Retry**

**Chosen:** pybreaker circuit breaker with fail_max=5, reset_timeout=60s

**Alternative:** Simple retry with exponential backoff

**Rationale:**
- Circuit breaker prevents cascading failures
- Protects system resources during outages
- Auto-recovers without manual intervention
- Provides state visibility (CLOSED/OPEN/HALF_OPEN)

**Trade-offs:**
- Additional dependency (pybreaker)
- More complex state management
- Requires monitoring of circuit state

---

**2. Multiplicative Confidence Penalties vs Additive**

**Chosen:** Multiplicative (high=1.0x, medium=0.9x, low=0.8x)

**Alternative:** Additive (high=+0, medium=-5pts, low=-10pts)

**Rationale:**
- Multiplicative scales with score magnitude
- Higher scores penalized more for low confidence (fair)
- Lower scores less impacted (compassionate)
- Aligns with statistical confidence intervals

**Trade-offs:**
- More complex to explain to users
- Can't predict exact penalty without knowing base score
- But more statistically sound

---

**3. Notion Status Field vs State Machine Library**

**Chosen:** Simple Notion select field "Scoring Status" with 3 states

**Alternative:** Full state machine library (pytransitions, etc.)

**Rationale:**
- Simple states: "Not Scored" → "Scored" / "Failed"
- No complex transitions needed
- Easy to understand in Notion UI
- Avoids over-engineering

**Trade-offs:**
- Less formal state validation
- No transition history tracking
- But sufficient for FEAT-003 requirements

---

**4. Manual Rescore vs Automatic Retry Queue**

**Chosen:** Manual rescore command for failed practices

**Alternative:** Automatic retry queue with exponential backoff

**Rationale:**
- Manual rescore gives control to users
- Avoids retry storms on system-wide issues
- Circuit breaker handles transient failures
- Permanent failures (bad data) need human review

**Trade-offs:**
- Requires manual intervention for failed practices
- But provides better observability and control

---

### Future Enhancements

**Phase 2 Improvements (Post-MVP):**
1. **ML-Based Scoring:** Train model on conversion data for dynamic weights
2. **Real-Time Enrichment:** Trigger enrichment on-demand during scoring
3. **Batch Optimization:** Parallel scoring with rate limiting
4. **Score Decay:** Reduce lead_score over time if no activity
5. **A/B Testing:** Compare scoring algorithms on subset of practices

---

## Summary

FEAT-003 implements a resilient, performance-optimized lead scoring system with comprehensive error boundaries, graceful degradation, and robust integration with FEAT-002 enrichment. The architecture prioritizes system reliability through circuit breaker patterns, timeout enforcement, and complete error isolation while maintaining observability through structured logging and Notion status tracking.

**Key Design Decisions:**
- Circuit breaker prevents cascading failures
- Multiplicative confidence penalties scale fairly
- Baseline-only mode handles missing enrichment gracefully
- 5-second timeout enforced per practice
- All errors isolated from FEAT-002 workflow
- Simple state machine in Notion for observability

**Ready for Implementation:** This architecture provides complete specifications for all components, error handling, integration contracts, and performance requirements.

