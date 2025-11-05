# Notion Database Fields - Current & Planned

**Last Updated:** 2025-11-05
**Status:** Current (20 fields) + Planned (13 fields from FEAT-004 through FEAT-007)

This document lists ALL fields in the Notion database: currently implemented fields and planned fields from upcoming features.

---

## ✅ Current Implementation (20 Fields)

These fields are **actively used** by implemented features and should NOT be deleted.

### FEAT-001: Google Maps Scraping (5 fields)
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

### FEAT-003: Lead Scoring Output (5 fields)
17. **Lead Score** (number) - ICP fit score (0-120)
18. **Priority Tier** (select) - Hot/Warm/Cold/Out of Scope/Pending Enrichment
19. **Score Breakdown** (rich_text) - JSON with scoring details
20. **Confidence Flags** (multi_select) - Data quality warnings
21. **Scoring Status** (select) - Scored/Failed/Not Scored

---

## 🔜 Planned Fields (13 Total)

These fields will be added when features FEAT-004 through FEAT-007 are implemented.

### FEAT-005: Google Reviews Analysis (5 fields)
22. **Google Review Summary** (rich_text) - 2-3 sentence summary of review sentiment and key themes
23. **Google Review Themes** (multi_select) - Common themes: ["Compassionate Care", "Short Wait Times", "Expensive", "Emergency Excellence", "Exotic Pets", "Fear-Free", "Family-Owned"]
24. **Google Review Sample Size** (number) - How many reviews were analyzed (0-50)
25. **Google Review Decision Makers** (rich_text) - Decision maker names/roles mentioned in reviews
26. **Google Review Red Flags** (multi_select) - Concerning patterns: ["High Prices", "Long Waits", "Poor Communication", "Staff Turnover"]

**Status:** Planned - High Priority
**Cost:** +$0.001/lead
**Value:** High - Patient voice insights for personalized outreach

### FEAT-006: Improved LLM Extraction (4 fields)
27. **Founded Year** (number) - Practice founding year (e.g., 1985)
28. **Practice Story** (rich_text) - Founding narrative + mission statement (qualitative context)
29. **Unique Selling Points** (multi_select) - 3-5 unique facts for personalization (e.g., "Only exotic bird specialist in Boston", "AAHA accredited since 1995")
30. **Operating Hours** (rich_text) - Business hours from website
31. **Personalization Score** (select: 0-3 Low, 4-6 Medium, 7-10 High) - Quality of personalization context extracted

**Status:** Planned - Medium Priority
**Cost:** $0/lead (same LLM call, better prompt)
**Value:** Medium - Better personalization with zero cost increase

### FEAT-007: LinkedIn Enrichment (4 fields)
32. **LinkedIn Company URL** (url) - Link to LinkedIn company page
33. **LinkedIn Employee Count** (number) - Employee count from LinkedIn (validates vet count)
34. **LinkedIn Follower Count** (number) - Social media presence signal
35. **LinkedIn Decision Makers** (rich_text) - List of names + titles found (e.g., "Dr. Sarah Johnson (Owner), Jennifer Smith (Practice Manager)")

**Status:** Planned - Lower Priority (test with 10 practices first)
**Cost:** +$0.001-0.003/lead
**Value:** Medium - Decision maker identification, employee count validation

---

## 🔵 Optional Sales Workflow Fields

These fields are NOT used by any feature code, but may be used manually by your sales team in Notion.

1. **Status** (select) - Sales pipeline status (e.g., New Lead, Contacted, Qualified)
2. **Assigned To** (person) - Sales rep assigned to this practice
3. **Call Notes** (rich_text) - Notes from sales calls
4. **Last Contact Date** (date) - When practice was last contacted
5. **Next Follow-Up Date** (date) - Scheduled follow-up
6. **Next Action** (rich_text) - What needs to be done next
7. **Outreach Attempts** (number) - Number of contact attempts
8. **Out of Scope Reason** (select) - Why practice is out of scope

**Recommendation:** Keep these if your sales team actively uses them. If unused after 30 days, consider removing.

---

## 📊 Field Summary

| Category | Current | Planned | Total |
|----------|---------|---------|-------|
| **Feature-Used Fields** | 20 | 13 | 33 |
| **Sales Workflow Fields** | 8 | 0 | 8 |
| **Grand Total** | 28 | 13 | **41 fields** |

**Note:** Started with 66+ fields, cleaned up to 20, now planning to add 13 high-value fields = 33 total (50% reduction from original).

