"""Notion data mapper for FEAT-001 Google Maps → Notion pipeline.

Transforms VeterinaryPractice models into Notion API-compatible property dictionaries.
Handles field type conversions, null values, and payload structure.

Reference: AC-FEAT-001-010 (Notion Schema Compliance)
"""

import logging
from typing import Dict, Any, Optional

from src.models.apify_models import VeterinaryPractice

logger = logging.getLogger(__name__)


class NotionMapper:
    """Maps VeterinaryPractice data to Notion API format.

    Notion API property formats:
    - title: {"title": [{"text": {"content": "value"}}]}
    - rich_text: {"rich_text": [{"text": {"content": "value"}}]}
    - phone_number: {"phone_number": "+16175551234"} or {"phone_number": null}
    - url: {"url": "https://example.com"} or {"url": null}
    - number: {"number": 123.45} or {"number": null}
    - select: {"select": {"name": "Option Name"}}

    Example:
        >>> from src.integrations.notion_mapper import NotionMapper
        >>> from src.models.apify_models import VeterinaryPractice
        >>>
        >>> practice = VeterinaryPractice(
        ...     place_id="ChIJXXX",
        ...     practice_name="Boston Vet",
        ...     address="123 Main St",
        ...     initial_score=25
        ... )
        >>>
        >>> mapper = NotionMapper(database_id="2a0edda2a9a081d98dc9daa43c65e744")
        >>> payload = mapper.create_page_payload(practice)
        >>> # Ready to send to Notion API: client.pages.create(**payload)
    """

    def __init__(self, database_id: str):
        """Initialize NotionMapper with target database ID.

        Args:
            database_id: Notion database ID (32-char hex string)
        """
        self.database_id = database_id
        logger.debug(f"NotionMapper initialized for database: {database_id}")

    def map_to_notion_properties(self, practice: VeterinaryPractice) -> Dict[str, Any]:
        """Transform VeterinaryPractice to Notion properties dict.

        Maps fields to existing Notion database schema:
        - Practice Name → Name (Title field)
        - Place ID → Google Place ID (Rich Text)
        - Address → Address (Rich Text)
        - Phone → Phone (Phone Number, E.164 format)
        - Website → Website (URL)
        - Review Count → Google Review Count (Number)
        - Star Rating → Google Rating (Number, rounded to 1 decimal)
        - Initial Score → Lead Score (Number, 0-25)
        - Status → Status (Select, default: "New Lead")

        Args:
            practice: VeterinaryPractice instance with validated data

        Returns:
            Dict of Notion properties ready for API submission

        Example:
            >>> properties = mapper.map_to_notion_properties(practice)
            >>> assert "Name" in properties
            >>> assert properties["Status"]["select"]["name"] == "New Lead"
        """
        properties = {}

        # Practice Name → Name (Title field, unique identifier)
        properties["Name"] = self._format_title(practice.practice_name)

        # Place ID → Google Place ID (Rich Text)
        properties["Google Place ID"] = self._format_rich_text(practice.place_id)

        # Address → Address (Rich Text)
        properties["Address"] = self._format_rich_text(practice.address)

        # Phone → Phone (Phone Number, E.164 format, can be null)
        properties["Phone"] = self._format_phone_number(practice.phone)

        # Website → Website (URL, can be null)
        properties["Website"] = self._format_url(practice.website)

        # Review Count → Google Review Count (Number, can be null)
        properties["Google Review Count"] = self._format_number(practice.google_review_count)

        # Star Rating → Google Rating (Number, rounded to 1 decimal, can be null)
        properties["Google Rating"] = self._format_number(
            round(practice.google_rating, 1) if practice.google_rating is not None else None
        )

        # Initial Score → Lead Score (Number, 0-25, required)
        properties["Lead Score"] = self._format_number(practice.initial_score)

        # Status → Status (Select, default: "New Lead")
        properties["Status"] = self._format_select("New Lead")

        logger.debug(
            f"Mapped practice {practice.place_id} to Notion properties "
            f"({len(properties)} fields)"
        )

        return properties

    def create_page_payload(self, practice: VeterinaryPractice) -> Dict[str, Any]:
        """Create complete Notion API page creation payload.

        Combines database parent reference with mapped properties.

        Args:
            practice: VeterinaryPractice to convert to Notion page

        Returns:
            Complete payload for notion_client.pages.create(**payload)

        Example:
            >>> payload = mapper.create_page_payload(practice)
            >>> assert payload["parent"]["database_id"] == mapper.database_id
            >>> assert "properties" in payload
        """
        return {
            "parent": {"database_id": self.database_id},
            "properties": self.map_to_notion_properties(practice),
        }

    # ===== Notion Property Formatters =====

    @staticmethod
    def _format_title(value: str) -> Dict[str, Any]:
        """Format value as Notion title property.

        Title is used for Place ID (unique identifier).

        Args:
            value: String value (required, cannot be null)

        Returns:
            {"title": [{"text": {"content": "value"}}]}
        """
        return {"title": [{"text": {"content": value}}]}

    @staticmethod
    def _format_rich_text(value: str) -> Dict[str, Any]:
        """Format value as Notion rich_text property.

        Used for Business Name, Address.

        Args:
            value: String value (required, cannot be null)

        Returns:
            {"rich_text": [{"text": {"content": "value"}}]}
        """
        return {"rich_text": [{"text": {"content": value}}]}

    @staticmethod
    def _format_phone_number(value: Optional[str]) -> Dict[str, Any]:
        """Format value as Notion phone_number property.

        Phone numbers must be in E.164 format (+16175551234).
        VeterinaryPractice model already normalizes to E.164.

        Args:
            value: E.164 phone number string or None

        Returns:
            {"phone_number": "+16175551234"} or {"phone_number": null}
        """
        return {"phone_number": value}

    @staticmethod
    def _format_url(value: Optional[str]) -> Dict[str, Any]:
        """Format value as Notion url property.

        URLs should have https:// protocol.
        VeterinaryPractice model already sanitizes URLs.

        Args:
            value: URL string or None

        Returns:
            {"url": "https://example.com"} or {"url": null}
        """
        return {"url": value}

    @staticmethod
    def _format_number(value: Optional[float | int]) -> Dict[str, Any]:
        """Format value as Notion number property.

        Used for Review Count, Star Rating, Initial Score.

        Args:
            value: Number value or None

        Returns:
            {"number": 123.45} or {"number": null}
        """
        return {"number": value}

    @staticmethod
    def _format_select(value: str) -> Dict[str, Any]:
        """Format value as Notion select property.

        Used for Status field (default: "New Lead").

        Args:
            value: Select option name (must exist in database schema)

        Returns:
            {"select": {"name": "value"}}
        """
        return {"select": {"name": value}}
