# Notion Field Documentation - Website Enrichment

**Last Updated:** 2025-11-05
**Source:** Actual code analysis of extraction prompt + Pydantic models

---

## How Fields Are Populated

All fields are populated by OpenAI GPT-4o analyzing scraped website HTML content. The extraction uses **structured outputs** to guarantee valid JSON conforming to our Pydantic schema.

### Pages Scraped

Crawl4AI scrapes up to 5 pages per practice:
- **Homepage** (always attempted)
- **/about** pages (pattern: `*about*`)
- **/team** or **/staff** pages (pattern: `*team*`, `*staff*`)
- **/contact** pages (pattern: `*contact*`)

Max depth: 1 level from homepage
Timeout: 30 seconds per page

---

## Field Definitions

### Core Practice Information

#### **Vet Count (Total)**
- **Type:** Number (1-50)
- **Source:** Counted from team/staff pages OR explicit mention
- **Extraction Logic:**
  - OpenAI counts individual DVMs listed on team/staff pages
  - Looks for explicit statements like "Our 5 veterinarians..."
  - Conservative approach - returns null if uncertain
- **Confidence Levels:**
  - `high`: Explicit count or complete team page with photos
  - `medium`: Approximate count from context
  - `low`: Estimated from incomplete information
- **Example:** 4 veterinarians

#### **Vet Count Confidence**
- **Type:** Text (high/medium/low)
- **Source:** How the vet count was determined
- **When it's high:** Explicit team page listing all DVMs
- **When it's medium:** Count inferred from context
- **When it's low:** Educated guess from limited info

---

### Decision Maker Information

#### **Decision Maker Name**
- **Type:** Text (max 100 chars)
- **Source:** About page, team page, footer
- **Extraction Logic:**
  - Looks for titles: "Owner", "Practice Owner", "Medical Director", "Practice Manager", "Hospital Administrator"
  - Extracts actual names, not generic titles
  - Prioritizes owners over managers
- **Example:** "Dr. Mark E. Broady"

#### **Decision Maker Role**
- **Type:** Text (max 100 chars)
- **Source:** Same as name
- **Common Values:** "Owner", "Medical Director", "Practice Manager", "Hospital Administrator"
- **Example:** "Owner"

#### **Decision Maker Email**
- **Type:** Email (max 100 chars)
- **Source:** Contact page, team page, about page
- **Extraction Logic:**
  - **NEVER guessed or fabricated**
  - Must be explicitly stated on website
  - Does NOT construct emails (no "firstname@domain.com" guessing)
  - Often null because emails are in images or hidden
- **Example:** "drbroady@shelburnevet.com" or null

#### **Decision Maker Phone**
- **Type:** Text (max 50 chars)
- **Source:** Contact page, header, footer
- **Extraction Logic:**
  - Usually returns practice main line (not direct extension)
  - May include tel: or sms: prefixes (these cause validation errors)
- **Example:** "(413) 625-6622" or null

---

### Technology & Services (Boolean Fields)

#### **24/7 Emergency Services**
- **Type:** True/False (default: False)
- **Source:** Services page, homepage, about page
- **Prompt Field:** `services.emergency_24_7`
- **Extraction Logic:**
  - Marks true ONLY if explicitly mentioned
  - Looks for phrases like "24/7 emergency", "after-hours emergency", "open 24 hours"
  - Does NOT assume from "emergency services" alone
- **Why it might be False:** Practice doesn't offer 24/7 or doesn't mention it prominently

#### **Online Booking**
- **Type:** True/False (default: False)
- **Source:** Homepage, services page, contact page
- **Prompt Field:** `technology_features.online_booking`
- **Extraction Logic:**
  - Marks true if online appointment scheduling is visible
  - Looks for "book online", "schedule online", "request appointment online"
  - Does NOT count contact forms as "online booking"
- **Why it might be False:** Practice uses phone-only scheduling or doesn't mention online option

#### **Patient Portal**
- **Type:** True/False (default: False)
- **Source:** Services page, technology page, login links
- **Prompt Field:** `technology_features.patient_portal`
- **Extraction Logic:**
  - Marks true if online patient portal is mentioned
  - Looks for "patient portal", "my pet portal", "online records access"
  - Checks for login links to portal systems (PetDesk, VetCloud, etc.)
