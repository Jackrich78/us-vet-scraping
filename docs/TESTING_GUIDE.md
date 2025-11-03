# Testing Guide - How to Run Tests

**For:** Non-technical users and developers
**Purpose:** Simple guide to running and understanding tests
**Last Updated:** 2025-11-03

---

## What Are These Tests?

Think of tests as **automatic quality checks** that verify the code works correctly. They're like having a robot assistant that:
- Checks if the configuration loads properly
- Verifies logging works as expected
- Ensures data is mapped correctly to Notion
- Catches bugs before they cause problems

**We have 76 automated tests that run in ~0.06 seconds!**

---

## Quick Start: Running All Tests

### 1. Activate Your Environment (One Time Setup)

```bash
# Make sure you're in the project directory
cd /path/to/us_vet_scraping

# Activate the virtual environment
source venv/bin/activate  # On Mac/Linux
# OR
venv\Scripts\activate     # On Windows
```

### 2. Run All Tests

```bash
pytest tests/
```

**Expected output:**
```
============================== 76 passed in 0.06s ==============================
```

✅ **Success!** All tests passed. The code is working correctly.

---

## Understanding Test Results

### ✅ All Tests Pass
```
============================== 76 passed in 0.06s ==============================
```
**Meaning:** Everything works! Safe to continue development.

### ❌ Some Tests Fail
```
========================= 74 passed, 2 failed in 0.10s =========================
```
**Meaning:** Something broke. Look at the error messages to see what went wrong.

### ⚠️ Tests Have Errors
```
========================= 74 passed, 2 errors in 0.10s =========================
```
**Meaning:** Tests couldn't run properly. Usually a setup issue (missing fixtures, import errors).

---

## Running Specific Test Types

### Run Only Fast Unit Tests (most common)
```bash
pytest tests/unit/ -v
```
**What it does:** Tests individual components in isolation (config, logging, etc.)
**When to use:** After making small code changes
**Speed:** Very fast (~0.03 seconds)

### Run Integration Tests
```bash
pytest tests/integration/ -v
```
**What it does:** Tests how components work together (config + logging, retry + logging)
**When to use:** After changing how systems interact
**Speed:** Fast (~0.02 seconds)

### Run End-to-End Tests
```bash
pytest tests/e2e/ -v
```
**What it does:** Tests complete workflows from start to finish
**When to use:** Before committing major features
**Speed:** Moderate (~0.01 seconds)

---

## Useful Testing Commands

### Show More Details
```bash
pytest tests/ -v
```
Shows each test name as it runs. Good for seeing progress.

### Stop on First Failure
```bash
pytest tests/ -x
```
Stops immediately when a test fails. Useful for debugging.

### Run Only Tests Matching a Name
```bash
pytest tests/ -k "config"
```
Runs only tests with "config" in their name.

### Show Test Coverage
```bash
pytest tests/ --cov=src --cov-report=html
```
Creates a report showing which code is tested. Open `htmlcov/index.html` to view.

### Run in Quiet Mode (Less Output)
```bash
pytest tests/ -q
```
Shows only summary, not each test name.

---

## Test Organization

Our tests are organized by **how much they test**:

```
tests/
├── unit/              ← Test individual pieces (fast)
│   ├── test_config.py           # Configuration loading
│   ├── test_logging.py          # Logging functionality
│   ├── test_cache.py            # Caching logic
│   ├── test_retry.py            # Retry mechanisms
│   └── test_notion_mapper.py    # Notion data mapping
│
├── integration/       ← Test components together (medium)
│   ├── test_config_logging.py   # Config + Logging
│   ├── test_retry_logging.py    # Retry + Logging
│   └── test_notion_integration.py  # Full Notion flow
│
└── e2e/              ← Test complete workflows (comprehensive)
    └── test_batch_operation.py  # Full batch processing
```

---

## When to Run Tests

### Before Every Commit
```bash
pytest tests/ -q
```
**Why:** Ensure you didn't break anything
**Time:** ~0.06 seconds

### After Changing Config or Logging
```bash
pytest tests/unit/test_config.py tests/unit/test_logging.py -v
```
**Why:** Verify changes to core infrastructure
**Time:** ~0.02 seconds

### After Changing Multiple Files
```bash
pytest tests/ --cov=src --cov-report=term-missing
```
**Why:** See which code is tested and what's missing coverage
**Time:** ~0.10 seconds

### Before Pushing to GitHub
```bash
pytest tests/ -v --cov=src
```
**Why:** Full verification with coverage report
**Time:** ~0.10 seconds

---

## Reading Test Output

### Example: Successful Test
```
tests/unit/test_config.py::TestConfigLoading::test_config_loads_from_env PASSED [25%]
```
**Translation:**
- `tests/unit/test_config.py` - The test file
- `TestConfigLoading` - The test class (groups related tests)
- `test_config_loads_from_env` - The specific test that ran
- `PASSED` - ✅ Test succeeded
- `[25%]` - Progress (25% of tests complete)

