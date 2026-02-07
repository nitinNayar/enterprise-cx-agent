# Book Recommendation Data Model

**Comprehensive guide to customer data for personalized book recommendations**

---

## Overview

This document describes the enhanced customer data model designed to support sophisticated book recommendation algorithms. The data structure balances personalization with privacy and supports multiple recommendation strategies.

---

## Data Categories

### 1. Demographics
**Purpose:** Segment customers and understand context

```json
"demographics": {
  "age_range": "30-39",
  "location": "San Francisco, CA",
  "occupation": "Software Engineer"
}
```

**Recommendation Use Cases:**
- Age-appropriate content
- Regional author preferences
- Professional interest books
- Life stage recommendations (parenting books, retirement planning, etc.)

**Privacy Considerations:**
- Optional fields
- Age range (not exact age)
- City/state (not full address)

---

### 2. Reading Preferences
**Purpose:** Core matching for content recommendations

```json
"reading_preferences": {
  "favorite_genres": ["Cyberpunk", "Philosophy", "Tech Thrillers"],
  "favorite_authors": ["William Gibson", "Neal Stephenson"],
  "preferred_formats": ["E-book (60%)", "Paperback (40%)"],
  "reading_pace": "4-5 books/month",
  "preferred_length": "Any length",
  "listening_speed": "1.5x"  // For audiobooks
}
```

**Recommendation Use Cases:**
- Genre-based filtering
- "If you like X author, try Y"
- Format-specific promotions (e-book deals)
- Reading pace awareness (suggest series to fast readers)
- Audiobook narrator matching

**Advanced Fields:**
- `listening_speed`: Critical for audiobook recommendations (slow narrators frustrate 2x listeners)
- `preferred_length`: Some readers prefer novellas, others want epics

---

### 3. Explicit Preferences (Likes/Dislikes)
**Purpose:** Fine-tune recommendations, avoid bad matches

```json
"likes": [
  "Fast-paced action",
  "Realistic police work",
  "Strong protagonists",
  "Series with recurring characters",
  "New York-based settings"
],
"dislikes": [
  "Romance subplots",
  "Slow-paced literary fiction",
  "Supernatural elements",
  "Overly complex plots"
]
```

**Recommendation Use Cases:**
- **Positive filtering:** "Customers who like X also liked Y"
- **Negative filtering:** Exclude books with romance if customer dislikes it
- **Thematic matching:** Find books with similar themes
- **Content warnings:** Avoid triggering content

**Why This Matters:**
- A customer who loves sci-fi but hates romance won't like romantic sci-fi
- Someone avoiding supernatural won't want urban fantasy
- Setting preferences matter (NYC-based thrillers vs. rural mysteries)

---

### 4. Purchase History
**Purpose:** Behavioral data for collaborative filtering

```json
"purchase_history": [
  {
    "title": "Snow Crash",
    "author": "Neal Stephenson",
    "genre": "Cyberpunk",
    "purchase_date": "2024-08-01",
    "rating": 5,
    "format": "E-book",
    "edition": "First Edition"  // Optional
  }
]
```

**Recommendation Use Cases:**
- **Collaborative filtering:** "Customers who bought X also bought Y"
- **Author affinity:** Customer bought 5 books by Author X → recommend Author X's new release
- **Genre patterns:** 70% sci-fi purchases → prioritize sci-fi recommendations
- **Series completion:** Bought books 1-3 of series → recommend book 4
- **Price point analysis:** Average spend informs promotion strategy

**Advanced Fields:**
- `rating`: If provided, indicates satisfaction (high-rated authors get priority)
- `edition`: Collectors care about first editions, signed copies
- `format`: Format preference evolution over time

---

### 5. Recommendation Profile
**Purpose:** Synthesized insights for recommendation engine

```json
"recommendation_profile": {
  "series_following": ["Sprawl Trilogy"],
  "content_preferences": "Philosophical, tech-forward, strong female characters",
  "discovery_openness": "Very high",
  "price_sensitivity": "Medium",
  "book_club_participant": true,
  "narrator_preferences": ["Scott Brick", "George Guidall"],  // Audiobooks
  "narrator_avoidance": ["Monotone narrators"],
  "collector": false,
  "wishlist": ["First edition Le Guin"],
  "gift_buyer": true,
  "special_interests": ["AI ethics", "Virtual reality"]
}
```

**Recommendation Use Cases:**

