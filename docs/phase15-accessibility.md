# Accessibility & WCAG Audit — Phase 15 Hardening

This document reports on accessibility features, screen-reader optimizations, and motion guidelines in the NOVA AI system.

## 1. Implemented WCAG Enhancements

* **Screen Reader Labels & Attributes**:
  * Added `aria-label`, `aria-haspopup`, and `aria-expanded` attributes to key toggle controls including:
    * Sidebar drawer menus (`Sidebar.tsx`).
    * User account profiles (`Sidebar.tsx`).
    * AI intelligence model selectors (`Header.tsx`).
* **Focus Management**:
  * Keyboard navigation and focus trapping inside the **Command Palette** and **Shortcuts Dialog** overlay modals.
* **Keyboard Hotkeys**:
  * Support for standard shortcuts:
    * `Ctrl+K` / `Cmd+K`: Toggle Command Palette.
    * `Ctrl+N` / `Cmd+N`: Instantiate new chat session.
    * `Escape`: Dismiss active modals, panels, and slide-overs.

---

## 2. Animation & Reduced Motion Compliance

NOVA AI features smooth glassmorphic transition effects and gradient glows. To support users sensitive to motion, we enforce a strict CSS reset:

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-delay: 0s !important;
    animation-duration: 0s !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0s !important;
    scroll-behavior: auto !important;
  }
  
  .animate-float,
  .animate-float-slow,
  .animate-spin-slow,
  .animate-spin-reverse,
  .animate-pulse-slow,
  .animate-glow {
    animation: none !important;
    transform: none !important;
  }
}
```

This overrides high-frequency decorative animations instantly if the host operating system reports a "Reduce Motion" preference.
