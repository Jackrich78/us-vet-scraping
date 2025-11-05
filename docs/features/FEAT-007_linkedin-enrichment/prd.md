# FEAT-007: LinkedIn Decision Maker Discovery

**Status:** Planned - Lower Priority (after FEAT-004, FEAT-005, FEAT-006)
**Created:** 2025-11-05
**Owner:** Engineering Team
**Dependencies:** FEAT-004 (Fix Scraping Reliability)
**Cost Impact:** +$0.003-0.01/lead (depending on scraper choice)

---

## Problem Statement

Current website enrichment rarely finds decision maker email addresses because:
- Most vet websites only list generic emails (info@, contact@)
- Owner/manager names are mentioned but without direct contact info
- Sales teams need a way to reach decision makers directly

### LinkedIn as a Data Source

LinkedIn provides:
- **Company pages:** Business information, employee count, follower count
- **Employee profiles:** Names, titles, current/past roles
- **Decision maker identification:** Filter by title (Owner, Practice Manager, Hospital Director)
- **Professional context:** Years of experience, education, other companies

**However, LinkedIn is risky:**
- ❌ Aggressive anti-scraping measures
- ❌ Rate limiting and IP bans
- ❌ Requires maintaining valid session tokens/cookies
- ❌ Profile-level scraping may violate LinkedIn TOS

---

## Goals

### Primary Goal
**Identify practice owner/manager name and LinkedIn profile URL** for 40-60% of Boston veterinary practices.

### Secondary Goals
1. Validate practice size via LinkedIn employee count
2. Find LinkedIn company page for social proof
3. Identify 2-3 key decision makers per practice (not just owner)
4. Maintain conservative approach to avoid LinkedIn bans

---

## Proposed Solution

### Approach: Conservative LinkedIn Company Scraping Only

**Strategy:** Use Apify LinkedIn scrapers (safer than building custom) for COMPANY PAGES only, not individual profiles initially.

**Rationale:**
- Company pages are public and less risky to scrape
- Apify handles anti-bot measures, proxy rotation, rate limiting
- Can validate employee count without scraping individual profiles
- If needed, can add profile scraping in Phase 2

### 1. LinkedIn Company Page Discovery

**Step 1: Find Company Page URL**
- Search LinkedIn for "[Practice Name] veterinary [City, State]"
- Extract company page URL (e.g., `linkedin.com/company/example-vet-clinic`)

**Step 2: Scrape Company Page Data**
- Company description
- Employee count (from LinkedIn, not self-reported)
- Follower count
- Industry, specialties
- Website link (validate against Google Maps data)

**Apify Actor Options (to be researched):**

| Actor | Type | Cost/1K | Pros | Cons |
|-------|------|---------|------|------|
| `bebity/linkedin-premium-actor` | Company + Profile | $3-5 | Comprehensive | Higher cost, profile risk |
| `sanjeta/linkedin-company-profile-scraper` | Company only | $1-2 | Safer, cheaper | No profiles |
| `saswave/linkedin-profile` | Company + Profile | $3 | Mid-range | Unknown reliability |

**Recommendation:** Start with company-only scraper, add profiles in Phase 2 if needed.

**Acceptance Criteria:**
- AC-FEAT-007-001: Research 3+ Apify LinkedIn scrapers
- AC-FEAT-007-002: Select safest, most cost-effective option
- AC-FEAT-007-003: Test scraper on 10 Boston practices
- AC-FEAT-007-004: Measure success rate (expect 40-70%)

### 2. Decision Maker Identification (Phase 2 - Optional)

**If company-only scraping works well, consider adding:**
- Scrape employee list from company page
- Filter for titles: "Owner", "Practice Manager", "Hospital Director", "Medical Director"
- Extract names and profile URLs (NOT emails - too risky)

**Conservative approach:**
- No email scraping (violates LinkedIn TOS)
- No profile detail scraping (job history, education)
- Just name + title + profile URL