**Series Following:**
- Track which series customer is reading
- Recommend next book in series
- Alert when series continues
- Bundle series at discount

**Discovery Openness:**
- **High:** Recommend indie authors, new releases, experimental genres
- **Medium:** Mix known and new authors
- **Low:** Stick to established authors and series

**Price Sensitivity:**
- **Low:** Premium editions, hardcovers, pre-orders
- **Medium:** Mix of formats, wait for sales
- **High:** Paperback, used books, sale promotions

**Narrator Preferences (Audiobooks):**
- Critical for audiobook satisfaction
- Match customer to narrator style
- Avoid known dislikes
- Example: Customer who loves Scott Brick → recommend his other audiobooks

**Collector Status:**
- Recommend signed editions
- Alert to limited releases
- Offer rare/out-of-print books
- Premium pricing acceptable

**Gift Buyer:**
- Recommend gift-worthy books
- Suggest gift wrapping
- Promote during holidays
- Offer bestsellers (safe gifts)

**Special Interests:**
- Niche topic matching
- Academic interests
- Hobby-related books
- Professional development

---

## Recommendation Algorithm Strategies

### Strategy 1: Content-Based Filtering
**Use:** Find books similar to what customer liked

**Data Used:**
- `favorite_genres`
- `favorite_authors`
- `likes` (themes, settings, pacing)
- `purchase_history` (highly-rated books)

**Algorithm:**
```
For each book in customer's purchase history with rating >= 4:
  Find books with:
    - Same genre
    - Similar themes (from likes)
    - Same author or similar writing style
    - Matching content preferences
  Filter by:
    - Exclude dislikes
    - Match preferred format
    - Match price sensitivity
  Return top N matches
```

---

### Strategy 2: Collaborative Filtering
**Use:** "Customers like you also enjoyed..."

**Data Used:**
- `purchase_history` (all customers)
- `ratings`
- `favorite_genres`

**Algorithm:**
```
Find customers with similar purchase patterns:
  Calculate similarity score based on:
    - Overlapping purchases
    - Similar genre preferences
    - Similar ratings
  For similar customers:
    Find books they highly rated
    That this customer hasn't purchased
    Return top N recommendations
```

---

### Strategy 3: Series Completion
**Use:** Keep readers engaged with series

**Data Used:**
- `series_following`
- `purchase_history`

**Algorithm:**
```
For each series customer is following:
  Identify which books they own
  Find next book(s) in series
  If new release:
    High priority recommendation
  If older:
    Bundle discount offer
```

---

### Strategy 4: Narrator Matching (Audiobooks)
**Use:** Maximize audiobook satisfaction

**Data Used:**
- `narrator_preferences`
- `narrator_avoidance`
- `listening_speed`
- `purchase_history` (audiobook ratings by narrator)

**Algorithm:**
```
For audiobook recommendations:
  Find books narrated by preferred narrators
  Exclude narrators in avoidance list
  Match narration pace to listening speed:
    - Slow narrators (0.8-1.0x native) for 2x+ listeners
    - Dynamic narrators for 1.5x listeners
    - Any narrator for 1.0x listeners
  Filter by genre preferences
  Return top N matches
```

---

### Strategy 5: Discovery Based on Openness
**Use:** Balance exploration and safety

**Data Used:**
- `discovery_openness`
- `favorite_genres`
- `favorite_authors`

**Algorithm:**
```
If discovery_openness == "High":
  70% new/indie authors
  30% established authors
  Include experimental genres adjacent to favorites

If discovery_openness == "Medium":
  40% new authors
  60% established authors
  Stay within favorite genres

If discovery_openness == "Low":
  10% new authors (highly rated only)
  90% established authors and series
  No genre experimentation
```

---

### Strategy 6: Life Stage / Contextual
**Use:** Recommendations based on context

**Data Used:**
- `demographics.age_range`
- `demographics.occupation`
- `special_interests`
- `purchase_history` (recent trends)

**Examples:**
- Parent of young children → parenting books, children's literature
- Career change → professional development in new field
- Retiree → memoir, travel, history
- New hobby → instructional books

---

### Strategy 7: Social/Book Club
**Use:** Community-driven recommendations

**Data Used:**
- `book_club_participant`
- Purchase history of book club members
- Trending books in customer's genre preferences

**Algorithm:**
```
If book_club_participant == true:
  Recommend current book club selections
  Suggest discussion-worthy books
  Highlight group-read opportunities
  Show what other members are reading
```