- **Why it might be False:** Practice doesn't offer portal or doesn't advertise it

#### **Telemedicine / Virtual Care**
- **Type:** True/False (default: False)
- **Source:** Services page, COVID updates, technology page
- **Prompt Field:** `technology_features.telemedicine`
- **Model Field:** `telemedicine_virtual_care`
- **Extraction Logic:**
  - Marks true if virtual consultations are offered
  - Looks for "telemedicine", "virtual appointments", "video consultations"
  - Does NOT count phone consultations as telemedicine
- **Why it might be False:** Practice doesn't offer virtual visits or stopped offering after COVID

---

### Personalization & Outreach Data

#### **Personalization Context**
- **Type:** List of strings (max 3 items)
- **Source:** About page, homepage, news section
- **Prompt Field:** `personalization_context.unique_facts`
- **Model Field:** `personalization_context`
- **Extraction Logic:**
  - Finds 2-3 **SPECIFIC** and **UNIQUE** facts about this practice
  - Must be conversation starters for cold calls
  - **GOOD examples:**
    - "Founded by Dr. Mark Broady with over 45 years of experience"
    - "Recently opened 2nd location in Newton (October 2024)"
    - "Only practice in Boston specializing in avian medicine"
  - **BAD examples (rejected):**
    - "They care about animals" (too generic)
    - "Friendly staff" (applies to everyone)
    - "Good reviews" (not specific)
- **Why it might be empty:** Website has no unique or specific facts, only generic content
- **Example:**
  ```
  - "Founded by Dr. Mark Broady with over 45 years of experience."
  - "Lila Griswold has a passion for learning and specializes in fractious cats."
  ```

#### **Awards & Accreditations**
- **Type:** List of strings (max 5 items)
- **Source:** About page, homepage, certifications section
- **Prompt Field:** `personalization_context.awards_recognition` (MISMATCH!)
- **Model Field:** `awards_accreditations`
- **Current Status:** ⚠️ **NOT POPULATING** due to prompt/model mismatch
- **What it should extract:**
  - AAHA Accreditation
  - Fear Free Certified
  - Best Vet awards
  - Industry certifications
- **Why it's empty:** Extraction prompt asks for `awards_recognition` under nested `personalization_context`, but model expects standalone `awards_accreditations` field
- **Example (when fixed):** "AAHA Accredited", "Fear Free Certified"

#### **Community Involvement**
- **Type:** List of strings (max 3 items)
- **Source:** About page, news section, community page
- **Prompt Field:** `personalization_context.community_involvement` (MISMATCH!)
- **Model Field:** `community_involvement`
- **Current Status:** ⚠️ **NOT POPULATING** due to prompt/model mismatch
- **What it should extract:**
  - Local charity partnerships
  - Community event sponsorships
  - Rescue organization support
  - School programs
- **Why it's empty:** Same mismatch issue as awards
- **Example (when fixed):** "Sponsors Boston Animal Rescue League"

#### **Recent News/Updates**
- **Type:** List of strings (max 3 items, last 12 months)
- **Source:** News section, blog, about page updates
- **Prompt Field:** `personalization_context.recent_expansions` (MISMATCH!)
- **Model Field:** `recent_news_updates`
- **Current Status:** ⚠️ **NOT POPULATING** due to prompt/model mismatch
- **What it should extract:**
  - New location openings
  - New service launches
  - Major equipment investments
  - Staff additions
- **Why it's empty:** Prompt asks for `recent_expansions`, model expects `recent_news_updates`
- **Example (when fixed):** "Opened 2nd location in Newton (October 2024)"

#### **Practice Philosophy**
- **Type:** Text (max 500 chars)
- **Source:** About page mission statements, values sections
- **Prompt Field:** ⚠️ **NOT IN PROMPT AT ALL**
- **Model Field:** `practice_philosophy`
- **Current Status:** ⚠️ **NEVER POPULATES** - not requested in extraction prompt
- **What it should extract:**
  - Mission statements
  - Core values
  - Practice philosophy descriptions
  - "Our approach to veterinary care" sections
- **Why it's empty:** The extraction prompt doesn't ask OpenAI to extract this field at all
- **Example (when fixed):** "Our mission is to provide compassionate, cutting-edge veterinary care while treating every pet as family."

