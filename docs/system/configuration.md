# Configuration Management

**Last Updated:** 2025-11-03
**Status:** Active
**Approach:** Hybrid (config.json + .env for secrets)

## Overview

This document specifies the complete configuration management system using Pydantic v2 for validation, combining structured configuration files with environment variable overrides for sensitive data.

## Configuration Architecture

```
┌────────────────────────────────────────────────────┐
│              CONFIGURATION SOURCES                  │
├────────────────────────────────────────────────────┤
│                                                     │
│  config/config.json          .env                  │
│  (Structure & Logic)     (Secrets)                 │
│         ↓                     ↓                     │
│    Pydantic Models      Environment                │
│         ↓                  Settings                 │
│         └──────────┬──────────┘                    │
│                    ↓                                │
│            Validated Config                         │
│            (Type-Safe)                              │
└────────────────────────────────────────────────────┘
```

## Configuration Strategy

### What Goes Where

| Setting Type | Storage | Example | Why |
|--------------|---------|---------|-----|
| **Business Logic** | config.json | Search terms, scoring weights | Version controlled, shareable |
| **Secrets** | .env | API keys, tokens | Never committed, per-environment |
| **Structure** | config.json | Filter rules, field mappings | Portable across environments |
| **Infrastructure** | .env | Database IDs, endpoints | Environment-specific |

### Hybrid Loading Pattern

```python
# 1. Load base config from JSON
config = VetScrapingConfig.from_file("config/config.json")

# 2. Load secrets from environment
env = EnvironmentSettings()  # Loads from .env

# 3. Merge: env vars override JSON
config.apify.api_key = env.apify_api_key
config.notion.api_key = env.notion_api_key

# 4. Validate complete config
config.validate()  # Pydantic validates all fields
```

## Complete Pydantic Models

### Main Configuration Model

```python
from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Literal, Dict
from enum import Enum
from datetime import date

class VetScrapingConfig(BaseModel):
    """Main configuration for veterinary scraping system."""

    project_name: str
    version: str
    target: TargetConfig
    apify: ApifyConfig
    website_scraping: WebsiteScrapingConfig
    notion: NotionConfig
    scoring: ScoringConfig
    filtering: FilteringConfig
    log_level: LogLevel = LogLevel.INFO

    model_config = SettingsConfigDict(
        env_prefix="VET_SCRAPING_",
        case_sensitive=False,
        validate_assignment=True,
        extra="forbid",  # Reject unknown fields
    )

    @classmethod
    def from_file(cls, config_path: str) -> "VetScrapingConfig":
        """Load configuration from JSON file."""
        import json
        with open(config_path, "r") as f:
            config_data = json.load(f)
        return cls(**config_data)
```

### Target Configuration

```python
class TargetGeography(BaseModel):
    """Geographic targeting configuration."""

    center: str = Field(..., description="Center location (e.g., 'Boston, MA, USA')")
    radius_miles: int = Field(25, ge=1, le=100)
    include_cities: List[str] = Field(default_factory=list)

    @field_validator("include_cities")
    @classmethod
    def validate_cities(cls, v: List[str]) -> List[str]:
        """Ensure cities are non-empty strings."""
        return [city.strip() for city in v if city.strip()]


class TargetConfig(BaseModel):
    """Target business configuration."""

    business_type: str
    search_terms: List[str] = Field(min_length=1)
    geography: TargetGeography

    @field_validator("search_terms")
    @classmethod
    def validate_search_terms(cls, v: List[str]) -> List[str]:
        """Ensure search terms are non-empty."""
        if not v or all(not term.strip() for term in v):
            raise ValueError("At least one non-empty search term required")
        return [term.strip() for term in v if term.strip()]
```

### Apify Configuration

