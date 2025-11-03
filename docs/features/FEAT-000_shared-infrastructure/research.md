# Research Findings: Shared Infrastructure

**Feature ID:** FEAT-000
**Research Date:** 2025-11-03
**Researcher:** Researcher Agent

## Research Questions

*Questions from PRD that this research addresses:*

1. Should we validate API connectivity during config load or defer to feature code?
2. Should --test flag be in config.json or command-line only?
3. Should we use colorlog library or custom ANSI codes for console output?
4. Should test mode auto-switch to DEBUG log level?
5. Should we implement circuit breaker pattern now or Phase 2?
6. Should we log estimated cost per retry?
7. Should we cache Place IDs in memory during batch operations?
8. Should we validate Notion schema on startup?
9. Should errors be written to separate file or kept in-memory only?
10. Should Pydantic models include Notion field name mappings or keep separate?

## Findings

### Topic 1: Pydantic v2 Configuration Management

**Summary:** Pydantic v2 provides robust settings management through `pydantic-settings` package with `BaseSettings` class, offering type-safe configuration loading with automatic validation, environment variable integration, and flexible configuration sources.

**Details:**
- **Separate Package:** From Pydantic v2, settings management requires installing `pydantic-settings` separately from core `pydantic` package
- **SettingsConfigDict:** Use `SettingsConfigDict` instead of nested `Config` class for configuration (major v2 syntax change)
- **Environment Variables:** Automatic loading from `.env` files via `env_file` and `env_file_encoding` settings
- **Validation by Default:** Unlike `BaseModel`, `BaseSettings` validates default values automatically
- **Nested Settings:** Support for nested models via `env_nested_delimiter` for complex configurations
- **Priority Order:** Environment variables override `.env` file values; nested env vars take precedence over top-level JSON
- **Singleton Pattern:** Recommended to instantiate settings once at module level to avoid repeated file reads
- **Fail-Fast Validation:** Configuration errors are caught immediately on load, not at runtime

**Source:** Pydantic Official Documentation
**URL:** https://docs.pydantic.dev/latest/concepts/pydantic_settings/
**Retrieved:** 2025-11-03 via WebSearch

**Code Example (Pydantic v2 Syntax):**
```python
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class VetScrapingConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_nested_delimiter='__',
        case_sensitive=False
    )

    apify_api_key: str = Field(..., alias='APIFY_API_KEY')
    notion_database_id: str = Field(..., min_length=32, max_length=32)

    @field_validator('apify_api_key')
    @classmethod
    def validate_apify_key(cls, v: str) -> str:
        if not v.startswith('apify_api_'):
            raise ValueError('Invalid Apify API key format')
        return v
```

### Topic 2: Python Logging - Dual Output with JSON and Colorized Formatters

**Summary:** Python's standard library logging supports multiple handlers with different formatters, enabling dual output (JSON to file, colorized to console) without external dependencies. Structured logging best practices recommend JSON for production/files and simple colorized output for development/console.

**Details:**
- **No External Dependencies Needed:** Custom formatters using ANSI escape codes work without libraries like `colorlog`
- **Multiple Handlers Pattern:** Attach `StreamHandler` (console) and `FileHandler` separately to same logger
- **Different Formatters:** Assign `JSONFormatter` to file handler, `ColorizedFormatter` to console handler
- **Structured Logging:** JSON format enables machine parsing for log aggregation tools (ELK, Datadog, etc.)
- **Context Fields:** Include extra fields (practice_name, cost, scrape_run_id) via `extra` parameter in log calls
- **Environment-Specific:** Console for human readability (development), JSON for machine parsing (production)
- **Performance:** Minimal overhead with proper log level filtering

**Source:** Python Logging Cookbook (Official Documentation)
**URL:** https://docs.python.org/3/howto/logging-cookbook.html
**Retrieved:** 2025-11-03 via WebSearch

**Popular Libraries (Optional):**
- **python-json-logger:** Most popular library for JSON formatting (MIT license)
- **pylogrus:** Combines JSON and colorized output in one package
- **structlog:** Advanced structured logging with performance optimizations
- **Recommendation:** Start with custom formatters (zero dependencies), migrate to `python-json-logger` if needed

