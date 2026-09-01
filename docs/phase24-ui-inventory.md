# Phase 24 — UI/UX and Accessibility Inventory

This inventory captures all major interactive components, modal elements, selection controls, accessibility features (ARIA/WCAG), and responsive breakpoints in the NOVA AI Next.js frontend application.

---

## 1. Global Component & Button Inventory

### 1.1 Buttons (`src/components/ui/Button.tsx`)
* **Purpose:** Reusable button component providing glassmorphism and styled variants.
* **Accessibility (a11y):** Keyboard focus outline (`focus-visible:ring-2 focus-visible:ring-accent`), support for `aria-disabled` and `aria-label`.
* **Variants:**
  * **Primary:** Glow highlights, dark background (used for Send, Confirm, and Action triggers).
  * **Secondary:** Outlined border (used for Cancel, Close, and Secondary actions).
  * **Ghost:** Zero borders, background color appears only on hover (used for inline edits, delete, copy, and sidebar triggers).

### 1.2 Modals & Dialogs
* **Confirmation Modal (`src/components/ui/ConfirmationModal.tsx`):**
  * **Controls:** "Confirm" button (Danger/Primary), "Cancel" button (Secondary).
  * **Keyboard Accessibility:** Esc key closes dialog, focus traps active elements inside the modal.
  * **ARIA:** `role="dialog"`, `aria-modal="true"`, `aria-labelledby="confirm-title"`.
* **Command Palette (`src/components/ui/CommandPalette.tsx`):**
  * **Controls:** Search Input, list of action buttons, filter buttons.
  * **Keyboard Accessibility:** `Ctrl + K` shortcuts to toggle, arrow keys to navigate suggestions, `Enter` to select.

### 1.3 Settings & Selection Dropdowns (`src/components/settings/SettingsPanel.tsx`)
* **Theme Selector:**
  * **Controls:** Dark, Light, Cyberpunk theme selection buttons.
  * **Persistence:** Saved in `localStorage` and immediately updates body class list (`theme-dark`, etc.).
* **Model Selector:**
  * **Controls:** Selection dropdown mapping to active backend models (`gpt-4o-mini`, etc.).
* **Chat Detail & Tone Selectors:**
  * **Controls:** Options for Detail (`concise`, `balanced`, `detailed`) and Tone (`professional`, `friendly`, `technical`).
* **Keyboard Navigation:** Fully focusable with Tab, standard select menus use native `<select>` tags or custom listbox wrappers with keyboard support.

---

## 2. Page Layouts & Responsive Breakpoints

NOVA AI uses CSS media queries to guarantee full usability across different device classes.

### 2.1 Screen Breakpoints
1. **Desktop (`1920x1080` & `1440x900`):**
   * Full three-column layout (Sidebar navigation, active chat conversation viewport, document library sidebar).
   * Large visual real-estate, sidebar is pinned open by default.
2. **Tablet (`768x1024`):**
   * Sidebar navigation collapses into a left sliding panel (hamburger menu trigger).
   * Center chat viewport expands to fill the screen width.
   * Document library is accessible via a modal drawer.
3. **Mobile (`375x667` & `412x915`):**
   * Single-column layout.
   * Sidebar and workspace mode selectors are collapsible drawers.
   * Input box scales to full-width; font sizes increase to at least `16px` to prevent automatic zoom on iOS devices.

---

## 3. UI/UX Polishing & Interaction Details

* **Loading States:**
  * **Thinking Indicator (`src/components/chat/ThinkingIndicator.tsx`):** Smooth pulsing dots showing background RAG retrieval or active LLM generation.
  * **Upload States:** Spinner overlays on document cards when parsing is `"uploaded"` or `"processing"`.
* **Toast Alerts (`src/components/ui/Toast.tsx`):**
  * **Behavior:** Automatically dismisses after 5 seconds, supports `success`, `error`, and `info` categories. Can be dismissed manually via `[x]` button.
* **Error Recovery:**
  * **Error Boundary (`src/components/ui/ErrorBoundary.tsx`):** Captures unhandled React rendering exceptions and renders a safe fallback with a "Retry / Reload Application" button.
* **Streaming Markdown (`src/components/chat/MarkdownRenderer.tsx`):**
  * Renders markdown chunks dynamically. Contains an inline copy button on all code blocks, syntax-highlighted code panels, and tables.
