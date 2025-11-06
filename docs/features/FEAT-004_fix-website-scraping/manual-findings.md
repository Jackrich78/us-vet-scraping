# Manual findings of 5 vet websites

## Test Results

### URL 1: GreyLock Animal Hospital
**Website:** https://greylockanimalhospital.com/

**Step 1: Load Test**
- Loads: ✅ Yes
- Error (if any): tracker.min.js failed ```Request URL
https://apps.vetcor.com/assets/tracker.min.js
Request Method GET
Status Code 404 Not Found```

**Step 2: Redirects**
- Original URL: https://greylockanimalhospital.com/
- Redirects: ❌ No

**Step 3: Status Code**
- Status: 200

**Step 4: UTM Parameters**
- Has params: ❌ No

**Step 5: Blocking**
- Blocked: A couple of recaptcha entries in the network tab. nothing blocking the page for me as a user and I don't see any captch or anti-bot measures elsewhere.
- Type: recaptcha__en.js:```Request URL
https://www.gstatic.com/recaptcha/releases/naPR4A6FAh-yZLuCX253WaZq/recaptcha__en.js
Request Method
GET
Status Code
200 OK (from memory cache)
Remote Address
142.251.140.227:443
Referrer Policy
strict-origin-when-cross-origin```

**Step 6: Console Errors**
- Errors: ✅ Yes 
- Count: Possibly minor:```(index):270 Uncaught ReferenceError: ppv is not defined
    at (index):270:16
(anonymous) @ (index):270
(index):780 Uncaught TypeError: $ is not a function
    at (index):780:1
(anonymous) @ (index):780
(index):1971 Uncaught ReferenceError: google is not defined
    at (index):1971:1
(anonymous) @ (index):1971
main.js:330  GET https://maps.googleapis.com/maps/api/mapsjs/gen_204?csp_test=true net::ERR_BLOCKED_BY_CLIENT```

**Overall Assessment:**
- ✅ Site loads fine, no issues detected

---

### URL 2: Shelburne Falls Veterinary Hospital
**Website:** https://shelburnefallsvet.com/

**Step 1: Load Test**
- Loads: ✅ Yes
- Error (if any): Page loads fine but a few web?clientid errors like:```Request URL
https://csp.secureserver.net/eventbus/web?clientid=b18ef4f046435b64a469b32c3c1c20a3
Referrer Policy
strict-origin-when-cross-origin```

**Step 2: Redirects**
- Original URL: https://shelburnefallsvet.com/
- Redirects: ✅ Yes
- Final URL: ```Request URL
https://shelburnefallsvet.com/
Request Method
GET
Status Code
304 Not Modified
Remote Address
76.223.105.230:443
Referrer Policy
strict-origin-when-cross-origin``` doesn't look like the url is actually different.

**Step 3: Status Code**
- Status: 304

**Step 4: UTM Parameters**
- Has params: ❌ No

**Step 5: Blocking**
- Blocked: ❌ No

**Step 6: Console Errors**
- Errors: ✅ Yes 
- Count: 6 web?clientid= errors, seems safe to ignore. 1 404 for a file not found.

**Overall Assessment:**
- ✅ Site loads fine, no visible issues as a user detected

---

### URL 3: Main Street Veterinary Hospital
**Website:** https://mainstreetvethosp.com/

**Step 1: Load Test**
- Loads: ✅ Yes

**Step 2: Redirects**
- Redirects: ❌ No

**Step 3: Status Code**
- Status: 200

**Step 4: UTM Parameters**
- Has params: ❌ No

**Step 5: Blocking**
- Blocked: ✅ Yes
- Type: recaptcha__en.js

**Step 6: Console Errors**
- Errors: ✅ Yes
- Count: 3 minor. gtm.js, tracker.min.js, gen_204?csp_test=true

**Overall Assessment:**
- ✅ Site loads fine, no issues detected


---

### URL 4: Raynham Verterinary hospital
**Website:** https://raynhamvet.com/

**Step 1: Load Test**
- Loads: ✅ Yes

**Step 2: Redirects**
- Redirects: ❌ No

**Step 3: Status Code**
- Status: 200

**Step 4: UTM Parameters**
- Has params: ❌ No

**Step 5: Blocking**
- Blocked: ❌ No

**Step 6: Console Errors**
- Errors: ✅ Yes
- Count: 2 (minor - safe to ignore)

**Overall Assessment:**
- ✅ Site loads fine, no issues detected


---

### URL 5: Berkshire VEterinary Hospital
**Website:** https://berkshirevet.com/

**Step 1: Load Test**
- Loads: ✅ Yes

**Step 2: Redirects**
- Redirects: ❌ No

**Step 3: Status Code**
- Status: 200

**Step 4: UTM Parameters**
- Has params: ❌ No

**Step 5: Blocking**
- Blocked: ❌ No

**Step 6: Console Errors**
- Errors: ✅ Yes / ❌ No
- Count: 2 (minor Google Tag manager - safe to ignore)

**Overall Assessment:**
- ✅ Site loads fine, no issues detected


---

## Analysis & Recommendations

### Pattern Summary (Based on 5 URLs)

**Root Causes Identified:**
1. **GTM tag error:** Occurred on [3/5] URLs
   - Examples: (https://raynhamvet.com/), (https://berkshirevet.com/), (https://mainstreetvethosp.com/)
   - Recommendation: I hope we can ignore

2. **recaptcha in network tab, nothing visible to the user:** Occurred on [3/5] URLs
   - Examples: (https://greylockanimalhospital.com/), (https://mainstreetvethosp.com/), (https://shelburnefallsvet.com/)
   - Recommendation: Looking for your guidance on how to avoid. 

3. **1 redirect:** Occurred on [1/5] URLs
   - Examples: https://shelburnefallsvet.com/
   - Recommendation: Looking for your guidance, can we ignore and still get results?
