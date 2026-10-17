# Prompt: IBM BAW Process Portal

Create a full IBM BAW Process Portal as a single self-contained HTML file with embedded CSS and JavaScript.

---

## Critical Constraints — Read Before Writing Any Code

BAW Coach Views run inside an `<iframe>` served from the BAW host. The server sets:

```
Content-Security-Policy: default-src 'self'
```

The browser blocks every `fetch()` to any external domain before the request is sent — no workarounds exist.

**Do not include:**
- `<script src="…">`, `<link href="…">`, or `fetch()` pointing to a non-BAW domain
- The IBM logo in SVG — do not construct it from `<rect>` or `<path>` elements
- `import` statements of any kind

**Only these network calls are permitted:**
- `GET/PUT/POST/DELETE /rest/bpm/wle/v1/…` — BAW WLE REST API (same-origin)
- `GET /teamworks/…` — BAW task form URLs loaded in `<iframe>`

---

## File Structure

Single `.html` file:
- `<style>` block — all CSS inline, no `<link>` tags
- `<script>` block — all JS inline, no `<script src>` tags
- Font stack: `'IBM Plex Sans', 'Helvetica Neue', Arial, sans-serif` — do not load from any CDN

---

## Design Tokens

Define on `:root`:

```css
--ibm-blue-70:   #0043ce;
--ibm-blue-60:   #0f62fe;
--ibm-blue-50:   #4589ff;
--ibm-blue-10:   #edf5ff;
--ibm-gray-100:  #161616;
--ibm-gray-90:   #262626;
--ibm-gray-80:   #393939;
--ibm-gray-70:   #525252;
--ibm-gray-60:   #6f6f6f;
--ibm-gray-40:   #a8a8a8;
--ibm-gray-20:   #e0e0e0;
--ibm-gray-10:   #f4f4f4;
--ibm-white:     #ffffff;
--ibm-red-60:    #da1e28;
--ibm-red-10:    #fff1f1;
--ibm-orange-40: #ff832b;
--ibm-orange-10: #fff2e8;
--ibm-green-50:  #198038;
--ibm-green-10:  #defbe6;
--ibm-yellow-20: #fdd13a;
--ibm-yellow-10: #fcf4d6;
--ibm-purple-60: #8a3ffc;
--ibm-purple-10: #f6f2ff;
--ibm-teal-50:   #009d9a;
--ibm-teal-10:   #d9fbfb;
--radius:        4px;
--shadow-sm:     0 1px 3px rgba(0,0,0,.12), 0 1px 2px rgba(0,0,0,.08);
--shadow-md:     0 4px 12px rgba(0,0,0,.15);
--transition:    160ms cubic-bezier(.2,0,.38,.9);
--header-h:      48px;
--nav-w:         220px;
--touch-target:  44px;
--ptr-indicator-h: 56px;
```

---

## Page Layout

```
┌────────────────────────────────────────────────────────────┐
│  FIXED HEADER  48px  background: --ibm-gray-100            │
│  [☰]  IBM BAW Process Portal          [avatar ▾ name]      │
└────────────────────────────────────────────────────────────┘
┌──────────┬─────────────────────────────────────────────────┐
│ SIDEBAR  │  MAIN AREA  (scrollable)                        │
│ 220px    │                                                  │
│ bg:      │  Active view rendered here                       │
│ gray-90  │  (My Tasks / Start Process / Task Search /       │
│          │   Team View / Administration)                    │
│ My Work  │                                                  │
│ ☑ Tasks  │                                                  │
│ ▶ Start  │                                                  │
│ 🔍 Search│                                                  │
│ Team     │                                                  │
│ ⚙ Admin  │                                                  │
└──────────┴─────────────────────────────────────────────────┘
```

On mobile (`≤768px`): sidebar is hidden by default; `☰` toggle button appears in header. A dark semi-transparent backdrop covers main content when the sidebar is open.

---

## Header