**Acceptance Criteria:**
- AC-FEAT-007-005: Extract employee list from company page
- AC-FEAT-007-006: Filter for decision maker titles
- AC-FEAT-007-007: Store name + profile URL only (no emails)

### 3. Notion Integration

**New Notion Fields:**
- **LinkedIn Company URL** (url): Link to company page
- **LinkedIn Employee Count** (number): Employee count from LinkedIn (validates vet count)
- **LinkedIn Follower Count** (number): Social media presence signal
- **LinkedIn Decision Makers** (rich_text): List of names + titles found
  - Format: "Dr. Sarah Johnson (Owner), Jennifer Smith (Practice Manager)"
- **LinkedIn Enrichment Status** (select): Found/Not Found/Failed

**Acceptance Criteria:**
- AC-FEAT-007-008: New Notion fields added
- AC-FEAT-007-009: LinkedIn data populated during enrichment
- AC-FEAT-007-010: Employee count compared to vet count for validation

---

## Technical Approach

### File Changes

**`src/integrations/apify_linkedin.py` (new file):**
```python
class ApifyLinkedInClient:
    """Apify LinkedIn scraper client."""

    async def find_company_page(
        self,
        practice_name: str,
        city: str,
        state: str
    ) -> Optional[str]:
        """Search for LinkedIn company page URL."""

    async def scrape_company_data(
        self,
        company_url: str
    ) -> Optional[LinkedInCompanyData]:
        """Scrape company page data via Apify."""
```

**`src/models/enrichment_models.py`:**
```python
class LinkedInCompanyData(BaseModel):
    """LinkedIn company page data."""
    company_url: str
    employee_count: Optional[int] = None
    follower_count: Optional[int] = None
    description: Optional[str] = None
    decision_makers: List[Dict[str, str]] = Field(default_factory=list)
        # [{"name": "Dr. Sarah Johnson", "title": "Owner", "profile_url": "..."}]

class VetPracticeExtraction(BaseModel):
    # ... existing fields ...
    linkedin_data: Optional[LinkedInCompanyData] = None
```

**`src/enrichment/enrichment_orchestrator.py`:**
- Add LinkedIn enrichment step (optional, can be skipped if company page not found)
- Retry logic for LinkedIn failures (conservative: fail fast if blocked)

---

## Cost Analysis

### Company Page Scraping Only
- **Apify cost:** $1-2 per 1,000 company pages
- **Per practice:** $0.001-0.002
- **Success rate:** Assume 50% (not all practices have LinkedIn)
- **Effective cost:** $0.001/practice on average

### With Employee List (Phase 2)
- **Apify cost:** $3-5 per 1,000 profiles
- **Per practice:** $0.003-0.005
- **Success rate:** Assume 40% have findable decision makers
- **Effective cost:** $0.002-0.003/practice on average

### Budget Impact
- **Current:** $0.03/lead
- **After FEAT-007:** $0.031-0.033/lead
- **Remaining budget:** $0.067-0.069/lead

---

## Testing Strategy

### Research Phase
1. Manually search LinkedIn for 20 Boston vet practices
2. Document success rate finding company pages
3. Document typical employee counts, decision maker titles
4. Validate Apify scraper options with test runs

### Apify Actor Testing
1. Test 3 Apify scrapers on 10 practices each
2. Compare cost, success rate, data quality
3. Select best option

### Integration Testing
1. Integrate selected scraper into enrichment pipeline
2. Test on 50 practices
3. Measure success rate, cost, blocking incidents
4. Validate data quality (employee count matches vet count?)

**Success Criteria:**
- 40-60% of practices have findable LinkedIn company pages
- No IP bans or rate limiting issues
- Employee count correlation with vet count >70%

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Company page found | 40-60% | LinkedIn Company URL populated |
| Employee count validation | >70% | LinkedIn count ± 30% of vet count |
| Decision makers found | 20-40% | At least 1 name + title extracted |
| Scraping failures | <5% | API errors, blocks, timeouts |

---

## Risks & Mitigations

