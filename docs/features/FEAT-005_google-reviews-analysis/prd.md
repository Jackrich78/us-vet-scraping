# FEAT-005: Google Reviews Sentiment Analysis

**Status:** Planned - High Priority (after FEAT-004)
**Created:** 2025-11-05
**Owner:** Engineering Team
**Dependencies:** FEAT-004 (Fix Scraping Reliability)
**Cost Impact:** +$0.01/lead (LLM analysis only, review data is free)

---

## Problem Statement

Current enrichment focuses on extracting structured data from practice websites (vet count, services, decision makers), but **ignores rich qualitative insights from Google reviews** that we're already scraping.

### What We're Missing

Google reviews contain valuable personalization insights:
- **Patient pain points:** "Hard to get appointments", "Long wait times", "Expensive"
- **Unique strengths:** "Dr. Sarah is amazing with nervous cats", "Best emergency care in Boston"
- **Service quality signals:** "Always compassionate", "Explains everything clearly"
- **Decision maker mentions:** "The owner, Dr. Johnson, personally called to follow up"

### Current State

- We scrape Google Maps data via Apify (`compass/crawler-google-places`)
- `includeReviews` is hardcoded to `False` in `src/scrapers/apify_client.py:96`
- Review data is **available for free** (same API call), but we're not using it
- No review analysis, sentiment extraction, or theme identification

### Impact

- **Sales personalization:** Reps have no patient-voice context for cold calls
- **Lead qualification:** Can't identify practices with service issues or strengths
- **Competitive intel:** Missing what patients love/hate about each practice

---

## Goals

### Primary Goal
**Extract 2-3 actionable personalization insights from Google reviews** for each practice to enable more relevant cold outreach.

### Secondary Goals
1. Summarize common themes across 50+ reviews per practice
2. Identify unique mentions (decision makers, specialties, recent changes)
3. Flag potential red flags (negative sentiment patterns)
4. Store structured review data in Notion for sales team visibility

---

## Proposed Solution

### 1. Enable Review Scraping in Apify

**Change:** `src/scrapers/apify_client.py`
```python
# Before:
"includeReviews": False,  # Don't need full review text

# After:
"maxReviews": 50,  # Get last 50 reviews for analysis
```

**Rationale:**
- 50 reviews provides enough signal without overwhelming the LLM
- Apify returns review text, rating, date, reviewer name
- No additional API cost (already included in Google Maps scrape)

**Acceptance Criteria:**
- AC-FEAT-005-001: Apify actor configured with `maxReviews: 50`
- AC-FEAT-005-002: Review data stored in `ApifyGoogleMapsResult` model
- AC-FEAT-005-003: Reviews saved to `data/raw/` for debugging

### 2. LLM Review Summarization

**Approach:** Use GPT-4o-mini to analyze 50 reviews and extract insights

**Prompt Strategy:**
```
You are analyzing Google reviews for a veterinary practice to extract personalization
insights for B2B sales outreach.

Reviews (50 most recent):
[Review 1: ★★★★★ "Dr. Sarah is amazing with anxious cats..." - Posted 2 days ago]
[Review 2: ★★★★☆ "Great service but expensive..." - Posted 1 week ago]
...

Extract the following in JSON format:
{
  "summary": "2-3 sentence summary of overall sentiment and key themes",
  "themes": ["Compassionate Care", "Short Wait Times", "Expensive", "Emergency Excellence"],
  "unique_mentions": [
    "Dr. Sarah Johnson frequently praised for handling anxious pets",
    "Only practice in area with exotic bird specialist",
    "Recently renovated surgical suite (mentioned in 5 reviews)"
  ],
  "decision_maker_mentions": [
    {"name": "Dr. Sarah Johnson", "context": "Owner, personally handles difficult cases"}
  ],
  "red_flags": ["Multiple reviews mention high prices", "2 recent reviews about long wait times"]
}

Guidelines:
- Focus on SPECIFIC, ACTIONABLE insights (not generic praise)
- Identify patterns across multiple reviews (not one-offs)
- Extract decision maker names if mentioned
- Note any recent changes (new location, new vets, renovations)
- Flag concerning patterns (not isolated complaints)
```

**Cost Estimate:**
- 50 reviews × 200 words/review = 10,000 words
- ~13,000 tokens input + ~500 tokens output = ~13,500 total tokens
- GPT-4o-mini: $0.015 per 1M input tokens, $0.06 per 1M output tokens
- Cost per practice: ~$0.0002 input + $0.00003 output = **$0.00023/practice**
- **Rounded up to $0.001/practice for safety margin**

