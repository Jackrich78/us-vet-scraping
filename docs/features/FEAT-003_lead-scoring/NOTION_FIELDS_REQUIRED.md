# Notion Database Fields - Required vs Optional

**Last Updated:** 2025-11-04
**Status:** Complete Analysis

This document lists ALL fields in the Notion database, categorized by whether they are **required** by the implemented features or **optional/unused**.

---

## ✅ Required Fields (20 Total)

These fields are actively used by FEAT-001, FEAT-002, or FEAT-003 and **should NOT be deleted**.

### FEAT-001: Google Maps Scraping (6 fields)
1. **Name** (title) - Practice name
2. **Google Rating** (number) - Google Maps rating (0-5)
3. **Google Review Count** (number) - Number of reviews
4. **Website** (url) - Practice website URL
5. **Has Multiple Locations** (checkbox) - Multi-location indicator
6. **Google Place ID** (rich_text) - Unique Google identifier [Used for lookups]

### FEAT-002: Website Enrichment (8 fields)
7. **Vet Count** (number) - Total number of veterinarians
8. **Vet Count Confidence** (select: high/medium/low) - Confidence level
9. **24/7 Emergency Services** (checkbox) - Has emergency services
10. **Online Booking** (checkbox) - Has online booking system
11. **Patient Portal** (checkbox) - Has patient portal
12. **Telemedicine** (checkbox) - Offers telemedicine
13. **Specialty Services** (multi_select) - List of specialties
14. **Enrichment Status** (select) - Status of enrichment process

### FEAT-002: Decision Maker (2 fields)
15. **Decision Maker Name** (rich_text) - Owner/manager name
16. **Decision Maker Email** (email) - Owner/manager email

### FEAT-003: Lead Scoring Output (4 fields)
17. **Lead Score** (number) - ICP fit score (0-120)
18. **Priority Tier** (select) - Hot/Warm/Cold/Out of Scope/Pending Enrichment
19. **Score Breakdown** (rich_text) - JSON with scoring details
20. **Confidence Flags** (multi_select) - Data quality warnings

### Scoring Status (1 field)
21. **Scoring Status** (select) - Scored/Failed/Not Scored

---

## 🔵 Optional Sales Workflow Fields (8 fields)

These fields are NOT used by any feature code, but may be used manually by your sales team in Notion. **Review before deleting.**

1. **Status** (select) - Sales pipeline status (e.g., New Lead, Contacted, Qualified)
2. **Assigned To** (person) - Sales rep assigned to this practice
3. **Call Notes** (rich_text) - Notes from sales calls
4. **Last Contact Date** (date) - When practice was last contacted
5. **Next Follow-Up Date** (date) - Scheduled follow-up
6. **Next Action** (rich_text) - What needs to be done next
7. **Outreach Attempts** (number) - Number of contact attempts
8. **Out of Scope Reason** (select) - Why practice is out of scope

**Recommendation:** Keep these if your sales team uses them. Delete if unused.

---

## ⚠️ Duplicate Fields (5 fields - DELETE THESE)

These fields are duplicates of required fields above. **Safe to delete.**

