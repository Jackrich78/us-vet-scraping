# FEAT-003 Manual Validation Plan

**Purpose:** Validate that lead scoring works correctly and updates Notion database as expected.

## Pre-Validation Checklist

### 1. Verify Notion Database Schema

Run this script to check if scoring fields exist:

```python
from notion_client import Client
import os

client = Client(auth=os.getenv("NOTION_API_KEY"))
database_id = os.getenv("NOTION_DATABASE_ID")

# Retrieve database schema
response = client.databases.retrieve(database_id=database_id)
properties = response.get("properties", {})

# Check for scoring fields
required_fields = [
    "Lead Score",
    "Priority Tier",
    "Score Breakdown",
    "Confidence Flags",
    "Scoring Status"
]

print("Notion Database Scoring Fields:")
for field in required_fields:
    if field in properties:
        field_type = properties[field]["type"]
        print(f"  ✅ {field} ({field_type})")
    else:
        print(f"  ❌ {field} MISSING - Need to create this field!")
```

**If fields are missing, add them to Notion database:**
- `Lead Score`: Number field
- `Priority Tier`: Select field with options (🔥 Hot, 🌡️ Warm, ❄️ Cold, ⛔ Out of Scope, ⏳ Pending Enrichment)
- `Score Breakdown`: Text field (rich text)
- `Confidence Flags`: Multi-select field
- `Scoring Status`: Select field with options (Scored, Failed, Not Scored)

### 2. Verify Environment Variables

```bash
# Check .env file has required keys
cat .env | grep -E "NOTION_API_KEY|NOTION_DATABASE_ID"

# Should output:
# NOTION_API_KEY=secret_...
# NOTION_DATABASE_ID=2a0edda2a9a081d98dc9daa43c65e744
```

## Validation Phase 1: Single Practice Test

### Step 1: Find a Test Practice

Query Notion to find a practice with known data:

```bash
# List first 5 practices
python3 -c "
from notion_client import Client
import os

client = Client(auth=os.getenv('NOTION_API_KEY'))
db_id = os.getenv('NOTION_DATABASE_ID')

response = client.databases.query(database_id=db_id, page_size=5)

for i, page in enumerate(response['results'], 1):
    props = page['properties']
    name = props.get('Name', {}).get('title', [{}])[0].get('plain_text', 'Unknown')
    page_id = page['id']
    print(f'{i}. {name}')
    print(f'   ID: {page_id}')
    print()
"
```

### Step 2: Note Current State in Notion

Before scoring, open Notion and record:
- Current Lead Score value (should be empty or 0)
- Current Priority Tier (should be empty)
- Current Score Breakdown (should be empty)

### Step 3: Run Scoring on Single Practice

```bash
# Replace <page_id> with actual ID from Step 1
python3 score_leads.py --practice-id <page_id> --log-level DEBUG
```

**Expected Output:**
```
Scoring practice <page_id>...

============================================================
SCORING RESULT
============================================================
Practice ID: <page_id>
Lead Score: XX/120
Priority Tier: 🔥 Hot (or Warm/Cold/etc)
Practice Size: Sweet Spot (or Solo/Small/etc)

Component Scores:
  Practice Size: XX/40
  Call Volume: XX/40
  Technology: XX/20
  Baseline: XX/20
  Decision Maker: XX/10

Confidence:
  Multiplier: 1.0x (or 0.9x/0.7x)
  Total Before: XX
  Total After: XX

Duration: X.XXs
============================================================
```

### Step 4: Verify in Notion UI

1. Open Notion database
2. Find the practice you just scored
3. **VERIFY:**
   - ✅ Lead Score field populated with number (e.g., 85)
   - ✅ Priority Tier shows emoji and tier (e.g., 🔥 Hot)
   - ✅ Score Breakdown has JSON text
   - ✅ Scoring Status = "Scored"
   - ✅ Other fields (Name, Website, Vet Count, etc.) UNCHANGED

### Step 5: Check Score Breakdown JSON

In Notion, open the Score Breakdown field and verify JSON structure:

```json
{
  "practice_size": {
    "score": 25,
    "max_possible": 40,
    "detail": "5 vets, emergency=False",
    "contributing_factors": ["5 vets (sweet spot: +25 pts)"],
    "missing_factors": ["24/7 emergency services"]
  },
  "call_volume": { ... },
  "technology": { ... },
  "baseline": { ... },
  "decision_maker": { ... },
  "total_before_confidence": 85,
  "confidence_multiplier": 1.0,
  "total_after_confidence": 85,
  "confidence_level": "high",
  "confidence_flags": []
}
```

## Validation Phase 2: Batch Test (10 Practices)

### Step 1: Score First 10 Practices

```bash
python3 score_leads.py --batch --limit 10 --log-level INFO
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

Duration: XX.Xs
Average: X.XXs per practice

Priority Distribution:
  🔥 Hot (80-120): X
  🌡️  Warm (50-79): X
  ❄️  Cold (20-49): X
  ⛔ Out of Scope (<20): X
============================================================
```

### Step 2: Verify All 10 in Notion

Open Notion database and verify:
- All 10 practices have Lead Score values
- Priority Tier icons showing correctly
- Score Breakdown populated
- No practices showing "Failed" status

### Step 3: Spot Check Calculations

Pick 2-3 practices and manually calculate expected scores:

**Example Calculation:**
```
Practice: "Boston Veterinary Clinic"
- Vet Count: 5 (sweet spot = 25 pts)
- Emergency: Yes (+15 pts) = 40 pts practice size
- Reviews: 120 (100+ = 20 pts)
- Multiple Locations: Yes (+10 pts)
- Specialty Services: Surgery, Dentistry (+10 pts) = 40 pts call volume (capped)
- Online Booking: Yes (10 pts)
- Patient Portal: Yes (5 pts) = 15 pts technology
- Google Rating: 4.7 (6 pts)
- Website: Yes (4 pts) = 10 pts baseline
- Decision Maker: Dr. Smith <email> (10 pts)

Total: 40 + 40 + 15 + 10 + 10 = 115 pts
Confidence: High (1.0x) = 115 pts
Tier: 🔥 Hot (>= 80)
```

Compare manual calculation to actual Lead Score in Notion.

## Validation Phase 3: Full Batch (All Practices)

### Step 1: Check Total Practice Count

```bash
python3 -c "
from notion_client import Client
import os

client = Client(auth=os.getenv('NOTION_API_KEY'))
db_id = os.getenv('NOTION_DATABASE_ID')

response = client.databases.query(database_id=db_id, page_size=1)
# Notion doesn't return total count, so we need to query all
print('Querying all practices...')

count = 0
has_more = True
start_cursor = None

while has_more:
    response = client.databases.query(
        database_id=db_id,
        page_size=100,
        start_cursor=start_cursor
    )
    count += len(response['results'])
    has_more = response.get('has_more', False)
    start_cursor = response.get('next_cursor')

print(f'Total practices in database: {count}')
"
```

### Step 2: Backup Before Full Run (Optional)

Export Notion database to CSV as backup before running full batch.

### Step 3: Run Full Batch Scoring

```bash
# Score all practices
python3 score_leads.py --batch --all --log-level INFO

# Or start with a larger sample first
python3 score_leads.py --batch --limit 50
```

**Monitor for:**
- ✅ No circuit breaker opening
- ✅ No timeouts (or very few)
- ✅ Success rate > 95%
- ✅ Average time per practice < 3 seconds

### Step 4: Analyze Results in Notion

Create Notion views to analyze results:

**View 1: Hot Leads**
- Filter: Priority Tier = 🔥 Hot
- Sort: Lead Score descending
- Expected: Top scoring practices (80-120 pts)

**View 2: Priority Distribution**
- Group by: Priority Tier
- Count by: Practice Name
- Expected: Bell curve distribution (most Warm/Cold, fewer Hot/Out of Scope)

**View 3: Scoring Status**
- Group by: Scoring Status
- Filter: Scoring Status = Failed
- Expected: 0-5% failures

**View 4: Sweet Spot Targets**
- Filter: Priority Tier = 🔥 Hot OR 🌡️ Warm
- Filter: Practice Size = Sweet Spot (if using practice size field)
- Expected: Target ICP practices for outreach

