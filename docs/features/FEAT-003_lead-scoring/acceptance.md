# Acceptance Criteria: FEAT-003 ICP Lead Scoring

**Feature ID:** FEAT-003
**Feature Name:** ICP Lead Scoring
**Version:** 1.0.0
**Last Updated:** 2025-11-04
**Status:** Planning

## Overview

This document defines testable acceptance criteria for the ICP Lead Scoring feature. All criteria are written in Given/When/Then format and organized by functional area. Each criterion must be independently testable with clear pass/fail conditions.

## Acceptance Criteria

### 1. Data Quality Scenarios

**AC-FEAT-003-001: Full Enrichment Data Scoring**
- **Given** a practice has complete enrichment data (vet count, services, reviews, decision maker, etc.)
- **When** the scoring algorithm runs
- **Then** all scoring components are calculated (practice size, call volume, technology, baseline, decision maker) and summed to produce a score between 0-120 points

**AC-FEAT-003-002: Partial Enrichment Data Scoring**
- **Given** a practice has enrichment data with some missing fields (e.g., no decision maker, no service details)
- **When** the scoring algorithm runs
- **Then** missing fields contribute 0 points to their respective components and the practice receives a reduced score based only on available data

**AC-FEAT-003-003: Low Confidence Enrichment Penalty**
- **Given** a practice has enrichment data marked with low confidence (confidence < 0.8)
- **When** the scoring algorithm runs
- **Then** the final score is multiplied by 0.7 (confidence penalty) and confidence flags are set in the Confidence Flags field

**AC-FEAT-003-004: Baseline-Only Scoring (No Enrichment)**
- **Given** a practice has only Google Maps data (no website enrichment)
- **When** the scoring algorithm runs
- **Then** only baseline components are scored (rating, reviews, has_website) with a maximum possible score of 40 points

**AC-FEAT-003-005: Null Enrichment Data Handling**
- **Given** a practice has enrichment_data = None or null
- **When** the scoring algorithm runs
- **Then** the system handles this gracefully without crashing and applies baseline-only scoring

### 2. Scoring Algorithm Correctness

**AC-FEAT-003-006: Practice Size Sweet Spot**
- **Given** a practice has 3-8 confirmed veterinarians
- **When** the practice size component is calculated
- **Then** the practice receives 25 points for practice size

**AC-FEAT-003-007: Practice Size Near Sweet Spot**
- **Given** a practice has exactly 2 veterinarians OR exactly 9 veterinarians
- **When** the practice size component is calculated
- **Then** the practice receives 15 points for practice size

**AC-FEAT-003-008: Practice Size Outside Sweet Spot**
- **Given** a practice has 1 veterinarian (solo) OR 10+ veterinarians (corporate)
- **When** the practice size component is calculated
- **Then** the practice receives 5 points for practice size

**AC-FEAT-003-009: Emergency 24/7 Services Bonus**
- **Given** a practice offers emergency services OR 24/7 availability
- **When** the call volume component is calculated
- **Then** the practice receives an additional 15 points

**AC-FEAT-003-010: Google Reviews Volume Scoring**
- **Given** a practice has Google reviews
- **When** the baseline component is calculated
- **Then** the practice receives:
  - 20 points if reviews >= 100
  - 12 points if 50 <= reviews < 100
  - 5 points if 20 <= reviews < 50
  - 0 points if reviews < 20

**AC-FEAT-003-011: Multiple Locations Bonus**
- **Given** a practice has multiple locations (location_count > 1 in enrichment data)
- **When** the call volume component is calculated
- **Then** the practice receives an additional 10 points

**AC-FEAT-003-012: High-Value Services Bonus**
- **Given** a practice offers boarding services OR specialty services
- **When** the call volume component is calculated
- **Then** the practice receives an additional 10 points

**AC-FEAT-003-013: Technology Adoption Scoring**
- **Given** a practice has technology features
- **When** the technology component is calculated
- **Then** the practice receives:
  - 10 points if online booking is available
  - 5 points if patient portal OR telemedicine is available (but not online booking)
  - 0 points if none of the above are available

**AC-FEAT-003-014: Google Rating Scoring**
- **Given** a practice has a Google rating
- **When** the baseline component is calculated
- **Then** the practice receives:
  - 6 points if rating >= 4.5
  - 4 points if 4.0 <= rating < 4.5
  - 2 points if 3.5 <= rating < 4.0
  - 0 points if rating < 3.5

**AC-FEAT-003-015: Website Presence Bonus**
- **Given** a practice has a website URL
- **When** the baseline component is calculated
- **Then** the practice receives an additional 4 points

