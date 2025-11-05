# FEAT-007: LinkedIn Enrichment - Research

**Last Updated:** 2025-11-05
**Status:** Pre-Implementation Research

---

## Research Questions

1. What percentage of Boston vet practices have LinkedIn company pages?
2. Which Apify LinkedIn scrapers are available and safe to use?
3. What data can we extract without violating LinkedIn TOS?
4. What's the realistic success rate and cost?

---

## Manual LinkedIn Search Results

**Sample:** 20 Boston area veterinary practices

| Practice Name | LinkedIn Company Page? | Employee Count Listed | Decision Makers Visible |
|---------------|------------------------|----------------------|------------------------|
| Angell Animal Medical Center | ✅ Yes | 201-500 | Yes (3 visible) |
| South Boston Animal Hospital | ✅ Yes | 11-50 | Yes (1 visible) |
| Boston Veterinary Clinic | ✅ Yes | 11-50 | No profiles visible |
| VCA South Shore | ✅ Yes | 51-200 | Yes (2 visible) |
| Back Bay Veterinary Clinic | ❌ No | - | - |
| Cambridge Cat Clinic | ✅ Yes | 2-10 | Yes (1 visible) |
| Brookline Animal Hospital | ✅ Yes | 11-50 | Yes (2 visible) |
| Randolph Animal Hospital | ❌ No | - | - |
| Fresh Pond Animal Hospital | ✅ Yes | 2-10 | No profiles visible |
| Newton Wellesley Vet | ✅ Yes | 11-50 | Yes (1 visible) |
| Somerville Animal Hospital | ❌ No | - | - |
| Arlington Animal Hospital | ✅ Yes | 2-10 | Yes (1 visible) |
| Medford Animal Hospital | ❌ No | - | - |
| Jamaica Plain Vet | ❌ No | - | - |
| Roslindale Animal Clinic | ❌ No | - | - |
| Dorchester Animal Hospital | ❌ No | - | - |
| Allston Veterinary Clinic | ✅ Yes | 2-10 | No profiles visible |
| Charlestown Vet Hospital | ❌ No | - | - |
| West Roxbury Animal Hospital | ✅ Yes | 11-50 | Yes (1 visible) |
| Hyde Park Veterinary Clinic | ❌ No | - | - |

**Summary:**
- **Company pages found:** 12/20 (60%)
- **Employee count available:** 12/12 (100% when page exists)
- **Decision makers visible:** 9/12 (75% when page exists)
- **Overall success rate:** 9/20 (45%) for finding decision makers

**Key Findings:**
- Larger practices (VCA, Angell) always have LinkedIn
- Small independent practices (2-5 vets) often don't have LinkedIn
- When LinkedIn exists, employee count is always listed
- Decision maker visibility varies (some pages hide employee list)

---

## Apify LinkedIn Scraper Options

### Option 1: `bebity/linkedin-premium-actor`
**Type:** Company + Profile scraper
**Cost:** $3-5 per 1,000 profiles
**Features:**
- Company page scraping
- Employee list extraction
- Profile detail scraping (name, title, experience)
- Email finder (claims to find emails, but risky)

**Pros:**
- Comprehensive data
- Can scrape both company and profiles

**Cons:**
- Higher cost
- Email scraping may violate LinkedIn TOS
- More aggressive = higher blocking risk

**Recommendation:** ❌ Too risky for initial implementation

### Option 2: `sanjeta/linkedin-company-profile-scraper`
**Type:** Company only
**Cost:** $1-2 per 1,000 companies
**Features:**
- Company description
- Employee count
- Follower count
- Industry, specialties
- Website link

**Pros:**
- Safer (public data only)
- Cheaper
- No profile scraping = lower TOS risk

**Cons:**
- No employee names/titles
- No decision maker identification

**Recommendation:** ✅ Good for Phase 1 (company data only)

### Option 3: `saswave/linkedin-profile` (Company + Profile)
**Type:** Combined scraper
**Cost:** $3 per 1,000 profiles
**Features:**
- Company page data
- Employee list (names + titles only)
- Profile URLs
- No email scraping

**Pros:**
- Mid-range cost
- Conservative approach (no emails)
- Can get decision maker names