```python
class ApifyConfig(BaseModel):
    """Apify API configuration."""

    google_maps_actor: str = "compass/crawler-google-places"
    linkedin_actor: str = "apimaestro/linkedin-company-employees-scraper-no-cookies"
    max_google_results: int = Field(200, ge=10, le=1000)
    api_key: str = Field(..., description="Loaded from env var")

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate Apify API key format."""
        if not v.startswith("apify_api_"):
            raise ValueError("Apify API key must start with 'apify_api_'")
        if len(v) < 20:
            raise ValueError("Apify API key too short")
        return v

    @field_validator("google_maps_actor")
    @classmethod
    def validate_actor_format(cls, v: str) -> str:
        """Validate actor ID format."""
        if "/" not in v:
            raise ValueError("Actor ID must be in format 'username/actor-name'")
        return v
```

### Website Scraping Configuration

```python
class WebsiteScrapingConfig(BaseModel):
    """Website scraping and LLM extraction configuration."""

    tool: Literal["crawl4ai"] = "crawl4ai"
    llm_provider: Literal["openai"] = "openai"
    llm_model: str = "gpt-4o-mini"
    extraction_prompt_file: str = "config/website_extraction_prompt.txt"
    pages_to_crawl: List[str] = Field(
        default_factory=lambda: ["homepage", "team", "about", "our-doctors", "staff"]
    )
    delay_between_requests_seconds: float = Field(4.0, ge=1.0, le=10.0)
    timeout_seconds: int = Field(30, ge=10, le=120)
    max_concurrent_requests: int = Field(5, ge=1, le=20)
    max_input_chars: int = Field(8000, ge=1000, le=32000)
    retry_attempts: int = Field(2, ge=1, le=5)

    @field_validator("extraction_prompt_file")
    @classmethod
    def validate_prompt_file_exists(cls, v: str) -> str:
        """Validate prompt file exists."""
        from pathlib import Path
        if not Path(v).exists():
            raise ValueError(f"Extraction prompt file not found: {v}")
        return v
```

### Notion Configuration

```python
class NotionConfig(BaseModel):
    """Notion API configuration."""

    api_key: str = Field(..., description="Loaded from env var")
    database_id: str = Field(..., description="Loaded from env var")
    batch_size: int = Field(10, ge=1, le=100)
    rate_limit_delay: float = Field(0.35, ge=0.1, le=1.0)
    update_existing_records: bool = True
    preserve_fields_on_update: List[str] = Field(
        default_factory=lambda: [
            "Status",
            "Assigned To",
            "Research Notes",
            "Call Notes",
            "Next Action",
            "Next Follow-Up Date",
            "Last Contact Date",
            "Outreach Attempts",
        ]
    )

    @field_validator("api_key")
    @classmethod
    def validate_notion_api_key(cls, v: str) -> str:
        """Validate Notion API key format."""
        if not v.startswith("secret_"):
            raise ValueError("Notion API key must start with 'secret_'")
        if len(v) < 40:
            raise ValueError("Notion API key too short")
        return v

    @field_validator("database_id")
    @classmethod
    def validate_database_id(cls, v: str) -> str:
        """Validate Notion database ID format."""
        # Remove dashes and validate length
        clean_id = v.replace("-", "")
        if len(clean_id) != 32:
            raise ValueError(
                f"Notion database ID must be 32 hex chars (got {len(clean_id)})"
            )
        # Validate hex
        try:
            int(clean_id, 16)
        except ValueError:
            raise ValueError("Notion database ID must be hexadecimal")
        return v
```

### Scoring Configuration

