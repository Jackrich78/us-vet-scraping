# Notion Schema Reconciliation for All Features

**Created:** 2025-11-04
**Status:** Action Required - Schema needs consolidation before testing
**Total Fields in Database:** 66
**Features Affected:** FEAT-001, FEAT-002, FEAT-003

---

## Executive Summary

The Notion database has **66 fields**, but there are significant naming inconsistencies and duplicates. Many fields exist with different names than what the code expects, causing "missing field" errors.

**Key Issues:**
1. **Duplicate/Similar Fields** - Same data with different names (e.g., "Google Rating" vs "Rating")
2. **Naming Inconsistencies** - Some fields have "Has" or "Google" prefixes, others don't
3. **Unused Fields** - 39 fields exist but aren't referenced by any feature code
4. **Type Mismatches** - Some fields exist but with wrong type (e.g., "State" is rich_text, should be select)

**Impact:** FEAT-003 scoring will fail because it expects fields like "Rating" but database has "Google Rating"

---

## Critical Field Mapping (Code → Database)

### Fields That Exist But With Different Names

| Code Expects | Database Has | Type | Action |
|--------------|--------------|------|--------|
| `Rating` | `Google Rating` | number | **RENAME** database field OR update code |
| `Review Count` | `Google Review Count` | number | **RENAME** database field OR update code |
| `Multiple Locations` | `Has Multiple Locations` | checkbox | **RENAME** database field OR update code |
| `Emergency 24/7` | `Has Emergency Services` OR `24/7 Emergency Services` | checkbox | **CONSOLIDATE** - 2 similar fields exist! |
| `Place ID` | `Google Place ID` | rich_text | **RENAME** database field OR update code |
| `Hours` | `Operating Hours` | rich_text | **RENAME** database field OR update code |
| `Zip` | `ZIP Code` | rich_text | **RENAME** database field OR update code |
| `Categories` | `Business Categories` | multi_select | **RENAME** database field OR update code |
| `Awards Accreditations` | `Awards/Accreditations` | multi_select | **RENAME** database field OR update code |
| `Online Booking` | `Has Online Booking` OR `Online Booking` | checkbox | **CONSOLIDATE** - 2 identical fields! |
| `Data Sources` | `Data Sources` | **TYPE MISMATCH** - code expects rich_text, DB has multi_select | **FIX** type OR update code |
| `Data Completeness` | `Data Completeness` | **TYPE MISMATCH** - code expects number, DB has select | **FIX** type OR update code |
| `Decision Maker Role` | `Decision Maker Role` | **TYPE MISMATCH** - code expects rich_text, DB has select | **FIX** type OR update code |

### Fields Truly Missing (Need to Add)

| Field Name | Type | Needed By | Purpose |
|------------|------|-----------|---------|
| `Confidence Flags` | multi_select | FEAT-003 | Warnings about data quality |
| `Scoring Status` | select | FEAT-003 | Scored/Failed/Not Scored |
| `Initial Score` | number | FEAT-001 | 0-25 baseline score from Google |
| `Vet Count Per Location` | rich_text | FEAT-002 | Breakdown by location |

**Note:** Only 4 fields are truly missing. The rest exist with different names!

---

## Recommended Approach: Option A (Minimal Changes)

**Strategy:** Update code to match existing database field names (least disruptive)

### Changes Required in Code

#### 1. FEAT-001 (Google Maps Scraping)
File: `src/integrations/notion_mapper.py`

```python
# OLD (expected)          # NEW (actual database field)
"Rating"           →      "Google Rating"
"Review Count"     →      "Google Review Count"
"Place ID"         →      "Google Place ID"
"Hours"            →      "Operating Hours"
"Zip"              →      "ZIP Code"
"Categories"       →      "Business Categories"
"Multiple Locations" →    "Has Multiple Locations"
```

#### 2. FEAT-002 (Website Enrichment)
File: `src/integrations/notion_enrichment.py`

```python
# OLD (expected)          # NEW (actual database field)
"Place ID"         →      "Google Place ID"
"Emergency 24/7"   →      "Has Emergency Services" (or "24/7 Emergency Services")
"Awards Accreditations" → "Awards/Accreditations"

# Type changes needed:
"Decision Maker Role"    →  Keep as select (already correct in DB)
"Data Completeness"      →  Keep as select (already correct in DB)
"Data Sources"           →  Keep as multi_select (already correct in DB)
```

#### 3. FEAT-003 (Lead Scoring)
File: `src/integrations/notion_scoring.py`

