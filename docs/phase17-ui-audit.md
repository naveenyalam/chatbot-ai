# Phase 17 — Frontend UI Audit

This document audits the complete presentation layer of the NOVA AI application.

## 1. Layout & Spacing Problems
- **Stale Cascade CSS Overrides:** Redundant global resets in `src/app/globals.css` (specifically `* { padding: 0; margin: 0; }`) override cascade-layered Tailwind CSS utility variables, leading to zero-padding text-icon overlaps and collapsed element heights.
- **Fixed and Arbitrary Widths:** Hardcoded constraints like `max-w-[440px]` on authentication wrappers prevent standard split-screen grid scaling.
- **Cramped Form Rhythm:** Form controls and input sections lack standard vertical breathing room (e.g. inputs stacked tightly near action buttons, checkbox containers aligned poorly with adjacent OAuth buttons).
- **Z-Index Collision:** Sidebars and command palettes use inconsistent `z-index` numbers (e.g. `z-35`, `z-40`, `z-50`, `z-55`), risking overlay overlap conflicts.

## 2. Typography Problems
- **Variable Font Misalignment:** Inconsistent usage of local font family scales versus Tailwind defaults.
- **Lack of Hierarchical Weighting:** Text hierarchies between page headers, segment cards, input labels, and auxiliary footer links are flat, reducing form legibility.
- **Line-Height Compression:** Tight leading on multi-line text descriptions (like OAuth dividers) creates visually compressed headers.

## 3. Responsive Problems
- **Absence of Split Grid Desktop Layout:** The login page uses a single card layout centered in the screen regardless of view width, wasting desktop space.
- **Lack of Tablet Adaptation:** No medium-width tablet configuration to transition from two-column to single-column auth layouts.
- **Mobile Edge Overflow Risk:** Elements using custom margins or fixed padding (like `pl-11` or absolute offsets) risk edge-clipping on 375px viewport sizes.

## 4. Authentication UI Problems
- **No Introduction Panel:** Desktop users are shown a blank background with a single floating login card, which looks like a developer prototype rather than a premium enterprise portal.
- **SSO Button Compressions:** Google and GitHub action buttons are cramped, using inline SVGs and hardcoded background values that mismatch the dark mode system.
- **Overlapping Icons:** Non-standard Tailwind padding offsets (like `pl-11`) result in placeholder inputs overriding left-aligned icon positions.

## 5. Component Consistency Problems
- **Invalid Tailwind Modifier Usage:** Elements in the `Sidebar` and `Header` components use `light:` prefixed modifiers (e.g. `light:bg-white`, `light:border-zinc-200`) which are not standard Tailwind modifiers. This breaks light mode compatibility.
- **Ad-Hoc Dark/Light Styles:** Hardcoded hex values like `bg-[#0b0f19]/70` are distributed randomly across files rather than using semantic variables.

## 6. Accessibility & Theme Problems
- **Insufficient Contrast:** Background colors lack semantic separation in light mode.
- **Lack of Aria Labels:** Icon-only control elements (e.g. settings sliders, command panel buttons) lack explicit descriptive `aria-label` tags.

## 7. Proposed Architecture
- **Implement a Strict Design System:** Declare centralized HSL-based colors in CSS variables under `@theme` inside `globals.css` for background, surface, borders, text states, and primary accents.
- **Split-Screen Authentication Shell:** Re-architect authentication pages into a two-column desktop grid: a custom product presentation panel on the left and a centralized card container on the right, collapsing into a single-column layout on mobile.
- **Standardize Form Controls:** Rebuild inputs to a consistent height (48–52px) with structured absolute icon offsets.
- **Sanitize Global Resets:** Remove raw unlayered `*` selector resets to protect Tailwind's Cascade Layer styles.
