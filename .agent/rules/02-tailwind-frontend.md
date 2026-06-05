---
name: tailwind-frontend
description: Overarching constraints for the Tailwind/Jinja Frontend application.
---
# Frontend Engineering Directives (Tailwind)

When operating on frontend logic (`static/`, `templates/`), you must strictly adhere to the following ecosystem constraints:

## 1. Theming & Styling
- **Utility First:** Use Tailwind CSS (`static/input.pcss`) exclusively. Do not write custom CSS grids or flex layouts manually in CSS unless strictly required.
- **Compilation:** Always run `npm run build:css` after modifying styles.

## 2. Structure
- Use semantic HTML elements within the `templates/` Jinja files.
- Favor standard forms and input validation natively in HTML5.

## 3. Aesthetic & Interactions
- Maintain a vibrant design with dynamic hover states.
- Incorporate subtle transitions using Tailwind's `transition` utilities.
