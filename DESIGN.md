---
name: MedVision Clinical
colors:
  surface: '#ffffff'
  surface-dim: '#e5e7eb'
  surface-bright: '#ffffff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f9fafb'
  surface-container: '#f3f4f6'
  surface-container-high: '#e5e7eb'
  surface-container-highest: '#e5e7eb'
  on-surface: '#111827'
  on-surface-variant: '#4b5563'
  inverse-surface: '#1f2937'
  inverse-on-surface: '#f9fafb'
  outline: '#9ca3af'
  outline-variant: '#e5e7eb'
  surface-tint: '#f59e0b'
  primary: '#f59e0b'
  on-primary: '#ffffff'
  primary-container: '#fef3c7'
  on-primary-container: '#92400e'
  inverse-primary: '#f59e0b'
  secondary: '#f59e0b'
  on-secondary: '#ffffff'
  secondary-container: '#fef3c7'
  on-secondary-container: '#92400e'
  tertiary: '#f59e0b'
  on-tertiary: '#ffffff'
  tertiary-container: '#fef3c7'
  on-tertiary-container: '#92400e'
  error: '#ef4444'
  on-error: '#ffffff'
  error-container: '#fee2e2'
  on-error-container: '#991b1b'
  background: '#ffffff'
  on-background: '#111827'
  surface-variant: '#f3f4f6'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '900'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  title-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-caps:
    fontFamily: Public Sans
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.1em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 12px
  md: 24px
  lg: 48px
  xl: 80px
  container-max: 1280px
  gutter: 24px
---

## Brand & Style

This design system is built for the **MedVision NLP** Medical Specialty Classification tool. The brand personality is clinical, cutting-edge, and highly trustworthy, evoking the sterile yet advanced atmosphere of a modern hospital AI lab. The target audience includes medical professionals, data scientists, and healthcare administrators who require high-density clinical information presented with absolute clarity and precision.

The visual style merges **Glassmorphism** with an "Ambient Medical" aesthetic. It relies on crisp, expansive white/dark backgrounds overlaid with subtle glowing orbs and highly legible typography. The emotional response should be one of sophisticated clarity—where critical medical data and AI explanations (like Captum feature attributions) are presented on a clean, luminous canvas for maximum legibility.

## Colors

The palette is anchored by a vibrant "Clinical Amber" (`#f59e0b`) representing urgency and clear attention to critical medical insights. The default experience utilizes a pure white background in Light Mode, combined with deep grays for high contrast and readability.

- **Monochromatic Accents**: Secondary and tertiary elements use similar amber tones, while the dark mode utilizes deep blacks (`#0a0a0a`) with glowing glass borders.
- **Explainable AI Representation**: The UI uses dynamic highlight spans (`rgba(245, 158, 11, opacity)`) to represent the intensity of word attributions from the NLP model.
- **Translucency**: Use glassmorphism (`backdrop-filter: blur(12px)`) with semi-transparent surfaces to create depth over the ambient glowing orbs without sacrificing readability.

## Typography

This design system pairs **Inter** for dense data and general UI elements with **Public Sans** for highly structured labels and navigation to achieve a systematic, clinical aesthetic.

- **Hierarchy**: Use `display-lg` (`font-black`) for main hero titles and bold statements.
- **Labels**: Use `label-caps` with `Public Sans` for navigation, sub-headers, and tags to differentiate from clinical review text.
- **Rhythm**: Maintain a strict vertical rhythm. Typography relies on the high contrast between the text and backgrounds to ensure absolute clarity for medical professionals.

## Layout & Spacing

The layout follows a **Fluid Grid** model.
- **Spacing Principle**: Generous padding on outer containers (e.g., `py-24`) to provide breathing room, and tight coupling of related medical data points within cards.
- **Bento Grids**: Use 3-column bento box grids for feature highlights, collapsing to 1 column on mobile.

## Elevation & Depth

Depth is created through **Glassmorphism** and subtle tonal layering.
- **Surface Level 0 (Base)**: The ambient background with large, blurry glowing orbs (`blur-[100px]`).
- **Surface Level 1 (Cards)**: Glass cards with subtle borders (`border-outline-variant/50`) and soft inner shadows (`shadow-inner`).
- **Shadows**: Use heavy, diffused shadows (`shadow-xl`, `shadow-primary/20`) on primary call-to-actions to make them pop off the screen.

## Shapes

The design system employs a heavily **Rounded** shape language to soften the technical density of medical AI.
- **Primary Radius**: 0.75rem (`rounded-xl`) or 1rem (`rounded-2xl`) for almost all standard cards, text areas, and buttons.
- **Large Radius**: 1.5rem (`rounded-3xl`) for main dashboard containers.
- **Pill**: Used exclusively for status indicators, history badges, and the floating chat assistant button.

## Components

- **Buttons**: Primary buttons are solid Amber (`bg-primary`) with bold text and a subtle scale-down on active state (`active:scale-[0.98]`). Hover states increase brightness.
- **Floating Chat Assistant**: A circular FAB (`w-14 h-14`) in the bottom right corner with a drop shadow, triggering a sliding side panel for the RAG chatbot.
- **Text Areas**: Deep, slightly inset text areas (`bg-surface-container-low`) with a focus ring (`focus:ring-2 focus:ring-primary`) to encourage input of long-form clinical notes.
- **Explainable AI Text**: Sentences are dynamically broken down with inline background color spans. Darker/more opaque backgrounds represent higher AI confidence/importance.
- **Mermaid Diagrams**: Embedded SVG diagrams forced to high contrast (black on light, white on dark) with transparent backgrounds.
