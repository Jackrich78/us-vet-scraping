"""
Configuration management for US Vet Scraping application.

Uses Pydantic v2 BaseSettings for environment variable loading with validation.
Supports nested configuration models and fail-fast validation.
"""

from typing import List, Optional
from pathlib import Path
from pydantic import Field, field_validator, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApifyConfig(BaseSettings):
    """Apify API configuration."""

    api_key: str = Field(..., alias='APIFY_API_KEY', min_length=10)
    actor_id: str = Field(default='compass/crawler-google-places')
    max_results: int = Field(default=50)
    timeout_seconds: int = Field(default=300)

    @field_validator('api_key')
    @classmethod
    def validate_apify_key(cls, v: str) -> str:
        if not v.startswith('apify_api_'):
            raise ValueError('Invalid Apify API key format - must start with "apify_api_"')
        return v


class OpenAIConfig(BaseSettings):
    """OpenAI API configuration."""

    api_key: str = Field(..., alias='OPENAI_API_KEY', min_length=20)
    model: str = Field(default='gpt-4o-mini')
    max_tokens: int = Field(default=1000)
    temperature: float = Field(default=0.1)

    @field_validator('api_key')
    @classmethod
    def validate_openai_key(cls, v: str) -> str:
        if not (v.startswith('sk-') or v.startswith('sk-proj-')):
            raise ValueError('Invalid OpenAI API key format - must start with "sk-" or "sk-proj-"')
        return v


class NotionConfig(BaseSettings):
    """Notion API configuration."""

    api_key: str = Field(..., alias='NOTION_API_KEY', min_length=20)
    database_id: str = Field(..., alias='NOTION_DATABASE_ID', min_length=32, max_length=32)
    batch_size: int = Field(default=10)
    rate_limit_delay: float = Field(default=0.35)
    update_existing: bool = Field(default=True)

    @field_validator('api_key')
    @classmethod
    def validate_notion_key(cls, v: str) -> str:
        if not (v.startswith('secret_') or v.startswith('ntn_')):
            raise ValueError('Invalid Notion API key format - must start with "secret_" or "ntn_"')
        return v


class WebsiteScrapingConfig(BaseSettings):
    """Website scraping configuration."""

    max_concurrent: int = Field(default=5)
    timeout_seconds: int = Field(default=30)
    retry_attempts: int = Field(default=2)
    extraction_prompt_file: str = Field(default='config/website_extraction_prompt.txt')
    cache_enabled: bool = Field(default=True)
    cache_directory: str = Field(default='data/website_cache')
    delay_between_requests: float = Field(default=4.0)


class RetryConfig(BaseSettings):
    """Retry logic configuration."""

    max_retries: int = Field(default=5, ge=0, le=10)
    backoff_base: int = Field(default=1, ge=1, le=5)
    max_backoff_seconds: int = Field(default=60)

    @property
    def backoff_sequence(self) -> List[int]:
        """Calculate exponential backoff sequence."""
        return [self.backoff_base * (2 ** i) for i in range(self.max_retries)]


class LoggingConfig(BaseSettings):
    """Logging configuration."""

    log_level: str = Field(default='INFO')
    log_file: Optional[str] = Field(default='logs/app.log')
    enable_ansi: bool = Field(default=True)
    enable_json_file: bool = Field(default=True)

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f'Invalid log level. Must be one of: {", ".join(valid_levels)}')
        return v_upper


class CacheConfig(BaseSettings):
    """Cache configuration."""

    max_size: int = Field(default=1000)
    max_memory_mb: int = Field(default=10)
    ttl_seconds: Optional[int] = Field(default=None)


class VetScrapingConfig(BaseSettings):
    """Main application configuration.

    Loads configuration from environment variables and .env file.
    Validates all settings on initialization with fail-fast behavior.
    """

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_nested_delimiter='__',
        case_sensitive=False,
        extra='ignore'
    )

    # Application metadata
    app_name: str = Field(default='US Vet Scraping')
    app_version: str = Field(default='1.0.0')

    # API configurations (loaded from env vars)
    apify: ApifyConfig = ApifyConfig()
    openai: OpenAIConfig = OpenAIConfig()
    notion: NotionConfig = NotionConfig()

    # Feature configurations (loaded from config.json or defaults)
    website_scraping: WebsiteScrapingConfig = WebsiteScrapingConfig()
    retry: RetryConfig = RetryConfig()
    logging: LoggingConfig = LoggingConfig()
    cache: CacheConfig = CacheConfig()

    # Runtime flags
    test_mode: bool = Field(default=False)

    def enable_test_mode(self) -> None:
        """Enable test mode with DEBUG logging."""
        self.test_mode = True
        self.logging.log_level = 'DEBUG'

    @classmethod
    def load_from_env(cls, env_file: str = '.env') -> 'VetScrapingConfig':
        """
        Load configuration from environment file with validation.

        Args:
            env_file: Path to environment file

        Returns:
            Validated configuration instance

        Raises:
            ValidationError: If configuration is invalid
            FileNotFoundError: If .env file doesn't exist
        """
        env_path = Path(env_file)
        if not env_path.exists():
            raise FileNotFoundError(f'Environment file not found: {env_file}')

        try:
            config = cls()
            return config
        except ValidationError as e:
            # Re-raise with clear error message
            error_fields = [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
            raise ValidationError.from_exception_data(
                "Configuration validation failed",
                [{"loc": ("config",), "msg": f"Invalid configuration: {', '.join(error_fields)}"}]
            ) from e


# Singleton instance for application-wide use
_config_instance: Optional[VetScrapingConfig] = None


def get_config() -> VetScrapingConfig:
    """
    Get singleton configuration instance.

    Returns:
        Validated configuration instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = VetScrapingConfig()
    return _config_instance


def reload_config() -> VetScrapingConfig:
    """
    Force reload of configuration from environment.

    Returns:
        New validated configuration instance
    """
    global _config_instance
    _config_instance = VetScrapingConfig()
    return _config_instance
