# Manual Testing Guide: Website Scraping Root Cause Validation

**Feature ID:** FEAT-004
**Created:** 2025-11-05
**Intended Audience:** You (User) - Pre-Session Work
**Estimated Time:** 30 minutes

---

## Purpose

Validate root causes of scraping failures BEFORE implementing fixes. Your findings will inform which fixes to prioritize in Session 2.

---

## Prerequisites

**Required:**
- ✅ Chrome browser (latest version)
- ✅ Access to Notion database with practice data
- ✅ 5 practice URLs that FAILED scraping in previous runs

**How to Find Failed Practices:**
- Open your Notion database
- Filter for practices where "Scraping Status" = "Failed" or "Enrichment Status" = "Pending"
- Select 5 practices with websites
- Copy their website URLs

---

## Test Steps

### For Each of 5 URLs, Complete All 5 Steps

---

### Step 1: Basic Load Test

**Action:**
1. Open URL in Chrome (new incognito window recommended)
2. Wait 10 seconds for page to load

**Document:**
- ✅ **Loads successfully?** Yes / No
- ✅ **If NO, what error?**
  - "This site can't be reached" (DNS/connection error)
  - "Connection timed out" (timeout)
  - Blank page (JavaScript error?)
  - Other: [describe]

---

### Step 2: Check for Redirects

**Action:**
1. Open Chrome DevTools: Press `F12` (Windows) or `Cmd+Option+I` (Mac)
2. Click **Network** tab at the top
3. **Reload the page** (Ctrl+R or Cmd+R)
4. Look at the FIRST request in the list (usually the URL you entered)
5. Check if **Status Code** is `301`, `302`, or `307` (these are redirects)
6. If redirected, look at **Location** header to see final URL

**Document:**
- ✅ **Original URL:** [URL you entered]
- ✅ **Redirects?** Yes / No
- ✅ **If YES:**
  - **Redirect Type:** 301 / 302 / 307
  - **Final URL:** [where it redirected to]
  - **Example:** `http://example.com` → `https://www.example.com`

**Screenshot Location:** Network tab showing redirect

---

### Step 3: Check Status Code

**Action:**
1. In Network tab (still open from Step 2)
2. Click on the FIRST request (the main page load)
3. Look at **Status Code** in the Headers section (right panel)

**Document:**
- ✅ **Status Code:** [number]
  - `200` = Success
  - `404` = Not Found
  - `403` = Forbidden (may be blocking)
  - `500` = Server Error
  - `502/503` = Server Temporarily Down
  - Other: [number]

**If NOT 200:**
- ✅ **Screenshot:** Capture error page or Network tab showing status

---

### Step 4: Check for UTM/Tracking Parameters

**Action:**
1. Look at the URL in Chrome's address bar
2. Check if it contains `?` followed by parameters

**Document:**
- ✅ **Has parameters?** Yes / No
- ✅ **If YES, list them:**
  - `utm_source=...`
  - `utm_medium=...`
  - `utm_campaign=...`
  - `y_source=...`
  - `fbclid=...`
  - `gclid=...`
  - Other: [parameter names]

**Example:**
```
URL with params: https://example-vet.com/contact?utm_source=google_my_business&y_source=1_MTU4NjM...
Parameters found: utm_source, y_source
```

---

### Step 5: Check for Blocking / Anti-Bot Measures

**Action:**
1. Look at the page content (the actual website)
2. Check for these signs of blocking:
   - **CloudFlare Challenge:** "Checking your browser..." message
   - **CAPTCHA:** "I'm not a robot" checkbox or image selection
   - **Access Denied:** "403 Forbidden" or "Access Denied" message
   - **Bot Detection:** "We've detected unusual activity" message

**Document:**
- ✅ **Blocking detected?** Yes / No
- ✅ **If YES, type:**
  - CloudFlare
  - CAPTCHA
  - Access Denied
  - Other: [describe]

**If YES:**
- ✅ **Screenshot:** Capture blocking page

---

### Step 6: Check Console for JavaScript Errors

**Action:**
1. In Chrome DevTools, click **Console** tab
2. Look for RED error messages

**Document:**
- ✅ **JavaScript errors?** Yes / No
- ✅ **If YES, count:** [number of errors]
- ✅ **If YES, common error types:**
  - "Failed to load resource" (missing files)
  - "Uncaught TypeError" (JavaScript bugs)
  - "Mixed Content" (http/https issues)
  - Other: [describe]

**Note:** A few minor errors are normal. Look for MANY errors or critical failures.

---

## Results Template

**Copy this template for each of your 5 URLs:**