```python
# OLD (expected)          # NEW (actual database field)
"Rating"           →      "Google Rating"
"Review Count"     →      "Google Review Count"
"Multiple Locations" →    "Has Multiple Locations"
"Emergency 24/7"   →      "Has Emergency Services" (or "24/7 Emergency Services")

# Add these 2 missing fields to Notion:
"Confidence Flags"  (multi_select)
"Scoring Status"    (select with options: Scored, Failed, Not Scored)
```

---

## Alternative Approach: Option B (Cleaner Schema)

**Strategy:** Rename database fields for consistency (more work but cleaner long-term)

### Database Renames Required

| Current Name | Rename To | Reason |
|--------------|-----------|--------|
| `Google Rating` | `Rating` | Simpler, no prefix needed |
| `Google Review Count` | `Review Count` | Simpler, no prefix needed |
| `Google Place ID` | `Place ID` | Simpler, no prefix needed |
| `Has Multiple Locations` | `Multiple Locations` | Consistent with "Website" (no "Has") |
| `Has Emergency Services` | `Emergency 24/7` | More specific name |
| `Operating Hours` | `Hours` | Simpler |
| `ZIP Code` | `Zip` | Consistent casing |
| `Business Categories` | `Categories` | Simpler |
| `Awards/Accreditations` | `Awards Accreditations` | Consistent naming (no slash) |

### Duplicate Fields to Consolidate

1. **Emergency Services (3 variants!)**
   - `Has Emergency Services` (checkbox)
   - `24/7 Emergency Services` (checkbox)
   - Code expects: `Emergency 24/7` (checkbox)

   **Action:** Delete duplicates, keep/rename one as `Emergency 24/7`

2. **Online Booking (2 variants!)**
   - `Has Online Booking` (checkbox)
   - `Online Booking` (checkbox)

   **Action:** Delete duplicate, keep `Online Booking`

3. **Vet Count (3 variants!)**
   - `Vet Count` (number) - current field being used
   - `Confirmed Vet Count - Total` (number) - duplicate?
   - `Confirmed Vet Count - Per Location` (number) - should be rich_text per spec

   **Action:** Keep `Vet Count`, evaluate if "Confirmed" fields are still needed

---

## Fields to Delete (Unused by Any Feature)

These 39 fields are NOT referenced by any feature code:

**Sales Workflow Fields (keep these):**
- Assigned To
- Call Notes
- Last Contact Date
- Next Follow-Up Date
- Next Action
- Research Notes
- Outreach Attempts
- Out of Scope Reason

**Duplicate/Redundant Fields (consider deleting):**
- `Has Emergency Services` (use `Emergency 24/7` instead)
- `Has Online Booking` (duplicate of `Online Booking`)
- `Confirmed Vet Count - Total` (duplicate of `Vet Count`?)
- `Confirmed Vet Count - Per Location` (if not used)

**Legacy/Unknown Purpose (evaluate before deleting):**
- Boarding Services
- Digital Records Mentioned
- Email Status
- Enrichment Error
- First Scraped Date
- Last Scraped Date
- Scrape Run ID
- Times Scraped
- Owner/Manager Email (vs Decision Maker Email?)
- Owner/Manager Name (vs Decision Maker Name?)
- Owner/Manager Title (vs Decision Maker Role?)
- Personalization Context (Multi) (duplicate of Personalization Context?)
- Services Offered (vs Specialty Services?)
- Technology Features (calculated from checkboxes?)
- Unique Services (vs Specialty Services?)
- Wellness Programs
- LinkedIn Profile URL
- Practice Size Category (calculated from Vet Count?)
- Decision Maker Contact Quality (calculated?)

---

## Type Mismatches to Fix

### Option 1: Keep DB Types, Update Code

| Field | Code Expects | DB Has | Action |
|-------|--------------|--------|--------|
| `State` | select | rich_text | Update code to read rich_text |
| `Decision Maker Role` | rich_text | select | Update code to read select |
| `Data Completeness` | number (0-100) | select (High/Medium/Low) | Update code to read select |
| `Data Sources` | rich_text (URLs) | multi_select | Update code to read multi_select |

### Option 2: Fix DB Types (Breaking Change)

**Not recommended** - Would lose existing data unless migrated carefully

---

## Recommended Action Plan

### Phase 1: Immediate Fixes (For FEAT-003 Testing)

**Goal:** Get scoring working with minimal changes

1. **Update FEAT-003 Code to Use Actual Field Names**
   - File: `src/integrations/notion_scoring.py`
   - Change 4 field names: Rating → Google Rating, Review Count → Google Review Count, Multiple Locations → Has Multiple Locations, Emergency 24/7 → Has Emergency Services