**AC-FEAT-003-016: Decision Maker Contact Scoring**
- **Given** enrichment data includes decision maker information
- **When** the decision maker component is calculated
- **Then** the practice receives:
  - 10 points if both name AND email are present
  - 5 points if only name is present
  - 0 points if neither is present

### 3. Confidence Penalty Application

**AC-FEAT-003-017: High Confidence No Penalty**
- **Given** enrichment data has confidence >= 0.9
- **When** the final score is calculated
- **Then** no confidence penalty is applied (score × 1.0)

**AC-FEAT-003-018: Medium Confidence Penalty**
- **Given** enrichment data has 0.8 <= confidence < 0.9
- **When** the final score is calculated
- **Then** the score is multiplied by 0.9 (10% penalty)

**AC-FEAT-003-019: Low Confidence Penalty**
- **Given** enrichment data has confidence < 0.8
- **When** the final score is calculated
- **Then** the score is multiplied by 0.7 (30% penalty)

**AC-FEAT-003-020: Low Confidence Vet Count Flag**
- **Given** enrichment data has low confidence vet count (< 0.8)
- **When** scoring completes
- **Then** the Confidence Flags field includes "⚠️ Low Confidence Vet Count"

### 4. Priority Tier Classification

**AC-FEAT-003-021: Hot Lead Classification**
- **Given** a practice has a lead score between 80-120 points
- **When** priority tier is assigned
- **Then** the practice is classified as "🔥 Hot"

**AC-FEAT-003-022: Warm Lead Classification**
- **Given** a practice has a lead score between 50-79 points
- **When** priority tier is assigned
- **Then** the practice is classified as "🌡️ Warm"

**AC-FEAT-003-023: Cold Lead Classification**
- **Given** a practice has a lead score between 0-49 points
- **When** priority tier is assigned
- **Then** the practice is classified as "❄️ Cold"

**AC-FEAT-003-024: Solo Practice Out of Scope**
- **Given** a practice has 1 veterinarian AND a lead score < 20 points
- **When** priority tier is assigned
- **Then** the practice is classified as "⛔ Out of Scope"

**AC-FEAT-003-025: Corporate Practice Out of Scope**
- **Given** a practice has 10+ veterinarians AND a lead score < 20 points
- **When** priority tier is assigned
- **Then** the practice is classified as "⛔ Out of Scope"

**AC-FEAT-003-026: Pending Enrichment Classification**
- **Given** a practice has not been enriched yet (enrichment_data is null)
- **When** priority tier is assigned
- **Then** the practice is classified as "⏳ Pending Enrichment"

### 5. Score Breakdown JSON Structure

**AC-FEAT-003-027: Valid JSON Score Breakdown**
- **Given** scoring completes successfully
- **When** the Score Breakdown field is written to Notion
- **Then** the content is valid JSON (parseable by json.loads())

**AC-FEAT-003-028: Complete Component Scores**
- **Given** scoring completes successfully
- **When** the Score Breakdown JSON is examined
- **Then** it includes all scoring components: practice_size, call_volume, technology, baseline, decision_maker with their point values

**AC-FEAT-003-029: Confidence Penalty Details**
- **Given** a confidence penalty was applied (confidence < 0.9)
- **When** the Score Breakdown JSON is examined
- **Then** it includes confidence_penalty details with original score, penalty multiplier, and final score

**AC-FEAT-003-030: Missing Field Notes**
- **Given** some enrichment fields are missing (e.g., no decision maker)
- **When** the Score Breakdown JSON is examined
- **Then** it includes notes for missing fields (e.g., "Decision Maker: Not found (0 pts)")

### 6. Error Handling

**AC-FEAT-003-031: Scoring Error Logging**
- **Given** an error occurs during scoring calculation
- **When** the error is caught
- **Then** the error details are logged to the Score Breakdown field as a JSON error object

**AC-FEAT-003-032: Null Lead Score on Failure**
- **Given** scoring fails with an unrecoverable error
- **When** the Notion record is updated
- **Then** the Lead Score field is set to null (not 0, not previous value)

**AC-FEAT-003-033: Failed Scoring Status**
- **Given** scoring fails with an error
- **When** the Notion record is updated
- **Then** the Scoring Status field is set to "Failed"

**AC-FEAT-003-034: Enrichment Status Preservation**
- **Given** scoring fails after successful enrichment
- **When** the Notion record is updated
- **Then** the Enrichment Status remains "Completed" (not reverted or changed)

