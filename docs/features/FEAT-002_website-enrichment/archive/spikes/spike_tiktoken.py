#!/usr/bin/env python3
"""
Spike Test 6: tiktoken Token Counting Accuracy

Tests tiktoken token counting vs actual OpenAI API usage.

Success Criteria:
- tiktoken estimates within 5% of actual API usage
- Variance consistent across different text lengths
"""

import os
import tiktoken
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_tiktoken_accuracy():
    """Test tiktoken token counting vs actual API usage."""

    print("="*60)
    print("TIKTOKEN TOKEN COUNTING ACCURACY TEST")
    print("="*60)

    # Get model from environment
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    print(f"Model: {model}")
    print(f"Encoding: o200k_base")
    print()

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    encoding = tiktoken.encoding_for_model(model)

    # 5 sample texts of varying lengths
    samples = [
        ("Short", "Boston Veterinary Clinic provides excellent care."),
        ("Medium", "Our team: Dr. Smith, Dr. Johnson, Dr. Lee. Services: 24/7 emergency, surgery, dental, wellness exams. We have been serving Boston since 1985."),
        ("Long", "Boston Veterinary Clinic - Serving Boston Since 1985\n\nOur Team:\n- Dr. Sarah Johnson, DVM (Owner) - sjohnson@bostonvet.com\n- Dr. Michael Chen, DVM\n- Dr. Emily Rodriguez, DVM\n\nServices:\n- 24/7 Emergency Care\n- Surgery, Dental, Wellness Exams\n- Online Appointment Booking Available\n- Patient Portal for Medical Records\n\nAwards:\n- AAHA Accredited Practice\n- Dr. Johnson named Boston Magazine Best Vet 2024\n- Fear Free Certified\n\nRecent News:\n- Opened 2nd location in Newton (October 2024)\n\nWe are committed to providing compassionate care for your pets."),
        ("Very Long", ("About Us " * 100) + "\n\n" + ("Our Services include emergency care, surgery, dental work, and wellness programs. " * 50)),
        ("Max Length", ("Veterinary Practice Information: " * 200))
    ]

    results = []
    total_cost = 0.0

    for name, text in samples:
        print(f"{'='*60}")
        print(f"Test: {name}")
        print(f"{'='*60}")

        # tiktoken estimate
        tiktoken_count = len(encoding.encode(text))
        print(f"Text length: {len(text)} chars")
        print(f"tiktoken estimate: {tiktoken_count} tokens")

        # Actual API call
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": text}],
                max_tokens=10  # Minimal output to test input tokens only
            )

            actual_input = response.usage.prompt_tokens
            actual_output = response.usage.completion_tokens
            actual_total = response.usage.total_tokens

            # Calculate variance
            variance = abs(tiktoken_count - actual_input) / actual_input * 100 if actual_input > 0 else 0

            # Calculate cost
            cost = (actual_input * 0.15 / 1_000_000) + (actual_output * 0.60 / 1_000_000)
            total_cost += cost

            results.append({
                "name": name,
                "tiktoken": tiktoken_count,
                "actual_input": actual_input,
                "actual_output": actual_output,
                "variance_pct": variance,
                "cost": cost
            })

            print(f"Actual API usage: {actual_input} input + {actual_output} output = {actual_total} total")
            print(f"Variance: {variance:.2f}%")
            print(f"Cost: ${cost:.6f}")

            # Check if variance is acceptable
            if variance <= 5.0:
                print(f"✅ Within 5% tolerance")
            else:
                print(f"⚠️  Exceeds 5% tolerance")

        except Exception as e:
            print(f"❌ API call failed: {e}")
            results.append({
                "name": name,
                "tiktoken": tiktoken_count,
                "error": str(e)
            })

        print()

    # Summary
    print("="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total tests: {len(samples)}")
    print(f"Successful: {sum(1 for r in results if 'error' not in r)}")
    print(f"Failed: {sum(1 for r in results if 'error' in r)}")
    print(f"Total cost: ${total_cost:.6f}")
    print()

    # Calculate average variance (excluding errors)
    valid_results = [r for r in results if 'error' not in r]
    if valid_results:
        avg_variance = sum(r["variance_pct"] for r in valid_results) / len(valid_results)
        max_variance = max(r["variance_pct"] for r in valid_results)
        min_variance = min(r["variance_pct"] for r in valid_results)

        print(f"Variance Statistics:")
        print(f"  Average: {avg_variance:.2f}%")
        print(f"  Min: {min_variance:.2f}%")
        print(f"  Max: {max_variance:.2f}%")
        print()

    # Check success criteria
    print("SUCCESS CRITERIA VALIDATION:")
    print("-"*60)

    all_successful = all('error' not in r for r in results)
    avg_within_5pct = valid_results and avg_variance <= 5.0

    criteria = [
        ("All API calls successful", all_successful),
        ("Average variance ≤5%", avg_within_5pct)
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
        print("   tiktoken is accurate enough for cost estimation.")
    else:
        print("\n❌ SOME CRITERIA FAILED")
        if not avg_within_5pct and valid_results:
            print(f"   Average variance: {avg_variance:.2f}% (target: ≤5%)")
            print("   Recommendation: Add 10-15% buffer to cost estimates")

    print("="*60)

    return all_passed

if __name__ == "__main__":
    try:
        success = test_tiktoken_accuracy()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