### Example: Failed Test
```
tests/unit/test_config.py::TestConfigLoading::test_config_loads_from_env FAILED [25%]
```
Scroll down to see the error details explaining what went wrong.

---

## Troubleshooting

### "pytest: command not found"
**Problem:** Virtual environment not activated
**Solution:**
```bash
source venv/bin/activate
# Then try again
pytest tests/
```

### "ModuleNotFoundError: No module named 'src'"
**Problem:** Running tests from wrong directory
**Solution:**
```bash
# Make sure you're in project root
cd /path/to/us_vet_scraping
pytest tests/
```

### "fixture 'something' not found"
**Problem:** Missing test fixture
**Solution:** Check `tests/*/conftest.py` files have the fixture defined

### Tests are very slow
**Problem:** Running E2E tests or external API calls
**Solution:** Run unit tests only:
```bash
pytest tests/unit/ -q
```

---

## What Each Test File Tests

### Unit Tests (Individual Components)

**`test_config.py`** - Configuration Management
- ✓ Loads .env file correctly
- ✓ Validates API keys
- ✓ Handles missing config
- ✓ Type coercion works

**`test_logging.py`** - Logging System
- ✓ Console logging works
- ✓ File logging works
- ✓ ANSI colors work in terminal
- ✓ Test mode enables debug logging

**`test_cache.py`** - Caching Logic
- ✓ Place IDs are cached
- ✓ Cache hits reduce API calls
- ✓ Cache memory stays under limit
- ✓ Cache clears after batch

**`test_retry.py`** - Retry Mechanism
- ✓ Exponential backoff timing
- ✓ Max retry limits respected
- ✓ Transient errors retried
- ✓ Non-retryable errors fail fast

**`test_notion_mapper.py`** - Notion Data Mapping
- ✓ Places data maps to Notion format
- ✓ Partial data handled gracefully
- ✓ Schema validation works
- ✓ Malformed data errors caught

### Integration Tests (Components Together)

**`test_config_logging.py`** - Config + Logging
- ✓ Config initializes logging
- ✓ Test mode enables debug logging
- ✓ Log files created from config

**`test_retry_logging.py`** - Retry + Logging
- ✓ Retry attempts logged
- ✓ Cost tracked across retries
- ✓ Backoff delays logged

**`test_notion_integration.py`** - Full Notion Flow
- ✓ Places → Notion mapping flow
- ✓ Schema validation before mapping
- ✓ Missing optional fields handled

### E2E Tests (Complete Workflows)

**`test_batch_operation.py`** - Batch Processing
- ✓ Batch processing with caching
- ✓ Test mode operation
- ✓ Cache cleared after batch
- ✓ Errors tracked across batch
- ✓ Performance with cache
- ✓ Configuration loads before batch

---

## Pro Tips

### 1. Run Tests While Developing
Keep a terminal open running:
```bash
pytest tests/unit/ --watch
```
Tests automatically re-run when you save files.

### 2. Focus on Relevant Tests
If changing config code, just run config tests:
```bash
pytest tests/unit/test_config.py -v
```

### 3. Use Coverage to Find Gaps
```bash
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html  # Mac
```
Shows which lines of code aren't tested yet.

### 4. Create a Testing Alias
Add to your `~/.bashrc` or `~/.zshrc`:
```bash
alias test='pytest tests/ -q'
alias testv='pytest tests/ -v'
alias testu='pytest tests/unit/ -v'
```

Now just type `test` to run all tests!

---

## FAQ

**Q: Do I need to write tests?**
A: For new features, yes! Tests ensure your code works and prevents future bugs.

**Q: How long should tests take?**
A: Unit tests should be instant (<0.1s). Integration tests <1s. E2E tests <5s.

**Q: What's a good test coverage percentage?**
A: Aim for 80%+ overall. Critical code (config, data mapping) should be 90%+.

**Q: Can I skip tests?**
A: Not recommended! But if needed:
```bash
pytest tests/ --ignore=tests/e2e/
```

**Q: How do I debug a failing test?**
A: Add `-vv` for more details and `--tb=short` for shorter error messages:
```bash
pytest tests/unit/test_config.py -vv --tb=short
```

---

## Next Steps

1. **Run all tests** to ensure everything works: `pytest tests/ -q`
2. **Explore test files** in `tests/` to understand what's tested
3. **Check coverage** to see what code needs more tests: `pytest --cov=src --cov-report=html`
4. **Write tests first** when adding new features (TDD approach)

**Remember:** Tests are your safety net. They catch bugs before users do!

---

**Need Help?**
- See `docs/sop/testing-strategy.md` for technical testing approach
- See `docs/features/FEAT-000_shared-infrastructure/testing.md` for feature-specific tests
- Run `pytest --help` for all available options
