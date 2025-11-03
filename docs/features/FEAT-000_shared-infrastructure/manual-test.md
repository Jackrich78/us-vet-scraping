# Manual Testing Guide: Shared Infrastructure

**Feature ID:** FEAT-000
**Status:** Draft
**Last Updated:** 2025-11-03
**Tester:** Developer/QA
**Estimated Time:** 30-45 minutes

## Prerequisites

### Required Software
- Python 3.9+ installed
- Terminal application (Terminal.app, iTerm2, or equivalent)
- Text editor for viewing log files
- Git repository cloned locally

### Required Files
- `.env` file with valid configuration (see template below)
- Access to Google Places API key (for realistic testing)
- Access to Notion API key and database ID (for integration testing)

### Environment Setup

1. **Create Virtual Environment**
   ```bash
   cd /Users/builder/dev/us_vet_scraping
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create Test `.env` File**
   ```bash
   cp .env.example .env
   # Edit .env with your test credentials
   ```

4. **Verify Installation**
   ```bash
   python --version  # Should be 3.9+
   pytest --version  # Should show pytest installed
   ```

## Test Scenarios

### Test 1: Configuration Loading and Validation

**Objective:** Verify configuration loads correctly from `.env` file with proper validation

**Steps:**

1. **Test Valid Configuration**
   ```bash
   # Ensure .env has all required fields
   python -c "from src.config import load_config; cfg = load_config(); print('Config loaded:', cfg)"
   ```

   **Expected Result:** Configuration loads successfully, prints config object

2. **Test Missing Required Field**
   ```bash
   # Temporarily remove GOOGLE_PLACES_API_KEY from .env
   mv .env .env.backup
   cat .env.backup | grep -v GOOGLE_PLACES_API_KEY > .env
   python -c "from src.config import load_config; cfg = load_config()"
   ```

   **Expected Result:** Pydantic validation error mentioning missing `GOOGLE_PLACES_API_KEY`

3. **Test Invalid Type**
   ```bash
   # Add invalid value for numeric field
   echo "MAX_RETRIES=not_a_number" >> .env
   python -c "from src.config import load_config; cfg = load_config()"
   ```

   **Expected Result:** Pydantic validation error for type mismatch

4. **Restore Valid Configuration**
   ```bash
   mv .env.backup .env
   ```

**Acceptance Checklist:**
- [ ] Valid configuration loads without errors
- [ ] Missing required fields raise clear validation errors
- [ ] Invalid types raise type mismatch errors
- [ ] Error messages include field name and expected type

---

### Test 2: ANSI Console Logging

**Objective:** Verify logging displays with correct colors in terminal

**Steps:**

1. **Test Standard Log Levels**
   ```bash
   python -c "
   from src.logging import setup_logger
   logger = setup_logger()
   logger.debug('Debug message - should be BLUE')
   logger.info('Info message - should be GREEN')
   logger.warning('Warning message - should be YELLOW')
   logger.error('Error message - should be RED')
   "
   ```

   **Expected Result:** Each log level displays in its designated color:
   - DEBUG = Blue
   - INFO = Green
   - WARNING = Yellow
   - ERROR = Red

2. **Test Cost Tracking in Logs**
   ```bash
   python -c "
   from src.logging import setup_logger
   logger = setup_logger()
   logger.info('API call completed', extra={'cost': 0.032})
   "
   ```

   **Expected Result:** Log includes cost information (e.g., `[$0.032]`)

3. **Visual Verification**
   - Take screenshot of terminal showing colored output
   - Verify colors are distinct and readable
   - Check timestamp format is consistent (ISO 8601)

**Acceptance Checklist:**
- [ ] DEBUG messages display in blue
- [ ] INFO messages display in green
- [ ] WARNING messages display in yellow
- [ ] ERROR messages display in red
- [ ] Cost tracking appears in log output
- [ ] Timestamps are present and formatted correctly

---

### Test 3: File Logging Without ANSI

**Objective:** Verify log files contain plain text without ANSI codes

**Steps:**

1. **Enable File Logging**
   ```bash
   # Add to .env or config
   echo "LOG_FILE=test_output.log" >> .env
   ```

2. **Generate Logs**
   ```bash
   python -c "
   from src.logging import setup_logger
   logger = setup_logger()
   logger.info('Info message to file')
   logger.warning('Warning message to file')
   logger.error('Error message to file')
   "
   ```

3. **Inspect Log File**
   ```bash
   cat test_output.log
   # or open in text editor
   open -a TextEdit test_output.log
   ```

   **Expected Result:** Log file contains:
   - Plain text without escape sequences (no `\x1b[` codes)
   - Timestamp, level, and message
   - No color artifacts

4. **Verify ANSI Stripping**
   ```bash
   grep -c "\\x1b" test_output.log
   ```

   **Expected Result:** Returns `0` (no ANSI codes found)

5. **Cleanup**
   ```bash
   rm test_output.log
   ```

**Acceptance Checklist:**
- [ ] Log file is plain text
- [ ] No ANSI escape codes present
- [ ] Log entries are readable
- [ ] Timestamp, level, and message included
- [ ] File can be opened in any text editor

---

### Test 4: Test Mode and Debug Logging

**Objective:** Verify `--test` flag enables debug logging automatically

**Steps:**

1. **Run Without Test Flag**
   ```bash
   python src/main.py --help
   # Note default log level in output
   ```

   **Expected Result:** Default log level is INFO (debug messages not shown)

2. **Run With Test Flag**
   ```bash
   python src/main.py --test --help
   ```

   **Expected Result:** Log level automatically switches to DEBUG, debug messages visible

3. **Verify Debug Output**
   - Look for additional debug messages
   - Confirm more verbose logging
   - Check that DEBUG messages are in blue

**Acceptance Checklist:**
- [ ] Without `--test`, log level is INFO
- [ ] With `--test`, log level is DEBUG
- [ ] Debug messages are visible in test mode
- [ ] Test mode is clearly indicated in logs

---

### Test 5: Retry Logic with Exponential Backoff

**Objective:** Verify retry logic handles transient failures with exponential backoff

**Steps:**

1. **Simulate Transient Failure**
   ```bash
   python -c "
   from src.retry import retry_with_backoff
   import time

   @retry_with_backoff(max_retries=5)
   def failing_function():
       print(f'Attempt at {time.time()}')
       raise Exception('Simulated transient failure')

   try:
       failing_function()
   except Exception as e:
       print(f'Final error: {e}')
   "
   ```

   **Expected Result:**
   - 5 retry attempts with increasing delays
   - Timestamps show exponential backoff (1s, 2s, 4s, 8s, 16s)
   - Final error raised after max retries

2. **Measure Backoff Timing**
   - Note timestamp differences between attempts
   - Verify exponential pattern (each delay approximately double previous)

3. **Test Non-Retryable Error**
   ```bash
   python -c "
   from src.retry import retry_with_backoff

   @retry_with_backoff(max_retries=5)
   def non_retryable_error():
       from requests.exceptions import HTTPError
       response = type('Response', (), {'status_code': 401})()
       raise HTTPError('Unauthorized', response=response)

   try:
       non_retryable_error()
   except Exception as e:
       print(f'Immediate error: {e}')
   "
   ```

   **Expected Result:** No retry attempts, immediate error propagation

**Acceptance Checklist:**
- [ ] Transient errors trigger retry logic
- [ ] Backoff timing follows exponential pattern
- [ ] Max retry limit is enforced (5 attempts)
- [ ] Non-retryable errors (401, 403, 400) fail immediately
- [ ] Cost is logged for each retry attempt

---

### Test 6: Notion Data Mapping

**Objective:** Verify Notion mapper transforms Places API data correctly

**Steps:**

1. **Test Complete API Response**
   ```bash
   python -c "
   from src.notion_mapper import map_place_to_notion

   place_data = {
       'place_id': 'ChIJ123abc',
       'name': 'Test Veterans Center',
       'formatted_address': '123 Main St, City, ST 12345',
       'formatted_phone_number': '(555) 123-4567',
       'website': 'https://example.com',
       'rating': 4.5,
       'user_ratings_total': 120
   }

   notion_data = map_place_to_notion(place_data)
   print('Mapped data:', notion_data)
   "
   ```

   **Expected Result:** All fields mapped correctly to Notion format

2. **Test Partial API Response**
   ```bash
   python -c "
   from src.notion_mapper import map_place_to_notion

   place_data = {
       'place_id': 'ChIJ123abc',
       'name': 'Test Veterans Center',
       'formatted_address': '123 Main St, City, ST 12345'
       # Missing optional fields
   }

   notion_data = map_place_to_notion(place_data)
   print('Mapped data with defaults:', notion_data)
   "
   ```

   **Expected Result:** Missing fields use appropriate defaults (null, empty string, or 0)

3. **Test Malformed Data**
   ```bash
   python -c "
   from src.notion_mapper import map_place_to_notion

   place_data = {
       'place_id': 'ChIJ123abc',
       'name': None,  # Invalid: name should be string
       'formatted_address': '123 Main St'
   }

   try:
       notion_data = map_place_to_notion(place_data)
   except Exception as e:
       print(f'Error caught: {e}')
   "
   ```

   **Expected Result:** Error caught with specific field context

**Acceptance Checklist:**
- [ ] Complete responses map all fields correctly
- [ ] Partial responses handle missing fields gracefully
- [ ] Malformed data raises clear errors
- [ ] Error messages indicate which field is problematic
- [ ] Mapper works independently of models

---

### Test 7: Place ID Caching Performance

**Objective:** Verify Place ID cache reduces redundant API calls

**Steps:**

1. **Test Cache Hit**
   ```bash
   python -c "
   from src.cache import PlaceIDCache

   cache = PlaceIDCache()

   # First lookup (cache miss)
   result1 = cache.get('ChIJ123abc')
   print(f'First lookup: {result1}')  # Should be None

   # Store in cache
   cache.set('ChIJ123abc', {'name': 'Test Place', 'address': '123 Main St'})

   # Second lookup (cache hit)
   result2 = cache.get('ChIJ123abc')
   print(f'Second lookup: {result2}')  # Should return cached data
   "
   ```

   **Expected Result:** Second lookup returns cached data without API call

2. **Measure Cache Performance**
   ```bash
   python -c "
   from src.cache import PlaceIDCache
   import time

   cache = PlaceIDCache()
   cache.set('ChIJ123abc', {'name': 'Test Place'})

   start = time.perf_counter()
   for _ in range(1000):
       cache.get('ChIJ123abc')
   elapsed = time.perf_counter() - start

   print(f'1000 lookups in {elapsed*1000:.2f}ms')
   print(f'Average: {elapsed/1000*1000:.3f}ms per lookup')
   "
   ```

   **Expected Result:** Average lookup time <1ms

3. **Test Cache Clearing**
   ```bash
   python -c "
   from src.cache import PlaceIDCache

   cache = PlaceIDCache()
   cache.set('ChIJ123abc', {'name': 'Test Place'})
   print(f'Before clear: {cache.get(\"ChIJ123abc\")}')

   cache.clear()
   print(f'After clear: {cache.get(\"ChIJ123abc\")}')
   "
   ```

   **Expected Result:** Cache cleared, second lookup returns None

**Acceptance Checklist:**
- [ ] Cache hit returns stored data
- [ ] Cache miss returns None
- [ ] Lookup performance <1ms per operation
- [ ] Cache clear removes all entries
- [ ] Memory usage reasonable for 1000+ entries

---

### Test 8: CI/CD Environment Logging

**Objective:** Verify ANSI codes are disabled in CI/CD environments

**Steps:**

1. **Simulate CI/CD Environment**
   ```bash
   # Unset terminal type to simulate CI
   env -u TERM python -c "
   from src.logging import setup_logger
   logger = setup_logger()
   logger.info('Info in CI environment')
   logger.error('Error in CI environment')
   "
   ```

   **Expected Result:** Logs display without ANSI colors (plain text)

2. **Test with NO_COLOR Environment Variable**
   ```bash
   NO_COLOR=1 python -c "
   from src.logging import setup_logger
   logger = setup_logger()
   logger.info('Info with NO_COLOR set')
   "
   ```

   **Expected Result:** ANSI codes disabled, plain text output

3. **Verify in Actual CI Pipeline**
   - Push code to trigger CI/CD
   - Check CI logs for plain text output
   - Confirm no ANSI escape sequences

**Acceptance Checklist:**
- [ ] ANSI disabled when TERM is unset
- [ ] NO_COLOR environment variable respected
- [ ] CI logs are readable plain text
- [ ] No color artifacts in CI output

---

## Performance Testing

### Configuration Load Performance

```bash
python -c "
import time
from src.config import load_config

start = time.perf_counter()
cfg = load_config()
elapsed = time.perf_counter() - start

print(f'Config load time: {elapsed*1000:.2f}ms')
assert elapsed < 0.1, 'Config load too slow'
"
```

**Expected:** <100ms

### Logging Performance

```bash
python -c "
import time
from src.logging import setup_logger

logger = setup_logger()

start = time.perf_counter()
for i in range(1000):
    logger.info(f'Log entry {i}')
elapsed = time.perf_counter() - start

print(f'1000 log entries in {elapsed*1000:.2f}ms')
print(f'Average: {elapsed/1000*1000:.3f}ms per entry')
assert elapsed/1000 < 0.005, 'Logging too slow'
"
```

**Expected:** <5ms per log entry

## Troubleshooting

### ANSI Colors Not Displaying
- Check terminal supports ANSI (most modern terminals do)
- Verify TERM environment variable is set
- Try different terminal application

### Configuration Validation Errors
- Check .env file syntax (no spaces around `=`)
- Verify all required fields are present
- Check for typos in environment variable names

### Log Files Not Created
- Verify LOG_FILE path is writable
- Check directory exists (or create it)
- Look for permission errors in console output

### Retry Logic Not Working
- Check network connectivity
- Verify API endpoints are accessible
- Look for non-retryable errors (4xx codes)

## Post-Testing Cleanup

```bash
# Remove test log files
rm -f test_output.log

# Restore original .env if modified
# (if you backed it up)

# Deactivate virtual environment
deactivate
```

## Test Summary Report

After completing all scenarios, fill out:

| Test Scenario | Status | Notes |
|---------------|--------|-------|
| Configuration Loading | ☐ Pass ☐ Fail | |
| ANSI Console Logging | ☐ Pass ☐ Fail | |
| File Logging | ☐ Pass ☐ Fail | |
| Test Mode | ☐ Pass ☐ Fail | |
| Retry Logic | ☐ Pass ☐ Fail | |
| Notion Mapping | ☐ Pass ☐ Fail | |
| Place ID Caching | ☐ Pass ☐ Fail | |
| CI/CD Logging | ☐ Pass ☐ Fail | |

**Overall Result:** ☐ All Pass ☐ Some Failures

**Tester Signature:** _______________ **Date:** _______________

## Next Steps

If all tests pass:
1. Document any issues or observations
2. Proceed with code review
3. Ready for PR submission

If tests fail:
1. Document failure details
2. Create bug tickets for issues
3. Re-test after fixes applied
