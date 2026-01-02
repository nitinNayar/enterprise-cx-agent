import kuzu
import shutil
import os

# Ensure paths are correct relative to this script
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "context_graph_db")

def init_db():
    # Ensure 'data' folder exists
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)

    if os.path.exists(DB_PATH):
        # Check if it's a file or a directory
        if os.path.isfile(DB_PATH):
            os.remove(DB_PATH) # Use os.remove for files
            print(f"🗑️  Removed existing file at {DB_PATH}")
        else:
            shutil.rmtree(DB_PATH) # Use rmtree for folders
            print(f"🗑️  Cleared existing database folder at {DB_PATH}")
    
    db = kuzu.Database(DB_PATH)
    conn = kuzu.Connection(db)
    
    print(f"⚙️  Initializing Kùzu Graph Database at {DB_PATH}...")

    conn.execute("CREATE NODE TABLE SupportCase(id STRING, decision STRING, rationale STRING, PRIMARY KEY (id))")
    conn.execute("CREATE NODE TABLE Tag(name STRING, PRIMARY KEY (name))")
    conn.execute("CREATE REL TABLE HAS_TAG(FROM SupportCase TO Tag)")
    
    # --- SCENARIO 1: VIP Socks ---
    conn.execute("""
        CREATE (c:SupportCase {
            id: 'PREC-VIP-001', 
            decision: 'APPROVE', 
            rationale: 'VIP customers are allowed to return Final Sale apparel as a one-time loyalty courtesy.'
        })
    """)
    tags_1 = ['socks', 'vip', 'exception', 'apparel']

    # --- SCENARIO 2: Holiday Gifts ---
    conn.execute("""
        CREATE (c:SupportCase {
            id: 'PREC-HOL-002', 
            decision: 'APPROVE', 
            rationale: 'Holiday gifts purchased in Dec have an extended 60-day return window.'
        })
    """)
    tags_2 = ['holiday', 'gift', 'late', 'extension', 'december']

    # --- SCENARIO 3: High-Value Tech ---
    conn.execute("""
        CREATE (c:SupportCase {
            id: 'PREC-TECH-003', 
            decision: 'APPROVE', 
            rationale: 'High-Value customers (> $5k spend) allowed one opened tech return per year.'
        })
    """)
    tags_3 = ['monitor', 'electronics', 'opened', 'high_value', 'tech']

    # --- Create Tags & Edges ---
    all_tags = list(set(tags_1 + tags_2 + tags_3)) 
    
    for tag in all_tags:
        conn.execute(f"CREATE (:Tag {{name: '{tag}'}})")

    def link_case(case_id, tags):
        for tag in tags:
            # FIX: Updated MATCH clause to use SupportCase
            conn.execute(f"""
                MATCH (c:SupportCase), (t:Tag) 
                WHERE c.id = '{case_id}' AND t.name = '{tag}' 
                CREATE (c)-[:HAS_TAG]->(t)
            """)

    link_case('PREC-VIP-001', tags_1)
    link_case('PREC-HOL-002', tags_2)
    link_case('PREC-TECH-003', tags_3)
    
    print("✅ Graph initialized with 3 Exception Scenarios!")

if __name__ == "__main__":
    init_db()