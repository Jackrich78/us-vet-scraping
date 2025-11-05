# Notion Database Field Analysis

**Date:** 2025-11-05
**Total Fields in Notion:** 48
**Fields Used by Code:** 31
**Unused Fields:** 17

---

## Executive Summary

Our Notion database has **48 fields** but we only write to **31 of them**. This analysis identifies:
1. **Redundant fields** that should be removed (duplicates, unused)
2. **Missing fields** we try to write but don't exist in Notion
3. **Potential fields** we could populate with available data
4. **Sales workflow fields** to keep (manual use)

---

## Field Categories

### ✅ ACTIVELY USED (31 fields)

#### FEAT-001: Google Maps Scraping (9 fields)
| Field Name | Type | Status | Notes |
|------------|------|--------|-------|
| Name | title | ✅ Used | Practice name |
| Google Place ID | rich_text | ✅ Used | Unique identifier |
| Address | rich_text | ✅ Used | Full street address |
| Phone | phone_number | ✅ Used | Primary phone |
| Website | url | ✅ Used | Practice website |
| Google Review Count | number | ✅ Used | Number of reviews |
| Google Rating | number | ✅ Used | Star rating (0-5) |
| Lead Score | number | ✅ Used | Initial score 0-25, final 0-120 |
| Status | select | ✅ Used | "New Lead" on creation |

#### FEAT-002: Website Enrichment (18 fields)
| Field Name | Type | Status | Notes |
|------------|------|--------|-------|
| Vet Count | number | ✅ Used | Total veterinarians |
| Vet Count Confidence | select | ✅ Used | high/medium/low |
| Decision Maker Name | rich_text | ✅ Used | Owner/director name |
| Decision Maker Role | select | ✅ Used | Job title |
| Decision Maker Email | email | ✅ Used | Contact email |
| Decision Maker Phone | phone_number | ✅ Used | Direct phone |
| 24/7 Emergency Services | checkbox | ✅ Used | Has emergency care |
| Online Booking | checkbox | ✅ Used | Has online scheduling |
| Patient Portal | checkbox | ✅ Used | Has patient portal |
| Telemedicine | checkbox | ✅ Used | Offers virtual care |
| Specialty Services | multi_select | ✅ Used | List of specialties |
| Personalization Context | rich_text | ✅ Used | 2-3 unique facts |
| **Awards/Accreditations** | multi_select | ⚠️ **MISSING** | We write, doesn't exist |
| **Recent News/Updates** | rich_text | ⚠️ **MISSING** | We write, doesn't exist |
| **Community Involvement** | rich_text | ⚠️ **MISSING** | We write, doesn't exist |
| **Practice Philosophy/Mission** | rich_text | ⚠️ **MISSING** | We write, doesn't exist |
| Enrichment Status | select | ✅ Used | "Completed"/"Failed" |
| Last Enrichment Date | date | ✅ Used | ISO timestamp |

#### FEAT-003: Lead Scoring (5 fields)
| Field Name | Type | Status | Notes |
|------------|------|--------|-------|
| Lead Score | number | ✅ Used | Final score 0-120 (overwrites initial) |
| Priority Tier | select | ✅ Used | 🔥 Hot / 🌡️ Warm / ❄️ Cold |
| Score Breakdown | rich_text | ✅ Used | JSON breakdown |
| Confidence Flags | multi_select | ✅ Used | Data quality warnings |
| Scoring Status | select | ✅ Used | "Scored"/"Failed" |

---

## ⚠️ MISSING FIELDS (4 fields)

These fields are referenced in our code but **DO NOT EXIST** in the Notion database:

| Field Name | Type Expected | Written By | Impact |
|------------|---------------|------------|--------|
| Awards/Accreditations | multi_select | FEAT-002 | **HIGH** - LLM extracts this, silently fails |
| Recent News/Updates | rich_text | FEAT-002 | **HIGH** - LLM extracts this, silently fails |
| Community Involvement | rich_text | FEAT-002 | **HIGH** - LLM extracts this, silently fails |
| Practice Philosophy/Mission | rich_text | FEAT-002 | **HIGH** - LLM extracts this, silently fails |