**AC-FEAT-003-035: Scoring Timeout Enforcement**
- **Given** scoring for a single practice takes longer than 5 seconds
- **When** the timeout is reached
- **Then** an asyncio.TimeoutError is raised and the practice receives Scoring Status="Failed"

**AC-FEAT-003-036: Auto-Trigger Failure Isolation**
- **Given** auto-triggered scoring fails for a practice
- **When** the error is handled
- **Then** the failure is logged but does not propagate back to FEAT-002 enrichment pipeline

**AC-FEAT-003-037: Circuit Breaker Opens**
- **Given** 5 consecutive scoring failures occur
- **When** the circuit breaker threshold is reached
- **Then** the circuit breaker opens and subsequent scoring requests are rejected immediately

**AC-FEAT-003-038: Circuit Breaker Reset**
- **Given** the circuit breaker is open
- **When** 60 seconds elapse with no new requests
- **Then** the circuit breaker resets to closed state and allows scoring requests again

### 7. Dual Scoring System

**AC-FEAT-003-039: Initial Score Preservation**
- **Given** a practice has an existing initial_score value
- **When** FEAT-003 scoring runs
- **Then** the initial_score field is never overwritten or modified

**AC-FEAT-003-040: Independent Lead Score**
- **Given** a practice is scored by FEAT-003
- **When** the lead_score is calculated
- **Then** it is computed independently of any initial_score value and stored separately

**AC-FEAT-003-041: Both Scores Visible**
- **Given** a practice has both initial_score and lead_score values
- **When** viewed in Notion
- **Then** both fields are visible and display their respective values

**AC-FEAT-003-042: Priority Tier from Lead Score**
- **Given** a practice has both initial_score and lead_score
- **When** priority tier is determined
- **Then** the tier is based on lead_score (not initial_score)

### 8. Integration with FEAT-002

**AC-FEAT-003-043: Auto-Trigger Enabled**
- **Given** auto_trigger_scoring=true in FEAT-002 configuration
- **When** website enrichment completes
- **Then** FEAT-003 scoring is automatically triggered for the practice

**AC-FEAT-003-044: Auto-Trigger Disabled**
- **Given** auto_trigger_scoring=false in FEAT-002 configuration
- **When** website enrichment completes
- **Then** FEAT-003 scoring is NOT triggered and the practice remains in "Not Scored" status

**AC-FEAT-003-045: Receives Enrichment Data**
- **Given** FEAT-002 completes enrichment for a practice
- **When** FEAT-003 scoring is triggered
- **Then** scoring receives the complete enrichment_data dictionary from FEAT-002

**AC-FEAT-003-046: Handles Null Enrichment Data**
- **Given** FEAT-002 passes enrichment_data=None to FEAT-003
- **When** scoring processes the practice
- **Then** baseline-only scoring is applied without errors

### 9. Manual Rescore Command

**AC-FEAT-003-047: Rescore All Practices**
- **Given** the command `python main.py --rescore all` is executed
- **When** the scoring system runs
- **Then** all practices in the database are rescored regardless of current status

**AC-FEAT-003-048: Rescore Single Practice**
- **Given** the command `python main.py --rescore <practice-id>` is executed
- **When** the scoring system runs
- **Then** only the specified practice is rescored

**AC-FEAT-003-049: Rescore Unenriched Practice**
- **Given** manual rescore is triggered for a practice without enrichment data
- **When** scoring runs
- **Then** baseline-only scoring is applied successfully

**AC-FEAT-003-050: Rescore Enriched Practice**
- **Given** manual rescore is triggered for a practice with complete enrichment data
- **When** scoring runs
- **Then** full scoring algorithm is applied successfully

**AC-FEAT-003-051: Rescore Not Found Handling**
- **Given** manual rescore is triggered for a non-existent practice ID
- **When** the system attempts to load the practice
- **Then** an appropriate error message is logged and the process exits cleanly (no crash)

### 10. Performance Requirements

**AC-FEAT-003-052: Single Practice Typical Performance**
- **Given** a practice with high-confidence enrichment data
- **When** scoring is executed
- **Then** the scoring completes in less than 100ms

**AC-FEAT-003-053: Single Practice Timeout Enforcement**
- **Given** scoring is executed for any practice
- **When** execution time is measured
- **Then** scoring never exceeds 5000ms (timeout is enforced)

**AC-FEAT-003-054: Batch Scoring Performance**
- **Given** 150 practices need to be scored
- **When** batch scoring is executed
- **Then** all practices are scored in less than 15 seconds total

**AC-FEAT-003-055: Baseline-Only Performance**
- **Given** a practice with only Google Maps data (no enrichment)
- **When** baseline-only scoring is executed
- **Then** scoring completes in less than 10ms

