# The BAW BPMN Dialect — import behavior and post-import steps

`scripts/generate_baw_bpmn.py` produces BAW's export dialect (`bpmnid-` UUID ids,
`processType="None"`, no diagram section). This reference explains what BAW creates
from each BPMN construct on import and the post-import steps to hand the user.

## Supported constructs

Only constructs in the import mapping below should be used. Elements outside that list
— callActivity, signal/escalation/compensation events, data stores — should not be
included (see `references/PROCESS_JSON_SCHEMA.md`).

## How lanes work on import

**Lanes are supported and should be emitted.** BAW assigns tasks to swim-lanes using
two signals, in priority order:

1. `<performer name="...">` child element on the task — BAW uses this as the primary
   semantic signal for lane assignment and team binding.
2. `<laneSet>/<lane>/<flowNodeRef>` membership — visual/structural fallback.

The generator emits both when the config has a `roles` section and tasks reference
roles via `"role": "<roleId>"`. Assign a role to every task; unassigned elements land
in an "Unassigned" catch-all lane BAW creates automatically.

**Pools are not emitted** — a pool in BPMN 2.0 represents a separate participant
(a different organisation), not a swim-lane within one process. BAW's own exports
do not use pools for single-process models.

BAW also ignores any incoming diagram/layout section and auto-arranges on import, so
the generator never emits one — "adjust the process layout" is an expected post-import
step per IBM's own docs, not a gap here.

## What BAW creates on import (official mapping)

From IBM's ["Mapping BPMN 2.0 constructs to workflow objects after import"](https://www.ibm.com/docs/en/baw/24.0.x?topic=iebm-mapping-bpmn-20-constructs-workflow-objects-after-import)
documentation. Constructs not in this table should not be included.

| BPMN construct | BAW object after import |
|---|---|
| Process | Process (BPD) |
| Task with performers / Human task / userTask | Activity (user task) + reference to a generated client-side human service |
| Service task / task without performers | Activity (system task) + **reference to a generated service flow** |
| Business rule task | Decision task + reference to a service flow |
| Script task | Activity with a JavaScript implementation |
| Subprocess | Activity with subprocess type (single none start event only) |
| Exclusive / Inclusive / Parallel gateway | Same gateway type |
| Event-based gateway | Converted to activity with message boundary events |
| None/message/timer/error start event | Same start event type (one none start honored) |
| End / error / message / terminate end event | Same end event type |
| Intermediate catch message/timer | Intermediate event (receiving) |
| Intermediate throw message | Intermediate message event (sending) |
| Boundary error/message/timer event | Event attached to the activity |
| Sequence flow | Sequence flow |
| Item definition | Business object |
| Data object / process data input / output | Private variable / process input / output |
| Input/output data association | Data mapping inside the activity |
| Text annotation | Note |
| Receive task | Intermediate message event |

Note the two rows this generator leans on most: **service task → a generated service
flow named after the task** (so name each `serviceTask` exactly what its service flow
should be called), and **item definition → business object** (how the sidecar `.xsd`
for `businessObjects` becomes real BAW business objects — see
`references/PROCESS_JSON_SCHEMA.md` for the mechanics).

## How to import (two supported routes)

Both routes want a **.zip** (the generator writes one next to the `.bpmn`, including
the business-object `.xsd` when one was generated — never strip it out):

- **New process app:** Workflow Center → Process Apps tab → **Import Process App** →
  choose the .zip. BAW creates the app, generates the artifacts, and auto-snapshots it.
  (An "Import Toolkit" equivalent exists on the Toolkits tab.)
- **Existing process app:** Process Designer → open the app → **File > Import** →
  choose the .zip. Imported artifacts get an "Imported" tag. Re-importing the same
  file creates duplicate copies — it never overwrites a previous import.

Multiple `.bpmn` files can share one zip to import several processes at once.

## Post-import checklist (from IBM's "next steps" guidance)

Import success ≠ done. Hand the user this list with the generated artifacts:

1. Open every generated artifact and confirm it looks as expected; read any import
   warnings — each one usually means an unsupported construct was dropped or converted.
2. Complete the **service flow** details (connectors, scripts, data mapping).
3. Customize the default generated **coaches** in the client-side human services.
4. Finish the **conditional logic** on exclusive/IOR gateways (imported conditions are
   a starting point; BAW expects them re-expressed against real variables).
5. Provide **default values** for uninitialized private variables.
6. Complete **JavaScript** in script activities.
7. Adjust the diagram **layout** and assign **team members** to activities.
8. Run BAW's validation and fix anything it flags.
