# FEAT-003 Lead Scoring - Quick Start Guide

**Status:** Ready for Testing
**Estimated Time:** 5-10 minutes for initial validation

## Prerequisites

1. ✅ Google Maps scraping completed (FEAT-001) - practices loaded in Notion
2. ✅ Website enrichment completed (FEAT-002) - practices enriched with vet count, decision makers, etc.
3. ✅ Notion database with required fields
4. ✅ Environment variables set (.env file)

## Step-by-Step Validation

### Step 1: Check Notion Schema (2 minutes)

Verify all required fields exist in your Notion database:

```bash
python3 check_notion_schema.py
```

**Expected Output:**
```
✅ Database schema is COMPLETE and ready for scoring!
```

**If fields are missing:**
- The script will list exactly which fields to add
- Open Notion database in browser
- Add missing fields with specified types
- Re-run schema check

### Step 2: List Available Practices (1 minute)

Get Notion page IDs for testing:

```bash
python3 list_notion_practices.py --limit 10
```

**Expected Output:**
```
Found 10 practices:

1. Boston Veterinary Hospital
   Page ID: 2a0edda2-a9a0-81d9-8dc9-daa43c65e744
   Vets: 5 | Rating: 4.7★ | Reviews: 120
   Enrichment: Completed | Lead Score: Not scored
   Website: https://example.com

...
```

**Copy a Page ID** from the output for the next step.

### Step 3: Score Single Practice (30 seconds)

Test scoring on one practice:

```bash
# Replace with actual Page ID from Step 2
python3 score_leads.py --practice-id 2a0edda2-a9a0-81d9-8dc9-daa43c65e744
```

**Expected Output:**
```
Scoring practice 2a0edda2-a9a0-81d9-8dc9-daa43c65e744...

============================================================
SCORING RESULT
============================================================
Practice ID: 2a0edda2-a9a0-81d9-8dc9-daa43c65e744
Lead Score: 85/120
Priority Tier: 🔥 Hot
Practice Size: Sweet Spot

Component Scores:
  Practice Size: 40/40
  Call Volume: 30/40
  Technology: 15/20
  Baseline: 16/20
  Decision Maker: 10/10

Confidence:
  Multiplier: 1.0x
  Total Before: 111
  Total After: 111

Duration: 1.23s
============================================================
```

### Step 4: Verify in Notion (1 minute)

1. Open Notion database in browser
2. Find the practice you just scored (by name)
3. **Check these fields were updated:**
   - ✅ Lead Score: Shows number (e.g., 85)
   - ✅ Priority Tier: Shows emoji and tier (e.g., 🔥 Hot)
   - ✅ Score Breakdown: Has JSON text
   - ✅ Scoring Status: Shows "Scored"
4. **Check these fields were NOT changed:**
   - ✅ Name, Website, Phone (unchanged)
   - ✅ Vet Count, Emergency 24/7 (unchanged)
   - ✅ Enrichment Status (unchanged)

**If fields weren't updated:**
- Check for errors in terminal output
- Verify Page ID is correct (UUID format, not Google Place ID)
- Run with `--log-level DEBUG` for detailed logs

### Step 5: Score Batch of 10 (2-3 minutes)

Test batch scoring:

```bash
python3 score_leads.py --batch --limit 10
```

**Expected Output:**
```
Querying practices...
Found 10 practices to score

Scoring practices  [####################################]  100%

============================================================
BATCH SCORING SUMMARY
============================================================
Total Practices: 10
Succeeded: 10 (100.0%)
Failed: 0 (0.0%)

Duration: 25.3s
Average: 2.53s per practice

Priority Distribution:
  🔥 Hot (80-120): 2
  🌡️  Warm (50-79): 5
  ❄️  Cold (20-49): 3
  ⛔ Out of Scope (<20): 0
============================================================
```

**Verify in Notion:**
- All 10 practices should have Lead Score values
- Priority Tier emojis showing
- Score Breakdown populated

