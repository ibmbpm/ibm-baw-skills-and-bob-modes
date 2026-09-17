# Quality and validation

> **Skill:** `create-baw-portal`
> **Purpose:** Accessibility, security, and data-freshness requirements for generated portals.
> **Evidence:** `scripts/audit-a11y.mjs` (78 checks) · `scripts/audit-security.mjs` (25 checks) ·
> `scripts/audit-refresh.mjs` (40 checks) · Reference HTML passes all 143 checks.

---

## Audit suite

Three static audit scripts exist as a regression guard for the approved reference HTML example.
They are hardcoded to the reference file and **cannot be pointed at generated output**:

```bash
# Validates the approved reference example only — not generated portals
node skills/create-baw-portal/scripts/audit-a11y.mjs      # 78 checks
node skills/create-baw-portal/scripts/audit-security.mjs  # 25 checks
node skills/create-baw-portal/scripts/audit-refresh.mjs   # 40 checks
```

Reference file: `assets/examples/ibm-baw-task-dashboard/ibm-baw-task-dashboard.html`
All three currently exit `0`. Run them if the reference HTML is ever edited to catch regressions.

**For generated portals:** use the requirements in this document as a checklist during code review.
The checks below describe exactly what the scripts look for — apply the same bar manually or
through equivalent tooling for any stack (standalone HTML, React, Vue, etc.).

---

## Accessibility (78 checks, A01–A78)

### Structural landmarks

- `<header>`, `<main id="main-task-content" tabindex="-1">`, `<nav>`, `<section>`
- `<h2>` for section headings
- Skip link targeting `#main-task-content`; visible on `:focus`

### Interactive elements

- All buttons: `type="button"` — no omissions
- Stat cards: `<button type="button">` with `aria-pressed` (initial "All Tasks" = `"true"`)
- Sort buttons: `class="sort-btn"` with `aria-sort`; updated on each sort call
- `:focus-visible` ring defined globally
- `--touch-target` CSS variable; stat cards, buttons, and mobile tap targets all at minimum 44×44 CSS px

### Forms and labels

- Explicit `<label for="searchInput">`, `<label for="priorityFilter">`, `<label for="statusFilter">`

### Dynamic content

- `.sr-only` class defined
- Priority and status badges include screen-reader-only text prefixes
- `.status-dot` is `aria-hidden="true"`
- Loading state: `role="status"` · Error state: `role="alert"` · State icons: `aria-hidden`
- `announceSR()` function present
- `aria-live="polite"` on `#srTableStatus` and `#resultCount`
- `aria-live="assertive"` on `#toastContainer`

### Motion

- `@media (prefers-reduced-motion: reduce)` — `animation-duration: .01ms` on all animations;
  pull-to-refresh CSS transitions suppressed

### Modal (task iframe)

- `role="dialog"` `aria-modal="true"` `aria-labelledby` `aria-describedby`
- Focus sentinels at start and end of modal
- Focus trapping functions (`trapFocusToEnd`, `trapFocusToStart`)
- `openTask()` moves focus to close button on open
- Escape key → `closeModal()`
- `closeModal()` restores focus to the element that triggered the modal

### Task iframe security

- `taskId` validated numeric: `/^\d+$/.test(String(taskId))`
- iframe URL hard-coded to `/teamworks/process.lsw`
- iframe `src` cleared to `'about:blank'` on close
- `title="Task form"` on iframe
- Add `TODO` comment noting `sandbox` attribute is pending deployment validation (deployment advisory)

### Mobile

- Mobile card layout present at narrow breakpoint (`max-width: 680px`)
- Desktop table hidden at narrow breakpoint
- Responsive pagination shared between desktop and mobile layouts
- Toolbar wraps at narrow breakpoint

### Pull-to-refresh (mobile)

- `#ptrIndicator` with `aria-hidden="true"`
- Touch device gate: `'ontouchstart' in window`
- PTR only at `scrollTop === 0`; blocked when modal is open
- All touch listeners `{ passive: true }`
- `prefers-reduced-motion` suppresses PTR CSS transitions

---

## Security (25 checks, S01–S25)

- `'use strict'` present
- `escHtml()` applied to all task field values before `innerHTML` insertion
- No unescaped task data in `innerHTML` template literals
- `state.loading` in-flight guard; `finally` block resets `state.loading`
- Search input debounced with `clearTimeout` / `setTimeout`
- `clearAllFilters()` calls `applyFilters()` directly — no debounce delay
- `MAX_TOASTS` constant; oldest toast evicted on overflow
- No unsafe inline event handlers on `<body>` or `<html>`
- `credentials: 'same-origin'` on all `fetch()` calls
- `taskId` numeric validation before URL construction
- `encodeURIComponent(taskId)` in iframe URL
- iframe URL hard-coded — not constructed from user input
- No `eval()`, no `document.write()`

**Additional requirements enforced by code review:**

- No task data, task IDs, or process data in `localStorage` — in-memory only
- Full API response payloads not logged to `console`
- XSRF: Use `credentials: 'same-origin'` for all WLE REST mutations — no `bpm-csrf-token` header required (see non-federated-api-guide.md).

---

## Refresh pipeline (40 checks, R01–R40)

- `POLL_INTERVAL` and `STALE_THRESHOLD` constants
- `triggerRefresh(silent = false)` — single public entry point; returns early when `state.loading`
- `_doLoad()` — internal async implementation
- `computeFingerprint()` — compare fingerprints; update `state.taskFingerprint` after fetch
- `state.lastUpdatedAt = new Date()` — update on success
- `startPolling()` / `stopPolling()` / `resetPollTimer()` using `setInterval` / `clearInterval`
- `visibilitychange` listener: silent refresh on `visible`; skip poll when `hidden`
- `#refreshBar` with `aria-live`, `#lastUpdatedLabel`, `#staleMsg`
- `.refresh-bar.stale` CSS rule; `markStale()` adds `.stale`
- Refresh button toggles `.refreshing` class and `disabled` state during load
- `prefers-reduced-motion` suppresses spinner animation
- `closeModal()` calls `triggerRefresh(true)` after close
- Init: `triggerRefresh(false)` + `startPolling()`
- Non-silent load calls `renderTableLoading()`; silent poll failure calls `markStale()` and `toast()`

---

## Responsive validation

Visual review required at:

| Breakpoint | Width |
|---|---|
| Desktop | 1280 px + |
| Tablet | 768–899 px |
| Mobile | ≤ 600 px |

Reference screenshot: `assets/examples/ibm-baw-task-dashboard/screenshots/desktop.jpeg`

---

## Static versus runtime validation

**Static audits (scripts):** Validate code patterns in the HTML source. Necessary but not sufficient.

**Runtime validation:** Required before a generated portal is delivered.

Before delivery, the developer must confirm:

1. Test against a live BAW instance for the specific deployment target.
2. Task list API returns data and the task launch iframe opens correctly.
3. Keyboard-only navigation test.
4. Screen-reader announcement test.
5. 200% and 400% zoom / reflow test.
6. Confirm `totalCount` vs returned count and surface truncation indication if paging is required.
7. Confirm CSP header with BAW administrator before deploying inline implementations.
8. Test `sandbox` attribute compatibility with BAW task forms before enabling the `sandbox` attribute.

**Do not claim live runtime validation** unless an authenticated BAW environment was used in the current session.

---

## Completed audit evidence

The reference HTML passes all 143 static checks. These results are recorded in the repository
and must not be regenerated or re-attributed to a new run without cause.

Reference the existing audit results as baseline evidence for the reference implementation.
New portals must independently achieve a 100% pass rate — they do not inherit the reference's audit status.
