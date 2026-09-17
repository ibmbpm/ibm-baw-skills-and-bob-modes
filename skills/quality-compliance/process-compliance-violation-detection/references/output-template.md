# Output Template

Always produce the full structure below. Do not omit sections.
If a section has nothing to report, write: `None identified at this time.`

---

```markdown
# Process Compliance Analysis Report

**Process Application:** [Name and version]
**Analysis Date:** [Date]
**Compliance Documents Reviewed:** [List]
**Active Rule Set:** Default Rules | Document-Extracted Rules | Custom Rules (delete as applicable)
**Total Rules Evaluated:** [N]
**Overall Status:** COMPLIANT | PARTIALLY COMPLIANT | NON-COMPLIANT | ASSESSMENT INCOMPLETE

---

## 1. Compliance Documents Reviewed

[For each document: name, type, key sections relevant to this process app]

---

## 2. Compliance Rules Extracted

[Table: Rule ID | Category | Description | Source Section | Severity | Required Evidence]

---

## 3. Process Application Understanding

[Concise summary: name, platform, main scenario, key roles, happy path (≤5 steps), known integrations, observable controls]

---

## 4. Evidence Collected

[List of artifacts examined: BPD names, service names, team names, coach names, decision services, integration endpoints, tracked variables, etc.]

---

## 5. Compliance Assessment

[Table: Rule ID | Status | Evidence | Confidence | Reasoning | Impact]

---

## 6. Compliance Findings

[Summary of COMPLIANT, PARTIALLY_COMPLIANT, NON_COMPLIANT, NOT_VERIFIABLE counts with severity breakdown]

---

## 7. Violations Detected

[One Violation Finding block per violation in this format:]

### Finding [VIO-NNN]
**Category:** [category]
**Severity:** Critical | High | Medium | Low
**Artifact:** [artifact name]
**Rule Violated:** [Rule ID]
**Description:** [what is wrong]
**Evidence:** [what was found or not found]
**Impact:** [consequence]

---

## 8. Risks

[List risks that are not outright violations but represent elevated risk. Include risk level and probability.]

---

## 9. Missing Evidence

[List rules that are NOT_VERIFIABLE and what evidence is needed to resolve them]

---

## 10. Rule Clarification & Discovery Audit Trail

This section is the immutable record of all questions asked and answers received during rule clarification and evidence discovery. Populate it regardless of output format.

### 10a. Rule Clarification Log

[For each clarification question asked during rule review, record the following:]

**Q[N] — [Rule ID]: [short rule description]**
Question asked: [verbatim question]
User answer: [verbatim or paraphrased answer, or "No answer provided"]
Action taken: `[Clarified: <summary>]` | `[EXCLUDED — <reason>]` | `[Custom rule added: CUSTOM-NNN]` | `[No change]`

### 10b. Evidence Discovery Log

[For each discovery question asked during evidence gap review, record the following:]

**Q[N] — [Rule ID]: [short rule description]**
Question asked: [verbatim question]
User answer: [verbatim or paraphrased answer, or "No answer provided / Accepted as-is"]
Action taken: Status changed from `[old]` → `[new]` | `[Discovery confirmed — status unchanged]` | `[Accepted by user]` | `[New finding created: VIO-NNN]`

### 10c. Open Questions

[List any questions that remain unanswered and the verdict that stands as a result. If all questions were answered, write: "None — all discovery questions were resolved."]

---

## 11. Remediation Recommendations

[One Remediation Record per Finding in this format:]

### Remediation [REM-NNN] — for Finding [VIO-NNN]
**Severity:** Critical | High | Medium | Low
**Recommended Change:** [what to do]
**BAW/CP4BA Capability:** [platform feature]
**Change Type:** [artifact type]

---

## 12. BAW / CP4BA Capability Recommendations

[List of specific BAW/CP4BA platform features recommended across all remediations, with brief description of why each is relevant]

---

## 13. Confidence Assessment

**Overall Confidence:** [%] — [tier: Verified | Strong | Partial | Low]

| Rule ID | Confidence | Tier | Limiting Factor |
|---|---|---|---|
| [Rule ID] | [%] | [tier] | [what limits confidence] |

**Confidence Narrative:** [2–4 sentences explaining overall confidence level and what evidence would raise it]
```
