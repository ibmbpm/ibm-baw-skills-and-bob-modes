# IBM BAW Log Formats & Error Patterns — Reference

> **Scope:** IBM Business Automation Workflow (BAW) 22.x–26.x on Liberty and traditional WebSphere Application Server.
> Items marked **(verify in your environment)** reflect patterns that may vary by version or topology.

---

## Table of Contents

1. [Overview — Log Files & Locations](#1-overview--log-files--locations)
2. [SystemOut.log / SystemErr.log](#2-systemoutlog--systemerrlog)
3. [messages.log — SIMPLE vs JSON](#3-messageslog--simple-vs-json)
4. [trace.log — Trace Specification & BPM Components](#4-tracelog--trace-specification--bpm-components)
5. [FFDC Files](#5-ffdc-files)
6. [Process/Errors API Response](#6-processerrors-api-response)
7. [Common Error Patterns](#7-common-error-patterns)
8. [Correlation Tips](#8-correlation-tips)

---

## 1. Overview — Log Files & Locations

### Traditional (on-premises)

| Log File | Default Path | Purpose |
|---|---|---|
| `SystemOut.log` | `<WAS_HOME>/profiles/<profile>/logs/<server>/SystemOut.log` | JVM stdout; all INFO+ entries |
| `SystemErr.log` | same directory | JVM stderr |
| `messages.log` | same directory | Structured INFO+ messages with thread IDs |
| `trace.log` | same directory | Verbose trace (created only when trace is enabled) |
| `ffdc/` directory | `<WAS_HOME>/profiles/<profile>/logs/ffdc/` | One `.txt` file per incident + `<server>_exception.log` summary |

### Container (CP4BA / BAW on OpenShift)

| Log | Container Path | Notes |
|---|---|---|
| `liberty-message.log` | `/logs/application/liberty-message.log` | Equivalent to messages.log |
| `liberty-trace.log` | `/logs/application/liberty-trace.log` | Created when trace_specification is non-default |
| `ffdc/` | `/logs/ffdc/` | Incident files |
| Console (stdout) | `kubectl logs <pod>` | JSON by default; controlled by `console_format` |

Container log parameters (under `baw_configuration[].logs` in the CR):
```yaml
logs:
  console_format: "json"           # default in containers
  message_format: "SIMPLE"         # SIMPLE | JSON
  trace_format: "ENHANCED"         # BASIC | ADVANCED | ENHANCED
  trace_specification: "*=info"    # default; extend for debugging
  console_source: "message,trace,accessLog,ffdc,audit"
```

---

## 2. SystemOut.log / SystemErr.log

### SIMPLE format entry anatomy

```
[DD/Mon/YYYY HH:mm:ss:SSS TZ] <threadId> <component> <levelCode> [msgId:] <message>
```

| Field | Example | Notes |
|---|---|---|
| Timestamp | `[25/Jan/2025 14:32:07:412 UTC]` | `dd/MMM/yyyy HH:mm:ss:SSS z` |
| Thread ID | `00000087` | 8-digit hex; correlates entries across all log files |
| Component | `com.ibm.bpm.bpdengine` | Logger or class name |
| Level code | `I` `A` `W` `E` `F` | See table below |
| Message ID | `CWWKZ0001I:` | Optional; present for NLS-translated messages |

**Level codes:** `I` = INFO · `A` = AUDIT · `W` = WARNING · `E` = ERROR · `F` = FAILURE

**Example:**
```
[25/Jan/2025 14:32:07:412 UTC] 00000087 com.ibm.bpm.bpdengine W CWWKZ0203W: Unable to locate task for token 4029 in instance BPDInstance.1234
```

---

## 3. messages.log — SIMPLE vs JSON

`messages.log` captures INFO, AUDIT, WARNING, ERROR, and FAILURE; excludes raw JVM output.

### JSON format (enabled with `message_format: JSON` or `WLP_LOGGING_MESSAGE_FORMAT=json`)

```json
{
  "ibm_datetime": "2025-01-25T14:32:07.412+0000",
  "loglevel": "WARNING",
  "ibm_threadId": "00000087",
  "module": "com.ibm.bpm.bpdengine",
  "ibm_messageId": "CWWKZ0203W",
  "message": "Unable to locate task for token 4029 in instance BPDInstance.1234",
  "ibm_hostName": "baw-pod-0",
  "type": "liberty_message"
}
```

Key fields: `ibm_threadId` (cross-file correlation), `ibm_messageId` (CWWK*/BPM* code), `ibm_hostName` (pod ID in clusters), `type` (source: `liberty_message`, `liberty_trace`, `liberty_ffdc`).

---

## 4. trace.log — Trace Specification & BPM Components

Create `trace.log` only when at least one component is traced below INFO. Enable targeted components; disable when done.

### Trace specification syntax

```
component=level:component2=level2
```

Component patterns:
- `PackageName.ClassName=level` — single class (e.g. `com.ibm.bpm.bpdengine.BPDEngine=all`)
- `com.ibm.bpm.*=all` — all classes under `com.ibm.bpm` and every sub-package (use `*` to group all classes under a package)
- `WLE.=all` — all classes grouped under the `WLE` logger group
- `*=all` — every component (extremely verbose — use only as last resort)

Examples:
- `WLE.=all:com.ibm.bpm.*=all:=info` — trace BAW engine, reset everything else to INFO

### Enabling trace

**Traditional (Liberty on-premises):** Add or update the `<logging>` element in `server.xml`:
```xml
<logging traceSpecification="WLE.=all:com.ibm.bpm.*=all:=info" traceFormat="ENHANCED"/>
```
(ref: https://www.ibm.com/docs/en/was-liberty/base?topic=liberty-logging-trace)

**Container:** set `trace_specification` in the CR:
```yaml
logs:
  trace_specification: "WLE.=all:com.ibm.bpm.*=all:com.ibm.workflow.*=all:=info"
```

### Key BPM/BAW trace component names

| Trace String | Area |
|---|---|
| `WLE.=all` | Workflow Logger Engine group — core BAW server-side code |
| `WLE.wle_bpd=all` | BPD execution engine |
| `WLE.wle_rest=all` | REST API layer |
| `WLE.wle_eventmgr=all` | Event Manager / scheduler |
| `com.ibm.bpm.bpdengine.*=all` | BPD script execution |
| `com.ibm.bpm.integration.*=all` | Integration service calls |
| `com.ibm.bpm.mon.oi.*=all` | BPM event emitter / tracking |
| `com.ibm.workflow.*=all` | Workflow-specific components |
| `com.ibm.ws.security.*=all` | Liberty security (SSO, LDAP, OIDC) |

### Example trace entry (ENHANCED format)

```
[25/01/25 14:32:09:011 UTC] 00000087 com.ibm.bpm.bpdengine.ProcessInstance 3 execute  > ProcessInstance.execute Entry  instanceId=BPDInstance.1234 activityId=ActivityA
```

---

## 5. FFDC Files

FFDC (First Failure Data Capture) records the full context of runtime failures.

### Location

Traditional: `<WAS_HOME>/profiles/<profile>/logs/ffdc/`
Container: `/logs/ffdc/` inside the pod

### File naming convention

```
<servername>_<threadId>_<YY.MM.DD>_<HH.mm.ss>_<sequence>.txt
```
Example: `defaultServer_00000087_25.01.25_14.32.07_0.txt`

The companion `<server_name>_exception.log` in the same directory summarises all incidents:
```
<count>  <lastTimestamp>  <exceptionClass>  <sourceId>  <probeId>
```

### Incident file structure

```
------Start of DE processing------
[25/01/25 14:32:07:412 UTC], key = com.ibm.bpm.bpdengine.BPDEngineException
Exception = com.ibm.bpm.bpdengine.BPDEngineException
Source    = com.ibm.bpm.bpdengine.ProcessInstance.execute
probeId   = 325
threadId  = 00000087

Stack Dump =
com.ibm.bpm.bpdengine.BPDEngineException: Script error in step "Calculate Total"
    at com.ibm.bpm.bpdengine.ScriptRunner.run(ScriptRunner.java:325)
    ...
Caused by: com.lombardisoftware.core.TWException: Cannot read property 'value' of undefined
    at ...
------End of DE processing------
```

**Key prologue fields:** `Exception` (root class), `Source` (class/method), `threadId` (cross-file correlation), `Stack Dump` (full chain including `Caused by`).

### FFDC pointer in messages.log

```
FFDC1015I: An FFDC Incident has been created: "com.ibm.bpm..." at defaultServer_00000087_25.01.25_14.32.07_0.txt
```
This message links you from messages.log directly to the FFDC file.

---

## 6. Process/Errors API Response

**Endpoint:** `PUT /rest/bpm/wle/v1/process/errors?instanceIds=<id1>,<id2>`
(ref: https://www.ibm.com/docs/en/baw/25.0.x?topic=information-put)

Returns `RuntimeErrorResponse` with per-instance runtime error details.

### Response structure

```json
{
  "status": "200",
  "data": {
    "runtimeErrors": [
      {
        "instanceId": "BPDInstance.1234",
        "errorMessage": "Runtime error in script (\"bpd engine expression\" 3:-1).\nScript (line 3):\n  3: throw \"error\"",
        "errorCode": "BPMD0049E",
        "failedStepName": "Calculate Total",
        "failedServiceName": "MyIntegrationService",
        "failedScriptName": "bpd engine expression",
        "failedLine": 3,
        "errorType": "ScriptError"
      }
    ],
    "failedOperations": []
  }
}
```

| Field | Description |
|---|---|
| `instanceId` | `BPDInstance.<number>` — the failed instance |
| `errorMessage` | Human-readable description; may include script excerpt |
| `errorCode` | BPM*/BPMD* message code (verify in your environment) |
| `failedStepName` | Activity name where failure occurred |
| `failedServiceName` | Called service name (if applicable) |
| `failedScriptName` | Script context label |
| `failedLine` | Line number in the script |
| `errorType` | `ScriptError`, `ServiceError`, `IntegrationError`, etc. |
| `failedOperations` | Instances whose error info could not be retrieved |

---

## 7. Common Error Patterns

| Error Pattern | Typical Cause | First Response Step |
|---|---|---|
| `CWWKZ0013E: Unable to install application` | Deployment descriptor error, missing class | Check FFDC for root exception; verify EAR/WAR contents |
| `CWWKS4000E: Authentication did not succeed` | LDAP misconfiguration, wrong credentials | Enable `com.ibm.ws.security.=all` trace; verify LDAP bind user |
| `CWWKS5207W: token has expired` | Token lifetime too short or clock skew | Increase token expiry; synchronize system clocks |
| `CWWKE0701E: Bundle could not be resolved` | Missing OSGi feature or version mismatch | Verify `server.xml` features match installed Liberty version |
| `CWTBG0019E: instanceId parameter missing or not valid` | Caller passed wrong format; instance deleted | Verify instance exists via Process Inspector before retrying |
| `CWTBG0550E: Process instance not in failed state` | Retry called on non-failed instance | Check instance state; use correct API action |
| `TWException` / `BPMScript error` | Uncaught JavaScript exception in Script task | Enable `WLE.wle_bpd=all` trace; review script in Process Designer |
| `ProcessNavigationException: Cannot navigate past end of process` | Token routing issue; gateway misconfiguration | Compare flow model with FFDC stack; check gateway conditions |
| `TaskCompletionException: Task already completed` | Race condition or duplicate completion | Check for concurrent submissions; enable `WLE.=all` trace |
| `ServiceException: Integration service call failed` | Downstream REST/SOAP unavailable or returned error | Check service output mapping; verify endpoint availability |
| `SQLCODE=-911` / `DB2 DEADLOCK` | DB lock contention on BPM schema | Review DB2 lock timeout; check for long-running transactions |
| `OutOfMemoryError: Java heap space` | Heap exhausted; often caused by large variable payloads | Review JVM heap config; inspect large Business Objects |
| `ConnectionPoolException: Unable to get connection` | JDBC pool exhausted | Check DataSource pool size; look for connection leaks in FFDC |
| `CWWKW0101E: failed with status 500` | Unhandled exception in REST handler | Follow `FFDC1015I` pointer in messages.log to incident file |

---

## 8. Correlation Tips

### By Thread ID

Every entry in `messages.log`, `trace.log`, and FFDC files carries the same **8-digit hex thread ID**. This is the primary correlation key for a single request.

```bash
grep "00000087" messages.log trace.log ffdc/*.txt
```

### By Process Instance ID

BAW log messages often include `BPDInstance.<number>` in the text.

```bash
grep "BPDInstance.1234" messages.log trace.log ffdc/*.txt
```

Then call the errors API for structured error data:
```
PUT /rest/bpm/wle/v1/process/errors?instanceIds=1234
```
(ref: https://www.ibm.com/docs/en/baw/25.0.x?topic=information-put)

### By FFDC Pointer

`FFDC1015I` in `messages.log` names the FFDC file. The `threadId` field in the FFDC prologue links back to trace entries for that exact failure.

### Container environments

All sources are multiplexed into stdout as JSON. Filter with `kubectl logs`:

```bash
kubectl logs <pod> | jq 'select(.ibm_threadId == "00000087")'
kubectl logs <pod> | jq 'select(.loglevel == "ERROR" or .loglevel == "FAILURE")'
```

`ibm_hostName` identifies the pod in multi-replica deployments.

---

*Grounded in IBM BAW 24.x/25.x and Liberty documentation. Verify paths and field names against your specific version.*
