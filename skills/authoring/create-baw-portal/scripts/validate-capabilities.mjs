#!/usr/bin/env node
/**
 * validate-capabilities.mjs
 * Independent structural validator for catalog.json and intent-map.json.
 *
 * Usage:
 *   node scripts/validate-capabilities.mjs
 *   node scripts/validate-capabilities.mjs --catalog path/to/catalog.json --intent-map path/to/intent-map.json
 *
 * Options:
 *   --catalog    Path to catalog.json   (default: capabilities/catalog.json relative to this script)
 *   --intent-map Path to intent-map.json
 *   --skill-root Root against which intent.playbook paths resolve (default: skill root of this script)
 *   --verbose    Print all passing checks in addition to errors
 *
 * Exit codes:
 *   0  All checks passed
 *   1  One or more validation errors found
 *
 * SECURITY NOTE: Authoritative enum values are defined INSIDE this script.
 * They are never read from catalog.json's "enums" object. A catalog edit
 * cannot bypass validation by adding an unsupported value alongside a
 * matching enum entry.
 */

import { readFileSync, existsSync, statSync, realpathSync } from 'node:fs';
import { resolve, dirname, relative, isAbsolute } from 'node:path';
import { fileURLToPath } from 'node:url';

// ---------------------------------------------------------------------------
// Authoritative enum values — defined here, never derived from catalog.json
// ---------------------------------------------------------------------------
const VALID_EVIDENCE_LEVELS = new Set([
  'runtime-verified',
  'structural-assertion-verified',
  'documentation-verified',
  'prototype-derived',
  'inference',
  'unverified',
]);

const VALID_STATUSES = new Set([
  'available',
  'partial',
  'gated',
  'unverified',
]);

const VALID_API_FAMILIES = new Set([
  'wle-v1',
  'wle-v2',
  'pfs-v1',
  'pfs-v2',
  'teamworks-url',
]);

const VALID_KINDS = new Set([
  'operation-group',
  'composite',
]);

const VALID_DEPLOYMENT_VALUES = new Set(['NF', 'PFS']);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
const __dirname = dirname(fileURLToPath(import.meta.url));

let errors = 0;
let warnings = 0;
let verbose = false;

const args = process.argv.slice(2);
let catalogPath = resolve(__dirname, '../capabilities/catalog.json');
let intentMapPath = resolve(__dirname, '../capabilities/intent-map.json');
let skillRoot = resolve(__dirname, '..');

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--catalog' && args[i + 1]) catalogPath = resolve(args[++i]);
  else if (args[i] === '--intent-map' && args[i + 1]) intentMapPath = resolve(args[++i]);
  else if (args[i] === '--skill-root' && args[i + 1]) skillRoot = resolve(args[++i]);
  else if (args[i] === '--verbose') verbose = true;
}

function err(location, msg) {
  console.error(`  ERROR [${location}] ${msg}`);
  errors++;
}

function warn(location, msg) {
  console.warn(`  WARN  [${location}] ${msg}`);
  warnings++;
}

function ok(msg) {
  if (verbose) console.log(`  OK    ${msg}`);
}

function loadJson(path, label) {
  if (!existsSync(path)) {
    err('file-load', `${label} not found: ${path}`);
    return null;
  }
  try {
    return JSON.parse(readFileSync(path, 'utf8'));
  } catch (e) {
    err('file-load', `${label} JSON parse error: ${e.message}`);
    return null;
  }
}

