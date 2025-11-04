# FEAT-002 Manual E2E Testing Guide

**Status:** Ready for Testing
**Date:** 2025-11-04
**Estimated Testing Time:** 30-60 minutes

---

## 🎯 Testing Objectives

1. Validate pipeline executes without errors
2. Verify cost tracking and budget enforcement
3. Confirm Notion updates preserve sales fields
4. Validate extraction quality (vet count, decision maker, personalization)
5. Test error handling and retry logic
6. Confirm performance meets targets (12-14 min for 150 practices)

---

## ⚠️ Prerequisites

### 1. Environment Setup
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Verify dependencies installed
pip list | grep -E "crawl4ai|openai|tiktoken|notion"
```

**Expected versions:**
- crawl4ai==0.7.6
- openai==2.7.1
- tiktoken==0.8.0
- notion-client==2.2.1

### 2. API Keys Configured
```bash
# Check .env file has all required keys
cat .env | grep -E "APIFY_API_KEY|OPENAI_API_KEY|NOTION_API_KEY|NOTION_DATABASE_ID"
```

### 3. Notion Database Ready
- Database ID: `2a0edda2a9a081d98dc9daa43c65e744`
- At least 10 practices with:
  - Website URLs populated
  - Enrichment Status NOT "Completed" (or >30 days old)
  - Some with sales workflow fields set (to test preservation)

### 4. OpenAI Budget Check
- Verify account has active API key
- Check usage limits for current tier
- Budget: $1.00 hard limit (expected usage: $0.03-$0.05 for 150 practices)

---

## 🧪 Testing Phases

### Phase 1: Dry Run Preview (0 cost, 0 risk)

**Purpose:** Validate Notion query without making API calls

```bash
python test_e2e_enrichment.py --dry-run --limit 10
```

**What to Check:**
- ✅ Script runs without errors
- ✅ Notion query returns practices
- ✅ Practice names and websites look correct
- ✅ Cost estimate displayed (~$0.001 for 10 practices)

**Expected Output:**
```
Found 10 practices needing enrichment

Practices that would be enriched:
1. Boston Veterinary Clinic
   Website: https://bostonveterinaryclinic.com
   ID: 12345678...

...

Estimated cost: $0.0012
```

**If Dry Run Fails:**
- Check .env file has correct NOTION_API_KEY and NOTION_DATABASE_ID
- Verify Notion database has practices with websites
- Check Notion API permissions (integration must have access to database)

---

### Phase 2: Single Practice Test (minimal cost: ~$0.0001)

**Purpose:** Validate full pipeline with 1 practice

```bash
python test_e2e_enrichment.py --limit 1
```

**Confirmation Prompt:**
- Review practice name and website
- Confirm estimated cost
- Type `yes` to proceed

**What to Check:**
1. **Website Scraping:**
   - ✅ Scraper finds 2-5 pages (homepage + /about or /team)
   - ✅ No timeout errors
   - ✅ Content extracted successfully

2. **LLM Extraction:**
   - ✅ Token count logged before API call
   - ✅ Budget check passes
   - ✅ OpenAI call succeeds
   - ✅ Extraction returns valid VetPracticeExtraction object
   - ✅ Actual cost logged (should be ~$0.0001)

3. **Notion Update:**
   - ✅ Notion API call succeeds
   - ✅ Enrichment Status → "Completed"
   - ✅ Last Enrichment Date → current timestamp

4. **Sales Field Preservation:**
   - ✅ Check Notion record manually - verify these fields UNCHANGED:
     - Status (New/Contacted/etc.)
     - Assigned To
     - Research Notes
     - Call Notes
     - Last Contact Date

5. **Results File:**
   - ✅ Check `data/test_results/enrichment_results_1practices_TIMESTAMP.txt`
   - ✅ Verify detailed extraction logged

**Expected Console Output:**
```
Step 1: Querying Notion... ✅
Step 2: Scraping 1 website... ✅ (3 pages in 5.2s)
Step 3: Extracting with OpenAI... ✅ (150 tokens, $0.000121)
Step 4: Updating Notion... ✅
Step 5: Retrying failures... (0 failures)
Step 6: Scoring disabled

