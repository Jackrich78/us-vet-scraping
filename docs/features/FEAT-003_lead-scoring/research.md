# Research Findings: ICP Fit Lead Scoring - Resilient Integration Patterns

**Feature ID:** FEAT-003
**Research Date:** 2025-11-04
**Researcher:** Researcher Agent

## Research Questions

*Questions from PRD that this research addresses:*

1. How to calculate partial scores with missing enrichment data? (Graceful degradation patterns)
2. How should scoring failures be handled without cascading to FEAT-002? (Error recovery strategies)
3. Best practices for implementing state machine in Python? (State machine implementation)
4. How to maintain performance (<100ms) when handling partial/missing data? (Performance optimization)
5. How do other systems handle initial vs final scoring? (Dual scoring system patterns)

## Findings

### Topic 1: Graceful Degradation with Weighted Scoring

**Summary:** Weighted scoring systems can handle missing data through partial calculations by adjusting weights proportionally. The key approaches are: (1) skip missing components and normalize weights, (2) assign 0 points for missing data, or (3) use default values with confidence penalties. Multiplicative penalties (0.7x, 0.9x, 1.0x) are preferred over additive for confidence-based scoring because they preserve proportional impact across all score ranges.

**Details:**
- **Weighted average with missing values**: Use `np.average()` with masked arrays or filter out NaN values before calculation. For scoring systems, set missing component score = 0 and exclude from weight normalization (i.e., calculate with available dimensions only).
- **Multiplicative vs Additive penalties**: Research shows multiplicative penalties (score × confidence_multiplier) provide consistent percentage impact regardless of base score magnitude. A 1% change in any indicator leads to 1% change in overall score with multiplicative weighting, making it more predictable. Additive penalties can skew results at different score ranges.
- **Score normalization strategies**: For additive scoring, the simplest normalization allocates a score of 100 for the best observed value on each criterion. When combining scores with different confidence levels, normalize first, then apply confidence multipliers.
- **Partial calculation pattern**: Detect NaN/null values, remove them before calculating the score by deleting corresponding weights and dropping NaN components. This allows graceful degradation to baseline-only scoring when enrichment data is unavailable.

**Source:** Stack Overflow - Row-wise score using weights with missing values, ScienceDirect - Score Normalization, O'Reilly - Soft Computing Evaluation Logic
**URL:** https://stackoverflow.com/questions/58066225/row-wise-score-using-weights-for-a-subset-of-columns-with-missing-values
**Retrieved:** 2025-11-04 via WebSearch

---

### Topic 2: Circuit Breaker Pattern for Error Recovery

**Summary:** Circuit breaker pattern prevents cascading failures by monitoring downstream service calls and "opening" the circuit after a threshold of failures. PyBreaker is the most mature Python implementation, supporting three states (Closed/Open/Half-Open) with configurable failure thresholds and reset timeouts. This prevents FEAT-003 scoring failures from blocking FEAT-002 enrichment pipeline.

**Details:**
- **Circuit breaker states**: (1) **Closed**: Normal operation, requests pass through. (2) **Open**: Failure threshold exceeded, all requests fail fast with CircuitBreakerError. (3) **Half-Open**: After reset_timeout, allows one trial call - success closes circuit, failure re-opens.
- **PyBreaker configuration**: `fail_max=5` sets consecutive failures before opening; `reset_timeout=60` (seconds) defines how long circuit stays open; `listeners` for monitoring/logging events; optional Redis backend for distributed state.
- **Integration with retries**: Combine Circuit Breaker with Retry pattern for comprehensive fault handling. Circuit breaker stops retries after threshold, preventing resource exhaustion. Use exponential backoff (5s, 10s, 30s, 1min) for retry delays.
- **Fallback mechanisms**: When circuit is open, return cached response, default value, or error with graceful degradation. For FEAT-003: log error in Score Breakdown field, set lead_score=null, preserve enrichment state.
- **Monitoring thresholds**: Alert when circuit opens frequently (>3 times/hour indicates systemic issue). Track error types (transient vs non-transient) to tune fail_max and reset_timeout.

**Source:** PyPI - pybreaker, Medium - Circuit Breaker Pattern in Python Microservices, GeeksforGeeks - Circuit Breaker Pattern
**URL:** https://pypi.org/project/pybreaker/
**Retrieved:** 2025-11-04 via WebSearch

---

### Topic 3: Python State Machine Libraries