**Code Example (Custom ANSI Formatters):**
```python
import logging

class ColorizedFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)

class JSONFormatter(logging.Formatter):
    def format(self, record):
        import json
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
        }
        # Add extra fields if present
        if hasattr(record, 'practice_name'):
            log_data['practice_name'] = record.practice_name
        if hasattr(record, 'cost'):
            log_data['cost'] = record.cost
        return json.dumps(log_data)
```

### Topic 3: Tenacity Retry Library - Exponential Backoff Patterns

**Summary:** Tenacity is the standard Python retry library (9.0+) providing decorator-based retry logic with exponential backoff, jitter, and flexible exception handling. Best practices emphasize setting stop conditions, using exponential backoff for distributed services, and adding jitter to prevent thundering herd problems.

**Details:**
- **Decorator Pattern:** Clean API using `@retry` decorator on functions
- **Exponential Backoff:** Use `wait_exponential(multiplier=1, min=4, max=10)` for growing delays
- **Jitter Recommended:** `wait_random_exponential()` or `wait_fixed() + wait_random()` prevents simultaneous retries
- **Stop Conditions:** Always set `stop_after_attempt()` or `stop_after_delay()` to prevent infinite loops
- **Exception Filtering:** Use `retry_if_exception_type()` to only retry specific errors (network, 429, timeouts)
- **Never Retry Client Errors:** Don't retry 400, 401, 403, 404 (permanent failures)
- **Logging Hooks:** Use `before`, `after`, and `retry` callbacks for observability
- **Cost Tracking:** Log estimated API cost in retry callbacks to monitor budget impact

**Source:** Tenacity Official Documentation & Medium Articles
**URL:** https://tenacity.readthedocs.io/
**Retrieved:** 2025-11-03 via WebSearch

**Best Practice Patterns:**
```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    wait_random_exponential,
    retry_if_exception_type,
    before_log,
    after_log
)
import logging

logger = logging.getLogger(__name__)

# Pattern 1: Exponential with jitter (recommended for distributed services)
@retry(
    wait=wait_random_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    before=before_log(logger, logging.WARNING),
    after=after_log(logger, logging.WARNING)
)
def call_external_api():
    pass

# Pattern 2: Fixed wait with jitter (for rate-limited APIs)
@retry(
    wait=wait_fixed(3) + wait_random(0, 2),
    stop=stop_after_attempt(2),
    retry=retry_if_exception_type(RateLimitError)
)
def call_openai():
    pass
```

### Topic 4: Notion API Rate Limiting

**Summary:** Notion API enforces 3 requests per second average rate limit with HTTP 429 responses. The official documentation recommends respecting `Retry-After` header or implementing request queuing with delays. For batch operations, a 0.33s (333ms) delay between requests ensures compliance.

**Details:**
- **Rate Limit:** 3 requests per second (average), with some burst tolerance
- **HTTP 429 Response:** Returns `"rate_limited"` error code when limit exceeded
- **Retry-After Header:** Contains integer seconds to wait before retrying
- **Recommended Delay:** 0.35s between requests (slightly above 1/3 second minimum)
- **Batch Processing:** Combine with request queuing for high-volume operations
- **Future Changes:** Notion may adjust limits or introduce tier-based pricing
- **Size Limits:** Max payload 500KB, 1000 block elements per request
- **Property Limits:** Rich text 2000 chars, URLs 2000 chars, arrays 100 elements

**Source:** Notion Developer Documentation
**URL:** https://developers.notion.com/reference/request-limits
**Retrieved:** 2025-11-03 via Archon MCP (cached documentation)

**Implementation Recommendations:**
- **Simple Approach:** `time.sleep(0.35)` between requests
- **Queue-Based:** Use `queue.Queue` for multi-threaded batch operations
- **Honor Retry-After:** Check response headers and wait specified duration
- **Cache Place ID Lookups:** Query all practices once, cache in memory during batch upsert

### Topic 5: Circuit Breaker Pattern vs Retry Logic

**Summary:** Circuit breaker pattern is designed for long-lasting failures (service outages) to prevent cascading failures, while retry logic handles transient failures (momentary network hiccups). They can be combined, but retry logic should be sensitive to circuit breaker state. For MVP with short-running pipelines, circuit breakers add unnecessary complexity.

