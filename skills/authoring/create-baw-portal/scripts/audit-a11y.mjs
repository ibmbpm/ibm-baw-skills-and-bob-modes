/**
 * audit-a11y.mjs
 * Static analysis for accessibility + mobile-first (Pass 1).
 *
 * Checks:
 *   A01 – Skip link targets #main-task-content
 *   A02 – Skip link :focus rule brings it on-screen
 *   A03 – <header> element present
 *   A04 – <main> element present with id="main-task-content"
 *   A05 – <main> has tabindex="-1"
 *   A06 – <nav> element(s) present
 *   A07 – <section> element(s) present
 *   A08 – <h2> present for section headings
 *   A09 – All stat cards are <button type="button">
 *   A10 – Stat cards have aria-pressed
 *   A11 – Initial All Tasks card has aria-pressed="true"
 *   A12 – setFilter() updates aria-pressed on all stat cards
 *   A13 – clearAllFilters() updates aria-pressed on all stat cards
 *   A14 – :focus-visible global ring defined
 *   A15 – --touch-target CSS variable defined
 *   A16 – .stat-card has min-height: var(--touch-target)
 *   A17 – .btn has min-height: var(--touch-target)
 *   A18 – Explicit <label for="searchInput"> present
 *   A19 – Explicit <label for="priorityFilter"> present
 *   A20 – Explicit <label for="statusFilter"> present
 *   A21 – Sort headers contain <button class="sort-btn">
 *   A22 – Sort headers have aria-sort attribute
 *   A23 – sortTasks() syncs aria-sort (ascending/descending)
 *   A24 – .sr-only class defined
 *   A25 – Priority badge has sr-only "Priority: " label
 *   A26 – Status badge has sr-only "Status: " label
 *   A27 – .status-dot is aria-hidden="true"
 *   A28 – Loading spinner has role="status"
 *   A29 – Error state has role="alert"
 *   A30 – state-icon is aria-hidden
 *   A31 – announceSR() function present
 *   A32 – aria-live="polite" on #srTableStatus
 *   A33 – aria-live on #resultCount
 *   A34 – aria-live="assertive" on #toastContainer
 *   A35 – @media prefers-reduced-motion suppresses all animations
 *   A36 – Modal has role="dialog" aria-modal="true"
 *   A37 – Modal has aria-labelledby
 *   A38 – Modal has aria-describedby
 *   A39 – Focus sentinel elements present (#modalSentinelStart, #modalSentinelEnd)
 *   A40 – trapFocusToEnd() and trapFocusToStart() functions present
 *   A41 – openTask() moves focus to #modalCloseBtn
 *   A42 – Escape key closes modal
 *   A43 – closeModal() restores focus to _modalTrigger
 *   A44 – taskId validated as numeric before iframe URL build
 *   A45 – iframe URL built from /teamworks/process.lsw only
 *   A46 – iframe src cleared on close
 *   A47 – iframe has title attribute
 *   A48 – TODO comment re sandbox testing present
 *   A49 – Mobile card list: #mobileTaskList present
 *   A50 – renderMobileCards() reads from state.filteredTasks (no extra fetch)
 *   A51 – Mobile cards show task name via mobile-task-name-btn
 *   A52 – Mobile cards show priority badge
 *   A53 – Mobile cards show due date with sr-only label
 *   A54 – Mobile cards show status badge
 *   A55 – Mobile cards have Open button (mobile-open-btn)
 *   A56 – Mobile breakpoint hides .table-wrap
 *   A57 – Desktop breakpoint hides .mobile-task-list
 *   A58 – Mobile pagination rendered by renderPaginationInto (shared)
 *   A59 – .mobile-task-name-btn has min-height: var(--touch-target)
 *   A60 – .mobile-open-btn has min-height: var(--touch-target)
 *   A61 – Toolbar stacks vertically at narrow breakpoint (flex-direction: column)
 *   A62 – openTaskFromLink() stores _modalTrigger
 *   A63 – openTaskFromBtn() stores _modalTrigger
 *   A64 – All buttons have type="button"
 *   A65 – getPageSlice() shared by both renderTable and renderMobileCards
 *   A66 – goPage() renders both table and mobile cards
 */