// ---------------------------------------------------------------------------
// CATALOG VALIDATION
// ---------------------------------------------------------------------------
function validateCatalog(catalog) {
  console.log('\n── Catalog validation ──────────────────────────────────────');

  // Top-level schema
  if (!catalog.operations || !Array.isArray(catalog.operations)) {
    err('catalog.operations', 'Missing or non-array "operations"');
    return { opIds: new Set(), capIds: new Set(), conflictIds: new Set() };
  }
  if (!catalog.capabilities || !Array.isArray(catalog.capabilities)) {
    err('catalog.capabilities', 'Missing or non-array "capabilities"');
    return { opIds: new Set(), capIds: new Set(), conflictIds: new Set() };
  }
  if (!catalog.conflicts || !Array.isArray(catalog.conflicts)) {
    err('catalog.conflicts', 'Missing or non-array "conflicts"');
    return { opIds: new Set(), capIds: new Set(), conflictIds: new Set() };
  }

  // Count check
  console.log(`  operations: ${catalog.operations.length} (expected 72)`);
  console.log(`  capabilities: ${catalog.capabilities.length} (expected 49)`);
  console.log(`  conflicts: ${catalog.conflicts.length} (expected 6)`);
  if (catalog.operations.length !== 72)  err('catalog.operations.count', `Expected 72, got ${catalog.operations.length}`);
  if (catalog.capabilities.length !== 49) err('catalog.capabilities.count', `Expected 49, got ${catalog.capabilities.length}`);
  if (catalog.conflicts.length !== 6)    err('catalog.conflicts.count', `Expected 6, got ${catalog.conflicts.length}`);

  // --- Operations ---
  const opIds = new Set();
  for (const op of catalog.operations) {
    const loc = `operation[${op.id ?? '?'}]`;

    // Required fields
    for (const field of ['id', 'family', 'method', 'path', 'summary', 'evidence']) {
      if (!op[field]) err(loc, `Missing required field "${field}"`);
    }
    if (!op.id) continue;

    // Unique IDs
    if (opIds.has(op.id)) err(loc, `Duplicate operation id "${op.id}"`);
    opIds.add(op.id);

    // Enum values — validated against this script's authoritative sets
    if (op.evidence && !VALID_EVIDENCE_LEVELS.has(op.evidence)) {
      err(loc, `Invalid evidence level "${op.evidence}"`);
    }
    if (op.family && !VALID_API_FAMILIES.has(op.family)) {
      err(loc, `Invalid api family "${op.family}"`);
    }

    // deployment object
    if (op.deployment) {
      for (const key of ['nonFederated', 'federated', 'fdrRequired', 'pfsRequired']) {
        if (typeof op.deployment[key] !== 'boolean') {
          err(loc, `deployment.${key} must be boolean, got ${typeof op.deployment[key]}`);
        }
      }
    } else {
      err(loc, 'Missing "deployment" object');
    }

    // conflict cross-references
    const conflictIds = new Set(catalog.conflicts.map(c => c.id));
    for (const cid of (op.conflicts ?? [])) {
      if (!conflictIds.has(cid)) err(loc, `References unknown conflict "${cid}"`);
    }
  }
  ok(`${opIds.size} operation IDs unique`);

  // --- Conflicts ---
  const conflictIds = new Set();
  for (const c of catalog.conflicts) {
    const loc = `conflict[${c.id ?? '?'}]`;
    for (const field of ['id', 'topic', 'description']) {
      if (!c[field]) err(loc, `Missing required field "${field}"`);
    }
    if (!c.id) continue;
    if (conflictIds.has(c.id)) err(loc, `Duplicate conflict id "${c.id}"`);
    conflictIds.add(c.id);
  }
  ok(`${conflictIds.size} conflict IDs unique`);

  // --- Capabilities ---
  const capIds = new Set();
  for (const cap of catalog.capabilities) {
    const loc = `capability[${cap.id ?? '?'}]`;

    for (const field of ['id', 'name', 'description', 'kind', 'domain',
                          'requiredOperations', 'optionalOperations', 'status']) {
      if (cap[field] === undefined || cap[field] === null) {
        err(loc, `Missing required field "${field}"`);
      }
    }
    if (!cap.id) continue;

    if (capIds.has(cap.id)) err(loc, `Duplicate capability id "${cap.id}"`);
    capIds.add(cap.id);

    // Enum validation — authoritative sets
    if (cap.kind && !VALID_KINDS.has(cap.kind)) {
      err(loc, `Invalid kind "${cap.kind}"`);
    }
    if (cap.status && !VALID_STATUSES.has(cap.status)) {
      err(loc, `Invalid status "${cap.status}"`);
    }
    if (cap.evidence?.level && !VALID_EVIDENCE_LEVELS.has(cap.evidence.level)) {
      err(loc, `Invalid evidence.level "${cap.evidence.level}"`);
    }

    // Operation cross-references
    for (const opId of (cap.requiredOperations ?? [])) {
      if (!opIds.has(opId)) err(loc, `requiredOperations references unknown operation "${opId}"`);
    }
    for (const opId of (cap.optionalOperations ?? [])) {
      if (!opIds.has(opId)) err(loc, `optionalOperations references unknown operation "${opId}"`);
    }

    // Conflict cross-references
    for (const cid of (cap.conflicts ?? [])) {
      if (!conflictIds.has(cid)) err(loc, `conflicts references unknown conflict id "${cid}"`);
    }

    // Deployment boolean check
    if (cap.deployment) {
      for (const key of ['nonFederated', 'federated', 'fdrRequired', 'pfsRequired']) {
        if (typeof cap.deployment[key] !== 'boolean') {
          err(loc, `deployment.${key} must be boolean`);
        }
      }
    }

    // FDR-gated capability must have fdrRequired=true in deployment
    if (cap.status === 'gated' && cap.deployment && cap.deployment.fdrRequired !== true) {
      // Only flag if capability's deployment.nonFederated=true (NF gate expected)
      // Some gates may be pfsRequired — skip those
      if (cap.deployment.nonFederated && !cap.deployment.fdrRequired) {
        warn(loc, `status=gated but deployment.fdrRequired=false — verify gate condition`);
      }
    }

    // related capabilities are strings (light check — not cross-ref because cyclic is fine)
    for (const r of (cap.related ?? [])) {
      if (typeof r !== 'string') err(loc, `related entry must be a string`);
    }
  }
  ok(`${capIds.size} capability IDs unique`);

  return { opIds, capIds, conflictIds };
}

