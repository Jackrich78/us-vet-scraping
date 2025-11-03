# Testing Strategy: Shared Infrastructure

**Feature ID:** FEAT-000
**Status:** Draft
**Last Updated:** 2025-11-03

## Overview

Shared infrastructure requires comprehensive testing to ensure reliability across all dependent features. Testing focuses on configuration validation, logging correctness, error handling resilience, and Notion integration accuracy. The strategy emphasizes unit testing for individual components, integration testing for component interactions, and manual testing for environment-specific behaviors.

## Test Levels

### Unit Tests (Primary Focus)

**Scope:** Individual functions and classes in isolation
**Framework:** pytest with fixtures and mocking
**Coverage Goal:** >90% for all shared infrastructure modules

**Test Files:**
- `tests/unit/test_config.py` - Configuration loading and validation
- `tests/unit/test_logging.py` - Logging functionality and ANSI handling
- `tests/unit/test_retry.py` - Retry logic and exponential backoff
- `tests/unit/test_notion_mapper.py` - Notion data mapping utilities
- `tests/unit/test_cache.py` - Place ID caching logic

**Key Testing Patterns:**
- Use `pytest.fixture` for configuration and logger setup
- Mock external dependencies (API calls, file I/O)
- Parametrize tests for multiple scenarios
- Test both success and failure paths
- Validate error messages and types

### Integration Tests

**Scope:** Component interactions and end-to-end flows
**Framework:** pytest with real file system and limited mocking
**Coverage Goal:** >70% for integration scenarios

**Test Files:**
- `tests/integration/test_config_logging.py` - Config initialization with logging setup
- `tests/integration/test_retry_logging.py` - Retry logic with cost tracking logs
- `tests/integration/test_notion_integration.py` - Full Notion mapping and validation flow

**Key Testing Patterns:**
- Use temporary directories for `.env` files and logs
- Test real file I/O with cleanup fixtures
- Validate cross-component interactions
- Test environment variable precedence
- Verify log output in files and console

### End-to-End Tests

**Scope:** Complete workflows in realistic environments
**Framework:** pytest with minimal mocking
**Coverage Goal:** Key user scenarios covered

**Test Files:**
- `tests/e2e/test_batch_operation.py` - Simulate batch processing with caching and retries

**Key Testing Patterns:**
- Use test mode flag to avoid real API calls
- Validate Place ID caching reduces redundant operations
- Test full error handling and logging flow
- Measure performance under realistic load

### Manual Testing

**Scope:** Environment-specific behaviors and visual validation
**Responsibility:** Developer verification before PR
**Documented in:** `manual-test.md`

**Key Scenarios:**
- ANSI color display in different terminals
- Log file output without color codes
- CI/CD environment logging
- Performance profiling under load

## Test File Structure

```
tests/
├── unit/
│   ├── __init__.py
│   ├── conftest.py                 # Shared fixtures for unit tests
│   ├── test_config.py              # Configuration tests
│   ├── test_logging.py             # Logging tests
│   ├── test_retry.py               # Retry logic tests
│   ├── test_notion_mapper.py       # Notion mapper tests
│   └── test_cache.py               # Caching tests
├── integration/
│   ├── __init__.py
│   ├── conftest.py                 # Shared fixtures for integration tests
│   ├── test_config_logging.py     # Config + logging integration
│   ├── test_retry_logging.py      # Retry + logging integration
│   └── test_notion_integration.py # Notion full flow
├── e2e/
│   ├── __init__.py
│   ├── conftest.py                 # Shared fixtures for e2e tests
│   └── test_batch_operation.py    # End-to-end batch processing
└── fixtures/
    ├── sample_env.txt              # Sample .env file for testing
    ├── sample_places_response.json # Sample Google Places API response
    └── sample_notion_schema.json   # Sample Notion database schema
```

## Coverage Goals

### By Module

| Module | Target Coverage | Priority |
|--------|----------------|----------|
| `config.py` | >95% | Critical |
| `logging.py` | >90% | Critical |
| `retry.py` | >90% | Critical |
| `notion_mapper.py` | >90% | Critical |
| `cache.py` | >85% | High |
| Integration flows | >70% | Medium |

### By Test Type

| Test Type | Percentage of Total | Estimated Count |
|-----------|---------------------|-----------------|
| Unit Tests | ~70% | 50-60 tests |
| Integration Tests | ~20% | 15-20 tests |
| E2E Tests | ~10% | 5-10 tests |

## Key Test Scenarios

### Configuration Testing

1. **Valid configuration loading** - All fields present and correct types
2. **Missing required fields** - Clear validation errors raised
3. **Invalid types** - Type coercion and validation errors
4. **Default values** - Optional fields use correct defaults
5. **Nested models** - Complex configuration validates correctly
6. **Environment variable precedence** - Env vars override defaults

### Logging Testing

1. **ANSI console output** - Colors display correctly in terminal
2. **File output without ANSI** - Log files are plain text
3. **Test mode debug level** - `--test` flag enables DEBUG
4. **Cost tracking** - API cost estimates logged correctly
5. **CI/CD environment** - ANSI disabled automatically
6. **Log format** - Timestamp, level, message present

### Retry Logic Testing

1. **Exponential backoff timing** - 1s, 2s, 4s, 8s, 16s intervals
2. **Max retry limit** - Stops after 5 attempts
3. **Transient error retry** - HTTP 429, 503, timeouts retried
4. **Non-retryable errors** - HTTP 400, 401, 403 not retried
5. **Cost logging per retry** - Each attempt logs cost
6. **Error propagation** - Final error includes retry context

### Notion Mapping Testing

