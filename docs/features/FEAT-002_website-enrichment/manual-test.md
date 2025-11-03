# Manual Testing Guide: Website Enrichment & LLM Extraction

**Feature ID:** FEAT-002
**Created:** 2025-11-03
**Intended Audience:** Developers, QA testers, product managers

## Overview

This guide provides step-by-step instructions for manually testing the FEAT-002 website enrichment pipeline. Each test scenario validates multi-page scraping, OpenAI extraction, cost tracking, Notion updates, and automatic scoring trigger.

**Prerequisites:**
- Access level required: Developer with access to .env file and Notion database
- Test environment: Local development environment
- Test credentials: OPENAI_API_KEY, NOTION_API_KEY in .env file
- Sample data: Notion database with ≥10 veterinary practices having website URLs

**Estimated Time:** 45 minutes for all scenarios

## Test Setup

### Before You Begin

1. **Environment:** Local development (not production Notion database)
2. **Data Reset:** Create dedicated test Notion database or use existing database in test mode
3. **Browser:** Not applicable (backend feature, no browser needed)
4. **Screen Size:** Not applicable

### Test Account Setup

**Environment Variables (.env):**
```bash
# Required for testing
OPENAI_API_KEY=sk-proj-xxxxxxxxxx
NOTION_API_KEY=secret_xxxxxxxxxx
NOTION_DATABASE_ID=2a0edda2a9a081d98dc9daa43c65e744  # or test database ID
```

**Test Credentials:**
- **OpenAI API Key:** Must have access to gpt-4o-mini model
- **Notion API Key:** Must have write access to Notion database
- **Role:** Developer with full access to codebase and .env file

### Sample Data Needed

- **Notion Database:** ≥10 practices with website URLs populated
- **Test Practices:** Mix of:
  - 3 practices never enriched (enrichment_status=null)
  - 3 practices enriched <30 days ago (should be skipped)
  - 4 practices enriched >30 days ago (should be re-enriched)
- **Websites:** Real vet practice websites with accessible homepages, /about pages, and /team pages

## Test Scenarios

### Test Scenario 1: Test Mode Execution (10 Practices)

**Acceptance Criteria:** AC-FEAT-002-014

**Purpose:** Verify pipeline runs in test mode, enriches exactly 10 practices within 1-2 minutes

**Steps:**
1. **Navigate** to project root directory
   ```bash
   cd /path/to/us_vet_scraping
   ```
   - **Expected:** You are in the project root directory

2. **Run** the enrichment pipeline in test mode
   ```bash
   python -m src.main --feature FEAT-002 --test
   ```
   - **Expected:** Pipeline starts, logs show "Test mode: limiting to 10 practices"
   - **Screenshot:** Not applicable (terminal output)

3. **Observe** execution progress in logs
   - **Expected:** Logs show:
     - "Querying Notion for practices needing enrichment (limit=10)"
     - "Scraping 10 practices with 5 concurrent workers"
     - "Cost update: $X.XXXX / $1.00" (logged every 10 practices)
     - "Enrichment complete: 10 practices enriched"

4. **Measure** total execution time (from start to completion)
   - **Expected:** Total time ≤2 minutes
   - **Screenshot:** Terminal timestamp at start and end

5. **Verify** the result:
   - [ ] Exactly 10 practices enriched (not 9, not 11)
   - [ ] Total execution time ≤2 minutes
   - [ ] Final cost report shows total cost ≤$0.006 (10 × $0.0006)

**Pass Criteria:**
- All expected logs appeared
- Exactly 10 practices enriched within 2 minutes
- Cost ≤$0.006

**Fail Scenarios:**
- If >10 or <10 practices enriched, report: test mode limit not working
- If execution time >2 minutes, report: performance issue
- If cost >$0.01, report: cost estimation error

---

### Test Scenario 2: Notion Field Verification

**Acceptance Criteria:** AC-FEAT-002-011, AC-FEAT-002-012, AC-FEAT-002-402

**Purpose:** Verify all enrichment fields populated correctly in Notion, sales fields preserved

**Steps:**
1. **Navigate** to Notion database in web browser
   ```
   https://www.notion.so/2a0edda2a9a081d98dc9daa43c65e744
   ```
   - **Expected:** Notion database view loads with all practices

2. **Identify** 5 practices that were enriched in Test Scenario 1
   - Look for practices with "Enrichment Status" = "Completed"
   - Note the practice names for inspection

3. **Open** first enriched practice record (click on practice name)
   - **Expected:** Full record view opens

