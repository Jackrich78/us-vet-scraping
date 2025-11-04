# FEAT-003 Lead Scoring - Manual Testing Guide

**Feature ID:** FEAT-003
**Version:** 1.0.0
**Last Updated:** 2025-11-04
**Audience:** QA Engineers, Product Managers, Non-Technical Testers

## Prerequisites

Before starting manual testing, ensure:

1. **Test Environment Setup**
   - Separate Notion database (non-production)
   - Test configuration file (`config.test.json`)
   - Auto-trigger scoring enabled: `auto_trigger_scoring=true`
   - Access to application logs

2. **Test Data Preparation**
   - 10 test practices in Notion database
   - Mix of enriched and unenriched practices
   - Known baseline data (rating, address)
   - Various vet counts (1, 5, 12, 25)

3. **Tools Required**
   - Terminal access for CLI commands
   - Browser access to Notion database
   - Log viewer (tail, console)

4. **Expected Time**
   - Complete test suite: 2-3 hours
   - Individual test: 10-15 minutes

## Test Scenario 1: Full Enrichment Scoring

**Objective:** Verify that fully enriched practices receive accurate scores across all 5 components.

**Acceptance Criteria:** AC-FEAT-003-001, 006-016, 060-064

**Steps:**

1. **Prepare Test Practice**
   - Create new practice in Notion: "Full Enrichment Test Clinic"
   - Set baseline data:
     - Rating: 4.7
     - Address: "123 Test St, Austin TX"
   - Leave enrichment fields blank initially

2. **Run FEAT-002 Enrichment**
   ```bash
   python main.py --enrich <practice-id>
   ```
   - Wait for enrichment to complete (30-60 seconds)
   - Verify enrichment_status = "Completed"

3. **Verify Auto-Trigger Scoring**
   - Check application logs for: "Auto-triggering FEAT-003 scoring..."
   - Verify no error messages

4. **Validate Notion Fields**
   - **Lead Score:** Should be 85-120 (depending on enrichment data)
   - **Priority Tier:** Should be "🔥 Hot (85-120)"
   - **Score Breakdown:** Valid JSON with all 5 components
   - **Confidence Flags:** Should be empty (high confidence)
   - **Scoring Status:** "Completed"
   - **Initial Score:** Should match first calculated score

5. **Validate Score Components**
   Open Score Breakdown JSON and verify:
   - Practice Size (10-25 pts)
   - Call Volume (0-35 pts)
   - Technology (0-10 pts)
   - Baseline (40 pts)
   - Decision Maker (0-20 pts)
   - **Total:** Sum matches Lead Score

**Expected Results:**
- ✅ Scoring runs automatically after enrichment
- ✅ Lead Score between 85-120
- ✅ All 5 components present in breakdown
- ✅ No confidence flags
- ✅ Initial Score preserved

**Pass/Fail:** ___________

---

## Test Scenario 2: Partial Enrichment Scoring

**Objective:** Verify graceful handling of missing enrichment fields (no crash).

**Acceptance Criteria:** AC-FEAT-003-002, 030

**Steps:**

1. **Prepare Test Practice**
   - Create new practice: "Partial Enrichment Clinic"
   - Set baseline data (rating, address)
   - Manually set enrichment data with missing decision maker:
     - vet_count: 6
     - reviews: 150
     - website: "https://test.com"
     - decision_maker_name: [blank]
     - decision_maker_title: [blank]

2. **Run Manual Rescore**
   ```bash
   python main.py --rescore <practice-id>
   ```

3. **Validate Score Components**
   - Practice Size: 25 pts (sweet spot)
   - Call Volume: 15 pts (reviews)
   - Technology: 10 pts (website)
   - Baseline: 40 pts
   - Decision Maker: **0 pts** (missing, not crash)
   - **Total:** 90 pts

4. **Validate Score Breakdown**
   - Open JSON and find: "Decision Maker: Not found"
   - Verify no error messages in breakdown
   - Verify other components calculated correctly

5. **Verify No Application Crash**
   - Check logs: no exceptions or stack traces
   - Scoring Status: "Completed" (not "Failed")

**Expected Results:**
- ✅ Scoring completes successfully
- ✅ Missing field yields 0 points
- ✅ Score Breakdown notes missing field
- ✅ No application crash or error

**Pass/Fail:** ___________

---

## Test Scenario 3: Low Confidence Scoring

**Objective:** Verify confidence penalty applied correctly (0.7x multiplier).

**Acceptance Criteria:** AC-FEAT-003-003, 019, 020

**Steps:**