```html
<header class="app-header">
  <button type="button" class="sidebar-toggle" id="sidebarToggle"
    aria-label="Toggle navigation" aria-expanded="false">☰</button>
  <span class="header-logo"><span>IBM</span> BAW Process Portal</span>
  <div class="header-spacer"></div>
  <div class="header-right">
    <button type="button" class="user-profile-btn" id="userProfileBtn"
      aria-label="User profile" aria-haspopup="true" aria-expanded="false"
      onclick="toggleProfileDropdown()">
      <div class="user-avatar" id="userAvatar" aria-hidden="true">?</div>
      <span class="user-name" id="userName">Loading…</span>
      <span aria-hidden="true">▾</span>
    </button>
    <div class="user-dropdown" id="userDropdown" role="menu" aria-label="User profile">
      <div class="user-dropdown-header">
        <div class="user-dropdown-avatar" id="dropdownAvatar" aria-hidden="true">?</div>
        <div>
          <div id="dropdownFullName">—</div>
          <div id="dropdownUserName">—</div>
        </div>
      </div>
      <div id="dropdownBody"><p>Loading profile…</p></div>
    </div>
  </div>
</header>
```

- Fixed, `z-index: 300`, background `--ibm-gray-100`
- **No logo image of any kind** — the coloured `<span>IBM</span>` + text is the brand identifier
- Avatar: 28×28px circle, `background: --ibm-blue-60`, shows user initials in white
- Profile dropdown populated by `loadUser()` / `renderProfileDropdown()` — only renders fields actually returned by the API
- Clicking outside the dropdown closes it via a `document.addEventListener('click', …)` handler

---

## Sidebar Navigation

```html
<nav class="sidebar" id="sidebar" aria-label="Main navigation">
  <span class="nav-section-label">My Work</span>
  <button type="button" class="nav-item active" id="nav-tasks"
    onclick="showView('tasks')" aria-current="page">
    <span class="nav-icon" aria-hidden="true">☑</span>
    My Tasks
    <span class="nav-badge" id="navTaskBadge" style="display:none"></span>
  </button>
  <button type="button" class="nav-item" id="nav-launch" onclick="showView('launch')">
    <span class="nav-icon" aria-hidden="true">▶</span> Start Process
  </button>
  <button type="button" class="nav-item" id="nav-search" onclick="showView('search')">
    <span class="nav-icon" aria-hidden="true">🔍</span> Task Search
  </button>
  <hr class="nav-divider" />
  <span class="nav-section-label">Team</span>
  <button type="button" class="nav-item" id="nav-team" onclick="showView('team')">
    <span class="nav-icon" aria-hidden="true">👥</span> Team View
  </button>
  <hr class="nav-divider" />
  <span class="nav-section-label">System</span>
  <button type="button" class="nav-item" id="nav-admin" onclick="showView('admin')">
    <span class="nav-icon" aria-hidden="true">⚙</span> Administration
  </button>
</nav>
```

`navTaskBadge` shows the overdue task count in red; hidden when count is 0.

```js
function showView(name) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => {
    n.classList.remove('active'); n.removeAttribute('aria-current');
  });
  document.getElementById(`view-${name}`)?.classList.add('active');
  const btn = document.getElementById(`nav-${name}`);
  if (btn) { btn.classList.add('active'); btn.setAttribute('aria-current', 'page'); }
  closeSidebar();
  /* Lazy-load data on first visit */
  if (name === 'launch' && state.allProcesses.length === 0) loadLaunchableProcesses();
  if (name === 'search' && state.savedSearches.length === 0) loadSavedSearches();
  if (name === 'search') loadSearchMetadata();
  if (name === 'team'   && state.teams.length === 0) loadTeams();
}
```

---

## View Shell

Each view is a `<div class="view" id="view-{name}">`. Only the active one has `class="view active"` (CSS: `.view { display:none } .view.active { display:block }`). Views: `tasks`, `launch`, `search`, `team`, `admin`.

