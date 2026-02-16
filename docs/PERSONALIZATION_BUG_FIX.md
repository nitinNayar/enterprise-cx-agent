# Personalization Bug Fix - Generic Offer Message

## 🐛 The Bug

**Observed:** Agent uses generic message when offering recommendations

```
"Would you be interested in seeing a couple book recommendations
that might interest you (with your 15% Gold VIP discount)?"
```

**Expected:** Agent should use specific genres/authors

```
"I noticed you've loved thrillers by Lee Child and Michael Connelly
(you gave Killing Floor 5 stars!). Would you be interested in seeing
a couple similar books (with your 15% Gold VIP discount)?"
```

---

## 🔍 Root Cause Analysis

### Step-by-Step Diagnosis:

1. **Agent calls `get_customer_info`** (early in workflow) ✓
2. **Agent needs reading preferences** to craft personalized offer
3. **Prompt instructs:** "Look for `reading_preferences.favorite_genres`"
4. **Agent searches customer_info response...** ❌ NOT FOUND
5. **Agent falls back to generic message** ❌

### The Mismatch:

**Prompt told agent:**
```
"You already called get_customer_info earlier - use that data!
 Look for reading_preferences.favorite_genres
 Look for purchase_history to find authors"
```

**But `get_customer_info` returned:**
```python
{
  "customer_name": "John McClane",
  "is_vip": true,
  "tier": "Gold",
  "years_active": 5
  # ❌ NO reading_preferences
  # ❌ NO favorite_genres
  # ❌ NO purchase_history
}
```

### Root Cause:

**Data mismatch between prompt expectations and service response**

- Prompt assumes reading preferences are in customer_info
- Service doesn't return reading preferences
- Agent has no data to craft personalized message
- Falls back to generic phrasing

---

## 🔧 The Fix

### Change 1: Updated `get_customer_info` Service

**File:** `services/services.py` (lines 113-156)

**Added to response:**

```python
{
  # Existing fields
  "customer_name": "John McClane",
  "is_vip": true,
  "tier": "Gold",
  "years_active": 5,

  # NEW: Reading preferences for personalization
  "reading_preferences": {
    "favorite_genres": ["Action Thrillers", "Detective Fiction"],
    "favorite_authors": ["Lee Child", "Michael Connelly"],
    "preferred_formats": ["Hardcover", "Paperback"]
  },

  # NEW: Purchase summary for personalization
  "purchase_summary": {
    "top_authors": ["Lee Child", "Michael Connelly", "James Patterson"],
    "highly_rated_books": [
      {
        "title": "Killing Floor",
        "author": "Lee Child",
        "rating": 5
      }
    ]
  }
}
```

**Logic added:**
- Extracts `reading_preferences` from customer data
- Analyzes `purchase_history` to find top authors (by purchase count)
- Identifies highly-rated books (rating >= 4)
- Returns top 3 of each for conciseness

### Change 2: Updated Prompt Instructions

**File:** `prompts.py` (lines 237-242)

**Before:**
```
- Look for reading_preferences.favorite_genres
- Look for purchase_history to find authors
```

**After:**
```
- Extract from the response:
  * reading_preferences.favorite_genres
  * reading_preferences.favorite_authors
  * purchase_summary.top_authors
  * purchase_summary.highly_rated_books
- Use this to craft a SPECIFIC, personalized offer
```

**Also added concrete examples:**
```
If reading_preferences.favorite_genres = ["Action Thrillers"]
→ "I noticed you love action thrillers..."

If purchase_summary.top_authors = ["Lee Child", "Michael Connelly"]
→ "Since you've enjoyed books by Lee Child and Michael Connelly..."

If highly_rated_books includes "Killing Floor" (rating: 5)
→ "...you gave Killing Floor 5 stars!"
```

---

## 🧪 Test the Fix

### Before:
```
Agent: "Would you be interested in seeing a couple book
       recommendations that might interest you?"
```

