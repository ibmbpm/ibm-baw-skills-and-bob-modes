# Diff output format

This file defines the exact structure for the comparison report that `compare-baw-versions` produces in Step 5.

---

## Report structure

Follow this template in order. Omit any section that has zero changes.

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
| User Interface | 1 | 0 | 2 | 0 |
| Business Objects | 0 | 0 | 1 | 1 |
| Variables | 2 | 1 | 0 | 0 |
| Scripts | 0 | 0 | 1 | 0 |
| Configuration | 0 | 0 | 0 | 0 |
| Other changes | 0 | 0 | 0 | 0 |
**Total changes: N**

**Coverage:** {N} files changed between the two versions. {N} reviewed and accounted for in this report ({X} with functional changes, {Y} with no functional change, {Z} not fully reviewed).

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

## User Interface

### ✏️ Modified: Loan Intake (Coach Flow)
- **Component added:** `Button` labeled "Save draft" in the Coach "Applicant details" (after the "Submit" button)
- **Component removed:** `Select` labeled "Loan type" (was bound to `tw.local.loan.type`)
- **Component changed:** `Text` labeled "Applicant name" — label changed to "Full legal name", binding unchanged

### ✏️ Modified: Applicant CV (Coach View)
- **Component added:** `Text` labeled "Middle name" in the section "Person data"

### ➕ Added: Interviewer CV (Coach View)
- New Coach View artifact

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

## Other changes

### ✏️ Modified: {artifact display name}
- {Plain description of what changed}

---

## Reviewed, no functional change  _(only if present)_
These files differ between the two versions, but the difference is a re-save, a regenerated ID, or a timestamp, with no change in behavior or appearance.

- {artifact display name} ({artifact type}) — {one-line reason, for example "internal IDs regenerated"}

---

## Not fully reviewed  _(only if present)_
- {artifact display name} — {reason it could not be reviewed reliably}

---

> ⚠️ The changes above are informational only — no modifications have been made to either version. To apply changes, open the target version in BAW Process Designer and make the edits manually.
```

---

## Output files

The skill always produces two files. Producing them is never optional and never depends on a request from the user.

| File | When | Contents |
|---|---|---|
| `<acronym>-<versionA>-vs-<versionB>-diff.md` | End of Step 5 | Full diff report |
| `<acronym>-<versionA>-vs-<versionB>-reconciliation.md` | End of Step 6 (if run) | Reconciliation checklist |

Use the snapshot acronyms (not the full names) in the file name. They are short and suitable for file names. Example: `HSS-v10-vs-v11-diff.md`.

---

## Formatting rules

**Change icons.** Prefix each artifact heading with one of these icons:
- ➕ Added (exists in B, not in A)
- ➖ Removed (exists in A, not in B)
- ✏️ Modified (exists in both, and the content differs)
- ⚠️ Conflict hint (changed in both, and needs manual attention)

**Conflict hints section.** If any conflict hints exist, always render this section first, immediately after the header block. Make it impossible to miss. It is the most important part of the output for a developer who is about to reconcile manually.

**Summary table.** Always render the table, even if most cells are 0. It gives the developer a quick triage view before they read the details.

**Script diffs.** Show only the changed lines in unified diff format (`-` for old, `+` for new). Do not dump the entire script. If a script is completely replaced (no shared lines), show the first five lines of each version with the note "full replacement: {A lines} → {B lines}".

**Empty categories.** Omit entire sections (heading and all content) when a category has zero changes. Do not write "No changes" entries. The absence of a section is the signal.

**Coverage line.** Always include the coverage line under the summary table. The "changed" count is the number of files that differ between the two versions, as determined in Step 4a. If the numbers do not add up, review the missing files before you present the report.

**Coach components.** Describe added or changed components in terms a developer sees in Process Designer: the component type, its visible label, and the Coach that contains it. Do not quote raw XML or JSON.

**Reviewed, no functional change.** Use this section for files whose differences you confirmed are not functional (regenerated IDs, timestamps, re-saved content). Never use it for a file you did not review.

**Artifact names.** Use the human-readable display name from the TWX file (the `name` attribute on the element), not the internal ID or file name.

**Length.** For large diffs (more than about 20 changed artifacts), offer to break the report into sections:
> *"There are N changes across M artifact types. I can show you the full report at once, or break it down by category. Which would you prefer?"*

**Tone.** Use plain, technical, neutral language. Do not recommend which version is better. Do not comment on code quality. Report facts only.

---

## Reconciliation checklist format

Produce the checklist at the end of Step 6 (interactive conflict resolution). Always use this exact structure:

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
- List decisions in the order the user made them during Step 6.
- For "Blend" decisions, write out the user's described outcome verbatim, not a summary.
- One-sided changes come from the diff that Steps 4 and 5 produce. Include all of them, not just the ones discussed.
- If the user skipped zero conflicts, omit the "Skipped conflicts" section entirely.
- If the user skipped all conflicts, or declined Step 6, the checklist still includes the one-sided changes section. It is always useful.
