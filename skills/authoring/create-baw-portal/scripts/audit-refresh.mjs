/**
 * audit-refresh.mjs
 * Static analysis for the refresh pipeline (Pass 3).
 *
 * Checks:
 *   R01 – POLL_INTERVAL constant declared
 *   R02 – STALE_THRESHOLD constant declared
 *   R03 – state.loading in-flight guard present
 *   R04 – triggerRefresh() is the single public entry point
 *   R05 – _doLoad() function present
 *   R06 – silent flag accepted by triggerRefresh (default parameter)
 *   R07 – silent flag used inside _doLoad
 *   R08 – computeFingerprint() function present
 *   R09 – fingerprint compare (newFingerprint !== state.taskFingerprint)
 *   R10 – state.taskFingerprint assigned after fetch
 *   R11 – state.lastUpdatedAt assigned on success
 *   R12 – updateLastUpdatedBar() called on success
 *   R13 – scheduleStaleWarning() called on success
 *   R14 – startPolling() function present
 *   R15 – stopPolling() function present
 *   R16 – resetPollTimer() function present
 *   R17 – setInterval used inside startPolling
 *   R18 – clearInterval used inside stopPolling
 *   R19 – visibilitychange listener present
 *   R20 – silent triggerRefresh on visibility visible
 *   R21 – document.visibilityState check in poll interval handler
 *   R22 – #refreshBar element present in HTML
 *   R23 – #lastUpdatedLabel element present in HTML
 *   R24 – #staleMsg element present in HTML
 *   R25 – refresh-bar.stale class triggers stale message (CSS)
 *   R26 – setRefreshBtnSpinning() function present
 *   R27 – btn.disabled toggled in setRefreshBtnSpinning
 *   R28 – refreshing CSS class toggled in setRefreshBtnSpinning
 *   R29 – spin-refresh keyframe animation defined
 *   R30 – closeModal calls triggerRefresh(true) after close
 *   R31 – loadTasks() stub delegates to triggerRefresh
 *   R32 – init calls triggerRefresh(false) (first load)
 *   R33 – init calls startPolling()
 *   R34 – renderTableLoading called on non-silent _doLoad
 *   R35 – silent poll failure calls markStale()
 *   R36 – toast called on poll failure
 *   R37 – aria-live on #refreshBar
 *   R38 – prefers-reduced-motion suppresses spin-refresh animation
 *   R39 – state.staleTimer cleared in scheduleStaleWarning
 *   R40 – markStale() adds .stale class to refreshBar
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

/* ── helpers ── */
const has  = (pattern) => (typeof pattern === 'string' ? src.includes(pattern) : pattern.test(src));
const pass = (id, desc, ok) => ({ id, desc, ok });