```python
class ScoringConfig(BaseModel):
    """Lead scoring algorithm configuration."""

    practice_size_and_complexity: Dict[str, int] = Field(
        default_factory=lambda: {
            "3_to_5_vets": 25,
            "2_or_6_vets": 15,
            "7_to_9_vets": 5,
            "emergency_services": 15,
        }
    )
    call_volume_indicators: Dict[str, int] = Field(
        default_factory=lambda: {
            "100_plus_reviews": 20,
            "50_to_99_reviews": 12,
            "20_to_49_reviews": 5,
            "multiple_locations": 10,
        }
    )
    technology_sophistication: Dict[str, int] = Field(
        default_factory=lambda: {
            "online_booking": 10,
            "modern_website": 5,
            "client_portal_or_live_chat": 5,
        }
    )
    baseline_criteria: Dict[str, int] = Field(
        default_factory=lambda: {
            "rating_3_5_plus": 5,
            "has_website": 5,
        }
    )
    decision_maker_bonus: Dict[str, int] = Field(
        default_factory=lambda: {
            "email_verified": 20,
            "email_guessed": 15,
            "name_only": 10,
        }
    )

    @model_validator(mode="after")
    def validate_max_score(self) -> "ScoringConfig":
        """Ensure total max score doesn't exceed 120."""
        # Calculate max possible base score
        max_size = max(self.practice_size_and_complexity.values())
        max_volume = sum(
            [
                self.call_volume_indicators["100_plus_reviews"],
                self.call_volume_indicators["multiple_locations"],
            ]
        )
        max_tech = sum(self.technology_sophistication.values())
        max_baseline = sum(self.baseline_criteria.values())
        max_bonus = max(self.decision_maker_bonus.values())

        total_max = max_size + max_volume + max_tech + max_baseline + max_bonus

        if total_max > 120:
            raise ValueError(
                f"Max possible score ({total_max}) exceeds 120. "
                "Adjust scoring weights."
            )

        return self
```

### Filtering Configuration

```python
class HardDisqualifiers(BaseModel):
    """Hard disqualification criteria."""

    min_google_reviews: int = Field(10, ge=0)
    must_have_website: bool = True
    exclude_if_closed: bool = True
    exclude_keywords: List[str] = Field(
        default_factory=lambda: ["pet store", "grooming only", "boarding only"]
    )

    @field_validator("exclude_keywords")
    @classmethod
    def lowercase_keywords(cls, v: List[str]) -> List[str]:
        """Normalize keywords to lowercase."""
        return [kw.lower().strip() for kw in v]


class FilteringConfig(BaseModel):
    """Filtering and disqualification rules."""

    hard_disqualifiers: HardDisqualifiers
    must_have_one_of: List[str] = Field(
        default_factory=lambda: [
            "emergency_services",
            "50_plus_reviews",
            "multiple_locations",
            "3_plus_vets",
        ]
    )

    @field_validator("must_have_one_of")
    @classmethod
    def validate_criteria(cls, v: List[str]) -> List[str]:
        """Validate criteria names."""
        valid_criteria = [
            "emergency_services",
            "50_plus_reviews",
            "multiple_locations",
            "3_plus_vets",
        ]
        for criterion in v:
            if criterion not in valid_criteria:
                raise ValueError(f"Invalid criterion: {criterion}")
        return v
```

### Logging Configuration

```python
class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
```

## Environment Settings

### Environment Variable Schema

```python
from pydantic_settings import BaseSettings

class EnvironmentSettings(BaseSettings):
    """Environment-specific settings (secrets and overrides)."""

    # Required API Keys
    apify_api_key: str = Field(..., validation_alias="APIFY_API_KEY")
    openai_api_key: str = Field(..., validation_alias="OPENAI_API_KEY")
    notion_api_key: str = Field(..., validation_alias="NOTION_API_KEY")
    notion_database_id: str = Field(..., validation_alias="NOTION_DATABASE_ID")

    # Optional Overrides
    log_level: Optional[str] = Field(None, validation_alias="LOG_LEVEL")
    test_mode: bool = Field(False, validation_alias="TEST_MODE")
    max_practices: Optional[int] = Field(None, validation_alias="MAX_PRACTICES")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore unknown env vars
    )

    @field_validator("apify_api_key")
    @classmethod
    def validate_apify_key(cls, v: str) -> str:
        if not v.startswith("apify_api_"):
            raise ValueError("Invalid Apify API key format")
        return v

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key(cls, v: str) -> str:
        if not v.startswith("sk-"):
            raise ValueError("Invalid OpenAI API key format")
        return v

    @field_validator("notion_api_key")
    @classmethod
    def validate_notion_key(cls, v: str) -> str:
        if not v.startswith("secret_"):
            raise ValueError("Invalid Notion API key format")
        return v
```

### .env File Format

**`.env.example` (checked into git):**
```bash
# API Keys (REQUIRED)
APIFY_API_KEY=apify_api_your_key_here
OPENAI_API_KEY=sk-your_openai_key_here
NOTION_API_KEY=secret_your_notion_integration_token
NOTION_DATABASE_ID=2a0edda2a9a081d98dc9daa43c65e744

# Optional Overrides
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
TEST_MODE=false  # true = only scrape 10 practices
MAX_PRACTICES=150  # Override max results from config.json
```

