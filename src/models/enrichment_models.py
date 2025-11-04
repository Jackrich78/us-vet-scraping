"""
Data models for website enrichment and LLM extraction.

These models define the structure for OpenAI structured outputs and Notion database
updates. All models are Pydantic v2 with validation constraints.

Usage:
    from src.models.enrichment_models import VetPracticeExtraction

    extraction = VetPracticeExtraction(
        vet_count_total=3,
        vet_count_confidence="high",
        decision_maker=DecisionMaker(
            name="Dr. Sarah Johnson",
            role="Owner",
            email="sjohnson@example.com"
        )
    )
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class DecisionMaker(BaseModel):
    """Decision maker contact information extracted from website.

    Attributes:
        name: Full name of decision maker (practice owner, medical director, etc.)
        role: Job title or role (e.g., "Owner", "Medical Director", "Practice Manager")
        email: Explicit email address (NEVER guessed - must be stated on website)
        phone: Direct phone number (optional, usually practice main line)
    """
    name: Optional[str] = Field(None, max_length=100)
    role: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)

    @field_validator('email')
    @classmethod
    def validate_email_explicit(cls, v: Optional[str]) -> Optional[str]:
        """Ensure email is only set if explicitly found (no guessing)."""
        if v and '@' not in v:
            return None  # Invalid email format - discard
        return v


class VetPracticeExtraction(BaseModel):
    """Structured data extracted from veterinary practice website.

    This model is used with OpenAI structured outputs (beta.chat.completions.parse)
    to guarantee 100% valid JSON responses with no parsing errors.

    All fields follow these principles:
    - Only include information explicitly stated on website
    - Never guess or infer information
    - Use confidence levels for uncertain extractions
    - Preserve null values when data not found

    Attributes:
        vet_count_total: Number of veterinarians at practice (1-50)
        vet_count_confidence: Confidence level for vet count ("high", "medium", "low")
        decision_maker: Owner, medical director, or practice manager contact info
        emergency_24_7: True if practice offers 24/7 emergency services
        online_booking: True if practice has online appointment booking
        patient_portal: True if practice has online patient portal
        telemedicine_virtual_care: True if practice offers virtual consultations
        specialty_services: List of specialty services (e.g., "surgery", "dentistry")
        personalization_context: 1-3 specific facts for personalized outreach
        awards_accreditations: List of awards or certifications (e.g., "AAHA Accredited")
        recent_news_updates: Recent practice news (e.g., new location, new services)
        community_involvement: Community events or charitable work mentioned
        practice_philosophy: Stated mission, values, or philosophy
    """

    # Vet count with confidence
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

    # Decision maker
    decision_maker: Optional[DecisionMaker] = Field(
        None,
        description="Practice owner, medical director, or manager with contact info"
    )

    # Technology indicators
    emergency_24_7: bool = Field(
        False,
        description="True if practice offers 24/7 emergency services"
    )
    online_booking: bool = Field(
        False,
        description="True if practice has online appointment scheduling"
    )
    patient_portal: bool = Field(
        False,
        description="True if practice has online patient portal"
    )
    telemedicine_virtual_care: bool = Field(
        False,
        description="True if practice offers telemedicine or virtual consultations"
    )

    # Services and specialties
    specialty_services: List[str] = Field(
        default_factory=list,
        max_length=10,
        description="List of specialty services (surgery, dentistry, oncology, etc.)"
    )

    # Personalization data (for outreach)
    personalization_context: List[str] = Field(
        default_factory=list,
        min_length=0,
        max_length=3,
        description="1-3 specific facts for personalized outreach (e.g., 'Opened 2nd location in Newton Oct 2024')"
    )
    awards_accreditations: List[str] = Field(
        default_factory=list,
        max_length=5,
        description="Awards or certifications (e.g., 'AAHA Accredited', 'Fear Free Certified')"
    )
    recent_news_updates: List[str] = Field(
        default_factory=list,
        max_length=3,
        description="Recent practice news or updates from last 12 months"
    )
    community_involvement: List[str] = Field(
        default_factory=list,
        max_length=3,
        description="Community events, charity work, or local partnerships"
    )
    practice_philosophy: Optional[str] = Field(
        None,
        max_length=500,
        description="Mission statement, values, or practice philosophy"
    )

    @field_validator('personalization_context', 'awards_accreditations', 'recent_news_updates', 'community_involvement')
    @classmethod
    def validate_list_items_not_empty(cls, v: List[str]) -> List[str]:
        """Remove empty strings from lists."""
        return [item.strip() for item in v if item and item.strip()]

    @field_validator('vet_count_total')
    @classmethod
    def validate_vet_count_range(cls, v: Optional[int]) -> Optional[int]:
        """Ensure vet count is realistic (1-50)."""
        if v is not None and (v < 1 or v > 50):
            return None  # Invalid count - discard
        return v


class WebsiteData(BaseModel):
    """Raw website data from multi-page scraping.

    Used internally by WebsiteScraper to store scraped pages before LLM extraction.

    Attributes:
        url: Page URL
        title: Page title
        content: Extracted text content (cleaned)
        scraped_at: Timestamp when page was scraped
    """
    url: str
    title: Optional[str] = None
    content: str
    scraped_at: datetime = Field(default_factory=lambda: datetime.now())

    @field_validator('content')
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        """Ensure content is not empty."""
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        return v.strip()


class EnrichmentResult(BaseModel):
    """Result of enriching a single practice.

    Used by EnrichmentOrchestrator to track success/failure for each practice.

    Attributes:
        practice_id: Notion database record ID
        practice_name: Practice name (for logging)
        status: "success", "scrape_failed", "llm_failed", "notion_failed"
        extraction: Extracted data (if successful)
        error_message: Error description (if failed)
        pages_scraped: Number of pages successfully scraped
        cost_incurred: OpenAI API cost for this practice (in USD)
        processing_time: Time taken to process this practice (in seconds)
    """
    practice_id: str
    practice_name: str
    status: str = Field(pattern="^(success|scrape_failed|llm_failed|notion_failed)$")
    extraction: Optional[VetPracticeExtraction] = None
    error_message: Optional[str] = None
    pages_scraped: int = Field(0, ge=0)
    cost_incurred: float = Field(0.0, ge=0.0)
    processing_time: float = Field(0.0, ge=0.0)

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Ensure status is valid."""
        valid_statuses = {"success", "scrape_failed", "llm_failed", "notion_failed"}
        if v not in valid_statuses:
            raise ValueError(f"Invalid status: {v}. Must be one of {valid_statuses}")
        return v
