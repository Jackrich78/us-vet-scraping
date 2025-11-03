# Manual Testing Guide
**Feature:** FEAT-001 - Google Maps Scraping & Notion Integration
**Date:** 2025-11-03
**Version:** 1.0
**Audience:** Non-technical users, QA testers, stakeholders

## Overview

This guide provides step-by-step instructions for manually testing the Google Maps scraping and Notion integration feature. No coding knowledge required - just follow the steps and check the results.

## Prerequisites

Before you begin testing, ensure you have:

1. **Apify Account & API Key**
   - Sign up at https://apify.com
   - Navigate to Settings → Integrations → API Token
   - Copy your API token (starts with "apify_api_...")

2. **Notion Account & Integration**
   - Sign up at https://notion.com
   - Create an integration at https://www.notion.so/my-integrations
   - Copy the Internal Integration Token (starts with "secret_...")

3. **Notion Database Setup**
   - Create a new database in Notion
   - Add the following properties:
     - **Place ID** (Title) - Primary key
     - **Business Name** (Text)
     - **Address** (Text)
     - **Phone** (Phone)
     - **Website** (URL)
     - **Review Count** (Number)
     - **Star Rating** (Number)
     - **Initial Score** (Number)
     - **Status** (Select) - Options: "New Lead", "Contacted", "Qualified"
   - Share the database with your integration (click Share → Select your integration)
   - Copy the database ID from the URL (32-character hex after the last slash)

4. **Environment Variables**
   - Set the following in your terminal:
   ```bash
   export APIFY_API_KEY="your_apify_key_here"
   export NOTION_API_KEY="your_notion_key_here"
   export NOTION_DATABASE_ID="your_database_id_here"
   ```

5. **Python Environment**
   - Python 3.11 or higher installed
   - Dependencies installed: `pip install -r requirements.txt`

## Test Scenarios

### Test 1: Run Pipeline in Test Mode (10 Practices)

**Objective:** Validate the pipeline works end-to-end with a small sample

**Steps:**
1. Open your terminal/command prompt
2. Navigate to the project directory: `cd /path/to/us_vet_scraping`
3. Run the pipeline with test flag: `python main.py --test`
4. Watch the console output for progress messages:
   - "Starting Apify scraper..."
   - "Scraping completed: 10 results found"
   - "Applying filters..."
   - "Calculating initial scores..."
   - "Uploading to Notion in batches..."
   - "Pipeline completed successfully!"

