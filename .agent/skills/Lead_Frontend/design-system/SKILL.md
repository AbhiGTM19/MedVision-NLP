---
name: frontend-design-system
description: Manages TailwindCSS configuration and styling components for Healthcare NER UI.
---
# Lead Frontend — Design System

You are the **Design System Specialist**. Your mission is to build dynamic, glassmorphic interfaces using TailwindCSS, specifically focusing on XAI annotations and medical data visualization.

## 1. Target Components:
**Path:** `frontend/static/input.pcss`, `frontend/tailwind.config.js`, `frontend/package.json`

## 2. Source of Truth Mappings:
| Category | Mapping |
| :--- | :--- |
| **CSS Input** | `frontend/static/input.pcss` |
| **Tailwind Config** | `frontend/tailwind.config.js` |
| **Compiled CSS** | `frontend/static/styles.css` |
| **Agent State** | `.agent/skills/Lead_Frontend/design-system/SKILL_STATE.json` |

## 3. Tooling Requirements:
- TailwindCSS
- PostCSS
- npm

## 4. Strict Workflow Rules:
1. Run `npm run build:css` after any style modifications.
2. Update `SKILL_STATE.json` upon task completion.

## 5. Domain-Specific Rules:
- Avoid inline CSS. Rely entirely on Tailwind utility classes.
- Follow `.agent/rules/02-tailwind-frontend.md` rules for glassmorphism.
- **Animation Vocabulary:** Refer to `.agent/skills/Lead_Frontend/design-system/animation-vocabulary.md` for standardized terminology when creating, reviewing, or prompting for motion, transitions, and easing effects.
- **XAI Entity Tokens:** You MUST maintain specific color schemes for medical entity tags in `script.js` (e.g., Red for `PROBLEM`, Blue for `TREATMENT`, Green for `TEST`, Purple for `MEDICATION`). Ensure these colors pass accessibility contrast checks.
- **Image Previews:** Ensure the EasyOCR image upload dropzone (`#dropzone`) provides visual feedback (e.g., border color changes on drag over) and properly scales the preview image.

## 6. Karpathy Execution Protocol:
- **XML-Strict Reasoning:** Wrap logic in `<thought>`, `<surgical_plan>`, `<verification_log>`.
- **Minimal Edits:** Do not rewrite entire files.

## 7. Collaboration & Hand-offs:
- **To Core Architecture:** Inform them of any necessary utility classes added to HTML, particularly for the XAI Annotated Text highlighting.

## 8. Troubleshooting Decision Tree:
- **Issue: Styles not updating** -> *Check:* `frontend/static/styles.css` cache -> *Fix:* Rerun `npm run build:css` (in frontend dir).
- **Issue: Entity Tags unreadable** -> *Check:* Tailwind color opacity -> *Fix:* Use solid text colors with low-opacity backgrounds (e.g., `bg-red-500/20 text-red-700`).

## 9. Strict Output Formats:
Output the following upon completion:
```markdown
### Design System Report
- **CSS Compiled:** [Yes/No]
- **Components Styled:** [List]
```

## Initial Acknowledgment
"Frontend Design System rules acknowledged. Ready to style Medical XAI interfaces."
