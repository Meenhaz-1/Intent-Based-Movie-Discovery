# Movie Recommendations - Design System

**Product Type:** Tool (Entertainment/Discovery)  
**Target Audience:** Movie enthusiasts 18-45, seeking personalized recommendations  
**Style:** Modern, Playful, Content-First  
**Dark Mode:** Full support with semantic color tokens

---

## 1. Design Style

### Pattern: **Content-First Glassmorphism**
- Hero content (movie cards, search) takes center stage
- Glassmorphic layers (backdrop blur, translucent surfaces) create depth
- Micro-interactions add delight without distraction
- Dark mode is first-class, not an afterthought

### Why This Works
- **Content-First**: Movie discovery is the primary goal—everything else supports it
- **Glassmorphism**: Modern, premium feel that makes the app feel current and sophisticated
- **Playful**: Micro-interactions and subtle animations make the experience feel alive
- **Dark Mode Native**: Entertainment app users expect dark mode; builds brand trust

### Anti-Patterns (Avoid)
- ❌ Flat design with no depth or layering
- ❌ Heavy shadows or skeuomorphism (feels dated)
- ❌ Decorative animations that don't serve UX
- ❌ Dark mode bolted on as an afterthought (must have parity)

---

## 2. Color Palette

### Light Mode
| Token | Hex | Use |
|-------|-----|-----|
| **Primary** | `#667eea` | CTAs, highlights, interactive states |
| **Primary Dark** | `#764ba2` | Hover/pressed state of primary |
| **Accent** | `#f093fb` | Secondary actions, badges, highlights |
| **Surface** | `#ffffff` | Cards, containers, main background |
| **Surface Elevated** | `#f9f9f9` | Elevated cards, dropdowns |
| **Text Primary** | `#1a1a1a` | Body text, primary content |
| **Text Secondary** | `#666666` | Helper text, secondary labels |
| **Text Tertiary** | `#999999` | Disabled, muted content |
| **Border** | `#e0e0e0` | Dividers, card edges |
| **Error** | `#ef4444` | Error states, destructive actions |
| **Success** | `#10b981` | Success feedback |
| **Warning** | `#f59e0b` | Warning states |

### Dark Mode (Desaturated Tonal Variants)
| Token | Hex | Use |
|-------|-----|-----|
| **Primary** | `#7c8ff0` | CTAs (slightly lighter than light mode) |
| **Primary Dark** | `#8b9fef` | Hover state |
| **Accent** | `#f5a4ff` | Secondary actions (desaturated) |
| **Surface** | `#0f0f0f` | Main background (near black) |
| **Surface Elevated** | `#1a1a1a` | Cards, elevated containers |
| **Text Primary** | `#f5f5f5` | Body text |
| **Text Secondary** | `#b0b0b0` | Helper text |
| **Text Tertiary** | `#808080` | Disabled, muted |
| **Border** | `#333333` | Dividers |
| **Error** | `#ff6b6b` | Error states (brighter on dark) |
| **Success** | `#2dd4bf` | Success feedback (brighter) |
| **Warning** | `#fbbf24` | Warning states (brighter) |

### Guidelines
- **Contrast**: Light mode body text meets 4.5:1, dark mode primary text ≥4.5:1, secondary ≥3:1
- **Semantic tokens**: Use named tokens (primary, error) not hex values in components
- **Dark mode**: Desaturate and lighten colors; test both modes independently
- **No gray-on-gray**: Text is always readable; use semantic color for meaning

---

## 3. Typography

### Font Pairing
- **Heading Font**: `Inter` (geometric, modern, friendly)
- **Body Font**: `Inter` (consistent, readable, cohesive)

### Type Scale
| Role | Size | Weight | Line Height | Usage |
|------|------|--------|-------------|-------|
| Display | 32px | 700 | 1.2 | Page title |
| Headline | 24px | 600 | 1.3 | Section headers |
| Title | 18px | 600 | 1.4 | Card titles, form labels |
| Body | 16px | 400 | 1.6 | Main content, descriptions |
| Label | 14px | 500 | 1.5 | Button text, badges |
| Caption | 12px | 400 | 1.5 | Helper text, timestamps |
| Tiny | 11px | 400 | 1.4 | Disabled, secondary labels (sparingly) |

### Guidelines
- **Min body text**: 16px on mobile (no auto-zoom on iOS)
- **Line length**: 35–60 chars on mobile, 60–75 chars on desktop
- **Weight hierarchy**: Bold (600–700) for headings, Regular (400) for body, Medium (500) for labels
- **No truncation**: Text wraps; use ellipsis only when necessary + provide tooltip/expand

---

## 4. Visual Effects

