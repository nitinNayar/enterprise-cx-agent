"""
Debug script to inspect graph database and test queries
"""
import kuzu
import os
import json

# Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "context_graph_db")

db = kuzu.Database(DB_PATH, read_only=True)
conn = kuzu.Connection(db)

print("=" * 70)
print("GRAPH DATABASE DEBUGGER")
print("=" * 70)

# 1. Count all precedents
print("\n1. TOTAL PRECEDENTS IN DATABASE:")
result = conn.execute("MATCH (c:SupportCase) RETURN COUNT(*) AS count")
count = result.get_next()[0]
print(f"   Total SupportCase nodes: {count}")

# 2. List all precedents
print("\n2. ALL PRECEDENTS (with key fields):")
result = conn.execute("""
    MATCH (c:SupportCase)
    RETURN c.id, c.decision, c.decision_maker, c.timestamp
    ORDER BY c.id
""")
print(f"   {'ID':<25} {'Decision':<10} {'Decision Maker':<25} {'Timestamp':<25}")
print(f"   {'-'*25} {'-'*10} {'-'*25} {'-'*25}")
while result.has_next():
    id, decision, maker, timestamp = result.get_next()
    print(f"   {id:<25} {decision:<10} {maker or 'unknown':<25} {timestamp or 'N/A':<25}")

# 3. Count all tags
print("\n3. TOTAL TAGS IN DATABASE:")
result = conn.execute("MATCH (t:Tag) RETURN COUNT(*) AS count")
count = result.get_next()[0]
print(f"   Total Tag nodes: {count}")

# 4. List all tags
print("\n4. ALL TAGS:")
result = conn.execute("MATCH (t:Tag) RETURN t.name ORDER BY t.name")
tags = []
while result.has_next():
    tags.append(result.get_next()[0])
print(f"   {', '.join(tags)}")

# 5. Test specific query
print("\n5. TEST QUERY: 'VIP socks return exception'")
query_tags_str = "VIP socks return exception"
input_tags = [t.strip().lower() for t in query_tags_str.split()]
print(f"   Parsed tags: {input_tags}")

query = f"""
MATCH (c:SupportCase)-[:HAS_TAG]->(t:Tag)
WHERE t.name IN {input_tags}
RETURN c.id, c.decision, c.rationale, c.decision_maker,
       c.decision_maker_role, c.timestamp, c.case_id,
       c.customer_context, c.conditions, COUNT(t) AS score
ORDER BY score DESC
LIMIT 5
"""

print(f"\n   Cypher Query:")
print(f"   {query}")

result = conn.execute(query)

if result.has_next():
    print("\n   MATCHES FOUND:")
    match_num = 1
    while result.has_next():
        case_id, decision, rationale, decision_maker, decision_maker_role, timestamp, orig_case_id, customer_context, conditions, score = result.get_next()
        print(f"\n   Match #{match_num} (Score: {score}):")
        print(f"   {'-'*65}")
        print(f"   Precedent ID: {case_id}")
        print(f"   Decision: {decision}")
        print(f"   Decision Maker: {decision_maker} ({decision_maker_role})")
        print(f"   Timestamp: {timestamp}")
        print(f"   Case ID: {orig_case_id}")
        print(f"   Rationale: {rationale[:80]}..." if len(rationale) > 80 else f"   Rationale: {rationale}")
        print(f"   Customer Context: {customer_context[:60]}..." if len(customer_context) > 60 else f"   Customer Context: {customer_context}")
        print(f"   Conditions: {conditions[:60]}..." if len(conditions) > 60 else f"   Conditions: {conditions}")
        match_num += 1
else:
    print("\n   ❌ NO MATCHES FOUND")
    print("\n   Checking which tags exist in database:")
    for tag in input_tags:
        result = conn.execute(f"MATCH (t:Tag) WHERE t.name = '{tag}' RETURN COUNT(*)")
        exists = result.get_next()[0] > 0
        print(f"      '{tag}': {'✅ EXISTS' if exists else '❌ NOT FOUND'}")

# 6. Show tags for a specific precedent
print("\n6. TAGS FOR SPECIFIC PRECEDENT (PREC-VIP-001):")
result = conn.execute("""
    MATCH (c:SupportCase)-[:HAS_TAG]->(t:Tag)
    WHERE c.id = 'PREC-VIP-001'
    RETURN t.name
    ORDER BY t.name
""")
tags = []
while result.has_next():
    tags.append(result.get_next()[0])
if tags:
    print(f"   Tags: {', '.join(tags)}")
else:
    print("   No tags found for this precedent")

print("\n" + "=" * 70)
print("DEBUG COMPLETE")
print("=" * 70)
