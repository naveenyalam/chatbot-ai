# Product Experience Audit — Phase 16

This document records the user journey audit, highlighting UX gaps, broken flows, missing states, and recommendations.

## 1. Landing, Authentication & Session Life-Cycle
* **Current Behavior**:
  * Root path `/` redirects to `/login` if not authenticated.
  * Successful login sets standard secure HTTP-Only session cookies.
  * If a session expires, the API calls fail with 401, but the client might not redirect or preserve current composer text cleanly.
* **UX Gaps & Recommended Fixes**:
  * **Expirations**: Translate authentication failures to a toast and redirect, but retain compose draft state locally in standard memory so users don't lose long prompts.
  * **Flashes**: Ensure the transition from redirect is smooth with a branded loading skeleton.

---

## 2. Conversation Management
* **Current Behavior**:
  * Users can create new chats, rename them, duplicate, and delete them.
  * Sidebar lists and filters chats by title locally.
* **UX Gaps & Recommended Fixes**:
  * **Delete Confirmation**: The sidebar menu triggers deletion immediately. We must add a clean, custom confirmation dialog before executing deletes to prevent data loss.
  * **Active Chat Highlighting**: Highlighting needs to be contrast-hardened.
  * **Shortcuts**: Key shortcut `Ctrl/Cmd + N` starts a new chat cleanly.

---

## 3. Command Palette (`Ctrl+K`)
* **Current Behavior**:
  * The command palette supports filtering commands like theme toggling and view switches.
* **UX Gaps & Recommended Fixes**:
  * **Search Integration**: Integrate conversation list searching directly inside the command palette to let users jump to recent threads.
  * **Keyboard Navigation**: Ensure index bounds are safe when results list updates dynamically.

---

## 4. Streaming Response experience
* **Current Behavior**:
  * Server-Sent Events stream assistant tokens to the UI.
* **UX Gaps & Recommended Fixes**:
  * **Auto-Scroll Behavior**: Long streaming chats push the viewport down, but manual user scrolling up is overridden by autoscroll, fighting the user. We must implement smart auto-scroll checking (scroll lock release if scrolled up, with a floating "↓ New response" anchor button).
  * **Cursor & Status States**: Add clear dynamic status tags (e.g., "Thinking...", "Searching documents...") matching the real backend status events.
