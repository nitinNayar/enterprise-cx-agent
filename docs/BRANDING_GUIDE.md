# TrueCart - Branding Guide

This guide explains how to customize the branding of your Chainlit UI to match your company's brand identity.

## Table of Contents

1. [Overview](#overview)
2. [What's Been Set Up](#whats-been-set-up)
3. [Quick Customization](#quick-customization)
4. [Advanced Customization](#advanced-customization)
5. [File Structure](#file-structure)
6. [Testing Your Changes](#testing-your-changes)

---

## Overview

Your Chainlit application has been configured with custom branding for **TrueCart**. The branding includes:

- Custom logo and avatar
- Brand color scheme
- Custom CSS styling
- Branded welcome message
- Header navigation links

## What's Been Set Up

### 1. **Logo Files** (`/public/`)

Your logo files are located in the `public/` directory:
- `TrueCart_Light.png` - Used for light mode
- `TrueCart_dark.png` - Available for dark mode

**Currently Active:** Light version is set as both logo and avatar.

### 2. **Custom CSS** (`/public/brand.css`)

A comprehensive CSS file with:
- Brand color variables (easy to customize)
- Typography settings
- Component styling (buttons, messages, cards)
- Dark mode support
- Responsive design
- Accessibility features

### 3. **Configuration** (`.chainlit/config.toml`)

Updated settings:
- Assistant name: "Structura AI"
- Default theme: Light
- Layout: Wide
- Logo paths configured
- Custom CSS enabled
- Header links added

### 4. **Welcome Message** (`chainlit.md`)

Customized welcome screen with:
- Branded greeting
- Feature highlights
- Usage instructions
- Admin mode information

---

## Quick Customization

### Change Brand Colors

Edit `/public/brand.css` and modify these CSS variables:

```css
:root {
  /* Change these to your brand colors */
  --brand-primary: #2563eb;        /* Your main brand color */
  --brand-primary-hover: #1d4ed8;  /* Darker shade */
  --brand-primary-light: #dbeafe;  /* Light shade */

  --brand-secondary: #7c3aed;      /* Accent color */
}
```

**Recommended Color Tools:**
- [Coolors.co](https://coolors.co/) - Color palette generator
- [ColorSpace](https://mycolor.space/) - Color scheme generator
- [Adobe Color](https://color.adobe.com/) - Advanced color tools

### Change Company Name

Edit `.chainlit/config.toml`:

```toml
[UI]
name = "Your Company Name"
description = "Your company description here"
```

Also update `chainlit.md` to reflect your company name in the welcome message.

### Update Logo

#### Step 1: Prepare Your Logo Files

Create your logo files with these specifications:

**Logo Specifications:**
- **Format:** PNG with transparency (recommended) or JPG
- **Recommended size:** 200-400px width, height proportional
- **Aspect ratio:** Maintain proportions (e.g., 2:1, 3:1, or square)
- **File size:** Keep under 500KB (ideally under 100KB for fast loading)
- **Background:** Transparent PNG works best for all themes
- **Versions:** You can create separate versions for light/dark mode if desired

**Naming Convention:**
- Light mode: `YourCompany_Light.png` (note the capital L)
- Dark mode: `YourCompany_dark.png` (note the lowercase d)
- Example: `TrueCart_Light.png` and `TrueCart_dark.png`

#### Step 2: Place Logo Files in `/public/` Directory

1. Save your logo files to the `/public/` directory in your project root:
   ```
   enterprise-cx-agent/
   └── public/
       ├── TrueCart_Light.png
       └── TrueCart_dark.png
   ```

2. Verify files are in place:
   ```bash
   ls -la public/
   ```

#### Step 3: Configure Logo in `.chainlit/config.toml`

Open `.chainlit/config.toml` and find the `[UI]` section (around line 140):

```toml
# Load assistant logo directly from URL.
# Using the light version for light mode (dark version available at /public/TrueCart_dark.png)
logo_file_url = "/public/TrueCart_Light.png"

# Load assistant avatar image directly from URL.
# You can use the same logo or a different avatar image
default_avatar_file_url = "/public/TrueCart_Light.png"
```

**What each setting does:**
- `logo_file_url` - Logo shown in the header (top-left corner)
- `default_avatar_file_url` - Avatar shown next to assistant messages

**Path format:** `/public/filename.png` (must start with `/public/`)

#### Step 4: Configure Chat Profile Icons in `app.py`

Open `app.py` and find the `@cl.set_chat_profiles` function (around line 13):

```python
@cl.set_chat_profiles
async def chat_profile():
    return [
        cl.ChatProfile(
            name="TrueCart Support",
            markdown_description="Talk to our AI support agent to resolve your order issues.",
            icon="/public/TrueCart_Light.png"  # Update this path
        ),
        cl.ChatProfile(
            name="TrueCart Admin",
            markdown_description="**Admin Only**: View decision traces for any customer session.",
            icon="/public/TrueCart_Light.png"  # Update this path
        )
    ]
```

**Important:** The `icon` parameter controls what logo appears:
- In the chat profile selection screen
- In the header when that profile is active
- As the avatar in messages

#### Step 5: Restart Application

After making changes, restart Chainlit:

```bash
# Stop the server (Ctrl+C)
# Then restart
chainlit run app.py
```

**Clear browser cache:**
- Mac: `Cmd + Shift + R`
- Windows/Linux: `Ctrl + Shift + R`

#### Where Your Logo Appears

Your logo will be visible in multiple locations:

1. **Header Logo** (top-left)
   - Controlled by: `logo_file_url` in config.toml
   - When: On initial load and when no profile is selected

2. **Chat Profile Icon** (header when profile active)
   - Controlled by: `icon` parameter in `app.py` chat profiles
   - When: After selecting a chat profile
   - Replaces the header logo

3. **Profile Selection Cards**
   - Controlled by: `icon` parameter in `app.py` chat profiles
   - When: On the profile selection screen

4. **Message Avatar** (next to assistant messages)
   - Controlled by: `default_avatar_file_url` in config.toml
   - When: Every time the assistant sends a message
   - Shows circular avatar next to message bubble

5. **Welcome Screen Avatar** (center of page)
   - Controlled by: `default_avatar_file_url` in config.toml
   - When: Initial chat view before any messages

#### Advanced: Using Different Logos for Different Purposes

You can use different images for different purposes:

**Example - Different logo vs avatar:**
```toml
# Wide logo for header
logo_file_url = "/public/TrueCart_Logo_Wide.png"

# Square icon for avatar
default_avatar_file_url = "/public/TrueCart_Icon_Square.png"
```

**Example - Different icons per chat profile:**
```python
cl.ChatProfile(
    name="TrueCart Support",
    icon="/public/TrueCart_Support_Icon.png"
),
cl.ChatProfile(
    name="TrueCart Admin",
    icon="/public/TrueCart_Admin_Icon.png"
)
```

#### Troubleshooting Logo Issues

**Logo not showing (broken image icon):**
1. Check file exists: `ls public/YourLogo.png`
2. Verify exact filename (case-sensitive): `TrueCart_Light.png` ≠ `truecart_light.png`
3. Check path format: Must be `/public/filename.png` (starts with `/`)
4. Look for 404 errors in browser console (F12 → Console tab)
5. Restart Chainlit server
6. Clear browser cache (Ctrl+Shift+R)

**Logo appears pixelated:**
- Use higher resolution image (at least 200px width)
- Save as PNG for better quality
- Ensure you're not upscaling a small image

**Logo appears distorted:**
- Check original aspect ratio
- Don't specify fixed width/height in CSS
- Let Chainlit auto-resize proportionally

**Logo too large/small:**
- Edit `/public/brand.css` and adjust:
  ```css
  .logo img {
    max-height: 40px;  /* Increase this for larger logo */
    width: auto;
  }
  ```

**Logo showing old cached version:**
- Hard refresh: Ctrl+Shift+R
- Clear all browser cache
- Try incognito/private browsing mode
- Rename file (e.g., `logo_v2.png`) and update config

#### Using External URLs for Logos

Instead of local files, you can use external URLs:

```toml
logo_file_url = "https://yourdomain.com/images/logo.png"
default_avatar_file_url = "https://yourdomain.com/images/avatar.png"
```

```python
icon="https://yourdomain.com/images/icon.png"
```

**Pros:**
- No need to include files in repository
- Easy to update without redeploying
- Can use CDN for faster loading

**Cons:**
- Requires external hosting
- Won't work offline
- Depends on external service availability

### Change Welcome Message

Edit `chainlit.md` at the root of your project. Use Markdown formatting:

```markdown
# Welcome to [Your Company]

Your custom welcome message here...

## Features
- Feature 1
- Feature 2

## Getting Started
Instructions for users...
```

### Update Header Links

Edit `.chainlit/config.toml` and modify the `[[UI.header_links]]` sections:

```toml
[[UI.header_links]]
    name = "YourLink"
    display_name = "Link Display Name"
    icon_url = "https://api.iconify.design/mdi/your-icon.svg"
    url = "https://your-url.com"
    target = "_blank"
```

**Find Icons:** Browse [Iconify](https://icon-sets.iconify.design/) for free icons.

---

## Advanced Customization

### Dark Mode Colors

Customize dark mode appearance in `/public/brand.css`:

```css
@media (prefers-color-scheme: dark) {
  :root {
    --brand-background: #111827;
    --brand-surface: #1f2937;
    --brand-text-primary: #f9fafb;
  }
}
```

### Typography

Change fonts in `/public/brand.css`:

```css
body {
  font-family: 'Your Font Name', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
```

**To use custom fonts:**
1. Add font import at the top of `brand.css`:
   ```css
   @import url('https://fonts.googleapis.com/css2?family=Your+Font&display=swap');
   ```
2. Or host fonts locally in `/public/fonts/`

### Component Styling

Customize specific components in `/public/brand.css`:

```css
/* Message bubbles */
.message-user {
  background-color: var(--brand-primary) !important;
  border-radius: 12px; /* Adjust roundness */
}

/* Buttons */
.button-primary {
  background-color: var(--brand-primary) !important;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1); /* Add shadow */
}

/* Chat input */
.chat-input {
  border-radius: 20px; /* Rounded input */
}
```

### Custom JavaScript

For advanced interactions, create `/public/brand.js`:

```javascript
// Custom JavaScript for Chainlit UI
console.log('Structura AI - Custom branding loaded');

// Example: Add custom behavior
document.addEventListener('DOMContentLoaded', function() {
  // Your custom code here
});
```

Then enable it in `.chainlit/config.toml`:

```toml
custom_js = "/public/brand.js"
```

### Chat Profile Icons

Customize chat profile icons in `app.py`:

```python
@cl.set_chat_profiles
async def chat_profile():
    return [
        cl.ChatProfile(
            name="Support",
            markdown_description="Description",
            icon="https://your-icon-url.com/icon.png"  # Custom icon
        ),
    ]
```

---

## File Structure

```
enterprise-cx-agent/
├── .chainlit/
│   └── config.toml          # Main configuration
├── public/
│   ├── structura_ai_light.png  # Logo (light)
│   ├── structura_ai_dark.png   # Logo (dark)
│   ├── brand.css               # Custom styles
│   └── brand.js                # Custom scripts (optional)
├── docs/
│   └── BRANDING_GUIDE.md       # This file
├── chainlit.md                 # Welcome message
└── app.py                      # Application code
```

---

## Testing Your Changes

### 1. **Start the Application**

```bash
chainlit run app.py
```

### 2. **Check Browser Console**

Open browser DevTools (F12) to check for:
- CSS loading errors
- Missing image files
- JavaScript errors

### 3. **Test Responsive Design**

- Resize browser window
- Test on mobile devices
- Check tablet views

### 4. **Verify Dark Mode**

- Toggle system dark mode
- Check color contrast
- Verify logo visibility

### 5. **Test All Features**

- Click header links
- Try both chat profiles
- Send test messages
- Check file uploads

---

## Color Scheme Examples

### Professional Blue (Current)
```css
--brand-primary: #2563eb;
--brand-secondary: #7c3aed;
```

### Corporate Green
```css
--brand-primary: #059669;
--brand-secondary: #0891b2;
```

### Modern Purple
```css
--brand-primary: #7c3aed;
--brand-secondary: #ec4899;
```

### Tech Orange
```css
--brand-primary: #ea580c;
--brand-secondary: #0891b2;
```

---

## Best Practices

1. **Keep it Simple**
   - Don't overload with too many colors
   - Maintain good contrast ratios (WCAG AA standard)
   - Use consistent spacing

2. **Performance**
   - Optimize image sizes
   - Minimize CSS files if needed
   - Use web-optimized fonts

3. **Accessibility**
   - Ensure sufficient color contrast
   - Test with screen readers
   - Provide alt text for images

4. **Consistency**
   - Use the same colors throughout
   - Maintain consistent typography
   - Keep similar components styled the same

5. **Testing**
   - Test on multiple browsers
   - Check mobile responsiveness
   - Verify all interactive elements

---

## Troubleshooting

### Logo Not Showing
- Check file path in `config.toml`
- Verify file exists in `/public/`
- Check browser console for 404 errors
- Ensure filename matches exactly (case-sensitive)

### CSS Not Applied
- Check `custom_css` path in `config.toml`
- Verify CSS file is in `/public/`
- Clear browser cache (Ctrl+Shift+R)
- Check for CSS syntax errors in browser console

### Colors Not Changing
- Make sure you're editing `/public/brand.css`
- Check CSS variable names match
- Use `!important` if needed to override defaults
- Clear cache and reload

### Dark Mode Issues
- Verify dark mode media query in CSS
- Check system dark mode settings
- Test color contrast in both modes

---

## Resources

### Design Tools
- [Figma](https://figma.com) - UI design
- [Canva](https://canva.com) - Logo creation
- [Remove.bg](https://remove.bg) - Background removal

### Color Tools
- [Coolors](https://coolors.co) - Palette generator
- [Contrast Checker](https://webaim.org/resources/contrastchecker/) - Accessibility
- [Color Hunt](https://colorhunt.co) - Color inspiration

### Icon Resources
- [Iconify](https://icon-sets.iconify.design/) - Icon library
- [Font Awesome](https://fontawesome.com) - Icon fonts
- [Heroicons](https://heroicons.com) - SVG icons

### Font Resources
- [Google Fonts](https://fonts.google.com) - Free fonts
- [Font Squirrel](https://fontsquirrel.com) - Commercial fonts
- [Adobe Fonts](https://fonts.adobe.com) - Premium fonts

### Chainlit Documentation
- [Chainlit Docs](https://docs.chainlit.io) - Official documentation
- [Customization Guide](https://docs.chainlit.io/customisation/overview) - UI customization
- [Configuration](https://docs.chainlit.io/deployment/configuration) - Config options

---

## Quick Reference: Logo Configuration

### Current TrueCart Setup

**Files:**
```
public/
├── TrueCart_Light.png  (light mode logo)
└── TrueCart_dark.png   (dark mode logo - available but not configured)
```

**Configuration in `.chainlit/config.toml`:**
```toml
[UI]
name = "TrueCart"
description = "TrueCart - Enterprise Customer Experience Agent..."
logo_file_url = "/public/TrueCart_Light.png"
default_avatar_file_url = "/public/TrueCart_Light.png"
```

**Configuration in `app.py`:**
```python
cl.ChatProfile(
    name="TrueCart Support",
    icon="/public/TrueCart_Light.png"
),
cl.ChatProfile(
    name="TrueCart Admin",
    icon="/public/TrueCart_Light.png"
)
```

### Quick Change Checklist

To update your logo:

- [ ] Create logo file (PNG, 200-400px width)
- [ ] Save to `/public/` directory
- [ ] Update `logo_file_url` in `.chainlit/config.toml`
- [ ] Update `default_avatar_file_url` in `.chainlit/config.toml`
- [ ] Update `icon` paths in `app.py` chat profiles (2 places)
- [ ] Restart Chainlit server: `chainlit run app.py`
- [ ] Hard refresh browser: `Cmd+Shift+R` or `Ctrl+Shift+R`

### Logo Locations Map

| Location | Config File | Setting | Currently Shows |
|----------|-------------|---------|-----------------|
| Header (top-left) | `.chainlit/config.toml` | `logo_file_url` | TrueCart_Light.png |
| Message avatar | `.chainlit/config.toml` | `default_avatar_file_url` | TrueCart_Light.png |
| Profile icons | `app.py` | `icon` parameter | TrueCart_Light.png |
| Welcome avatar | `.chainlit/config.toml` | `default_avatar_file_url` | TrueCart_Light.png |

---

## Support

For additional help:
1. Check the [Chainlit Documentation](https://docs.chainlit.io)
2. Join the [Chainlit Discord Community](https://discord.gg/chainlit)
3. Review the [GitHub Issues](https://github.com/Chainlit/chainlit/issues)

---

**Last Updated:** January 14, 2026
**Version:** 1.0
**Chainlit Version:** 2.9.4
