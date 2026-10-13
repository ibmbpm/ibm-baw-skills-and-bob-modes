# Diff output format

This file defines the exact structure for the comparison report produced in Step 5 of `compare-baw-versions`.

---

## Report structure

Always follow this template — in order. Omit any section with zero changes.

```
# BAW Version Comparison: {App Name} ({Acronym})
**Version A:** {snapshot name} ({snapshot acronym})  
**Version B:** {snapshot name} ({snapshot acronym})  
**Compared on:** {date/time}

---

## ⚠️ Conflict Hints  _(only if present)_
These artifacts were modified in both versions. Review each carefully before reconciling in Process Designer.

| Artifact Type | Artifact Name | Change in A | Change in B |
|---|---|---|---|
| Process | Loan Approval | Step "Credit Check" removed | Step "Credit Check" renamed to "Auto Credit Check" |
| Business Object | LoanApplication | Field `creditScore` type: Integer | Field `creditScore` type: Decimal |

---

## Summary

| Category | Added | Removed | Modified | Conflict Hints |
|---|---|---|---|---|
| Processes | 0 | 0 | 2 | 1 |
| Services | 1 | 0 | 0 | 0 |
| Business Objects | 0 | 0 | 1 | 1 |
| Variables | 2 | 1 | 0 | 0 |
| Scripts | 0 | 0 | 1 | 0 |
| Configuration | 0 | 0 | 0 | 0 |
**Total changes: N**

---

## Processes

### ✏️ Modified: Loan Approval
- **Step added:** `Auto Credit Check` (after gateway "Approval Needed?")
- **Step removed:** `Manual Review` (was after gateway "Approval Needed?" → No branch)
- **Gateway condition changed:** "Approval Needed?" → Yes branch condition: `creditScore < 600` → `creditScore < 700`
- ⚠️ *Conflict hint — see above*

---

## Services

### ➕ Added: CreditScoreService
- New REST integration service
- Endpoint: `GET /api/v2/credit-score/{applicantId}`
- Output mapped to: `LoanApplication.creditScore`

---

## Business Objects

### ✏️ Modified: LoanApplication
- **Field type changed:** `creditScore` — `Integer` → `Decimal`
- ⚠️ *Conflict hint — see above*

---

## Variables

### ➕ Added (process: Loan Approval)
- `autoApprovalEnabled` — Boolean, private

### ➖ Removed (process: Loan Approval)
- `legacyApprovalFlag` — Boolean, private

---

## Scripts

### ✏️ Modified: Compute Risk Score (step in Loan Approval)
```diff
- var riskScore = creditScore / 850;
+ var riskScore = Math.min(creditScore / 850, 1.0);
+ if (riskScore < 0.3) { tw.local.highRisk = true; }
```

---

> ⚠️ The changes above are informational only — no modifications have been made to either version. To apply changes, open the target version in BAW Process Designer and make the edits manually.
```

---

## Output files

Two files are always produced — never optional, never on request:

| File | When | Contents |
|---|---|---|
| `<acronym>-<versionA>-vs-<versionB>-diff.md` | End of Step 5 | Full diff report |
| `<acronym>-<versionA>-vs-<versionB>-reconciliation.md` | End of Step 6 (if run) | Reconciliation checklist |

Use the snapshot **acronyms** (not full names) in the filename — they are short and safe for filenames. Example: `HSS-v10-vs-v11-diff.md`.

---

## Formatting rules

**Change icons:**
- ➕ Added (exists in B, not A)
- ➖ Removed (exists in A, not B)
- ✏️ Modified (exists in both, content differs)
- ⚠️ Conflict hint (modified in both — needs manual attention)

**Conflict hints section:** Always render it first, immediately after the header block, if any conflict hints exist. Make it impossible to miss — it is the most important part of the output for a developer about to reconcile manually.

**Summary table:** Always render it, even if most cells are 0. It gives the developer a quick triage view before they read the details.

**Script diffs:** Show only the changed lines in unified diff format (`-` old, `+` new). Do not dump the entire script. If a script is completely replaced (no shared lines), show the first 5 lines of each with a note "full replacement — {A lines} → {B lines}".

**Empty categories:** Omit entire sections (heading and all) when a category has zero changes. Do not write "No changes" entries — their absence is the signal.

**Artifact names:** Use the human-readable display name from the TWX (the `name` attribute on the element), not the internal ID or filename.

**Length:** For large diffs (more than ~20 changed artifacts), offer to break the report into sections:
> *"There are N changes across M artifact types. I can show you the full report at once, or break it down by category — which would you prefer?"*

**Tone:** Use plain, technical, neutral language. Do not recommend which version is "better". Do not comment on code quality. Report facts only.

---

## Reconciliation checklist format

Produced at the end of Step 6 (interactive conflict resolution). Always use this exact structure:

```
# Reconciliation Checklist: {App Name} — {Version A} → {Version B}

## ✅ Decisions made ({N} of N conflicts resolved)

| # | Artifact | Decision |
|---|---|---|
| 1 | Gateway "Approval Needed?" — condition | Keep Version B: `creditScore < 700` |
| 2 | BO LoanApplication — field `creditScore` type | Blend: use Decimal with max precision 2 |

## 🔲 One-sided changes to apply (safe — no decision needed)

These exist on one side only. Apply them directly in Process Designer:

- ➕ **Add** service `CreditScoreService` (exists in Version B only)
- ➖ **Remove** variable `legacyApprovalFlag` (exists in Version A only)
- ➕ **Add** variable `autoApprovalEnabled` — Boolean, private (exists in Version B only)

## ⏭️ Skipped conflicts ({N} still need a decision)

| # | Artifact | Version A | Version B |
|---|---|---|---|
| 3 | Script "Compute Risk Score" | Original logic | Extended with highRisk flag |

---
> No changes have been made to either version. Apply all items above manually in BAW Process Designer.
```

**Checklist rules:**
- List decisions in the order they were made during Step 6
- For "Blend" decisions, write out the user's described outcome verbatim — not a summary
- One-sided changes come from the diff produced in Step 4/5 — include all of them, not just the ones discussed
- If zero conflicts were skipped, omit the "Skipped" section entirely
- If the user skipped all conflicts (or said no to Step 6), the checklist still includes the one-sided changes section — it's always useful