### 11. State Management

**AC-FEAT-003-056: Scoring Status Update Success**
- **Given** scoring completes successfully for a practice
- **When** the Notion record is updated
- **Then** the Scoring Status field changes from "Not Scored" to "Scored"

**AC-FEAT-003-057: Scoring Status Update Failure**
- **Given** scoring fails for a practice
- **When** the Notion record is updated
- **Then** the Scoring Status field is set to "Failed"

**AC-FEAT-003-058: Confidence Flags Set**
- **Given** low-confidence data is detected during scoring
- **When** the Notion record is updated
- **Then** appropriate confidence flags are added to the Confidence Flags multi-select field

**AC-FEAT-003-059: Idempotent Scoring**
- **Given** the same practice with identical enrichment data is scored twice
- **When** both scoring runs complete
- **Then** both runs produce the exact same lead_score value

### 12. Notion Field Updates

**AC-FEAT-003-060: Lead Score Field Update**
- **Given** scoring completes successfully
- **When** Notion is updated
- **Then** the Lead Score field (number, 0-120, nullable) contains the calculated score

**AC-FEAT-003-061: Priority Tier Field Update**
- **Given** scoring completes successfully
- **When** Notion is updated
- **Then** the Priority Tier field (select, nullable) contains the appropriate tier (Hot/Warm/Cold/Out of Scope/Pending)

**AC-FEAT-003-062: Score Breakdown Field Update**
- **Given** scoring completes successfully
- **When** Notion is updated
- **Then** the Score Breakdown field (rich_text) contains valid JSON with all component scores

**AC-FEAT-003-063: Confidence Flags Field Update**
- **Given** low-confidence data is detected
- **When** Notion is updated
- **Then** the Confidence Flags field (multi_select) contains appropriate warning flags

**AC-FEAT-003-064: Scoring Status Field Update**
- **Given** scoring completes (success or failure)
- **When** Notion is updated
- **Then** the Scoring Status field (select) reflects the current state (Scored/Failed)

**AC-FEAT-003-065: Sales Workflow Field Preservation**
- **Given** a practice has existing sales workflow data (Status, Assigned To, Call Notes)
- **When** scoring updates the Notion record
- **Then** all sales workflow fields remain unchanged

**AC-FEAT-003-066: Enrichment Field Preservation**
- **Given** a practice has enrichment data (Confirmed Vet Count, Decision Maker Name, etc.)
- **When** scoring updates the Notion record
- **Then** all enrichment fields remain unchanged

### 13. Configuration Management

**AC-FEAT-003-067: Load ScoringConfig**
- **Given** config.json contains a scoring section
- **When** the scoring system initializes
- **Then** the ScoringConfig is loaded successfully with all parameters

**AC-FEAT-003-068: Validate Sweet Spot Range**
- **Given** ScoringConfig is loaded
- **When** configuration validation runs
- **Then** sweet_spot_min <= sweet_spot_max (raises error if invalid)

**AC-FEAT-003-069: Validate Timeout Positive**
- **Given** ScoringConfig is loaded
- **When** configuration validation runs
- **Then** timeout > 0 (raises error if zero or negative)

**AC-FEAT-003-070: Validate Confidence Multipliers**
- **Given** ScoringConfig is loaded
- **When** configuration validation runs
- **Then** all confidence multipliers (high, medium, low) are between 0.0 and 1.0 inclusive

## Summary

**Total Acceptance Criteria:** 70

**Coverage:**
- Data Quality Scenarios: 5 criteria
- Scoring Algorithm Correctness: 11 criteria
- Confidence Penalty Application: 4 criteria
- Priority Tier Classification: 6 criteria
- Score Breakdown JSON Structure: 4 criteria
- Error Handling: 8 criteria
- Dual Scoring System: 4 criteria
- Integration with FEAT-002: 4 criteria
- Manual Rescore Command: 5 criteria
- Performance Requirements: 4 criteria
- State Management: 4 criteria
- Notion Field Updates: 7 criteria
- Configuration Management: 4 criteria

**Traceability:**
- All criteria map to PRD user stories and edge case scenarios
- All criteria map to architecture decisions and component specifications
- All criteria are independently testable with clear pass/fail conditions
- All criteria cover both happy path and error scenarios

## Next Steps

1. Review acceptance criteria with stakeholders
2. Create test stubs in `tests/features/scoring/` directory
3. Implement scoring system following TDD approach
4. Validate all criteria during implementation
5. Update manual testing guide with test scenarios

---

**Document Status:** Complete
**Review Required:** Yes
**Implementation Ready:** Yes
