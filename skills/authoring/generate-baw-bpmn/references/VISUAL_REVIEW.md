# Visual Review — diagram conventions and the review artifact

Read this alongside Phases 2, 3, and step 6 in `SKILL.md`. It covers how to make the
Mermaid diagrams easier to read at a glance, and how to publish them (plus the data
model and role table) as a single reviewable artifact instead of scattered chat blocks.
Everything here is additive: if the Artifact tool isn't available in this environment,
skip the artifact-publishing parts and keep doing the plain chat-rendered Mermaid/YAML
blocks the rest of `SKILL.md` already describes -- no other step changes.

## Diagram conventions

**Legend, shown once.** The first time you render a flowchart in a conversation, add
one line above it: `Start/end = rounded, tasks = rectangle, decisions = diamond,
dashed = non-interrupting timer.` Don't repeat it on every re-render — once is enough
for the user to calibrate.

**Color by actor.** Once roles are known (they're on the plan from Phase 2 onward),
style nodes by role type so human vs. system vs. team work is visible without reading
every label:

```
classDef human fill:#4C6EF5,color:#fff;
classDef system fill:#868E96,color:#fff;
classDef team fill:#12B886,color:#fff;
class task_submit,task_review human
class sf_validate system
```

**Fake swimlanes — use with judgment.** `subgraph "Role Name" ... end` around a role's
nodes visually groups them like a swimlane, with no effect on the generated BPMN
(lanes are never emitted — see [BAW_BPMN_DIALECT.md](BAW_BPMN_DIALECT.md)). This helps when a
process has clear blocks of same-actor work (e.g., all of intake is the agent, then all
of review is underwriting). It hurts when actors interleave tightly (approve → reject →
re-review → approve), because Mermaid clusters each subgraph spatially and the
sequence arrows end up crossing back and forth between clusters, which is harder to
read than a plain top-to-bottom flow. Default to color-coding only; add subgraphs
only when you can point to actual contiguous blocks of one actor's steps.

**Business object relationships (Phase 3 onward).** Alongside the flowchart, render an
`erDiagram` from the `businessObjects` section: a `list: true` field is a one-to-many
relationship, a plain nested-object field is a to-one relationship. Keep attribute
blocks short — id/primary key and status/outcome fields only; the full field list
already lives in the YAML block, repeating it in the diagram just adds noise.

```
erDiagram
    SHAKEORDER ||--o{ ORDERITEM : items
    SHAKEORDER }o--|| CUSTOMER : customer
    CUSTOMER ||--o| ADDRESS : deliveryAddress
    SHAKEORDER {
        string orderId
        string status
    }
```

**Diffing a revision.** When the user asks to change the plan, the numbered plan is
where the diff lives, not the diagram: strike through removed steps (`~~old step~~`),
bold new ones (`**new step**`), and leave unchanged steps plain. Re-render the full
updated Mermaid diagram clean (no diff markup in the diagram itself — Mermaid has no
good way to show "removed," and a cluttered diagram defeats the point of having one).

## The review artifact

Once you have a plan (Phase 2) and, if requested, a data model (Phase 3), publish them
as a single Artifact instead of leaving the flowchart, ER diagram, and role table as
three separate chat blocks:

1. Load the `artifact-design` skill before writing the file — this is a content-dense
   internal review page (diagrams, a role table, YAML), not a marketing page, so keep
   the design investment functional: readable typography, diagram containers that
   scroll rather than overflow, light/dark aware. Don't over-produce it.
2. Write a Markdown file (Artifacts render Mermaid natively in `.md` files, no HTML
   needed) to a scratch/temp location, named `<ProcessName-kebab>-review.md` — the
   filename is the artifact's title. Include: the flowchart, the role table, and (from
   Phase 3 onward) the business-object `erDiagram` and YAML.
3. Publish it with the `Artifact` tool. Use a consistent favicon across this skill's
   artifacts (a process-flow icon works well) and a one-line description ("Process flow
   and data model review for <Process Name>").
4. On every later revision (plan changes, Phase 3's data model, or the confirmed final
   version in step 6), overwrite the same scratch file and call `Artifact` again with
   the same `file_path` — this redeploys to the same URL, so the user keeps one stable
   link across the whole conversation instead of getting a new one each turn.
5. Mention the artifact link once when first published, and again if it's updated —
   don't repeat it in every message.

## Round-trip after generation (step 6)

After the generator writes the `.bpmn`/`.zip`/`README.md`, the README's Mermaid diagram
is the ground truth (it's built from the same config that produced the XML). Copy its
diagram and documentation into the same review-artifact file from above and republish
at the same URL, so what the user sees matches exactly what was generated — closing the
loop without them having to open the output folder to check. If the diagram in the
artifact doesn't match what you expected, the config is wrong, not the diagram: fix the
config and regenerate rather than hand-editing either.
