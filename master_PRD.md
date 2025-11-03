Notion Database (Sherpas Workspace) URL: [(https://www.notion.so/2a0edda2a9a081d98dc9daa43c65e744?pvs=21)] 

# 🎯 **PRODUCT REQUIREMENTS DOCUMENT (PRD)**

## **Veterinary Practice Lead Generation & Scoring System - MVP**

**Version:** 1.0

**Date:** November 3, 2025

**Target:** Boston, MA Veterinary Clinics (3-5 vets sweet spot)

**Objective:** Generate 100+ scored, enriched leads ready for cold calling

---

## 📋 **EXECUTIVE SUMMARY**

**Problem:** Dan needs 100 qualified veterinary practice leads in Boston to sell the Voice Receptionist product. Manual research is too slow and lacks depth.

**Solution:** Automated lead generation pipeline that:

1. Scrapes Google Maps for veterinary practices
2. Enriches with website data (vet count, decision makers, personalization context)
3. Optionally enriches with LinkedIn for decision maker discovery
4. Scores leads 0-120 based on ICP fit
5. Pushes all data to Notion for sales workflow

**Success Criteria:**

- ✅ 100+ practices in Notion database
- ✅ 80%+ have confirmed vet count
- ✅ 60%+ have identified decision maker name
- ✅ 50%+ have personalization context for outreach
- ✅ All leads scored and prioritized (Hot/Warm/Cold)
- ✅ Cost <$10 for MVP run

---

## 🏗️ **SYSTEM ARCHITECTURE**

```
┌─────────────────────────────────────────────────────────┐
│ STAGE 1: Google Maps Scraping (Primary Data Source)     │
│ Tool: Apify Actor - compass/crawler-google-places       │
│ Input: Search terms + Boston geography                  │
│ Output: ~150-200 raw veterinary practice records        │
│ Data: Name, address, phone, website, Place ID,          │
│       rating, review count, categories, hours            │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ STAGE 2: Website Scraping (Critical Enrichment)         │
│ Tool: Crawl4AI + OpenAI API (cheaper model)             │
│ For each practice with website:                         │
│   • Crawl: Homepage, Team/Staff page, About page        │
│   • Extract with LLM:                                    │
│     - Vet count (total + per location if multiple)      │
│     - Owner/Practice Manager name & contact              │
│     - Services offered (emergency, specialty, etc.)      │
│     - Technology features (booking, portal, chat)        │
│     - PERSONALIZATION CONTEXT (unique facts)             │
│ Delay: 3-5 seconds between requests (respectful)        │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ STAGE 3: LinkedIn Decision Maker Lookup (Optional)      │
│ Tool: Apify Actor - apimaestro/linkedin-company-        │
│       employees-scraper-no-cookies                       │
│ Trigger: Only if website scraping didn't find           │
│          owner/practice manager                          │
│ Extract: Employee names, titles (filter for Owner,      │
│          Practice Manager, Hospital Administrator)       │
│ Cost: ~$0.50 for 100 practices                          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ STAGE 4: Lead Scoring & Classification                  │
│ Calculate: 0-120 point score based on ICP fit           │
│ Classify: Practice Size (Solo/Small/Sweet Spot/Large)   │
│ Prioritize: Hot (80-120) / Warm (50-79) / Cold (0-49)   │
│ Flag: Out of scope (10+ vets, solo practitioner)        │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ STAGE 5: Notion Database Push (Batch Insert/Update)     │
│ De-duplicate: Check Place ID against existing records   │
│ Batch: 25-50 records per API call (reliable)            │
│ Logic: Update data fields, preserve sales status        │
│ Output: All enriched leads ready for Dan's outreach     │
└─────────────────────────────────────────────────────────┘

```

**Execution Time:** ~1.5-2 hours for 150 practices

**Estimated Cost:** $6-8 total

---

## 🎯 **TARGET IDEAL CUSTOMER PROFILE (ICP)**

### **Sweet Spot (3-5 Vets):**

- **Perfect fit** for Voice Receptionist
- Multi-doctor coordination needed
- High enough volume to justify $799/month
- Not too corporate/complex for Phase 1

### **Must-Have Signals:**

1. Located in Boston/Greater Boston area
2. 3-5 veterinarians (primary target)
3. Emergency or 24/7 services (high complexity)
4. 50+ Google reviews (busy practice indicator)
5. Has website (tech sophistication baseline)

### **Strong Positive Signals:**

- Owner/Practice Manager name identified
- Multiple locations
- Modern website with online booking
- Recent expansion or growth signals
- Unique personalization context available

### **Disqualifiers:**

- Solo practitioner (1 vet) - too small
- 10+ vets - corporate, out of scope for MVP
- No website - not tech-forward enough
- <10 Google reviews - too new or not busy
- Permanently closed

---

## 📊 **LEAD SCORING ALGORITHM (0-120 Points)**

### **BASE SCORE (0-100 Points)**

### **Practice Size & Complexity (40 points max)**

- 🎯 **3-5 vets confirmed** → 25 pts (SWEET SPOT)
- 2 or 6 vets → 15 pts (Still qualified)
- 7-9 vets → 5 pts (Large, track for future)
- 🚨 **Emergency/24-hour services** → 15 pts

### **Call Volume Indicators (30 points max)**

- 100+ Google reviews → 20 pts
- 50-99 Google reviews → 12 pts
- 20-49 Google reviews → 5 pts
- **Multiple locations** → 10 pts

### **Technology Sophistication (20 points max)**

- Online booking visible → 10 pts
- Modern website → 5 pts
- Client portal/live chat → 5 pts

### **Baseline Quality (10 points max)**

- Rating 3.5+ → 5 pts
- Has website → 5 pts

### **DECISION MAKER BONUS (+20 Points)**

Critical for getting past reception:

- 🏆 **Owner/PM name + direct email found** → +20 pts
- ⭐ **Owner/PM name + email pattern guessable** → +15 pts (mark as "Guessed - Verify")
- 👤 **Owner/PM name found only** → +10 pts
- 📞 **Generic contact only** → 0 pts

**Total Maximum Score:** 120 points

### **PRIORITY TIERS**

- 🔥 **HOT (80-120 pts):** 3-5 vets + decision maker + emergency/high volume
- 🌡️ **WARM (50-79 pts):** Good signals, some unknowns
- ❄️ **COLD (0-49 pts):** Weak signals, needs manual research
- ⛔ **OUT OF SCOPE:** 10+ vets (corporate) OR 1 vet (too small)

---

## 🗂️ **NOTION DATABASE SCHEMA**

### **Instructions for Database Creation:**

**📍 FOR SEPARATE CLAUDE CHAT:**

Create a new Notion database with the following schema. Parent page ID will be provided by user.

**Database Name:** `Veterinary Lead Pipeline - Boston`

**Database Type:** Full Page Database (not inline)

---

### **COMPLETE FIELD SPECIFICATION:**

### **🔵 CORE DATA (From Google Maps Scraping)**

| Field Name | Type | Configuration | Required | Notes |
| --- | --- | --- | --- | --- |
| **Practice Name** | Title | - | ✅ Yes | Primary identifier |
| **Address** | Text | - | ✅ Yes | Full street address |
| **City** | Text | - | ✅ Yes | For filtering/sorting |
| **State** | Text | Default: "MA" | ✅ Yes | For multi-state expansion |
| **ZIP Code** | Text | - | No | From address |
| **Phone** | Phone | - | ✅ Yes | Main practice number |
| **Website** | URL | - | No | Practice website |
| **Google Maps URL** | URL | - | ✅ Yes | Link to Google listing |
| **Google Place ID** | Text | - | ✅ Yes | Unique ID for de-duplication |
| **Google Rating** | Number | Format: 0-5, 1 decimal | No | Google star rating |
| **Google Review Count** | Number | - | No | Total Google reviews |
| **Business Categories** | Multi-select | Options: Veterinarian, Animal Hospital, Emergency Vet, Pet Store, Grooming | No | From Google categories |

### **🟢 ENRICHMENT DATA (From Website Scraping)**

| Field Name | Type | Configuration | Required | Notes |
| --- | --- | --- | --- | --- |
| **Confirmed Vet Count - Total** | Number | - | No | Total across all locations |
| **Confirmed Vet Count - Per Location** | Number | - | No | Average per location if multiple |
| **Practice Size Category** | Select | Options: Solo, Small (2-3), Sweet Spot (3-5), Large (6-9), Corporate (10+), Unknown | ✅ Yes | Auto-calculated from vet count |
| **Has Emergency Services** | Checkbox | Default: Unchecked | No | 24/7 or after-hours |
| **Has Multiple Locations** | Checkbox | Default: Unchecked | No | More than one office |
| **Has Online Booking** | Checkbox | Default: Unchecked | No | Digital scheduling visible |
| **Technology Features** | Multi-select | Options: Modern Website, Live Chat, Client Portal, Mobile App, Email Reminders, SMS Reminders | No | Tech sophistication signals |
| **Services Offered** | Multi-select | Options: General Practice, Emergency, Surgery, Dental, Exotic Animals, Boarding, Grooming, House Calls | No | Service complexity |
| **Operating Hours** | Long Text | - | No | Business hours (formatted) |

### **👥 DECISION MAKER INFORMATION**

| Field Name | Type | Configuration | Required | Notes |
| --- | --- | --- | --- | --- |
| **Owner/Manager Name** | Text | - | No | Decision maker identified |
| **Owner/Manager Title** | Select | Options: Owner, Practice Manager, Hospital Administrator, Veterinarian Owner, Unknown | No | Leadership role |
| **Owner/Manager Email** | Email | - | No | If found or guessed |
| **Email Status** | Select | Options: Verified Found, Pattern Guessed, LinkedIn Found, Not Found | No | Source and confidence |
| **Decision Maker Contact Quality** | Select | Options: 🏆 Complete, ⭐ Strong, 👤 Partial, 📞 Generic | ✅ Yes | Bonus score indicator |
| **LinkedIn Profile URL** | URL | - | No | If found via LinkedIn lookup |

### **🎯 PERSONALIZATION CONTEXT (Critical for Cold Calling)**

| Field Name | Type | Configuration | Required | Notes |
| --- | --- | --- | --- | --- |
| **Personalization Context** | Long Text | - | No | **UNIQUE FACTS FOR CONVERSATION OPENERS** Examples: "Recently opened 2nd location in Newton", "Fear-free certified practice", "Dr. Johnson featured in Boston Magazine 2024", "Specializes in exotic birds - only one in area" |

### **📈 SCORING & PRIORITIZATION**

| Field Name | Type | Configuration | Required | Notes |
| --- | --- | --- | --- | --- |
| **Lead Score** | Number | Format: 0-120 | ✅ Yes | Total ICP fit score |
| **Priority Tier** | Select | Options: 🔥 Hot (80-120), 🌡️ Warm (50-79), ❄️ Cold (0-49), ⛔ Out of Scope | ✅ Yes | Call priority |
| **Score Breakdown** | Long Text | - | No | Which criteria met/missed |
| **Out of Scope Reason** | Select | Options: Too Large (10+ vets), Solo Practice, No Website, Permanently Closed, Other | No | Why disqualified |

### **🎯 SALES WORKFLOW**

| Field Name | Type | Configuration | Required | Notes |
| --- | --- | --- | --- | --- |
| **Status** | Select | Options: New, Researching, Contact Ready, Contacted, Qualified, Pitched, Closed Won, Closed Lost, Not a Fit | ✅ Yes | Default: "New" |
| **Assigned To** | Person | - | No | Dan / Jack / Remco |
| **Research Notes** | Long Text | - | No | Dan's pre-call research |
| **Call Notes** | Long Text | - | No | Conversation notes |
| **Next Action** | Text | - | No | What needs to happen next |
| **Next Follow-Up Date** | Date | - | No | When to reach out again |
| **Last Contact Date** | Date | - | No | Most recent touch |
| **Outreach Attempts** | Number | Default: 0 | No | How many times called |

### **🔧 METADATA (Tracking)**

| Field Name | Type | Configuration | Required | Notes |
| --- | --- | --- | --- | --- |
| **First Scraped Date** | Date | Default: Today | ✅ Yes | When first discovered |
| **Last Scraped Date** | Date | Default: Today | ✅ Yes | Most recent update |
| **Scrape Run ID** | Text | - | ✅ Yes | Batch identifier (e.g., "BOS-2025-11-03-01") |
| **Data Sources** | Multi-select | Options: Google Maps, Website, LinkedIn | ✅ Yes | Where data came from |
| **Times Scraped** | Number | Default: 1 | ✅ Yes | How many runs found this |
| **Data Completeness** | Select | Options: High (80%+), Medium (50-79%), Low (<50%) | No | % of fields populated |

**Total Fields:** 48 fields

---

## ⚙️ **CONFIGURATION FILE (config.json)**

```json
{
  "project_name": "Veterinary Lead Generation - Boston MVP",
  "version": "1.0",

  "target": {
    "business_type": "veterinary clinics",
    "search_terms": [
      "veterinarian",
      "vet clinic",
      "animal hospital",
      "emergency vet",
      "veterinary hospital"
    ],
    "geography": {
      "center": "Boston, MA, USA",
      "radius_miles": 25,
      "include_cities": [
        "Boston",
        "Cambridge",
        "Brookline",
        "Newton",
        "Quincy",
        "Somerville",
        "Medford",
        "Waltham",
        "Arlington",
        "Watertown"
      ]
    }
  },

  "apify": {
    "google_maps_actor": "compass/crawler-google-places",
    "linkedin_actor": "apimaestro/linkedin-company-employees-scraper-no-cookies",
    "max_google_results": 200,
    "api_key_env_var": "APIFY_API_KEY"
  },

  "website_scraping": {
    "tool": "crawl4ai",
    "llm_provider": "openai",
    "llm_model": "gpt-4o-mini",
    "pages_to_crawl": [
      "homepage",
      "team",
      "about",
      "our-doctors",
      "staff",
      "meet-the-team"
    ],
    "delay_between_requests_seconds": 4,
    "timeout_seconds": 30,
    "extraction_prompt_template": "website_extraction_prompt.txt"
  },

  "linkedin_enrichment": {
    "enabled": true,
    "trigger_condition": "no_decision_maker_from_website",
    "job_titles_to_find": [
      "Owner",
      "Practice Owner",
      "Practice Manager",
      "Hospital Administrator",
      "Hospital Manager",
      "Managing Director"
    ],
    "max_cost_per_practice": 0.10
  },

  "filtering": {
    "hard_disqualifiers": {
      "min_google_reviews": 10,
      "must_have_website": true,
      "exclude_if_closed": true,
      "exclude_keywords": [
        "mobile only",
        "house call only",
        "mobile vet service"
      ]
    },
    "must_have_one_of": [
      "emergency_services",
      "50_plus_reviews",
      "multiple_locations",
      "3_plus_vets"
    ]
  },

  "scoring": {
    "practice_size_and_complexity": {
      "3_to_5_vets": 25,
      "2_or_6_vets": 15,
      "7_to_9_vets": 5,
      "emergency_services": 15
    },
    "call_volume_indicators": {
      "100_plus_reviews": 20,
      "50_to_99_reviews": 12,
      "20_to_49_reviews": 5,
      "multiple_locations": 10
    },
    "technology_sophistication": {
      "online_booking": 10,
      "modern_website": 5,
      "client_portal_or_chat": 5
    },
    "baseline_quality": {
      "rating_3_5_plus": 5,
      "has_website": 5
    },
    "decision_maker_bonus": {
      "name_and_direct_email": 20,
      "name_and_guessed_email": 15,
      "name_only": 10,
      "generic_contact": 0
    },
    "priority_tiers": {
      "hot": {"min": 80, "max": 120, "emoji": "🔥"},
      "warm": {"min": 50, "max": 79, "emoji": "🌡️"},
      "cold": {"min": 0, "max": 49, "emoji": "❄️"}
    }
  },

  "notion": {
    "api_key_env_var": "NOTION_API_KEY",
    "database_id_env_var": "NOTION_DATABASE_ID",
    "batch_size": 25,
    "update_existing_records": true,
    "preserve_fields_on_update": [
      "Status",
      "Assigned To",
      "Research Notes",
      "Call Notes",
      "Next Action",
      "Next Follow-Up Date",
      "Last Contact Date",
      "Outreach Attempts"
    ]
  },

  "output": {
    "scrape_run_id_format": "{city_short}-{date}-{run_number}",
    "log_level": "INFO",
    "save_raw_data": true,
    "raw_data_directory": "./data/raw/"
  }
}

```

---

## 🔍 **WEBSITE EXTRACTION PROMPT (website_extraction_prompt.txt)**

```
You are analyzing a veterinary practice website to extract structured data for B2B sales lead generation.

From the provided website content, extract the following information in JSON format:

{
  "vet_count": {
    "total": <number or null>,
    "per_location": <number or null>,
    "confidence": "high|medium|low",
    "source": "explicit count mentioned|counted from team page|estimated from context"
  },

  "veterinarians": [
    {
      "name": "Dr. First Last",
      "title": "Owner|Associate Veterinarian|Chief Veterinarian",
      "specialties": ["surgery", "internal medicine", "etc"]
    }
  ],

  "decision_maker": {
    "name": "First Last",
    "title": "Owner|Practice Manager|Hospital Administrator|null",
    "email": "email@domain.com or null",
    "email_status": "verified_found|pattern_guessed|not_found",
    "confidence": "high|medium|low"
  },

  "email_pattern": {
    "pattern": "firstname@domain|firstlast@domain|null",
    "example_emails_found": ["staff@domain.com", "reception@domain.com"]
  },

  "services": {
    "emergency_24_7": true|false,
    "after_hours": true|false,
    "surgery": true|false,
    "dental": true|false,
    "exotic_animals": true|false,
    "boarding": true|false,
    "grooming": true|false,
    "house_calls": true|false
  },

  "technology_features": {
    "online_booking": true|false,
    "live_chat": true|false,
    "client_portal": true|false,
    "mobile_app": true|false,
    "email_reminders": true|false,
    "sms_reminders": true|false,
    "modern_website_design": true|false
  },

  "multiple_locations": {
    "has_multiple": true|false,
    "location_count": <number or null>,
    "locations": ["City1", "City2"]
  },

  "personalization_context": {
    "unique_facts": [
      "Recently opened 2nd location in Newton (2024)",
      "Fear-free certified practice",
      "Dr. Sarah Johnson featured in Boston Magazine Best Vets 2024",
      "Only practice in Boston specializing in exotic birds",
      "Family-owned for 3 generations since 1952",
      "New state-of-the-art surgical suite opened May 2024",
      "Sponsors Boston Animal Rescue League"
    ],
    "awards_recognition": [],
    "community_involvement": [],
    "recent_expansions": [],
    "unique_specialties": []
  },

  "operating_hours": {
    "formatted": "Mon-Fri: 8am-7pm, Sat: 9am-5pm, Sun: Closed",
    "extended_hours": true|false,
    "weekend_hours": true|false
  }
}

CRITICAL INSTRUCTIONS:
1. The "personalization_context.unique_facts" field is ESSENTIAL - find at least 2-3 unique, specific facts about this practice that could be conversation starters for a cold call.
2. For decision_maker.email, if you find a pattern (e.g., staff@domain.com), intelligently guess owner@ or manager@ and mark as "pattern_guessed".
3. Be conservative with vet_count - only report if confident. Better to return null than guess incorrectly.
4. Extract ACTUAL names when possible, not generic titles.
5. Return null for any field where information is not found - do not guess or hallucinate.

```

---

## 🔄 **DE-DUPLICATION LOGIC**

### **Primary Key Hierarchy:**

1. **Google Place ID** (most reliable, unique Google identifier)
2. **Website URL** (normalized: lowercase, remove www., trailing slash)
3. **Phone Number** (normalized: remove all formatting, country code)
4. **Name + Address** (fuzzy match, 85%+ similarity)

### **Update vs. Create Logic:**

```python
def upsert_lead_to_notion(new_lead_data, existing_records):
    """
    Check if lead exists, update data or create new record
    """
    # Try to match by Place ID first
    existing = find_by_place_id(new_lead_data['place_id'], existing_records)

    if existing:
        # UPDATE existing record
        update_fields = {
            # Update data fields from scraping
            'Google Rating': new_lead_data['rating'],
            'Google Review Count': new_lead_data['reviews'],
            'Confirmed Vet Count - Total': new_lead_data['vet_count'],
            # ... all enrichment fields

            # Update metadata
            'Last Scraped Date': today(),
            'Times Scraped': existing['Times Scraped'] + 1,
            'Data Sources': merge_unique(existing['Data Sources'], new_lead_data['sources'])
        }

        # PRESERVE sales workflow fields - never overwrite!
        preserve_fields = [
            'Status', 'Assigned To', 'Research Notes', 'Call Notes',
            'Next Action', 'Next Follow-Up Date', 'Last Contact Date',
            'Outreach Attempts'
        ]

        # If status is not "New", don't update status
        if existing['Status'] != 'New':
            preserve_fields.append('Priority Tier')  # Don't change priority if being worked

        notion_update(existing['id'], update_fields, preserve=preserve_fields)
        return 'UPDATED'

    else:
        # CREATE new record
        notion_create(new_lead_data)
        return 'CREATED'

```

---

## ⚠️ **ERROR HANDLING & EDGE CASES**

### **Google Maps Scraping**

- **Rate limiting:** Apify handles this automatically
- **No results found:** Expand radius or try alternate search terms
- **Duplicate listings:** Filter by Place ID uniqueness

### **Website Scraping**

- **No website:** Skip enrichment, mark "Data Completeness: Low"
- **Website timeout:** Retry once, then skip and flag for manual review
- **JavaScript-heavy sites:** Crawl4AI handles this well
- **403/blocked:** Rotate user agents, respect robots.txt

### **LLM Extraction**

- **Malformed JSON:** Retry with clearer prompt, fall back to regex parsing
- **Hallucination risk:** Cross-validate vet count with multiple page sections
- **No personalization context found:** Mark as "Generic - Manual Research Needed"

### **LinkedIn Lookup**

- **Company not found:** Try alternate name formats (e.g., "Boston Animal Hospital" vs "Boston Animal Hospital, Inc.")
- **No matching job titles:** Expand search to all employees, filter by seniority
- **Rate limits:** Batch requests, spread across time

### **Notion API**

- **Rate limits:** 3 requests/second, batch records
- **Field type mismatches:** Validate data before pushing
- **Network errors:** Retry with exponential backoff

---

## 💰 **COST BREAKDOWN (MVP Execution)**

| Stage | Tool | Volume | Unit Cost | Total |
| --- | --- | --- | --- | --- |
| **Google Maps Scraping** | Apify (compass actor) | 200 practices | ~$0.01/result | **$2.00** |
| **Website Scraping** | Crawl4AI | 150 websites | Free (local) | **$0.00** |
| **LLM Extraction** | OpenAI GPT-4o-mini | 150 extractions | ~$0.02/call | **$3.00** |
| **LinkedIn Lookup** | Apify (LinkedIn actor) | ~50 practices | ~$0.01/lookup | **$0.50** |
| **Notion API** | Notion | 150 records | Free tier | **$0.00** |
| **Infrastructure** | Server/compute | 2 hours | Negligible | **$0.00** |
| **TOTAL** |  |  |  | **~$5.50** |

**With buffer:** $6-8 for MVP execution

---

## ⏱️ **IMPLEMENTATION TIMELINE**

### **MVP Build (Today - 6-8 hours)**

- Hour 1-2: Project setup, config file, dependencies
- Hour 2-3: Google Maps scraping + data pipeline
- Hour 3-5: Crawl4AI website scraping + LLM extraction
- Hour 5-6: LinkedIn enrichment (optional stage)
- Hour 6-7: Scoring algorithm + classification
- Hour 7-8: Notion integration + de-duplication + testing

### **MVP Execution (1.5-2 hours)**

- 0:00-0:10: Google Maps scrape (200 practices)
- 0:10-1:20: Website scraping (150 sites × 30 sec avg)
- 1:20-1:30: LinkedIn enrichment (50 practices)
- 1:30-1:40: Scoring + classification
- 1:40-1:50: Notion batch push
- 1:50-2:00: Validation + spot checks

**Total MVP delivery:** Same day (build + execute)

---

## 🚀 **EXECUTION INSTRUCTIONS FOR CLAUDE CODE**

### **Phase 1: Project Setup**

```bash
# Create project structure
/src
  /scrapers
    google_maps.py
    website_scraper.py
    linkedin_scraper.py
  /scoring
    lead_scorer.py
    classifier.py
  /notion
    notion_client.py
    upsert.py
  /utils
    config_loader.py
    logger.py
/config
  config.json
  website_extraction_prompt.txt
/data
  /raw
  /processed
/tests
requirements.txt
.env.example
README.md
main.py

```

### **Phase 2: Dependencies**

```
# requirements.txt
apify-client==1.7.0
crawl4ai==0.3.0
openai==1.0.0
notion-client==2.2.0
python-dotenv==1.0.0
requests==2.31.0
beautifulsoup4==4.12.0

```

### **Phase 3: Environment Variables**

```bash
# .env
APIFY_API_KEY=your_apify_key
OPENAI_API_KEY=your_openai_key
NOTION_API_KEY=your_notion_key
NOTION_DATABASE_ID=your_database_id

```

### **Phase 4: Execution**

```bash
python main.py --config config/config.json --mode full

```

**Modes:**

- `full`: Complete pipeline (Google → Website → LinkedIn → Score → Notion)
- `google-only`: Just Google Maps scraping
- `enrich`: Enrich existing Notion records with website/LinkedIn data
- `score-only`: Recalculate scores for existing records

---

## 📈 **SUCCESS METRICS**

### **Quantitative:**

- ✅ 100+ practices in Notion
- ✅ 80%+ have confirmed vet count (120+ of 150)
- ✅ 60%+ have decision maker name (90+ of 150)
- ✅ 50%+ have personalization context (75+ of 150)
- ✅ 40%+ are "Hot" tier (60+ of 150)
- ✅ <$10 total cost

### **Qualitative:**

- ✅ Dan can start calling within 2 hours of kickoff
- ✅ Each lead has actionable information for personalization
- ✅ System is config-driven for easy geography/business type changes
- ✅ Data quality is high enough to avoid wasted calls

---

## 🔮 **PHASE 2 & 3 ROADMAP**

### **Phase 2 - Enhanced (Next Week)**

- Add Yelp cross-reference for additional review validation
- Implement email verification (SMTP check for guessed emails)
- Add PMS vendor detection (job postings, tech stack analysis)
- Build analytics dashboard (lead quality over time)
- A/B test different search terms and radius

### **Phase 3 - Scale (Month 2)**

- Multi-geography support (expand to NYC, SF, Chicago)
- Competitive intelligence (track competitor mentions)
- Recurring scraper (weekly updates to existing leads)
- Integration with CRM (HubSpot, Salesforce)
- Dental practice adaptation (HIPAA compliance focus)

---

## ❓ **OPEN QUESTIONS / DECISIONS NEEDED**

1. ✅ **Notion Parent Page ID:** User will provide
2. ✅ **Email Guessing:** Yes, mark as "Pattern Guessed"
3. ✅ **LinkedIn Enrichment:** Yes, via Apify no-cookie actors
4. ✅ **Yelp:** Descoped for MVP
5. ✅ **Vet Counting:** Track both total and per-location
6. ✅ **Notion Push:** Batch after all enrichment complete

---

## 📝 **ACCEPTANCE CRITERIA**

**The MVP is successful when:**

1. ✅ System runs end-to-end without manual intervention
2. ✅ All 100+ leads pushed to Notion with proper de-duplication
3. ✅ Lead scores are accurate and prioritization makes sense
4. ✅ Personalization context is useful for cold calling
5. ✅ Decision maker names are identified for 60%+ of leads
6. ✅ Dan can immediately start outreach using the data
7. ✅ Config file allows easy adaptation to new markets/businesses
8. ✅ Cost stays under $10 for MVP run
9. ✅ Documentation is clear for future team members

---

## 🎯 **FINAL NOTES FOR CLAUDE CODE IMPLEMENTATION**

### **Critical Priorities:**

1. **Personalization context field** - This is the secret weapon for cold calling
2. **Decision maker identification** - Getting past reception is the #1 challenge
3. **3-5 vet sweet spot** - Don't waste time on too-small or too-large practices
4. **De-duplication** - Multiple scrapes should update, not create duplicates
5. **Notion batching** - Reliable pushes without rate limiting

### **Quality > Speed:**

- Take 3-5 seconds between website crawls (respectful scraping)
- Validate data before scoring (garbage in = garbage out)
- Log everything for debugging
- Save raw data for manual review if needed

### **Config-Driven Everything:**

- Search terms, geography, scoring weights all in config.json
- Easy to adapt to dental practices, different cities, etc.
- Future team members can modify without touching code

---

**END OF PRD**

