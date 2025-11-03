# Architecture Decision: Shared Infrastructure

**Feature ID:** FEAT-000
**Status:** Proposed
**Last Updated:** 2025-11-03
**Word Count:** ~750

## Problem Statement

The US Vet Scraping project requires foundational infrastructure components to support reliable data acquisition, processing, and storage. Core needs include: configuration management with environment-specific settings, structured logging with cost tracking for API calls, standardized error handling with categorization, rate limiting to respect external API quotas, and Notion integration utilities for data persistence.

Without this shared infrastructure, each feature would implement its own configuration, logging, and error handling patterns, leading to inconsistency, duplication, and maintenance overhead. The infrastructure must support batch processing, test mode operation, and cost visibility while remaining simple and maintainable.

## Options Analysis

### Option 1: Minimal Custom Implementation

**Description:** Build lightweight custom solutions using standard library and Pydantic for configuration. Implement custom ANSI logging, simple retry logic with exponential backoff, and basic Notion utilities.

**Pros:**
- No external dependencies beyond Pydantic and standard library
- Full control over behavior and customization
- Lightweight with minimal overhead
- Easy to understand and modify
- Tailored exactly to project needs

**Cons:**
- More initial development effort
- Need to implement retry logic from scratch
- Custom ANSI codes require manual maintenance
- Testing burden falls entirely on project
- May miss edge cases that libraries handle

**Key Dependencies:** pydantic-settings, python-dotenv, standard library only

**Estimated Effort:** 3-4 days for initial implementation + testing

### Option 2: Library-Heavy Approach

**Description:** Use established libraries for each concern: python-decouple or dynaconf for config, structlog or loguru for logging, tenacity for retries, circuit breaker library (pybreaker), and full Notion SDK wrapper.

**Pros:**
- Battle-tested solutions with community support
- Rich feature sets out of the box
- Well-documented with examples
- Faster initial development
- Handles edge cases and corner cases

**Cons:**
- Dependency bloat (10+ additional packages)
- Learning curve for each library's API
- Potential version conflicts
- Over-engineered for simple use cases
- Harder to customize specific behaviors
- Lock-in to library conventions

**Key Dependencies:** python-decouple, structlog, tenacity, pybreaker, notion-client extensions

**Estimated Effort:** 1-2 days for integration + learning curve

### Option 3: Hybrid Approach (Recommended)

**Description:** Combine Pydantic BaseSettings for config with selective use of proven utilities. Use Pydantic validation, custom ANSI logging (no colorlog), basic retry with exponential backoff (no full tenacity), defer circuit breaker to Phase 2, and custom Notion mapper utility.

**Pros:**
- Balanced between control and convenience
- Minimal dependencies (pydantic-settings only)
- Pydantic validation is robust and well-known
- Custom components where project-specific logic needed
- Can add libraries later if requirements evolve
- Clear upgrade path

**Cons:**
- Still requires implementing retry logic
- Custom logging needs testing across environments
- Circuit breaker deferred means less resilience initially
- Notion mapper may need iteration

**Key Dependencies:** pydantic-settings, python-dotenv, requests (already needed for APIs)

**Estimated Effort:** 2-3 days for implementation + testing

## Comparison Matrix

| Criteria | Option 1: Minimal | Option 2: Library-Heavy | Option 3: Hybrid (Rec) |
|----------|-------------------|-------------------------|------------------------|
| **Feasibility** | High - standard patterns | High - proven libraries | High - best of both |
| **Performance** | Excellent - minimal overhead | Good - library overhead | Excellent - lean stack |
| **Maintainability** | Good - simple code, more tests | Fair - dependency updates | Excellent - clear patterns |
| **Cost** | Low - no licenses | Low - OSS libraries | Low - minimal deps |
| **Complexity** | Medium - custom logic | Low - library abstractions | Medium-Low - selective |
| **Community Support** | Low - custom solutions | High - library ecosystems | Medium - Pydantic strong |
| **Integration Effort** | Medium - build from scratch | Low - plug and play | Medium - targeted building |

## Recommendation

**Selected Approach:** Option 3 - Hybrid Approach

