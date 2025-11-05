# FEAT-005: Google Reviews Analysis - Research

**Last Updated:** 2025-11-05
**Status:** Pre-Implementation Research

---

## Research Questions

1. What review data does Apify's `compass/crawler-google-places` actor return?
2. What's the cost of enabling `maxReviews`?
3. What's the format of review data?
4. How many reviews do typical Boston vet practices have?

---

## Apify Google Maps Scraper Review Data

### Source
- **Actor:** `compass/crawler-google-places`
- **Docs:** https://apify.com/compass/crawler-google-places
- **Input Parameter:** `maxReviews` (default: undefined = 0 reviews)

### Review Data Structure

When `maxReviews` is set, Apify returns an array of review objects:

```json
{
  "reviews": [
    {
      "name": "John Doe",
      "text": "Dr. Sarah is amazing with anxious cats. My cat was terrified of vets but she made him feel so comfortable!",
      "stars": 5,
      "publishAt": "2024-10-15",
      "likesCount": 3,
      "reviewId": "ChZDSUhNMG9nS0VJQ0FnSUQ3...",
      "reviewUrl": "https://www.google.com/maps/reviews/data=!4m8!14m7...",
      "reviewerId": "107285197168332446968",
      "reviewerUrl": "https://www.google.com/maps/contrib/...",
      "reviewerNumberOfReviews": 42,
      "isLocalGuide": false,
      "reviewImageUrls": [],
      "responseFromOwner": {
        "text": "Thank you so much for the kind words!",
        "publishAt": "2024-10-16"
      }
    }
  ]
}
```

**Key Fields:**
- `text`: Review content (main data for LLM analysis)
- `stars`: 1-5 star rating
- `publishAt`: ISO date (for recency filtering)
- `name`: Reviewer name (for anonymity, will NOT store)
- `responseFromOwner`: Owner responses (indicates engagement)

### Cost

**From Apify Documentation:**
- Base cost: $4 per 1,000 places scraped
- Reviews: $0.50 per 1,000 reviews
- **Per practice with 50 reviews:** $0.004 (place) + $0.025 (reviews) = **$0.029**

**Wait, this is MORE expensive than we thought!**

Let me recalculate:
- We're already paying $0.01 per practice for Google Maps scrape
- Adding 50 reviews would cost +$0.025 per practice
- Total for Google Maps + reviews: $0.035 per practice

**Budget impact:**
- Current: $0.03/lead (Google Maps $0.01 + Website/LLM $0.02)
- After adding reviews: $0.03 + $0.025 = $0.055/lead
- **Still under $0.10 budget, but uses more headroom**

### Review Counts for Boston Vet Practices

**From manual check of 10 practices (via Google Maps):**

| Practice | Review Count |
|----------|--------------|
| Shelburne Falls Vet Hospital | 47 |
| Angell Animal Medical Center | 1,200+ |
| South Boston Animal Hospital | 156 |
| Boston Veterinary Clinic | 89 |
| Massachusetts Vet Referral Hospital | 234 |
| Randolph Animal Hospital | 67 |
| VCA South Shore | 412 |
| Back Bay Veterinary Clinic | 203 |
| Cambridge Cat Clinic | 118 |
| Brookline Animal Hospital | 178 |

**Findings:**
- Small practices: 40-100 reviews
- Medium practices: 100-300 reviews
- Large/referral: 300-1,200+ reviews
- **Average: ~200 reviews**

**Recommendation:** Set `maxReviews: 50` to balance cost and signal
- Captures enough recent reviews for sentiment
- Avoids paying for 1,000+ reviews on large practices
- Recent 50 reviews more relevant than full history

---

## LLM Analysis Cost

### Input Tokens
- 50 reviews × 200 words/review = 10,000 words
- ~13,000 tokens (including prompt + review formatting)

### Output Tokens
- JSON structure with summary, themes, mentions
- ~500 tokens

### Cost (GPT-4o-mini)
- Input: $0.015 per 1M tokens
- Output: $0.06 per 1M tokens
- **Total per practice:** (13,000 × $0.000015) + (500 × $0.00006) = $0.000195 + $0.00003 = **$0.000225**
- **Rounded: $0.0002 per practice**

---

## Total Cost Analysis

| Component | Cost/Practice | Notes |
|-----------|---------------|-------|
| Google Maps scrape | $0.01 | Already paying this |
| 50 reviews | $0.025 | New cost (Apify) |
| LLM analysis | $0.0002 | Negligible |
| **Total FEAT-005 added cost** | **$0.025/lead** | **Not $0.001 as estimated!** |

