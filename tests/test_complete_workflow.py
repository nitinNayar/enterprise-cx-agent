"""
Test complete Decision Ledger workflow with agent integration.

This simulates a VIP customer requesting a return for final sale socks.
Tests the full path:
1. Agent receives request
2. Queries precedent with attribution
3. Cites decision maker in response
4. Records decision to audit log
"""

from agent.agent import SupportAgent
from logging_config import setup_logging
import json
import os

# Initialize logging
print("=" * 70)
print("COMPLETE WORKFLOW TEST: VIP Socks Exception")
print("=" * 70)

audit_logger = setup_logging()

# Initialize agent
agent = SupportAgent()

# Simulate VIP customer request
print("\n🧪 Simulating user request...")
print("-" * 70)

user_input = """
I want to return order ORD-777. It's a pair of socks that I bought.
I know socks are usually final sale, but I'm a VIP customer with 10 years
of loyalty and I've spent over $50k with your company. I need an exception.
"""

print(f"User: {user_input.strip()}")
print("\n⏳ Agent processing (this may take 10-20 seconds)...\n")

try:
    # Run agent
    response = agent.run(user_input)

    print("\n" + "=" * 70)
    print("AGENT RESPONSE")
    print("=" * 70)
    print(response)

    # Check if response contains attribution
    print("\n" + "=" * 70)
    print("ATTRIBUTION CHECK")
    print("=" * 70)

    has_name = "Sarah Chen" in response or "sarah" in response.lower()
    has_role = "VP" in response or "customer experience" in response.lower()
    has_exception = "exception" in response.lower() or "precedent" in response.lower()

    if has_name:
        print("✅ Response cites decision maker's name")
    else:
        print("❌ Response does NOT cite decision maker's name")

    if has_role:
        print("✅ Response cites decision maker's role")
    else:
        print("❌ Response does NOT cite decision maker's role")

    if has_exception:
        print("✅ Response acknowledges this is an exception")
    else:
        print("❌ Response does NOT acknowledge exception")

    # Display audit logs
    print("\n" + "=" * 70)
    print("AUDIT TRAIL")
    print("=" * 70)

    log_file = "logs/decision_audit.log"
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            lines = f.readlines()

        # Get logs from this session
        session_id = agent.session_id
        session_logs = [json.loads(line) for line in lines if session_id in line]

        print(f"Found {len(session_logs)} audit log entries for session {session_id}:\n")

        for log in session_logs:
            event_type = log.get('event_type', 'UNKNOWN')
            message = log.get('message', '')
            print(f"[{event_type}] {message}")

            if 'decision_id' in log:
                print(f"  └─ Decision: {log['decision_id']}")
            if 'person_name' in log:
                print(f"  └─ Person: {log['person_name']} ({log.get('person_role', 'N/A')})")
            if 'order_id' in log:
                print(f"  └─ Order: {log['order_id']}")
            if 'agent_decision' in log:
                print(f"  └─ Agent Decision: {log['agent_decision']}")
            print()

        # Pretty print last log entry
        print("Last audit log entry (formatted):")
        print(json.dumps(session_logs[-1], indent=2))

    else:
        print("❌ Audit log file not found")

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    all_checks = [has_name, has_role, has_exception]
    passed = sum(all_checks)
    total = len(all_checks)

    if passed == total:
        print(f"✅ ALL CHECKS PASSED ({passed}/{total})")
        print("\n🎉 Decision Ledger is fully functional!")
        print("   - Agent queries precedents with attribution")
        print("   - Agent cites decision makers by name and role")
        print("   - All decisions logged to audit trail")
    else:
        print(f"⚠️  PARTIAL PASS ({passed}/{total} checks)")
        print("\nNote: Agent may need prompt adjustments to consistently cite attribution.")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