**Summary:** Two mature Python state machine libraries: **transitions** (established, object-oriented, attached to models) and **python-statemachine** (modern, declarative, separate concerns). For FEAT-003, a simple state machine is sufficient - Notion status field can track state without a full library. Idempotent transitions are achieved by checking current state before allowing transitions.

**Details:**
- **transitions library**: Lightweight, uses `Machine` class attached to model objects. Supports ordered transitions, conditional transitions, callbacks on enter/exit. Well-documented with extensive examples. Compatible with Python 2.7+ and 3.0+.
- **python-statemachine library**: Declarative syntax with chained transitions (e.g., `green.to(yellow) | yellow.to(red)`). States defined as class attributes, events bound to transitions. Supports validation, graph visualization, Python 3-focused design. More modern but slightly heavier.
- **State persistence in Notion**: For simple state tracking, use Notion status select field: "Pending Enrichment", "Completed", "Failed". No need for library - check current state before transitions in application logic.
- **Idempotent state transitions**: Ensure transitions are safe to retry by checking preconditions. Example: Only transition from "Pending" → "Completed" if score calculation succeeds. If already "Completed", skip transition. Log state changes with timestamp for audit trail.
- **Best practices**: (1) Clear state definitions with concise names. (2) Minimal set of states capturing essential behavior. (3) Use Python enums for type-safe state representation. (4) Validate transitions with conditions/guards. (5) Avoid ambiguous or overlapping states.

**Source:** GitHub - pytransitions/transitions, PyPI - python-statemachine, DEV Community - State Machines Best Practices
**URL:** https://github.com/pytransitions/transitions
**Retrieved:** 2025-11-04 via WebSearch

---

### Topic 4: Asyncio Timeout Patterns for Performance

**Summary:** `asyncio.wait_for()` is the standard pattern for timeout enforcement in async Python. Set per-practice timeout (5 seconds for FEAT-003), catch TimeoutError, and implement graceful fallback. Fast-path optimization: check if enrichment data exists before expensive calculations. Use timeout decorators for reusable timeout injection across multiple coroutines.

**Details:**
- **asyncio.wait_for() usage**: Waits for task completion with timeout, cancels task and raises TimeoutError if exceeded. Basic pattern: `await asyncio.wait_for(score_practice(id), timeout=5.0)`. Always wrap in try/except to handle TimeoutError gracefully.
- **Best practices for timeouts**: (1) Always use timeouts when touching external systems. (2) Log timeout events with timestamp and context. (3) Implement retry strategy with progressive timeouts or max retry count. (4) Use shield() to prevent task cancellation if you need task to complete despite timeout.
- **Fast-path vs slow-path optimization**: Check if enrichment data exists before starting score calculation (fast-path: return baseline score immediately if no enrichment). Slow-path: Full calculation with all dimensions when enrichment available. This avoids unnecessary computation and reduces timeout risk.
- **Timeout decorator pattern**: Create reusable decorator that injects timeout behavior automatically. Keeps async functions clean and timeouts consistent across codebase. Example: `@timeout(5.0)` decorator applies to any coroutine.
- **Performance monitoring**: Track timeout frequency, average calculation time, and timeout-to-success ratio. Alert when timeouts exceed 5% of requests (indicates performance degradation or timeout too aggressive).

**Source:** Super Fast Python - Asyncio Timeout Best Practices, Python Tutorial - asyncio.wait_for(), Better Stack - Complete Guide to Timeouts
**URL:** https://superfastpython.com/asyncio-timeout-best-practices/
**Retrieved:** 2025-11-04 via WebSearch

---

### Topic 5: Dead Letter Queue and Retry Patterns

**Summary:** Dead Letter Queue (DLQ) stores messages that fail processing after retry attempts. For FEAT-003, implement DLQ for scoring failures that can be manually reprocessed later via CLI rescore command. Distinguish transient errors (retry immediately) from non-transient errors (send to DLQ). Use exponential backoff for retries to avoid overwhelming services.

