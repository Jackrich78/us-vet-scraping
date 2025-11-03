# Acceptance Criteria (Global)

**Purpose:** Central repository of all acceptance criteria across features

**Format:** AC-FEAT-XXX-### for feature-specific criteria, AC-GLOBAL-### for project-wide standards

---

## Global Standards

### AC-GLOBAL-001: Documentation Completeness
All features must have complete planning documentation before implementation (PRD, research, architecture, acceptance, testing, manual-test).

### AC-GLOBAL-002: Template Compliance
All planning documents must follow templates exactly with all required sections present.

### AC-GLOBAL-003: Word Limits
Planning documents must respect word limits: PRD ≤800 words, research ≤1000 words, others ≤800 words.

### AC-GLOBAL-004: Test Stubs Required
All features must have test stubs generated in tests/ directory with TODO comments and acceptance criteria references.

### AC-GLOBAL-005: Reviewer Validation
All planning workflows must pass Reviewer agent validation before being marked complete.

### AC-GLOBAL-006: No Placeholders
Planning documents must not contain TODO, TBD, or placeholder content (except in test stubs).

### AC-GLOBAL-007: Given/When/Then Format
All acceptance criteria must use Given/When/Then format for testability.

---

## Feature-Specific Criteria

*Feature acceptance criteria will be appended here by the Planner agent during `/plan` command*

### FEAT-001: Example Feature

**AC-FEAT-001-001:** Example Documentation Complete
Given a developer is using the AI workflow template, when they review FEAT-001 example feature, then all 6 planning documents are present and follow templates.

**AC-FEAT-001-002:** Templates Demonstrated
Given an AI agent is generating feature documentation, when the agent references FEAT-001 as an example, then the agent can replicate the structure and quality.

---

*New feature criteria will be appended here automatically during planning*

---

## FEAT-000: Shared Infrastructure

### AC-FEAT-000-001: Environment Variable Loading
**Given** a `.env` file with required configuration variables
**When** the application initializes
**Then** all configuration values are loaded correctly with proper type coercion
**And** missing required fields raise clear validation errors

### AC-FEAT-000-002: Nested Configuration Models
**Given** complex configuration with API keys and Notion settings
**When** configuration is loaded
**Then** nested models validate correctly (e.g., `notion.api_key`, `notion.database_id`)
**And** invalid nested values raise specific field errors

### AC-FEAT-000-003: Configuration Validation
**Given** invalid configuration values (wrong type, missing required fields)
**When** application attempts to load configuration
**Then** Pydantic validation errors are raised with clear field names
**And** error messages indicate expected type and constraints

### AC-FEAT-000-005: ANSI Console Logging
**Given** the application is running in an interactive terminal
**When** logs are emitted at different severity levels (DEBUG, INFO, WARNING, ERROR)
**Then** each level displays with appropriate ANSI color (blue, green, yellow, red)
**And** log format includes timestamp, level, and message

### AC-FEAT-000-006: File Logging Without ANSI
**Given** logs are written to a file
**When** log entries are created
**Then** ANSI color codes are stripped from file output
**And** logs remain readable in plain text editors

### AC-FEAT-000-007: Test Mode Debug Logging
**Given** the application is started with `--test` flag
**When** logging is initialized
**Then** log level automatically switches to DEBUG
**And** debug messages are visible in output

### AC-FEAT-000-008: Cost Tracking in Logs
**Given** an API call with known cost estimation
**When** the call is logged
**Then** log entry includes estimated cost in USD
**And** retry attempts log cumulative cost

### AC-FEAT-000-010: Exponential Backoff Retry
**Given** a transient API failure (HTTP 429, 503, or timeout)
**When** retry logic is triggered
**Then** requests are retried with exponential backoff (1s, 2s, 4s, 8s, 16s)
**And** maximum retry limit (5 attempts) is respected

### AC-FEAT-000-011: Cost Logging per Retry
**Given** a retryable API call that fails and retries
**When** each retry attempt occurs
**Then** estimated cost is logged for each attempt
**And** cumulative cost is trackable across retries

### AC-FEAT-000-013: Non-Retryable Error Handling
**Given** a non-retryable error (HTTP 400, 401, 403)
**When** the error occurs
**Then** no retry attempts are made
**And** error is raised immediately with clear categorization

### AC-FEAT-000-015: Notion Schema Validation
**Given** a Notion database connection
**When** the connection is initialized
**Then** expected properties are validated to exist
**And** missing critical properties raise clear errors

### AC-FEAT-000-016: Places API to Notion Mapping
**Given** a Google Places API response
**When** data is mapped to Notion format
**Then** all fields are transformed correctly (name, address, phone, hours, etc.)
**And** missing fields are handled gracefully with null/empty values

### AC-FEAT-000-017: Malformed Data Handling
**Given** malformed or unexpected data from Places API
**When** mapping to Notion format
**Then** errors are caught and logged with specific field context
**And** partial data is preserved where possible

### AC-FEAT-000-020: Place ID Caching
**Given** batch processing of multiple places
**When** the same Place ID is encountered multiple times
**Then** cached data is used instead of making redundant API calls
**And** cache is cleared at end of batch operation

### AC-FEAT-000-021: Cache Performance
**Given** a batch operation with 100 places, 20% duplicates
**When** Place ID caching is enabled
**Then** API calls are reduced by ~20%
**And** cache lookup overhead is less than 1ms per lookup

### AC-FEAT-000-022: Configuration Load Performance
**Given** application startup with valid configuration
**When** configuration is loaded and validated
**Then** total load time is less than 100ms
**And** no blocking I/O occurs during load

### AC-FEAT-000-023: Logging Performance Overhead
**Given** high-frequency logging (100+ log entries per second)
**When** logs are emitted
**Then** logging overhead is less than 5ms per entry
**And** application performance is not degraded

---

**Note:** This file is append-only. Criteria are added by agents during `/plan` command and should not be manually edited or removed.

**Last Updated:** 2025-11-03
