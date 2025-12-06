# UX Features Guide - Visual Reference

## 1. Breadcrumb Navigation

### Location
Appears at the top of content area on all pages except homepage

### Visual Design
```
+------------------------------------------------------------------+
|  Home > Research > WP1: Data Space                               |
+------------------------------------------------------------------+
```

### Styling
- Background: Light gray (#F8F9FA)
- Border: 1px bottom border
- Links: EU Blue (#003399)
- Hover: Underline + darker blue
- Current page: Gray text, bold

### Responsive Behavior
- Desktop: Full size (12px padding, 0.8rem font)
- Mobile: Smaller (10px padding, 0.75rem font, 50px top margin)

### Code Location
- Template: `layouts/partials/breadcrumbs.html`
- CSS: Lines 1257-1285 in `static/css/style.css`

---

## 2. Back to Top Button

### Location
Fixed position: 30px from bottom-right corner

### Visual Design
```
      +-----+
      |  ^  |  <- Gold circle with blue arrow
      |     |     Appears when scrolled > 300px
      +-----+
```

### Styling
- Shape: Circle (50px diameter)
- Background: EU Gold (#FFD700)
- Icon: Blue arrow pointing up
- Shadow: Subtle drop shadow
- Animation: Fade in/out + slide up

### Interaction States
1. **Hidden**: Opacity 0, translateY(20px)
2. **Visible**: Opacity 1, translateY(0)
3. **Hover**: Blue background, gold icon, lift effect (-3px)

### Responsive Behavior
- Desktop: 50px x 50px, 30px from edges
- Mobile: 45px x 45px, 20px from edges

### Code Location
- HTML: Lines 109-114 in `layouts/_default/baseof.html`
- JavaScript: Lines 50-69 in `static/js/main.js`
- CSS: Lines 1287-1326 in `static/css/style.css`

---

## 3. Mobile Menu Improvements

### Desktop View (> 768px)
```
+----------+--------------------+
|          |                    |
| Sidebar  |  Main Content      |
| (fixed)  |                    |
|          |                    |
+----------+--------------------+
```

### Mobile View (< 768px) - Closed
```
[Menu]  <- Button only
|                    |
|  Main Content      |
|  (full width)      |
|                    |
+--------------------+
```

### Mobile View - Open
```
[Menu] <- Active button
+----------+
| Sidebar  | [Dark overlay]
| (slides  | Main Content
|  in)     | (dimmed)
+----------+
```

### Animation Details

**Sidebar Slide-In**:
- Transform: translateX(-100%) -> translateX(0)
- Duration: 0.3s ease
- Shadow: Appears on right edge

**Overlay Backdrop**:
- Background: rgba(0, 0, 0, 0.5)
- Animation: fadeIn 0.3s
- Z-index: 999

**Menu Button**:
- Position: Fixed top-left (15px from edges)
- Background: EU Blue
- Hover: Lighter blue
- Z-index: 1001

### Behavior
1. Click menu button -> sidebar slides in, overlay appears
2. Click overlay -> sidebar slides out, overlay fades
3. Click nav link -> sidebar auto-closes
4. Click outside -> sidebar auto-closes

### Code Location
- JavaScript: Lines 71-100 in `static/js/main.js`
- CSS: Lines 1328-1409 in `static/css/style.css`

---

## Color Reference

### Primary Colors
- **EU Blue**: #003399
- **EU Dark Blue**: #001a4d
- **EU Gold**: #FFD700
- **Secondary Blue**: #0055CC

### Neutral Colors
- **Text**: #333333
- **Text Light**: #666666
- **Background**: #FFFFFF
- **Background Light**: #F8F9FA
- **Border**: #E0E4E8

---

## Accessibility Features

### Breadcrumbs
- `<nav>` element with `aria-label="Breadcrumb"`
- Clear visual hierarchy
- Links properly labeled

### Back to Top Button
- `aria-label="Back to top"`
- `title="Back to top"` tooltip
- Keyboard accessible (focusable)
- Large touch target (50px)

### Mobile Menu
- `aria-expanded` state on toggle button
- Focus management
- Keyboard navigation support
- ESC key support (standard browser behavior)

---

## Browser Support

### Modern Browsers (Full Support)
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

### Features Used
- CSS Grid/Flexbox
- CSS Transforms
- CSS Animations
- ES6 JavaScript
- `window.scrollTo` with smooth behavior

### Graceful Degradation
- Browsers without smooth scroll: Instant scroll fallback
- Older browsers: Basic functionality maintained

---

## Performance Notes

### Optimizations
- GPU-accelerated CSS (transform, opacity)
- Minimal reflows/repaints
- Event delegation where possible
- No external dependencies

### Load Impact
- CSS: +167 lines (minified ~3KB)
- JS: +60 lines (minified ~1KB)
- HTML: +15 lines (minimal)
- **Total added**: ~4KB uncompressed

---

## Testing Checklist

### Breadcrumbs
- [ ] Appears on all non-home pages
- [ ] Shows correct path hierarchy
- [ ] Links navigate correctly
- [ ] Current page is not linked
- [ ] Responsive on mobile

### Back to Top
- [ ] Hidden when page loads
- [ ] Appears after scrolling 300px down
- [ ] Smooth scroll to top on click
- [ ] Hover effect works
- [ ] Responsive size on mobile

### Mobile Menu
- [ ] Toggle button appears < 768px
- [ ] Sidebar slides in smoothly
- [ ] Overlay appears behind sidebar
- [ ] Closes on outside click
- [ ] Closes on link click
- [ ] Closes on toggle button click

### Content Updates
- [ ] Event dates are not "December 1, 2025"
- [ ] Blog posts show excerpts
- [ ] Event listings sort by date correctly

---

## Customization Guide

### Changing Colors

**Breadcrumbs**:
```css
.breadcrumb-link {
    color: var(--eu-blue);  /* Change link color */
}
```

**Back to Top**:
```css
.back-to-top {
    background: var(--eu-gold);  /* Change button color */
    color: var(--eu-blue-dark);   /* Change icon color */
}
```

### Adjusting Scroll Threshold

**Back to Top Button** (in `main.js`):
```javascript
if (window.pageYOffset > 300) {  // Change 300 to desired value
    backToTopButton.classList.add('visible');
}
```

### Changing Animation Speed

**Mobile Menu** (in `style.css`):
```css
.sidebar {
    transition: transform 0.3s ease;  /* Change 0.3s to desired duration */
}
```

---

## Troubleshooting

### Breadcrumbs Not Showing
1. Check page is not homepage (`{{ if not .IsHome }}`)
2. Verify partial exists: `layouts/partials/breadcrumbs.html`
3. Check CSS is loaded

### Back to Top Button Not Appearing
1. Check scroll position is > 300px
2. Verify JavaScript has no errors (console)
3. Check CSS `.back-to-top.visible` class is applied

### Mobile Menu Not Working
1. Verify viewport width < 768px
2. Check JavaScript console for errors
3. Ensure CSS transform is supported

### Event Dates Still Wrong
1. Re-run `python scripts/61_fix_event_dates.py`
2. Clear Hugo cache: `hugo --gc`
3. Check front matter format

---

## File Reference Quick Links

```
Breadcrumbs:
  Template: layouts/partials/breadcrumbs.html
  CSS:      static/css/style.css (lines 1257-1285)
  Include:  layouts/_default/baseof.html (line 86)

Back to Top:
  HTML:     layouts/_default/baseof.html (lines 109-114)
  JS:       static/js/main.js (lines 50-69)
  CSS:      static/css/style.css (lines 1287-1326)

Mobile Menu:
  JS:       static/js/main.js (lines 71-100)
  CSS:      static/css/style.css (lines 1328-1409)
```

---

## Future Enhancement Ideas

### Potential Additions
1. **Search Functionality**: Add Fuse.js for client-side search
2. **Progress Bar**: Show reading progress on blog posts
3. **Theme Switcher**: Light/dark mode toggle
4. **Breadcrumb Schema**: Add structured data for SEO
5. **Keyboard Shortcuts**: Add hotkeys (e.g., '/' for search)

### Search Implementation (Stretch Goal)
- Would require: Fuse.js library (~50KB)
- Search index generation from content
- Search UI in sidebar
- Results dropdown with highlighting

---

End of UX Features Guide
