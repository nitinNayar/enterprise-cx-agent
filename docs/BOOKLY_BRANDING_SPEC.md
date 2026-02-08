# Bookly Branding Specification

## Overview

This document outlines the branding specifications for Bookly, an AI-powered online bookshop. The branding has been updated from "TrueCart" to "Bookly" to better reflect the business focus on books and literature.

---

## Brand Identity

### Brand Name
**Bookly**

### Tagline
"Your AI-Powered Bookshop Assistant"

### Brand Personality
- **Intelligent** - Leverages AI for personalized service
- **Literary** - Celebrates books and reading culture
- **Friendly** - Approachable and helpful
- **Efficient** - Fast, accurate support
- **Trustworthy** - Reliable customer service

---

## Required Brand Assets

### Logo Files (TO BE CREATED)

The following image files need to be created and placed in `/public/`:

#### 1. Light Mode Logo
- **Filename:** `Bookly_Light.png`
- **Dimensions:** 300x300px (minimum), vector preferred
- **Format:** PNG with transparent background (or SVG)
- **Usage:** Main logo for light theme UI, header, avatar

#### 2. Dark Mode Logo
- **Filename:** `Bookly_dark.png`
- **Dimensions:** 300x300px (minimum), vector preferred
- **Format:** PNG with transparent background (or SVG)
- **Usage:** Logo for dark theme UI (optional, can use light version)

---

## Logo Design Recommendations

### Concept 1: Book + Technology Fusion
- **Icon:** Stylized open book with subtle tech elements
- **Elements:**
  - Open book pages forming a "B" shape
  - Circuit board pattern or digital pixels in background
  - Clean, modern lines

### Concept 2: Typography-Focused
- **Icon:** Elegant "B" lettermark
- **Elements:**
  - Serif or modern sans-serif typeface
  - Book spine integrated into letter design
  - Minimalist and clean

### Concept 3: Abstract Book Symbol
- **Icon:** Abstract representation of stacked books
- **Elements:**
  - 3-4 horizontal rectangles representing book spines
  - Gradient or solid colors
  - Modern, geometric style

### Color Palette Recommendations

#### Primary Colors
- **Deep Blue:** #2B5E82 (Intelligence, Trust)
  - Represents reliability and professionalism
  - Good contrast for text

- **Warm Brown:** #8B6F47 (Books, Literature)
  - Evokes classic book bindings and aged paper
  - Warm, inviting feeling

- **Sage Green:** #7A9D7E (Growth, Knowledge)
  - Represents growth through reading
  - Calming, natural

#### Secondary Colors
- **Accent Gold:** #D4AF37
  - Premium feel
  - Use for highlights and CTAs

- **Soft Cream:** #F5F1E8
  - Background color
  - Paper-like feel

- **Dark Gray:** #333333
  - Text and UI elements

#### Current CSS Variables
The brand.css file can be updated with Bookly color scheme:
```css
:root {
  --bookly-primary: #2B5E82;
  --bookly-secondary: #8B6F47;
  --bookly-accent: #D4AF37;
  --bookly-background: #F5F1E8;
  --bookly-text: #333333;
}
```

---

## Typography

### Headings
- **Font Family:** Merriweather, Georgia, serif
- **Weight:** 700 (Bold) for main headings
- **Style:** Classic, readable serif for literary feel

### Body Text
- **Font Family:** Inter, -apple-system, sans-serif
- **Weight:** 400 (Regular), 600 (Semi-bold) for emphasis
- **Style:** Clean, modern sans-serif for readability

### Code Example
```css
h1, h2, h3, h4, h5, h6 {
  font-family: 'Merriweather', Georgia, serif;
  font-weight: 700;
}

body, p, div {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  font-weight: 400;
}
```

---

## Icon and Visual Style

### Icon Style
- **Type:** Line icons with rounded edges
- **Weight:** 2px stroke weight
- **Style:** Minimalist, modern, friendly

### Book-Related Icons to Use
- 📚 Stack of books
- 📖 Open book
- 🔖 Bookmark
- 📕 Closed book
- ✨ Sparkles (for recommendations)

---

## Implementation Status

### ✅ Completed Updates
- [x] Updated `.chainlit/config.toml` - Changed name from "TrueCart" to "Bookly"
- [x] Updated `chainlit.md` - Revised welcome message and description
- [x] Updated `app.py` - Changed chat profile names
- [x] Updated logo file references to `Bookly_Light.png` and `Bookly_dark.png`

### ❌ Pending - Requires External Design Work
- [ ] Create `Bookly_Light.png` logo file
- [ ] Create `Bookly_dark.png` logo file (optional)
- [ ] Update `public/brand.css` with Bookly color scheme (optional)
- [ ] Create favicon.ico for browser tab

---

## How to Create Logo Files

### Option 1: AI Image Generators
Use DALL-E, Midjourney, or similar tools with prompts like:
```
"Modern minimalist logo for 'Bookly' bookshop,
featuring an open book icon, clean lines,
blue and brown color scheme, professional,
transparent background, vector style"
```

### Option 2: Design Tools
- **Figma** (free, web-based)
- **Canva** (free tier available)
- **Adobe Illustrator** (professional, paid)
- **Inkscape** (free, open-source)

### Option 3: Hire a Designer
- Fiverr: $5-50 for simple logos
- Upwork: Professional designers
- 99designs: Design contest platform

### Option 4: Use Icon Libraries
Temporarily use a book icon from:
- **Font Awesome:** `fa-book` or `fa-book-open`
- **Material Icons:** `menu_book` or `import_contacts`
- **Heroicons:** Book icon sets

---

## Temporary Placeholder

Until custom logos are created, you can use:

### Text-Based Logo
Add this to `public/brand.css`:
```css
.logo-text {
  font-family: 'Merriweather', serif;
  font-size: 24px;
  font-weight: 700;
  color: #2B5E82;
}

.logo-text::before {
  content: "📚 ";
}
```

### Emoji Placeholder
Use 📚 (book emoji) as temporary logo until custom assets are created.

---

## Files Updated in This Rebrand

1. **`.chainlit/config.toml`**
   - Changed `name` to "Bookly"
   - Updated `description` for bookshop context
   - Changed logo references to `Bookly_Light.png`

2. **`chainlit.md`**
   - Updated welcome message
   - Changed feature descriptions to book-focused
   - Updated tone for bookshop audience

3. **`app.py`**
   - Updated chat profile names to "Bookly Support" and "Bookly Admin"
   - Changed profile descriptions

4. **`policies/*.md`**
   - All policy files reference "Bookly" brand
   - return_policy.md, shipping_policy.md, privacy_policy.md, password_reset.md, faq.md

---

## Next Steps

1. **Create Logo Files**
   - Design and export `Bookly_Light.png` and `Bookly_dark.png`
   - Place in `/public/` directory

2. **Optional Enhancements**
   - Update `public/brand.css` with Bookly color scheme
   - Create custom favicon
   - Add book-themed illustrations to UI

3. **Testing**
   - Run `chainlit run app.py` to verify branding
   - Check light and dark modes
   - Verify all references are updated

---

## Contact

For questions about branding implementation:
- **Project Lead:** [Your Name]
- **Design Team:** [Designer Contact]

---

*Last Updated: February 2026*
*Version: 1.0 - Initial Bookly Rebrand*