// ---------------------------------------------------------------------------
// INTENT-MAP VALIDATION
// ---------------------------------------------------------------------------
function validateIntentMap(intentMap, opIds, capIds, conflictIds) {
  console.log('\n── Intent-map validation ───────────────────────────────────');

  if (!intentMap.intents || !Array.isArray(intentMap.intents)) {
    err('intent-map.intents', 'Missing or non-array "intents"');
    return;
  }
  if (!intentMap.selectionRules?.rules || !Array.isArray(intentMap.selectionRules.rules)) {
    err('intent-map.selectionRules', 'Missing or non-array "selectionRules.rules"');
    return;
  }
  if (!intentMap.acceptanceFixtures?.fixtures || !Array.isArray(intentMap.acceptanceFixtures.fixtures)) {
    err('intent-map.acceptanceFixtures', 'Missing or non-array "acceptanceFixtures.fixtures"');
    return;
  }
  if (!intentMap.discoveryAmbiguities || !Array.isArray(intentMap.discoveryAmbiguities)) {
    err('intent-map.discoveryAmbiguities', 'Missing or non-array "discoveryAmbiguities"');
    return;
  }

  const intentCount   = intentMap.intents.length;
  const ruleCount     = intentMap.selectionRules.rules.length;
  const fixtureCount  = intentMap.acceptanceFixtures.fixtures.length;
  const ambiguityCount = intentMap.discoveryAmbiguities.length;

  console.log(`  intents: ${intentCount} (expected 14 after addendum additions)`);
  console.log(`  selectionRules: ${ruleCount} (expected 10)`);
  console.log(`  fixtures: ${fixtureCount} (expected 13 after FIX-13 addition)`);
  console.log(`  discoveryAmbiguities: ${ambiguityCount} (expected 7)`);

  if (ruleCount !== 10) err('intent-map.selectionRules', `Expected 10 rules, got ${ruleCount}`);
  if (fixtureCount !== 13) err('intent-map.fixtures.count', `Expected 13 fixtures after FIX-13, got ${fixtureCount}`);
  if (ambiguityCount !== 7) err('intent-map.ambiguities.count', `Expected 7 ambiguities, got ${ambiguityCount}`);

  // --- Intents ---
  const intentIds = new Set();
  for (const intent of intentMap.intents) {
    const loc = `intent[${intent.id ?? '?'}]`;

    // Required fields
    for (const field of ['id', 'label', 'aliases', 'capabilities', 'deployment', 'prerequisites', 'related']) {
      if (intent[field] === undefined) err(loc, `Missing required field "${field}"`);
    }
    if (!intent.id) continue;

    if (intentIds.has(intent.id)) err(loc, `Duplicate intent id "${intent.id}"`);
    intentIds.add(intent.id);

    // aliases must be non-empty array of strings
    if (!Array.isArray(intent.aliases) || intent.aliases.length === 0) {
      err(loc, 'aliases must be a non-empty array');
    }

    // deployment must be array of valid values
    if (Array.isArray(intent.deployment)) {
      for (const d of intent.deployment) {
        if (!VALID_DEPLOYMENT_VALUES.has(d)) {
          err(loc, `Invalid deployment value "${d}" — must be NF or PFS`);
        }
      }
    }

    // capabilities: validate cap IDs found anywhere in the structure
    const capsInIntent = extractCapabilityIds(intent.capabilities ?? {});
    for (const capId of capsInIntent) {
      if (!capIds.has(capId)) {
        err(loc, `capabilities references unknown capability "${capId}"`);
      }
    }

    // related: validate intent ID references
    for (const relId of (intent.related ?? [])) {
      // Validated post-loop; collect here
      if (typeof relId !== 'string') err(loc, `related entry must be a string`);
    }

    // fdrGate structure: probeCapability must be an operation ID (no embedded prose)
    if (intent.fdrGate) {
      const gate = intent.fdrGate;
      if (typeof gate.required !== 'boolean') {
        err(loc, 'fdrGate.required must be boolean');
      }
      if (!Array.isArray(gate.deployments) || gate.deployments.length === 0) {
        err(loc, 'fdrGate.deployments must be a non-empty array');
      }
      if (!gate.probeCapability) {
        err(loc, 'fdrGate.probeCapability is required');
      } else {
        // probeCapability must be a clean operation ID — no spaces
        if (/\s/.test(gate.probeCapability)) {
          err(loc, `fdrGate.probeCapability "${gate.probeCapability}" contains whitespace — must be a clean operation ID, not prose. Put human notes in probeNote.`);
        }
        if (!opIds.has(gate.probeCapability)) {
          err(loc, `fdrGate.probeCapability "${gate.probeCapability}" is not a known operation ID`);
        }
      }
      // secondaryProbe if present must also be a clean operation ID
      if (gate.secondaryProbe) {
        if (/\s/.test(gate.secondaryProbe)) {
          err(loc, `fdrGate.secondaryProbe "${gate.secondaryProbe}" contains whitespace — must be a clean operation ID. Put human notes in secondaryProbeNote.`);
        }
        if (!opIds.has(gate.secondaryProbe)) {
          err(loc, `fdrGate.secondaryProbe "${gate.secondaryProbe}" is not a known operation ID`);
        }
      }
    }

    // conflict cross-references on intent
    for (const cid of (intent.conflicts ?? [])) {
      if (!conflictIds.has(cid)) err(loc, `conflicts references unknown conflict id "${cid}"`);
    }

    // Deployment gate check: FDR-only intents must list NF in deployment
    if (intent.fdrGate?.required && !intent.deployment.includes('NF')) {
      err(loc, 'fdrGate.required=true but "NF" not in deployment array');
    }

    // Semantic check — PFS mutation intents must reference PFS lifecycle capability, not NF-only
    if (intent.deployment.includes('PFS')) {
      const pfsCapIds = extractCapabilityIds(
        typeof intent.capabilities?.PFS === 'object' ? intent.capabilities.PFS : {}
      );
      // Check that PFS task-action intents don't reference NF task lifecycle directly
      if (intent.id === 'INT-TASK-ACTIONS' && pfsCapIds.includes('CAP-TASK-LIFECYCLE-NF')) {
        err(loc, 'INT-TASK-ACTIONS PFS selection references CAP-TASK-LIFECYCLE-NF — should be CAP-TASK-LIFECYCLE-PFS for PFS deployments');
      }
    }
  }

  // Validate related intent cross-references (post-loop, all IDs known)
  for (const intent of intentMap.intents) {
    const loc = `intent[${intent.id}]`;
    for (const relId of (intent.related ?? [])) {
      if (!intentIds.has(relId)) {
        err(loc, `related references unknown intent "${relId}"`);
      }
    }
    // Disambiguations may reference intent IDs by "use INT-xxx" pattern
    for (const d of (intent.disambiguations ?? [])) {
      const matches = d.match(/INT-[A-Z0-9-]+/g) ?? [];
      for (const intentRef of matches) {
        if (!intentIds.has(intentRef)) {
          err(loc, `disambiguations text references unknown intent "${intentRef}"`);
        }
      }
    }
  }
  ok(`${intentIds.size} intent IDs unique and cross-references valid`);

  // --- Selection rules count ---
  ok(`${ruleCount} selection rules present`);

  // --- Fixtures ---
  const fixtureIds = new Set();
  for (const fix of intentMap.acceptanceFixtures.fixtures) {
    const loc = `fixture[${fix.id ?? '?'}]`;

    for (const field of ['id', 'label', 'userRequest', 'resolvedContext', 'expectedCapabilities']) {
      if (fix[field] === undefined) err(loc, `Missing required field "${field}"`);
    }
    if (!fix.id) continue;

    if (fixtureIds.has(fix.id)) err(loc, `Duplicate fixture id "${fix.id}"`);
    fixtureIds.add(fix.id);

    // resolvedContext.deployment must be NF, PFS, or "unknown"
    const dep = fix.resolvedContext?.deployment;
    if (dep === undefined || dep === null) {
      err(loc, 'resolvedContext.deployment is required');
    } else if (dep !== 'unknown' && !VALID_DEPLOYMENT_VALUES.has(dep)) {
      err(loc, `resolvedContext.deployment "${dep}" must be NF, PFS, or "unknown"`);
    }

    // expectedCapabilities must reference known cap IDs
    for (const capId of (fix.expectedCapabilities ?? [])) {
      if (!capIds.has(capId)) {
        err(loc, `expectedCapabilities references unknown capability "${capId}"`);
      }
    }
    // notExpected must also reference known cap IDs
    for (const capId of (fix.notExpected ?? [])) {
      if (!capIds.has(capId)) {
        err(loc, `notExpected references unknown capability "${capId}"`);
      }
    }
    // optionalExtensions
    for (const capId of (fix.optionalExtensions ?? [])) {
      if (!capIds.has(capId)) {
        err(loc, `optionalExtensions references unknown capability "${capId}"`);
      }
    }

    // Semantic: a NF fixture must not expect PFS capabilities
    if (dep === 'NF') {
      for (const capId of (fix.expectedCapabilities ?? [])) {
        if (capId.includes('-PFS')) {
          err(loc, `NF fixture expects PFS capability "${capId}" — deployment mismatch`);
        }
      }
    }
    // Semantic: a PFS fixture must not expect NF-exclusive capabilities
    if (dep === 'PFS') {
      for (const capId of (fix.expectedCapabilities ?? [])) {
        const cap = null; // resolved below from capIds map if needed
        // Pattern-based check: capabilities ending in -NF that are known NF-only
        // CAP-TASK-LIFECYCLE-PFS is the correct PFS choice; CAP-TASK-LIFECYCLE-NF is wrong for PFS
        if (capId === 'CAP-TASK-LIFECYCLE-NF') {
          err(loc, `PFS fixture expects NF-only capability "CAP-TASK-LIFECYCLE-NF" — should use CAP-TASK-LIFECYCLE-PFS`);
        }
      }
    }

    // FDR-gated fixture: if fdrGate:true, deployment must be NF
    if (fix.fdrGate === true && dep !== 'NF') {
      err(loc, 'fdrGate=true but deployment is not NF — FDR gate is NF-only');
    }

    // conflictsApply must reference known conflict IDs
    for (const cid of (fix.conflictsApply ?? [])) {
      if (!conflictIds.has(cid)) {
        err(loc, `conflictsApply references unknown conflict "${cid}"`);
      }
    }
  }
  ok(`${fixtureIds.size} fixture IDs unique and cross-references valid`);

  // --- Ambiguities ---
  const ambIds = new Set();
  for (const amb of intentMap.discoveryAmbiguities) {
    const loc = `ambiguity[${amb.id ?? '?'}]`;
    for (const field of ['id', 'description', 'affectedIntents']) {
      if (!amb[field]) err(loc, `Missing required field "${field}"`);
    }
    if (!amb.id) continue;
    if (ambIds.has(amb.id)) err(loc, `Duplicate ambiguity id "${amb.id}"`);
    ambIds.add(amb.id);
    // affectedIntents cross-reference
    for (const intentId of (amb.affectedIntents ?? [])) {
      if (!intentIds.has(intentId)) {
        err(loc, `affectedIntents references unknown intent "${intentId}"`);
      }
    }
  }
  ok(`${ambIds.size} ambiguity IDs unique and cross-references valid`);
}