/* ── checks ── */
const checks = [
  // Constants
  pass('R01', 'POLL_INTERVAL constant declared',
    has('const POLL_INTERVAL')),
  pass('R02', 'STALE_THRESHOLD constant declared',
    has('const STALE_THRESHOLD')),

  // In-flight guard
  pass('R03', 'state.loading in-flight guard present',
    has('state.loading') && has('if (state.loading) return')),

  // Entry point
  pass('R04', 'triggerRefresh() declared as function',
    has('function triggerRefresh(')),
  pass('R05', '_doLoad() function declared',
    has('async function _doLoad(')),
  pass('R06', 'triggerRefresh has silent default parameter',
    has('function triggerRefresh(silent = false)')),
  pass('R07', 'silent flag used inside _doLoad',
    has(/if \(!silent\)/)),

  // Change detection
  pass('R08', 'computeFingerprint() function declared',
    has('function computeFingerprint(')),
  pass('R09', 'fingerprint inequality comparison present',
    has("newFingerprint !== state.taskFingerprint")),
  pass('R10', 'state.taskFingerprint assigned after fetch',
    has('state.taskFingerprint = newFingerprint')),

  // Post-success bookkeeping
  pass('R11', 'state.lastUpdatedAt assigned on success',
    has('state.lastUpdatedAt = new Date()')),
  pass('R12', 'updateLastUpdatedBar() called on success',
    has('updateLastUpdatedBar()')),
  pass('R13', 'scheduleStaleWarning() called on success',
    has('scheduleStaleWarning()')),

  // Polling lifecycle
  pass('R14', 'startPolling() function declared',
    has('function startPolling(')),
  pass('R15', 'stopPolling() function declared',
    has('function stopPolling(')),
  pass('R16', 'resetPollTimer() function declared',
    has('function resetPollTimer(')),
  pass('R17', 'setInterval used inside startPolling',
    has(/startPolling[\s\S]{0,200}setInterval/)),
  pass('R18', 'clearInterval used inside stopPolling',
    has(/stopPolling[\s\S]{0,200}clearInterval/)),

  // Visibility handling
  pass('R19', "visibilitychange event listener present",
    has("visibilitychange")),
  pass('R20', 'silent refresh fired on tab visible',
    has(/visibilityState.*===.*['"](visible)['"]/)),
  pass('R21', 'hidden tab guard in poll interval handler',
    has(/visibilityState.*===.*['"](hidden)['"]/)),

  // DOM elements
  pass('R22', '#refreshBar element present',
    has('id="refreshBar"')),
  pass('R23', '#lastUpdatedLabel element present',
    has('id="lastUpdatedLabel"')),
  pass('R24', '#staleMsg element present',
    has('id="staleMsg"')),

  // CSS stale
  pass('R25', 'refresh-bar.stale CSS rule present',
    has('.refresh-bar.stale')),

  // Refresh button spinner
  pass('R26', 'setRefreshBtnSpinning() function declared',
    has('function setRefreshBtnSpinning(')),
  pass('R27', 'btn.disabled toggled in setRefreshBtnSpinning',
    has(/setRefreshBtnSpinning[\s\S]{0,300}btn\.disabled/)),
  pass('R28', '.refreshing class toggled in setRefreshBtnSpinning',
    has(/setRefreshBtnSpinning[\s\S]{0,300}refreshing/)),
  pass('R29', 'spin-refresh @keyframes defined',
    has('@keyframes spin-refresh')),

  // Modal close triggers silent refresh
  // closeModal body is ~684 chars; use 750 window; trailing \) allows 0-10 chars after 'true'
  pass('R30', 'closeModal calls triggerRefresh(true)',
    has(/closeModal[\s\S]{0,750}triggerRefresh\([\s\S]{0,20}true[\s\S]{0,10}\)/)),

  // Compat stub
  pass('R31', 'loadTasks() stub delegates to triggerRefresh',
    has(/function loadTasks\s*\(\s*\)[\s\S]{0,60}triggerRefresh/)),

  // Init
  pass('R32', 'init calls triggerRefresh(false)',
    has(/triggerRefresh\(\s*(\/\*\s*silent\s*\*\/\s*)?false\s*\)/)),
  pass('R33', 'init calls startPolling()',
    has('startPolling()')),

  // Silent vs full load paths
  pass('R34', 'renderTableLoading called inside _doLoad',
    has(/if \(!silent\)[\s\S]{0,60}renderTableLoading/)),
  pass('R35', 'silent poll failure calls markStale()',
    has(/silent[\s\S]{0,200}markStale\(\)/)),
  pass('R36', 'toast called on poll failure',
    has(/toast\(.*[Ff]ailed/)),

  // Accessibility on refresh bar
  pass('R37', '#refreshBar has aria-live',
    has(/"refreshBar"[\s\S]{0,80}aria-live/)),

  // Reduced motion suppresses spinner animation
  // The keyframe name and the media query are both present; check independently
  pass('R38', 'prefers-reduced-motion suppresses spin-refresh',
    has('@keyframes spin-refresh') && has(/prefers-reduced-motion[\s\S]{0,300}refreshing[\s\S]{0,60}animation\s*:\s*none/)),

  // Stale timer lifecycle
  pass('R39', 'scheduleStaleWarning clears staleTimer',
    has(/scheduleStaleWarning[\s\S]{0,120}clearTimeout.*staleTimer/)),
  pass('R40', 'markStale adds .stale class to refreshBar',
    has(/markStale[\s\S]{0,120}classList\.add\([\s\S]{0,20}stale/)),
];

/* ── report ── */
const failed  = checks.filter(c => !c.ok);
const passed  = checks.filter(c =>  c.ok);
const total   = checks.length;

console.log(`\n╔═══════════════════════════════════════════════════════════╗`);
console.log(`║          REFRESH PIPELINE AUDIT — static analysis         ║`);
console.log(`╚═══════════════════════════════════════════════════════════╝\n`);

checks.forEach(c => {
  const icon = c.ok ? '✅' : '❌';
  console.log(`  ${icon}  ${c.id}  ${c.desc}`);
});

console.log(`\n─────────────────────────────────────────────────────────────`);
console.log(`  Passed : ${passed.length} / ${total}`);
console.log(`  Failed : ${failed.length}`);
if (failed.length) {
  console.log(`\n  Failing checks:`);
  failed.forEach(c => console.log(`    • ${c.id}: ${c.desc}`));
}
console.log(`─────────────────────────────────────────────────────────────\n`);

process.exit(failed.length > 0 ? 1 : 0);