Total: 1, Successful: 1, Failed: 0
Cost: $0.000121, Time: 8.3s
```

**If Single Practice Fails:**
- **Scraping fails (0 pages):** Website may block crawlers - try different practice
- **LLM extraction fails:** Check OpenAI API key, account limits
- **Notion update fails:** Check Notion API key, database schema
- **Cost exceeds $0.001:** Investigate - may indicate issue with token counting

---

### Phase 3: Three Practice Test (cost: ~$0.0004)

**Purpose:** Validate concurrency and variety

```bash
python test_e2e_enrichment.py --limit 3
```

**What to Check:**
1. **Concurrent Scraping:**
   - ✅ All 3 practices scraped concurrently (should take 5-10s total, not 15-30s)
   - ✅ Mix of success (2-5 pages) and potential failures (0 pages if blocking)

2. **Sequential Extraction:**
   - ✅ Extractions happen sequentially (budget check before each)
   - ✅ Cost logged every 10 practices (won't trigger with only 3)
   - ✅ All 3 extractions succeed (or fail gracefully)

3. **Data Quality:**
   - ✅ At least 60% vet count detected
   - ✅ At least 50% decision maker email found
   - ✅ Personalization context has 1-3 facts

4. **Performance:**
   - ✅ Total time: 15-25 seconds
   - ✅ Average: 5-8 seconds per practice

**Expected Output:**
```
Total: 3, Successful: 3, Failed: 0
Cost: $0.000363, Time: 18.7s

Successful Extractions:
  • Boston Vet Clinic
    Vet Count: 3 (high)
    Decision Maker: Dr. Sarah Johnson
    Email: sjohnson@bostonvet.com
    Personalization: 2 facts
    Pages Scraped: 4
