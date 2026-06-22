"""Quick direct test of the guard_agent's check_intent_for_policy_violation tool."""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from app.agents.guard_agent import check_intent_for_policy_violation, EXCLUDED_SECTORS

test_cases = [
    ("Buy 100% of portfolio in coal stocks", True),
    ("Invest in weapons manufacturers", True),
    ("Analyze AAPL for climate-aware investment", False),
    ("<script>alert('xss')</script>", False),
    ("Buy tobacco stocks for my portfolio", True),
]

print("=" * 60)
print("GUARD AGENT -- Intent Policy Check Test")
print("=" * 60)

for request, expected_blocked in test_cases:
    result = check_intent_for_policy_violation(request)
    actual_blocked = result["blocked"]
    status = "[PASS]" if actual_blocked == expected_blocked else "[FAIL]"

    display = request[:50] + "..." if len(request) > 50 else request
    print(f"\n{status} | Request: \"{display}\"")

    if actual_blocked:
        print(f"  >> TRADE BLOCKED")
        print(f"  {'-' * 44}")
        print(f"  Reason       : {result['reason']}")
        print(f"  Sector Match : {result['matched_sector']}")
        print(f"  Action       : Trade rejected. No execution will occur.")
    else:
        print(f"  >> No policy violation detected. Request is clean.")

print("\n" + "=" * 60)
print(f"Excluded sectors enforced: {sorted(EXCLUDED_SECTORS)}")
print("=" * 60)
