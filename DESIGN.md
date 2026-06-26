---
name: MedVision NLP
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#44474c'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#75777d'
  outline-variant: '#c5c6cd'
  surface-tint: '#515f74'
  primary: '#051324'
  on-primary: '#ffffff'
  primary-container: '#1a283a'
  on-primary-container: '#818fa5'
  inverse-primary: '#b9c7df'
  secondary: '#505f76'
  on-secondary: '#ffffff'
  secondary-container: '#d4e3ff'
  on-secondary-container: '#56657c'
  tertiary: '#001421'
  on-tertiary: '#ffffff'
  tertiary-container: '#002a3f'
  on-tertiary-container: '#6493b5'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d5e3fc'
  primary-fixed-dim: '#b9c7df'
  on-primary-fixed: '#0e1c2e'
  on-primary-fixed-variant: '#3a485b'
  secondary-fixed: '#d4e3ff'
  secondary-fixed-dim: '#b8c7e2'
  on-secondary-fixed: '#0c1c30'
  on-secondary-fixed-variant: '#39485e'
  tertiary-fixed: '#c8e6ff'
  tertiary-fixed-dim: '#9cccf0'
  on-tertiary-fixed: '#001e2f'
  on-tertiary-fixed-variant: '#134b6a'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
  surface-glass: rgba(255, 255, 255, 0.8)
  outline-muted: '#e2e8f0'
  success-dim: '#89ceff'
  error-alert: '#ba1a1a'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.2'
  title-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: '1.4'
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '700'
    lineHeight: '1'
    letterSpacing: 0.05em
  status-tiny:
    fontFamily: Inter
    fontSize: 10px
    fontWeight: '700'
    lineHeight: '1'
    letterSpacing: 0.1em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  xs: 4px
  base: 8px
  sm: 12px
  md: 24px
  lg: 48px
  margin: 32px
  xl: 80px
  gutter: 24px
---

## Brand & Style

The brand identity for MedVision NLP is defined by **Clinical Precision and Future-Forward Intelligence**. It is designed for medical professionals who require high-reliability tools that feel sophisticated yet approachable. 

The visual style is a **Modern-Corporate** hybrid with a heavy **Glassmorphic** influence. It balances the sterile, trustworthy nature of clinical software with the dynamic, airy feel of modern SaaS. The UI utilizes semi-transparent layers, backdrop blurs, and subtle animations (floating, pulsing rings) to communicate that the system is "active" and "intelligent." The goal is to evoke a sense of calm efficiency, reducing the cognitive load associated with complex medical data entry and analysis.

## Colors

The palette is anchored in **Deep Slate (#1a283a)**, providing a serious, authoritative foundation for primary actions and typography. A secondary **Steel Blue (#505f76)** is used for supporting labels and iconography, maintaining a monochromatic professional feel.

The background system utilizes a very light **Cool Grey (#f7f9fb)** rather than pure white to reduce eye strain during long clinical sessions. Accent colors are used sparingly: a **Soft Cyan/Tertiary** is reserved for status indicators and "success" states, while the primary color is used for high-emphasis buttons and active input states. Transparency plays a critical role, with background blurs (80% opacity) used on navigation and cards to create depth.

## Typography

The system uses **Inter** exclusively to ensure maximum legibility and a systematic, utilitarian aesthetic. 

- **Headlines:** Use tighter letter-spacing and semi-bold weights to appear confident.
- **Data Entry Labels:** Utilize a "Label-Caps" style—uppercase, bold, and slightly tracked out—to distinguish them clearly from the user-inputted data.
- **Body Text:** Optimized for readability with a generous 1.6 line-height.
- **Status/Meta:** Tiny 10px caps are used for non-essential system information to keep the interface clean.

## Layout & Spacing

The interface uses a **Dual-Pane Split Layout** for its primary workflow.
- **Left Pane (50%):** Scrollable input/form area.
- **Right Pane (50%):** Fixed visualization/results area.

A **32px (Margin)** safety zone is maintained around the screen edges. Internal spacing follows an 8px base grid. Content within cards uses **24px (MD)** padding, while vertical spacing between cards is also **24px**. The navigation bar is fixed at **64px (h-16)** to maximize the remaining vertical workspace for data analysis.

## Elevation & Depth

Hierarchy is established through **Glassmorphism and Ambient Shadows**:
- **Level 0 (Background):** Solid `surface-bright` (#f7f9fb).
- **Level 1 (Cards):** Semi-transparent white (80% opacity) with a `16px` backdrop blur. Edges are defined by a very soft `white/40` border to simulate light hitting the edge of glass.
- **Shadows:** Use extremely diffused shadows (`0 4px 20px rgba(71, 85, 105, 0.05)`) to create a sense of lifting off the page without feeling heavy.
- **Interaction:** Cards scale slightly (1.01x) and gain a deeper shadow on hover to provide tactile feedback.

## Shapes

The shape language is **Rounded and Organic**. 
- **Standard Cards & Input Fields:** Use a `0.75rem` (rounded-xl) or `0.5rem` (rounded-lg) radius to soften the clinical environment.
- **Buttons:** Primary action buttons use a `0.75rem` radius for a modern, friendly feel.
- **Profile & Icons:** Use full circles (`rounded-full`) for avatars and status indicators to contrast against the rectangular grid of the form.
- **Inputs:** Form elements use a slightly softer `0.5rem` radius.

## Components

### Buttons
- **Primary:** High-contrast `primary` background, `on-primary` text, `rounded-xl`. Includes a subtle `pulse-ring` animation for the main CTA (e.g., "Run Analysis").
- **Secondary/Action:** `primary-container` background with `on-primary-container` text.
- **Icon Buttons:** Circular, `40x40px`, with a subtle hover state change.

### Input Fields
- **Default:** `surface-container-low` background, no border, `rounded-lg`.
- **Focus State:** White background, `1px solid primary` ring, and label color shifts to `primary`.
- **Selects:** Identical styling to text inputs but with a custom chevron.

### Cards (Glass)
- White 80% opacity, `backdrop-blur-16`, `border-white/40`, and `shadow-sm`. Used to group related data sets (e.g., Demographics, Biomarkers).

### File Upload
- A dashed-border container with a `floating icon` animation. Uses `surface-container-low/50` which turns white on drag-over.

### Analysis Indicators
- Utilizes "Subtle Float" animations and "Pulse Rings" to show system readiness or active processing.