### Step 5: Statistical Validation

Query summary statistics:

```python
from notion_client import Client
import os
import statistics

client = Client(auth=os.getenv("NOTION_API_KEY"))
db_id = os.getenv("NOTION_DATABASE_ID")

scores = []
tiers = {"Hot": 0, "Warm": 0, "Cold": 0, "Out of Scope": 0, "Pending": 0}

# Query all practices
has_more = True
start_cursor = None

while has_more:
    response = client.databases.query(
        database_id=db_id,
        page_size=100,
        start_cursor=start_cursor
    )

    for page in response['results']:
        props = page['properties']

        # Extract Lead Score
        score = props.get('Lead Score', {}).get('number')
        if score is not None:
            scores.append(score)

        # Extract Priority Tier
        tier = props.get('Priority Tier', {}).get('select', {}).get('name', '')
        if tier:
            for key in tiers:
                if key in tier:
                    tiers[key] += 1
                    break

    has_more = response.get('has_more', False)
    start_cursor = response.get('next_cursor')

# Print statistics
print("SCORING STATISTICS")
print("=" * 60)
print(f"Total Practices Scored: {len(scores)}")
print(f"\nScore Distribution:")
print(f"  Mean: {statistics.mean(scores):.1f}")
print(f"  Median: {statistics.median(scores):.1f}")
print(f"  Min: {min(scores)}")
print(f"  Max: {max(scores)}")
print(f"  Std Dev: {statistics.stdev(scores):.1f}")
print(f"\nPriority Tier Distribution:")
for tier, count in tiers.items():
    pct = (count / len(scores) * 100) if scores else 0
    print(f"  {tier}: {count} ({pct:.1f}%)")
```

**Expected Results:**
- Mean score: 40-60 pts
- Median score: 45-55 pts
- Hot (80-120): 10-20%
- Warm (50-79): 30-40%
- Cold (20-49): 30-40%
- Out of Scope (<20): 10-20%

## Troubleshooting

### Issue: No Changes in Notion

**Possible Causes:**
1. Scoring fields don't exist in database
2. Wrong database ID
3. API key permissions insufficient
4. Script errored silently

**Debug Steps:**
```bash
# Check if scoring succeeded
python3 score_leads.py --practice-id <page_id> --log-level DEBUG 2>&1 | tee scoring_debug.log

# Look for errors in log
grep -i error scoring_debug.log

# Check Notion API calls
grep -i "notion" scoring_debug.log
```

### Issue: Circuit Breaker Opens

**Symptoms:** "Circuit breaker is OPEN" error after 5 failures

**Resolution:**
```bash
# Check status
python3 score_leads.py --status

# Reset circuit breaker
python3 score_leads.py --reset-circuit-breaker

# Retry with lower batch size
python3 score_leads.py --batch --limit 10
```

### Issue: Timeouts

**Symptoms:** Multiple "Scoring timeout" messages

**Resolution:**
- Timeouts are expected for slow practices (< 5%)
- If > 10% timeout, check network latency
- Increase timeout in code if needed

### Issue: Wrong Scores

**Symptoms:** Lead Score doesn't match expected calculation

**Debug Steps:**
1. Check Score Breakdown JSON for component details
2. Verify input data (vet count, rating, reviews, etc.)
3. Manual calculate expected score
4. Compare to actual components in breakdown
5. Report discrepancy with example

## Success Criteria

✅ **Phase 1 (Single Practice):**
- Scoring completes without errors
- All 5 scoring fields updated in Notion
- Score matches manual calculation
- Other fields preserved

✅ **Phase 2 (10 Practices):**
- 100% success rate
- All practices updated in < 30 seconds
- Priority distribution reasonable
- No circuit breaker triggers

✅ **Phase 3 (Full Batch):**
- > 95% success rate
- Average < 3 seconds per practice
- Statistical distribution matches expectations
- Ready for sales workflow

## Next Steps After Validation

1. Document any issues found
2. Fix scoring calculation errors (if any)
3. Update unit tests to match actual behavior
4. Run `/update-docs` to update documentation index
5. Create Notion views for sales team
6. Train sales team on priority tiers
