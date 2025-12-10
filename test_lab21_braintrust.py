"""
Lab 21 Verification Test: Braintrust Custom Tracing

This script tests the review_application function and verifies Braintrust tracing.
After running, check Braintrust dashboard for the "Review Job Description" trace.
"""

import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from ai import review_application

# Test data from Lab 21
TEST_JOB_DESCRIPTION = """
We're seeking a Forward Deployed Engineer. We want someone with 3+ years of software engineering experience with production systems. They should be rockstar programmers and problem solvers. They should have experience in a customer-facing technical role with a background in systems integration or professional services
"""

def test_review_application():
    """Test the 3-chain review_application function with Braintrust tracing."""
    print("=" * 60)
    print("Lab 21: Testing review_application with Braintrust Tracing")
    print("=" * 60)
    print()
    print("Input Job Description:")
    print("-" * 40)
    print(TEST_JOB_DESCRIPTION.strip())
    print("-" * 40)
    print()
    print("Running 3-chain analysis (Analysis → Rewrite → Finalise)...")
    print("This will be traced in Braintrust under 'Review Job Description'")
    print()
    
    try:
        result = review_application(TEST_JOB_DESCRIPTION)
        
        print("✅ SUCCESS!")
        print()
        print("Overall Summary:")
        print("-" * 40)
        print(result.overall_summary)
        print()
        print("Revised Description:")
        print("-" * 40)
        print(result.revised_description[:500] + "..." if len(result.revised_description) > 500 else result.revised_description)
        print()
        print("=" * 60)
        print("Next Steps:")
        print("1. Go to https://www.braintrust.dev/")
        print("2. Open project 'Prodapt'")
        print("3. Click 'Traces' tab")
        print("4. Find trace named 'Review Job Description'")
        print("5. Verify 3 spans inside (Analysis, Rewrite, Finalise chains)")
        print("=" * 60)
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_review_application()
    sys.exit(0 if success else 1)