**Action Required:** Either:
1. **Add these 4 fields** to Notion (recommended - provides sales context)
2. **Remove from extraction model** (lose valuable personalization data)

---

## ❌ REDUNDANT/UNUSED FIELDS (17 fields)

These exist in Notion but are **NEVER written** by our code:

### Category 1: Sales Workflow Fields (KEEP - Manual Use)
| Field Name | Type | Purpose | Recommendation |
|------------|------|---------|----------------|
| Assigned To | people | Sales team assignment | ✅ **KEEP** - Manual |
| Call Notes | rich_text | Sales call notes | ✅ **KEEP** - Manual |
| Last Contact Date | date | Last outreach | ✅ **KEEP** - Manual |
| Next Follow-Up Date | date | Follow-up scheduling | ✅ **KEEP** - Manual |
| Next Action | rich_text | Next step to take | ✅ **KEEP** - Manual |
| Outreach Attempts | number | Contact attempts | ✅ **KEEP** - Manual |
| Research Notes | rich_text | Manual research | ✅ **KEEP** - Manual |

### Category 2: Duplicate/Redundant Fields (REMOVE)
| Field Name | Type | Issue | Recommendation |
|------------|------|-------|----------------|
| **Services Offered** | multi_select | **DUPLICATE** of "Specialty Services" | ❌ **REMOVE** |
| **Personalisation Hook** | rich_text | **DUPLICATE** of "Personalization Context" | ❌ **REMOVE** |
| **Personalization Context (Multi)** | multi_select | **DUPLICATE** of "Personalization Context" | ❌ **REMOVE** |

### Category 3: Metadata Fields (Unclear Purpose)
| Field Name | Type | Current Use | Recommendation |
|------------|------|-------------|----------------|
| Enrichment Error | rich_text | Never written (we use Enrichment Status) | ⚠️ **REVIEW** - Could be useful for debugging |
| First Scraped Date | date | Never written | ❌ **REMOVE** - Not tracking |
| Last Scraped Date | date | Never written | ❌ **REMOVE** - Not tracking |
| Times Scraped | number | Never written | ❌ **REMOVE** - Not tracking |
| Scrape Run ID | rich_text | Never written | ❌ **REMOVE** - Not tracking |

### Category 4: Future Features (Planned - KEEP)
| Field Name | Type | Planned For | Recommendation |
|------------|------|-------------|----------------|
| Google Maps URL | url | FEAT-001 enhancement | ✅ **KEEP** - Easy to populate |
| LinkedIn Profile URL | url | FEAT-007 (LinkedIn enrichment) | ✅ **KEEP** - Planned |
| PMS Vendor | select | FEAT-006 (LLM extraction) | ✅ **KEEP** - Planned |
| Operating Hours | rich_text | FEAT-001 enhancement | ✅ **KEEP** - Easy to populate |
| Out of Scope Reason | select | FEAT-003 enhancement | ✅ **KEEP** - Useful |
| Has Multiple Locations | checkbox | FEAT-003 scoring (already used) | ✅ **KEEP** - Used in scoring |

---

## 🔧 FIELDS WE COULD POPULATE NOW (5 fields)

These fields exist in Notion and we have the data available:

### High Priority (Should Add)
| Field Name | Data Source | Effort | Value |
|------------|-------------|--------|-------|
| **Google Maps URL** | Apify response | **5 min** | High - Direct link to GMaps |
| **Operating Hours** | Apify response | **5 min** | High - Helpful for outreach timing |
| **Enrichment Error** | Enrichment failures | **10 min** | High - Better debugging |

