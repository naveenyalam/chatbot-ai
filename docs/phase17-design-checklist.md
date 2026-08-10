# Design Quality Checklist — Phase 17

This checklist defines standard rules to maintain cohesive, high-quality, premium visual styling across all screen sizes and themes.

---

## 1. Typography & Hierarchy
- [ ] **Headings**: Use sans-serif (Inter/Outfit) weights: 800 (h1), 700 (h2), 600 (h3).
- [ ] **Paragraphs**: Text sizing should be `text-sm` (14px) for readability, `text-xs` (12px) for metadata/sub-labels, and `text-[10px]` for tags.
- [ ] **Monospace**: Code snippets must use a strict monospaced family (Fira Code, JetBrains Mono) at `text-xs` or `text-sm`.

---

## 2. Spacing, Borders & Shadows
- [ ] **Padding**: Maintain consistent container paddings: `p-4` (mobile viewports), `p-6` to `p-8` (desktop screens).
- [ ] **Borders**: All cards, inputs, and dropdown overlays must use a border width of `1px` with a subtle tint (`border-white/10` for dark theme, `border-zinc-200` for light theme).
- [ ] **Gradients**: Limit heavy gradients; restrict them to core brand highlights (e.g. submit CTA button and brand logo header).
- [ ] **Radii**: Apply uniform rounded corners: `rounded-xl` for small items (buttons, inputs), `rounded-2xl` for message blocks, `rounded-3xl` for main overlay panels.

---

## 3. UI States (Empty, Loading, Errors)
- [ ] **Loading**: Always render a spinning animated SVG spinner or skeleton block. Disable control inputs during execution to block extra requests.
- [ ] **Errors**: Wrap failures in a red warning card. Provide recovery buttons (e.g. Retry or Reload) instead of simple messages.
- [ ] **Empty States**: Present simple descriptions, a helpful icon, and a quick-action button.

---

## 4. Accessibility & Transitions
- [ ] **Focus Rings**: Interactive elements must show a distinct outline ring on focus (`focus:ring-2 focus:ring-indigo-500/30`).
- [ ] **ARIA**: Screen reader tags (`aria-label`, `aria-expanded`, `role`) must match current active states.
- [ ] **Animations**: Keep transitions light: duration `150ms` to `200ms` max, using ease-out easing parameters.