// ---------------------------------------------------------------------------
// SEMANTIC CHECKS
// ---------------------------------------------------------------------------
function runSemanticChecks(catalog, intentMap) {
  console.log('\n── Semantic checks ─────────────────────────────────────────');

  // Build capability->deployment map from catalog
  const capDeployment = new Map();
  for (const cap of catalog.capabilities) {
    if (cap.id) capDeployment.set(cap.id, cap.deployment);
  }

  // S1: PFS intent with fdrGate.required=true is a contract defect
  //     (FDR is NF-only — PFS team workload uses its own endpoints, no FDR gate needed)
  for (const intent of intentMap.intents) {
    if (intent.fdrGate?.required && Array.isArray(intent.deployment)) {
      if (intent.deployment.includes('PFS') && !intent.deployment.includes('NF')) {
        err(`intent[${intent.id}]`, 'fdrGate.required=true on a PFS-only intent — FDR gate is NF-only');
      }
    }
  }

  // S2: For FDR-gated capabilities, their deployment.fdrRequired must be true
  for (const intent of (intentMap.intents ?? [])) {
    if (intent.fdrGate?.required) {
      const allCaps = extractCapabilityIds(intent.capabilities ?? {});
      for (const capId of allCaps) {
        const dep = capDeployment.get(capId);
        if (dep && dep.nonFederated && !dep.fdrRequired) {
          // warn rather than error: composite NF workload capabilities may have FDR via the gate
          warn(`intent[${intent.id}]`, `fdrGate set but capability "${capId}" has deployment.fdrRequired=false`);
        }
      }
    }
  }

  // S3: Saved-search execution — strategy operations must not be cumulative
  //     CAP-SAVED-SEARCH-EXEC-NF requiredOperations = [NF-SAVED-GET, NF-ADHOC-SEARCH] (Strategy A)
  //     NF-SAVED-EXEC-PARAM is optional (Strategy B) — validator checks they're NOT both required
  for (const cap of catalog.capabilities) {
    if (cap.id === 'CAP-SAVED-SEARCH-EXEC-NF' || cap.id === 'CAP-SAVED-SEARCH-EXEC-PFS') {
      const reqOps = new Set(cap.requiredOperations ?? []);
      const optOps = new Set(cap.optionalOperations ?? []);
      const execParam = cap.id === 'CAP-SAVED-SEARCH-EXEC-NF' ? 'NF-SAVED-EXEC-PARAM' : 'PFS-SAVED-EXEC-PARAM';
      if (reqOps.has(execParam)) {
        err(`capability[${cap.id}]`, `${execParam} must be in optionalOperations (Strategy B), not requiredOperations — strategies are alternatives, not cumulative`);
      }
      ok(`${cap.id}: saved-search strategy separation correct`);
    }
  }

  // S4: CAP-TASK-LIFECYCLE-PFS must include NF-TASK-CLAIM etc. (source-routed) and NOT PFS mutation IDs
  for (const cap of catalog.capabilities) {
    if (cap.id === 'CAP-TASK-LIFECYCLE-PFS') {
      const reqOps = new Set(cap.requiredOperations ?? []);
      // Must include NF-TASK-CLAIM (source routing)
      if (!reqOps.has('NF-TASK-CLAIM')) {
        err('capability[CAP-TASK-LIFECYCLE-PFS]', 'Missing NF-TASK-CLAIM in requiredOperations — PFS task mutations must route to source system via NF task operations');
      }
      // Must NOT include a "PFS-TASK-CLAIM" operation (which doesn't exist)
      for (const opId of reqOps) {
        if (opId.startsWith('PFS-TASK-') && !['PFS-TASK-LIST', 'PFS-TASK-LAUNCH'].includes(opId)) {
          err('capability[CAP-TASK-LIFECYCLE-PFS]', `Invented PFS mutation operation "${opId}" — PFS has no task mutation endpoints; route via NF operations`);
        }
      }
      ok('CAP-TASK-LIFECYCLE-PFS: source-routed NF operations present, no invented PFS mutation operations');
    }
  }

  // S5: INT-PROCESS-INSTANCE-SEARCH PFS side must not map to instance-detail capability
  for (const intent of intentMap.intents) {
    if (intent.id === 'INT-PROCESS-INSTANCE-SEARCH') {
      const pfsCaps = extractCapabilityIds(
        intent.capabilities?.PFS ?? (typeof intent.capabilities?.PFS === 'object' ? intent.capabilities.PFS : {})
      );
      // CAP-PROCESS-INSTANCE-DETAIL-NF is NF-only; using it for PFS instance detail is incorrect
      if (pfsCaps.includes('CAP-PROCESS-INSTANCE-DETAIL-NF')) {
        err('intent[INT-PROCESS-INSTANCE-SEARCH]',
          'PFS capabilities include CAP-PROCESS-INSTANCE-DETAIL-NF — instance detail is NF-only; PFS instance search (CAP-INSTANCE-SEARCH-PFS) is the correct PFS choice. Source-routed PFS instance detail is not modeled.');
      }
      ok('INT-PROCESS-INSTANCE-SEARCH: PFS side does not mix in NF-only instance-detail capability');
    }
  }

  console.log('  Semantic checks complete.');
}