1. **Complete API response** - All fields mapped correctly
2. **Partial API response** - Missing fields handled gracefully
3. **Malformed data** - Errors caught with field context
4. **Schema validation** - Expected properties verified
5. **Null/empty handling** - Appropriate defaults applied
6. **Utility independence** - Mapper works without model coupling

### Caching Testing

1. **Cache hit** - Duplicate Place IDs use cached data
2. **Cache miss** - New Place IDs fetch fresh data
3. **Cache performance** - Lookup overhead <1ms
4. **Cache memory** - Usage under 10MB for 1000 entries
5. **Cache clearing** - Batch operation ends clear cache

## Testing Tools and Libraries

### Core Testing Framework
- **pytest** - Test runner and framework
- **pytest-cov** - Coverage reporting
- **pytest-mock** - Mocking utilities
- **pytest-timeout** - Test timeout enforcement

### Mocking and Fixtures
- **unittest.mock** - Standard library mocking
- **pytest fixtures** - Shared test setup
- **tmp_path** - Temporary directory fixture
- **monkeypatch** - Environment variable patching

### Assertions and Validation
- **pytest assertions** - Rich assertion output
- **pydantic validation** - Configuration validation testing
- **re** module - Log format validation

### Performance Testing
- **time** module - Timing measurements
- **memory_profiler** - Memory usage tracking (optional)

## Test Data Management

### Fixtures Location
`tests/fixtures/` contains:
- Sample `.env` files for various configurations
- Mock API responses (Places API, Notion API)
- Sample schemas for validation testing

### Test Data Principles
1. **Deterministic** - Tests produce consistent results
2. **Isolated** - No shared state between tests
3. **Realistic** - Data resembles production scenarios
4. **Minimal** - Only include data needed for test
5. **Documented** - Comments explain fixture purpose

## Continuous Integration

### CI Pipeline Testing
1. Run all tests on every PR
2. Enforce >90% coverage threshold
3. Run tests across Python 3.9, 3.10, 3.11
4. Validate linting and formatting (black, isort, flake8)
5. Generate and publish coverage reports

### Test Execution Order
1. Linting and formatting checks
2. Unit tests (parallel execution)
3. Integration tests (serial execution)
4. E2E tests (serial execution)
5. Coverage report generation

## Manual Testing Requirements

### Developer Verification
Before submitting PR, developer must:
1. Test ANSI colors in their terminal
2. Verify log files are plain text
3. Run application with `--test` flag
4. Profile performance with realistic data
5. Test configuration with missing/invalid values

### Pre-Deployment Checklist
- All automated tests pass
- Manual testing completed and documented
- Performance benchmarks met
- No regression in coverage percentage
- Documentation updated for new features

## Performance Benchmarks

### Target Metrics
- Configuration load: <100ms
- Logger initialization: <50ms
- Log entry creation: <5ms per entry
- Cache lookup: <1ms per lookup
- Notion mapper: <10ms per transformation
- Retry backoff calculation: <1ms

### Performance Testing Strategy
1. Use `pytest-benchmark` for micro-benchmarks
2. Measure under realistic load (100+ operations)
3. Compare against baseline after changes
4. Fail CI if >20% performance regression

## Test Maintenance

### Regular Updates
- Review and update fixtures quarterly
- Add tests for new edge cases discovered
- Refactor duplicate test code
- Update mocks when external APIs change
- Maintain >90% coverage as code evolves

### Documentation
- Document complex test scenarios with comments
- Maintain README in tests/ directory
- Update this strategy document when approach changes
- Link acceptance criteria to specific tests

## Acceptance Criteria Coverage

| AC ID | Test File | Test Function |
|-------|-----------|---------------|
| AC-FEAT-000-001 | test_config.py | test_env_variable_loading |
| AC-FEAT-000-002 | test_config.py | test_nested_configuration |
| AC-FEAT-000-003 | test_config.py | test_configuration_validation |
| AC-FEAT-000-005 | test_logging.py | test_ansi_console_logging |
| AC-FEAT-000-006 | test_logging.py | test_file_logging_no_ansi |
| AC-FEAT-000-007 | test_logging.py | test_test_mode_debug |
| AC-FEAT-000-008 | test_logging.py | test_cost_tracking |
| AC-FEAT-000-010 | test_retry.py | test_exponential_backoff |
| AC-FEAT-000-011 | test_retry.py | test_cost_logging_per_retry |
| AC-FEAT-000-012 | test_retry.py | test_error_propagation |
| AC-FEAT-000-013 | test_retry.py | test_non_retryable_errors |
| AC-FEAT-000-015 | test_notion_mapper.py | test_schema_validation |
| AC-FEAT-000-016 | test_notion_mapper.py | test_places_to_notion_mapping |
| AC-FEAT-000-017 | test_notion_mapper.py | test_malformed_data_handling |
| AC-FEAT-000-020 | test_cache.py | test_place_id_caching |
| AC-FEAT-000-021 | test_cache.py | test_cache_performance |

*Additional mappings to be completed during test implementation*

## Risk Mitigation

### High-Risk Areas
1. **ANSI code handling** - May fail in unusual terminal environments
2. **Retry timing** - Timing tests can be flaky
3. **Environment variables** - Test isolation critical
4. **File I/O** - Race conditions in parallel tests

### Mitigation Strategies
1. Use environment detection for ANSI (test across terminals)
2. Use mocked time for retry tests (avoid real sleeps)
3. Use pytest fixtures for clean env var setup/teardown
4. Use tmp_path fixture and avoid shared file paths

## Success Criteria

Testing is complete when:
- All acceptance criteria have corresponding tests
- >90% code coverage achieved for shared infrastructure
- All tests pass in CI/CD pipeline
- Manual testing checklist completed and documented
- Performance benchmarks meet target metrics
- No critical bugs found in code review
