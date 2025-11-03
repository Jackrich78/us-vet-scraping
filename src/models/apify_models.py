"""
Pydantic models for Apify Google Maps scraping results (FEAT-001).

Models handle data validation, sanitization, and normalization:
- ApifyGoogleMapsResult: Raw Apify API response
- VeterinaryPractice: Filtered and scored practice data for Notion
"""

import re
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, HttpUrl
import phonenumbers


class ApifyGoogleMapsResult(BaseModel):
    """
    Raw Google Maps result from Apify API.

    Maps Apify actor output to validated Python model with sanitization:
    - Extracts postal code from address if missing
    - Normalizes phone numbers to E.164 format
    - Sanitizes URLs (adds https:// if missing)
    - Validates rating range (0.0-5.0)
    """

    place_id: str = Field(..., alias="placeId", min_length=1)
    practice_name: str = Field(..., alias="title", min_length=1)
    address: str = Field(..., min_length=1)
    phone: Optional[str] = Field(default=None)
    website: Optional[str] = Field(default=None)
    google_rating: Optional[float] = Field(
        default=None, alias="totalScore", ge=0.0, le=5.0
    )
    google_review_count: Optional[int] = Field(default=None, alias="reviewsCount", ge=0)
    business_categories: List[str] = Field(default_factory=list, alias="categoryName")
    postal_code: Optional[str] = Field(default=None, alias="postalCode")
    permanently_closed: bool = Field(default=False, alias="permanentlyClosed")
    temporarily_closed: bool = Field(default=False, alias="temporarilyClosed")

    class Config:
        populate_by_name = True

    @field_validator("business_categories", mode="before")
    @classmethod
    def parse_category_name(cls, v):
        """Convert single categoryName string to list."""
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return v
        return []

    @field_validator("postal_code", mode="before")
    @classmethod
    def extract_postal_code_from_address(cls, v, info):
        """Extract ZIP code from address if postalCode is null (AC-FEAT-001-001)."""
        if v:
            return v

        # Try to extract from address field
        address = info.data.get("address", "")
        if not address:
            return None

        # Match 5-digit ZIP or ZIP+4
        zip_match = re.search(r"\b(\d{5}(?:-\d{4})?)\b", address)
        if zip_match:
            return zip_match.group(1)

        return None

    @field_validator("website", mode="before")
    @classmethod
    def sanitize_url(cls, v):
        """Add https:// protocol if missing (AC-FEAT-001-030)."""
        if not v:
            return None

        v = v.strip()

        # Already has protocol
        if v.startswith(("http://", "https://")):
            return v

        # Add https:// prefix
        return f"https://{v}"

    @field_validator("phone", mode="before")
    @classmethod
    def normalize_phone(cls, v):
        """Normalize phone number to E.164 format (AC-FEAT-001-010)."""
        if not v:
            return None

        try:
            # Parse phone number (default to US region)
            parsed = phonenumbers.parse(v, "US")

            # Validate it's a valid number
            if not phonenumbers.is_valid_number(parsed):
                return v  # Return original if invalid

            # Format to E.164 (+16175550100)
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            # If parsing fails, return original
            return v


class VeterinaryPractice(BaseModel):
    """
    Filtered and scored veterinary practice for Notion database.

    Extends ApifyGoogleMapsResult with:
    - initial_score: 0-25 point ICP fit score
    - priority_tier: Hot/Warm/Cold classification
    - first_scraped_date: Timestamp for tracking
    """

    place_id: str = Field(..., min_length=1)
    practice_name: str = Field(..., min_length=1)
    address: str = Field(..., min_length=1)
    phone: Optional[str] = Field(default=None)
    website: Optional[str] = Field(default=None)
    google_rating: Optional[float] = Field(default=None, ge=0.0, le=5.0)
    google_review_count: Optional[int] = Field(default=None, ge=0)
    business_categories: List[str] = Field(default_factory=list)
    postal_code: Optional[str] = Field(default=None)
    permanently_closed: bool = Field(default=False)

    # Scoring fields (FEAT-001 adds initial score 0-25)
    initial_score: int = Field(..., ge=0, le=25, description="ICP fit score (0-25)")
    priority_tier: str = Field(default="Cold", description="Hot/Warm/Cold")

    # Metadata
    first_scraped_date: Optional[str] = Field(
        default=None, description="ISO 8601 date"
    )

    @field_validator("priority_tier", mode="before")
    @classmethod
    def validate_priority_tier(cls, v):
        """Validate priority tier is one of Hot/Warm/Cold."""
        if not v:
            return "Cold"

        valid_tiers = ["Hot", "Warm", "Cold"]
        if v not in valid_tiers:
            raise ValueError(f"Priority tier must be one of: {', '.join(valid_tiers)}")

        return v