---

## My Tasks View

### Stat Cards

Four `<button type="button" class="stat-card …">` in a `grid-template-columns: repeat(4,1fr)` grid. Use `<button>`, not `<div tabindex="0">`.

```html
<button type="button" class="stat-card stat-card--overdue" data-filter="overdue"
  aria-pressed="false" onclick="setFilter('overdue')">
  <div class="stat-label" aria-hidden="true">Overdue</div>
  <div class="stat-count" id="statOverdue">—</div>
  <div class="stat-desc">Past due date</div>
</button>
```

| Card | `data-filter` | Stripe / count colour | Description |
|---|---|---|---|
| Overdue | `overdue` | `--ibm-red-60` | Past due date |
| At Risk | `atrisk` | `--ibm-orange-40` | Due within 24 hours |
| Active | `active` | `--ibm-blue-60` | Claimed by you |
| All Tasks | `all` | `--ibm-gray-60` / `--ibm-gray-80` | Assigned to you |

`setFilter()` toggles `active-filter` class and `aria-pressed` on all cards.

### Toolbar

```html
<div class="toolbar" role="toolbar" aria-label="Task filters">
  <div class="search-wrap">
    <!-- inline SVG magnifier -->
    <label for="searchInput" class="sr-only">Search tasks</label>
    <input class="search-input" id="searchInput" type="search"
      placeholder="Search tasks, processes…" oninput="handleSearch()" />
  </div>
  <label for="priorityFilter" class="sr-only">Priority filter</label>
  <select class="filter-select" id="priorityFilter" onchange="applyFilters()">
    <option value="">All Priorities</option>
    <option value="high">High</option>
    <option value="medium">Medium</option>
    <option value="low">Low</option>
  </select>
  <label for="statusFilter" class="sr-only">Status filter</label>
  <select class="filter-select" id="statusFilter" onchange="applyFilters()">
    <option value="">All Statuses</option>
    <option value="claimed">Claimed</option>
    <option value="ready">Ready</option>
    <option value="received">Received</option>
  </select>
  <button type="button" class="btn btn-ghost" onclick="clearAllFilters()">Clear filters</button>
  <button type="button" class="btn btn-primary" id="refreshBtn" onclick="triggerRefresh()">
    <span class="refresh-icon" aria-hidden="true">↻</span> Refresh
  </button>
  <span id="resultCount" role="status" aria-live="polite" aria-atomic="true"></span>
</div>
```

### Refresh / Stale Bar

```html
<div class="refresh-bar" id="refreshBar" aria-live="polite" aria-atomic="true">
  <span id="lastUpdatedLabel"></span>
  <span class="refresh-stale-msg" id="staleMsg" role="status">Data may be stale — click Refresh</span>
</div>
```

`staleMsg` is hidden by default; shown by adding class `stale` to `refreshBar` after `STALE_THRESHOLD` (90 s) without a successful load.

### Truncation Banner

```html
<div class="truncation-banner" id="truncationBanner" role="status" aria-live="polite">
  ⚠ <span id="truncationMsg"></span>
</div>
```

Shown (`banner.classList.add('visible')`) when `totalCount > returnedCount` (API returned fewer items than the server total).

### Task Table

Columns: **Task Name** | **Process** | **Priority** | **Due Date** | **Status** | **Actions**

Sortable columns use `<button type="button" class="sort-btn">` inside `<th class="sortable">`, not `onclick` on the `<th>`:

```html
<th class="sortable" id="th-priority" aria-sort="none" scope="col">
  <button type="button" class="sort-btn" onclick="sortBy('priority')">
    Priority<span class="sort-indicator" aria-hidden="true">↕</span>
  </button>
</th>
```

`<table>` has `aria-describedby="resultCount"`. `colspan="6"` for state rows (loading, error, empty).

### Mobile Card List

On `≤680px`, the table is hidden and replaced with a `<div id="mobileTaskList">` containing card components. Both share the same data slice and `goPage()` function.