```markdown
## Test Results

### URL 1: [Practice Name]
**Website:** https://example-vet.com

**Step 1: Load Test**
- Loads: ✅ Yes / ❌ No
- Error (if any): [describe]

**Step 2: Redirects**
- Original URL: https://example-vet.com
- Redirects: ✅ Yes / ❌ No
- Final URL: [if different]

**Step 3: Status Code**
- Status: 200
- Screenshot: [if not 200]

**Step 4: UTM Parameters**
- Has params: ❌ No
- Parameters: [none]

**Step 5: Blocking**
- Blocked: ❌ No
- Type: [none]

**Step 6: Console Errors**
- Errors: ✅ Yes / ❌ No
- Count: 2 (minor - safe to ignore)

**Overall Assessment:**
- ✅ Site loads fine, no issues detected
- ⚠️ Minor issue: [describe]
- ❌ Critical issue: [describe]

---

### URL 2: [Practice Name]
**Website:** https://example2-vet.com?utm_source=google

[Repeat template]

---

### URL 3: [Practice Name]
**Website:** https://example3-vet.com

[Repeat template]

---

### URL 4: [Practice Name]
**Website:** https://example4-vet.com

[Repeat template]

---

### URL 5: [Practice Name]
**Website:** https://example5-vet.com

[Repeat template]

---

## Analysis & Recommendations

### Pattern Summary (Based on 5 URLs)

**Root Causes Identified:**
1. **[Most Common Issue]:** Occurred on [X/5] URLs
   - Examples: URL 1, URL 3
   - Recommendation: [Which fix to prioritize]

2. **[Second Most Common]:** Occurred on [X/5] URLs
   - Examples: URL 2
   - Recommendation: [Which fix]

3. **[Other Issues]:** Occurred on [X/5] URLs
   - Examples: URL 4
   - Recommendation: [Action]

### Fix Priority for Session 2

**Based on your findings, prioritize these fixes:**

**HIGH PRIORITY (Implement first):**
- [ ] **Retry Logic** - IF you saw timeouts or 5xx errors
- [ ] **URL Sanitization** - IF you saw UTM parameters (utm_, y_source, fbclid)
- [ ] **URL Pattern Expansion** - IF you couldn't validate (sites load but we're not scraping them)

**LOW PRIORITY (Skip or implement last):**
- [ ] **User Agent Rotation** - IF you saw 403/blocking on MOST sites (unlikely)
- [ ] **Fallback Scraping** - IF sites are simple static HTML
- [ ] **Other:** [based on your findings]

### Unexpected Findings

**Did you discover anything surprising?**
- [Describe unexpected observations]
- [New hypothesis about failures]
- [Questions for Session 1]

---

## Completion Checklist

- [ ] Tested all 5 URLs
- [ ] Documented all 6 steps for each URL
- [ ] Identified 1-3 common patterns
- [ ] Prioritized fixes for Session 2
- [ ] Saved this file with your findings
- [ ] Ready to share results at start of Session 1

---

## What Happens Next

**Session 1 will:**
1. Review your findings from this manual test
2. Fix prompt schema (30 min)
3. Add diagnostic logging (2 hours)
4. Run automated diagnostic on 20 practices
5. Compare your manual findings with automated diagnostic
6. Finalize fix priorities for Session 2

**Your manual findings will validate (or challenge) our assumptions about root causes!**

---

## Questions or Issues?

**If you encounter problems during testing:**
1. Document what happened in the "Unexpected Findings" section
2. Take screenshots if helpful
3. We'll discuss at start of Session 1

**If a URL is completely inaccessible:**
- That's valuable data! Document it.
- Move to next URL if you can't test it

---

## Example Completed Test (For Reference)

```markdown
## Test Results

### URL 1: Boston Veterinary Clinic
**Website:** https://bostonvetclinic.com

**Step 1: Load Test**
- Loads: ✅ Yes
- Error: None

**Step 2: Redirects**
- Original URL: https://bostonvetclinic.com
- Redirects: ❌ No
- Final URL: Same

**Step 3: Status Code**
- Status: 200
- Screenshot: N/A

**Step 4: UTM Parameters**
- Has params: ❌ No
- Parameters: None

**Step 5: Blocking**
- Blocked: ❌ No
- Type: None

**Step 6: Console Errors**
- Errors: ✅ Yes
- Count: 1 (Google Analytics - safe to ignore)

**Overall Assessment:**
- ✅ Site loads perfectly, no issues

---

### URL 2: Example Animal Hospital
**Website:** http://exampleanimalhospital.com?utm_source=google_my_business

**Step 1: Load Test**
- Loads: ✅ Yes
- Error: None

**Step 2: Redirects**
- Original URL: http://exampleanimalhospital.com
- Redirects: ✅ Yes
- Final URL: https://www.exampleanimalhospital.com (removed params, added https)

**Step 3: Status Code**
- Status: 301 (redirect) → 200 (final)
- Screenshot: N/A

**Step 4: UTM Parameters**
- Has params: ✅ Yes
- Parameters: utm_source=google_my_business

**Step 5: Blocking**
- Blocked: ❌ No
- Type: None

**Step 6: Console Errors**
- Errors: ❌ No
- Count: 0

**Overall Assessment:**
- ⚠️ Has UTM parameter + redirect (may confuse scraper)
- Recommendation: URL sanitization would help

---

[Continue for URLs 3-5]

## Analysis

**Root Causes Identified:**
1. **UTM Parameters:** 2/5 URLs had tracking parameters
   - Recommendation: HIGH PRIORITY - Implement URL sanitization

2. **Redirects:** 2/5 URLs redirected (http → https)
   - Recommendation: MEDIUM - URL sanitization handles this too

3. **All Sites Load:** 5/5 URLs loaded successfully in browser
   - Recommendation: Scraper issue, not website issue

### Fix Priority
1. ✅ **URL Sanitization** (HIGH) - Affects 40% of URLs
2. ✅ **Prompt Fix** (CRITICAL) - All URLs load but extractions fail
3. ⚠️ **Retry Logic** (SKIP FOR NOW) - No timeouts observed
```

---

**Good luck with your testing! Your findings will be invaluable for Session 1.** 🚀