**Details:**
- **Error types**: (1) **Transient errors**: Connectivity issues, temporary timeouts - retry directly without DLQ. (2) **Non-transient errors**: Validation failures, missing required data, logic errors - send to DLQ after max retries. (3) **Poison pills**: Messages that always fail (e.g., invalid data format) - route to permanent DLQ immediately.
- **Retry strategies**: (1) **Synchronous retry**: Block consumer thread, reprocess immediately (simple but blocks pipeline). (2) **Asynchronous retry**: Queue failed messages with delay, process separately (complex but non-blocking). For FEAT-003: No automatic retries in auto-trigger flow - manual rescore via CLI instead.
- **Exponential backoff**: Gradually increase delay between retries: 5s, 10s, 30s, 1min. Prevents overwhelming downstream services. Set max retry limit (e.g., 3 attempts) before sending to DLQ.
- **DLQ best practices**: (1) Only push non-retryable errors to DLQ. (2) Keep original message with metadata (error message, timestamp, app name). (3) Set TTL or max messages to prevent infinite buildup. (4) Provide replay mechanism (CLI command for FEAT-003).
- **FEAT-003 application**: Log scoring failures in Score Breakdown field (JSON with error key). Set lead_score=null. Preserve enrichment_status. No automatic retry - sales team can trigger manual rescore via CLI when data corrected.

**Source:** Redpanda Blog - Reliable Message Processing with Dead Letter Queue, GitHub - RabbitMQ Retry using DLX in Python, Karafka - Dead Letter Queue Documentation
**URL:** https://www.redpanda.com/blog/reliable-message-processing-with-dead-letter-queue
**Retrieved:** 2025-11-04 via WebSearch

---

### Topic 6: Dual Scoring System Database Patterns

**Summary:** Dual scoring systems maintain multiple score versions for different purposes (initial triage vs comprehensive evaluation). Database design uses separate columns for each score type (initial_score, lead_score) with timestamps. Score history tracking requires separate table with version_id and current_flag. For FEAT-003 MVP, store both scores in main table without version history.

**Details:**
- **Score versioning strategies**: (1) **Separate columns**: Simplest approach - store initial_score and lead_score in same table row. (2) **Version table**: Linked list of score versions with version_id, prev_version_id, current_flag. (3) **Archive table**: Copy record to history table on each update, maintain audit trail.
- **Dual score use cases**: Initial score for quick triage during data ingestion (FEAT-001: 0-25 points from Google Maps). Lead score for detailed evaluation after enrichment (FEAT-003: 0-120 points with full dimensions). Both coexist in Notion: initial_score never changes (historical), lead_score recalculated on rescore.
- **Migration patterns**: Start with simple scoring, add complex scoring later. Preserve initial scores for comparison, append new scores without overwriting. Document score calculation changes in changelog for business transparency.
- **Score breakdown storage**: Store score components as JSON in rich_text field (Notion) or JSONB column (PostgreSQL). Example: `{"practice_size": {"score": 25, "reason": "4 vets"}, "total": 115}`. Enables debugging and transparency without separate tables.
- **UI considerations**: Display both scores with labels ("Initial" vs "Lead"). Highlight which score is current priority tier basis. Show confidence flags for low-confidence components.

**Source:** Stack Overflow - Database design for scoring system, Stack Overflow - Versioning design patterns, Vertabelo - Database Model for Board Games
**URL:** https://stackoverflow.com/questions/14835512/sql-database-model-for-a-scoring-system
**Retrieved:** 2025-11-04 via WebSearch

---

## Recommendations

### Primary Recommendation: Weighted Scoring with Graceful Degradation + Circuit Breaker Pattern

**Rationale:**
- **Weighted scoring with missing data handling**: Use partial calculation by excluding missing components and calculating with available dimensions only. Assign 0 points to missing components (not null, not default value) for clean score breakdown. This aligns with PRD Scenarios B, D, E where practices have incomplete enrichment data.
- **Multiplicative confidence penalties**: Apply confidence multipliers (high=1.0x, medium=0.9x, low=0.7x) to practice_size_score only (most critical dimension). Multiplicative approach maintains proportional impact across all score ranges, unlike additive penalties which can skew results.
- **Circuit breaker for auto-trigger integration**: Wrap scoring calls in PyBreaker circuit breaker with fail_max=5, reset_timeout=60s. If scoring fails repeatedly, circuit opens and returns graceful fallback (lead_score=null, error logged). Prevents cascading failures to FEAT-002 enrichment pipeline.
- **Asyncio timeout per practice**: Use `asyncio.wait_for(score_practice(id), timeout=5.0)` to enforce 5-second timeout. Catch TimeoutError, log in Score Breakdown, set lead_score=null. Fast-path check: if no enrichment data, return baseline score immediately without expensive calculations.
- **No automatic retries**: Manual rescore via CLI command instead of automatic retry queue. Simpler architecture, avoids DLQ complexity for MVP. Sales team triggers rescore after data corrections.