---

## Advanced Recommendation Features

### 1. Seasonal Recommendations
**Summer Reading:**
- Beach reads (lighter fiction)
- Travel guides
- Fast-paced thrillers

**Holiday Season:**
- Gift-worthy books
- Coffee table books
- Cozy mysteries
- Holiday themes

**Back to School:**
- Academic books
- Study guides
- YA fiction

### 2. Event-Based Recommendations
**Book-to-Movie Adaptations:**
- Movie releasing → recommend book
- Customer loved book → recommend similar adaptations

**Author Events:**
- Author signing near customer's location
- Virtual author talks
- New release pre-orders

**Awards Season:**
- Pulitzer Prize winners
- Hugo/Nebula for sci-fi fans
- Edgar Awards for mystery readers

### 3. Price-Conscious Recommendations
**Daily Deals:**
- Match deals to customer preferences
- Notify when wishlist items on sale
- Personalized bundle offers

**Format Arbitrage:**
- E-book cheaper than hardcover? Suggest format swap
- Audiobook + e-book bundles
- Used books for price-sensitive customers

### 4. Reading Goal Support
**Annual Reading Challenge:**
- Track progress
- Recommend shorter books to meet goal
- Celebrate milestones

**Genre Expansion:**
- "Try something new" recommendations
- Gentle introduction to adjacent genres
- Curated discovery collections

---

## Data Collection Methods

### 1. Explicit Collection (Customer Input)
- **Onboarding Quiz:** "Tell us about your reading preferences"
- **Genre Selection:** Multi-select favorite genres
- **Author Favorites:** Name your top 3 authors
- **Reading Goals:** Books per year target
- **Content Preferences:** Opt-in to triggers/content warnings

### 2. Implicit Collection (Behavioral)
- **Purchase History:** Automatically tracked
- **Browsing Behavior:** Viewed but didn't buy
- **Rating Prompts:** "How did you like this book?"
- **Wish List Additions:** Shows interest
- **Search Queries:** What they're looking for

### 3. Inferred Data
- **Genre Affinity:** Calculate from purchases
- **Discovery Openness:** Ratio of new vs. known authors
- **Price Sensitivity:** Average spend, sale responsiveness
- **Format Preference:** % e-book vs. physical vs. audiobook

---

## Privacy & Ethics

### Data Minimization
- Only collect what's needed for recommendations
- Age range (not exact birthdate)
- City/state (not full address)
- Optional demographic fields

### Transparency
- Explain why recommendations are shown
- "Because you liked [Book X]"
- "Based on your interest in [Genre]"
- "Customers like you also enjoyed..."

### Control
- Edit preferences anytime
- Clear individual recommendations
- Opt-out of personalization
- Delete purchase history from recommendations

### Bias Mitigation
- Avoid recommendation bubbles
- Include diversity in discovery recommendations
- Don't over-personalize (show bestsellers too)
- Surface diverse authors

---

## Recommendation UI/UX

### Recommendation Sections

**Homepage:**
- "Recommended for You" (personalized)
- "Because You Loved [Book]" (content-based)
- "Popular in [Genre]" (collaborative + trending)
- "Continue Your Series" (series completion)
- "New Releases in Your Genres"

**Product Pages:**
- "Customers Also Bought" (collaborative)
- "Similar Books" (content-based)
- "From the Same Author"
- "More Like This"

**Email Campaigns:**
- Weekly personalized picks
- Wishlist price drop alerts
- New releases from favorite authors
- "Finishing that series?" reminders

---

## Metrics to Track

### Recommendation Quality
- **Click-through Rate:** % who click recommended books
- **Conversion Rate:** % who purchase recommended books
- **Discovery Rate:** % who try new authors/genres
- **Satisfaction:** Ratings of recommended books

### Business Impact
- **Revenue from Recommendations:** % of sales from recommended items
- **Average Order Value:** Recommendations increase basket size?
- **Repeat Purchase:** Do good recommendations drive loyalty?
- **Churn Reduction:** Engaged customers stay longer

### Data Quality
- **Profile Completeness:** % of customers with rich profiles
- **Rating Frequency:** How often customers rate books
- **Preference Accuracy:** Do preferences match behavior?

---

## Implementation Roadmap

### Phase 1: Foundation (Months 1-2)
- Collect basic preferences (genres, authors)
- Track purchase history
- Implement simple content-based filtering
- Test with VIP customers

