# FEAT-008: Social Media Presence Tracking

**Status:** Research Placeholder - DO NOT IMPLEMENT YET
**Created:** 2025-11-05
**Owner:** TBD
**Dependencies:** TBD
**Cost Impact:** TBD (likely $0.005-0.02/lead)

---

## Problem Statement

Social media presence (Facebook, Instagram, Twitter) indicates practice marketing sophistication and community engagement, which could inform lead scoring and personalization.

### Potential Value
- **Marketing sophistication:** Active social = tech-savvy practice
- **Community engagement:** Follower count, engagement rate
- **Content insights:** Recent posts, promotions, events
- **Brand strength:** Consistent posting, professional content

### Why This is a Placeholder

**High Complexity:**
- Each platform requires separate scraping approach
- Facebook/Instagram have strong anti-scraping measures
- API access requires app approval + ongoing maintenance
- Data structure varies significantly across platforms

**Moderate Value:**
- Nice-to-have, not critical for initial enrichment
- Social presence doesn't strongly correlate with ICP fit
- Many small practices have minimal social media

**Priority:**
- FEAT-004, 005, 006, 007 provide higher ROI
- Social media can wait until Phase 2 or 3

---

## Research Questions (To Answer Before Implementation)

1. **What percentage of Boston vet practices have active social media?**
   - Manually check 50 practices
   - Facebook: ?%
   - Instagram: ?%
   - Twitter: ?%

2. **What's the best data source?**
   - Option A: Apify social media scrapers (~$0.01/profile)
   - Option B: Official APIs (Facebook Graph API, Instagram Basic Display)
   - Option C: Web scraping (risky, likely blocked)

3. **What data is actually useful?**
   - Follower count? (vanity metric, may not matter)
   - Post frequency? (indicates active marketing)
   - Engagement rate? (complex to calculate)
   - Recent post content? (for personalization)

4. **What's the cost/benefit?**
   - If 50% of practices have Facebook: $0.005/practice
   - If 30% have Instagram: $0.003/practice
   - Total: ~$0.008/practice for social enrichment
   - Worth it? TBD based on sales team feedback

---

## Potential Approach (If Implemented in Phase 2)

### 1. Facebook Business Page Scraping
**Data to Extract:**
- Page URL
- Follower count
- Check-ins (indicates popularity)
- Page category
- Last post date (active vs dormant)

### 2. Instagram Business Profile Scraping
**Data to Extract:**
- Profile URL
- Follower count
- Post count
- Last post date
- Bio (may have tagline/mission)

### 3. Notion Fields (Proposed)
- **Facebook Page URL** (url)
- **Facebook Followers** (number)
- **Facebook Last Post Date** (date)
- **Instagram Profile URL** (url)
- **Instagram Followers** (number)
- **Instagram Post Count** (number)
- **Social Media Score** (select: None/Low/Medium/High)
  - None: No social presence
  - Low: <100 followers, infrequent posts
  - Medium: 100-1000 followers, regular posts
  - High: >1000 followers, consistent engagement

---

## Next Steps (Not Today)

1. **Phase 2 Research:**
   - Manually audit 50 practices for social media presence
   - Test Apify social media scrapers
   - Calculate ROI vs. cost

2. **Decision Point:**
   - If >70% of practices have active social: consider implementing
   - If <50%: defer to Phase 3 or abandon

3. **If Approved:**
   - Create full PRD with technical approach
   - Estimate development time (likely 2-3 days)
   - Add to enrichment pipeline

---

## Why Not Now?

**Priority:** Fix core enrichment first (FEAT-004)
**Value:** Nice-to-have, not critical for sales personalization
**Complexity:** High (multiple platforms, scraping challenges)
**Cost:** Moderate ($0.008/practice adds up at scale)

**Recommendation:** Complete FEAT-004, 005, 006, 007 first. Reassess social media in 3-6 months based on sales team feedback.

---

## References

- Apify Facebook scraper: https://apify.com/apify/facebook-pages-scraper
- Apify Instagram scraper: https://apify.com/apify/instagram-scraper
- Facebook Graph API: https://developers.facebook.com/docs/graph-api
- Instagram Basic Display API: https://developers.facebook.com/docs/instagram-basic-display-api