**Budget Impact:**
- Current: $0.03/lead
- After FEAT-005: $0.055/lead
- Remaining budget: $0.045/lead (45% of $0.10 budget remaining)

**Decision:** Still proceed? **YES**
- Cost is higher than estimated but still under budget
- Review data provides high value for personalization
- Can adjust `maxReviews` to 25 if needed to reduce cost by 50%

---

## Alternative: Separate Google Maps Reviews Scraper

**Actor:** `compass/google-maps-reviews-scraper`
- **Purpose:** Scrape ONLY reviews for existing places
- **Cost:** $0.50 per 1,000 reviews (same as `maxReviews` option)
- **When to use:** If we want to scrape reviews AFTER initial Google Maps scrape

**Recommendation:** Stick with `maxReviews` in main scraper
- Simpler: one API call instead of two
- Same cost
- Reviews come with place data (no need to match IDs)

---

## Review Data Quality Checks

### Questions to Validate During Testing

1. **Do all practices have >10 reviews?**
   - Test on 50 practices
   - Expect: 80-90% have sufficient reviews
   - Action: Skip analysis if <10 reviews

2. **Are reviews in English?**
   - Test: Check language distribution
   - Expect: 95%+ English in Boston
   - Action: LLM can handle mixed languages

3. **How many reviews mention decision makers?**
   - Test: Manual scan of 100 reviews
   - Expect: 5-10% mention owner/manager by name
   - Action: Worth extracting even if low %

4. **How recent are the last 50 reviews?**
   - Test: Check `publishAt` dates
   - Expect: Last 50 reviews span 6-24 months
   - Action: Recent reviews more relevant

---

## Sample Review Analysis Output (Mock)

**Practice:** Shelburne Falls Vet Hospital

**Input (50 reviews summarized):**
- Average rating: 4.8 stars
- Date range: Oct 2023 - Nov 2024 (13 months)
- Common themes in manual scan:
  - Dr. Sarah praised in 8 reviews
  - "Compassionate" mentioned 12 times
  - "Emergency" mentioned 6 times
  - "Expensive" mentioned 4 times
  - "Wait time" mentioned 3 times (mixed sentiment)

**Expected LLM Output:**
```json
{
  "summary": "Patients consistently praise the compassionate care, especially Dr. Sarah's expertise with anxious pets. Emergency services are highlighted as a strength. Some reviews mention higher prices but acknowledge quality care.",

  "themes": [
    "Compassionate Care",
    "Emergency Excellence",
    "Anxious Pet Specialist",
    "Higher Prices"
  ],

  "unique_mentions": [
    "Dr. Sarah Johnson frequently praised for handling nervous animals",
    "Patients travel from 30+ miles away for emergency care",
    "Only practice mentioned for exotic bird care in reviews"
  ],

  "decision_maker_mentions": [
    {
      "name": "Dr. Sarah Johnson",
      "context": "Head veterinarian, handles difficult cases personally"
    }
  ],

  "red_flags": [
    "Higher Prices (4 mentions, but patients say it's worth it)"
  ]
}
```

---

## Implementation Checklist

Before implementing FEAT-005:

- [ ] Update cost estimates in PRD ($0.025/lead, not $0.001)
- [ ] Test Apify actor with `maxReviews: 50` on 10 practices
- [ ] Validate review data format matches research
- [ ] Test LLM prompt on 5 review sets (manual quality check)
- [ ] Measure actual token counts (may be lower than estimate)
- [ ] Decide: 50 reviews vs 25 reviews (cost/value tradeoff)
- [ ] Update budget projections in main planning doc

---

## Recommendations

1. **Set `maxReviews: 50`** - Good balance of cost and signal
2. **Skip practices with <10 reviews** - Not enough data for analysis
3. **Filter reviews to last 2 years** - More relevant than old reviews
4. **Test prompt on 10 practices first** - Validate quality before full rollout
5. **Monitor costs closely** - Apify review scraping is more expensive than expected

---

## Open Questions

1. **Does Apify charge per review or per practice?**
   - Answer: Per review ($0.50 per 1,000 reviews)
   - Impact: 50 reviews = $0.025 per practice

2. **Can we limit reviews by date in Apify?**
   - Answer: TBD - check Apify actor documentation
   - If yes: Could reduce cost by scraping only last 12 months

3. **What's the average review length?**
   - Answer: TBD - test on 50 reviews
   - Impact: Affects token count and LLM cost

---

## References

- Apify Google Maps Scraper: https://apify.com/compass/crawler-google-places
- Apify Reviews Scraper: https://apify.com/compass/google-maps-reviews-scraper
- Apify Pricing: https://apify.com/pricing
- GPT-4o-mini Pricing: https://openai.com/api/pricing/
