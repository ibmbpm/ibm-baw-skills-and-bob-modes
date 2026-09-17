---
active_gaps:
  - id: API-GATEWAY
    title: API gateway token exchange
    classification: DEPLOYMENT — NOT TESTED
    owner: BAW Administrator
  - id: D2a
    title: External runtime-validation boundary (Profile C)
    classification: PRODUCT DEFINITION — OPEN
    owner: PM
  - id: D9
    title: BAW version matrix
    classification: CONFIGURATION — REQUIRED
    owner: PM
---

# Known gaps

> **Skill:** `create-baw-portal`
> **Purpose:** Tracks unresolved gaps that currently block or constrain implementation decisions.
> Every entry here means: do not generate code for this capability without the stated action first.
> When a gap is resolved, remove it — do not accumulate resolved entries here.

---

## API gateway token exchange

| Configuration | Status |
|---|---|
| API gateway token exchange | NOT TESTED — deployment-specific; no standard endpoint to probe |

**Required action:** State that the mechanism is deployment-specific and must be confirmed with the BAW administrator. Do not generate gateway token-exchange code without knowing the specific gateway configuration.

---

## D2a — External runtime-validation boundary

| Attribute | Value |
|---|---|
| **Classification** | PRODUCT DEFINITION — OPEN |
| **Affects** | Profile C (external portal generation) |
| **What is unknown** | Which external authentication, proxy, and hosting configurations must be demonstrated as working for product delivery versus delivered as generated code with documented deployment prerequisites. |
| **Required action** | PM to define the runtime-validation boundary for external deployments before Profile C acceptance criteria can be finalized. |

---

## D9 — BAW version matrix

| Attribute | Value |
|---|---|
| **Classification** | CONFIGURATION — REQUIRED |
| **Affects** | WLE v2 API gating; version-conditional code generation |
| **What is unknown** | Which BAW versions and deployment configurations must be supported for product delivery. WLE v2 availability is version-dependent. |
| **Required action** | PM to confirm the supported BAW version matrix. Gate WLE v2 code generation on FDR probe result until confirmed. |