### After:
```
Agent: "I noticed you've loved action thrillers by Lee Child
       and Michael Connelly (you gave Killing Floor 5 stars!).
       Would you be interested in seeing a couple similar books?"
```

### Test Script:

```bash
chainlit run app.py -w
```

**Input:**
```
I want to return my order
ORD-123
Yes, unopened
```

**Watch for:**
- ✅ Specific genres mentioned ("action thrillers", "detective fiction")
- ✅ Specific authors mentioned ("Lee Child and Michael Connelly")
- ✅ Specific books mentioned ("Killing Floor")
- ✅ Ratings mentioned ("you gave it 5 stars!")
- ❌ NO generic phrases ("book recommendations that might interest you")

---

## 📊 Before vs After

| Aspect | Before (Generic) | After (Specific) |
|--------|------------------|------------------|
| **Data available** | Name, VIP, years only | + genres, authors, books |
| **Message** | "book recommendations that might interest you" | "loved thrillers by Lee Child and Michael Connelly" |
| **Personalization** | None | High (references actual purchases) |
| **Customer feeling** | "They don't know me" | "They remember what I like!" |

---

## 🎯 Why This Fix Works

### 1. **Data Availability**
- Agent now has reading preferences in `get_customer_info` response
- No need to guess or use generic language
- Data is available when needed (before making offer)

### 2. **Explicit Examples**
- Prompt shows exact format: "If favorite_genres = X, say Y"
- Agent can pattern-match and apply to customer
- Removes ambiguity

### 3. **Purchase Summary**
- Don't need to analyze full purchase history
- Pre-computed: top authors, highly-rated books
- Lightweight and actionable

### 4. **Right Timing**
- Reading preferences loaded early (with customer_info)
- Available when crafting offer (step 7)
- Don't need second API call

---

## 🚨 Edge Cases Handled

### Customer with no purchase history:
```python
"reading_preferences": {
  "favorite_genres": [],  # Empty
  "favorite_authors": []
},
"purchase_summary": {
  "top_authors": [],
  "highly_rated_books": []
}
```

**Agent behavior:** Will fall back to simpler offer:
- "Would you like to see a couple recommendations?"
- Still better than before (at least knows there's no data)

### Customer with minimal data:
```python
"reading_preferences": {
  "favorite_genres": ["Thriller"]  # Just one genre
}
```

**Agent behavior:** Uses what's available:
- "Since you enjoy thrillers..."

---

## 📁 Files Modified

1. **services/services.py**
   - Updated `get_customer_info()` method
   - Added reading_preferences extraction
   - Added purchase_summary computation

2. **prompts.py**
   - Updated personalization instructions
   - Added explicit examples with data paths
   - Added good/bad examples

---

## ✅ Success Criteria

After fix, agent should:

- [x] Reference specific genres from customer data
- [x] Reference specific authors from customer data
- [x] Reference specific books customer rated highly
- [x] Include ratings ("you gave it 5 stars!")
- [x] Feel personalized, not templated
- [x] Never use "book recommendations that might interest you"

---

## 🎓 Lessons Learned

### For System Design:

1. **Match prompt expectations to data availability**
   - If prompt says "look for X", ensure X is in the data
   - Document what each tool/service returns

2. **Provide examples with exact data paths**
   - "If field X = Y, say Z"
   - Removes guesswork

3. **Preprocess data for agent consumption**
   - Don't make agent analyze purchase history
   - Give it pre-computed summaries

4. **Test with actual data**
   - Use real customer records in tests
   - Verify personalization appears

---

## 🔄 Future Improvements

1. **Smarter fallbacks:**
   - If no authors, use genres
   - If no genres, acknowledge loyalty instead

2. **More context:**
   - Recent purchases (last 3 months)
   - Reading trends (genre shifts)

3. **A/B Testing:**
   - Measure conversion rate: generic vs specific
   - Track customer satisfaction

---

**Last Updated:** 2026-02-09
**Status:** ✅ Fixed and deployed