**Key Benefits:**
- Graceful degradation ensures scoring never blocks enrichment pipeline (no cascading failures)
- Multiplicative confidence penalties provide consistent, predictable score adjustments
- Circuit breaker prevents resource exhaustion from repeated failures
- Timeout enforcement maintains performance target (<100ms typical, <5s max)
- Manual rescore gives control to users without automatic retry complexity
- Preserves dual scoring (initial_score + lead_score) without version history overhead

**Considerations:**
- Circuit breaker adds dependency (pybreaker library) - but well-maintained, stable (1.3.0, 2024 release)
- Multiplicative penalties require careful testing to ensure intuitive behavior at edge cases (0 pts, max pts)
- Manual rescore requires CLI command implementation and user documentation
- No automatic recovery from scoring failures - requires human intervention for data correction

---

### Alternative Approaches Considered

#### Alternative 1: Additive Confidence Penalties with Automatic Retry Queue

- **Pros:**
  - Additive penalties simpler to understand (subtract fixed points for low confidence)
  - Automatic retry queue recovers from transient errors without manual intervention
  - DLQ pattern is battle-tested in message queue systems

- **Cons:**
  - Additive penalties less predictable across score ranges (10 point penalty has different impact on 20 vs 100 score)
  - Automatic retry adds significant complexity (queue management, retry strategy, backoff logic)
  - DLQ requires infrastructure (Redis/RabbitMQ) not needed for MVP
  - Risk of retry storms if errors systemic (circuit breaker safer)

- **Why not chosen:** Multiplicative penalties more consistent with research findings on scoring systems. Manual rescore via CLI sufficient for MVP - automatic retry is Phase 2 enhancement per PRD (line 1013).

#### Alternative 2: Full State Machine Library (python-statemachine) with State Versioning

- **Pros:**
  - Declarative state transitions with validation/guards
  - Graph visualization for debugging state flows
  - Type-safe state representation with enums
  - Built-in state persistence and history tracking

- **Cons:**
  - Overkill for simple state tracking (only 3 states: Pending/Completed/Failed)
  - Adds dependency and learning curve for team
  - Notion status field already provides state tracking UI
  - State versioning not required per PRD (Non-Goals line 57)

- **Why not chosen:** FEAT-003 state machine is simple (enrich → score, with error branches). Notion status field + application logic sufficient without full library. Idempotent transitions achieved by checking current state before updates. Save state machine library for more complex workflows (future lead routing).

---

## Trade-offs

### Performance vs. Complexity
**Analysis:** Graceful degradation with fast-path optimization (check enrichment data exists before calculation) achieves <100ms performance for baseline-only scenarios. Full calculation with all dimensions may approach 5-second timeout under load, but acceptable for auto-trigger (non-blocking). Trade-off: Simple timeout + fallback (low complexity) vs elaborate caching/memoization (high complexity, marginal benefit). **Decision:** Keep it simple - timeout + fallback sufficient for MVP.

### Fast Failure vs. Retry Logic
**Analysis:** Fast failure with circuit breaker (fail_max=5, no automatic retry) prevents resource exhaustion and cascading failures. Manual rescore via CLI gives control to users. Trade-off: Simplicity and control (fast failure) vs automatic recovery (retry logic). **Decision:** Fast failure for MVP - automatic retry is Phase 2 enhancement per PRD open questions (line 1012-1014).

### Simple State Tracking vs. Full State Machine
**Analysis:** Notion status field + application logic tracks 3 states (Pending/Completed/Failed) with idempotent transitions. Full state machine library (python-statemachine) adds validation, visualization, history but increases complexity. Trade-off: Minimal code (Notion field) vs type safety and features (state machine library). **Decision:** Use Notion field for MVP - revisit state machine library if state transitions become complex (e.g., lead routing with multiple stages).

### Immediate Scoring vs. Deferred Scoring
**Analysis:** Auto-trigger scoring immediately after enrichment (FEAT-002) provides real-time priority tier assignment for sales reps. Deferred scoring (batch job every N hours) reduces load but delays insights. Trade-off: Real-time visibility (immediate) vs. performance isolation (deferred). **Decision:** Immediate auto-trigger with timeout + circuit breaker - achieves real-time updates while protecting against cascading failures.

