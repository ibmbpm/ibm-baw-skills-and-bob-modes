# BAW/CP4BA Remediation Capability Map

Use this mapping when selecting the appropriate platform capability for each Remediation Record in Phase 7.

| Gap type | BAW/CP4BA capability |
|---|---|
| Approval gap | Human Task with approval outcome variable |
| Missing audit trail | Process tracking, BPDW tracking group, or event logging service |
| Missing escalation | Boundary Intermediate Timer Event with non-interrupting escalation path |
| Missing error handling | Boundary Error Intermediate Event or catch block in service flow |
| Missing SoD | Separate Lane/Team assignment; do not allow the same user in both lanes |
| Missing notification | Intermediate Message Event or inline notification service call |
| Missing data validation | Decision service with BAL rules or input validation coach controls |
| Missing SLA | Timer start event duration or due date assignment at process start |
| Missing roles | TWProcessParticipant group or Lane assignment in Process Designer |
| Missing security | BPM security roles (BPMAuthor, BPMAdministrator, task-level security), OAuth/OIDC if external |
| Missing reporting | BPDW tracking group, Operational Decision Manager (ODM) for rule-driven reports |