**Acceptance Criteria:**
- AC-FEAT-005-004: LLM summarizes 50 reviews into structured JSON
- AC-FEAT-005-005: Extracts 2-5 themes per practice
- AC-FEAT-005-006: Identifies 1-3 unique mentions per practice
- AC-FEAT-005-007: Flags decision maker mentions if present
- AC-FEAT-005-008: Flags red flags if patterns detected

### 3. Notion Database Integration

**New Fields:**
- **Google Review Summary** (rich_text): 2-3 sentence summary of review sentiment
- **Google Review Themes** (multi_select): ["Compassionate Care", "Short Wait Times", "Expensive", "Emergency Excellence", "Exotic Pets", "Fear-Free", "Family-Owned"]
- **Google Review Sample Size** (number): How many reviews were analyzed (0-50)
- **Google Review Decision Makers** (rich_text): Any decision maker mentions from reviews
- **Google Review Red Flags** (multi_select): ["High Prices", "Long Waits", "Poor Communication", "Staff Turnover"]

**Acceptance Criteria:**
- AC-FEAT-005-009: New Notion fields created in database schema
- AC-FEAT-005-010: Review insights written to Notion during enrichment
- AC-FEAT-005-011: Fields preserved during scoring updates (partial update)

### 4. Sales Workflow Integration

**Use Cases:**
1. **Cold Call Prep:** "I noticed patients rave about Dr. Sarah's expertise with anxious cats..."
2. **Red Flag Awareness:** "Multiple reviews mention pricing concerns - may need to address value prop"
3. **Unique Selling Points:** "Patients specifically highlight your exotic bird specialist"
4. **Decision Maker ID:** "Reviews mention Dr. Johnson as the owner - confirms our research"

**Acceptance Criteria:**
- AC-FEAT-005-012: Review summary visible in Notion database view
- AC-FEAT-005-013: Themes filterable for targeted outreach (e.g., find all "Emergency Excellence" practices)

---

## Technical Approach

### File Changes

**`src/models/apify_models.py`:**
```python
class GoogleReview(BaseModel):
    """Single Google review from Apify."""
    text: str
    rating: int  # 1-5 stars
    published_at: str  # ISO date
    reviewer_name: Optional[str] = None

class ApifyGoogleMapsResult(BaseModel):
    # ... existing fields ...
    reviews: List[GoogleReview] = Field(default_factory=list)
```

**`src/models/enrichment_models.py`:**
```python
class ReviewInsights(BaseModel):
    """LLM-extracted insights from Google reviews."""
    summary: str = Field(max_length=500)
    themes: List[str] = Field(max_length=10)
    unique_mentions: List[str] = Field(max_length=5)
    decision_maker_mentions: List[Dict[str, str]] = Field(default_factory=list)
    red_flags: List[str] = Field(default_factory=list)

class VetPracticeExtraction(BaseModel):
    # ... existing fields ...
    review_insights: Optional[ReviewInsights] = None
    review_sample_size: int = 0
```

**New file: `src/enrichment/review_analyzer.py`:**
```python
class ReviewAnalyzer:
    """Analyze Google reviews with LLM."""

    async def analyze_reviews(
        self,
        practice_name: str,
        reviews: List[GoogleReview]
    ) -> Optional[ReviewInsights]:
        """Extract insights from reviews using GPT-4o-mini."""
```

**`src/enrichment/enrichment_orchestrator.py`:**
- Add review analysis step after website scraping
- Pass reviews to ReviewAnalyzer
- Merge review insights into VetPracticeExtraction

**`src/integrations/notion_enrichment.py`:**
- Map `review_insights` to new Notion fields
- Handle empty reviews gracefully (practices with <10 reviews)

**`config/review_analysis_prompt.txt`:**
- Store LLM prompt for review analysis (separate from website extraction)

---

## Data Flow

```
1. Apify Google Maps Scrape
   ↓
2. Extract reviews (up to 50 per practice)
   ↓
3. ReviewAnalyzer: LLM summarization
   ↓
4. Merge with website enrichment data
   ↓
5. Write to Notion (Google Review Summary, Themes, etc.)
   ↓
6. Sales team uses insights for outreach
```

---

## Testing Strategy

### Unit Tests
- `tests/unit/test_review_analyzer.py`:
  - Test review summarization with mock LLM responses
  - Test theme extraction
  - Test decision maker mention parsing
  - Test red flag detection

### Integration Tests
- `tests/integration/test_review_enrichment.py`:
  - Test full pipeline: Apify → Review Analysis → Notion
  - Use test fixtures with sample reviews
  - Validate Notion fields updated correctly