### In-Table Action Buttons

Each row includes an Actions column with:
- **Open** — `openTaskFromBtn(this)` (always present)
- **Claim** — `claimTask(this)` (only when `state === 'ready'` or `'received'`)
- **Reassign** — `openReassignDialog(this)` (always present)
- **Priority select** — `updatePriority(this)` (inline `<select>` with values 10/20/30/40/50)
- **Release** — `releaseTask(this)` (only when task is claimed — releases claim back to pool)

---

## Priority Badge

`PRIORITY` field is **numeric** (`10`–`50`). **Lower number = higher priority** (BAW convention):

```js
function priorityLabel(val) {
  const n = Number(val);
  if (n <= 20) return 'high';    // red badge  (Critical=10, High=20)
  if (n <= 30) return 'medium';  // orange badge (Medium=30)
  return 'low';                  // green badge (Low=40, Very Low=50)
}
```

The inline priority select maps: `10=Critical`, `20=High`, `30=Medium`, `40=Low`, `50=Very Low`.

---

## Due Date Display

```js
const MS_HOUR = 3_600_000;
const MS_DAY  = 86_400_000;

function formatDue(due) {
  if (!due) return '—';
  const diff = due - Date.now();
  const days = Math.round(diff / MS_DAY);
  if (diff < 0) {
    const ago = Math.round(-diff / MS_DAY);
    return ago === 0 ? 'Today (overdue)' : `${ago}d overdue`;
  }
  if (diff < MS_HOUR) return 'Due < 1 hr';
  if (diff < MS_DAY)  return `Due in ${Math.round(diff / MS_HOUR)}h`;
  if (days === 0)     return 'Today';
  if (days === 1)     return 'Tomorrow';
  return `In ${days} days`;
}
```

Colour classes: `due-overdue` (red), `due-atrisk` (orange), `due-ok` (grey).

---

## Status Badge

Strip the `State_` prefix before displaying:

```js
function normState(task) {
  return (task.STATE || task.STATUS || '').toLowerCase().replace(/^state_/, '');
}
const stNorm  = normState(task);
const stClass = ['claimed','ready','received'].includes(stNorm)
              ? `status-${stNorm}` : 'status-other';
const stLabel = stNorm ? stNorm.charAt(0).toUpperCase() + stNorm.slice(1) : '—';
```

| Normalised value | Badge colour |
|---|---|
| `claimed` | Blue |
| `ready` | Green |
| `received` | Yellow |
| anything else | Grey |

---

## Pagination

- `PAGE_SIZE = 10`
- Smart ellipsis range: `[1 … cur-1  cur  cur+1 … last]`
- Prev `‹` / Next `›` disabled at boundaries
- `aria-current="page"` on active page button
- `"X–Y of N"` count label
- Shared `renderPaginationInto(bar, pages, total)` used for both desktop and mobile nav bars

---

## Task Modal

Opens when a task name link or Open button is clicked. Tracks the triggering element to restore focus on close.

```html
<div class="modal-backdrop" id="taskModal" role="dialog" aria-modal="true"
     aria-labelledby="modalTitle" onclick="handleBackdropClick(event)">
  <div class="modal">
    <span class="focus-sentinel" id="modalSentinelStart" tabindex="0"
      aria-hidden="true" onfocus="trapFocusToEnd()"></span>
    <div class="modal-header">
      <span class="modal-title" id="modalTitle">Task</span>
      <button type="button" class="modal-close" id="modalCloseBtn"
        aria-label="Close task" onclick="closeModal()">✕</button>
    </div>
    <iframe class="modal-iframe" id="taskIframe" src="about:blank" title="Task form"></iframe>
    <span class="focus-sentinel" id="modalSentinelEnd" tabindex="0"
      aria-hidden="true" onfocus="trapFocusToStart()"></span>
  </div>
</div>
```

