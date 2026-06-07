/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: [
    "./templates/**/*.html",
    "./static/**/*.js"
  ],
  theme: {
    extend: {
      colors: {
        "surface-dim": "var(--tw-color-surface-dim)",
        "surface-container-highest": "var(--tw-color-surface-container-highest)",
        "surface-container-lowest": "var(--tw-color-surface-container-lowest)",
        "inverse-primary": "var(--tw-color-inverse-primary)",
        "secondary-fixed": "var(--tw-color-secondary-fixed)",
        "tertiary-container": "var(--tw-color-tertiary-container)",
        "on-surface": "var(--tw-color-on-surface)",
        "surface-container": "var(--tw-color-surface-container)",
        "secondary": "var(--tw-color-secondary)",
        "inverse-surface": "var(--tw-color-inverse-surface)",
        "on-secondary-fixed-variant": "var(--tw-color-on-secondary-fixed-variant)",
        "surface": "var(--tw-color-surface)",
        "primary-fixed": "var(--tw-color-primary-fixed)",
        "on-tertiary": "var(--tw-color-on-tertiary)",
        "on-primary-container": "var(--tw-color-on-primary-container)",
        "on-tertiary-fixed": "var(--tw-color-on-tertiary-fixed)",
        "surface-container-low": "var(--tw-color-surface-container-low)",
        "on-secondary": "var(--tw-color-on-secondary)",
        "on-surface-variant": "var(--tw-color-on-surface-variant)",
        "primary-container": "var(--tw-color-primary-container)",
        "outline-variant": "var(--tw-color-outline-variant)",
        "on-error-container": "var(--tw-color-on-error-container)",
        "on-primary-fixed-variant": "var(--tw-color-on-primary-fixed-variant)",
        "tertiary": "var(--tw-color-tertiary)",
        "on-secondary-fixed": "var(--tw-color-on-secondary-fixed)",
        "surface-bright": "var(--tw-color-surface-bright)",
        "outline": "var(--tw-color-outline)",
        "on-secondary-container": "var(--tw-color-on-secondary-container)",
        "error-container": "var(--tw-color-error-container)",
        "error": "var(--tw-color-error)",
        "on-tertiary-container": "var(--tw-color-on-tertiary-container)",
        "background": "var(--tw-color-background)",
        "tertiary-fixed-dim": "var(--tw-color-tertiary-fixed-dim)",
        "on-primary": "var(--tw-color-on-primary)",
        "primary-fixed-dim": "var(--tw-color-primary-fixed-dim)",
        "secondary-fixed-dim": "var(--tw-color-secondary-fixed-dim)",
        "on-primary-fixed": "var(--tw-color-on-primary-fixed)",
        "surface-container-high": "var(--tw-color-surface-container-high)",
        "inverse-on-surface": "var(--tw-color-inverse-on-surface)",
        "on-error": "var(--tw-color-on-error)",
        "surface-tint": "var(--tw-color-surface-tint)",
        "tertiary-fixed": "var(--tw-color-tertiary-fixed)",
        "surface-variant": "var(--tw-color-surface-variant)",
        "on-background": "var(--tw-color-on-background)",
        "primary": "var(--tw-color-primary)",
        "secondary-container": "var(--tw-color-secondary-container)",
        "on-tertiary-fixed-variant": "var(--tw-color-on-tertiary-fixed-variant)"
      },
      fontFamily: {
        "headline": ["Inter", "sans-serif"],
        "display": ["Inter", "sans-serif"],
        "body": ["Inter", "sans-serif"],
        "label": ["Public Sans", "sans-serif"]
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/container-queries')
  ],
}