**Rationale:**
1. **Pydantic Alignment:** BaseSettings provides robust validation, environment variable parsing, and type safety without additional dependencies
2. **Simplicity:** Custom ANSI logging and retry logic are straightforward to implement and test
3. **Flexibility:** Can add libraries incrementally if needs evolve (e.g., circuit breaker in Phase 2)
4. **Maintainability:** Fewer dependencies means less update churn and clearer ownership
5. **Cost Visibility:** Custom logging allows precise cost tracking tailored to Google Places API pricing

**Key Decisions from Research:**
- Use Pydantic v2 `BaseSettings` with `pydantic-settings` package for configuration
- Implement custom ANSI codes for console logging (no colorlog dependency)
- CLI flag `--test` controls test mode (not in config.json)
- Auto-switch to DEBUG logging level when `--test` flag active
- Defer circuit breaker implementation to Phase 2
- Log estimated cost per retry attempt for visibility
- Cache Place IDs in memory during batch operations to avoid duplicate lookups
- Light schema validation on Notion connection (verify expected properties exist, not full schema enforcement)
- Track errors in-memory only (already captured in logs)
- Create separate `notion_mapper.py` utility module (not embedded in models)

**Trade-offs Accepted:**
- More initial development effort vs. library integration speed
- Custom retry logic vs. tenacity's advanced features
- Deferred circuit breaker vs. immediate fault tolerance
- In-memory Place ID cache vs. persistent cache (sufficient for batch runs)

## Spike Plan

### Goal
Validate that Pydantic BaseSettings handles all configuration requirements and custom ANSI logging works across environments (terminal, log files, CI/CD).

### Steps

**Step 1: Pydantic BaseSettings Validation (4 hours)**
- Create `config.py` with BaseSettings class for all environment variables
- Test `.env` file loading and validation
- Verify type coercion (integers, booleans, lists)
- Test missing required fields raise clear errors
- Validate nested configuration models (API keys, Notion config)

**Success Criteria:** All config scenarios load correctly with proper validation errors.

**Step 2: Custom ANSI Logging Prototype (3 hours)**
- Implement ANSI color codes for console output (INFO=green, WARNING=yellow, ERROR=red, DEBUG=blue)
- Test logging to console, file, and CI/CD environments
- Verify ANSI codes stripped when writing to files
- Test `--test` flag auto-switches to DEBUG level
- Validate log format includes timestamp, level, message, optional cost

**Success Criteria:** Logs are readable in all environments with appropriate colors/formatting.

**Step 3: Retry Logic Implementation (3 hours)**
- Build exponential backoff retry decorator
- Test with simulated API failures
- Verify cost logging on each retry attempt
- Test max retry limits and timeout handling
- Validate error propagation after exhausting retries

**Success Criteria:** Retry logic handles transient failures gracefully with cost visibility.

**Step 4: Notion Mapper Utility (4 hours)**
- Create `notion_mapper.py` with helper functions for data transformation
- Test mapping Places API response to Notion properties
- Validate light schema check (expected properties exist)
- Test error handling for malformed data
- Verify no full schema enforcement overhead

**Success Criteria:** Mapper transforms data correctly with clear errors on schema mismatch.

**Step 5: Integration Testing (2 hours)**
- Test all components working together in realistic scenario
- Run with `--test` flag to verify test mode behavior
- Validate Place ID cache reduces redundant API calls
- Test configuration loading in different environments
- Measure performance impact of logging and validation

**Success Criteria:** Components integrate seamlessly with acceptable performance overhead (<10ms per operation).

### Total Time Estimate
16 hours (2 days) for complete spike validation.

### Success Metrics
- All configuration scenarios pass validation
- Logging works correctly in 3+ environments
- Retry logic reduces transient failures by >80%
- Notion mapper handles real API responses without errors
- Performance overhead remains under 10ms per operation

## Open Questions

1. Should Place ID cache persist across script runs, or is in-memory sufficient for current use cases?
2. What's the threshold for adding circuit breaker in Phase 2 (e.g., >5 consecutive failures)?
3. Should cost tracking include only API calls, or also Notion write operations?
4. Is light schema validation sufficient, or will full schema enforcement be needed later?

## Next Steps

1. Execute spike plan to validate architecture decisions
2. Implement core components based on spike learnings
3. Create comprehensive test suite for shared infrastructure
4. Document usage examples for other features to consume
5. Plan Phase 2 enhancements (circuit breaker, persistent cache)