Task URL:
```
/teamworks/process.lsw?zWorkflowState=1&zTaskId={TKIID}&zResetContext=true
```

`TKIID` must be validated as numeric (`/^\d+$/.test(taskId)`) before use.

Close via: ✕ button · `Escape` key · backdrop click.
On close: reset `taskIframe.src = 'about:blank'`, restore focus to `_modalTrigger`, call `triggerRefresh(true)` to silently refresh.

---

## Confirm Dialog (async)

```js
let _confirmResolve = null;
function confirm(body, title = 'Confirm') {
  return new Promise(resolve => {
    _confirmResolve = resolve;
    document.getElementById('confirmTitle').textContent = title;
    document.getElementById('confirmBody').textContent  = body;
    document.getElementById('confirmDialog').classList.add('open');
    document.getElementById('confirmOkBtn').focus();
  });
}
function resolveConfirm(result) {
  document.getElementById('confirmDialog').classList.remove('open');
  if (_confirmResolve) { _confirmResolve(result); _confirmResolve = null; }
}
```

Used by `releaseTask()`, `deleteSavedSearch()`, and `startProcess()`.

---

## BAW API Integration

### Fetch Options (mandatory)

Every API call must include `credentials: 'same-origin'` — BAW uses session cookies:

```js
const FETCH_OPTS = {
  method: 'GET',
  credentials: 'same-origin',
  headers: { 'Accept': 'application/json' }
};
```

For `PUT`/`POST` with a body, also add `'Content-Type': 'application/json'`.

### Current User

```
GET /rest/bpm/wle/v1/user/current?parts=all
```

`loadUser()` populates the header avatar/name and calls `renderProfileDropdown(data)`.

`renderProfileDropdown()` renders only fields actually present in the API response — never fabricates values. Documented fields: `fullName`, `displayName`, `userName`, `emailAddress`, `primaryGroup`, `isAdmin`, `membersOf[]`.

### Tasks (My Tasks view)

```
GET /rest/bpm/wle/v1/tasks?interaction=claimed_and_available&calcStats=true&size=500&offset=0
```

**Do not use `/rest/bpm/federated/v1/tasks`** as the primary call — it returns `404` on single-server deployments.

Handle all known response shapes:

```js
let raw = [];
if (Array.isArray(json))                  raw = json;
else if (Array.isArray(json.items))       raw = json.items;
else if (Array.isArray(json.data?.items)) raw = json.data.items;
else if (Array.isArray(json.data))        raw = json.data;
const totalCount = json.data?.totalCount || json.totalCount || raw.length;
```

Exclude terminal states using substring matching (handles both prefixed and bare values):

```js
const EXCLUDE_STATES = ['finished', 'terminated', 'completed', 'closed', 'failed'];
const fresh = raw.filter(t => {
  const st = (t.STATE || t.STATUS || '').toLowerCase();
  return !EXCLUDE_STATES.some(x => st.includes(x));
});
```

### Task Mutations

All mutations use `PUT /rest/bpm/wle/v1/task/{taskId}?{params}`. No CSRF token required — `credentials: 'same-origin'` session cookie is sufficient for WLE v1.

| Action | Params |
|---|---|
| Claim | `action=claim` |
| Cancel | `action=cancel` |
| Reassign to user | `action=assign&toUser={username}` |
| Reassign to self | `action=assign&toMe=true` |
| Reassign to previous | `action=assign&back=true` |
| Update priority | `action=update&priority={10\|20\|30\|40\|50}` |

### Process Launcher (Start Process view)

```
GET /rest/bpm/wle/v1/exposed
```

Response shape: `json.data.exposedItemsList || json.exposedItemsList`. Filter to `type === 'process'`.

**Critical — use `startURL` as the parameter source, not the raw response fields:**