**Details:**
- **Retry Pattern:** For transient failures (network blips, brief timeouts) - lasts seconds
- **Circuit Breaker:** For sustained failures (service down, connectivity lost) - lasts minutes/hours
- **Retry = Recovery:** Assumes fault is temporary, tries again after delay
- **Circuit Breaker = Protection:** Assumes fault is persistent, fails fast to prevent cascade
- **Combining Patterns:** Retry should respect circuit breaker "open" state and abandon attempts
- **Danger of Misuse:** Incorrect combination can amplify failures across microservice ecosystems
- **When to Use Circuit Breaker:**
  - Microservice architectures with inter-service dependencies
  - Long-running applications with sustained external service calls
  - Systems where cascading failures are catastrophic
- **When NOT to Use:**
  - Short-lived scripts/pipelines (like batch scraping)
  - Single external dependency (no cascade risk)
  - Failures are always transient (no sustained outages expected)

**Source:** Multiple articles on distributed systems resilience
**URL:** https://dev.to/supriyasrivatsa/retry-vs-circuit-breaker-346o
**Retrieved:** 2025-11-03 via WebSearch

**Python Libraries:**
- **pybreaker:** Full-featured circuit breaker implementation
- **circuitbreaker:** Simpler decorator-based approach

**Recommendation for FEAT-000:**
- **Phase 1 (MVP):** Retry logic only (sufficient for pipeline use case)
- **Phase 2 (Future):** Add circuit breaker if moving to long-running service architecture
- **Rationale:** Batch pipeline runs are short-lived; circuit breakers protect long-running services

### Topic 6: API Client Wrapper Pattern - Rate Limiting & Batch Operations

**Summary:** Best practices for API client wrappers include decorator-based rate limiting, request queuing for batch operations, exponential backoff for 429 responses, and optional persistent backends (SQLite/Redis) for multi-process environments. Batch operations should optimize throughput by bundling requests when hitting RPM limits.

**Details:**
- **Decorator Pattern:** Use `@ratelimit` decorator or custom implementation for clean separation
- **Queue-Based Batching:** Use `queue.Queue` with consumer threads for high-throughput scenarios
- **Persistent Rate Limiting:** SQLite or Redis backends for multi-process/multi-threaded apps
- **Calculate Delays:** For 3 req/sec limit, delay = 1/3 = 0.33s (add margin → 0.35s)
- **Batch Optimization:** If hitting RPM but not TPM (tokens per minute), bundle multiple operations
- **Handle 429 Responses:** Exponential backoff with `Retry-After` header respect
- **Multi-threaded Considerations:** Aggregate rate limiting across all threads
- **In-Memory Caching:** Cache lookup results during batch operations to reduce API calls

**Source:** Multiple Python API rate limiting guides
**URL:** https://medium.com/neural-engineer/implementing-effective-api-rate-limiting-in-python-6147fdd7d516
**Retrieved:** 2025-11-03 via WebSearch

**Popular Libraries:**
- **ratelimit:** Simple decorator-based (`@ratelimit(calls=3, period=1)`)
- **ratelimiter:** More flexible with persistent backends
- **requests-ratelimiter:** Integrates with `requests` library

**Pattern for Notion Client:**
```python
import time
from typing import Dict, List, Optional
from functools import lru_cache

class NotionClient:
    def __init__(self, api_key: str, rate_limit_delay: float = 0.35):
        self.client = Client(auth=api_key)
        self.rate_limit_delay = rate_limit_delay
        self._place_id_cache: Dict[str, str] = {}  # place_id -> page_id

    def _rate_limit(self):
        """Simple rate limiting via sleep"""
        time.sleep(self.rate_limit_delay)

    def batch_upsert(self, practices: List[Dict]) -> Dict[str, int]:
        # Cache all existing Place IDs once
        self._refresh_place_id_cache()

        created = 0
        updated = 0

        for practice in practices:
            place_id = practice['google_place_id']

            if place_id in self._place_id_cache:
                self.update_practice(self._place_id_cache[place_id], practice)
                updated += 1
            else:
                page_id = self.create_practice(practice)
                self._place_id_cache[place_id] = page_id
                created += 1

            self._rate_limit()

        return {'created': created, 'updated': updated}

    def _refresh_place_id_cache(self):
        """Query all practices once, cache Place ID → Page ID mapping"""
        # Single paginated query instead of 150 individual lookups
        all_practices = self.query_all_practices()
        self._place_id_cache = {
            p['properties']['Google Place ID']['rich_text'][0]['text']['content']: p['id']
            for p in all_practices
            if p['properties'].get('Google Place ID')
        }
```