---

## Answers to Open Questions

### Question 1: How to calculate partial scores with missing enrichment data?

**Answer:** Use weighted scoring with graceful degradation: (1) Assign 0 points to missing components (not null, not default value). (2) Calculate total score with available dimensions only. (3) Apply confidence penalty (multiplicative: high=1.0x, medium=0.9x, low=0.7x) to practice_size_score only. (4) For completely unenriched practices (Scenario D), calculate baseline-only score (max 20 pts) and set Priority Tier = "Pending Enrichment". (5) Store score breakdown as JSON showing which components contributed.

**Confidence:** High

**Source:** Research Topic 1 (Graceful Degradation with Weighted Scoring), Stack Overflow weighted average with missing values, PRD Scenarios A-E (lines 76-221)

### Question 2: How should scoring failures be handled without cascading to FEAT-002?

**Answer:** Wrap scoring calls in PyBreaker circuit breaker (fail_max=5, reset_timeout=60s) with asyncio.wait_for() timeout (5 seconds per practice). On failure: (1) Log error in Score Breakdown field (JSON with error key). (2) Set lead_score=null. (3) Preserve enrichment_status (don't overwrite). (4) Return gracefully without blocking enrichment pipeline. (5) Manual rescore via CLI command when data corrected. Circuit breaker opens after 5 consecutive failures, preventing further calls until reset timeout.

**Confidence:** High

**Source:** Research Topic 2 (Circuit Breaker Pattern), Topic 4 (Asyncio Timeout Patterns), PRD Integration section (lines 549-621)

### Question 3: Best practices for implementing state machine in Python?

**Answer:** For FEAT-003's simple state tracking (3 states: Pending/Completed/Failed), use Notion status field + application logic without a state machine library. Ensure idempotent transitions by checking current state before allowing changes (e.g., only transition Pending → Completed if score calculation succeeds). Log state changes with timestamp for audit trail. If state transitions become complex (e.g., future lead routing with multiple stages), consider python-statemachine library for declarative syntax, validation, and type safety.

**Confidence:** High

**Source:** Research Topic 3 (Python State Machine Libraries), PRD State Machine diagram (lines 490-543)

### Question 4: How to maintain performance (<100ms) when handling partial/missing data?

**Answer:** Use fast-path optimization: (1) Check if enrichment data exists before starting calculation. If no enrichment, return baseline score immediately (fast-path: <10ms). (2) For full calculation, skip null checks by assigning 0 points to missing components (avoids conditional branching). (3) Enforce 5-second timeout per practice with asyncio.wait_for() to prevent runaway calculations. (4) Typical latency <100ms for full calculation, <5s max. (5) Monitor timeout frequency - alert if >5% of requests timeout (indicates performance degradation).

**Confidence:** High

**Source:** Research Topic 4 (Asyncio Timeout Patterns), PRD Performance Requirements (lines 622-627)

### Question 5: How do other systems handle initial vs final scoring?

**Answer:** Dual scoring systems use separate database columns for each score type (initial_score, lead_score) with clear purposes: initial for quick triage during ingestion, lead for comprehensive evaluation after enrichment. In FEAT-003, initial_score (0-25 from Google Maps) never changes (historical record), while lead_score (0-120 with full dimensions) is recalculated on manual rescore. Both stored in Notion main table without version history (Non-Goal per PRD line 57). Score breakdown stored as JSON in rich_text field showing components and confidence flags.

**Confidence:** Medium

**Source:** Research Topic 6 (Dual Scoring System Database Patterns), PRD Dual Scoring System section (lines 668-717)

---

## Resources

### Official Documentation
- **Python asyncio documentation**: https://docs.python.org/3/library/asyncio-task.html
- **NumPy documentation**: https://numpy.org/doc/stable/reference/generated/numpy.average.html
- **PyBreaker library**: https://pypi.org/project/pybreaker/

### Technical Articles
- **Super Fast Python - Asyncio Timeout Best Practices**: https://superfastpython.com/asyncio-timeout-best-practices/ (2024)
- **GeeksforGeeks - Graceful Degradation in Distributed Systems**: https://www.geeksforgeeks.org/system-design/graceful-degradation-in-distributed-systems/ (2024)
- **Medium - Circuit Breaker Pattern in Python Microservices**: https://medium.com/@abhinav.manoj1503/circuit-breaker-pattern-in-microservices-using-flask-cf19e9ed6147 (2024)
- **Better Stack - Complete Guide to Timeouts in Python**: https://betterstack.com/community/guides/scaling-python/python-timeouts/ (2024)

### Code Examples
- **Stack Overflow - Row-wise score with missing values**: https://stackoverflow.com/questions/58066225/row-wise-score-using-weights-for-a-subset-of-columns-with-missing-values
- **Stack Overflow - Pandas weighted average with missing values**: https://stackoverflow.com/questions/41782990/pandas-filling-missing-values-by-weighted-average-in-each-group
- **GitHub - PyBreaker Circuit Breaker Implementation**: https://github.com/danielfm/pybreaker
- **GitHub - Python Transitions State Machine**: https://github.com/pytransitions/transitions

### Community Resources
- **Redpanda Blog - Dead Letter Queue Best Practices**: https://www.redpanda.com/blog/reliable-message-processing-with-dead-letter-queue (2024)
- **DEV Community - State Machines in Practice**: https://dev.to/pragativerma18/state-machines-in-practice-implementing-solutions-for-real-challenges-3l76 (2023)
- **O'Reilly - Soft Computing Evaluation Logic**: https://www.oreilly.com/library/view/soft-computing-evaluation/9781119256458/c1-3.xhtml

---

## Archon Status

### Knowledge Base Queries
*Archon MCP was not available for this research session.*

### Recommendations for Archon
*Frameworks/docs to crawl for future features:*

1. **Python asyncio Official Documentation**
   - **Why:** Core library for async patterns used throughout FEAT-002 and FEAT-003. Essential for timeout, concurrency, and error handling patterns.
   - **URLs to crawl:**
     - https://docs.python.org/3/library/asyncio.html
     - https://docs.python.org/3/library/asyncio-task.html
     - https://docs.python.org/3/library/asyncio-exceptions.html
   - **Benefit:** Fast lookup for timeout patterns, wait_for() usage, exception handling in future async features.

2. **PyBreaker Circuit Breaker Documentation**
   - **Why:** Primary error recovery pattern for microservices integration. Likely needed for future features with external API calls.
   - **URLs to crawl:**
     - https://pypi.org/project/pybreaker/
     - https://github.com/danielfm/pybreaker
   - **Benefit:** Quick reference for circuit breaker configuration, event listeners, Redis backend integration.

3. **NumPy and Pandas Aggregation Functions**
   - **Why:** Used for scoring calculations, weighted averages, and data normalization. Core data science libraries for analytics features.
   - **URLs to crawl:**
     - https://numpy.org/doc/stable/reference/routines.statistics.html
     - https://pandas.pydata.org/docs/reference/groupby.html
   - **Benefit:** Fast lookup for aggregation patterns, missing data handling, weighted calculations in future analytics features.

4. **Notion API Documentation (if not already in Archon)**
   - **Why:** Primary database for project. Critical for all FEAT-XXX features.
   - **URLs to crawl:**
     - https://developers.notion.com/reference/intro
     - https://developers.notion.com/reference/database
   - **Benefit:** Quick reference for field types, query filters, update operations across all features.

---

## Next Steps

1. **Architecture Planning:** Use recommendations to design LeadScorer class with graceful degradation, circuit breaker integration for auto-trigger, and asyncio timeout enforcement.

2. **Technical Spike:** None required - patterns are well-established with mature libraries (pybreaker, asyncio). Proceed directly to planning.

3. **Proceed to Planning:** Run `/plan FEAT-003` with these research findings. Key design decisions:
   - Weighted scoring with multiplicative confidence penalties (0.7x, 0.9x, 1.0x)
   - PyBreaker circuit breaker for auto-trigger integration (fail_max=5, reset_timeout=60s)
   - Asyncio timeout per practice (5 seconds)
   - Manual rescore CLI command (no automatic retry queue for MVP)
   - Notion status field for simple state tracking (no state machine library)
   - Dual scoring preserved (initial_score + lead_score in same table)

---

**Research Complete:** ✅
**Ready for Planning:** Yes

**Implementation Notes:**
- Add pybreaker dependency to requirements.txt (version 1.3.0+)
- Create LeadScorer class with graceful degradation methods
- Integrate circuit breaker in FEAT-002 auto-trigger call
- Implement manual rescore CLI command in src/scoring/rescore_leads.py
- Write comprehensive tests for Scenarios A-E with circuit breaker/timeout edge cases