| Field | Do not use directly | Reason |
|---|---|---|
| `itemID` | ❌ as `bpdId` | Causes HTTP 409 at runtime |
| `processAppID` | ❌ as `processAppId` | Causes HTTP 400 `CWTBG0012E: projectId invalid` |
| `snapshotID` | ❌ as `snapshotId` | Causes HTTP 400 `CWTBG0012E: snapshotId invalid` — omit entirely |
| `startURL` | ✅ parse from this | Contains the exact `bpdId` and `processAppId` BAW accepts |

Parse `bpdId` and `processAppId` from the `startURL` query string, then POST — omitting `snapshotId`:

```js
const u = new URL(item.startURL, 'https://x');
const bpdId        = u.searchParams.get('bpdId')        || u.searchParams.get('bpd_id');
const processAppId = u.searchParams.get('processAppId') || u.searchParams.get('appId');
// POST — no snapshotId
fetch(`/rest/bpm/wle/v1/process?action=start&bpdId=${encodeURIComponent(bpdId)}&processAppId=${encodeURIComponent(processAppId)}`,
  { method: 'POST', credentials: 'same-origin', headers: { 'Accept': 'application/json' } });
```

After a successful start, show a confirm dialog offering to open the first task (`json.data.tasks[0].tkiid`).

### Task Search (Task Search view)

Advanced search uses `PUT /rest/bpm/wle/v1/tasks` with a JSON body:

```js
function buildSearchPayload(conditions = []) {
  return { interaction: 'all_claimed_and_available', size: 100, offset: 0, calcStats: true, conditions };
}
```

Each condition: `{ field, operator, value }` — e.g. `{ field: 'TAD_DISPLAY_NAME', operator: 'LIKE', value: '%invoice%' }`.

**Saved searches:**

| Operation | Method | Endpoint |
|---|---|---|
| List | `GET` | `/rest/bpm/wle/v1/searches/tasks` |
| Run | `GET` | `/rest/bpm/wle/v1/searches/tasks/{name}` |
| Save | `POST` | `/rest/bpm/wle/v1/searches/tasks` (body: payload + `name`) |
| Rename | `PUT` | `/rest/bpm/wle/v1/searches/tasks/{oldName}` (body: payload + new `name`) |
| Delete | `DELETE` | `/rest/bpm/wle/v1/searches/tasks/{name}` |

**Search field metadata** (augments filter dropdowns with server-provided fields — optional, falls back gracefully):

```
GET /rest/bpm/wle/v1/searches/tasks/meta/fields
GET /rest/bpm/wle/v1/searches/tasks/meta/constraintFields
```

### Team View

```
GET /rest/bpm/wle/v1/managedGlobalTeams
```

Fallback if empty: `GET /rest/bpm/wle/v1/globalTeams`.

Per-team member count: `GET /rest/bpm/wle/v1/globalTeamUsers/{teamId}`.

Team workload dashboard (requires BAW 24.0.0.1+ with FDR enabled — may return `503`):

```
GET /rest/bpm/wle/v2/dashboards/teamsummary/{teamId}
```

Handle `503` gracefully: show "Team workload data is unavailable. Contact your BAW administrator."

---

## API Field Reference

The WLE tasks API returns **UPPERCASE** field names:

| Field | Type | Notes |
|---|---|---|
| `TKIID` | string | Task instance ID — validate as numeric before use |
| `TAD_DISPLAY_NAME` | string | Display name (preferred over `NAME`) |
| `NAME` | string | Fallback task name |
| `PT_NAME` | string | Process template name |
| `TAD_DESCRIPTION` | string | Task description (used in search) |
| `PRIORITY` | number | `10`–`50`; lower = higher priority |
| `DUE` | string | ISO 8601 date string |
| `STATE` | string | **Prefixed**: `"State_claimed"`, `"State_finished"`, etc. |
| `STATUS` | string | Fallback if `STATE` is absent |

---

## Application State

