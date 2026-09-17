# Architecture and usage

> **Skill:** `create-baw-portal`
> **Purpose:** Describes the skill's purpose, flow, and output types.

---

## Skill responsibility

`create-baw-portal` teaches developers:

- Which BAW APIs are needed for a requested portal
- What those APIs do and how to call them correctly
- How authorization and task scope work
- How non-federated and federated environments differ
- How authentication, CORS, proxies, gateways, pagination, and XSRF affect implementation
- How to generate or adapt portal code using that knowledge

The skill does not create Coach Views, CSHS artifacts, BAW XML, or TWX packages.
Those belong to separate skills.

---

## Simplified request flow

```
Developer request
    ↓
create-baw-portal
    ├── API guidance only
    │       └── Evidence-classified endpoint descriptions, parameters,
    │           response fields, and gap classifications
    │
    ├── Existing application adaptation
    │       └── Targeted integration code that fits the existing stack;
    │           preserves existing architecture
    │
    └── New portal / application generation
            ↓
        Developer-selected stack
            ├── React (default when no stack specified)
            ├── Developer-specified framework (Vue, Angular, plain JS, etc.)
            └── Standalone single HTML (when requested)
```

---

## Output types

| Output | Description |
|---|---|
| **API guidance** | Evidence-classified endpoint descriptions, parameter tables, response field lists, XSRF notes, gap classifications |
| **Generated code** | New portal or application built using the developer-selected stack and BAW APIs |
| **Adapted code** | Targeted additions or modifications to an existing application |
| **Guidance plus code** | API guidance with illustrative code examples that the developer can apply |

---

## Deployment environment shapes the API family

The skill supports two runtime environments:

| Environment | API family | Endpoint prefix |
|---|---|---|
| Non-federated BAW | WLE REST API | `/rest/bpm/wle/v1/` and `/rest/bpm/wle/v2/` |
| Federated BAW with PFS | PFS Federated REST API | `/rest/bpm/federated/v1/` and `/rest/bpm/federated/v2/` |

Non-federated BAW is the primary supported environment with the most extensive runtime evidence.
Federated/PFS APIs have been runtime-verified against CP4BA 26.0.0 (two federated source systems).

---

## Portal targets

The implementation targets:

- Task worker experience
- Manager/team experience
- Executive/process-owner dashboard
- Administrator-aware experience

---

## Scope boundary

This skill explicitly does not orchestrate:

- Coach View generation
- Coach composition
- Client-Side Human Service (CSHS) creation
- Internal BAW XML generation
- Authoring APIs
- TWX packaging or deployment
- BAW Coach Widget or Coach Composer

When a request touches those areas, the portal work should be completed first,
and the out-of-scope work should be referred to the appropriate skill or workflow.