### Manual Testing
1. Run enrichment on 10 practices with reviews
2. Manually review LLM outputs for quality
3. Check Notion fields populated correctly
4. Validate themes are actionable (not generic)

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Practices with reviews | >80% | Have at least 10 reviews |
| Themes extracted | 2-5 per practice | Average themes per practice |
| Unique mentions | 1-3 per practice | Actionable personalization facts |
| Decision makers found | 10-20% | Practices with DM mentions in reviews |
| Red flags detected | 5-10% | Practices with concerning patterns |

---

## Cost Analysis

### Per Practice
- **Apify review scraping:** $0 (included in existing Google Maps scrape)
- **LLM analysis:** ~$0.001 (GPT-4o-mini for 50 reviews)
- **Total added cost:** **$0.001/practice**

### Full Dataset (150 practices)
- **Total added cost:** $0.15 (one-time for initial enrichment)
- **Ongoing cost:** $0.001/practice for re-enrichment

### Budget Impact
- **Current:** $0.03/lead
- **After FEAT-005:** $0.031/lead
- **Remaining budget:** $0.069/lead (69% of $0.10 budget remaining)

---

## Risks & Mitigations

### Risk 1: Many practices have <10 reviews
**Likelihood:** Medium (small practices may have few reviews)
**Impact:** Low (gracefully handle empty reviews)
**Mitigation:**
- Skip review analysis if <10 reviews
- Mark field as "Insufficient Data" in Notion

### Risk 2: LLM extracts generic themes (not actionable)
**Likelihood:** Medium (depends on prompt quality)
**Impact:** Medium (wastes sales team time)
**Mitigation:**
- Iterate on prompt with manual review of 20 outputs
- Emphasize "SPECIFIC, ACTIONABLE" in prompt
- Add examples of good vs bad insights

### Risk 3: Reviews are outdated (5+ years old)
**Likelihood:** Low (Apify returns recent reviews first)
**Impact:** Low (insights may be stale)
**Mitigation:**
- Filter reviews to last 2 years only
- Log average review age per practice

### Risk 4: Review content violates privacy (phone numbers, emails)
**Likelihood:** Very Low (Google filters PII from reviews)
**Impact:** Medium (data compliance issues)
**Mitigation:**
- Strip any detected emails/phone numbers before storing
- Don't store reviewer names in Notion (keep anonymous)

---

## Dependencies

**Depends On:**
- FEAT-004 (Fix Scraping) - Need reliable scraping before adding review analysis

**Blocks:**
- None - can be implemented independently

**Related:**
- FEAT-006 (Better LLM Prompts) - Similar LLM extraction approach

---

## Implementation Phases

### Phase 1: Enable Review Scraping (Day 1)
- Change `includeReviews` to `maxReviews: 50`
- Update `ApifyGoogleMapsResult` model to include reviews
- Test Apify scrape returns reviews

### Phase 2: LLM Review Analysis (Day 1-2)
- Create `review_analyzer.py`
- Write review analysis prompt
- Test with 10 practice review sets
- Iterate on prompt quality

### Phase 3: Notion Integration (Day 2)
- Add new Notion fields to schema
- Update `notion_enrichment.py` to map review insights
- Test full pipeline

### Phase 4: Validation (Day 2-3)
- Run on 50 practices
- Manually review 20 outputs for quality
- Adjust prompt based on findings
- Full rollout to 150+ practices

---

## Acceptance Criteria Summary

- AC-FEAT-005-001: Apify configured with `maxReviews: 50`
- AC-FEAT-005-002: Reviews stored in model
- AC-FEAT-005-003: Reviews saved to `data/raw/`
- AC-FEAT-005-004: LLM summarizes reviews to JSON
- AC-FEAT-005-005: 2-5 themes extracted per practice
- AC-FEAT-005-006: 1-3 unique mentions per practice
- AC-FEAT-005-007: Decision makers flagged if mentioned
- AC-FEAT-005-008: Red flags detected for patterns
- AC-FEAT-005-009: New Notion fields created
- AC-FEAT-005-010: Review insights written to Notion
- AC-FEAT-005-011: Fields preserved during updates
- AC-FEAT-005-012: Review summary visible in Notion
- AC-FEAT-005-013: Themes filterable in Notion

---

## Future Enhancements (Phase 2)

- **Sentiment trend analysis:** Track sentiment changes over time
- **Competitor comparison:** Compare review themes across practices
- **Review response analysis:** Identify practices that respond to reviews (shows engagement)
- **Photo analysis:** Extract insights from review photos (facility quality, cleanliness)

---

## References

- Apify Google Maps Scraper: https://apify.com/compass/crawler-google-places
- GPT-4o-mini pricing: https://openai.com/api/pricing/
- Current Apify client: `src/scrapers/apify_client.py`
- Review data structure research: `docs/features/FEAT-005_google-reviews-analysis/research.md`
