"""
Data models for FEAT-003 Lead Scoring.

This module defines Pydantic models for scoring inputs, outputs, and breakdowns.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class PriorityTier(str, Enum):
    """Priority tier classifications for leads."""
    HOT = "🔥 Hot"
    WARM = "🌡️ Warm"
    COLD = "❄️ Cold"
    OUT_OF_SCOPE = "⛔ Out of Scope"
    PENDING_ENRICHMENT = "⏳ Pending Enrichment"


class PracticeSizeCategory(str, Enum):
    """Practice size classifications based on vet count."""
    SOLO = "Solo"  # 1 vet
    SMALL = "Small"  # 2 vets
    SWEET_SPOT = "Sweet Spot"  # 3-8 vets (TARGET ICP)
    LARGE = "Large"  # 9-19 vets
    CORPORATE = "Corporate"  # 20+ vets


class ConfidenceLevel(str, Enum):
    """Confidence levels for enrichment data."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ScoreComponent(BaseModel):
    """Individual scoring component with breakdown."""
    score: int = Field(..., ge=0, description="Points earned for this component")
    max_possible: int = Field(..., gt=0, description="Maximum possible points for this component")
    detail: str = Field(..., description="Human-readable explanation of how score was calculated")
    contributing_factors: List[str] = Field(default_factory=list, description="List of factors that contributed points")
    missing_factors: List[str] = Field(default_factory=list, description="List of factors that could have contributed but were missing")


class ScoreBreakdown(BaseModel):
    """Complete breakdown of all scoring components."""
    practice_size: ScoreComponent
    call_volume: ScoreComponent
    technology: ScoreComponent
    baseline: ScoreComponent
    decision_maker: ScoreComponent

    total_before_confidence: int = Field(..., ge=0, le=130, description="Total score before confidence penalty")
    confidence_multiplier: float = Field(..., ge=0.0, le=1.0, description="Confidence penalty multiplier (1.0, 0.9, or 0.7)")
    total_after_confidence: int = Field(..., ge=0, le=120, description="Final score after confidence penalty applied")

    confidence_level: Optional[ConfidenceLevel] = Field(None, description="Overall confidence of enrichment data")
    confidence_flags: List[str] = Field(default_factory=list, description="Warnings about low-confidence data")


class ScoringInput(BaseModel):
    """Input data for scoring calculation."""
    practice_id: str = Field(..., description="Notion page ID of the practice")

    # Google Maps baseline data (from FEAT-001)
    google_rating: Optional[float] = Field(None, ge=0.0, le=5.0, description="Google Maps rating")
    google_review_count: Optional[int] = Field(None, ge=0, description="Number of Google reviews")
    website: Optional[str] = Field(None, description="Practice website URL")
    has_multiple_locations: Optional[bool] = Field(False, description="Whether practice has multiple locations")

    # Enrichment data (from FEAT-002)
    vet_count_total: Optional[int] = Field(None, ge=0, le=50, description="Total number of veterinarians")
    vet_count_confidence: Optional[ConfidenceLevel] = Field(None, description="Confidence level of vet count")

    emergency_24_7: bool = Field(False, description="Has 24/7 emergency services")
    online_booking: bool = Field(False, description="Has online booking system")
    patient_portal: bool = Field(False, description="Has patient portal")
    telemedicine_virtual_care: bool = Field(False, description="Offers telemedicine/virtual care")

    specialty_services: List[str] = Field(default_factory=list, description="List of specialty services offered")

    decision_maker_name: Optional[str] = Field(None, description="Name of identified decision maker")
    decision_maker_email: Optional[str] = Field(None, description="Email of decision maker")

    enrichment_status: Optional[str] = Field(None, description="Enrichment status from FEAT-002")

    @validator('vet_count_total')
    def validate_vet_count(cls, v):
        """Ensure vet count is in reasonable range."""
        if v is not None and (v < 0 or v > 50):
            raise ValueError("vet_count_total must be between 0 and 50")
        return v

    @validator('google_rating')
    def validate_rating(cls, v):
        """Ensure rating is in valid range."""
        if v is not None and (v < 0.0 or v > 5.0):
            raise ValueError("google_rating must be between 0.0 and 5.0")
        return v


class ScoringResult(BaseModel):
    """Complete scoring result with all metadata."""
    practice_id: str = Field(..., description="Notion page ID of the practice")

    lead_score: int = Field(..., ge=0, le=120, description="Final ICP fit score (0-120)")
    priority_tier: PriorityTier = Field(..., description="Priority classification")
    practice_size_category: Optional[PracticeSizeCategory] = Field(None, description="Size classification")

    score_breakdown: ScoreBreakdown = Field(..., description="Detailed breakdown of scoring")

    confidence_flags: List[str] = Field(default_factory=list, description="Warnings about data quality")
    scoring_status: str = Field(default="Scored", description="Scoring status (Scored/Failed)")

    notes: Optional[str] = Field(None, description="Additional notes about scoring")

    def to_notion_update(self) -> Dict[str, Any]:
        """
        Convert scoring result to Notion API update format.

        Returns:
            Dict compatible with Notion API properties update
        """
        import json
        return {
            "Lead Score": {"number": self.lead_score},
            "Priority Tier": {"select": {"name": self.priority_tier.value}},
            "Score Breakdown": {
                "rich_text": [{
                    "text": {"content": json.dumps(self.score_breakdown.model_dump(), indent=2)}
                }]
            },
            "Confidence Flags": {
                "multi_select": [{"name": flag} for flag in self.confidence_flags]
            },
            "Scoring Status": {"select": {"name": self.scoring_status}}
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/debugging."""
        return {
            "practice_id": self.practice_id,
            "lead_score": self.lead_score,
            "priority_tier": self.priority_tier.value,
            "practice_size_category": self.practice_size_category.value if self.practice_size_category else None,
            "confidence_flags": self.confidence_flags,
            "scoring_status": self.scoring_status,
            "breakdown": {
                "practice_size": self.score_breakdown.practice_size.score,
                "call_volume": self.score_breakdown.call_volume.score,
                "technology": self.score_breakdown.technology.score,
                "baseline": self.score_breakdown.baseline.score,
                "decision_maker": self.score_breakdown.decision_maker.score,
                "total_before_confidence": self.score_breakdown.total_before_confidence,
                "confidence_multiplier": self.score_breakdown.confidence_multiplier,
                "total_after_confidence": self.score_breakdown.total_after_confidence
            }
        }


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open and prevents scoring attempts."""
    pass


class ScoringTimeoutError(Exception):
    """Raised when a single practice scoring exceeds timeout limit."""
    pass


class ScoringValidationError(Exception):
    """Raised when input data fails validation."""
    pass