// ---------------------------------------------------------------------------
// Utility: extract all CAP-* IDs from a capabilities value.
// Handles: array of strings, object with NF/PFS keys, nested objects.
// ---------------------------------------------------------------------------
function extractCapabilityIds(obj) {
  const ids = [];
  if (!obj) return ids;
  // Direct array of cap IDs
  if (Array.isArray(obj)) {
    for (const item of obj) {
      if (typeof item === 'string' && item.startsWith('CAP-')) ids.push(item);
      else if (typeof item === 'object' && item !== null) ids.push(...extractCapabilityIds(item));
    }
    return ids;
  }
  if (typeof obj !== 'object') return ids;
  for (const [key, val] of Object.entries(obj)) {
    if (key.startsWith('_')) continue;
    if (Array.isArray(val)) {
      for (const item of val) {
        if (typeof item === 'string' && item.startsWith('CAP-')) ids.push(item);
        else if (typeof item === 'object' && item !== null) ids.push(...extractCapabilityIds(item));
      }
    } else if (typeof val === 'object' && val !== null) {
      ids.push(...extractCapabilityIds(val));
    }
  }
  return ids;
}

// ---------------------------------------------------------------------------
// Local doc-ref existence checks
// ---------------------------------------------------------------------------
function validateDocRefs(catalog, baseDir) {
  console.log('\n── Doc-ref existence checks ────────────────────────────────');
  let checked = 0;
  let missing = 0;
  const checkedPaths = new Set();

  function checkRef(ref, loc) {
    if (!ref || ref.startsWith('http')) return; // skip URLs
    const full = resolve(baseDir, ref);
    if (checkedPaths.has(full)) return;
    checkedPaths.add(full);
    checked++;
    if (!existsSync(full)) {
      err(loc, `docRef file not found: ${ref} (resolved to ${full})`);
      missing++;
    }
  }

  for (const op of (catalog.operations ?? [])) {
    for (const ref of (op.docRefs ?? [])) checkRef(ref, `operation[${op.id}].docRefs`);
  }
  for (const cap of (catalog.capabilities ?? [])) {
    for (const ref of (cap.docRefs ?? [])) checkRef(ref, `capability[${cap.id}].docRefs`);
  }

  console.log(`  Checked ${checkedPaths.size} unique local doc-refs — ${missing} missing`);
}