1. **Has Online Booking** (checkbox) - Duplicate of "Online Booking" (#10)
2. **Has Emergency Services** (checkbox) - Duplicate of "24/7 Emergency Services" (#9)
3. **Confirmed Vet Count - Total** (number) - Duplicate of "Vet Count" (#7)
4. **Owner/Manager Name** (rich_text) - Duplicate of "Decision Maker Name" (#15)
5. **Owner/Manager Email** (email) - Duplicate of "Decision Maker Email" (#16)

---

## ❌ Unused Fields (DELETE THESE - 32+ fields)

These fields are NOT referenced by any feature code and appear to be legacy or experimental. **Safe to delete** unless you have a specific use case.

### Location/Address Fields (Not Used)
1. **Address** (rich_text) - Full address [Google Maps has this, not stored]
2. **City** (rich_text) - City name [Not extracted]
3. **State** (rich_text or select) - State [Not extracted]
4. **ZIP Code** (rich_text) - Postal code [Not extracted]
5. **Operating Hours** (rich_text) - Business hours [Not extracted]

### Legacy Enrichment Fields (Not Used)
6. **Boarding Services** (checkbox) - Not tracked
7. **Wellness Programs** (checkbox) - Not tracked
8. **Unique Services** (rich_text) - Not tracked
9. **Services Offered** (multi_select) - Replaced by "Specialty Services"
10. **Digital Records Mentioned** (checkbox) - Not tracked
11. **Awards/Accreditations** (multi_select) - Not extracted
12. **Business Categories** (multi_select) - Not used

### Metadata Fields (Not Used by Features)
13. **First Scraped Date** (date) - Not tracked
14. **Last Scraped Date** (date) - Not tracked
15. **Scrape Run ID** (rich_text) - Not tracked
16. **Times Scraped** (number) - Not tracked
17. **Email Status** (select) - Not used
18. **Enrichment Error** (rich_text) - Not used (errors logged elsewhere)
19. **Data Sources** (multi_select) - Not tracked
20. **Data Completeness** (select or number) - Not tracked

### Decision Maker Fields (Not Used)
21. **Owner/Manager Title** (rich_text) - Not extracted
22. **Decision Maker Role** (select) - Not extracted
23. **Decision Maker Contact Quality** (select) - Not tracked
24. **LinkedIn Profile URL** (url) - Not extracted

### Analysis/Categorization Fields (Not Used)
25. **Practice Size Category** (select) - Calculated from Vet Count, not stored separately
26. **Technology Features** (multi_select) - Calculated from checkboxes, not stored
27. **Personalization Context** (rich_text) - Not used
28. **Personalization Context (Multi)** (multi_select) - Duplicate, not used
29. **Research Notes** (rich_text) - Not generated by features

### Enrichment Tracking (Not Used)
30. **Confirmed Vet Count - Per Location** (number) - Not tracked
31. **Vet Count Per Location** (rich_text) - Not tracked

### Unknown/Unclear Purpose
32. **Initial Score** (number) - Not implemented (was planned for FEAT-001 but never added to code)

---

## 📊 Summary

| Category | Count | Action |
|----------|-------|--------|
| **Required by Features** | 21 | **KEEP** |
| **Optional Sales Fields** | 8 | Review, keep if used |
| **Duplicates** | 5 | **DELETE** |
| **Unused/Legacy** | 32+ | **DELETE** |
| **TOTAL IN DATABASE** | 66+ | |

---

## 🎯 Recommended Cleanup Plan

### Step 1: Delete Obvious Duplicates (5 fields)
These are confirmed duplicates - safe to delete immediately:
- Has Online Booking
- Has Emergency Services
- Confirmed Vet Count - Total
- Owner/Manager Name
- Owner/Manager Email

### Step 2: Evaluate Sales Fields (8 fields)
Ask your sales team if they use:
- Status, Assigned To, Call Notes, Last Contact Date, Next Follow-Up Date, Next Action, Outreach Attempts, Out of Scope Reason

If unused, delete them.

### Step 3: Delete Unused Fields (32 fields)
Delete all fields in the "Unused Fields" section above unless you have a specific reason to keep them.

### Step 4: Final Database (21-29 fields)
After cleanup, you should have:
- 21 required fields (features)
- 0-8 optional fields (sales workflow, if kept)
- **Total: 21-29 fields** (down from 66!)

---

## 🔍 How to Identify Which Fields Are Actually Used

### Method 1: Search the Codebase
```bash
# Search for all Notion field references
grep -r "properties.get" src/integrations/*.py

# Current results show these fields are accessed:
# - Name (title)
# - Google Rating
# - Google Review Count
# - Website
# - Has Multiple Locations
# - Google Place ID
# - Vet Count
# - Vet Count Confidence
# - 24/7 Emergency Services
# - Online Booking
# - Patient Portal
# - Telemedicine
# - Specialty Services
# - Decision Maker Name
# - Decision Maker Email
# - Enrichment Status
# - Lead Score
# - Priority Tier
# - Score Breakdown
# - Confidence Flags
# - Scoring Status
```

### Method 2: Check Feature Documentation
- **FEAT-001:** See `docs/features/FEAT-001_google-maps-notion/`
- **FEAT-002:** See `docs/features/FEAT-002_website-enrichment/`
- **FEAT-003:** See `docs/features/FEAT-003_lead-scoring/STATUS.md`

### Method 3: Verify with Schema Check Script
```bash
python3 check_notion_schema.py
```

This shows which fields the code expects vs. which exist in the database.

---

## ⚙️ How to Delete Fields in Notion

**Warning:** Deleting fields is permanent. Export your database first as a backup.

1. Open your Notion database
2. Click the "..." menu in the top right
3. Select "Customize database"
4. Find the field you want to delete
5. Click the "..." next to the field name
6. Select "Delete property"
7. Confirm deletion

**Pro Tip:** Hide fields first instead of deleting if you're unsure:
1. Click the "..." menu
2. Toggle off the field to hide it
3. Monitor for 1-2 weeks to ensure nothing breaks
4. Then delete if confirmed unused

---

## 📞 Questions to Ask Before Deleting

1. **Sales Fields:** Does your sales team manually use Status, Assigned To, Call Notes, etc.?
2. **Metadata:** Do you need First Scraped Date, Last Scraped Date, Times Scraped for analytics?
3. **Initial Score:** Was this planned for future use in FEAT-001?
4. **Location Fields:** Do you need Address, City, State, ZIP for filtering/reporting?

If the answer to all is "No," then delete them!

---

## ✅ Verification After Cleanup

After deleting fields, verify everything still works:

```bash
# 1. Check schema is still valid
python3 check_notion_schema.py

# Should show: 21/21 fields found (or 21-29 if you kept sales fields)

# 2. Test FEAT-001 (Google Maps scraping)
python3 main.py --test

# 3. Test FEAT-002 (Website enrichment)
python3 test_e2e_enrichment.py

# 4. Test FEAT-003 (Lead scoring)
python3 score_leads.py --batch --limit 5

# All should pass without errors
```

---

**Bottom Line:** You can safely delete **37+ fields** (5 duplicates + 32 unused) and reduce your database from 66 fields to 21-29 fields without affecting any functionality.