```js
const PAGE_SIZE        = 10;
const SEARCH_PAGE_SIZE = 20;
const POLL_INTERVAL    = 60_000;   // ms between background polls
const STALE_THRESHOLD  = 90_000;   // ms before data is considered stale

let state = {
  /* My Tasks */
  allTasks:          [],
  filteredTasks:     [],
  sortField:         'due',
  sortDir:           'asc',
  currentFilter:     'all',
  searchQuery:       '',
  priorityFilter:    '',
  statusFilter:      '',
  currentPage:       1,
  loading:           false,
  lastUpdatedAt:     null,
  taskFingerprint:   '',
  pollTimer:         null,
  staleTimer:        null,
  apiTotalCount:     0,

  /* Launch */
  allProcesses:      [],
  filteredProcesses: [],

  /* Search */
  savedSearches:     [],
  searchResults:     [],
  searchCurrentPage: 1,
  lastSearchPayload: null,

  /* Team */
  teams: [],
};
```

---

## Background Polling

```js
function startPolling() {
  stopPolling();
  state.pollTimer = setInterval(() => {
    if (document.visibilityState === 'hidden') return;
    triggerRefresh(true);  // silent — only re-renders if fingerprint changed
  }, POLL_INTERVAL);
}
```

`computeFingerprint(tasks)` — sorted join of `TKIID:STATE:DUE` strings. No re-render if fingerprint is unchanged.

`document.addEventListener('visibilitychange', …)` triggers a silent refresh when the tab becomes visible.

---

## Pull-to-Refresh (touch only)

IIFE guarded by `if (!('ontouchstart' in window)) return`. Touch handlers use `{ passive: true }`. The `ptr-indicator` is `aria-hidden="true"` and uses `role="presentation"`.

Threshold: `72px` pull triggers refresh. `PTR_MAX_DRAG: 96px`.

---

## Initialisation

```js
(async function init() {
  await loadUser();
  triggerRefresh(false);
  startPolling();
})();
```

---

## XSS Protection

Always escape before inserting into `innerHTML`:

```js
function escHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
```

---

## Responsive Breakpoints

```css
/* Sidebar */
@media (max-width: 768px) {
  .sidebar { transform: translateX(-100%); }
  .sidebar.open { transform: translateX(0); }
  .sidebar-toggle { display: flex; }
  .sidebar-backdrop { display: block; }
  .main-area { margin-left: 0; }
}

/* Stats grid */
@media (max-width: 900px) { .stats-row { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 600px) { .stats-row { grid-template-columns: 1fr 1fr; } }

/* Mobile card list (replaces table) */
@media (max-width: 680px) {
  .table-wrap     { display: none; }
  .mobile-task-list { display: block; }
  .toolbar { flex-direction: column; align-items: stretch; }
  .btn { min-height: var(--touch-target); width: 100%; }
}
@media (min-width: 681px) {
  .table-wrap     { display: block; }
  .mobile-task-list { display: none; }
}
```

---

## Accessibility

- Skip link: `<a class="skip-link" href="#main-content">Skip to main content</a>`
- SR live region: `<div id="srTableStatus" class="sr-table-status" aria-live="polite" aria-atomic="true"></div>`
- `prefers-reduced-motion`: `animation-duration: .01ms !important; transition-duration: .01ms !important`
- `:focus-visible` ring: `outline: 2px solid var(--ibm-blue-60); outline-offset: 2px`
- `:focus:not(:focus-visible) { outline: none; }`
- Sidebar toggle: `aria-expanded` updated on open/close
- Stat cards: `<button type="button">` with `aria-pressed` toggled by `setFilter()`
- Sort headers: `aria-sort="ascending|descending|none"` on `<th>`, sort trigger inside `<button class="sort-btn">`
- Result count: `role="status" aria-live="polite" aria-atomic="true"`
- Modal: `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, focus sentinels, focus restored to trigger on close
- Pagination: `aria-current="page"`, `aria-label` on prev/next buttons
- Mobile cards: `min-height: var(--touch-target)` on tap targets
- `announceSR(msg)` function for programmatic SR announcements via `srTableStatus`