**`.env` (gitignored, actual secrets):**
```bash
# Copy .env.example to .env and fill in your actual values
APIFY_API_KEY=apify_api_abc123xyz...
OPENAI_API_KEY=sk-proj-def456uvw...
NOTION_API_KEY=secret_ghi789rst...
NOTION_DATABASE_ID=2a0edda2a9a081d98dc9daa43c65e744

LOG_LEVEL=DEBUG
TEST_MODE=true
```

## Configuration Loading

### Complete Loading Function

```python
def load_full_config(config_path: str = "config/config.json") -> VetScrapingConfig:
    """Load and merge configuration from JSON + environment.

    Steps:
    1. Load base config from JSON
    2. Load secrets from environment (.env)
    3. Merge: environment overrides JSON
    4. Validate complete config
    5. Return validated config object

    Returns:
        Fully validated VetScrapingConfig
    """
    # Step 1: Load base config
    config = VetScrapingConfig.from_file(config_path)

    # Step 2: Load environment settings
    env = EnvironmentSettings()

    # Step 3: Merge secrets
    config.apify.api_key = env.apify_api_key
    config.notion.api_key = env.notion_api_key
    config.notion.database_id = env.notion_database_id

    # Note: OpenAI key passed separately to OpenAI client
    # Not stored in config object for security

    # Step 4: Apply overrides
    if env.log_level:
        config.log_level = LogLevel(env.log_level)

    if env.test_mode:
        config.apify.max_google_results = 10
        config.website_scraping.max_concurrent_requests = 2

    if env.max_practices:
        config.apify.max_google_results = env.max_practices

    # Step 5: Final validation happens automatically (Pydantic)

    return config
```

### Usage Example

```python
# In main.py
from src.config.settings import load_full_config

# Load configuration
config = load_full_config("config/config.json")

# Access validated config
print(f"Scraping {config.apify.max_google_results} practices")
print(f"Search terms: {config.target.search_terms}")
print(f"Notion database: {config.notion.database_id}")

# Pass to components
apify_scraper = ApifyScraper(api_key=config.apify.api_key)
notion_client = NotionClient(api_key=config.notion.api_key)
```

## Configuration Validation

### Startup Validation Script

```python
def validate_config_on_startup(config: VetScrapingConfig) -> bool:
    """Validate configuration before running pipeline.

    Checks:
    - All required fields present
    - API keys valid format
    - File paths exist
    - Scoring weights sum correctly
    - Database connection works

    Returns:
        True if valid, raises exception otherwise
    """
    # Check extraction prompt file
    if not Path(config.website_scraping.extraction_prompt_file).exists():
        raise FileNotFoundError(
            f"Extraction prompt file not found: "
            f"{config.website_scraping.extraction_prompt_file}"
        )

    # Validate Notion connection
    try:
        notion = Client(auth=config.notion.api_key)
        notion.databases.retrieve(database_id=config.notion.database_id)
        print("✓ Notion connection validated")
    except Exception as e:
        raise ConnectionError(f"Notion connection failed: {e}")

    # Validate Apify connection
    try:
        apify = ApifyClient(config.apify.api_key)
        # Test API by fetching user info
        user = apify.user().get()
        print(f"✓ Apify connection validated (user: {user['username']})")
    except Exception as e:
        raise ConnectionError(f"Apify connection failed: {e}")

    # Validate OpenAI connection
    try:
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # Test with minimal API call
        openai_client.models.list()
        print("✓ OpenAI connection validated")
    except Exception as e:
        raise ConnectionError(f"OpenAI connection failed: {e}")

    print("✓ All configuration validated successfully")
    return True
```

### Command-Line Validation

```bash
# Validate configuration without running pipeline
python -m src.utils.config_loader --validate

# Output:
# Loading config from config/config.json...
# ✓ Config loaded successfully
# ✓ Notion connection validated
# ✓ Apify connection validated
# ✓ OpenAI connection validated
# ✓ All configuration validated successfully
```