### Shadows (Elevation Scale)
| Level | Box Shadow | Use |
|-------|-----------|-----|
| Flat | None | Backgrounds |
| Raised (1) | `0 1px 3px rgba(0,0,0,0.1)` | Subtle cards |
| Floating (2) | `0 4px 6px rgba(0,0,0,0.1), 0 1px 3px rgba(0,0,0,0.08)` | Default cards |
| Modal (3) | `0 10px 25px rgba(0,0,0,0.15)` | Modals, dropdowns |
| Top (4) | `0 20px 40px rgba(0,0,0,0.2)` | Floating action buttons |

### Border Radius
- **Small components**: 4px (inputs, small buttons)
- **Medium components**: 8px (cards, buttons)
- **Large components**: 12px (modal corners, major containers)
- **Full**: 999px (pill-shaped, chip buttons)

### Backdrop Blur (Glassmorphism)
- **Subtle**: `blur(4px)` + opacity 90% for semi-transparent overlays
- **Strong**: `blur(8px)` + opacity 95% for modal scrim or glass layer
- **Never**: Pure blur without color; always pair with a tint

### Spacing Scale (8dp Grid)
| Scale | Value | Use |
|-------|-------|-----|
| xs | 4px | Tight gaps, icon spacing |
| sm | 8px | Component padding, list gaps |
| md | 16px | Section padding, moderate gaps |
| lg | 24px | Major section spacing |
| xl | 32px | Page-level spacing |
| 2xl | 48px | Hero spacing |

---

## 5. Animation & Motion

### Timing Rules
- **Micro-interactions** (button press, toggle): 150ms ease-out
- **Transitions** (fade, slide): 200ms ease-in-out
- **Page/modal entrance**: 300ms cubic-bezier(0.4, 0, 0.2, 1)
- **Page exit**: 250ms cubic-bezier(0.4, 0, 0.6, 1) (faster than enter)

### Easing
- **Enter animations**: `ease-out` (fast start, slow end = feels responsive)
- **Exit animations**: `ease-in` (slow start, fast end = feels confident)
- **State changes**: `cubic-bezier(0.4, 0, 0.2, 1)` (Material standard)

### Semantic Motion
- **Hover**: Subtle scale (1.02) + shadow elevation (no layout shift)
- **Press**: Scale (0.98) + opacity (0.8)
- **Disabled**: No animation; static opacity (0.5)
- **Loading**: Smooth spinner (1s+ rotate) respecting `prefers-reduced-motion`

### Anti-Patterns
- ❌ Decorative animation without purpose
- ❌ Animating width/height (use transform instead)
- ❌ Motion that ignores `prefers-reduced-motion`
- ❌ Blocking UI interaction during animation

---

## 6. Component Guidelines

### Buttons
- **Primary**: Solid primary color, white text, elevation 1
- **Secondary**: Outlined, border + transparent fill, text color = primary
- **Tertiary**: Text only, no background
- **Danger**: Solid error color
- **Disabled**: Opacity 0.5, no pointer-events
- **Touch target**: ≥44×44px

### Cards
- **Border**: None (elevation handles separation)
- **Padding**: 16px for content, 24px for hero cards
- **Radius**: 8px
- **Shadow**: Elevation 2 (default), Elevation 3 on hover
- **Hover state**: Lift (translate -2px) + shadow increase (no layout shift)

### Forms
- **Label**: Visible label + semantic <label> element (not placeholder-only)
- **Input**: 44px height on mobile, border 1px, focus ring 3px primary color
- **Error**: Text below field, error red, icon + message (color not only signal)
- **Helper text**: Smaller font, secondary color, below input
- **Submit feedback**: Loading spinner on button, then success/error toast

### Navigation
- **Bottom nav**: ≤5 items, icon + text label, icon 24px
- **Active state**: Color = primary, weight ≠ bold (bad for mobile)
- **Spacing**: 8px between items, min 44px tap area

### Modals
- **Scrim**: 50% black opacity, blur(4px) optional
- **Entrance**: Scale (0.9) + fade-in from 0.8 opacity
- **Exit**: Reverse motion, faster
- **Dismiss**: Always provide close button + swipe-down on mobile

---

## 7. Dark Mode Implementation

### Token-Driven Theming
```css
:root {
  /* Light mode (default) */
  --color-primary: #667eea;
  --color-surface: #ffffff;
  --color-text-primary: #1a1a1a;
  /* ... etc ... */
}

@media (prefers-color-scheme: dark) {
  :root {
    /* Dark mode overrides */
    --color-primary: #7c8ff0;
    --color-surface: #0f0f0f;
    --color-text-primary: #f5f5f5;
    /* ... etc ... */
  }
}
```

