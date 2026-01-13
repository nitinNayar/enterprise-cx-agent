"""
Initialize Kùzu Graph Database with Decision Ledger schema.

This script:
1. Backs up the existing database
2. Creates new Person/Decision/Product/Tag schema
3. Migrates existing 3 precedents to new model
4. Creates indexes for performance

Run with: python scripts/init_graph.py
"""

import kuzu
import shutil
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "context_graph_db")


def init_db():
    """
    Initialize Kùzu Graph Database with Decision Ledger schema.
    Replaces old SupportCase/Tag schema with Person/Decision/Product model.
    """

    # Ensure 'data' folder exists
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)

    # Backup existing database before clearing
    if os.path.exists(DB_PATH):
        backup_path = DB_PATH + f".backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        if os.path.isfile(DB_PATH):
            shutil.copy2(DB_PATH, backup_path)
        else:
            shutil.copytree(DB_PATH, backup_path)
        print(f"📦 Backed up old database to {backup_path}")

        # Remove old database
        if os.path.isfile(DB_PATH):
            os.remove(DB_PATH)
        else:
            shutil.rmtree(DB_PATH)
        print(f"🗑️  Cleared existing database at {DB_PATH}")

    db = kuzu.Database(DB_PATH)
    conn = kuzu.Connection(db)

    print(f"⚙️  Initializing Kùzu Graph Database at {DB_PATH}...")

    # ===========================================
    # CREATE NODE TABLES
    # ===========================================

    print("Creating Person table...")
    conn.execute("""
        CREATE NODE TABLE Person(
            id STRING,
            name STRING,
            email STRING,
            role STRING,
            department STRING,
            authority_level INT64,
            last_active STRING,
            created_at STRING,
            PRIMARY KEY (id)
        )
    """)

    print("Creating Decision table...")
    conn.execute("""
        CREATE NODE TABLE Decision(
            id STRING,
            title STRING,
            context STRING,
            outcome STRING,
            reasoning STRING,
            conditions STRING,
            source_ref STRING,
            confidence_score DOUBLE,
            expires_at STRING,
            created_at STRING,
            case_id STRING,
            PRIMARY KEY (id)
        )
    """)

    print("Creating Product table...")
    conn.execute("""
        CREATE NODE TABLE Product(
            category_name STRING,
            risk_level STRING,
            returnable_by_default BOOL,
            requires_special_handling BOOL,
            description STRING,
            PRIMARY KEY (category_name)
        )
    """)

    print("Creating Tag table...")
    conn.execute("""
        CREATE NODE TABLE Tag(
            name STRING,
            category STRING,
            weight DOUBLE,
            PRIMARY KEY (name)
        )
    """)

    # ===========================================
    # CREATE RELATIONSHIP TABLES
    # ===========================================

    print("Creating relationships...")

    conn.execute("""
        CREATE REL TABLE MADE(
            FROM Person TO Decision,
            decision_timestamp STRING,
            is_override BOOL
        )
    """)

    conn.execute("""
        CREATE REL TABLE APPLIES_TO(
            FROM Decision TO Product,
            specificity STRING
        )
    """)

    conn.execute("""
        CREATE REL TABLE HAS_CONTEXT(
            FROM Decision TO Tag,
            relevance_score DOUBLE
        )
    """)

    conn.execute("""
        CREATE REL TABLE CITES(
            FROM Decision TO Decision,
            citation_reason STRING
        )
    """)

    print("✅ Schema created successfully!")

    # ===========================================
    # SEED DATA - Migrate 3 existing precedents
    # ===========================================

    print("\n📊 Seeding with converted precedents...")
    seed_converted_precedents(conn)

    print("\n✅ Graph initialized with Decision Ledger schema!")
    print("📝 Next steps:")
    print("   1. Run: python scripts/extract_decisions.py")
    print("   2. Or manually add decisions via text files")


