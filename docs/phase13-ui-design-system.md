# Phase 13 — NOVA AI UI Design System Specification

## 1. Design Principles

- **AI-Native & Futuristic**: Minimalist interface prioritizing content, streaming text readability, and context awareness.
- **Enterprise Precision**: Crisp borders, subtle glassmorphism, consistent 8px grid spacing, and balanced typography scales.
- **Dual-Theme Superiority**: Complete parity between Dark Mode (deep zinc/slate) and Light Mode (soft porcelain/white) without color contrast degradation.

---

## 2. Design Tokens & CSS Variables

```css
/* Dark Theme (Default) */
:root, .dark {
  --background: #030712;
  --foreground: #f9fafb;
  --surface-primary: #0b0f19;
  --surface-secondary: #111827;
  --surface-tertiary: #1f2937;
  --border-subtle: rgba(255, 255, 255, 0.08);
  --border-hover: rgba(99, 102, 241, 0.3);
  --text-primary: #f9fafb;
  --text-secondary: #d1d5db;
  --text-muted: #9ca3af;
  --accent-primary: #6366f1;
  --accent-hover: #4f46e5;
  --accent-gradient: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #06b6d4 100%);
  --glass-bg: rgba(11, 15, 25, 0.85);
  --glass-border: rgba(255, 255, 255, 0.1);
}

/* Light Theme */
.light {
  --background: #f8fafc;
  --foreground: #0f172a;
  --surface-primary: #ffffff;
  --surface-secondary: #f1f5f9;
  --surface-tertiary: #e2e8f0;
  --border-subtle: rgba(15, 23, 42, 0.1);
  --border-hover: rgba(79, 70, 229, 0.4);
  --text-primary: #0f172a;
  --text-secondary: #334155;
  --text-muted: #64748b;
  --accent-primary: #4f46e5;
  --accent-hover: #4338ca;
  --accent-gradient: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #0284c7 100%);
  --glass-bg: rgba(255, 255, 255, 0.9);
  --glass-border: rgba(15, 23, 42, 0.1);
}
```

---

## 3. Typography Hierarchy

| Level | Size | Weight | Line Height | Usage |
| :--- | :--- | :--- | :--- | :--- |
| **Display** | 3rem (48px) | 800 (Black) | 1.1 | Auth Headings & Main Hero Titles |
| **H1** | 2.25rem (36px) | 800 (Bold) | 1.2 | Section Headers & Workspace Titles |
| **H2** | 1.5rem (24px) | 700 (Bold) | 1.3 | Card Headings & Modal Titles |
| **H3** | 1.125rem (18px) | 600 (Semibold) | 1.4 | Subheaders & Feature Titles |
| **Body** | 0.875rem (14px) | 400 (Regular) | 1.5 | Chat Messages, Input Text, Descriptions |
| **Small** | 0.75rem (12px) | 500 (Medium) | 1.4 | Badges, Timestamps, Labels |
| **Caption** | 0.625rem (10px) | 600 (Semibold) | 1.3 | Metadata & Status Indicators |

---

## 4. UI Primitives

1. **Button**:
   - `primary`: Gradient background (`from-indigo-600 to-purple-600`), white text, shadow ring.
   - `secondary`: Surface border (`border-subtle`), hover elevation.
   - `ghost`: Transparent background, muted text, soft hover tint.
   - `danger`: Red tint (`bg-red-500/10 text-red-400 border-red-500/20`).

2. **Input & Textarea**:
   - Surface backdrop, 1px subtle border, 12px padding, indigo focus ring (`focus:ring-2 focus:ring-indigo-500/50`).

3. **Card & Glass Panel**:
   - Rounded 2xl or 3xl, backdrop blur (20px), subtle 1px border.

4. **Badges**:
   - Rounded full, 10px bold uppercase font, status-aware background tints (Emerald for complete, Indigo for running, Amber for warning, Red for error).
