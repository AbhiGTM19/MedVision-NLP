---
name: tailwind-frontend
description: Overarching constraints for the Tailwind/Jinja Frontend application.
---
# Frontend Engineering Directives (Tailwind)

When operating on frontend logic (`frontend/static/`, `frontend/templates/`), you must strictly adhere to the following ecosystem constraints:

## 1. Theming & Styling
- **Utility First:** Use Tailwind CSS (`frontend/static/input.pcss`) exclusively. Do not write custom CSS grids or flex layouts manually in CSS unless strictly required.
- **Compilation:** Always run `npm run build:css` after modifying styles.

## 2. Structure
- Use semantic HTML elements within the `frontend/templates/` Jinja files.
- Favor standard forms and input validation natively in HTML5.

## 3. Aesthetic & Interactions
- Maintain a vibrant design with dynamic hover states.
- Incorporate subtle transitions using Tailwind's `transition` utilities.
