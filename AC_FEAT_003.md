# Acceptance Criteria: FEAT-003 ICP Lead Scoring

## Data Quality Scenarios
- **AC-FEAT-003-001:** Full Enrichment Data Scoring - Given a practice has complete enrichment data (vet count, services, reviews, decision maker, etc.), when the scoring algorithm runs, then all scoring components are calculated and summed to produce a score between 0-120 points
- **AC-FEAT-003-002:** Partial Enrichment Data Scoring - Given a practice has enrichment data with some missing fields, when the scoring algorithm runs, then missing fields contribute 0 points and the practice receives a reduced score based only on available data
- **AC-FEAT-003-003:** Low Confidence Enrichment Penalty - Given a practice has enrichment data marked with low confidence (< 0.8), when the scoring algorithm runs, then the final score is multiplied by 0.7 and confidence flags are set
- **AC-FEAT-003-004:** Baseline-Only Scoring (No Enrichment) - Given a practice has only Google Maps data, when the scoring algorithm runs, then only baseline components are scored with a maximum of 40 points
- **AC-FEAT-003-005:** Null Enrichment Data Handling - Given a practice has enrichment_data = None, when the scoring algorithm runs, then the system handles this gracefully and applies baseline-only scoring

## Scoring Algorithm Correctness
- **AC-FEAT-003-006:** Practice Size Sweet Spot - Given a practice has 3-8 confirmed veterinarians, when practice size is calculated, then the practice receives 25 points
- **AC-FEAT-003-007:** Practice Size Near Sweet Spot - Given a practice has exactly 2 or 9 veterinarians, when practice size is calculated, then the practice receives 15 points
- **AC-FEAT-003-008:** Practice Size Outside Sweet Spot - Given a practice has 1 or 10+ veterinarians, when practice size is calculated, then the practice receives 5 points
- **AC-FEAT-003-009:** Emergency 24/7 Services Bonus - Given a practice offers emergency services or 24/7 availability, when call volume is calculated, then the practice receives an additional 15 points
- **AC-FEAT-003-010:** Google Reviews Volume Scoring - Given a practice has Google reviews, when baseline is calculated, then the practice receives 20/12/5/0 points based on volume (100+/50-99/20-49/<20)
- **AC-FEAT-003-011:** Multiple Locations Bonus - Given a practice has multiple locations (location_count > 1), when call volume is calculated, then the practice receives an additional 10 points
- **AC-FEAT-003-012:** High-Value Services Bonus - Given a practice offers boarding or specialty services, when call volume is calculated, then the practice receives an additional 10 points
- **AC-FEAT-003-013:** Technology Adoption Scoring - Given a practice has technology features, when technology component is calculated, then the practice receives 10 points for online booking or 5 points for portal/telemedicine
- **AC-FEAT-003-014:** Google Rating Scoring - Given a practice has a Google rating, when baseline is calculated, then the practice receives 6/4/2/0 points based on rating (4.5+/4.0-4.4/3.5-3.9/<3.5)
- **AC-FEAT-003-015:** Website Presence Bonus - Given a practice has a website URL, when baseline is calculated, then the practice receives an additional 4 points
- **AC-FEAT-003-016:** Decision Maker Contact Scoring - Given enrichment includes decision maker info, when decision maker component is calculated, then the practice receives 10 points for name+email, 5 points for name only, or 0 points

## Confidence Penalty Application
- **AC-FEAT-003-017:** High Confidence No Penalty - Given enrichment confidence >= 0.9, when final score is calculated, then no confidence penalty is applied (score × 1.0)
- **AC-FEAT-003-018:** Medium Confidence Penalty - Given enrichment confidence 0.8-0.89, when final score is calculated, then the score is multiplied by 0.9
- **AC-FEAT-003-019:** Low Confidence Penalty - Given enrichment confidence < 0.8, when final score is calculated, then the score is multiplied by 0.7
- **AC-FEAT-003-020:** Low Confidence Vet Count Flag - Given enrichment has low confidence vet count, when scoring completes, then Confidence Flags includes "⚠️ Low Confidence Vet Count"