### Step 6: Score All Practices (5-15 minutes)

Once validation passes, score all scraped practices:

```bash
# Score everything
python3 score_leads.py --batch --all
```

**Expected for 150 practices:**
- Duration: ~5-10 minutes (2-4 seconds per practice)
- Success rate: > 95%
- Hot leads: 15-25% of total
- Warm leads: 30-40% of total
- Cold leads: 30-40% of total

## Troubleshooting

### Error: "No module named pytest"

This is expected - pytest is for development testing, not production use.

**Run manual validation instead:**
```bash
python3 score_leads.py --practice-id <PAGE_ID>
```

### Error: "setup_logging() got an unexpected keyword argument 'level'"

This was fixed. Pull latest code or verify line 192 of score_leads.py uses `log_level=` not `level=`.

### Error: Practice ID format wrong

**Symptoms:**
```
Error: Practice not found
```

**Cause:** Using Google Place ID (starts with "ChIJ") instead of Notion Page ID (UUID format)

**Solution:** Use `list_notion_practices.py` to get correct Page IDs

### Error: "Circuit breaker is OPEN"

**Cause:** 5 consecutive scoring failures triggered circuit breaker

**Solution:**
```bash
# Check status
python3 score_leads.py --status

# Reset circuit breaker
python3 score_leads.py --reset-circuit-breaker

# Retry with smaller batch
python3 score_leads.py --batch --limit 5
```

### Error: Missing Notion fields

**Symptoms:**
```
KeyError: 'Lead Score'
```

**Solution:**
```bash
# Check schema
python3 check_notion_schema.py

# Add missing fields in Notion UI
# Re-run schema check to verify
```

### Scores seem wrong

**Check manually:**
1. Look at Score Breakdown JSON in Notion
2. Verify component scores make sense
3. Compare to expected calculation in SCORING_FORMULA_CORRECTION.md

**Example:**
- Practice with 5 vets, emergency, 100 reviews, 4.5 rating, website
- Expected: ~61 pts (25 practice + 20 reviews + 16 baseline)
- If actual is very different, report as bug

## Next Steps After Validation

1. ✅ All practices scored successfully
2. Create Notion views for sales team:
   - **Hot Leads View:** Filter Priority Tier = 🔥 Hot, Sort by Lead Score desc
   - **Sweet Spot Targets:** Filter Practice Size = Sweet Spot, Priority = Hot or Warm
   - **Ready for Outreach:** Filter Scoring Status = Scored, Priority != Out of Scope
3. Update documentation with `/update-docs`
4. Train sales team on priority tiers
5. Begin outreach to Hot leads

## Commands Reference

```bash
# Schema validation
python3 check_notion_schema.py

# List practices
python3 list_notion_practices.py [--limit N]

# Score single practice
python3 score_leads.py --practice-id <PAGE_ID>

# Score batch
python3 score_leads.py --batch --limit N
python3 score_leads.py --batch --all

# Circuit breaker management
python3 score_leads.py --status
python3 score_leads.py --reset-circuit-breaker

# Debug mode
python3 score_leads.py --practice-id <PAGE_ID> --log-level DEBUG
```

## Success Criteria

✅ **Phase 1 Validation (Single Practice):**
- Scoring completes without errors
- All 5 Notion fields updated
- Score matches manual calculation
- Other fields preserved

✅ **Phase 2 Validation (Batch 10):**
- 100% success rate
- All practices updated in < 30 seconds
- Priority distribution reasonable

✅ **Phase 3 Production (All Practices):**
- > 95% success rate
- Average < 3 seconds per practice
- Statistical distribution normal
- Ready for sales workflow

## Getting Help

- **Test failures:** See SCORING_FORMULA_CORRECTION.md
- **Detailed validation:** See MANUAL_VALIDATION_PLAN.md
- **Implementation details:** See IMPLEMENTATION_SUMMARY.md
- **Scoring logic:** See prd.md and architecture.md
