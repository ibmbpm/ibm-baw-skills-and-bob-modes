# Process Compliance Violation Detection — Documentation

> Evaluate IBM® BAW and CP4BA process applications against compliance, governance, regulatory, business policy, architecture, or standards documents — detecting violations, gaps, and risks, then recommending remediation using documented BAW/CP4BA platform capabilities.

## Purpose

This skill is for BAW and CP4BA developers, architects, and compliance officers who need to verify that a process application meets a given compliance standard before going to production. Provide a compliance document (policy, regulation, internal standard, or named regulation such as SOX or GDPR) and a process application (exported `.twx` file or a live BAW server to export from), and the skill runs a structured eight-phase analysis pipeline: rule extraction → rule confirmation → process artifact discovery → evidence evaluation → Socratic gap-filling → violation detection → remediation recommendations → report generation. The skill also supports document-only analysis (extract rules with no process app yet) and process-only analysis (evaluate against the built-in default rule set when no compliance document is available).

## Setup and configuration

- No MCP server is required. This skill uses only HTTP calls to the BAW REST API and local file reads — no special MCP tools are needed.
- BAW REST access (REST mode only): Provide a BAW server URL and valid credentials. The skill handles authentication (CSRF token + session cookies) internally. Credentials are used only within the session and are never stored.
- Path mode (no server access needed): Export the `.twx` file from BAW / Workflow Center manually, then provide the local file path. No server credentials required.
- Workspace write access: The skill writes two output files — `Rules.md` (the active rule set) and `[ProcessAppName]-compliance-report.md` — to your workspace directory.

## Compatibility

- IBM® BAW and CP4BA only. The rule extraction, evidence model, and remediation map are specific to BAW / CP4BA artifacts (BPDs, Human Tasks, Coaches, Decision Services, BPDW tracking groups, etc.). Non-BAW process platforms are not supported.
- `.twx` file required for process analysis. The skill can read a `.twx` via a local path (Path mode) or export one live via REST (REST mode). Without a `.twx` source, only document-only analysis is possible.
- BAW REST API version: REST endpoints are drawn from the BAW 26.0.x Operations API (`/ops` base path). Server versions significantly older than 26.x may expose different endpoint paths.
- Report output is always Markdown. The skill writes a `.md` file and does not offer alternative formats.

> **Note:** Credentials shown in prompt examples are for illustration only. Never use real production credentials in prompts. Use environment variables or a secrets manager for sensitive values.

## Prompt examples

### Full analysis — compliance document + TWX file (Path mode)

**Prompt:**
> I need a full compliance analysis. The compliance document is at `docs/policies/SOX_Section404_Controls.md` and the process application TWX file is at `exports/InvoiceApproval-SS2.0.twx`.

**What to expect:** The skill extracts rules from the compliance document, confirms the rule set with you, evaluates all process artifacts in the `.twx` against those rules, asks targeted questions to resolve evidence gaps, then writes a complete 13-section Markdown report (`InvoiceApproval-compliance-report.md`) with violation findings, severity levels, and BAW-specific remediation recommendations.

---

### Full analysis — live BAW server (REST mode)

**Prompt:**
> I need a compliance check against our GDPR data-handling policy at `policies/GDPR_Article32.md`. The process app is live on our BAW server at `https://baw.corp.example.com:9443`. Username is `bawadmin`, password is `P@ssw0rd!`. Process app acronym is `CUST`, snapshot is `SS3.1`.

**What to expect:** The skill logs in to the BAW server, lists available process apps to validate the acronyms, exports the `.twx`, then runs the same full analysis pipeline — confirming each REST call's HTTP status before proceeding.

---

### Process-only analysis — no compliance document (default rules)

**Prompt:**
> I don't have a compliance document. Just check my process app at `exports/LoanOrigination-Tip.twx` against your default governance rules and tell me what issues you find.

**What to expect:** The skill presents the built-in default rule set (DEF-001 through DEF-111 across 11 categories) as suggestions for you to accept, exclude, or modify before any evaluation begins — it will not apply them silently.

---

### Document-only analysis — no process app yet

**Prompt:**
> I only have a compliance document right now — no process app yet. The document is at `compliance/HR_Hiring_Policy_v2.md`. Can you extract the rules and tell me what BAW evidence I'll need to prove compliance for each one?

**What to expect:** The skill extracts all rules from the document, assigns `DOC-NNN` IDs with category and severity, writes `Rules.md`, and for each rule specifies exactly which BAW artifact or behavior would constitute proof — with no violation findings and no overall verdict.

---

### Custom rule injection alongside a compliance document

**Prompt:**
> Audit the Purchase Order process at `exports/PurchaseOrder-SS1.0.twx` against `policies/Procurement_Policy.md`. Also add this custom rule before you start:
>
> ```
> CUSTOM RULE: All purchase order approvals above $50,000 must be routed to the CFO team.
> Category: Approval
> Severity: Critical
> Source: Internal Finance Directive FIN-2024-003
> Required Evidence: Gateway condition or decision service checking po_amount > 50000 with routing to CFO team lane.
> ```

**What to expect:** The skill assigns the custom rule a `CUSTOM-NNN` ID, appends it to `Rules.md` with source marked `[Custom]`, evaluates it alongside the document-extracted rules, and includes it in the violation findings and remediation section if the process does not implement the required routing logic.

---

### Disable default rules — document-extracted rules only

**Prompt:**
> Audit `exports/EmployeeOnboarding-SS2.0.twx` against `policies/OnboardingPolicy.md`. Only apply the rules in the compliance document — disable the default rule set for this run.

**What to expect:** The skill acknowledges the instruction, notes "Default Rule Set: Disabled" in the report header, and evaluates only the `DOC-NNN` rules extracted from the provided document — no `DEF-NNN` rules appear anywhere in the assessment.

---

### No inputs provided — redirect

**Prompt:**
> Can you do a compliance check?

**What to expect:** The skill responds by stating that at least one input is needed (a compliance document, a `.twx` path, or server credentials) and waits — it does not guess, invent analysis, or auto-load example files.

---

### Compliance document provided; process app to follow later

**Prompt:**
> Audit the Accounts Payable process against our ISO 27001 controls at `policies/ISO27001_AppendixA.md`. I'll provide the process app later.

**What to expect:** The skill offers to perform document-only analysis immediately (extracting rules and writing `Rules.md`) while clearly stating that process-side evaluation requires either a `.twx` file path or BAW server credentials — it does not invent process content.