## Priority Tier Classification
- **AC-FEAT-003-021:** Hot Lead Classification - Given a practice has lead score 80-120, when priority tier is assigned, then the practice is classified as "🔥 Hot"
- **AC-FEAT-003-022:** Warm Lead Classification - Given a practice has lead score 50-79, when priority tier is assigned, then the practice is classified as "🌡️ Warm"
- **AC-FEAT-003-023:** Cold Lead Classification - Given a practice has lead score 0-49, when priority tier is assigned, then the practice is classified as "❄️ Cold"
- **AC-FEAT-003-024:** Solo Practice Out of Scope - Given a practice has 1 vet and score < 20, when priority tier is assigned, then the practice is classified as "⛔ Out of Scope"
- **AC-FEAT-003-025:** Corporate Practice Out of Scope - Given a practice has 10+ vets and score < 20, when priority tier is assigned, then the practice is classified as "⛔ Out of Scope"
- **AC-FEAT-003-026:** Pending Enrichment Classification - Given a practice has not been enriched yet, when priority tier is assigned, then the practice is classified as "⏳ Pending Enrichment"

## Score Breakdown JSON Structure
- **AC-FEAT-003-027:** Valid JSON Score Breakdown - Given scoring completes successfully, when Score Breakdown is written to Notion, then the content is valid JSON
- **AC-FEAT-003-028:** Complete Component Scores - Given scoring completes successfully, when Score Breakdown JSON is examined, then it includes all components: practice_size, call_volume, technology, baseline, decision_maker
- **AC-FEAT-003-029:** Confidence Penalty Details - Given a confidence penalty was applied, when Score Breakdown JSON is examined, then it includes penalty details with original score, multiplier, and final score
- **AC-FEAT-003-030:** Missing Field Notes - Given some enrichment fields are missing, when Score Breakdown JSON is examined, then it includes notes for missing fields

## Error Handling
- **AC-FEAT-003-031:** Scoring Error Logging - Given an error occurs during scoring, when the error is caught, then error details are logged to Score Breakdown as JSON
- **AC-FEAT-003-032:** Null Lead Score on Failure - Given scoring fails with unrecoverable error, when Notion is updated, then Lead Score is set to null
- **AC-FEAT-003-033:** Failed Scoring Status - Given scoring fails with error, when Notion is updated, then Scoring Status is set to "Failed"
- **AC-FEAT-003-034:** Enrichment Status Preservation - Given scoring fails after successful enrichment, when Notion is updated, then Enrichment Status remains "Completed"
- **AC-FEAT-003-035:** Scoring Timeout Enforcement - Given scoring takes longer than 5 seconds, when timeout is reached, then asyncio.TimeoutError is raised and status becomes "Failed"
- **AC-FEAT-003-036:** Auto-Trigger Failure Isolation - Given auto-triggered scoring fails, when error is handled, then failure is logged but does not propagate to FEAT-002
- **AC-FEAT-003-037:** Circuit Breaker Opens - Given 5 consecutive scoring failures occur, when threshold is reached, then circuit breaker opens and rejects subsequent requests
- **AC-FEAT-003-038:** Circuit Breaker Reset - Given circuit breaker is open, when 60 seconds elapse with no requests, then circuit breaker resets to closed state

## Dual Scoring System
- **AC-FEAT-003-039:** Initial Score Preservation - Given a practice has existing initial_score, when FEAT-003 scoring runs, then initial_score is never overwritten
- **AC-FEAT-003-040:** Independent Lead Score - Given a practice is scored by FEAT-003, when lead_score is calculated, then it is computed independently of initial_score
- **AC-FEAT-003-041:** Both Scores Visible - Given a practice has both initial_score and lead_score, when viewed in Notion, then both fields are visible
- **AC-FEAT-003-042:** Priority Tier from Lead Score - Given a practice has both scores, when priority tier is determined, then tier is based on lead_score (not initial_score)

## Integration with FEAT-002
- **AC-FEAT-003-043:** Auto-Trigger Enabled - Given auto_trigger_scoring=true in FEAT-002 config, when enrichment completes, then FEAT-003 scoring is automatically triggered
- **AC-FEAT-003-044:** Auto-Trigger Disabled - Given auto_trigger_scoring=false in FEAT-002 config, when enrichment completes, then FEAT-003 scoring is NOT triggered
- **AC-FEAT-003-045:** Receives Enrichment Data - Given FEAT-002 completes enrichment, when FEAT-003 is triggered, then scoring receives complete enrichment_data dictionary
- **AC-FEAT-003-046:** Handles Null Enrichment Data - Given FEAT-002 passes enrichment_data=None, when scoring processes practice, then baseline-only scoring is applied without errors