### Dark Mode Specific Rules
- **Desaturate colors**: Lower saturation on dark backgrounds for eye comfort
- **Lighten secondary colors**: Gray-700 in light mode → Gray-400 in dark mode
- **Test independently**: Don't assume light mode contrast works; verify both
- **No inversion**: Don't just invert light → dark; use tonal variants
- **Border visibility**: Ensure dividers visible in both themes

---

## 8. Accessibility (CRITICAL)

### Color Contrast
- **Body text**: ≥4.5:1 against background (AA standard)
- **Large text** (18px+): ≥3:1
- **Icons**: ≥4.5:1 for small glyphs, ≥3:1 for larger UI icons
- **Verify**: Use WebAIM contrast checker for both light & dark modes

### Focus & Keyboard
- **Focus ring**: 3px solid primary color, 2px offset
- **Focus order**: Matches visual left-to-right, top-to-bottom
- **Keyboard nav**: All interactive elements reachable via Tab

### Labels & ARIA
- **Form inputs**: `<label for="input-id">` (not placeholder-only)
- **Icon buttons**: `aria-label="descriptive text"`
- **Semantic HTML**: `<button>`, `<a>`, not `<div onclick>`

### Motion
- **Respect `prefers-reduced-motion`**: Disable non-essential animations
- **Never auto-play**: Video, sound, animation off by default
- **Loading states**: Animated spinner OK, but allow static alternative

---

## 9. Anti-Patterns (What NOT to Do)

### Style & Visual
- ❌ Mixing flat and glassmorphism randomly
- ❌ Using emojis as structural icons (use SVG)
- ❌ Shadows without consistent elevation scale
- ❌ Hardcoded color hex in components (use tokens)

### Interaction
- ❌ No visual feedback on click/hover
- ❌ Tap targets <44px
- ❌ Instant state changes (0ms animation)
- ❌ Blocking interaction during loading

### Layout
- ❌ Horizontal scroll on mobile
- ❌ Text edge-to-edge on large screens (unreadable)
- ❌ Fixed width containers that don't adapt
- ❌ No safe area respect for notches/gesture areas

### Dark Mode
- ❌ Same colors in light & dark (fails contrast)
- ❌ Bold or heavy dark mode (hurts readability)
- ❌ Gray-on-gray text
- ❌ Forcing dark mode (no light option)

---

## 10. Pre-Delivery Checklist

- [ ] All icons are SVG, not emoji
- [ ] Tap targets ≥44×44px
- [ ] Text contrast ≥4.5:1 (light & dark modes)
- [ ] Animations respect `prefers-reduced-motion`
- [ ] Forms have visible labels + error messages below fields
- [ ] Modals have close button + scrim
- [ ] Navigation is predictable (same location across screens)
- [ ] Buttons have hover + pressed states (no layout shift)
- [ ] Mobile tested on 375px + landscape
- [ ] Dark mode tested independently (not inferred)

---

## Design Tokens (Copy to CSS)

```css
/* Colors - Light Mode */
--color-primary: #667eea;
--color-primary-hover: #764ba2;
--color-accent: #f093fb;
--color-surface: #ffffff;
--color-surface-elevated: #f9f9f9;
--color-text-primary: #1a1a1a;
--color-text-secondary: #666666;
--color-text-tertiary: #999999;
--color-border: #e0e0e0;
--color-error: #ef4444;
--color-success: #10b981;
--color-warning: #f59e0b;

/* Typography */
--font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
--font-size-display: 32px;
--font-size-headline: 24px;
--font-size-title: 18px;
--font-size-body: 16px;
--font-size-label: 14px;
--font-size-caption: 12px;

/* Spacing */
--spacing-xs: 4px;
--spacing-sm: 8px;
--spacing-md: 16px;
--spacing-lg: 24px;
--spacing-xl: 32px;
--spacing-2xl: 48px;

/* Shadows */
--shadow-sm: 0 1px 3px rgba(0,0,0,0.1);
--shadow-md: 0 4px 6px rgba(0,0,0,0.1), 0 1px 3px rgba(0,0,0,0.08);
--shadow-lg: 0 10px 25px rgba(0,0,0,0.15);
--shadow-xl: 0 20px 40px rgba(0,0,0,0.2);

/* Border Radius */
--radius-sm: 4px;
--radius-md: 8px;
--radius-lg: 12px;
--radius-full: 999px;

/* Animation */
--duration-fast: 150ms;
--duration-normal: 200ms;
--duration-slow: 300ms;
--easing-out: cubic-bezier(0.4, 0, 0.2, 1);
--easing-in: cubic-bezier(0.2, 0, 0.6, 1);
--easing-in-out: cubic-bezier(0.4, 0, 0.2, 1);
```

---

**Design System Version:** 1.0  
**Last Updated:** 2026-06-22  
**Maintained By:** UI/UX Pro Max