4. **Inspect** enrichment fields (verify all present and correct):
   - **Confirmed Vet Count (Total):** Number (e.g., 3) or empty
   - **Vet Count Confidence:** Select (high/medium/low) or empty
   - **Decision Maker Name:** Rich text (e.g., "Dr. Jane Smith") or empty
   - **Decision Maker Role:** Select (Owner, Practice Manager, Medical Director) or empty
   - **Decision Maker Email:** Email (e.g., drsmith@example.com) or empty
   - **Decision Maker Phone:** Phone number or empty
   - **24/7 Emergency Services:** Checkbox (checked or unchecked)
   - **Specialty Services:** Multi-select (Surgery, Dental, Oncology, etc.) or empty
   - **Wellness Programs:** Checkbox (checked or unchecked)
   - **Boarding Services:** Checkbox (checked or unchecked)
   - **Online Booking:** Checkbox (checked or unchecked)
   - **Telemedicine:** Checkbox (checked or unchecked)
   - **Patient Portal:** Checkbox (checked or unchecked)
   - **Digital Records Mentioned:** Checkbox (checked or unchecked)
   - **Personalization Context:** Multi-select (1-3 facts) or empty
   - **Awards/Accreditations:** Multi-select (AAHA, etc.) or empty
   - **Unique Services:** Multi-select or empty
   - **Enrichment Status:** Select = "Completed"
   - **Last Enrichment Date:** Date (today's date)

5. **Verify** sales workflow fields NOT overwritten (if they existed before):
   - **Status:** Should be unchanged (e.g., "New Lead", "Qualified", etc.)
   - **Assigned To:** Should be unchanged (or empty if never set)
   - **Research Notes:** Should be unchanged (or empty)
   - **Call Notes:** Should be unchanged (or empty)
   - **Last Contact Date:** Should be unchanged (or empty)

6. **Repeat** inspection for 4 more enriched practices (total 5 inspected)
   - Verify similar field population and preservation

**Pass Criteria:**
- All enrichment fields populated correctly (or reasonably empty if data not found on website)
- Sales workflow fields preserved (not overwritten)
- Enrichment Status = "Completed" for all inspected practices
- Last Enrichment Date = today's date

**Fail Scenarios:**
- If sales fields overwritten, report: field preservation bug
- If enrichment fields missing or malformed, report: Notion mapper error
- If Enrichment Status != "Completed", report: status update bug

---

### Test Scenario 3: Cost Tracking Validation

**Acceptance Criteria:** AC-FEAT-002-009, AC-FEAT-002-010, AC-FEAT-002-209

**Purpose:** Verify cost tracking with tiktoken, logging every 10 practices, no cost overruns

**Steps:**
1. **Review** terminal logs from Test Scenario 1 (or re-run if needed)
   - Scroll to find cost logging entries

2. **Locate** cost logging entries (should appear at practice #10)
   - **Expected:** Log entry: "Cost update: $0.XXXX / $1.00"
   - **Expected:** Format shows cumulative cost and threshold

3. **Verify** final cost report at end of pipeline
   - **Expected:** Log entry: "Total cost: $0.XXXX for 10 API calls"
   - **Expected:** Average cost per practice shown (e.g., "$0.0006 per extraction")

4. **Calculate** expected cost manually:
   - Average website: 2-3 pages, ~4000 input tokens, ~500 output tokens
   - Expected cost per extraction: (4000 × $0.15/1M) + (500 × $0.60/1M) = $0.0009
   - 10 practices: 10 × $0.0009 = $0.009
   - **Verify:** Actual cost is within 20% of expected (e.g., $0.007-$0.011)

5. **Verify** no cost abort (pipeline completed successfully)
   - **Expected:** No "CostLimitExceeded" errors in logs

**Pass Criteria:**
- Cost logged at practice #10
- Final cost report shows total cost, per-practice average
- Actual cost within 20% of expected calculation
- No cost abort errors

**Fail Scenarios:**
- If cost not logged at interval, report: logging configuration error
- If actual cost >2x expected, report: token counting error or inefficient prompts
- If cost abort triggered at <$1.00, report: CostTracker threshold bug

---

### Test Scenario 4: Re-enrichment Logic (30-Day Window)

**Acceptance Criteria:** AC-FEAT-002-013

**Purpose:** Verify only practices >30 days old or never enriched are re-enriched

**Steps:**
1. **Prepare** test data in Notion:
   - **Practice A:** Set "Last Enrichment Date" to 31 days ago (should be re-enriched)
   - **Practice B:** Set "Last Enrichment Date" to 29 days ago (should be skipped)
   - **Practice C:** Set "Last Enrichment Date" to null (never enriched, should be enriched)

2. **Run** enrichment pipeline in test mode
   ```bash
   python -m src.main --feature FEAT-002 --test
   ```

3. **Observe** logs for query filter
   - **Expected:** Log entry: "Query filter: enrichment_status != 'Completed' OR last_enriched_date > 30 days ago"

4. **Verify** which practices were enriched:
   - Check Notion "Last Enrichment Date" for Practice A, B, C after pipeline completes
   - **Expected:**
     - Practice A: Last Enrichment Date updated to today (re-enriched)
     - Practice B: Last Enrichment Date unchanged (skipped, only 29 days old)
     - Practice C: Last Enrichment Date set to today (newly enriched)

**Pass Criteria:**
- Practice A (31 days old) was re-enriched
- Practice B (29 days old) was skipped
- Practice C (never enriched) was enriched
- Query filter correctly excludes recently enriched practices

**Fail Scenarios:**
- If Practice B was re-enriched, report: re-enrichment window logic bug
- If Practice A was skipped, report: query filter error
- If Practice C was skipped, report: query filter missing never-enriched condition

---

### Test Scenario 5: Multi-Page Scraping Verification

**Acceptance Criteria:** AC-FEAT-002-001, AC-FEAT-002-203

**Purpose:** Verify multi-page scraping finds homepage + /about + /team pages

**Steps:**
1. **Select** 3 practices from Notion with known website structures:
   - **Practice 1:** Website with homepage + /about + /team (all 3 pages exist)
   - **Practice 2:** Website with homepage + /about only (no /team page)
   - **Practice 3:** Website with homepage only (no /about, no /team)

2. **Run** enrichment pipeline in test mode
   ```bash
   python -m src.main --feature FEAT-002 --test
   ```

3. **Observe** scraping logs for each practice:
   - **Expected for Practice 1:**
     - "Scraped 3 pages: https://practice1.com/ (homepage), https://practice1.com/about, https://practice1.com/team"
   - **Expected for Practice 2:**
     - "Scraped 2 pages: https://practice2.com/ (homepage), https://practice2.com/about"
   - **Expected for Practice 3:**
     - "Scraped 1 page: https://practice3.com/ (homepage)"

4. **Inspect** Notion records after enrichment:
   - **Practice 1:** Likely has "Confirmed Vet Count (Total)" populated (found on /team page)
   - **Practice 2:** May have vet count if mentioned on /about page
   - **Practice 3:** Less likely to have vet count (only homepage scraped)

**Pass Criteria:**
- Multi-page scraping finds /about and /team pages when they exist
- Vet count detection rate higher for practices with /team pages
- URL pattern filter correctly matches *about*, *team*, *staff*, *contact*

**Fail Scenarios:**
- If /team page exists but not scraped, report: URL pattern filter not working
- If all practices only show 1 page scraped, report: BFSDeepCrawlStrategy not enabled
- If unrelated pages scraped (e.g., /blog, /services), report: URL pattern filter too broad

---

### Test Scenario 6: Scoring Trigger Integration (if FEAT-003 implemented)

**Acceptance Criteria:** AC-FEAT-002-015, AC-FEAT-002-016

**Purpose:** Verify automatic FEAT-003 scoring trigger after enrichment (if enabled)

**Steps:**
1. **Check** if FEAT-003 is implemented and scoring_service available
   - If not implemented, skip this scenario

2. **Enable** auto-trigger scoring in config
   ```json
   // config/config.json
   {
     "enrichment": {
       "auto_trigger_scoring": true
     }
   }
   ```

3. **Run** enrichment pipeline in test mode
   ```bash
   python -m src.main --feature FEAT-002 --test
   ```

4. **Observe** logs for scoring trigger
   - **Expected:** Log entries after each enrichment:
     - "Triggering FEAT-003 scoring for practice: Boston Veterinary Clinic"
     - "Scored Boston Veterinary Clinic: 85/120"

5. **Verify** Notion records updated with ICP scores
   - Check "ICP Fit Score" field in Notion
   - **Expected:** All enriched practices have ICP scores (0-120)

6. **Test** graceful degradation (scoring disabled)
   - Set `auto_trigger_scoring: false` in config
   - Re-run pipeline
   - **Expected:** No scoring logs, enrichment still completes successfully

**Pass Criteria:**
- When enabled: Scoring triggered for all enriched practices
- When disabled: No scoring attempts, pipeline completes successfully
- Notion updated with ICP scores when scoring enabled

**Fail Scenarios:**
- If scoring not triggered when enabled, report: scoring trigger not working
- If pipeline fails when scoring disabled, report: graceful degradation bug
- If scoring failures block enrichment, report: error handling bug

---

## Visual & UX Validation

*Not applicable - FEAT-002 is backend-only feature with no visual UI*

## Performance Check

### Execution Time Validation

1. **Test Mode (10 Practices):**
   - [ ] Total execution time ≤2 minutes
   - [ ] Scraping time ≤1.5 minutes (10 practices × 3 pages avg × 3s per page ÷ 5 concurrent)
   - [ ] LLM extraction time ≤30 seconds (10 practices × 1s avg per extraction)
   - [ ] Notion updates ≤10 seconds (10 practices × 0.35s rate limit)

2. **Production Mode (150 Practices) - Optional:**
   - [ ] Total execution time ≤14 minutes
   - [ ] Cost ≤$0.50

### Cost Efficiency Validation

- [ ] Per-extraction cost ≤$0.001 (average across 10 test practices)
- [ ] Total cost for 10 practices ≤$0.01
- [ ] No unexpected cost spikes (verify logs for outliers)

## Error Handling Check

### Triggered Failure Scenarios

1. **Website Timeout:**
   - Temporarily block access to a practice website (firewall rule)
   - Run pipeline in test mode
   - **Expected:** Practice added to retry queue, retried once at end

2. **Invalid URL:**
   - Add practice with invalid website URL (e.g., "http://notarealwebsite123.com")
   - Run pipeline
   - **Expected:** Connection error logged, practice marked as failed after retry

3. **Cost Abort (simulated):**
   - Temporarily lower cost threshold to $0.01 in config
   - Run pipeline with 10 practices
   - **Expected:** Pipeline aborts after 10-15 extractions with "CostLimitExceeded" error

## Bug Reporting

**If You Find a Bug, Report:**
1. **Title:** [Brief description of issue]
2. **Scenario:** [Which test scenario: e.g., "Test Scenario 2: Notion Field Verification"]
3. **Steps to Reproduce:**
   - [Exact steps taken]
   - [Command run]
   - [Practice inspected]
4. **Expected Result:** [What should have happened]
5. **Actual Result:** [What actually happened]
6. **Logs/Screenshots:** [Attach terminal output, Notion screenshots]
7. **Environment:**
   - OS: [macOS, Linux, Windows]
   - Python version: [e.g., 3.11.5]
   - Test mode: [True or False]
   - OpenAI API Key: [masked, e.g., sk-proj-***]

**Example Bug Report:**
```
Title: Sales fields overwritten during enrichment
Scenario: Test Scenario 2 - Notion Field Verification
Steps to Reproduce:
1. Created practice in Notion with Status="Qualified", Assigned To="John"
2. Ran: python -m src.main --feature FEAT-002 --test
3. Inspected practice record in Notion after enrichment
Expected Result: Status="Qualified", Assigned To="John" (preserved)
Actual Result: Status="New Lead" (overwritten), Assigned To=empty (cleared)
Logs: [Attach terminal output showing Notion update payload]
Environment: macOS 14.1, Python 3.11.5, Test mode: True
```

## Test Completion Checklist

### All Scenarios Complete
- [ ] Test Scenario 1: Test Mode Execution (10 Practices) - PASS / FAIL
- [ ] Test Scenario 2: Notion Field Verification - PASS / FAIL
- [ ] Test Scenario 3: Cost Tracking Validation - PASS / FAIL
- [ ] Test Scenario 4: Re-enrichment Logic (30-Day Window) - PASS / FAIL
- [ ] Test Scenario 5: Multi-Page Scraping Verification - PASS / FAIL
- [ ] Test Scenario 6: Scoring Trigger Integration (if FEAT-003 implemented) - PASS / FAIL / SKIPPED

### Additional Checks
- [ ] Performance validation complete (execution time ≤2 min, cost ≤$0.01)
- [ ] Error handling checks complete (timeout, invalid URL, cost abort)
- [ ] Log inspection complete (no API keys exposed, cost logging correct)

### Summary
- **Total Scenarios:** 6 (or 5 if FEAT-003 not implemented)
- **Passed:** [Y]
- **Failed:** [Z]
- **Bugs Filed:** [Number and links]

**Overall Assessment:**
- [ ] Feature is ready for deployment
- [ ] Feature has minor issues (specify)
- [ ] Feature has blocking issues (specify)

**Tester Sign-off:**
- **Name:** [Tester name]
- **Date:** [Testing completion date]
- **Notes:** [Any additional observations]

---

**Next Steps:**
- If all tests pass: Feature approved for Phase 2 implementation
- If bugs found: Development team will fix and retest affected scenarios
- Update this document if feature changes significantly during implementation
