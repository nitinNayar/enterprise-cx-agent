"""Quick test to verify new Person/Decision/Product schema"""
import kuzu
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "context_graph_db")

db = kuzu.Database(DB_PATH)
conn = kuzu.Connection(db)

print("=" * 60)
print("Testing New Decision Ledger Schema")
print("=" * 60)

# Test 1: Count nodes
print("\n1. Node Counts:")
result = conn.execute("MATCH (p:Person) RETURN COUNT(p)")
print(f"   - Persons: {result.get_next()[0]}")

result = conn.execute("MATCH (d:Decision) RETURN COUNT(d)")
print(f"   - Decisions: {result.get_next()[0]}")

result = conn.execute("MATCH (prod:Product) RETURN COUNT(prod)")
print(f"   - Products: {result.get_next()[0]}")

result = conn.execute("MATCH (t:Tag) RETURN COUNT(t)")
print(f"   - Tags: {result.get_next()[0]}")

# Test 2: Query Person→Decision relationships
print("\n2. Person→Decision Relationships:")
result = conn.execute("""
    MATCH (p:Person)-[m:MADE]->(d:Decision)
    RETURN p.name, p.role, d.id, d.title
""")

while result.has_next():
    name, role, dec_id, title = result.get_next()
    print(f"   - {name} ({role}) made {dec_id}: {title}")

# Test 3: Test tag-based query (simulating check_precedents)
print("\n3. Test Tag-Based Query (VIP Socks):")
result = conn.execute("""
    MATCH (p:Person)-[m:MADE]->(d:Decision)-[ctx:HAS_CONTEXT]->(t:Tag)
    WHERE t.name IN ['vip', 'socks']
      AND d.confidence_score >= 0.7
    WITH p, d, SUM(ctx.relevance_score) AS score
    ORDER BY score DESC, p.authority_level DESC
    LIMIT 1
    RETURN
        d.id,
        d.title,
        d.outcome,
        d.reasoning,
        p.name,
        p.role,
        p.authority_level,
        score
""")

if result.has_next():
    dec_id, title, outcome, reasoning, name, role, authority, score = result.get_next()
    print(f"   ✅ Found: {dec_id}")
    print(f"      Title: {title}")
    print(f"      Outcome: {outcome}")
    print(f"      Decision Maker: {name} ({role}, Authority: {authority})")
    print(f"      Match Score: {score}")
    print(f"      Reasoning: {reasoning[:100]}...")
else:
    print("   ❌ No precedent found!")

# Test 4: Test Decision→Product relationships
print("\n4. Decision→Product Relationships:")
result = conn.execute("""
    MATCH (d:Decision)-[:APPLIES_TO]->(prod:Product)
    RETURN d.id, prod.category_name, prod.risk_level
""")

while result.has_next():
    dec_id, category, risk = result.get_next()
    print(f"   - {dec_id} applies to {category} (risk: {risk})")

print("\n" + "=" * 60)
print("✅ Schema verification complete!")
print("=" * 60)