**Expected Results:**
- Pipeline completes without errors in <2 minutes
- Console shows exactly 10 practices scraped
- Some practices may be filtered out (if they don't meet criteria)
- Remaining practices uploaded to Notion

**Pass Criteria:**
- [ ] Pipeline completes without errors
- [ ] Console output shows 10 practices scraped
- [ ] At least 1 practice uploaded to Notion (some may be filtered)
- [ ] No API errors or exceptions in console

**If Test Fails:**
- Check environment variables are set correctly
- Verify Apify and Notion API keys are valid
- Check Notion database has correct properties
- Review error messages in console for specific issues

---

### Test 2: Verify Notion Records Created Correctly

**Objective:** Validate data quality and field mapping in Notion

**Steps:**
1. Open your Notion database in a web browser
2. Check for new records created in the last few minutes
3. Verify each record has the following fields populated:
   - **Place ID**: Unique Google Maps ID (e.g., "ChIJ...")
   - **Business Name**: Practice name (e.g., "Happy Paws Veterinary Clinic")
   - **Address**: Full street address with city, state, zip
   - **Phone**: Valid phone number format
   - **Website**: Valid URL starting with http:// or https://
   - **Review Count**: Number ≥10 (due to filter)
   - **Star Rating**: Number between 3.0 and 5.0
   - **Initial Score**: Number between 0 and 25
   - **Status**: Should be "New Lead"

**Expected Results:**
- All fields populated correctly
- No missing or null values
- Data matches what you'd see on Google Maps for that business

**Pass Criteria:**
- [ ] All required fields populated for every record
- [ ] Review Count ≥10 for all records
- [ ] Website field contains valid URL for all records
- [ ] Initial Score is between 0-25
- [ ] Status is "New Lead" for all records

**If Test Fails:**
- Check Notion database schema matches prerequisites
- Verify field types are correct (Number for numeric fields, URL for website)
- Review console logs for data validation errors

---

### Test 3: Run Full Pipeline (150 Practices)

**Objective:** Validate production-scale performance and cost

**Steps:**
1. Open your terminal/command prompt
2. Navigate to the project directory: `cd /path/to/us_vet_scraping`
3. Run the pipeline without test flag: `python main.py`
4. Watch the console output for progress (this will take 5-8 minutes)
5. Note the start and end time to calculate total duration

**Expected Results:**
- Pipeline completes in <8 minutes
- Console shows 150 practices scraped
- After filtering, 50-100 practices remain (depends on quality)
- All remaining practices uploaded to Notion successfully

**Pass Criteria:**
- [ ] Pipeline completes without errors
- [ ] Execution time ≤8 minutes
- [ ] 150 practices scraped initially
- [ ] 50-100+ practices uploaded to Notion (after filtering)
- [ ] No API timeout or rate limit errors

**If Test Fails:**
- If timeout: Check internet connection, increase timeout in config
- If rate limit errors: Verify batch delays are configured (3.5s between batches)
- If cost exceeds budget: Review Apify billing dashboard

---

### Test 4: Verify De-duplication (Re-run Pipeline)

**Objective:** Ensure no duplicate records created on subsequent runs

**Steps:**
1. Note the current count of records in your Notion database
2. Run the pipeline again: `python main.py --test`
3. Watch console output for de-duplication messages:
   - "Found 5 existing Place IDs in Notion"
   - "Skipped 5 duplicates"
   - "Uploaded 5 new practices"
4. Check Notion database record count again

**Expected Results:**
- Record count increases by number of new practices only
- No duplicate Place IDs in database
- Console shows duplicates detected and skipped

**Pass Criteria:**
- [ ] No duplicate Place IDs in Notion database
- [ ] Console shows "Skipped X duplicates" message
- [ ] Only new practices (if any) uploaded
- [ ] Existing records not modified

**If Test Fails:**
- Check Place ID field is set as database key/unique
- Verify de-duplication logic runs before batch upload
- Review console logs for de-duplication errors

---

### Test 5: Validate Initial Scores Calculated Correctly

**Objective:** Verify scoring algorithm produces expected results

**Steps:**
1. Open your Notion database
2. Find a practice with the following characteristics:
   - Review Count: 50
   - Star Rating: 4.5
   - Website: Present
3. Calculate expected score manually:
   - Review points: ~3 points (logarithmic scale for 50 reviews)
   - Rating points: ~13 points (4.5 - 3.0) * 10
   - Website points: 5 points
   - **Total: ~21 points**
4. Compare with Initial Score field in Notion

**Expected Results:**
- Initial Score field shows value close to manual calculation (±2 points)
- Higher review counts = higher scores
- Higher ratings = higher scores

**Pass Criteria:**
- [ ] Initial Score matches expected calculation (±2 points tolerance)
- [ ] All scores are between 0-25
- [ ] Practices with more reviews/higher ratings have higher scores
- [ ] Scoring is consistent across all records

**If Test Fails:**
- Review scoring formula in documentation
- Check for data validation errors in console
- Verify review count and star rating values are correct

---

### Test 6: Test Error Handling (Invalid API Key)

**Objective:** Validate graceful error handling and user-friendly messages

**Steps:**
1. Temporarily set an invalid Apify API key:
   ```bash
   export APIFY_API_KEY="invalid_key_123"
   ```
2. Run the pipeline: `python main.py --test`
3. Observe the error message in console

**Expected Results:**
- Pipeline fails fast (within 30 seconds)
- Clear error message indicating invalid API key
- No confusing stack traces or technical jargon
- Suggested fix provided (e.g., "Check APIFY_API_KEY environment variable")

**Pass Criteria:**
- [ ] Pipeline fails within 30 seconds
- [ ] Error message is clear and actionable
- [ ] No sensitive information (API keys) logged in plaintext
- [ ] Suggested fix provided in error message

**After Test:**
- Restore valid API key: `export APIFY_API_KEY="your_valid_key"`

**If Test Fails:**
- Check error handling code includes user-friendly messages
- Verify API keys are masked in logs (should show "***...***")

---

## Visual Checks

### Notion Database Appearance

After successful pipeline run, your Notion database should look like this:

```
╔════════════════════╦═══════════════════════╦══════════════════╦════════════╗
║ Place ID (Title)   ║ Business Name         ║ Address          ║ Phone      ║
╠════════════════════╬═══════════════════════╬══════════════════╬════════════╣
║ ChIJ123abc...      ║ Happy Paws Vet Clinic ║ 123 Main St, ... ║ 555-1234   ║
║ ChIJ456def...      ║ Pet Care Center       ║ 456 Oak Ave, ... ║ 555-5678   ║
║ ChIJ789ghi...      ║ Animal Hospital Plus  ║ 789 Elm Blvd, ...║ 555-9012   ║
╚════════════════════╩═══════════════════════╩══════════════════╩════════════╝

╔════════════╦═══════════════╦═══════════════╦═════════════════╦════════════╗
║ Website    ║ Review Count  ║ Star Rating   ║ Initial Score   ║ Status     ║
╠════════════╬═══════════════╬═══════════════╬═════════════════╬════════════╣
║ https://...║ 50            ║ 4.5           ║ 21              ║ New Lead   ║
║ https://...║ 75            ║ 4.8           ║ 24              ║ New Lead   ║
║ https://...║ 30            ║ 4.0           ║ 17              ║ New Lead   ║
╚════════════╩═══════════════╩═══════════════╩═════════════════╩════════════╝
```

**Look for:**
- Clean, organized data (no weird characters or formatting)
- All fields aligned and populated
- URLs are clickable
- Status dropdown shows "New Lead" for all records

---

## Performance Benchmarks

Track these metrics during testing:

| Metric | Test Mode (10 practices) | Production (150 practices) | Target |
|--------|-------------------------|---------------------------|--------|
| **Execution Time** | <2 minutes | <8 minutes | ✓ |
| **Apify Cost** | <$0.10 | <$2.00 | ✓ |
| **Success Rate** | 90%+ | 85%+ | ✓ |
| **Records Uploaded** | 5-10 | 50-100 | ✓ |

---

## Troubleshooting

### Common Issues

**Issue 1: "No results found" message**
- **Cause:** Search query too specific or no practices match filters
- **Fix:** Try broader search term (e.g., "veterinary" instead of "exotic animal veterinarian")

**Issue 2: "Notion rate limit exceeded (429)"**
- **Cause:** Too many API requests too quickly
- **Fix:** Increase batch delay in config (default: 3.5s, try 5s)

**Issue 3: "Invalid database schema" error**
- **Cause:** Notion database missing required properties
- **Fix:** Review Prerequisites section, ensure all properties exist with correct types

**Issue 4: Pipeline hangs during "Waiting for Apify results..."**
- **Cause:** Apify actor taking longer than expected
- **Fix:** Check Apify dashboard for actor status, may need to increase timeout

**Issue 5: Some practices not uploaded**
- **Cause:** Practices filtered out (no website, <10 reviews, or closed)
- **Fix:** This is expected behavior - check console logs for filter summary

---

## Bug Reporting

If you encounter a bug, please provide:

1. **Steps to Reproduce:** What did you do?
2. **Expected Behavior:** What should have happened?
3. **Actual Behavior:** What actually happened?
4. **Environment:**
   - Operating System (Windows/Mac/Linux)
   - Python version: `python --version`
   - Test mode or production mode?
5. **Console Output:** Copy/paste error messages
6. **Screenshots:** If visual issue in Notion database

**Submit bugs to:** [Your bug tracking system or email]

---

## Acceptance Checklist

Mark all as complete before considering FEAT-001 validated:

- [ ] Test 1: Test mode (10 practices) passes
- [ ] Test 2: Notion records have correct data
- [ ] Test 3: Full pipeline (150 practices) completes in <8 minutes
- [ ] Test 4: De-duplication prevents duplicate records
- [ ] Test 5: Initial scores calculated correctly
- [ ] Test 6: Error handling provides clear messages
- [ ] Performance benchmarks met (time, cost, success rate)
- [ ] Visual checks pass (Notion database looks correct)
- [ ] No unresolved bugs or issues

---

**Template Version:** 1.0.0
**Last Updated:** 2025-11-03
**Next Review:** After first production run
