# FEAT-006: Improve LLM Website Extraction

**Status:** Planned - Medium Priority (after FEAT-004, FEAT-005)
**Created:** 2025-11-05
**Owner:** Engineering Team
**Dependencies:** FEAT-004 (Fix Scraping Reliability)
**Cost Impact:** $0 (same LLM call, better prompt)

---

## Problem Statement

Current website enrichment extracts minimal useful data despite successful scraping:
- Test results show: **"Vet Count: None, Decision Maker: None"** even on successful scrapes
- LLM returns mostly empty/null values
- Current prompt (`config/website_extraction_prompt.txt`) may be asking for data that **doesn't exist on most vet websites**

### Reality Check: What's Actually on Vet Websites?

Most veterinary practice websites are simple 5-10 page sites with:
- **Homepage:** General welcome, maybe 1-2 vet names
- **About:** Practice history, mission statement
- **Services:** List of services offered
- **Team:** Sometimes vet photos/bios (but rarely complete list with specialties)
- **Contact:** Address, phone, hours

**What's RARELY present:**
- ❌ Complete vet count ("We have 5 veterinarians")
- ❌ Decision maker email (info@ or contact forms only)
- ❌ Explicit technology mentions ("We use Covetrus practice management software")
- ❌ Recent news/updates (unless they have a blog)

**What's SOMETIMES present:**
- ⚠️ Founding year or "family-owned since 1985"
- ⚠️ Owner name in About section ("Founded by Dr. Sarah Johnson")
- ⚠️ Individual vet bios with specialties
- ⚠️ Awards/certifications (AAHA accredited, Fear Free certified)
- ⚠️ Operating hours

---

## Goals

### Primary Goal
**Extract realistic, actionable personalization context** from 60-80% of practice websites (up from current ~10%).

