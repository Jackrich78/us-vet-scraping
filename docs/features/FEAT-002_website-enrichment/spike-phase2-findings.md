# Phase 2 Findings: FEAT-000 Infrastructure Audit

**Date:** 2025-11-04
**Status:** Complete

## Summary

FEAT-000 shared infrastructure components referenced in FEAT-002 architecture do NOT exist yet. Per user decision, these will be **built inline during FEAT-002 implementation** and potentially extracted to FEAT-000 later.

## Missing Components

### 1. VetPracticeExtraction Model
**Location:** Should be in `src/models/enrichment_models.py` (doesn't exist)
**Status:** ❌ Missing
**Decision:** Create inline in FEAT-002 implementation
**Complexity:** Low (simple Pydantic model based on PRD schema)

### 2. CostTracker Utility
**Location:** Should be in `src/utils/cost_tracker.py` (doesn't exist)
**Status:** ❌ Missing
**Decision:** Create inline in FEAT-002 implementation
**Complexity:** Medium (tiktoken integration, budget monitoring)

### 3. retry_api_call Decorator
**Location:** Should be in `src/utils/retry.py` (doesn't exist)
**Status:** ❌ Missing
**Decision:** Use `tenacity` library directly, no custom decorator needed
**Complexity:** Low (can use tenacity.retry decorator directly)

### 4. ErrorAggregator Utility
**Location:** Should be in `src/utils/error_tracker.py` (doesn't exist)
**Status:** ❌ Missing
**Decision:** Use simple list tracking for MVP
**Complexity:** Low (basic error collection)

## Existing Infrastructure (✅ Ready)

### 1. WebsiteScrapingConfig
**Location:** `src/config/config.py:63-73`
**Status:** ✅ Exists
**Notes:** Has all required fields (max_concurrent, timeout, cache_enabled, etc.)

### 2. Logging Setup
**Location:** `src/utils/logging.py`
**Status:** ✅ Exists
**Notes:** Basic console and file logging with test mode support

### 3. Notion Config
**Location:** `src/config/config.py:46-60`
**Status:** ✅ Exists
**Notes:** Has API key, database ID, batch size, rate limit delay

### 4. VeterinaryPractice Model
**Location:** `src/models/apify_models.py:112-154`
**Status:** ✅ Exists (but different from VetPracticeExtraction)
**Notes:** Used for FEAT-001 Google Maps data, not website enrichment

## Implementation Strategy

### Phase 1: Create Models (FEAT-002 Implementation)
```python
# src/models/enrichment_models.py
from pydantic import BaseModel, Field
from typing import Optional, List

class DecisionMaker(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

class VetPracticeExtraction(BaseModel):
    vet_count_total: Optional[int] = Field(None, ge=1, le=50)
    vet_count_confidence: Optional[str] = Field(None, pattern="^(high|medium|low)$")
    decision_maker: Optional[DecisionMaker] = None
    emergency_24_7: bool = False
    specialty_services: List[str] = Field(default_factory=list)
    wellness_programs: bool = False
    boarding_services: bool = False
    online_booking: bool = False
    telemedicine: bool = False
    patient_portal: bool = False
    digital_records_mentioned: bool = False
    personalization_context: List[str] = Field(default_factory=list, max_length=3)
    awards_accreditations: List[str] = Field(default_factory=list)
    unique_services: List[str] = Field(default_factory=list)
    extraction_timestamp: str = Field(..., description="ISO 8601 timestamp")
```

### Phase 2: Create CostTracker (FEAT-002 Implementation)
```python
# src/utils/cost_tracker.py
import tiktoken
from typing import Optional

class CostTracker:
    def __init__(self, max_budget: float = 1.00, model: str = "gpt-4o-mini"):
        self.max_budget = max_budget
        self.cumulative_cost = 0.0
        self.call_count = 0
        self.encoding = tiktoken.encoding_for_model(model)

        # gpt-4o-mini pricing (as of 2025-11-04)
        self.input_price_per_million = 0.15
        self.output_price_per_million = 0.60

    def count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        input_cost = (input_tokens * self.input_price_per_million) / 1_000_000
        output_cost = (output_tokens * self.output_price_per_million) / 1_000_000
        return input_cost + output_cost

    def check_budget(self, estimated_cost: float) -> bool:
        if self.cumulative_cost + estimated_cost > self.max_budget:
            raise CostLimitExceeded(
                f"Cost limit exceeded: ${self.cumulative_cost:.4f} + ${estimated_cost:.4f} > ${self.max_budget:.2f}"
            )
        return True

    def track_call(self, input_tokens: int, output_tokens: int):
        cost = self.estimate_cost(input_tokens, output_tokens)
        self.cumulative_cost += cost
        self.call_count += 1

class CostLimitExceeded(Exception):
    pass
```

### Phase 3: Use tenacity for Retries
```python
# No custom decorator needed, use tenacity directly:
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def call_openai_with_retry(...):
    # OpenAI API call
    pass
```

### Phase 4: Simple Error Tracking
```python
# No dedicated class needed for MVP:
failed_practices = []
for practice in practices:
    try:
        # ... scraping/extraction logic ...
    except Exception as e:
        failed_practices.append({
            "practice_id": practice.id,
            "error": str(e),
            "error_type": type(e).__name__
        })
```

## Descoped Features (Track in future-enhancements.md)

These can be extracted to FEAT-000 after FEAT-002 is complete:

1. **CostTracker** → Extract to `src/utils/cost_tracker.py` with enhanced features:
   - Multiple model support
   - Cost history tracking
   - Budget alerts

2. **ErrorAggregator** → Extract to `src/utils/error_tracker.py`:
   - Error categorization
   - Retry statistics
   - Error reporting

3. **Retry Utilities** → Extract to `src/utils/retry.py`:
   - Custom retry decorators
   - Backoff strategies
   - Circuit breaker pattern

## Next Steps

- ✅ Phase 2 complete
- → Move to Phase 3: Validate Notion schema
- → Spikes 1-5: Validate technical assumptions
- → Create models/utilities during FEAT-002 implementation

---

**Conclusion:** FEAT-000 dependencies are not blocking. We can proceed with FEAT-002 implementation using inline components.