## Configuration File Structure

### config/config.json (Complete Example)

```json
{
  "project_name": "Veterinary Lead Generation - Boston MVP",
  "version": "1.0",

  "target": {
    "business_type": "veterinary clinics",
    "search_terms": [
      "veterinarian",
      "vet clinic",
      "animal hospital",
      "emergency vet",
      "veterinary hospital"
    ],
    "geography": {
      "center": "Boston, MA, USA",
      "radius_miles": 25,
      "include_cities": [
        "Boston",
        "Cambridge",
        "Brookline",
        "Newton",
        "Quincy",
        "Somerville",
        "Medford",
        "Waltham"
      ]
    }
  },

  "apify": {
    "google_maps_actor": "compass/crawler-google-places",
    "linkedin_actor": "apimaestro/linkedin-company-employees-scraper-no-cookies",
    "max_google_results": 200
  },

  "website_scraping": {
    "tool": "crawl4ai",
    "llm_provider": "openai",
    "llm_model": "gpt-4o-mini",
    "extraction_prompt_file": "config/website_extraction_prompt.txt",
    "pages_to_crawl": [
      "homepage",
      "team",
      "about",
      "our-doctors",
      "staff"
    ],
    "delay_between_requests_seconds": 4.0,
    "timeout_seconds": 30,
    "max_concurrent_requests": 5,
    "max_input_chars": 8000,
    "retry_attempts": 2
  },

  "notion": {
    "batch_size": 10,
    "rate_limit_delay": 0.35,
    "update_existing_records": true,
    "preserve_fields_on_update": [
      "Status",
      "Assigned To",
      "Research Notes",
      "Call Notes",
      "Next Action",
      "Next Follow-Up Date",
      "Last Contact Date",
      "Outreach Attempts"
    ]
  },

  "scoring": {
    "practice_size_and_complexity": {
      "3_to_5_vets": 25,
      "2_or_6_vets": 15,
      "7_to_9_vets": 5,
      "emergency_services": 15
    },
    "call_volume_indicators": {
      "100_plus_reviews": 20,
      "50_to_99_reviews": 12,
      "20_to_49_reviews": 5,
      "multiple_locations": 10
    },
    "technology_sophistication": {
      "online_booking": 10,
      "modern_website": 5,
      "client_portal_or_live_chat": 5
    },
    "baseline_criteria": {
      "rating_3_5_plus": 5,
      "has_website": 5
    },
    "decision_maker_bonus": {
      "email_verified": 20,
      "email_guessed": 15,
      "name_only": 10
    }
  },

  "filtering": {
    "hard_disqualifiers": {
      "min_google_reviews": 10,
      "must_have_website": true,
      "exclude_if_closed": true,
      "exclude_keywords": [
        "pet store",
        "grooming only",
        "boarding only"
      ]
    },
    "must_have_one_of": [
      "emergency_services",
      "50_plus_reviews",
      "multiple_locations",
      "3_plus_vets"
    ]
  },

  "log_level": "INFO"
}
```

## Common Pitfalls

### Pitfall 1: Secrets in config.json

**Problem:** Committing API keys to git.

**Solution:** Always use .env for secrets, config.json for structure.

### Pitfall 2: Not Validating on Startup

**Problem:** Pipeline fails 30 minutes in due to invalid config.

**Solution:** Run `validate_config_on_startup()` before main pipeline.

### Pitfall 3: Hardcoded Values

**Problem:** Changing batch size requires code changes.

**Solution:** All tunable parameters in config.json.

### Pitfall 4: No Type Safety

**Problem:** Typos in config cause runtime errors.

**Solution:** Pydantic validates all fields with types.

### Pitfall 5: Environment Variables Not Loading

**Problem:** .env file exists but values not loaded.

**Solution:** Use `python-dotenv` and `load_dotenv()` at startup:

```python
from dotenv import load_dotenv

load_dotenv()  # Load .env file into os.environ
```

---

**See Also:**
- [stack.md](stack.md) - Pydantic version
- [integrations.md](integrations.md) - API credentials format
- [architecture.md](architecture.md) - ConfigLoader component
