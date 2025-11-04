# How to Run Website Enrichment

**Feature:** FEAT-002 Website Enrichment
**Status:** ✅ Production Ready
**Last Updated:** 2025-11-04

---

## Quick Start

```bash
# Activate virtual environment
source venv/bin/activate

# Preview what will be enriched (no API calls, no cost)
python test_e2e_enrichment.py --dry-run

# Run enrichment on all practices needing enrichment
echo "yes" | python test_e2e_enrichment.py
```

---

## What This Does

The enrichment pipeline:

1. **Queries Notion** for practices needing enrichment (new OR stale >30 days)
2. **Scrapes websites** using multi-page crawling (homepage + /about + /team pages)
3. **Extracts data** with OpenAI GPT-4o-mini (vet count, decision maker, personalization facts)
4. **Updates Notion** with enrichment data while preserving sales fields
5. **Tracks costs** with hard abort at $1.00

---

## Fields Updated

**Always Updated:**
- Enrichment Status → "Completed"
- Last Enrichment Date → current timestamp
- 24/7 Emergency Services → true/false
- Online Booking → true/false
- Patient Portal → true/false
- Telemedicine → true/false

**Conditionally Updated (if found on website):**
- Confirmed Vet Count (Total)
- Vet Count Confidence (high/medium/low)
- Decision Maker Name
- Decision Maker Role
- Decision Maker Email ⭐ (critical for outreach)
- Decision Maker Phone
- Specialty Services
- Personalization Context ⭐ (1-3 specific facts for cold calls)
- Awards/Accreditations
- Recent News/Updates
- Community Involvement
- Practice Philosophy/Mission

**Sales Fields Preserved (NEVER changed):**
- Status
- Assigned To
- Research Notes
- Call Notes
- Last Contact Date

---

## Usage Examples

### Preview Only (No Cost)
```bash
python test_e2e_enrichment.py --dry-run
```
Shows which practices will be enriched and estimated cost.

### Enrich Specific Number
```bash
# Enrich up to 10 practices
python test_e2e_enrichment.py --limit 10

# Enrich 1 practice for testing
python test_e2e_enrichment.py --limit 1
```

### Enrich All
```bash
# No limit - enriches all practices needing enrichment
python test_e2e_enrichment.py
```

### Auto-Confirm (for automation)
```bash
# Pipe "yes" to skip confirmation prompt
echo "yes" | python test_e2e_enrichment.py --limit 10
```

---

## Expected Performance

Based on actual test runs:

**Success Rate:** ~40-50% (many websites block crawlers - this is normal)

**Per Practice:**
- Time: 5-7 seconds
- Cost: $0.0008 per practice
- Pages scraped: 1-4 pages

**For 150 Practices:**
- Time: 12-15 minutes
- Cost: ~$0.05-$0.12
- Successful: 60-75 practices (40-50% success rate)

---

## Cost Tracking

- **Budget Limit:** $1.00 hard abort
- **Estimated Cost:** $0.000121 per extraction (validated via testing)
- **Safety Buffer:** 10% added to estimates
- **Cost Logged:** Every 10 practices during execution

The pipeline will **automatically abort** if cumulative cost exceeds $1.00.

---

## Common Issues

### "No practices found needing enrichment"

**Cause:** All practices already enriched within last 30 days

**Solution:**
- Check Notion database - verify practices have websites
- Wait 30 days for re-enrichment window
- Manually clear "Enrichment Status" in Notion to force re-enrichment

### "scrape_failed: Website scraping failed (0 pages scraped)"

**Cause:** Website blocks crawlers or times out

**Solution:**
- This is expected for ~50% of websites
- Nothing you can do - website is blocking automated access
- Focus on the successful enrichments

### "Notion API error: Field X is not a property"

**Cause:** Notion database schema doesn't have required field

**Solution:**
- Run: `python docs/features/FEAT-002_website-enrichment/spike_notion_schema.py`
- Verify all enrichment fields exist in Notion database
- See `docs/features/FEAT-002_website-enrichment/architecture.md` for field names

### "Cost limit exceeded"

**Cause:** Cumulative cost hit $1.00 limit

**Solution:**
- This shouldn't happen with normal usage (~$0.05 for 150 practices)
- Check OpenAI API - may have pricing change
- Review cost tracking logs for anomalies

---

## Results

Results are automatically saved to:
```
data/test_results/enrichment_results_Npractices_TIMESTAMP.txt
```

Check this file for:
- Detailed extraction results per practice
- Success/failure breakdown
- Cost tracking
- Error messages

---

## Re-Enrichment

Practices are automatically re-enriched if:
- Enrichment Status != "Completed", OR
- Last Enrichment Date > 30 days ago

This ensures data stays fresh without redundant API calls.

---

## Integration with FEAT-003 (Future)

Once FEAT-003 (Lead Scoring) is implemented, enrichment will automatically trigger scoring updates. For now, enrichment runs standalone.

---

## Troubleshooting

**Check logs:**
```bash
# View latest enrichment log
cat enrichment_full_run.log

# View saved results
cat data/test_results/enrichment_results_*.txt
```

**Verify Notion updates:**
1. Open Notion database
2. Filter by: Enrichment Status = "Completed"
3. Check: Last Enrichment Date = today
4. Verify: Personalization Context has content
5. Confirm: Sales fields unchanged

**Test with 1 practice:**
```bash
python test_e2e_enrichment.py --limit 1
```
Cheapest way to debug issues (~$0.0001 cost).

---

## API Keys Required

Ensure `.env` file has:
```
OPENAI_API_KEY=sk-...
NOTION_API_KEY=ntn_...
NOTION_DATABASE_ID=...
```

Missing keys will cause immediate failure.

---

## Next Steps

1. Review enriched practices in Notion
2. Use Personalization Context for cold call prep
3. Follow up on practices with Decision Maker emails
4. Re-run enrichment monthly for fresh data

---

**Questions?** See `/docs/features/FEAT-002_website-enrichment/TESTING_GUIDE.md` for detailed testing documentation.