### Phase 2: Personalization (Months 3-4)
- Add collaborative filtering
- Implement series tracking
- Add explicit likes/dislikes
- A/B test recommendation strategies

### Phase 3: Advanced Features (Months 5-6)
- Narrator matching for audiobooks
- Discovery openness algorithm
- Wishlist price alerts
- Book club integration

### Phase 4: Optimization (Months 7-8)
- Machine learning model training
- Real-time recommendations
- Cross-platform sync
- API for third-party integrations

---

## Technology Stack Suggestions

### Data Storage
- **PostgreSQL:** Customer profiles, purchase history
- **Neo4j / Graph DB:** Collaborative filtering, customer similarity
- **Redis:** Real-time recommendation caching
- **Elasticsearch:** Book search and content matching

### Recommendation Engine
- **Python:** scikit-learn for basic ML
- **TensorFlow/PyTorch:** Deep learning for complex patterns
- **Apache Spark:** Large-scale collaborative filtering
- **FastAPI:** Recommendation API service

### Real-time Processing
- **Kafka:** Purchase event streaming
- **Apache Flink:** Real-time preference updates
- **Redis Streams:** Hot recommendations cache

---

## Example Queries

### Query 1: Content-Based Recommendation
```sql
-- Find books similar to customer's favorites
SELECT DISTINCT b.title, b.author, b.genre
FROM books b
JOIN book_themes bt ON b.id = bt.book_id
WHERE bt.theme IN (
  SELECT theme FROM customer_preferences
  WHERE customer_id = 'CUST-VIP-0001'
  AND preference_type = 'likes'
)
AND b.genre IN (
  SELECT favorite_genre FROM customers
  WHERE customer_id = 'CUST-VIP-0001'
)
AND b.id NOT IN (
  SELECT book_id FROM purchases
  WHERE customer_id = 'CUST-VIP-0001'
)
ORDER BY b.rating DESC, b.popularity DESC
LIMIT 10;
```

### Query 2: Collaborative Filtering
```sql
-- Find books purchased by similar customers
WITH similar_customers AS (
  SELECT customer_id, similarity_score
  FROM customer_similarity
  WHERE base_customer_id = 'CUST-VIP-0001'
  ORDER BY similarity_score DESC
  LIMIT 50
)
SELECT b.title, b.author, COUNT(*) as purchase_count, AVG(r.rating) as avg_rating
FROM purchases p
JOIN similar_customers sc ON p.customer_id = sc.customer_id
JOIN books b ON p.book_id = b.id
LEFT JOIN ratings r ON b.id = r.book_id AND r.customer_id IN (SELECT customer_id FROM similar_customers)
WHERE p.book_id NOT IN (
  SELECT book_id FROM purchases WHERE customer_id = 'CUST-VIP-0001'
)
GROUP BY b.id, b.title, b.author
HAVING AVG(r.rating) >= 4.0
ORDER BY purchase_count DESC, avg_rating DESC
LIMIT 10;
```

### Query 3: Series Completion
```sql
-- Find next books in customer's active series
SELECT s.series_name, b.title, b.book_number, b.release_date
FROM series s
JOIN books b ON s.series_id = b.series_id
WHERE s.series_id IN (
  SELECT DISTINCT b2.series_id
  FROM purchases p
  JOIN books b2 ON p.book_id = b2.id
  WHERE p.customer_id = 'CUST-VIP-0001'
  AND b2.series_id IS NOT NULL
)
AND b.id NOT IN (
  SELECT book_id FROM purchases
  WHERE customer_id = 'CUST-VIP-0001'
)
ORDER BY s.series_name, b.book_number;
```

---

## Conclusion

This enhanced customer data model enables sophisticated, multi-strategy book recommendations while respecting customer privacy and control. The key is balancing explicit preferences (what customers tell us) with implicit behavior (what they actually do) and collaborative signals (what similar customers enjoy).

**Key Takeaways:**
1. **Multi-dimensional profiles** enable better matching
2. **Explicit likes/dislikes** prevent bad recommendations
3. **Purchase history** is gold for collaborative filtering
4. **Discovery openness** prevents recommendation bubbles
5. **Format preferences** matter (especially audiobook narrators!)
6. **Privacy-first** design builds trust

---

*Last Updated: February 2026*
*File: `data/mock_customers_enhanced.json`*