## Manual Rescore Command
- **AC-FEAT-003-047:** Rescore All Practices - Given command `--rescore all` is executed, when scoring system runs, then all practices are rescored regardless of status
- **AC-FEAT-003-048:** Rescore Single Practice - Given command `--rescore <practice-id>` is executed, when scoring runs, then only specified practice is rescored
- **AC-FEAT-003-049:** Rescore Unenriched Practice - Given manual rescore for practice without enrichment, when scoring runs, then baseline-only scoring is applied successfully
- **AC-FEAT-003-050:** Rescore Enriched Practice - Given manual rescore for practice with complete enrichment, when scoring runs, then full scoring algorithm is applied successfully
- **AC-FEAT-003-051:** Rescore Not Found Handling - Given manual rescore for non-existent practice ID, when system attempts to load practice, then error is logged and process exits cleanly

## Performance Requirements
- **AC-FEAT-003-052:** Single Practice Typical Performance - Given a practice with high-confidence enrichment, when scoring is executed, then scoring completes in less than 100ms
- **AC-FEAT-003-053:** Single Practice Timeout Enforcement - Given scoring is executed for any practice, when execution time is measured, then scoring never exceeds 5000ms
- **AC-FEAT-003-054:** Batch Scoring Performance - Given 150 practices need scoring, when batch scoring is executed, then all practices are scored in less than 15 seconds
- **AC-FEAT-003-055:** Baseline-Only Performance - Given a practice with only Google Maps data, when baseline-only scoring is executed, then scoring completes in less than 10ms

## State Management
- **AC-FEAT-003-056:** Scoring Status Update Success - Given scoring completes successfully, when Notion is updated, then Scoring Status changes from "Not Scored" to "Scored"
- **AC-FEAT-003-057:** Scoring Status Update Failure - Given scoring fails, when Notion is updated, then Scoring Status is set to "Failed"
- **AC-FEAT-003-058:** Confidence Flags Set - Given low-confidence data is detected, when Notion is updated, then appropriate confidence flags are added to Confidence Flags field
- **AC-FEAT-003-059:** Idempotent Scoring - Given same practice with identical enrichment is scored twice, when both runs complete, then both produce exact same lead_score

## Notion Field Updates
- **AC-FEAT-003-060:** Lead Score Field Update - Given scoring completes successfully, when Notion is updated, then Lead Score field (number, 0-120, nullable) contains calculated score
- **AC-FEAT-003-061:** Priority Tier Field Update - Given scoring completes successfully, when Notion is updated, then Priority Tier field (select, nullable) contains appropriate tier
- **AC-FEAT-003-062:** Score Breakdown Field Update - Given scoring completes successfully, when Notion is updated, then Score Breakdown field (rich_text) contains valid JSON with all components
- **AC-FEAT-003-063:** Confidence Flags Field Update - Given low-confidence data is detected, when Notion is updated, then Confidence Flags field (multi_select) contains warning flags
- **AC-FEAT-003-064:** Scoring Status Field Update - Given scoring completes (success or failure), when Notion is updated, then Scoring Status field reflects current state
- **AC-FEAT-003-065:** Sales Workflow Field Preservation - Given a practice has existing sales workflow data, when scoring updates Notion, then all sales workflow fields remain unchanged
- **AC-FEAT-003-066:** Enrichment Field Preservation - Given a practice has enrichment data, when scoring updates Notion, then all enrichment fields remain unchanged

## Configuration Management
- **AC-FEAT-003-067:** Load ScoringConfig - Given config.json contains scoring section, when scoring system initializes, then ScoringConfig is loaded successfully
- **AC-FEAT-003-068:** Validate Sweet Spot Range - Given ScoringConfig is loaded, when validation runs, then sweet_spot_min <= sweet_spot_max (raises error if invalid)
- **AC-FEAT-003-069:** Validate Timeout Positive - Given ScoringConfig is loaded, when validation runs, then timeout > 0 (raises error if zero or negative)
- **AC-FEAT-003-070:** Validate Confidence Multipliers - Given ScoringConfig is loaded, when validation runs, then all confidence multipliers are between 0.0 and 1.0 inclusive