### Risk 1: LinkedIn blocks Apify scrapers
**Likelihood:** Medium
**Impact:** High (feature unusable)
**Mitigation:**
- Use Apify (handles blocks better than custom scraping)
- Start with company pages only (lower risk)
- Conservative rate limiting (max 10 practices/hour)
- Monitor for blocks during pilot

### Risk 2: Many practices don't have LinkedIn pages
**Likelihood:** High (small practices may not have LinkedIn)
**Impact:** Medium (lower success rate)
**Mitigation:**
- Accept 40-60% success rate as baseline
- Don't penalize practices without LinkedIn in scoring
- Mark as "Not Found" vs "Failed" in Notion

### Risk 3: Employee count doesn't match reality
**Likelihood:** Medium (LinkedIn data may be stale)
**Impact:** Low (just validation data, not primary source)
**Mitigation:**
- Use as validation signal only, not ground truth
- Flag large discrepancies for manual review

### Risk 4: Decision maker names are inaccurate
**Likelihood:** Medium (people change jobs, titles update slowly)
**Impact:** Medium (sales team reaches wrong person)
**Mitigation:**
- Add "LinkedIn Last Updated" timestamp
- Sales team verifies before outreach
- Re-scrape LinkedIn quarterly

---

## Dependencies

**Depends On:**
- FEAT-004 (Fix Scraping) - Need reliable pipeline before adding LinkedIn

**Blocks:**
- None

**Related:**
- FEAT-006 (Better LLM Extraction) - May extract decision makers from websites too

---

## Implementation Phases

### Phase 1: Research (Day 1)
- Manual LinkedIn search for 20 practices
- Research Apify scraper options
- Cost/benefit analysis
- Document findings in `research.md`

### Phase 2: Apify Testing (Day 1-2)
- Test 3 scrapers on 10 practices each
- Measure success rate, cost, quality
- Select best scraper

### Phase 3: Integration (Day 2)
- Build `apify_linkedin.py` client
- Integrate into enrichment orchestrator
- Add Notion fields

### Phase 4: Pilot (Day 3)
- Run on 50 practices
- Monitor for blocks
- Measure success metrics
- Decision: roll out or defer to Phase 2

---

## Decision Points

**After Research Phase:**
- ❓ Is success rate >40%? (If no, defer feature)
- ❓ Is cost <$0.005/practice? (If no, evaluate ROI)

**After Pilot:**
- ❓ Did we get blocked? (If yes, abort or reduce rate)
- ❓ Is data quality acceptable? (If no, improve or defer)
- ❓ Do sales team find it useful? (If no, don't scale)

---

## Acceptance Criteria Summary

- AC-FEAT-007-001: Research 3+ Apify scrapers
- AC-FEAT-007-002: Select safest option
- AC-FEAT-007-003: Test on 10 practices
- AC-FEAT-007-004: Measure success rate (40-70%)
- AC-FEAT-007-005: Extract employee list
- AC-FEAT-007-006: Filter decision maker titles
- AC-FEAT-007-007: Store name + profile URL only
- AC-FEAT-007-008: New Notion fields added
- AC-FEAT-007-009: LinkedIn data populated
- AC-FEAT-007-010: Employee count compared
- **AC-FEAT-007-011: 40-60% success rate on 50+ practices**
- **AC-FEAT-007-012: No blocking incidents during pilot**

---

## Future Enhancements (Phase 2)

- **Profile detail scraping:** Education, years of experience (if safe)
- **Connection suggestions:** "You have 5 mutual connections with Dr. Johnson"
- **Engagement scoring:** Follower count, post frequency, engagement rate
- **Alumni lookup:** Find decision makers who went to same school as sales rep

---

## References

- Apify LinkedIn scrapers: https://apify.com/store?search=linkedin
- LinkedIn scraper comparison: `docs/features/FEAT-007_linkedin-enrichment/research.md` (to be created)
- LinkedIn TOS: https://www.linkedin.com/legal/user-agreement