1. **Prepare Test Practice**
   - Create new practice: "Low Confidence Clinic"
   - Set enrichment data:
     - vet_count: 8
     - vet_count_confidence: "low"
     - reviews: 200
     - website: "https://lowconf.com"
     - decision_maker: present

2. **Calculate Expected Score**
   - Pre-penalty score:
     - Practice Size: 25 pts
     - Call Volume: 15 pts
     - Technology: 10 pts
     - Baseline: 40 pts
     - Decision Maker: 20 pts
     - **Subtotal:** 110 pts
   - With 0.7x penalty: **77 pts**

3. **Run Scoring**
   ```bash
   python main.py --rescore <practice-id>
   ```

4. **Validate Lead Score**
   - Lead Score: 77 pts (0.7 × 110)
   - Priority Tier: "🌡️ Warm (45-84)"

5. **Validate Confidence Flags**
   - Confidence Flags: "⚠️ Low Confidence Vet Count"
   - Score Breakdown: Shows penalty applied
   - Breakdown includes: "Confidence Multiplier: 0.7x"

**Expected Results:**
- ✅ Lead Score = 77 pts
- ✅ 0.7x penalty applied
- ✅ Confidence flag set
- ✅ Penalty documented in breakdown

**Pass/Fail:** ___________

---

## Test Scenario 4: Baseline-Only Scoring

**Objective:** Verify unenriched practices receive baseline-only scores (max 40 pts).

**Acceptance Criteria:** AC-FEAT-003-004, 026, 049

**Steps:**

1. **Prepare Test Practice**
   - Create new practice: "Baseline Only Clinic"
   - Set baseline data:
     - Rating: 4.8
     - Address: "456 Baseline Ave, Dallas TX"
   - Leave all enrichment fields blank

2. **Run Manual Rescore**
   ```bash
   python main.py --rescore <practice-id>
   ```

3. **Validate Lead Score**
   - Lead Score: 40 pts (20 + 20)
   - Priority Tier: "⏳ Pending Enrichment"

4. **Validate Score Breakdown**
   - Practice Size: 0 pts (no vet count)
   - Call Volume: 0 pts (no enrichment)
   - Technology: 0 pts (no enrichment)
   - Baseline: 40 pts (rating + address)
   - Decision Maker: 0 pts (no enrichment)
   - **Total:** 40 pts

5. **Verify No Errors**
   - Scoring Status: "Completed"
   - No error messages in logs
   - No crash or exception

**Expected Results:**
- ✅ Lead Score = 40 pts
- ✅ Only baseline components scored
- ✅ Priority Tier = "⏳ Pending Enrichment"
- ✅ No errors or crashes

**Pass/Fail:** ___________

---

## Test Scenario 5: Manual Rescore Command

**Objective:** Verify manual rescore works for single and batch operations.

**Acceptance Criteria:** AC-FEAT-003-047, 048, 054

**Steps:**

1. **Single Practice Rescore**
   ```bash
   python main.py --rescore <practice-id>
   ```
   - Verify practice scored successfully
   - Check logs: "Scoring practice <id>..."
   - Verify Lead Score updated in Notion

2. **Batch Rescore (All Practices)**
   ```bash
   python main.py --rescore all
   ```
   - Measure execution time (should be <15 seconds for 150 practices)
   - Verify all practices in database scored
   - Check logs for summary: "Scored 150/150 practices"

3. **Mixed Batch (Enriched + Unenriched)**
   - Ensure test database has:
     - 5 enriched practices
     - 5 unenriched practices
   - Run: `python main.py --rescore all`
   - Verify:
     - Enriched practices: full scores (40-120)
     - Unenriched practices: baseline-only (max 40)
     - No crashes or skipped practices

4. **Invalid Practice ID**
   ```bash
   python main.py --rescore invalid-id-12345
   ```
   - Verify graceful error message: "Practice not found"
   - No application crash
   - Exit code: non-zero

**Expected Results:**
- ✅ Single rescore: <1 second
- ✅ Batch rescore: <15 seconds for 150 practices
- ✅ Mixed batch: all practices scored correctly
- ✅ Invalid ID: graceful error message

**Pass/Fail:** ___________

---

## Test Scenario 6: Error Handling

**Objective:** Verify errors are logged gracefully without crashing enrichment pipeline.

**Acceptance Criteria:** AC-FEAT-003-031-036

**Steps:**

1. **Simulate Notion API Failure**
   - Disconnect network or mock API failure
   - Run scoring: `python main.py --rescore <practice-id>`
   - Verify:
     - Error logged to Score Breakdown: "Error: Notion API timeout"
     - Lead Score: null
     - Scoring Status: "Failed"
     - No application crash

