# Bookly Rebrand Summary

**Date:** February 7, 2026
**Branch:** `rebrand_bookly`
**Theme:** Online bookstore customer support agent

---

## Overview

Successfully rebranded the Enterprise CX Agent from TrueCart (general retailer) to **Bookly** (online bookstore). All mock data, policies, and precedents have been updated to reflect book-specific scenarios while maintaining the same underlying architecture and agent behavior patterns.

---

## Files Updated

### 1. Mock Orders (`data/mock_orders.json`)

**Changes:**
- All product items changed to books and book-related products
- Added book-specific metadata (edition type, format, condition)

**New Order Items:**
- Physical books (hardcover, paperback, special editions)
- Digital products (e-books, audiobooks)
- Book accessories (bookmarks, book lights)
- Gift cards
- Signed/personalized editions

**Example Orders:**
- `ORD-123`: "Die Hard: The Official Movie Novelization" (Hardcover)
- `ORD-777`: "The Terminator Files: Technical Manual" (Signed Edition)
- `ORD-222`: "Master of Disguise: A Spy's Memoir" (Audiobook download)
- `ORD-888`: "Complete Sherlock Holmes Collection" (Leather-bound gift set)
- `ORD-1001`: "The Art of War" (E-book download)

**Total Orders:** 12 (10 existing updated + 2 new)

---

### 2. Mock Customers (`data/mock_customers.json`)

