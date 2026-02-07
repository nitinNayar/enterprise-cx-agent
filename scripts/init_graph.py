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
    # PRECEDENT 1: VIP Read Book Exception
    # ===========================================

    print("  → Converting PREC-VIP-001 (VIP Read Book)...")

    # Person: Sarah Chen
    conn.execute("""
        CREATE (p:Person {
            id: 'sarah.chen@bookly.com',
            name: 'Sarah Chen',
            email: 'sarah.chen@bookly.com',
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
            title: 'Book Club VIP Exception for Read Books',
            context: 'Book Club Platinum member with 10+ year history and $50k lifetime value requesting return of signed edition that was opened and read (first chapter)',
            outcome: 'APPROVE',
            reasoning: 'Book Club Platinum members with demonstrated loyalty and high lifetime value should receive exceptional service when circumstances warrant. This builds long-term customer relationships and reinforces the value of Book Club membership.',
            conditions: 'One-time exception only. Not to be used as precedent for all Book Club members. Limited to once per year for read books.',
            source_ref: 'esc-2024-001-vip-read-book-exception.txt',
            confidence_score: 1.0,
            expires_at: 'NEVER',
            created_at: '2024-12-15T14:30:00Z',
            case_id: 'ESC-2024-001'
        })
    """)

    # Product: Signed Books
    conn.execute("""
        CREATE (prod:Product {
            category_name: 'signed_books',
            risk_level: 'MEDIUM',
            returnable_by_default: false,
            requires_special_handling: true,
            description: 'Special edition books - Signed and collectible editions'
        })
    """)

    # Tags for VIP Read Books
    tags_1 = [
        ('vip', 'customer_tier', 2.0),
        ('book', 'product_type', 1.5),
        ('read', 'product_condition', 1.5),
        ('signed', 'product_type', 1.2),
        ('exception', 'context', 1.5),
        ('book_club', 'customer_tier', 1.8),
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
        MATCH (p:Person {id: 'sarah.chen@bookly.com'}),
              (d:Decision {id: 'DEC-2024-001'})
        CREATE (p)-[:MADE {
            decision_timestamp: '2024-12-15T14:30:00Z',
            is_override: true
        }]->(d)
    """)

    conn.execute("""
        MATCH (d:Decision {id: 'DEC-2024-001'}),
              (prod:Product {category_name: 'signed_books'})
        CREATE (d)-[:APPLIES_TO {specificity: 'SPECIFIC'}]->(prod)
    """)

    for tag_name, _, weight in tags_1:
        conn.execute(f"""
            MATCH (d:Decision {{id: 'DEC-2024-001'}}),
                  (t:Tag {{name: '{tag_name}'}})
            CREATE (d)-[:HAS_CONTEXT {{relevance_score: {weight}}}]->(t)
        """)

    # ===========================================
    # PRECEDENT 2: Holiday Gift Book Extension
    # ===========================================

    print("  → Converting PREC-HOL-002 (Holiday Gift Book)...")

    conn.execute("""
        CREATE (p:Person {
            id: 'mike.rodriguez@bookly.com',
            name: 'Mike Rodriguez',
            email: 'mike.rodriguez@bookly.com',
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
            title: 'Holiday Gift Book Return Window Extension',
            context: 'Customer purchased book collection in December as holiday gift, recipient requesting return in January (39 days)',
            outcome: 'APPROVE',
            reasoning: 'Holiday gift books purchased in November-December should receive extended consideration. Recipients often do not receive or evaluate gifts until after the holidays. A 60-day window for November-December purchases is reasonable and builds goodwill.',
            conditions: 'Applies to purchases made in November-December only. Extended window is 60 days from purchase date. Book must be in unread condition.',
            source_ref: 'esc-2024-002-holiday-gift-late-return.txt',
            confidence_score: 1.0,
            expires_at: '2025-02-01T00:00:00Z',
            created_at: '2024-01-20T10:15:00Z',
            case_id: 'ESC-2024-002'
        })
    """)

    # Product: Books (create if not exists)
    conn.execute("""
        CREATE (prod:Product {
            category_name: 'books',
            risk_level: 'LOW',
            returnable_by_default: true,
            requires_special_handling: false,
            description: 'Physical books - Hardcover and paperback'
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
        MATCH (p:Person {id: 'mike.rodriguez@bookly.com'}),
              (d:Decision {id: 'DEC-2024-002'})
        CREATE (p)-[:MADE {
            decision_timestamp: '2024-01-20T10:15:00Z',
            is_override: true
        }]->(d)
    """)

    conn.execute("""
        MATCH (d:Decision {id: 'DEC-2024-002'}),
              (prod:Product {category_name: 'books'})
        CREATE (d)-[:APPLIES_TO {specificity: 'GENERAL'}]->(prod)
    """)

    for tag_name, _, weight in tags_2:
        conn.execute(f"""
            MATCH (d:Decision {{id: 'DEC-2024-002'}}),
                  (t:Tag {{name: '{tag_name}'}})
            CREATE (d)-[:HAS_CONTEXT {{relevance_score: {weight}}}]->(t)
        """)

    # ===========================================
    # PRECEDENT 3: Book Club VIP Audiobook Exception
    # ===========================================

    print("  → Converting PREC-AUDIO-003 (Book Club VIP Audiobook)...")

    conn.execute("""
        CREATE (p:Person {
            id: 'jennifer.park@bookly.com',
            name: 'Jennifer Park',
            email: 'jennifer.park@bookly.com',
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
            title: 'Book Club VIP Downloaded Audiobook Exception',
            context: 'Book Club Silver member ($8k lifetime value) with exceptional audiobook purchase history (47 audiobooks, 2 returns) requesting return of downloaded audiobook due to narrator incompatibility',
            outcome: 'APPROVE',
            reasoning: 'Book Club members with demonstrated loyalty and high audiobook purchase volume deserve exceptional service on rare occasions. Narrator compatibility is a legitimate audiobook concern that cannot be assessed before purchase. This exception strengthens customer lifetime value and reinforces Book Club membership benefits.',
            conditions: 'One-time exception. Limited to one digital product return per customer per year. Only applies to Book Club members with $5k+ lifetime value. Customer must report within 7 days of download. Applies only if less than 20% of audiobook consumed.',
            source_ref: 'esc-2024-003-opened-audiobook-high-value.txt',
            confidence_score: 1.0,
            expires_at: 'NEVER',
            created_at: '2024-02-05T15:45:00Z',
            case_id: 'ESC-2024-003'
        })
    """)

    conn.execute("""
        CREATE (prod:Product {
            category_name: 'audiobooks',
            risk_level: 'MEDIUM',
            returnable_by_default: false,
            requires_special_handling: true,
            description: 'Digital audiobooks - Downloaded audio content'
        })
    """)

    tags_3 = [
        ('audiobook', 'product_type', 1.8),
        ('digital', 'product_type', 1.5),
        ('downloaded', 'product_condition', 1.5),
        ('book_club', 'customer_tier', 2.0),
        ('vip', 'customer_tier', 1.8),
        ('narrator', 'issue_type', 1.0),
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
        MATCH (p:Person {id: 'jennifer.park@bookly.com'}),
              (d:Decision {id: 'DEC-2024-003'})
        CREATE (p)-[:MADE {
            decision_timestamp: '2024-02-05T15:45:00Z',
            is_override: true
        }]->(d)
    """)

    conn.execute("""
        MATCH (d:Decision {id: 'DEC-2024-003'}),
              (prod:Product {category_name: 'audiobooks'})
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