2. **Add 2 Missing Fields to Notion**
   - `Confidence Flags` (multi_select)
   - `Scoring Status` (select: Scored, Failed, Not Scored)

3. **Test FEAT-003 Scoring**
   - Run: `python3 score_leads.py --batch --limit 10`
   - Verify fields update correctly

**Time Required:** 15-30 minutes

---

### Phase 2: Schema Cleanup (After Testing)

**Goal:** Consolidate schema for long-term maintainability

1. **Create Field Mapping Document**
   - Document which fields are truly needed
   - Identify safe-to-delete fields
   - Get user approval before deleting anything

2. **Rename Fields for Consistency** (If desired)
   - Remove "Google" prefix (Google Rating → Rating)
   - Remove "Has" prefix (Has Multiple Locations → Multiple Locations)
   - Standardize casing (ZIP Code → Zip)

3. **Consolidate Duplicates**
   - Emergency services (3 variants → 1)
   - Online booking (2 variants → 1)
   - Vet count fields (3 variants → clarify purpose)

4. **Update All Feature Code**
   - FEAT-001, FEAT-002, FEAT-003
   - Update field references
   - Test each feature

**Time Required:** 2-3 hours

---

## Decision Matrix: Which Option?

| Criteria | Option A (Update Code) | Option B (Rename DB) |
|----------|------------------------|----------------------|
| **Speed** | ✅ 15 min | ❌ 2-3 hours |
| **Testing Risk** | ✅ Low | ⚠️ Medium (need to re-test all features) |
| **Data Loss Risk** | ✅ None | ⚠️ Possible if done wrong |
| **Long-term Maintainability** | ⚠️ Inconsistent names | ✅ Clean schema |
| **Breaking Changes** | ✅ None | ⚠️ All features affected |

**Recommendation:**
- **Now (for FEAT-003 testing):** Option A (update code to match DB)
- **Later (Phase 2):** Option B (clean up schema systematically)

---

## Next Session Checklist

For the next session to test FEAT-003, complete these steps:

### Pre-Testing Setup (15 minutes)

- [ ] **Step 1:** Review this document and decide on Option A or B
- [ ] **Step 2:** If Option A, update `src/integrations/notion_scoring.py` field names
- [ ] **Step 3:** Add 2 missing fields to Notion: `Confidence Flags`, `Scoring Status`
- [ ] **Step 4:** Run schema check: `python3 check_notion_schema.py`
- [ ] **Step 5:** Verify all required fields now exist

### Testing (30 minutes)

- [ ] **Step 6:** List practices: `python3 list_notion_practices.py --limit 10`
- [ ] **Step 7:** Score 1 practice: `python3 score_leads.py --practice-id <ID>`
- [ ] **Step 8:** Verify in Notion UI (fields updated correctly)
- [ ] **Step 9:** Score batch of 10: `python3 score_leads.py --batch --limit 10`
- [ ] **Step 10:** Score all: `python3 score_leads.py --batch --all`

### Post-Testing (Optional)

- [ ] **Step 11:** Plan Phase 2 schema cleanup (if desired)
- [ ] **Step 12:** Create field mapping for unused fields
- [ ] **Step 13:** Update all features to use consistent naming
- [ ] **Step 14:** Document final schema in `docs/system/database.md`

---

## Files for Next Session

**Created:**
- `analyze_notion_fields.py` - Comprehensive field analysis script
- `check_notion_schema.py` - Quick schema validation
- `list_notion_practices.py` - List practices with correct Page IDs
- `notion_schema_analysis.json` - Detailed analysis export
- `NOTION_SCHEMA_RECONCILIATION.md` - This document

**Key Files to Reference:**
- `docs/system/database.md` - Original schema specification
- `src/integrations/notion_scoring.py` - FEAT-003 field references
- `src/integrations/notion_enrichment.py` - FEAT-002 field references
- `src/integrations/notion_mapper.py` - FEAT-001 field references

---

## Questions for Next Session

1. **Do you want Option A (quick fix) or Option B (clean schema)?**
2. **Which duplicate fields should we keep?** (e.g., which "Emergency Services" field)
3. **Which 39 unused fields are safe to delete?**
4. **Should we keep type mismatches or fix them?** (e.g., Data Completeness as select vs number)
5. **What's the purpose of "Confirmed Vet Count" vs "Vet Count"?**

---

**Summary:** The Notion database is functional but has 66 fields with naming inconsistencies. To test FEAT-003 now, we need to either: (A) update 4 field names in code and add 2 missing fields, OR (B) rename 9 database fields and consolidate duplicates. Option A is faster for immediate testing, Option B is better long-term.