---

## 🎯 Field Usage by Feature

| Feature | Fields Added | Priority | Cost/Lead | Status |
|---------|--------------|----------|-----------|--------|
| FEAT-001: Google Maps | 6 | ✅ Complete | $0.01 | Implemented |
| FEAT-002: Website Enrichment | 10 | ✅ Complete | $0.02 | Implemented |
| FEAT-003: Lead Scoring | 5 | ✅ Complete | $0.00 | Implemented |
| **FEAT-004: Fix Scraping** | **0** | **🔴 Critical** | **$0.00** | **Planned** |
| FEAT-005: Review Analysis | 5 | 🟠 High | $0.001 | Planned |
| FEAT-006: Better LLM Prompt | 5 | 🟡 Medium | $0.00 | Planned |
| FEAT-007: LinkedIn | 4 | 🟢 Low | $0.001-0.003 | Planned |
| FEAT-008: Social Media | TBD | ⚪ Research | TBD | Deferred |

---

## 🔧 Implementation Sequence

1. **FEAT-004** (Fix Website Scraping) - **CRITICAL**
   - No new fields
   - Fixes 60% failure rate in current enrichment
   - Blocks all other improvements

2. **FEAT-005** (Google Reviews)
   - Add 5 review-related fields
   - High value for sales personalization
   - Quick win: just enable existing Apify data

3. **FEAT-006** (Better LLM Extraction)
   - Add 5 website-extraction fields
   - Zero cost improvement
   - Requires manual audit of vet websites first

4. **FEAT-007** (LinkedIn)
   - Add 4 LinkedIn fields
   - Test with 10 practices before full rollout
   - Watch for LinkedIn blocking

---

## 🚫 Fields to Delete (If Not Already Removed)

If your database still contains these fields from the original 66-field schema, they are safe to delete:

### Confirmed Duplicates (5 fields)
- Has Online Booking → duplicate of "Online Booking"
- Has Emergency Services → duplicate of "24/7 Emergency Services"
- Confirmed Vet Count - Total → duplicate of "Vet Count"
- Owner/Manager Name → duplicate of "Decision Maker Name"
- Owner/Manager Email → duplicate of "Decision Maker Email"

### Unused Legacy Fields (30+ fields)
- Address, City, State, ZIP Code (not stored, only in Google Maps)
- Operating Hours (will be added back in FEAT-006)
- Boarding Services, Wellness Programs (not tracked)
- Awards/Accreditations (will be added back in FEAT-006 as part of Unique Selling Points)
- First Scraped Date, Last Scraped Date, Scrape Run ID, Times Scraped (metadata not tracked)
- Initial Score (was planned for FEAT-001 but never implemented)

**See original NOTION_FIELDS_REQUIRED.md (dated 2025-11-04) for complete list.**

---

## 📋 Field Definitions (Current + Planned)

### Current Fields (20)

| Field Name | Type | Feature | Description | Example |
|------------|------|---------|-------------|---------|
| Name | title | FEAT-001 | Practice name (unique identifier) | "Boston Veterinary Clinic" |
| Google Place ID | rich_text | FEAT-001 | Google Maps unique ID | "ChIJN1t_tDeuEmsR..." |
| Google Rating | number | FEAT-001 | Average rating 0-5 stars | 4.5 |
| Google Review Count | number | FEAT-001 | Total number of reviews | 156 |
| Website | url | FEAT-001 | Practice website URL | "https://example-vet.com" |
| Has Multiple Locations | checkbox | FEAT-001 | Multi-location indicator | true |
| Vet Count | number | FEAT-002 | Number of veterinarians | 5 |
| Vet Count Confidence | select | FEAT-002 | Confidence: high/medium/low | "high" |
| 24/7 Emergency Services | checkbox | FEAT-002 | Has emergency services | true |
| Online Booking | checkbox | FEAT-002 | Has online booking system | true |
| Patient Portal | checkbox | FEAT-002 | Has patient portal | false |
| Telemedicine | checkbox | FEAT-002 | Offers telemedicine | false |
| Specialty Services | multi_select | FEAT-002 | List of specialties | ["Surgery", "Dentistry"] |
| Enrichment Status | select | FEAT-002 | Status: Completed/Failed/Not Started | "Completed" |
| Decision Maker Name | rich_text | FEAT-002 | Owner/manager name | "Dr. Sarah Johnson" |
| Decision Maker Email | email | FEAT-002 | Owner/manager email | "sjohnson@example.com" |
| Lead Score | number | FEAT-003 | ICP fit score 0-120 | 85 |
| Priority Tier | select | FEAT-003 | Hot/Warm/Cold/Out of Scope | "Hot" |
| Score Breakdown | rich_text | FEAT-003 | JSON with scoring details | {practice_size: 40, ...} |
| Confidence Flags | multi_select | FEAT-003 | Data quality warnings | ["Low Vet Count Confidence"] |
| Scoring Status | select | FEAT-003 | Scored/Failed/Not Scored | "Scored" |

