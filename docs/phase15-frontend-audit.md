# Frontend UI/UX Audit — Phase 15 Hardening

This audit covers pages, layouts, inputs, buttons, and loading states across the NOVA AI frontend interface.

## 1. Discovered Issues & Technical Debt

### A. Code Quality & Logic Bugs
* **Sidebar Menu Ref Override**: In `Sidebar.tsx`, the `menuRef` is instantiated inside a `map` loop. The ref value gets overwritten on each list item render, causing click-outside close handlers to only function correctly on the final element of the list.
* **Mock File Attachment Uploads**: In `ChatInput.tsx`, selecting a local file triggers simulated upload timers instead of transmitting the payload to the actual RAG `/api/documents/upload` route.
* **Browser Alerts for Shortcuts**: The keyboard shortcuts reference displays a raw browser `alert()` modal, diverging from the premium glassmorphic modal design language.

### B. Keyboard Accessibility & WCAG Gaps
* **Missing Keyboard Action**: The shortcut reference mentions `Ctrl+N` for a new conversation, but this is never captured in the event handler in `MainLayout.tsx`.
* **Missing Semantic Indicators**: Toggle buttons (Sidebar drawer, Speech-to-text, Tools menus) are missing standard WCAG fields like `aria-expanded` and `aria-selected` to inform assistive screen-readers of dynamic updates.
* **prefers-reduced-motion**: High-frequency animations (rotating loading icons, pulsing microphone effects, sliding drawers) do not offer static or slowed-down variants when a user requests reduced motion in system preferences.

### C. Error Fault Tolerance
* **Application Crashes**: Standard React rendering errors (e.g. malformed markdown rendering, bad local Storage parsing) lack local Error Boundaries, risking blank screens on client crashes.

---

## 2. Component Health Summary

| Component Name | File Path | Status | Planned Refinements |
| :--- | :--- | :--- | :--- |
| **Root Layout** | `src/app/layout.tsx` | Healthy | Wrap body with root-level Error Boundary. |
| **Chat Workspace** | `src/app/page.tsx` | Healthy | Track uploading file states, handle errors gracefully. |
| **Shell Frame** | `src/components/layout/MainLayout.tsx` | Hardening | Wire up `Ctrl+N` handler, replace browser alerts with dialogs. |
| **Navigation** | `src/components/layout/Sidebar.tsx` | Hardening | Implement DOM class-closest detection for outside clicks, add accessibility tags. |
| **Composer** | `src/components/chat/ChatInput.tsx` | Hardening | Connect local file selection to real document uploads. |
| **Command Palette** | `src/components/ui/CommandPalette.tsx` | Healthy | Improve accessibility markup, focus restoration. |

---

## 3. Responsive Breakpoints Verification

All critical pages (login, register, main layout) scale correctly across target dimensions:
* **Mobile (320px - 414px)**: Sidebar folds into a drawer with backdrop blur overlay. The chat input wraps content efficiently without overflow.
* **Tablet (768px)**: Sidebar stays hidden by default; can be toggled using the header menu button.
* **Desktop (1024px - 1920px)**: Sidebar remains docked; fluid layout adjusts chat prompt margins.