**Cons:**
- Unknown reliability (fewer reviews than others)

**Recommendation:** ⚠️ Test in Phase 2 if Option 2 insufficient

### Option 4: `curious_coder/linkedin-profile-scraper`
**Type:** Profile scraper
**Cost:** Variable
**Features:**
- Individual profile scraping
- Job history, education, skills

**Pros:**
- Detailed profile data

**Cons:**
- Requires profile URLs (need company scraper first)
- More aggressive = higher risk
- Not needed for our use case

**Recommendation:** ❌ Not needed

---

## Recommended Approach

### Phase 1: Company Pages Only (`sanjeta/linkedin-company-profile-scraper`)

**What to scrape:**
1. Search LinkedIn for "[Practice Name] veterinary [City, State]"
2. Get company page URL
3. Scrape company data:
   - Employee count
   - Follower count
   - Description
   - Website (validate against Google Maps data)

**No profile scraping in Phase 1**
- Lower risk of blocks
- Still valuable for employee count validation
- Can add profiles in Phase 2 if needed

**Cost:**
- $1-2 per 1,000 companies
- Per practice: $0.001-0.002
- Success rate: 60% (based on manual search)
- Effective cost: $0.001/practice on average

### Phase 2: Add Employee List (If Needed)

If sales team finds company data insufficient, test `saswave/linkedin-profile`:
- Extract employee list from company page
- Filter for titles: Owner, Practice Manager, Hospital Director
- Store: name + title + profile URL (NO emails)

**Additional cost:**
- $3 per 1,000 profiles
- Per practice: $0.003
- Success rate: 45% (based on manual search)
- Effective cost: $0.0015/practice on average

---

## LinkedIn TOS Compliance

### What's Allowed (Public Data)
✅ Company page data (public)
✅ Employee count (public)
✅ Follower count (public)
✅ Employee names visible on company page (public)

### What's Risky
⚠️ Scraping individual profiles (may trigger blocks)
⚠️ Scraping at scale without rate limiting
⚠️ Using multiple accounts/cookies

### What's Prohibited
❌ Email scraping (violates TOS)
❌ Scraping private profiles
❌ Scraping via fake accounts
❌ Selling scraped data

### Our Approach (Conservative)
- Use Apify (they handle blocks/rate limiting)
- Company pages only in Phase 1
- No email scraping
- Conservative rate limiting: max 10 practices/hour
- Monitor for blocks during pilot

---

## Data Quality Validation

### Employee Count Validation

Compare LinkedIn employee count to Vet Count from website:

| Practice | Vet Count (Website) | LinkedIn Employee Count | Ratio | Valid? |
|----------|---------------------|-------------------------|-------|--------|
| South Boston AH | 3 vets | 11-50 employees | 3.7-16.7x | ✅ Reasonable |
| Cambridge Cat Clinic | 2 vets | 2-10 employees | 1-5x | ✅ Reasonable |
| Angell Medical Center | 50+ vets | 201-500 employees | 4-10x | ✅ Reasonable |

**Expected ratio:** 1 vet : 3-5 total employees (techs, receptionists, etc.)

**Validation logic:**
- If LinkedIn employees < Vet count: Flag as error
- If LinkedIn employees > Vet count × 10: Flag as error
- Otherwise: Use as supporting signal

---

## Decision Maker Title Patterns

From manual LinkedIn search, common titles for vet practice decision makers:

**Owner/Executive:**
- Owner
- Co-Owner
- Founder
- President
- Chief Executive Officer
- Medical Director

**Management:**
- Practice Manager
- Hospital Administrator
- Hospital Manager
- Office Manager (sometimes, but often not decision maker)

**Veterinarian Leadership:**
- Chief Veterinarian
- Lead Veterinarian
- Senior Veterinarian (sometimes)

**Filter logic:**
```python
decision_maker_titles = [
    "owner", "co-owner", "founder",
    "president", "ceo", "chief executive",
    "medical director", "chief veterinarian",
    "practice manager", "hospital administrator", "hospital manager"
]

def is_decision_maker(title: str) -> bool:
    title_lower = title.lower()
    return any(dm_title in title_lower for dm_title in decision_maker_titles)
```

---

## Testing Plan