// ---------------------------------------------------------------------------
// intent.playbook path checks
// Only intents that explicitly declare "playbook" are checked; the field is optional.
// A declared playbook must be a nonempty skill-root-relative path, contain no ".."
// segment, resolve (after symlink resolution) inside the skill root, and be a regular file.
// ---------------------------------------------------------------------------
function isInside(root, target) {
  const rel = relative(root, target);
  return rel !== '' && !rel.startsWith('..') && !isAbsolute(rel);
}

function validatePlaybookRefs(intentMap, root) {
  console.log('\n── Intent playbook path checks ─────────────────────────────');
  let declared = 0;
  for (const intent of (intentMap.intents ?? [])) {
    if (!Object.prototype.hasOwnProperty.call(intent, 'playbook')) continue;
    declared++;
    const loc = `intent[${intent.id ?? '?'}].playbook`;
    const p = intent.playbook;
    if (typeof p !== 'string' || p.trim() === '') {
      err(loc, 'playbook must be a nonempty string path');
      continue;
    }
    if (isAbsolute(p) || /^[A-Za-z]:/.test(p) || p.startsWith('\\')) {
      err(loc, `playbook must be relative to the skill root, got absolute path "${p}"`);
      continue;
    }
    if (/^[a-z][a-z0-9+.-]*:\/\//i.test(p)) {
      err(loc, `playbook must be a local path, got URL "${p}"`);
      continue;
    }
    if (p.split(/[\\/]+/).includes('..')) {
      err(loc, `playbook path must not contain ".." segments: "${p}"`);
      continue;
    }
    const full = resolve(root, p);
    if (!isInside(root, full)) {
      err(loc, `playbook resolves outside the skill root: "${p}"`);
      continue;
    }
    if (!existsSync(full)) {
      err(loc, `playbook file not found: "${p}" (resolved to ${full})`);
      continue;
    }
    let real;
    try { real = realpathSync(full); } catch (e) { err(loc, `playbook cannot be resolved: ${e.message}`); continue; }
    if (!isInside(realpathSync(root), real)) {
      err(loc, `playbook resolves outside the skill root via symlink: "${p}"`);
      continue;
    }
    if (!statSync(real).isFile()) {
      err(loc, `playbook is not a regular file: "${p}"`);
      continue;
    }
    ok(`${loc} → ${p}`);
  }
  console.log(`  Checked ${declared} declared playbook path(s) against ${root}`);
}

