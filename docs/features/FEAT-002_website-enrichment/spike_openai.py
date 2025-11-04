#!/usr/bin/env python3
"""
Spike Test 2: OpenAI Structured Outputs

Tests OpenAI beta.chat.completions.parse() with gpt-4o-mini and Pydantic models.

Success Criteria:
- beta.chat.completions.parse() method works
- Returns valid Pydantic objects
- No JSON parsing errors
- Cost per extraction ≤$0.001
"""

import os
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define VetPracticeExtraction model (simplified for spike)
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
    online_booking: bool = False
    patient_portal: bool = False
    personalization_context: List[str] = Field(default_factory=list, max_length=3)
    awards_accreditations: List[str] = Field(default_factory=list)

def test_openai_structured_outputs():
    """Test OpenAI structured outputs with sample vet website data."""

    # Sample website texts (from real patterns)
    sample_texts = [
        {
            "name": "Large practice with full details",
            "text": """
Boston Veterinary Clinic - Serving Boston Since 1985

Our Team:
- Dr. Sarah Johnson, DVM (Owner) - sjohnson@bostonvet.com - (617) 555-0100
- Dr. Michael Chen, DVM
- Dr. Emily Rodriguez, DVM

Services:
- 24/7 Emergency Care
- Surgery, Dental, Wellness Exams
- Online Appointment Booking Available
- Patient Portal for Medical Records

Awards:
- AAHA Accredited Practice
- Dr. Johnson named Boston Magazine Best Vet 2024
- Fear Free Certified

Recent News:
- Opened 2nd location in Newton (October 2024)
            """,
            "expected": {
                "vet_count": 3,
                "confidence": "high",
                "has_email": True,
                "emergency": True,
                "online_booking": True,
                "personalization": True
            }
        },
        {
            "name": "Small practice with minimal info",
            "text": """
Newton Animal Hospital

Welcome to our practice! We provide comprehensive veterinary care.

Services: Wellness exams, vaccinations, surgery

Contact: (617) 555-0200
            """,
            "expected": {
                "vet_count": None,
                "confidence": "low",
                "has_email": False,
                "emergency": False,
                "online_booking": False
            }
        },
        {
            "name": "Medium practice with decision maker",
            "text": """
Cambridge Vet Clinic

Meet Our Team:
Dr. Amanda Wilson - Practice Owner
Dr. James Lee - Associate Veterinarian

We offer:
- General wellness care
- Surgery and dental services
- Book online at cambridgevet.com/booking

Contact Practice Manager: manager@cambridgevet.com
            """,
            "expected": {
                "vet_count": 2,
                "confidence": "high",
                "has_email": True,
                "emergency": False,
                "online_booking": True
            }
        }
    ]

    print("="*60)
    print("OPENAI STRUCTURED OUTPUTS TEST")
    print("="*60)
    print(f"Model: gpt-4o-mini")
    print(f"Method: beta.chat.completions.parse()")
    print()

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    results = []
    total_cost = 0.0

    for i, sample in enumerate(sample_texts, 1):
        print(f"{'='*60}")
        print(f"Test {i}: {sample['name']}")
        print(f"{'='*60}")
        print()

        try:
            # Test structured output extraction
            response = client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Extract veterinary practice data into structured JSON. Only include information explicitly stated in the text."},
                    {"role": "user", "content": sample["text"]}
                ],
                response_format=VetPracticeExtraction,
                temperature=0.1
            )

            # Validate response
            extraction = response.choices[0].message.parsed

            # Calculate cost
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = (input_tokens * 0.15 / 1_000_000) + (output_tokens * 0.60 / 1_000_000)
            total_cost += cost

            print(f"✅ Extraction successful")
            print(f"   Tokens: {input_tokens} input + {output_tokens} output")
            print(f"   Cost: ${cost:.6f}")
            print()
            print(f"Extracted Data:")
            print(f"  Vet Count: {extraction.vet_count_total} ({extraction.vet_count_confidence})")
            if extraction.decision_maker:
                print(f"  Decision Maker: {extraction.decision_maker.name} ({extraction.decision_maker.role})")
                print(f"  Email: {extraction.decision_maker.email}")
            print(f"  24/7 Emergency: {extraction.emergency_24_7}")
            print(f"  Online Booking: {extraction.online_booking}")
            print(f"  Patient Portal: {extraction.patient_portal}")
            print(f"  Personalization: {extraction.personalization_context}")
            print(f"  Awards: {extraction.awards_accreditations}")
            print()

            # Verify against expectations
            expected = sample["expected"]
            checks = []

            if expected.get("vet_count") is not None:
                checks.append(("Vet count match", extraction.vet_count_total == expected["vet_count"]))

            if expected.get("has_email"):
                has_email = extraction.decision_maker and extraction.decision_maker.email is not None
                checks.append(("Email found", has_email))

            checks.append(("Emergency services", extraction.emergency_24_7 == expected.get("emergency", False)))
            checks.append(("Online booking", extraction.online_booking == expected.get("online_booking", False)))

            all_passed = all(passed for _, passed in checks)

            print("Validation:")
            for check, passed in checks:
                icon = "✅" if passed else "⚠️ "
                print(f"  {icon} {check}")

            results.append({
                "test": sample["name"],
                "success": True,
                "cost": cost,
                "all_checks_passed": all_passed
            })

        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "test": sample["name"],
                "success": False,
                "error": str(e)
            })

        print()

    # Summary
    print("="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total tests: {len(sample_texts)}")
    print(f"Successful: {sum(1 for r in results if r.get('success'))}")
    print(f"Failed: {sum(1 for r in results if not r.get('success'))}")
    print(f"Total cost: ${total_cost:.6f}")
    print(f"Average cost per extraction: ${total_cost / len(sample_texts):.6f}")
    print()

    # Check success criteria
    print("SUCCESS CRITERIA VALIDATION:")
    print("-"*60)

    avg_cost = total_cost / len(sample_texts)
    all_successful = all(r.get("success") for r in results)

    criteria = [
        ("beta.chat.completions.parse() works", all_successful),
        ("All responses are valid Pydantic objects", all_successful),
        ("No JSON parsing errors", all_successful),
        ("Average cost ≤$0.001 per extraction", avg_cost <= 0.001)
    ]

    all_passed = True
    for criterion, passed in criteria:
        icon = "✅" if passed else "❌"
        print(f"{icon} {criterion}")
        if not passed:
            all_passed = False

    print("="*60)

    if all_passed:
        print("\n✅ ALL CRITERIA PASSED!")
        print("   OpenAI structured outputs are ready for FEAT-002.")
    else:
        print("\n❌ SOME CRITERIA FAILED")
        print("   Review results and adjust configuration.")

    print("="*60)

    return all_passed

if __name__ == "__main__":
    try:
        success = test_openai_structured_outputs()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