### Phase 1: Manual Validation (Before Apify)
1. ✅ Manually search LinkedIn for 20 Boston practices (DONE)
2. Document success rate finding company pages (60%)
3. Document decision maker visibility (45%)
4. Validate employee count ranges match expectations

### Phase 2: Apify Testing
1. Test `sanjeta/linkedin-company-profile-scraper` on 10 practices
2. Measure:
   - Success rate finding company pages
   - Data quality (employee count, follower count)
   - Cost per practice
   - Blocking incidents (should be 0)
3. Compare Apify results to manual search results

### Phase 3: Pilot
1. Integrate into enrichment pipeline
2. Run on 50 practices
3. Monitor for blocks (pause if any blocks detected)
4. Validate data quality vs manual checks
5. Decision: roll out or defer

---

## Cost-Benefit Analysis

### Costs
- **Development time:** 1-2 days
- **Apify cost:** $0.001/practice (company pages only)
- **Opportunity cost:** Could work on FEAT-004 or FEAT-005 instead

### Benefits
- **Employee count validation:** Confirms vet count accuracy
- **Decision maker names:** 45% success rate finding names
- **LinkedIn profile URL:** Enables LinkedIn outreach
- **Social proof:** Follower count indicates brand strength

### ROI Calculation
- **Cost:** $0.001 × 150 practices = $0.15 one-time
- **Value:** If sales team closes 1 extra deal due to LinkedIn context = 100x ROI
- **Risk:** Low (conservative approach, low cost)

**Recommendation:** Proceed with Phase 1 (company pages only)

---

## Blocking Risk Assessment

### Risk Factors
- **Rate:** 10 practices/hour = very conservative
- **Method:** Apify (professional scraper with anti-block measures)
- **Scope:** Company pages only (public data)
- **Account:** Apify uses their own infrastructure

**Likelihood of blocks:** LOW (<5%)

**Mitigation:**
- Start with 10 practice test
- Monitor for any 429 errors or CAPTCHAs
- If blocked: pause, reduce rate, or abort

---

## Alternative: Manual Enrichment

If Apify LinkedIn scraping proves too risky or blocked:

**Plan B: Manual LinkedIn lookups by sales team**
- Export practice list to CSV
- Sales team manually searches LinkedIn
- Adds company URLs to Notion manually
- Time: ~2 minutes per practice = 5 hours for 150 practices

**When to use Plan B:**
- If Apify gets blocked during pilot
- If success rate <30%
- If cost exceeds benefit

---

## Open Questions

1. **Does Apify LinkedIn scraper work without personal LinkedIn account?**
   - Answer: TBD - test with Apify actor
   - Impact: May require LinkedIn login credentials

2. **How often does LinkedIn data go stale?**
   - Answer: Employee counts update slowly (quarterly?)
   - Impact: Re-scrape quarterly or when employee count seems off

3. **Can we search LinkedIn by practice name + location programmatically?**
   - Answer: TBD - Apify may have search functionality
   - Impact: Affects accuracy of company page matching

---

## Recommendations

1. **Start with Phase 1** (company pages only via `sanjeta/linkedin-company-profile-scraper`)
2. **Test on 10 practices first** before full rollout
3. **Monitor for blocks closely** - abort if any blocking detected
4. **Don't scrape profiles initially** - too risky, lower value
5. **Compare LinkedIn employee count to vet count** - flag large discrepancies
6. **Add employee list (Phase 2) only if sales team requests it**

---

## Implementation Checklist

Before implementing FEAT-007:

- [ ] Test `sanjeta/linkedin-company-profile-scraper` on 10 practices
- [ ] Validate data format matches research
- [ ] Measure actual success rate vs manual (expect 50-70%)
- [ ] Confirm no blocking incidents
- [ ] Build LinkedIn search logic (practice name + city matching)
- [ ] Create Notion fields for LinkedIn data
- [ ] Add employee count validation logic

---

## References

- Apify LinkedIn scrapers: https://apify.com/store?search=linkedin
- LinkedIn Company Profile Scraper: https://apify.com/sanjeta/linkedin-company-profile-scraper
- LinkedIn TOS: https://www.linkedin.com/legal/user-agreement
- Manual search results: This document, table above