### Planned Fields (13)

| Field Name | Type | Feature | Description | Example |
|------------|------|---------|-------------|---------|
| Google Review Summary | rich_text | FEAT-005 | 2-3 sentence review sentiment summary | "Patients consistently praise Dr. Sarah's expertise with anxious cats and the short wait times..." |
| Google Review Themes | multi_select | FEAT-005 | Common themes from reviews | ["Compassionate Care", "Short Wait Times"] |
| Google Review Sample Size | number | FEAT-005 | Number of reviews analyzed | 50 |
| Google Review Decision Makers | rich_text | FEAT-005 | DMs mentioned in reviews | "Dr. Sarah Johnson (Owner)" |
| Google Review Red Flags | multi_select | FEAT-005 | Concerning patterns | ["High Prices"] |
| Founded Year | number | FEAT-006 | Practice founding year | 1985 |
| Practice Story | rich_text | FEAT-006 | Founding narrative + mission | "Family-owned for 3 generations, founded by Dr. Johnson in 1985..." |
| Unique Selling Points | multi_select | FEAT-006 | 3-5 unique facts | ["Only exotic bird specialist in Boston", "AAHA accredited since 1995"] |
| Operating Hours | rich_text | FEAT-006 | Business hours | "Mon-Fri 8am-7pm, Sat 9am-5pm" |
| Personalization Score | select | FEAT-006 | Quality of context: 0-3/4-6/7-10 | "7-10 High" |
| LinkedIn Company URL | url | FEAT-007 | LinkedIn company page | "https://linkedin.com/company/example-vet" |
| LinkedIn Employee Count | number | FEAT-007 | Employee count from LinkedIn | 22 |
| LinkedIn Follower Count | number | FEAT-007 | LinkedIn followers | 350 |
| LinkedIn Decision Makers | rich_text | FEAT-007 | Names + titles from LinkedIn | "Dr. Sarah Johnson (Owner), Jennifer Smith (Practice Manager)" |

---

## ✅ Schema Validation

### Current Schema Check
Run this command to validate current 20 fields exist:
```bash
python3 check_notion_schema.py
```

Expected output:
```
Total Required: 20
✅ Existing: 20
⚠️  Type Mismatches: 0
❌ Missing: 0

✅ Database schema is COMPLETE and ready for scoring!
```

### After Feature Implementation
When FEAT-005, 006, 007 are implemented, this script will need to be updated to check for 33 fields instead of 20.

---

## 📞 Questions Before Deleting Fields

1. **Sales Workflow Fields:** Does your sales team actually use Status, Assigned To, Call Notes, etc.?
   - If YES: Keep them
   - If NO: Safe to delete

2. **Duplicate Fields:** Have these been deleted already?
   - Run `check_notion_schema.py` to see current field count
   - If you see 28 fields (20 required + 8 sales), duplicates likely already removed

3. **Legacy Fields:** Any fields not listed in "Current (20)" or "Planned (13)" are legacy
   - Safe to delete unless you have a specific use case

---

## 🔄 Changelog

| Date | Change | Notes |
|------|--------|-------|
| 2025-11-05 | Added 13 planned fields from FEAT-004 through FEAT-007 | Feature PRDs created |
| 2025-11-04 | Cleaned up from 66 to 20 fields | Removed duplicates and unused fields |
| 2025-11-03 | Initial field audit | Identified required vs unused fields |

---

## 📚 References

- Current schema check script: `check_notion_schema.py`
- FEAT-005 PRD: `docs/features/FEAT-005_google-reviews-analysis/prd.md`
- FEAT-006 PRD: `docs/features/FEAT-006_improve-llm-extraction/prd.md`
- FEAT-007 PRD: `docs/features/FEAT-007_linkedin-enrichment/prd.md`
- Notion database ID: `2a0edda2a9a081d98dc9daa43c65e744`