def seed_converted_precedents(conn):
    """
    Convert 3 existing SupportCase precedents to new schema:
    - PREC-VIP-001: VIP Socks Exception → Person(Sarah Chen) + Decision(DEC-2024-001)
    - PREC-HOL-002: Holiday Gift Extension → Person(Mike Rodriguez) + Decision(DEC-2024-002)
    - PREC-TECH-003: High-Value Tech Exception → Person(Jennifer Park) + Decision(DEC-2024-003)
    """

    # ===========================================
    # PRECEDENT 1: VIP Socks Exception
    # ===========================================

    print("  → Converting PREC-VIP-001 (VIP Socks)...")

    # Person: Sarah Chen
    conn.execute("""
        CREATE (p:Person {
            id: 'sarah.chen@company.com',
            name: 'Sarah Chen',
            email: 'sarah.chen@company.com',
            role: 'VP Customer Experience',
            department: 'Customer Experience',
            authority_level: 5,
            last_active: '2024-12-15T14:30:00Z',
            created_at: '2024-12-15T14:30:00Z'
        })
    """)

    # Decision: VIP Exception
    conn.execute("""
        CREATE (d:Decision {
            id: 'DEC-2024-001',
            title: 'VIP Loyalty Exception for Final Sale Items',
            context: 'VIP customer with 10+ year history and $50k lifetime value requesting exception on final sale socks',
            outcome: 'APPROVE',
            reasoning: 'VIP customers with demonstrated loyalty and high lifetime value should receive exceptional service when circumstances warrant. This builds long-term brand loyalty.',
            conditions: 'One-time exception only. Not to be used as precedent for all VIP customers. Customer should be informed this is a courtesy exception.',
            source_ref: 'esc-2024-001-vip-socks-exception.txt',
            confidence_score: 1.0,
            expires_at: 'NEVER',
            created_at: '2024-12-15T14:30:00Z',
            case_id: 'ESC-2024-001'
        })
    """)

    # Product: Socks
    conn.execute("""
        CREATE (prod:Product {
            category_name: 'socks',
            risk_level: 'LOW',
            returnable_by_default: false,
            requires_special_handling: false,
            description: 'Apparel - Socks and intimates'
        })
    """)

    # Tags for VIP Socks
    tags_1 = [
        ('vip', 'customer_tier', 2.0),
        ('socks', 'product_type', 1.0),
        ('exception', 'context', 1.5),
        ('apparel', 'product_type', 1.0),
        ('final_sale', 'policy_type', 1.5),
        ('loyalty', 'context', 1.2)
    ]

    for tag_name, tag_category, weight in tags_1:
        conn.execute(f"""
            MERGE (t:Tag {{name: '{tag_name}'}})
            ON CREATE SET
                t.category = '{tag_category}',
                t.weight = {weight}
        """)

    # Relationships for PREC-VIP-001
    conn.execute("""
        MATCH (p:Person {id: 'sarah.chen@company.com'}),
              (d:Decision {id: 'DEC-2024-001'})
        CREATE (p)-[:MADE {
            decision_timestamp: '2024-12-15T14:30:00Z',
            is_override: true
        }]->(d)
    """)

    conn.execute("""
        MATCH (d:Decision {id: 'DEC-2024-001'}),
              (prod:Product {category_name: 'socks'})
        CREATE (d)-[:APPLIES_TO {specificity: 'SPECIFIC'}]->(prod)
    """)

    for tag_name, _, weight in tags_1:
        conn.execute(f"""
            MATCH (d:Decision {{id: 'DEC-2024-001'}}),
                  (t:Tag {{name: '{tag_name}'}})
            CREATE (d)-[:HAS_CONTEXT {{relevance_score: {weight}}}]->(t)
        """)

    # ===========================================
    # PRECEDENT 2: Holiday Gift Extension
    # ===========================================

    print("  → Converting PREC-HOL-002 (Holiday Gift)...")

    conn.execute("""
        CREATE (p:Person {
            id: 'mike.rodriguez@company.com',
            name: 'Mike Rodriguez',
            email: 'mike.rodriguez@company.com',
            role: 'Customer Service Manager',
            department: 'Customer Service',
            authority_level: 3,
            last_active: '2024-01-20T10:15:00Z',
            created_at: '2024-01-20T10:15:00Z'
        })
    """)

    conn.execute("""
        CREATE (d:Decision {
            id: 'DEC-2024-002',
            title: 'Holiday Gift Return Window Extension',
            context: 'Customer purchased gift card in December as holiday gift, recipient requesting return in January (39 days)',
            outcome: 'APPROVE',
            reasoning: 'Holiday gifts purchased in December should receive extended consideration. Recipients often do not unwrap or evaluate gifts until after the holidays. A 60-day window for December purchases is reasonable and builds goodwill.',
            conditions: 'Applies to purchases made in December only. Extended window is 60 days from purchase date.',
            source_ref: 'esc-2024-002-holiday-gift-late-return.txt',
            confidence_score: 1.0,
            expires_at: '2025-02-01T00:00:00Z',
            created_at: '2024-01-20T10:15:00Z',
            case_id: 'ESC-2024-002'
        })
    """)

    # Product: Gift Cards (create if not exists)
    conn.execute("""
        CREATE (prod:Product {
            category_name: 'gift_cards',
            risk_level: 'MEDIUM',
            returnable_by_default: false,
            requires_special_handling: true,
            description: 'Digital goods - Gift cards and codes'
        })
    """)

    tags_2 = [
        ('holiday', 'context', 1.8),
        ('gift', 'context', 1.5),
        ('late', 'policy_type', 1.0),
        ('extension', 'context', 1.2),
        ('december', 'temporal', 1.5)
    ]

    for tag_name, tag_category, weight in tags_2:
        conn.execute(f"""
            MERGE (t:Tag {{name: '{tag_name}'}})
            ON CREATE SET
                t.category = '{tag_category}',
                t.weight = {weight}
        """)

    conn.execute("""
        MATCH (p:Person {id: 'mike.rodriguez@company.com'}),
              (d:Decision {id: 'DEC-2024-002'})
        CREATE (p)-[:MADE {
            decision_timestamp: '2024-01-20T10:15:00Z',
            is_override: true
        }]->(d)
    """)

    conn.execute("""
        MATCH (d:Decision {id: 'DEC-2024-002'}),
              (prod:Product {category_name: 'gift_cards'})
        CREATE (d)-[:APPLIES_TO {specificity: 'GENERAL'}]->(prod)
    """)

    for tag_name, _, weight in tags_2:
        conn.execute(f"""
            MATCH (d:Decision {{id: 'DEC-2024-002'}}),
                  (t:Tag {{name: '{tag_name}'}})
            CREATE (d)-[:HAS_CONTEXT {{relevance_score: {weight}}}]->(t)
        """)

    # ===========================================
    # PRECEDENT 3: High-Value Tech Exception
    # ===========================================

    print("  → Converting PREC-TECH-003 (High-Value Tech)...")

    conn.execute("""
        CREATE (p:Person {
            id: 'jennifer.park@company.com',
            name: 'Jennifer Park',
            email: 'jennifer.park@company.com',
            role: 'Director of Customer Experience',
            department: 'Customer Experience',
            authority_level: 4,
            last_active: '2024-02-05T15:45:00Z',
            created_at: '2024-02-05T15:45:00Z'
        })
    """)

    conn.execute("""
        CREATE (d:Decision {
            id: 'DEC-2024-003',
            title: 'High-Value Customer Opened Electronics Exception',
            context: 'High-value customer ($12k annual spend) with perfect return history requesting return of opened gaming monitor',
            outcome: 'APPROVE',
            reasoning: 'High-value customers with demonstrated loyalty and clean history deserve exceptional service on rare occasions. This exception strengthens customer lifetime value and reinforces that we value long-term relationships.',
            conditions: 'One-time exception. Limited to one opened electronics return per customer per year. Does not apply to customers under $5k annual spend.',
            source_ref: 'esc-2024-003-opened-tech-high-value.txt',
            confidence_score: 1.0,
            expires_at: 'NEVER',
            created_at: '2024-02-05T15:45:00Z',
            case_id: 'ESC-2024-003'
        })
    """)

    conn.execute("""
        CREATE (prod:Product {
            category_name: 'electronics',
            risk_level: 'HIGH',
            returnable_by_default: true,
            requires_special_handling: true,
            description: 'Electronics - Computers, monitors, gaming devices'
        })
    """)

    tags_3 = [
        ('monitor', 'product_type', 1.0),
        ('electronics', 'product_type', 1.2),
        ('opened', 'product_condition', 1.5),
        ('high_value', 'customer_tier', 2.0),
        ('tech', 'product_type', 1.0),
        ('loyalty', 'context', 1.2)
    ]

    for tag_name, tag_category, weight in tags_3:
        conn.execute(f"""
            MERGE (t:Tag {{name: '{tag_name}'}})
            ON CREATE SET
                t.category = '{tag_category}',
                t.weight = {weight}
        """)

    conn.execute("""
        MATCH (p:Person {id: 'jennifer.park@company.com'}),
              (d:Decision {id: 'DEC-2024-003'})
        CREATE (p)-[:MADE {
            decision_timestamp: '2024-02-05T15:45:00Z',
            is_override: true
        }]->(d)
    """)

    conn.execute("""
        MATCH (d:Decision {id: 'DEC-2024-003'}),
              (prod:Product {category_name: 'electronics'})
        CREATE (d)-[:APPLIES_TO {specificity: 'SPECIFIC'}]->(prod)
    """)

    for tag_name, _, weight in tags_3:
        conn.execute(f"""
            MATCH (d:Decision {{id: 'DEC-2024-003'}}),
                  (t:Tag {{name: '{tag_name}'}})
            CREATE (d)-[:HAS_CONTEXT {{relevance_score: {weight}}}]->(t)
        """)

    print("  ✅ 3 precedents converted successfully")


if __name__ == "__main__":
    init_db()