### Medium Priority (Nice to Have)
| Field Name | Data Source | Effort | Value |
|------------|-------------|--------|-------|
| **First Scraped Date** | FEAT-001 timestamp | **5 min** | Medium - Historical tracking |
| **Last Scraped Date** | FEAT-001 timestamp | **5 min** | Medium - Data freshness |

---

## 📊 Summary Statistics

| Category | Count | Action |
|----------|-------|--------|
| **Total Fields in Notion** | 48 | - |
| **Fields We Write** | 31 | - |
| **Missing Fields (Code writes, Notion lacks)** | 4 | ⚠️ **ADD TO NOTION** |
| **Redundant/Duplicate Fields** | 3 | ❌ **REMOVE** |
| **Unused Metadata Fields** | 5 | ❌ **REMOVE** |
| **Sales Workflow Fields (Manual)** | 7 | ✅ **KEEP** |
| **Future Feature Fields** | 6 | ✅ **KEEP** |
| **Could Populate Now** | 5 | 🔧 **QUICK WINS** |

---

## 🎯 Recommended Actions

### Immediate (Before Next Run)

1. **Add 4 Missing Fields to Notion:**
   - Awards/Accreditations (multi_select)
   - Recent News/Updates (rich_text)
   - Community Involvement (rich_text)
   - Practice Philosophy/Mission (rich_text)

   **Impact:** Prevents silent data loss, improves personalization

2. **Remove 3 Duplicate Fields:**
   - Services Offered (use "Specialty Services" instead)
   - Personalisation Hook (use "Personalization Context")
   - Personalization Context (Multi) (use "Personalization Context")

   **Impact:** Cleaner schema, less confusion

3. **Remove 5 Unused Metadata Fields:**
   - First Scraped Date
   - Last Scraped Date
   - Times Scraped
   - Scrape Run ID
   - (Consider keeping Enrichment Error for debugging)

   **Impact:** Simpler database, faster queries

### Quick Wins (1 hour)

4. **Populate 5 Available Fields:**
   - Google Maps URL (from Apify)
   - Operating Hours (from Apify)
   - Enrichment Error (from failures)
   - First Scraped Date (from FEAT-001)
   - Last Scraped Date (from FEAT-001)

   **Effort:** 30-60 minutes
   **Impact:** Better data, improved debugging

### Keep for Future

5. **Preserve Future Feature Fields:**
   - LinkedIn Profile URL (FEAT-007)
   - PMS Vendor (FEAT-006)
   - Out of Scope Reason (FEAT-003 enhancement)
   - Has Multiple Locations (already used in FEAT-003)

6. **Preserve Sales Workflow Fields:**
   - All 7 manual fields (Assigned To, Call Notes, etc.)

---

## 🔍 Field Name Consistency Check

### Inconsistencies Found
None! All field names match between code and Notion after the "Vet Count" fix.

### Potential Naming Improvements
1. "Personalization Context" → Consider renaming to "Outreach Context" (clearer purpose)
2. "Score Breakdown" → Consider renaming to "Scoring Details" (more descriptive)

---

## 📝 Next Steps

1. **User Decision Required:**
   - Should we add the 4 missing enrichment fields? (Awards, News, Community, Philosophy)
   - Should we remove the 8 redundant/unused fields?
   - Should we populate the 5 "quick win" fields?

2. **If Yes to Adding Fields:**
   - Create Notion fields (5 min)
   - Re-run test: `python test_e2e_enrichment.py --limit 1 --enable-scoring --yes`
   - Validate: `python validate_notion_fields.py <practice_id>`

3. **If Yes to Removing Fields:**
   - Archive data from fields to be removed
   - Delete fields in Notion
   - Update documentation

4. **If Yes to Quick Wins:**
   - Update `src/integrations/notion_mapper.py` (FEAT-001)
   - Update `src/integrations/notion_enrichment.py` (FEAT-002)
   - Test and validate

---

**Analysis Complete:** Ready for user review and decision.