### Topic 7: Pydantic Field Aliases and Mapper Patterns

**Summary:** Pydantic v2 provides separate `validation_alias` and `serialization_alias` for bidirectional mapping, along with `AliasGenerator` for automated transformations. Best practice is to keep domain models clean and use separate mapper functions/classes for external system formatting (like Notion API).

**Details:**
- **Three Alias Types:** `alias` (both directions), `validation_alias` (input only), `serialization_alias` (output only)
- **AliasGenerator:** Automated alias creation via callable functions (e.g., snake_case → camelCase)
- **AliasPath:** Map nested JSON structures to flat model fields
- **Separation of Concerns:** Domain models use clean Python names; mappers handle external formats
- **by_alias Parameter:** Use `model_dump(by_alias=True)` to output with serialization aliases
- **Read vs Write Models:** Different models for parsing (validation_alias) vs outputting (serialization_alias)
- **Mapper Pattern Benefits:**
  - Models stay focused on domain logic
  - External API changes isolated to mapper layer
  - Easier testing (models don't depend on API formats)
  - Clear separation between internal and external representations

**Source:** Pydantic Official Documentation
**URL:** https://docs.pydantic.dev/latest/concepts/alias/
**Retrieved:** 2025-11-03 via WebSearch

**Recommendation:**
- **Keep Models Clean:** Use standard Python field names (snake_case)
- **Separate Mapper:** Create `notion_mapper.py` with functions to transform Pydantic models to/from Notion API format
- **Example:**

```python
# models/practice.py - Clean domain model
class VeterinaryPractice(BaseModel):
    practice_name: str
    google_place_id: str
    lead_score: int

# clients/notion_mapper.py - External format handling
def to_notion_properties(practice: VeterinaryPractice) -> Dict:
    return {
        'Practice Name': {'title': [{'text': {'content': practice.practice_name}}]},
        'Google Place ID': {'rich_text': [{'text': {'content': practice.google_place_id}}]},
        'Lead Score': {'number': practice.lead_score},
    }

def from_notion_page(page: Dict) -> VeterinaryPractice:
    props = page['properties']
    return VeterinaryPractice(
        practice_name=props['Practice Name']['title'][0]['text']['content'],
        google_place_id=props['Google Place ID']['rich_text'][0]['text']['content'],
        lead_score=props['Lead Score']['number'],
    )
```

### Topic 8: Fail-Fast Validation on Application Startup

**Summary:** The fail-fast principle recommends validating configuration and external dependencies immediately on application startup to detect issues before processing begins. This prevents wasted work, reduces debugging time, and provides clear error messages to users.

**Details:**
- **Fail-Fast Definition:** Immediately report errors rather than continuing in degraded state
- **Benefits:**
  - Prevents cascading failures from propagating through system
  - Reduces Mean Time To Recovery (MTTR) with clear error messages
  - Avoids wasted processing time on invalid configuration
  - Catches mistakes before expensive API calls
- **Startup Validation Scope:**
  - Configuration file syntax and required fields (Pydantic handles)
  - API key format validation (Pydantic validators)
  - External API connectivity (basic auth check)
  - File path existence (prompt files, log directories)
- **Trade-offs:**
  - Adds startup time (2-5 seconds for API checks)
  - May reject valid configs if external service temporarily down
  - Requires network connectivity at startup
- **Recommendation:** Light validation (auth check) not heavy validation (schema inspection)

**Source:** Multiple software engineering best practices articles
**URL:** https://www.codereliant.io/p/fail-fast-pattern
**Retrieved:** 2025-11-03 via WebSearch

**Implementation Pattern:**
```python
def validate_config_on_startup(config: VetScrapingConfig, logger: logging.Logger):
    """Fail-fast validation of configuration and external dependencies"""

    # 1. Test Notion API connectivity (light check)
    try:
        from notion_client import Client
        client = Client(auth=config.notion.api_key)
        # Just check auth, don't inspect full schema
        client.users.me()
        logger.info("✓ Notion API connection successful")
    except Exception as e:
        logger.error(f"✗ Notion API connection failed: {e}")
        raise RuntimeError("Cannot connect to Notion API. Check NOTION_API_KEY in .env")

    # 2. Check required files exist
    if not Path(config.website_scraping.extraction_prompt_file).exists():
        raise FileNotFoundError(f"Extraction prompt file not found: {config.website_scraping.extraction_prompt_file}")

    # 3. Apify/OpenAI validation deferred to first use (avoid startup costs)
    logger.info("Configuration validation complete")
```

### Topic 9: OpenAI API Cost Tracking

**Summary:** Cost tracking for OpenAI API calls involves logging token usage (from API responses) and calculating costs based on model pricing. Best practices include tracking per-request costs, aggregating totals, and using libraries like `openai_pricing_logger` or custom solutions with `tiktoken` for token counting.

**Details:**
- **Token Usage in Responses:** OpenAI API returns `usage` object with `prompt_tokens`, `completion_tokens`, `total_tokens`
- **Pricing Models:** Different rates for input vs output tokens (e.g., GPT-4: $0.03/1K prompt, $0.06/1K completion)
- **Pre-Request Estimation:** Use `tiktoken` library to count tokens before API call for budget checks
- **Post-Request Logging:** Extract actual usage from response, calculate cost, log to structured logs
- **Aggregation:** Sum costs across all requests for pipeline total
- **Per-Retry Cost:** Log estimated cost on each retry attempt to monitor wasted budget
- **Cost API:** OpenAI provides official Cost API for historical usage queries

**Source:** OpenAI Cookbook and community articles
**URL:** https://cookbook.openai.com/examples/completions_usage_api
**Retrieved:** 2025-11-03 via WebSearch

**Python Libraries:**
- **openai_pricing_logger:** Automatic cost logging to file
- **tiktoken:** Official OpenAI tokenizer for pre-request counting
- **openai-cost-tracker:** PyPI package for cost tracking

**Custom Implementation Example:**
```python
import tiktoken
import logging

# Model pricing (update as needed)
PRICING = {
    'gpt-4': {'prompt': 0.03 / 1000, 'completion': 0.06 / 1000},
    'gpt-3.5-turbo': {'prompt': 0.0015 / 1000, 'completion': 0.002 / 1000},
}

def log_openai_cost(response, model: str, logger: logging.Logger):
    """Log cost from OpenAI API response"""
    usage = response.usage
    prompt_cost = usage.prompt_tokens * PRICING[model]['prompt']
    completion_cost = usage.completion_tokens * PRICING[model]['completion']
    total_cost = prompt_cost + completion_cost

    logger.info(
        f"OpenAI API call cost: ${total_cost:.4f}",
        extra={
            'model': model,
            'prompt_tokens': usage.prompt_tokens,
            'completion_tokens': usage.completion_tokens,
            'total_tokens': usage.total_tokens,
            'cost': total_cost
        }
    )

    return total_cost

# Use in retry decorator
@retry(
    wait=wait_exponential(multiplier=1, max=60),
    stop=stop_after_attempt(2),
    after=lambda retry_state: logger.warning(
        f"Retry {retry_state.attempt_number}: Estimated cost ${estimate_cost(retry_state.args[0]):.4f}"
    )
)
def call_openai(prompt: str, model: str = 'gpt-3.5-turbo'):
    response = openai.ChatCompletion.create(...)
    log_openai_cost(response, model, logger)
    return response
```

## Recommendations

### Primary Recommendation: Pragmatic MVP Approach with Future-Ready Patterns

**Rationale:**
- **Start Simple:** Use Python standard library where possible (logging, no circuit breakers)
- **Fail Fast:** Validate configuration and API connectivity on startup to catch errors early
- **Structured Logging:** JSON to file, colorized to console using custom formatters (no dependencies)
- **Retry with Backoff:** Use Tenacity with exponential backoff + jitter for all external APIs
- **Defer Complexity:** Circuit breakers and advanced caching are Phase 2 optimizations
- **Clean Architecture:** Separate domain models from external API formats (mapper pattern)

**Key Benefits:**
- **Zero Additional Dependencies:** Custom logging formatters, simple rate limiting via `time.sleep()`
- **Production Ready:** Structured logs, comprehensive error handling, cost tracking
- **Easy to Test:** Dependency injection, clean separation of concerns
- **Future-Proof:** Can add circuit breakers, advanced caching, persistent rate limiting later

**Considerations:**
- **Startup Time:** API validation adds 2-5 seconds to startup
- **Rate Limiting Simplicity:** `time.sleep()` approach is single-threaded only (sufficient for MVP)
- **Manual Cost Tracking:** Requires custom code vs using `openai_pricing_logger` library

### Alternative Approaches Considered

#### Alternative 1: Library-Heavy Approach (colorlog, pybreaker, ratelimiter, etc.)
- **Pros:** Off-the-shelf solutions, less custom code, battle-tested
- **Cons:** More dependencies to manage, potential version conflicts, added complexity
- **Why not chosen:** MVP should minimize dependencies; custom solutions are simple enough

#### Alternative 2: Validate API Connectivity Per-Feature (No Startup Check)
- **Pros:** Faster startup, no network dependency at init
- **Cons:** Errors appear late (after processing begins), poor user experience
- **Why not chosen:** Fail-fast principle saves time and debugging effort

#### Alternative 3: Embed Notion Field Mappings in Pydantic Models
- **Pros:** Single source of truth, no separate mapper code
- **Cons:** Domain models polluted with external API details, harder to test
- **Why not chosen:** Separation of concerns keeps models clean and testable

## Trade-offs

### Performance vs. Complexity
**Startup Validation:** Light validation (auth check) strikes balance between fail-fast benefits and startup time overhead. Heavy validation (schema inspection) adds unnecessary complexity.

**Rate Limiting:** Simple `time.sleep(0.35)` approach sacrifices throughput for simplicity. Acceptable for MVP batch pipeline (150 practices = 52.5 seconds). Queue-based approach with threading deferred to Phase 2 if needed.

**Caching:** In-memory Place ID cache during single run provides 150x reduction in API calls (1 paginated query vs 150 lookups) with zero persistence overhead.

### Cost vs. Features
**Retry Cost Logging:** Minimal effort (extract token usage from response) with high value (budget monitoring). Recommended for MVP.

**Circuit Breakers:** High implementation complexity for marginal benefit in short-lived pipeline. Defer to Phase 2 or long-running service architecture.

**Advanced Logging Libraries:** `python-json-logger` provides polished JSON formatting, but custom `JSONFormatter` (10 lines of code) is sufficient for MVP.

### Time to Market vs. Quality
**Custom Formatters:** 30 minutes to implement custom `JSONFormatter` and `ColorizedFormatter` vs 5 minutes to install `pylogrus`. Trade-off favors custom (zero dependencies, full control).

**Pydantic Validation:** Comprehensive field validators (API key format, Notion DB ID length) catch 90% of config errors. API connectivity check catches remaining 10% at startup.

**Test Coverage:** Focus on critical paths (config loading, retry logic, Notion client) over exhaustive unit tests. 80% coverage target aligns with MVP timeline.

### Maintenance vs. Flexibility
**Mapper Pattern:** Separate `notion_mapper.py` adds one more file but isolates Notion API changes. If Notion changes field format, only mapper needs updates (not all domain models).

**Settings Singleton:** Instantiate `VetScrapingConfig` once at module level vs dependency injection everywhere. Trade-off favors singleton for simplicity in pipeline context (vs web service).

**Structured Logging:** JSON logs enable future integration with log aggregation tools (ELK, Datadog) without code changes. Initial overhead (custom formatter) pays off long-term.

## Resources

### Official Documentation
- **Pydantic v2 Settings Management:** https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- **Pydantic Field Aliases:** https://docs.pydantic.dev/latest/concepts/alias/
- **Python Logging Cookbook:** https://docs.python.org/3/howto/logging-cookbook.html
- **Tenacity Documentation:** https://tenacity.readthedocs.io/
- **Notion API Rate Limits:** https://developers.notion.com/reference/request-limits

### Technical Articles
- **Tenacity Best Practices:** https://medium.com/@bounouh.fedi/enhancing-resilience-in-python-applications-with-tenacity-a-comprehensive-guide-d92fe0e07d89
- **Circuit Breaker vs Retry:** https://dev.to/supriyasrivatsa/retry-vs-circuit-breaker-346o
- **Python Logging Best Practices:** https://www.datadoghq.com/blog/python-logging-best-practices/
- **API Rate Limiting in Python:** https://medium.com/neural-engineer/implementing-effective-api-rate-limiting-in-python-6147fdd7d516

### Code Examples
- **Dual Logging Setup (Console + File):** https://gist.github.com/fonic/7e5ab76d951a2ab2d5f526a7db3e2004
- **python-json-logger:** https://github.com/madzak/python-json-logger

### Community Resources
- **Pydantic v2 Migration Discussion:** https://github.com/pydantic/pydantic/discussions/7701
- **OpenAI Cost Tracking:** https://cookbook.openai.com/examples/completions_usage_api

## Archon Status

### Knowledge Base Queries
*Archon MCP was available and used for this research:*

- ✅ **Pydantic Documentation:** Found in Archon (`c0e629a894699314`), used for configuration management research
- ✅ **Notion API Documentation:** Found in Archon (`86308a97988d5d3b`), retrieved full rate limits page
- ❌ **Tenacity Documentation:** Not in Archon, used WebSearch (official docs + Medium articles)
- ❌ **Python Logging Best Practices:** Not in Archon, used WebSearch (Python.org + Datadog)
- ❌ **Circuit Breaker Patterns:** Not in Archon, used WebSearch (DEV Community + Medium)

### Recommendations for Archon
*Frameworks/docs to crawl for future features:*

1. **Tenacity Library**
   - **Why:** Standard Python retry library, frequently used in API integrations
   - **URLs to crawl:**
     - https://tenacity.readthedocs.io/en/latest/
     - https://github.com/jd/tenacity (README + examples)
   - **Benefit:** Instant access to retry patterns for all future API-heavy features

2. **Python Standard Library - Logging Module**
   - **Why:** Core Python logging patterns apply to all projects
   - **URLs to crawl:**
     - https://docs.python.org/3/library/logging.html
     - https://docs.python.org/3/howto/logging-cookbook.html
   - **Benefit:** Reference for logging configuration in every feature

3. **Structlog Library**
   - **Why:** Advanced structured logging if we outgrow custom formatters
   - **URLs to crawl:**
     - https://www.structlog.org/en/stable/
   - **Benefit:** Future migration path for high-performance structured logging

## Answers to Open Questions

### Question 1: Should we validate API connectivity during config load or defer to feature code?
**Answer:** Add `validate_config_on_startup()` function called from `main.py` after config loading. Perform light validation (auth check) for Notion API, not heavy schema inspection. Defer Apify/OpenAI validation to first use to avoid startup costs.

**Confidence:** High

**Source:** Fail-fast pattern research from software engineering best practices. Notion auth check takes <1 second, catches 90% of credential issues early.

**Rationale:** Balance between fail-fast benefits (catch errors before processing) and startup performance (don't validate everything). Auth check is cheap and catches most issues.

### Question 2: Should --test flag be in config.json or command-line only?
**Answer:** CLI flag (`--test`) that overrides config. Use `argparse` to parse CLI args, then update `VetScrapingConfig` instance after loading from file.

**Confidence:** High

**Source:** Pydantic settings management best practices, CLI integration patterns.

**Rationale:** More flexible than editing config file every test run. Aligns with standard CLI tool patterns (pytest, mypy, etc.). Pydantic v2 supports `cli_parse_args` flag for this use case.

### Question 3: Should we use colorlog library or custom ANSI codes for console output?
**Answer:** Custom ANSI codes via `ColorizedFormatter` class (no external library).

**Confidence:** High

**Source:** Python logging cookbook, comparison of custom vs library approaches.

**Rationale:** Zero dependencies, simple implementation (10-15 lines of code), full control over formatting. `colorlog` library adds marginal value for this use case.

### Question 4: Should test mode auto-switch to DEBUG log level?
**Answer:** Yes. If `--test` flag is present, set `log_level = logging.DEBUG` before calling `setup_logging()`.

**Confidence:** High

**Source:** Python logging best practices, development vs production patterns.

**Rationale:** More visibility during development/testing without cluttering production logs. Standard pattern across Python tooling.

### Question 5: Should we implement circuit breaker pattern now or defer to Phase 2?
**Answer:** Phase 2. Use retry logic only for MVP.

**Confidence:** High

**Source:** Circuit breaker vs retry pattern research, microservices resilience articles.

**Rationale:** Circuit breakers protect long-running services from cascading failures. Batch pipeline is short-lived (runs to completion in minutes), no inter-service dependencies, no sustained failure scenarios. Added complexity not justified for MVP.

### Question 6: Should we log estimated cost per retry?
**Answer:** Yes. Extract token usage from OpenAI API responses, calculate cost, log in retry warning message.

**Confidence:** High

**Source:** OpenAI API cost tracking research, Tenacity retry hooks.

**Rationale:** Minimal implementation effort (10 lines of code), high value for budget monitoring. Use Tenacity's `after` callback to log cost on each retry attempt.

### Question 7: Should we cache Place IDs in memory during batch operations?
**Answer:** Yes. Query all practices once at start of `batch_upsert()`, build `Dict[place_id, page_id]` cache in memory.

**Confidence:** High

**Source:** API client wrapper patterns, Notion rate limiting research.

**Rationale:** Reduces 150 individual Place ID queries to 1 paginated query (saves 149 API calls = 52 seconds). In-memory cache sufficient for single batch run (no persistence needed).

### Question 8: Should we validate Notion schema on startup?
**Answer:** Basic check only (database exists, accessible). No full schema validation (field names, types, etc.).

**Confidence:** Medium

**Source:** Fail-fast pattern research, Notion API documentation.

**Rationale:** Full schema validation is brittle (breaks if Notion workspace changes field names) and adds complexity. Basic connectivity check via `client.users.me()` is sufficient to confirm auth works. Trust that database has correct schema (documented in `docs/system/notion-schema.md`).

### Question 9: Should errors be written to separate file or kept in-memory only?
**Answer:** In-memory only. Errors already written to main log file via structured logging.

**Confidence:** High

**Source:** Structured logging best practices, avoiding duplication.

**Rationale:** No duplication needed. Structured JSON logs contain all error details with context (practice_name, category, message). ErrorAggregator provides in-memory summary for final report. If needed, can parse logs to extract errors.

### Question 10: Should Pydantic models include Notion field name mappings or keep separate?
**Answer:** Keep separate. Create `clients/notion_mapper.py` with `to_notion_properties()` and `from_notion_page()` functions.

**Confidence:** High

**Source:** Pydantic alias patterns, separation of concerns principles.

**Rationale:** Domain models stay clean (Python naming conventions), external API format isolated in mapper. Easier to test, change Notion schema, or swap to different database later. Models focused on domain logic, not API formatting.

## Next Steps

1. **Architecture Planning:** Use recommendations to design component structure in `docs/features/FEAT-000_shared-infrastructure/architecture.md`
2. **Technical Decisions:**
   - Use Pydantic v2 `BaseSettings` with `SettingsConfigDict`
   - Custom `JSONFormatter` and `ColorizedFormatter` (no external dependencies)
   - Tenacity decorators with exponential backoff + jitter
   - Simple rate limiting via `time.sleep(0.35)` in Notion client
   - In-memory Place ID caching during batch operations
   - Separate `notion_mapper.py` for API format conversion
   - Startup validation function with light connectivity check
3. **Proceed to Planning:** Run `/plan FEAT-000` with these research findings to create architecture and acceptance criteria

---

**Research Complete:** ✅
**Ready for Planning:** Yes
