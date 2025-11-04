"""Notion database schema validation for FEAT-001.

Validates that a Notion database has all required properties for veterinary practice leads.
Helps catch configuration errors before attempting to upload data.
"""

import logging
from typing import Dict, List, Set

from notion_client import Client

logger = logging.getLogger(__name__)


class NotionSchemaError(Exception):
    """Raised when Notion database schema doesn't match requirements."""

    pass


# Required properties for FEAT-001 Google Maps → Notion pipeline
# Maps to existing database schema: "Veterinary Lead Pipeline - Boston"
REQUIRED_PROPERTIES = {
    "Name": "title",  # Practice name (unique identifier)
    "Google Place ID": "rich_text",  # Google Maps Place ID
    "Address": "rich_text",
    "Phone": "phone_number",
    "Website": "url",
    "Google Review Count": "number",
    "Google Rating": "number",
    "Lead Score": "number",  # Initial ICP fit score (0-25)
    "Status": "select",
}


def validate_notion_database(database_id: str, api_key: str) -> Dict[str, any]:
    """Validate that Notion database has all required properties.

    Args:
        database_id: Notion database ID (32-char hex or UUID format)
        api_key: Notion integration API key (secret_* or ntn_* format)

    Returns:
        Database object from Notion API with properties

    Raises:
        NotionSchemaError: If database is missing required properties or types don't match
        Exception: If Notion API call fails (connection, auth, etc.)

    Example:
        >>> from src.integrations.notion_schema import validate_notion_database
        >>> db = validate_notion_database("2a0edda2a9a081d98dc9daa43c65e744", "secret_xxx")
        >>> print(f"Database '{db['title'][0]['plain_text']}' validated successfully")
    """
    logger.info(f"Validating Notion database schema: {database_id}")

    # Initialize Notion client
    try:
        client = Client(auth=api_key)
        database = client.databases.retrieve(database_id=database_id)
    except Exception as e:
        logger.error(f"Failed to retrieve Notion database: {e}")
        raise NotionSchemaError(
            f"Cannot connect to Notion database {database_id}. "
            f"Check API key and database ID. Error: {e}"
        ) from e

    # Extract existing properties
    existing_properties = database.get("properties", {})
    existing_names = set(existing_properties.keys())
    required_names = set(REQUIRED_PROPERTIES.keys())

    # Check for missing properties
    missing = required_names - existing_names
    if missing:
        logger.error(f"Missing required properties: {missing}")
        raise NotionSchemaError(
            f"Notion database is missing required properties: {sorted(missing)}. "
            f"Please add these properties to the database schema."
        )

    # Check property types match
    type_mismatches = []
    for prop_name, expected_type in REQUIRED_PROPERTIES.items():
        actual_prop = existing_properties[prop_name]
        actual_type = actual_prop.get("type")

        if actual_type != expected_type:
            type_mismatches.append(
                f"'{prop_name}': expected {expected_type}, got {actual_type}"
            )

    if type_mismatches:
        logger.error(f"Property type mismatches: {type_mismatches}")
        raise NotionSchemaError(
            f"Notion database has property type mismatches: {type_mismatches}. "
            f"Please update the property types in the database schema."
        )

    # Validation passed
    logger.info(
        f"Notion database validated successfully: {len(existing_names)} properties found"
    )
    return database


def get_property_details(database: Dict[str, any]) -> List[Dict[str, str]]:
    """Extract property names and types from database object.

    Useful for debugging and displaying database schema information.

    Args:
        database: Database object from Notion API

    Returns:
        List of dicts with 'name' and 'type' keys for each property

    Example:
        >>> db = validate_notion_database("xxx", "secret_xxx")
        >>> props = get_property_details(db)
        >>> for prop in props:
        ...     print(f"{prop['name']}: {prop['type']}")
    """
    properties = database.get("properties", {})
    return [
        {"name": name, "type": prop.get("type")} for name, prop in properties.items()
    ]