**Changes:**
- Updated VIP tier to "Book Club" membership concept
- Added reading preference notes
- Kept all customer names (they're great readers!)
- Added 2 new customers (Indiana Jones, Maximus Decimus)

**VIP Tiers:**
- **Platinum**: $50k+ lifetime value (Sarah Connor - sci-fi collector)
- **Gold**: $12k-15k lifetime value (John McClane, Lara Croft - genre enthusiasts)
- **Silver**: $5k-8k lifetime value (Ethan Hunt, Trinity - audiobook fans)

**Regular Customers:** 6 customers with varying tenure (0.5-6 years)

**Total Customers:** 12 (10 existing + 2 new)

---

### 3. Return Policy (`policies/return_policy.md`)

**Complete Rewrite for Bookstore Context**

**New Non-Returnable Categories:**
- ✘ E-books (downloaded)
- ✘ Audiobooks (downloaded)
- ✘ Digital gift cards
- ✘ Personalized books with inscriptions
- ✘ Books with visible signs of reading (bent pages, markings, wear)
- ✘ Customer-damaged books (water damage, torn pages, stains)

**New Book-Specific Rules:**

**Physical Books:**
- Must be in "unread, resellable condition"
- No bent spines, dog-eared pages, or annotations
- If shrink-wrapped, packaging must be intact

**Digital Products:**
- Non-returnable once downloaded/accessed
- No exceptions, even if not consumed
- Technical issues handled by Tech Support (not returns)

**Signed & Limited Editions:**
- Must be pristine, unopened condition
- Opening = loss of collectible value
- Personalized inscriptions = final sale

**Book Condition Guidelines:**
Added detailed definitions:
- What IS "unread condition" (straight spine, no markings, etc.)
- What is NOT "unread condition" (cracked spine, bent pages, stains, etc.)

**Book Club Member Benefits:**
- VIP members may receive extended consideration
- Special exception protocol for loyal members

**Total Sections:** 10 comprehensive sections (vs. 5 in original)

---

### 4. Decision Precedent Emails

**Three precedents updated with bookstore scenarios:**

#### Precedent 1: VIP Read Book Exception
**Old:** `esc-2024-001-vip-socks-exception.txt` (socks, final sale)
**New:** `esc-2024-001-vip-read-book-exception.txt` (signed book, opened and read)

**Scenario:**
- Customer: Sarah Connor (Platinum Book Club member, 10 years, $50k)
- Item: "The Terminator Files: Technical Manual" (Signed Edition - $125)
- Issue: Customer opened and read first chapter
- Policy: Read books non-returnable
- **Decision:** APPROVED (one-time VIP exception)
- **Conditions:** Once per year limit for read books

**Tags:** vip, book, read, signed, exception, book_club, loyalty

---

#### Precedent 2: Holiday Gift Book Late Return
**Old:** `esc-2024-002-holiday-gift-late-return.txt` (PlayStation gift card)
**New:** `esc-2024-002-holiday-gift-late-return.txt` (book collection)

**Scenario:**
- Customer: Jack Ryan (Regular customer, not VIP)
- Item: "Complete Sherlock Holmes Collection" (Leather-bound - $85)
- Issue: Holiday gift, 39 days since purchase (outside 30-day window)
- Policy: 30-day return window
- **Decision:** APPROVED (holiday exception)
- **Conditions:** 60-day window for November-December purchases, unread condition

**Tags:** holiday, gift, late, extension, december

---

#### Precedent 3: Downloaded Audiobook Exception
**Old:** `esc-2024-003-opened-tech-high-value.txt` (gaming monitor, opened)
**New:** `esc-2024-003-opened-audiobook-high-value.txt` (audiobook, downloaded)

**Scenario:**
- Customer: Ethan Hunt (Silver Book Club member, $8k, 47 audiobooks purchased)
- Item: "Master of Disguise: A Spy's Memoir" (Audiobook - $29.99)
- Issue: Downloaded, listened to 2 chapters, narrator incompatibility
- Policy: Digital audiobooks non-returnable
- **Decision:** APPROVED (Book Club VIP exception)
- **Conditions:** Once per year, <20% consumed, reported within 7 days, $5k+ members only

**Tags:** audiobook, digital, downloaded, book_club, vip, narrator, loyalty

---

### 5. Graph Database Initialization (`scripts/init_graph.py`)

**Updated all three precedents:**

**Email Domains:**
- Changed: `@company.com` → `@bookly.com`
- Sarah Chen: `sarah.chen@bookly.com`
- Mike Rodriguez: `mike.rodriguez@bookly.com`
- Jennifer Park: `jennifer.park@bookly.com`

**Decision Titles:**
- DEC-2024-001: "VIP Loyalty Exception for Final Sale Items" → "Book Club VIP Exception for Read Books"
- DEC-2024-002: "Holiday Gift Return Window Extension" (updated context to books)
- DEC-2024-003: "High-Value Customer Opened Electronics Exception" → "Book Club VIP Downloaded Audiobook Exception"

**Product Categories:**
- Changed: `socks` → `signed_books`
- Changed: `gift_cards` → `books`
- Changed: `electronics` → `audiobooks`

**Tags Updated:**
- Precedent 1: socks → book, read, signed, book_club
- Precedent 2: (kept holiday/gift, updated context)
- Precedent 3: monitor, electronics, tech → audiobook, digital, downloaded, narrator

---

## Book-Specific Scenarios

### Scenario 1: Simple Return (Policy-Compliant)
**Order:** ORD-123 - "Die Hard: The Official Movie Novelization"
**Customer:** John McClane (Gold VIP)
**Status:** Shipped, eligible
**Expected Flow:** Look up → Greet → Ask "Is the book in unread condition?" → Policy check → Approve

---

### Scenario 2: Late Return (Regular Customer)
**Order:** ORD-456 - "The Bourne Identity"
**Customer:** Jason Bourne (Regular)
**Status:** 45 days old, expired
**Expected Flow:** Look up → Greet → Policy check → Deny (outside window)

---

### Scenario 3: VIP Read Book Exception
**Order:** ORD-777 - "The Terminator Files" (Signed)
**Customer:** Sarah Connor (Platinum VIP, 10 years)
**Status:** Opened and read first chapter
**Expected Flow:**
1. Look up → Greet → Ask about condition
2. Customer: "I read the first chapter"
3. Policy check → DENY (read books non-returnable)
4. VIP check → TRUE (Platinum)
5. Precedent check → FOUND (DEC-2024-001)
6. **APPROVE with exception notice**

---

### Scenario 4: Holiday Gift Late Return
**Order:** ORD-888 - "Sherlock Holmes Collection"
**Customer:** Jack Ryan (Regular, not VIP)
**Status:** 39 days old, holiday gift
**Expected Flow:**
1. Look up → Greet → Ask about reason
2. Customer: "It was a Christmas gift"
3. Policy check → DENY (outside 30-day window)
4. Precedent check → FOUND (DEC-2024-002, holiday exception)
5. **APPROVE with holiday exception notice**

---

### Scenario 5: Downloaded Audiobook (VIP)
**Order:** ORD-222 - "Master of Disguise" (Audiobook)
**Customer:** Ethan Hunt (Silver VIP)
**Status:** Downloaded, listened to 2 chapters
**Expected Flow:**
1. Look up → Greet → Ask "Have you downloaded the audiobook?"
2. Customer: "Yes, listened to 2 chapters but narrator's voice doesn't work for me"
3. Policy check → DENY (digital products non-returnable)
4. VIP check → TRUE (Silver)
5. Precedent check → FOUND (DEC-2024-003)
6. **APPROVE with exception notice and conditions**

---

### Scenario 6: E-book Download (Regular Customer)
**Order:** ORD-1001 - "The Art of War" (E-book)
**Customer:** Maximus Decimus (Regular)
**Status:** Downloaded
**Expected Flow:**
1. Look up → Greet → Policy check → DENY (digital products non-returnable)
2. VIP check → FALSE
3. Polite denial: "E-books are non-returnable once downloaded per our policy"

---

### Scenario 7: Angry Customer (Immediate Escalation)
**Order:** ORD-999 - "The Matrix and Philosophy"
**Customer:** Neo Anderson (Regular)
**Sentiment:** ANGRY (delayed shipment)
**Expected Flow:** Detect angry sentiment → **IMMEDIATE ESCALATE** (no policy checks)

---

### Scenario 8: Damaged Book (Always Returnable)
**Order:** ORD-333 - "Pirates of the Caribbean Visual Guide"
**Customer:** Jack Sparrow (Regular)
**Status:** Customer spilled rum on book, pages damaged
**Expected Flow:**
1. Look up → Greet → Customer explains damage
2. Policy check → Customer-damaged books typically non-returnable
3. BUT customer says "It arrived already damaged" → Always approve damaged in transit

---

## Key Bookstore Concepts

### Return Policy Priorities (in order):
1. **Damaged in transit** - Always returnable
2. **Wrong book shipped** - Always returnable
3. **Book Club VIP exceptions** - Can override policies (with precedents)
4. **Holiday gift exceptions** - Extended windows for Nov-Dec
5. **Standard policy** - 30 days, unread condition
6. **Non-returnable** - Digital goods, personalized, read books

### Book Condition States:
- **Unread:** Straight spine, no markings, pristine
- **Read:** Bent spine, dog-eared pages, wear
- **Damaged:** Water damage, torn pages, stains
- **Opened (digital):** Downloaded, accessed
- **Unopened (shrink-wrapped):** Original packaging intact

### Customer Tiers:
- **Book Club Platinum:** $50k+ (highest exceptions)
- **Book Club Gold:** $12-15k
- **Book Club Silver:** $5-8k
- **Regular:** No minimum

---

## Testing Checklist

After reinitialization, test these scenarios:

### ✅ Standard Returns
- [ ] Unread hardcover book (should approve)
- [ ] Unread paperback book (should approve)
- [ ] Late return >30 days (should deny for regular customer)

### ✅ Digital Products
- [ ] Downloaded e-book (should deny, non-returnable)
- [ ] Downloaded audiobook (should deny for regular, check VIP precedent)
- [ ] Digital gift card (should deny, non-returnable)

### ✅ VIP Exceptions
- [ ] VIP read book exception (ORD-777, Sarah Connor)
- [ ] Holiday gift book (ORD-888, Jack Ryan)
- [ ] VIP audiobook (ORD-222, Ethan Hunt)

### ✅ Edge Cases
- [ ] Angry customer (should escalate immediately)
- [ ] Personalized inscription (should deny, final sale)
- [ ] Damaged in transit (should approve)
- [ ] Wrong book shipped (should approve)

---

## Database Reinitialization Required

⚠️ **IMPORTANT:** After these changes, you MUST reinitialize the graph database:

```bash
python scripts/init_graph.py
```

**Expected Output:**
```
📦 Backed up old database...
🗑️  Cleared existing database...
⚙️  Initializing Kùzu Graph Database...
Creating Person table...
Creating Decision table...
Creating Product table...
Creating Tag table...
Creating relationships...
✅ Schema created successfully!

📊 Seeding with converted precedents...
  → Converting PREC-VIP-001 (VIP Read Book)...
  → Converting PREC-HOL-002 (Holiday Gift Book)...
  → Converting PREC-AUDIO-003 (Book Club VIP Audiobook)...
  ✅ 3 precedents converted successfully

✅ Graph initialized with Decision Ledger schema!
```

---

## Architecture Notes

### What Stayed the Same:
- ✅ Agent logic (ReAct loop)
- ✅ Tool system (7 tools unchanged)
- ✅ Service layer (EnterpriseServices)
- ✅ Governance layers (DB → Policy → Precedents)
- ✅ Audit logging system
- ✅ Observability (Phoenix)
- ✅ VIP exception protocol
- ✅ Session tracking
- ✅ Admin trace viewer

### What Changed:
- 🔄 Mock data (orders, customers)
- 🔄 Return policy (book-specific rules)
- 🔄 Decision precedents (bookstore scenarios)
- 🔄 Graph database seed data
- 🔄 Product categories in graph (books, audiobooks, signed_books)
- 🔄 Tags in graph (book-related)

### What Needs Updating (Beyond This PR):
- [ ] System prompt in `config.py` (mentions of TrueCart → Bookly)
- [ ] UI branding (logo, colors, etc.)
- [ ] Chainlit config (app name)
- [ ] Documentation references
- [ ] README examples

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Orders Updated | 10 |
| Orders Added | 2 |
| Customers Updated | 10 |
| Customers Added | 2 |
| Policy Sections | 10 |
| Precedents | 3 |
| Graph Persons | 3 |
| Graph Decisions | 3 |
| Graph Products | 3 |
| Graph Tags | 17 |

---

## Next Steps

1. ✅ Mock data updated
2. ✅ Policies rewritten
3. ✅ Precedents updated
4. ✅ Graph initialization script updated
5. ⏭️ Run `python scripts/init_graph.py`
6. ⏭️ Test all scenarios
7. ⏭️ Update system prompt (config.py)
8. ⏭️ Update UI branding
9. ⏭️ Update documentation

---

**Rebrand completed by:** Claude Sonnet 4.5
**Date:** February 7, 2026
**Branch:** `rebrand_bookly`
**Status:** ✅ Data layer complete, ready for testing