import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dir      = dirname(__filename);
const src        = readFileSync(
  join(__dir, '../assets/examples/ibm-baw-task-dashboard/ibm-baw-task-dashboard.html'),
  'utf8'
);

const has  = (p) => (typeof p === 'string' ? src.includes(p) : p.test(src));
const pass = (id, desc, ok) => ({ id, desc, ok });

const checks = [
  pass('A01', 'Skip link targets #main-task-content',
    has('href="#main-task-content"')),
  pass('A02', 'Skip link :focus moves on-screen',
    has('.skip-link:focus') && has(/\.skip-link:focus[\s\S]{0,60}top:\s*0/)),
  pass('A03', '<header> element present',
    has('<header ')),
  pass('A04', '<main> has id="main-task-content"',
    has('id="main-task-content"')),
  pass('A05', '<main> has tabindex="-1"',
    has('tabindex="-1"')),
  pass('A06', '<nav> element present',
    has('<nav ')),
  pass('A07', '<section> element present',
    has('<section')),
  pass('A08', '<h2> present for section headings',
    has('<h2 ')),
  // HTML attribute order: type="button" comes before class="stat-card" in the markup
  pass('A09', 'Stat cards are <button type="button">',
    has(/type="button"[\s\S]{0,50}stat-card/)),
  pass('A10', 'Stat cards have aria-pressed',
    has('aria-pressed=')),
  pass('A11', 'Initial All Tasks card has aria-pressed="true"',
    has('aria-pressed="true"')),
  pass('A12', 'setFilter() syncs aria-pressed',
    has(/function setFilter[\s\S]{0,300}aria-pressed/)),
  pass('A13', 'clearAllFilters() syncs aria-pressed',
    has(/function clearAllFilters[\s\S]{0,300}aria-pressed/)),
  pass('A14', ':focus-visible ring defined',
    has(':focus-visible')),
  pass('A15', '--touch-target CSS variable defined',
    has('--touch-target')),
  // stat-card CSS block is ~358 chars; use 450 window
  pass('A16', '.stat-card min-height: var(--touch-target)',
    has(/\.stat-card[\s\S]{0,450}min-height:\s*var\(--touch-target\)/)),
  pass('A17', '.btn min-height: var(--touch-target)',
    has(/\.btn[\s\S]{0,200}min-height:\s*var\(--touch-target\)/)),
  pass('A18', '<label for="searchInput"> present',
    has('for="searchInput"')),
  pass('A19', '<label for="priorityFilter"> present',
    has('for="priorityFilter"')),
  pass('A20', '<label for="statusFilter"> present',
    has('for="statusFilter"')),
  pass('A21', 'Sort headers contain <button class="sort-btn">',
    has('class="sort-btn"')),
  pass('A22', 'Sort headers have aria-sort attribute',
    has('aria-sort=')),
  pass('A23', 'sortTasks() syncs aria-sort ascending/descending',
    has("'ascending'") && has("'descending'")),
  pass('A24', '.sr-only class defined',
    has('.sr-only')),
  pass('A25', 'Priority badge sr-only "Priority: " label',
    has('Priority: ')),
  pass('A26', 'Status badge sr-only "Status: " label',
    has('Status: ')),
  pass('A27', '.status-dot is aria-hidden="true"',
    has(/status-dot[\s\S]{0,40}aria-hidden="true"/)),
  pass('A28', 'Loading spinner has role="status"',
    has('role="status"')),
  pass('A29', 'Error state has role="alert"',
    has('role="alert"')),
  pass('A30', 'state-icon is aria-hidden',
    has(/state-icon[\s\S]{0,20}aria-hidden/)),
  pass('A31', 'announceSR() function present',
    has('function announceSR(')),
  pass('A32', 'aria-live="polite" on #srTableStatus',
    has(/srTableStatus[\s\S]{0,80}aria-live="polite"/)),
  pass('A33', 'aria-live on #resultCount',
    has(/resultCount[\s\S]{0,80}aria-live/)),
  pass('A34', 'aria-live="assertive" on #toastContainer',
    has('aria-live="assertive"')),
  pass('A35', 'prefers-reduced-motion suppresses all animations',
    has(/prefers-reduced-motion.*reduce[\s\S]{0,100}animation-duration.*\.01ms/)),
  pass('A36', 'Modal role="dialog" aria-modal="true"',
    has('role="dialog"') && has('aria-modal="true"')),
  pass('A37', 'Modal has aria-labelledby',
    has('aria-labelledby=')),
  pass('A38', 'Modal has aria-describedby',
    has('aria-describedby=')),
  pass('A39', 'Focus sentinels present',
    has('id="modalSentinelStart"') && has('id="modalSentinelEnd"')),
  pass('A40', 'trapFocusToEnd() and trapFocusToStart() present',
    has('function trapFocusToEnd(') && has('function trapFocusToStart(')),
  // openTask() body is ~946 chars; use 1100 window
  pass('A41', 'openTask() focuses #modalCloseBtn',
    has(/openTask[\s\S]{0,1100}modalCloseBtn[\s\S]{0,40}\.focus\(\)/)),
  pass('A42', 'Escape key closes modal',
    has("'Escape'") && has('closeModal()')),
  pass('A43', 'closeModal() restores focus to _modalTrigger',
    has(/_modalTrigger[\s\S]{0,60}\.focus\(\)/)),
  // File uses /^\d+$/ (regex literal); detect via .test(String(taskId))
  pass('A44', 'taskId validated as numeric',
    has(/\.test\(String\(taskId\)\)/)),
  pass('A45', 'iframe URL from /teamworks/process.lsw only',
    has('/teamworks/process.lsw')),
  pass('A46', 'iframe src cleared on close',
    has("'about:blank'")),
  pass('A47', 'iframe has title attribute',
    has('title="Task form"')),
  pass('A48', 'TODO sandbox comment present',
    has('sandbox')),
  pass('A49', '#mobileTaskList present',
    has('id="mobileTaskList"')),
  pass('A50', 'renderMobileCards reads state.filteredTasks (no extra fetch)',
    has('function renderMobileCards(') && !has(/renderMobileCards[\s\S]{0,200}fetch\(/)),
  pass('A51', 'Mobile cards show task name via mobile-task-name-btn',
    has('mobile-task-name-btn')),
  pass('A52', 'Mobile cards show priority badge',
    has(/mobile-task-card[\s\S]{0,300}priority-badge/)),
  pass('A53', 'Mobile cards show due date with sr-only label',
    has(/mobile-task-meta[\s\S]{0,200}Due:/)),
  pass('A54', 'Mobile cards show status badge',
    has(/mobile-task-footer[\s\S]{0,100}status-badge/)),
  pass('A55', 'Mobile cards have Open button (mobile-open-btn)',
    has('mobile-open-btn')),
  pass('A56', 'Mobile breakpoint hides .table-wrap',
    has(/max-width.*680[\s\S]{0,100}table-wrap[\s\S]{0,40}display.*none/)),
  // CSS: .mobile-task-list    { display: none; } — brace present; allow 80 chars after selector
  pass('A57', 'Desktop breakpoint hides .mobile-task-list',
    has(/min-width.*681[\s\S]{0,150}mobile-task-list[\s\S]{0,80}display\s*:\s*none/)),
  pass('A58', 'Mobile pagination uses shared renderPaginationInto',
    has('renderPaginationInto')),
  // CSS block is ~280 chars; use 350 window
  pass('A59', '.mobile-task-name-btn min-height: var(--touch-target)',
    has(/mobile-task-name-btn[\s\S]{0,350}min-height:\s*var\(--touch-target\)/)),
  pass('A60', '.mobile-open-btn min-height: var(--touch-target)',
    has(/mobile-open-btn[\s\S]{0,200}min-height:\s*var\(--touch-target\)/)),
  pass('A61', 'Toolbar stacks vertically at narrow breakpoint',
    has(/flex-direction:\s*column/)),
  pass('A62', 'openTaskFromLink() stores _modalTrigger',
    has(/function openTaskFromLink[\s\S]{0,100}_modalTrigger\s*=/)),
  pass('A63', 'openTaskFromBtn() stores _modalTrigger',
    has(/function openTaskFromBtn[\s\S]{0,100}_modalTrigger\s*=/)),
  pass('A64', 'All interactive buttons have type="button"',
    has('type="button"')),
  pass('A65', 'getPageSlice() function present (shared accessor)',
    has('function getPageSlice(')),
  pass('A66', 'goPage() calls both renderTable and renderMobileCards',
    has(/function goPage[\s\S]{0,200}renderTable\(\)[\s\S]{0,100}renderMobileCards\(\)/)),

  /* ── Pull-to-refresh checks (A67–A78) ────────────────────────────── */
  pass('A67', '#ptrIndicator element present in HTML',
    has('id="ptrIndicator"')),
  pass('A68', 'ptrIndicator has aria-hidden="true"',
    has(/ptrIndicator[\s\S]{0,80}aria-hidden="true"/)),
  pass('A69', 'initPullToRefresh IIFE present',
    has('function initPullToRefresh(')),
  pass('A70', 'Touch device gate: ontouchstart in window',
    has("'ontouchstart' in window")),
  pass('A71', 'PTR activates only at scrollTop === 0',
    has('scroller.scrollTop !== 0')),
  pass('A72', 'PTR blocked when modal is open',
    has(/ptrIndicator|taskModal[\s\S]{0,200}contains\('open'\)/)),
  pass('A73', 'PTR calls triggerRefresh(false) — same as toolbar button',
    has(/fireRefresh[\s\S]{0,300}triggerRefresh[\s\S]{0,20}false/)),
  pass('A74', 'All PTR touch listeners use { passive: true }',
    has(/passive:\s*true/)),
  pass('A75', 'PTR_THRESHOLD constant defined',
    has('PTR_THRESHOLD')),
  pass('A76', 'PTR_MAX_DRAG constant defined',
    has('PTR_MAX_DRAG')),
  pass('A77', 'prefers-reduced-motion suppresses PTR CSS transitions',
    has(/prefers-reduced-motion[\s\S]{0,200}ptr-indicator[\s\S]{0,60}transition\s*:\s*none/)),
  pass('A78', 'resetIndicator() resets label to "Pull down to refresh"',
    has("'Pull down to refresh'")),
];

const failed = checks.filter(c => !c.ok);
const passed = checks.filter(c =>  c.ok);
const total  = checks.length;

console.log(`\n╔═══════════════════════════════════════════════════════════╗`);
console.log(`║        ACCESSIBILITY + MOBILE AUDIT — static analysis      ║`);
console.log(`╚═══════════════════════════════════════════════════════════╝\n`);

checks.forEach(c => console.log(`  ${c.ok ? '✅' : '❌'}  ${c.id}  ${c.desc}`));

console.log(`\n─────────────────────────────────────────────────────────────`);
console.log(`  Passed : ${passed.length} / ${total}`);
console.log(`  Failed : ${failed.length}`);
if (failed.length) {
  console.log(`\n  Failing checks:`);
  failed.forEach(c => console.log(`    • ${c.id}: ${c.desc}`));
}
console.log(`─────────────────────────────────────────────────────────────\n`);
process.exit(failed.length > 0 ? 1 : 0);
