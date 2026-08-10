# Phase 17 — Design System & Tokens

This document details the centralized visual system implemented for **NOVA AI**.

## 1. Color Palette Tokens

The colors map to standard CSS custom variables for both dark and light modes:

| Variable | Dark Value (Default) | Light Value | Semantic Mapping |
| :--- | :--- | :--- | :--- |
| `--background` | `#070A12` | `#f8fafc` | Main screen backdrop |
| `--foreground` | `#f9fafb` | `#0f172a` | Default body copy |
| `--surface` | `#111827` | `#ffffff` | Content container bg |
| `--surface-elevated` | `#151b28` | `#f1f5f9` | Cards, popovers, drawers |
| `--surface-hover` | `#1a2233` | `#e2e8f0` | Hover states |
| `--border` | `rgba(255,255,255,0.08)`| `rgba(15,23,42,0.08)` | Subtly distinct dividers |
| `--border-strong` | `rgba(255,255,255,0.16)`| `rgba(15,23,42,0.16)` | Inputs, focus rings |
| `--primary` | `#4f46e5` | `#4f46e5` | Focus accents, brand buttons |
| `--primary-hover` | `#4338ca` | `#4338ca` | Button hover states |
| `--ring` | `rgba(99,102,241,0.3)` | `rgba(99,102,241,0.2)` | Interactive focus shadows |
| `--danger` | `#ef4444` | `#dc2626` | Destructive/error states |
| `--success` | `#10b981` | `#16a34a` | Confirmation alerts |
| `--warning` | `#f59e0b` | `#d97706` | Warning/system notifications |

## 2. Typography Standard Scale

- **Page Titles:** `30px` (tracking tight, extra-bold)
- **Section Headers:** `22px` (semibold)
- **Sub-headers / Card Labels:** `15px` (medium)
- **Body Text:** `14px` (regular, leading comfortable)
- **Helper Labels:** `12px` / `13px` (regular, muted colors)

## 3. Spacing Rhythm

We strictly adhere to an 8px grid alignment scale:
- `4px` - Micro paddings / indicators
- `8px` - Labels to inputs / gap spacings
- `12px` - Inner element lists / social group gaps
- `16px` - Card segments / medium gutters
- `24px` - Form fields vertical rhythms
- `32px` - Sidebar content dividers
- `48px` - Input Heights / Button sizes