```

---

### Phase 4: Test Mode (10 practices, cost: ~$0.0012)

**Purpose:** Full test mode validation

```bash
python test_e2e_enrichment.py --limit 10 --test-mode
```

**What to Check:**
1. **Scale Testing:**
   - ✅ All 10 practices processed
   - ✅ No pipeline crashes
   - ✅ Cost stays under $0.002

2. **Error Handling:**
   - ✅ Individual failures don't crash pipeline
   - ✅ Scrape failures marked as "scrape_failed"
   - ✅ LLM failures marked as "llm_failed"
   - ✅ Retry logic executes for failures

3. **Performance:**
   - ✅ Total time: 1-2 minutes
   - ✅ Scraping: ~30 seconds
   - ✅ Extraction: ~30 seconds
   - ✅ Notion updates: ~10 seconds

4. **Cost Tracking:**
   - ✅ Cost logged during execution
   - ✅ Final cost summary accurate
   - ✅ Average cost per practice: $0.000121

5. **Success Rate:**
   - ✅ ≥95% scraping success (9-10 practices)
   - ✅ ≥97% extraction success (9-10 practices)
   - ✅ 100% Notion update success (for successful extractions)

**Expected Output:**
```
Total: 10, Successful: 9-10, Failed: 0-1
Cost: $0.001089 - $0.001210
Time: 60-120s (1-2 minutes)
```

---

### Phase 5: Production Run (150 practices, cost: ~$0.03-$0.05)

**⚠️ ONLY RUN AFTER PHASES 1-4 PASS**

```bash
python test_e2e_enrichment.py
```

**Confirmation Required:**
- Review full list of practices
- Confirm cost estimate
- Type `yes` to proceed

**What to Check:**
1. **Performance:**
   - ✅ Total time: 12-14 minutes
   - ✅ Scraping: ~10-12 minutes (5 concurrent)
   - ✅ Extraction: ~1-2 minutes (sequential)

2. **Cost:**
   - ✅ Total cost: ≤$0.05
   - ✅ Average cost: ~$0.000121 per practice

3. **Data Quality:**
   - ✅ ≥60% vet count detection
   - ✅ ≥50% decision maker email found
   - ✅ ≥70% personalization context

4. **Success Rate:**
   - ✅ ≥95% scraping success (142+ practices)
   - ✅ ≥97% extraction success (145+ practices)

---

## 🔍 Manual Validation Checklist

### After Each Test, Check Notion Database:

1. **Enrichment Fields Updated:**
   - ✅ Enrichment Status = "Completed"
   - ✅ Last Enrichment Date = current date
   - ✅ Confirmed Vet Count (Total) = number (not null)
   - ✅ Vet Count Confidence = high/medium/low
   - ✅ Decision Maker Name = populated (if found)
   - ✅ Decision Maker Email = valid email (if found)
   - ✅ Personalization Context = 1-3 facts (if found)
   - ✅ 24/7 Emergency Services = true/false
   - ✅ Online Booking = true/false

2. **Sales Fields UNCHANGED:**
   - ✅ Status = same as before
   - ✅ Assigned To = same as before
   - ✅ Research Notes = same as before
   - ✅ Call Notes = same as before
   - ✅ Last Contact Date = same as before

3. **Failed Practices:**
   - ✅ Enrichment Status = "Failed" (if marked)
   - ✅ Enrichment Error = error message populated

---

## 🐛 Troubleshooting

### Scraping Issues

**Problem:** 0 pages scraped for all practices
**Solution:**
- Check internet connection
- Verify Crawl4AI 0.7.6 installed (`pip show crawl4ai`)
- Try different practice with simpler website

**Problem:** Scraping very slow (>30s per practice)
**Solution:**
- Check `page_timeout` setting (default 30s)
- Some websites are slow - expected behavior
- Reduce `max_pages` if needed

### LLM Extraction Issues

**Problem:** "Cost limit exceeded" error
**Solution:**
- Budget is $1.00 - shouldn't happen with 150 practices
- Check if token counting is working (`cost_tracker.py`)
- Review actual token counts in logs

**Problem:** All extractions return None
**Solution:**
- Check OpenAI API key valid
- Check account has available credits
- Review OpenAI API error messages in logs

### Notion Update Issues

**Problem:** "Notion API error: Invalid property"
**Solution:**
- Check Notion database schema matches expected fields
- Run spike test: `python docs/features/FEAT-002_website-enrichment/spike_notion_partial_updates.py`

**Problem:** Sales fields getting overwritten
**Solution:**
- This should NOT happen (partial updates validated)
- Check `notion_enrichment.py` - ensure only enrichment fields in properties dict
- Report as bug if this occurs

---

## 📊 Acceptance Criteria Validation

After testing, validate these key ACs from `acceptance.md`:

- **AC-FEAT-002-001:** ✅ Multi-page scraping works (homepage + /about + /team)
- **AC-FEAT-002-002:** ✅ 150 practices in 12-14 minutes
- **AC-FEAT-002-003:** ✅ 100% valid Pydantic objects
- **AC-FEAT-002-009:** ✅ tiktoken token counting before API call
- **AC-FEAT-002-010:** ✅ Cost abort at $1.00 threshold
- **AC-FEAT-002-011:** ✅ Partial updates preserve sales fields
- **AC-FEAT-002-027:** ✅ 12-14 min for 150 practices
- **AC-FEAT-002-028:** ✅ Total cost ≤$0.50 (target: $0.05)
- **AC-FEAT-002-029:** ✅ ≥60% vet count detection
- **AC-FEAT-002-030:** ✅ ≥50% decision maker email found

---

## 📝 Test Results Template

Copy this template for documenting each test:

```markdown
## Test Run: [DATE] - [PRACTICE COUNT] practices

**Configuration:**
- Limit: [number]
- Test Mode: [yes/no]
- Crawl4AI: [version]
- OpenAI Model: [model]

**Results:**
- Total Practices: [number]
- Successful: [number] ([percent]%)
- Failed: [number] ([percent]%)
- Total Cost: $[amount]
- Elapsed Time: [seconds]s ([minutes]m)

**Data Quality:**
- Vet Count Detection: [number]/[total] ([percent]%)
- Decision Maker Email Found: [number]/[total] ([percent]%)
- Personalization Context: [number]/[total] ([percent]%)

**Issues Encountered:**
- [List any issues, errors, or unexpected behavior]

**Notion Validation:**
- [X] Enrichment fields updated correctly
- [X] Sales fields preserved
- [X] Failed practices marked appropriately

**Notes:**
- [Any additional observations or findings]
```

---

## ✅ Sign-Off Criteria

Phase 2 testing complete when:
- [X] All 5 testing phases pass
- [X] Success rate ≥95% for 10-practice test
- [X] Cost ≤$0.05 for 150-practice test
- [X] Performance ≤14 minutes for 150 practices
- [X] Sales fields preserved (validated manually in Notion)
- [X] All critical ACs validated
- [X] Test results documented

---

**Ready to start?** Begin with Phase 1 (Dry Run).