---

## Known Issues

### Issue #1: Prompt/Model Schema Mismatch

**Problem:** The extraction prompt (written first) uses a nested JSON structure that doesn't match the final Pydantic model:

**Prompt Structure:**
```json
"personalization_context": {
  "unique_facts": [...],
  "awards_recognition": [...],     // ← Wrong field name
  "community_involvement": [...],  // ← Should be standalone
  "recent_expansions": [...],      // ← Wrong field name
  "unique_specialties": [...]
}
```

**Model Structure:**
```python
personalization_context: List[str]        # Flat list, not nested
awards_accreditations: List[str]          # Separate field
community_involvement: List[str]          # Separate field
recent_news_updates: List[str]            # Different name
practice_philosophy: Optional[str]        # Missing from prompt entirely
```

**Impact:**
- ✅ `personalization_context` works (maps from unique_facts)
- ❌ `awards_accreditations` always empty
- ❌ `community_involvement` always empty
- ❌ `recent_news_updates` always empty
- ❌ `practice_philosophy` always null

**Fix Required:** Update `/config/website_extraction_prompt.txt` to match the Pydantic schema exactly.

---

### Issue #2: Missing Team Pages

**Problem:** Many practices don't have a `/team` or `/staff` page matching our URL patterns.

**Impact:**
- Lower decision maker email detection (emails often on team pages)
- Less accurate vet counts
- Missing personalization context from bios

**Possible Solutions:**
- Add more URL patterns: `*people*`, `*veterinarians*`, `*doctors*`
- Increase max_depth to 2 (slower, more expensive)
- Accept lower coverage for small practices

---

### Issue #3: Email Addresses Hidden

**Problem:** Many practices hide email addresses to prevent spam:
- Email in images (can't be scraped)
- Contact forms only
- Email obfuscation (`drsmith [at] vetclinic.com`)

**Impact:** Decision Maker Email field is often null even when email exists

**No automated solution** - this is by design to prevent spam

---

## Recommendations for Notion Display

### Field Grouping

**Basic Info:**
- Vet Count (Total)
- Vet Count Confidence

**Decision Maker Contact:**
- Decision Maker Name
- Decision Maker Role
- Decision Maker Email ⚠️ Often empty
- Decision Maker Phone

**Services & Technology:**
- 24/7 Emergency Services
- Online Booking
- Patient Portal
- Telemedicine / Virtual Care

**Outreach Data (for sales):**
- Personalization Context ✅ Usually populated
- Awards & Accreditations ⚠️ Currently broken
- Community Involvement ⚠️ Currently broken
- Recent News/Updates ⚠️ Currently broken
- Practice Philosophy ⚠️ Currently broken

### Field Tooltips

Add these as tooltips in Notion to explain empty values:

- **Decision Maker Email (if empty):** "Email not found on website. May be in image format or hidden to prevent spam. Check manually."
- **Awards (if empty):** "Not mentioned on website or extraction prompt needs fixing."
- **Community Involvement (if empty):** "Not mentioned on website or extraction prompt needs fixing."
- **Practice Philosophy (if empty):** "Not currently extracted. Extraction prompt needs updating."

---

## Testing a Website

To diagnose why fields aren't populating for a specific practice:

```bash
python diagnose_website_scraping.py https://practice-website.com/
```

This shows:
- Which pages were scraped
- What data was extracted
- Why specific fields are empty
- Recommendations

---

## Next Steps to Fix Empty Fields

1. **Update extraction prompt** (`/config/website_extraction_prompt.txt`):
   - Change nested `personalization_context` to flat fields
   - Add `practice_philosophy` extraction
   - Match field names exactly to Pydantic model

2. **Test with diagnostic tool**:
   ```bash
   python diagnose_website_scraping.py http://www.shelburnefallsvet.com/
   ```

3. **Run enrichment again** on existing practices to populate missing fields

4. **Expected improvement:**
   - Current: ~18-50% field coverage
   - After fix: ~60-80% field coverage (for practices with rich websites)

---

**Note:** Even with fixes, some fields will remain empty if the data genuinely isn't on the practice's website. Small practices often don't publish awards, community involvement, or formal philosophy statements.
