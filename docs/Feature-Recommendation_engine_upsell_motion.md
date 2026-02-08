Goal of the feature: In the interview I want to demonstrate book recommendation. This will be used for when a user asks for a return. When a user asks for a return, we should recommend a book in exchange. If they are a 
(1) SILVER Tier: they should be offered a 10% discount
(2) GOLD Tier: they should be offered a 15% discount
(3) PLATINUM Tier: they should be offered a 25% discount

How to implement the recommendation engine:

This is a simple demo, so lets keep it simple
Approach:  Use simple rule-based recommendations + LLM explanations. This is honest, explainable, and shows modern AI integration.

Something simple like:  Use a rule-based system + LLM for explanations.
Simple Pseudo-Code Approach:
pythondef get_recommendations(user, n=5):
    recommendations = []
    
    # Rule 1: Books by same authors they liked (strongest signal)
    if user.liked_books:
        same_author_books = find_books_by_same_authors(user.liked_books)
        recommendations.extend(same_author_books[:2])
    
    # Rule 2: Books in favorite genres they haven't seen
    if user.favorite_genres:
        genre_books = find_top_rated_in_genres(user.favorite_genres)
        recommendations.extend(genre_books[:2])
    
    # Rule 3: "Trending with similar users" (fake it!)
    # Just grab highly rated books with similar genre tags
    similar_taste_books = find_popular_in_similar_genres(user)
    recommendations.extend(similar_taste_books[:1])
    
    # Deduplicate and return
    return unique(recommendations)[:n]
```

**Then add LLM-generated explanations for each recommendation.**

This is:
- ✅ Implemented in 30 minutes
- ✅ Easy to explain
- ✅ Actually works well for demos
- ✅ Shows modern AI integration (LLM explanations)
- ✅ Leaves time for the rest of your bookstore

---

## My Honest Recommendation

**What to actually build for your demo:**
```
70% - Core bookstore features
│   ├─ Clean UI for browsing/search
│   ├─ Book detail pages
│   ├─ Shopping cart
│   └─ Basic user profile
│
30% - "Smart" recommendations
    ├─ Simple rule-based logic (3-4 rules)
    └─ LLM-generated explanations (the wow factor)


Think about it step-by-step and think deeply
if you make any assumptions, show it with the <assumptions> tag show me your thinking with the <thinking> tag

If you don't know the resposne, or don't have enough information to answer with good confidence, please let me know

Don't hallucinate