### Secondary Goals
1. Focus on **qualitative context** over quantitative metrics
2. Lower expectations for data that's rarely present (vet count, decision maker email)
3. Emphasize **what makes this practice unique** for sales personalization
4. Extract **observable signals** (what's visible on the page) vs. inferred data

---

## Proposed Solution

### 1. Website Audit (Pre-Implementation)

**Action:** Manually audit 20 Boston vet practice websites to understand:
- What information is consistently present?
- What's the format/location of useful data?
- What patterns exist across sites?

**Deliverable:** `research.md` with findings:
- Common page structures
- Data availability percentages
- Examples of good vs poor content
- Recommendations for prompt focus areas

**Acceptance Criteria:**
- AC-FEAT-006-001: Audit 20 Boston vet websites
- AC-FEAT-006-002: Document data availability percentages
- AC-FEAT-006-003: Identify 5+ common content patterns

### 2. Revised Extraction Prompt

**New Focus Areas:**

**A. Practice Story & History (High Success Rate)**
```
Extract if present:
- Founded year: "Established in 1985"
- Family-owned mentions: "Family-owned for 3 generations"
- Founding story: "Dr. Sarah Johnson opened the practice..."
- Mission statement: Practice philosophy or values
```

**B. Observable Veterinarian Signals (Medium Success Rate)**
```
Extract if present:
- Named veterinarians: List all vet names mentioned (even if not complete)
- Vet specialties: "Dr. Johnson specializes in surgery"
- Vet tenure: "Dr. Smith has been with us for 15 years"
- Leadership mentions: "Dr. Sarah Johnson, Owner and Chief Veterinarian"
```

**C. Unique Selling Points (High Success Rate)**
```
Extract specific, unique facts:
- Awards: "AAHA Accredited", "Fear Free Certified", "Best of Boston 2024"
- Specializations: "Only practice in Boston with exotic bird specialist"
- Recent expansions: "Opened 2nd location in Newton in 2024"
- Community involvement: "Sponsors Boston Animal Rescue League"
- Unique services: "Mobile vet services", "House calls", "Farm animal care"
```

**D. Facility & Technology Signals (Medium Success Rate)**
```
Extract if VISIBLY present:
- Operating hours: From footer or contact page
- Technology features: Online booking button, patient portal link visible
- Facility mentions: "State-of-art surgical suite", "Digital x-ray"
- Accreditations: AAHA, Fear Free, VECCS logos
```

**E. Staff Beyond Vets (Low Success Rate - Optional)**
```
Extract if mentioned:
- "Our team of 20+ caring professionals"
- "3 licensed vet techs", "5 support staff"
- Vet tech names/bios if listed
```

**New Prompt Structure:**
```json
{
  "practice_story": {
    "founded_year": 1985 or null,
    "founding_narrative": "Dr. Sarah Johnson opened the practice in 1985...",
    "family_owned": true/false,
    "mission_statement": "..."
  },

  "veterinarians": {
    "named_vets": [
      {"name": "Dr. Sarah Johnson", "role": "Owner", "specialties": ["Surgery", "Internal Medicine"]}
    ],
    "estimated_count": 3 or null,
    "count_confidence": "high|medium|low|none"
  },

  "unique_selling_points": [
    "Only practice in Greater Boston specializing in exotic birds",
    "AAHA accredited since 1995",
    "Opened 2nd location in Newton in March 2024"
  ],

  "facility_tech": {
    "operating_hours": "Mon-Fri 8am-7pm, Sat 9am-5pm",
    "online_booking_visible": true,
    "patient_portal_visible": false,
    "facility_highlights": ["Digital x-ray", "In-house laboratory"]
  },

  "staff_beyond_vets": {
    "total_staff_mentioned": 20 or null,
    "vet_techs_count": 3 or null,
    "notable_staff": []
  },

  "personalization_score": 7,  // 0-10: How much unique, actionable context was found?
  "extraction_notes": "Strong practice history and unique bird specialization. No decision maker email found."
}
```

**Acceptance Criteria:**
- AC-FEAT-006-004: New prompt emphasizes qualitative over quantitative data
- AC-FEAT-006-005: Prompt includes 5+ example outputs (good vs bad)
- AC-FEAT-006-006: Prompt focuses on "observable" vs "inferred" data
- AC-FEAT-006-007: Personalization score guides sales team priority

### 3. Update Pydantic Models

**`src/models/enrichment_models.py`:**
```python
class PracticeStory(BaseModel):
    """Practice history and narrative."""
    founded_year: Optional[int] = None
    founding_narrative: Optional[str] = Field(None, max_length=500)
    family_owned: bool = False
    mission_statement: Optional[str] = Field(None, max_length=500)

class VetPracticeExtraction(BaseModel):
    # ... existing fields ...

    # New fields:
    practice_story: Optional[PracticeStory] = None
    unique_selling_points: List[str] = Field(default_factory=list, max_length=5)
    operating_hours: Optional[str] = None
    total_staff_count: Optional[int] = None
    vet_tech_count: Optional[int] = None
    personalization_score: int = Field(0, ge=0, le=10)
    extraction_notes: Optional[str] = None
```

**Acceptance Criteria:**
- AC-FEAT-006-008: Models updated to support new fields
- AC-FEAT-006-009: Backward compatible with existing enrichment data

### 4. Notion Field Mapping

**New Notion Fields:**
- **Founded Year** (number): Practice founding year
- **Practice Story** (rich_text): Founding narrative + mission statement
- **Unique Selling Points** (multi_select): 3-5 unique facts
- **Operating Hours** (rich_text): Business hours
- **Total Staff Count** (number): Total employees if mentioned
- **Personalization Score** (select: 0-3 Low, 4-6 Medium, 7-10 High): Quality of personalization context

**Acceptance Criteria:**
- AC-FEAT-006-010: New Notion fields added to schema
- AC-FEAT-006-011: Fields populated during enrichment
- AC-FEAT-006-012: Personalization score visible for sales prioritization

---

## Technical Approach

### File Changes

**`config/website_extraction_prompt.txt`:**
- Complete rewrite based on audit findings
- Focus on observable, qualitative data
- Include 5 examples of good outputs
- Emphasize "unique and specific" over "generic"

**`src/models/enrichment_models.py`:**
- Add `PracticeStory` model
- Add new fields to `VetPracticeExtraction`
- Add `personalization_score` calculation

**`src/enrichment/llm_extractor.py`:**
- No changes needed (uses same OpenAI call)

**`src/integrations/notion_enrichment.py`:**
- Map new fields to Notion
- Handle null values gracefully

---

## Testing Strategy

### Manual Audit (Pre-Implementation)
1. Visit 20 Boston vet websites
2. Manually extract data into spreadsheet
3. Calculate % availability for each field type
4. Identify patterns and common structures

### Prompt Testing
1. Test new prompt on 10 practice websites (with real scraped content)
2. Manually review LLM outputs for quality
3. Calculate personalization score distribution
4. Iterate prompt based on results

### Integration Testing
1. Run enrichment on 50 practices with new prompt
2. Compare extraction success rate: old vs new
3. Measure personalization score distribution
4. Validate Notion fields populated correctly

**Success Criteria:**
- Extraction success rate >60% (up from ~10%)
- Personalization score >4 for 60% of practices
- Sales team reports improved context quality

---

## Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Practices with useful data | ~10% | >60% | Has at least 1 unique selling point |
| Personalization score >4 | Unknown | >60% | Medium/High quality context |
| Decision maker found | <5% | 20-30% | Name extracted from About page |
| Operating hours extracted | 0% | >70% | Hours visible on website |
| Founded year found | 0% | >40% | Year mentioned on site |

---

## Cost Analysis

**Development Time:** 1-2 days
**Runtime Cost:** $0 (same LLM call, improved prompt)
**Performance Impact:** None (same API call)

---

## Risks & Mitigations

### Risk 1: Websites still don't have expected data
**Likelihood:** Medium
**Impact:** Medium (extraction improves but still limited)
**Mitigation:**
- Lower expectations and communicate realistic success rates
- Focus on practices with better websites (filter by website quality)

### Risk 2: LLM hallucinates "unique" facts
**Likelihood:** Low (GPT-4o-mini is accurate with structured outputs)
**Impact:** High (misinformation in sales outreach)
**Mitigation:**
- Prompt emphasizes "ONLY extract EXPLICITLY STATED facts"
- Add validation: flag suspiciously specific claims
- Manual review of 20 outputs before full rollout

### Risk 3: Personalization score is subjective
**Likelihood:** High
**Impact:** Low (sales team can override)
**Mitigation:**
- Define clear scoring rubric in prompt
- Test score distribution on 50 practices
- Allow sales team to manually adjust scores

---

## Dependencies

**Depends On:**
- FEAT-004 (Fix Scraping) - Need reliable content before improving extraction

**Blocks:**
- None

**Related:**
- FEAT-005 (Reviews) - Both use LLM extraction, can share learnings

---

## Implementation Phases

### Phase 1: Manual Audit (Day 1)
- Visit and audit 20 Boston vet websites
- Document findings in `research.md`
- Identify data availability patterns

### Phase 2: Prompt Rewrite (Day 1)
- Draft new prompt based on audit
- Test on 10 websites
- Iterate based on output quality

### Phase 3: Model & Integration (Day 2)
- Update Pydantic models
- Add Notion fields
- Update notion_enrichment.py

### Phase 4: Validation (Day 2)
- Run on 50 practices
- Measure success metrics
- Full rollout if >60% success rate

---

## Acceptance Criteria Summary

- AC-FEAT-006-001: Audit 20 Boston vet websites
- AC-FEAT-006-002: Document data availability percentages
- AC-FEAT-006-003: Identify 5+ common patterns
- AC-FEAT-006-004: New prompt emphasizes qualitative data
- AC-FEAT-006-005: Prompt includes 5+ examples
- AC-FEAT-006-006: Prompt focuses on observable data
- AC-FEAT-006-007: Personalization score added
- AC-FEAT-006-008: Models support new fields
- AC-FEAT-006-009: Backward compatible
- AC-FEAT-006-010: New Notion fields added
- AC-FEAT-006-011: Fields populated during enrichment
- AC-FEAT-006-012: Personalization score visible
- **AC-FEAT-006-013: Extraction success rate >60% on 50+ practices**

---

## Future Enhancements (Phase 2)

- **Website quality scoring:** Flag practices with poor/outdated websites
- **Multi-model extraction:** Test Claude vs GPT for extraction accuracy
- **Image analysis:** Extract info from team photos, facility images
- **Structured data extraction:** Parse schema.org markup if present

---

## References

- Current extraction prompt: `config/website_extraction_prompt.txt`
- Current LLM extractor: `src/enrichment/llm_extractor.py`
- Manual audit findings: `docs/features/FEAT-006_improve-llm-extraction/research.md` (to be created)