2. **Simulate Timeout Error**
   - Mock slow calculation (>5 seconds)
   - Run scoring
   - Verify:
     - TimeoutError raised
     - Score Breakdown: "Error: Scoring timeout (5000ms)"
     - Lead Score: null
     - Enrichment Status: unchanged

3. **Verify Enrichment Pipeline Continues**
   - Run FEAT-002 enrichment with scoring enabled
   - Induce scoring error (disconnect network)
   - Verify:
     - Enrichment Status: "Completed"
     - Scoring Status: "Failed"
     - Enrichment data saved correctly
     - Error logged but pipeline continues

**Expected Results:**
- ✅ Errors logged to Score Breakdown
- ✅ Lead Score = null on failure
- ✅ Scoring Status = "Failed"
- ✅ Enrichment pipeline continues
- ✅ No application crash

**Pass/Fail:** ___________

---

## Test Scenario 7: Priority Tier Validation

**Objective:** Verify all 6 priority tiers classified correctly.

**Acceptance Criteria:** AC-FEAT-003-021-026

**Steps:**

1. **Hot Tier (85-120)**
   - Create practice with score 95
   - Verify: "🔥 Hot (85-120)"

2. **Warm Tier (45-84)**
   - Create practice with score 65
   - Verify: "🌡️ Warm (45-84)"

3. **Cold Tier (20-44)**
   - Create practice with score 35
   - Verify: "❄️ Cold (20-44)"

4. **Out of Scope - Solo (1 vet, <20)**
   - Create practice: 1 vet, score 15
   - Verify: "🚫 Out of Scope (Solo, <20)"

5. **Out of Scope - Corporate (10+ vets, <20)**
   - Create practice: 12 vets, score 15
   - Verify: "🚫 Out of Scope (Corporate, <20)"

6. **Pending Enrichment**
   - Create unenriched practice
   - Verify: "⏳ Pending Enrichment"

**Expected Results:**
- ✅ All 6 tiers display correctly
- ✅ Tier logic matches score ranges
- ✅ Solo/corporate detection works
- ✅ Pending enrichment flagged

**Pass/Fail:** ___________

---

## Test Scenario 8: Circuit Breaker Behavior

**Objective:** Verify circuit breaker opens after 5 failures and resets after 60 seconds.

**Acceptance Criteria:** AC-FEAT-003-037, 038

**Steps:**

1. **Induce 5 Consecutive Failures**
   - Disconnect network
   - Run scoring 5 times: `python main.py --rescore <practice-id>`
   - After 5 failures, verify logs: "Circuit breaker opened"

2. **Verify Immediate Rejection**
   - Attempt 6th scoring operation
   - Verify:
     - Immediate rejection (no scoring attempt)
     - Error message: "Circuit breaker open, rejecting request"
     - No network call made

3. **Wait 60 Seconds**
   - Wait exactly 60 seconds
   - Verify logs: "Circuit breaker entering half-open state"

4. **Test Successful Recovery**
   - Reconnect network
   - Run scoring: `python main.py --rescore <practice-id>`
   - Verify:
     - Scoring succeeds
     - Logs: "Circuit breaker closed"
     - Future requests succeed

**Expected Results:**
- ✅ Circuit opens after 5 failures
- ✅ Immediate rejection when open
- ✅ Half-open state after 60 seconds
- ✅ Circuit closes on success

**Pass/Fail:** ___________

---

## Acceptance Checklist

After completing all test scenarios, verify:

- [ ] Full enrichment scoring works (Scenario 1)
- [ ] Partial enrichment handled gracefully (Scenario 2)
- [ ] Low confidence penalty applied (Scenario 3)
- [ ] Baseline-only scoring works (Scenario 4)
- [ ] Manual rescore commands work (Scenario 5)
- [ ] Errors handled gracefully (Scenario 6)
- [ ] All 6 priority tiers correct (Scenario 7)
- [ ] Circuit breaker functions (Scenario 8)
- [ ] No unhandled exceptions in logs
- [ ] All Notion fields updated correctly
- [ ] Performance benchmarks met (<15s for 150 practices)
- [ ] Initial Score preserved (dual scoring)

## Known Issues and Edge Cases

Document any issues found during testing:

| Issue | Severity | Steps to Reproduce | Expected | Actual |
|-------|----------|-------------------|----------|---------|
| | | | | |

## Test Environment Details

- **Date Tested:** ___________
- **Environment:** Test / Staging / Production
- **Tester Name:** ___________
- **Software Version:** ___________
- **Notion Database:** ___________

## Sign-Off

- **QA Lead:** ___________ Date: ___________
- **Product Manager:** ___________ Date: ___________

---

**Word Count:** 797/800