// ---------------------------------------------------------------------------
// CROSS-SOURCE CONTRACT CONSISTENCY & DRIFT CHECKS (P0)
// ---------------------------------------------------------------------------
function validateCrossSourceConsistency(catalog, intentMap, skillRoot, opIds, capIds) {
  console.log('\n── Cross-source contract consistency (P0) ───────────────────');

  const catalogPaths = new Set(catalog.operations.map(op => op.path));
  const catalogPathPatterns = catalog.operations.map(op => {
    // Convert path with {param} to regex pattern
    const patStr = '^' + op.path.replace(/\{[^}]+\}/g, '[^/?]+') + '(\\?.*)?$';
    return new RegExp(patStr);
  });

  // Explicit allowlist for documented unsupported, non-catalog, or infrastructure paths
  const ALLOWED_UNREGISTERED_PATHS = [
    '/rest/bpm/wle/v1/searches/tasks/meta/priority', // Documented as unsupported on NF
    '/rest/bpm/wle/v1/searches/meta/',              // Documented legacy 404 path
    '/rest/bpm/wle/v1/teams',                       // Documented nonexistent plural
    '/rest/bpm/wle/v1/launchableEntities',          // Documented PFS-only path
    '/rest/bpm/wle/v2/search',                      // Family base / prefix
    '/rest/bpm/wle/v2/dashboards',                  // Family base / prefix
    '/rest/bpm/federated/v1/',                      // Family base / prefix
    '/rest/bpm/federated/v2/',                      // Family base / prefix
    '/rest/bpm/federated/v1/globalTeams',           // Declared in baw-pfs-v1 OpenAPI spec
    '/bpm/system/login',                            // CSRF/auth token helper
    '/teamworks/process.lsw',                       // Task form URL
    '/teamworks/fauxRedirect.lsw',                  // Task form redirect URL
  ];

  function isPathAllowed(pathStr) {
    const cleanPath = pathStr.split('?')[0].replace(/[),.;]+$/, '');
    for (const pat of catalogPathPatterns) {
      if (pat.test(cleanPath)) return true;
    }
    for (const allowed of ALLOWED_UNREGISTERED_PATHS) {
      if (cleanPath.startsWith(allowed) || cleanPath === allowed) return true;
    }
    return false;
  }

  // 1. baw-rest.md alignment check
  const bawRestPath = resolve(skillRoot, 'references/baw-rest.md');
  if (existsSync(bawRestPath)) {
    const content = readFileSync(bawRestPath, 'utf8');
    const endpointMatches = content.match(/^### `([A-Z]+)\s+([^`]+)`/gm) || [];
    let bawRestCount = 0;
    for (const match of endpointMatches) {
      const m = match.match(/^### `([A-Z]+)\s+([^`]+)`/);
      if (m) {
        bawRestCount++;
        const p = m[2].trim();
        if (!isPathAllowed(p)) {
          err('baw-rest.md', `Declared endpoint "${p}" does not match any registered catalog operation or allowed path`);
        }
      }
    }
    ok(`baw-rest.md: ${bawRestCount} endpoints validated against catalog operations`);
  }

  // 2. Playbooks and feature catalog reference integrity
  const refFiles = [
    'references/feature-catalog.md',
    'references/personas-and-capabilities.md',
    'references/playbooks/task-lifecycle.md',
    'references/playbooks/saved-search-management.md',
    'references/playbooks/federated-portal-integration.md',
  ];

  for (const rel of refFiles) {
    const full = resolve(skillRoot, rel);
    if (!existsSync(full)) continue;
    const txt = readFileSync(full, 'utf8');

    // Check CAP-* references
    const capMatches = txt.match(/\bCAP-[A-Z0-9-]+\b/g) || [];
    for (const cid of capMatches) {
      if (!capIds.has(cid)) {
        err(rel, `References unknown capability ID "${cid}"`);
      }
    }

    // Check NF-* and PFS-* operation references (including wildcard prefixes like PFS-SAVED-*)
    const allOpRefs = txt.match(/\b(?:NF|PFS)-[A-Z0-9-]+(?:\*)?/g) || [];
    for (const raw of allOpRefs) {
      if (raw.endsWith('*')) {
        const prefix = raw.replace(/-?\*$/, '');
        const hasMatch = Array.from(opIds).some(op => op.startsWith(prefix + '-') || op === prefix);
        if (!hasMatch) {
          err(rel, `References unknown operation prefix "${raw}"`);
        }
      } else {
        const oid = raw.replace(/-+$/, '');
        if (!opIds.has(oid)) {
          err(rel, `References unknown operation ID "${oid}"`);
        }
      }
    }
    ok(`${rel}: all CAP-* and operation references valid`);
  }

  // 3. Evidence classification consistency
  const LEVEL_RANK = {
    'unverified': 0,
    'prototype-derived': 0,
    'inference': 0,
    'documentation-verified': 1,
    'structural-assertion-verified': 2,
    'runtime-verified': 3,
  };

  const opEvidenceMap = new Map(catalog.operations.map(op => [op.id, op.evidence]));

  for (const cap of catalog.capabilities) {
    if (!cap.evidence?.level) continue;
    const capLevel = cap.evidence.level;
    const capRank = LEVEL_RANK[capLevel] ?? 0;

    // Check required operations
    const reqOps = cap.requiredOperations || [];
    if (reqOps.length > 0) {
      let minOpRank = 3;
      for (const opId of reqOps) {
        const opEv = opEvidenceMap.get(opId) || 'unverified';
        const rank = LEVEL_RANK[opEv] ?? 0;
        if (rank < minOpRank) minOpRank = rank;
      }
      // Capability evidence should not exceed minimum required operation rank without explicit note
      if (capRank > minOpRank && !cap.evidence.evidenceNote && !cap.evidenceBasis && !cap.inferenceBasis) {
        err(`capability[${cap.id}]`, `Evidence level "${capLevel}" exceeds weakest required operation rank without evidenceNote or inferenceBasis`);
      }
    }
  }
  ok('Capability evidence level hierarchy and derivations valid');

  // 4. Prohibited retired/contradictory claims scan across all active skill files
  const activeFiles = [
    'SKILL.md',
    'references/hosting-and-generation.md',
    'references/non-federated-api-guide.md',
    'references/federated-api-guide.md',
    'references/personas-and-capabilities.md',
    'references/feature-catalog.md',
    'references/playbooks/task-lifecycle.md',
    'references/playbooks/saved-search-management.md',
    'references/playbooks/federated-portal-integration.md',
    'references/source-of-truth.md',
    'docs/create-baw-portal-doc.md',
  ];

  for (const rel of activeFiles) {
    const full = resolve(skillRoot, rel);
    if (!existsSync(full)) continue;
    const txt = readFileSync(full, 'utf8');

    // Rule A: Prohibit accepting data.search as valid definition
    if (rel !== 'references/playbooks/saved-search-management.md' && rel !== 'references/non-federated-api-guide.md') {
      if (/(?:def|criteria|definition)\s*=\s*(?:json|data|defJson)\??\.\s*data\??\.\s*search\b/.test(txt)) {
        err(rel, 'Contains retired data.search extraction pattern');
      }
    }

    // Rule B: Prohibit claiming reverse proxy alone solves iframe/CSP
    if (/proxy(?:\s+rewrites|\s+origin)?\s+(?:makes|allows)\s+(?:the\s+)?(?:task\s+form|iframe)\s+(?:same-origin\s*✅|embeddable)/i.test(txt)) {
      err(rel, 'Contains unsupported claim that reverse proxy alone makes iframe/task form same-origin');
    }

    // Rule C: Prohibit claiming itemID as bpdId or fallback
    if (/(?:pass(?:ing)?\s+itemID\s+(?:directly\s+)?as\s+bpdId|use\s+itemID\s+as\s+bpdId|itemID\s+as\s+fallback\s+for\s+bpdId)/i.test(txt)) {
      if (!/do not|never|causes? HTTP 409|invalid/i.test(txt)) {
        err(rel, 'Contains prohibited advice to use itemID as bpdId');
      }
    }

    // Rule D: Prohibit 10=Critical or 30=Medium in task priority mapping
    if (/10\s*=\s*Critical|20\s*=\s*High.*30\s*=\s*Medium/i.test(txt)) {
      err(rel, 'Contains obsolete priority mapping (10=Critical / 30=Medium)');
    }

    // Rule E: Prohibit endorsing unsupported NF meta/priority endpoint
    for (const line of txt.split('\n')) {
      if (/searches\/tasks\/meta\/priority/.test(line)) {
        if (!/do not|no verified|not supported|PFS-only|warns against/i.test(line)) {
          err(rel, `Endorses unsupported NF meta/priority endpoint: "${line.trim()}"`);
        }
      }
    }

    // Rule F: Prohibit calcStats placed on PUT search
    if (/PUT.*\/tasks.*calcStats.*URL query parameter/i.test(txt) || /body:.*calcStats/i.test(txt)) {
      err(rel, 'Contains calcStats in PUT /tasks request body or query parameters');
    }

    // Rules G and H are line-level; a line that states a prohibition is exempt.
    const prohibition = /\b(?:do not|don't|never|must not|not a|not set|refuse[sd]?|reject(?:s|ed)?|prohibit(?:s|ed)?|forbid(?:s|den)?|without)\b/i;
    for (const line of txt.split('\n')) {
      if (prohibition.test(line)) continue;

      // Rule G: Prohibit identifier substitution for missing launch parameters
      if (/\b(?:itemID|processAppID|processAppAcronym|snapshotID)\b/.test(line) &&
          /\b(?:fall(?:s|ing)?[ -]?back|fallback|substitut\w*|stand[- ]in)\b/i.test(line)) {
        err(rel, `Advises identifier substitution for a missing launch parameter: "${line.trim()}"`);
      }

      // Rule H: Prohibit insecure dev-server / TLS settings
      if (/\ballowedHosts\s*:\s*true\b/.test(line) ||
          /\bsecure\s*:\s*false\b/.test(line) ||
          /\brejectUnauthorized\s*:\s*false\b/.test(line) ||
          /NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*['"]?0/.test(line) ||
          /\bcors\s*:\s*true\b/.test(line)) {
        err(rel, `Insecure dev-server/TLS setting: "${line.trim()}"`);
      }
    }
  }
  ok('Prohibited retired/contradictory claims scan PASSED across all active files');
}

// ---------------------------------------------------------------------------
// MAIN
// ---------------------------------------------------------------------------
console.log('╔════════════════════════════════════════════════════════════╗');
console.log('║  validate-capabilities.mjs — Task 1D.1 independent audit  ║');
console.log('╚════════════════════════════════════════════════════════════╝');
console.log(`  catalog.json  : ${catalogPath}`);
console.log(`  intent-map.json: ${intentMapPath}`);

const catalog   = loadJson(catalogPath, 'catalog.json');
const intentMap = loadJson(intentMapPath, 'intent-map.json');

if (!catalog || !intentMap) {
  console.error('\nFATAL: Could not load one or both JSON files. Aborting.');
  process.exit(1);
}

const { opIds, capIds, conflictIds } = validateCatalog(catalog);
validateIntentMap(intentMap, opIds, capIds, conflictIds);
runSemanticChecks(catalog, intentMap);

// Determine base dir for docRefs (catalog lives in capabilities/)
const catalogBaseDir = resolve(dirname(catalogPath), '..');
validateDocRefs(catalog, catalogBaseDir);
validatePlaybookRefs(intentMap, skillRoot);
validateCrossSourceConsistency(catalog, intentMap, skillRoot, opIds, capIds);

// ---------------------------------------------------------------------------
// Summary
// ---------------------------------------------------------------------------
console.log('\n════════════════════════════════════════════════════════════');
if (errors === 0 && warnings === 0) {
  console.log('  ✓ All checks PASSED — no errors, no warnings.');
} else if (errors === 0) {
  console.log(`  ✓ All checks PASSED with ${warnings} warning(s).`);
} else {
  console.log(`  ✗ Validation FAILED: ${errors} error(s), ${warnings} warning(s).`);
}
console.log('════════════════════════════════════════════════════════════\n');

process.exit(errors > 0 ? 1 : 0);
