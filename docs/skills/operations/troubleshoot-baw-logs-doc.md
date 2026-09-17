# Troubleshoot BAW Logs — Documentation

> Diagnoses IBM® Business Automation Workflow (BAW) runtime failures by analyzing error logs, stack traces, and FFDC files. Identifies root causes, correlates entries across log types, and provides structured remediation steps.

## Purpose

This skill helps BAW developers and administrators move from raw log noise to a clear root cause with actionable next steps. It handles five input modes: pasted log content, local log files, live log retrieval from a connected BAW server (Liberty only), structured error lookup by process instance ID, and Event Manager task inspection for silently stuck timer or receive tasks. Use it whenever a BAW process is stuck in an error state, a task or service keeps failing, a snapshot deployment fails, or you have log output you need interpreted. When no MCP server is available the skill automatically switches to REST mode and executes `curl` calls itself — you are never asked to run commands manually.

## Setup and configuration

- No special setup is required for paste or file mode. Paste log content directly into the chat, or provide a locally accessible log file path.
- MCP server (optional — unlocks instance and live-log modes): Connect the `workflow-runtime-mcp-server`. The skill detects its presence by looking for `get_exposed_processes` in its tool list. With MCP connected it can call:
  - `get_process_instance_errors` — structured per-instance runtime error lookup
  - `get_process_details` — full instance state, business variables, and task history
  - `get_baw_server_logs` — live `messages.log` fetch (Liberty only)
- REST mode (no MCP needed): When the MCP server is absent the skill automatically switches to `curl`-based REST. It will ask for your `BAW_BASE_URL` (e.g. `https://baw.example.com:9443`) and credentials the first time a REST call is needed, then runs all calls itself. REST equivalents exist for every MCP operation.
- Liberty required for live-log retrieval: Both `get_baw_server_logs` (MCP) and `GET /ops/std/bpm/logs` (REST) are only available on Liberty-based BAW deployments. The skill detects a 404, 403, or empty-body response and falls back to paste/file mode automatically.
- Admin privileges required for `/ops/` endpoints: The `/ops/system/login`, `/ops/std/bpm/logs`, and `/ops/std/bpm/event_manager_tasks` REST endpoints require the caller to have BAW admin rights. A 403 response causes the skill to fall back gracefully.

## Compatibility

- BAW 22.x–26.x on Liberty — log formats, field names, and FFDC structure are documented for this version range; older versions or traditional WAS-profile deployments may vary.
- Liberty required for live-log and Event Manager REST endpoints — `get_baw_server_logs` (MCP) and `GET /ops/std/bpm/logs` (REST) return an empty body on non-Liberty (traditional WAS-profile) servers. The skill detects this and falls back to paste/file mode.
- Container log paths differ from on-premises — in CP4BA/BAW on OpenShift, `messages.log` lives at `/logs/application/liberty-message.log` inside the pod; the on-premises path is `<WAS_HOME>/profiles/<profile>/logs/<server>/messages.log`. Container logs are emitted as JSON to stdout and can be filtered with `kubectl logs … | jq`.
- CWLLG\* task IDs ≠ process instance IDs — messages like `CWLLG0181E: error in the 360 task` use Event Manager scheduler task IDs, not process instance IDs. Only treat a number as an instance reference when the log explicitly says `BPDInstance.<n>`, `piid=<n>`, or `instanceId` in the structured API response.
- `/rest/bpm/wle/v1/process/{processId}` and `/ops/system/login` — these endpoints are grounded by manual inspection; verify paths and field names against your specific BAW version before scripting.

> **Note:** Credentials shown in prompt examples are for illustration only. Never use real production credentials in prompts. Use environment variables or a secrets manager for sensitive values.

## Prompt examples

### Paste — script task null reference

**Prompt:**
> My invoice approval process failed. Here are the lines from SystemOut.log:
>
> ```
> [27/Mar/2025 09:14:22:311 UTC] 000000a3 com.ibm.bpm.bpdengine E TWException: Cannot read property 'invoiceTotal' of undefined
>   at TWScript.line5(CalculateLineItems:5)
> [27/Mar/2025 09:14:22:314 UTC] 000000a3 com.lombardisoftware.server W Process instance BPDInstance.9102 moved to error state
> ```
>
> What's the root cause and how do I fix it?

**What to expect:** A structured diagnosis report naming the exact script task (`CalculateLineItems`, line 5), the null reference on `invoiceTotal`, thread `000000a3` as the correlation key, and concrete remediation steps including a null guard before accessing the property.

---

### Paste — FFDC pointer in messages.log

**Prompt:**
> We had a server error this morning. Here are the relevant messages.log lines — what should I look at first?
>
> ```
> [28/Mar/2025 11:02:44:001 UTC] 00000061 com.ibm.bpm.bpdengine E CWWKZ0013E: Unable to install application MyProcessApp
> [28/Mar/2025 11:02:44:005 UTC] 00000061 com.ibm.bpm.bpdengine E FFDC1015I: An FFDC Incident has been created: "com.ibm.bpm.bpdengine.DeploymentException ..." at defaultServer_00000061_25.03.28_11.02.44_0.txt
> ```

**What to expect:** An explanation of `CWWKZ0013E` (deployment descriptor error or missing class), what the `FFDC1015I` pointer means, how to locate the named FFDC file on the server, and the next step — reading the `Caused by:` chain in the FFDC `Stack Dump` section bottom-up to find the root exception.

---

### Paste — FFDC file content

**Prompt:**
> Here's an FFDC file from our container at `/logs/ffdc/defaultServer_000000b2_25.03.27_08.14.07_0.txt`:
>
> ```
> ------Start of DE processing------
> [27/03/25 08:14:07:003 UTC], key = com.ibm.bpm.bpdengine.BPDEngineException
> Exception = com.ibm.bpm.bpdengine.BPDEngineException
> Source    = com.ibm.bpm.bpdengine.ProcessInstance.execute
> threadId  = 000000b2
>
> Stack Dump =
> com.ibm.bpm.bpdengine.BPDEngineException: Script error in step "ValidateShipment"
>     at com.ibm.bpm.bpdengine.ScriptRunner.run(ScriptRunner.java:210)
> Caused by: com.lombardisoftware.core.TWException: Cannot read property 'trackingNumber' of undefined
>     at TWScript.line7(ValidateShipment:7)
> ------End of DE processing------
> ```

**What to expect:** A diagnosis report that reads the `Caused by:` chain bottom-up to identify the deepest root exception (`TWException` on `trackingNumber` at line 7 of `ValidateShipment`), uses `threadId 000000b2` as the correlation key for searching companion log files, and provides null-guard remediation steps.

---

### Instance mode — MCP connected, retrieve errors and details

**Prompt:**
> Process instance 7743 is stuck in an error state. The workflow-runtime-mcp-server is connected. Can you find out what happened and show me the task history?

**What to expect:** The skill calls `get_process_instance_errors(instance_ids=7743)` to get the failing step and error code, then follows up with `get_process_details(process_instance_id=7743, task_limit=100, task_offset=0)` to retrieve instance state, business variables, and the task execution history — then produces a combined diagnosis report.

---

### Instance mode — completed instance, no active error

**Prompt:**
> I got an alert about process instance 5201 being in a failed state, but it looks like it might have finished. Can you check via MCP?

**What to expect:** The skill calls `get_process_instance_errors` and `get_process_details`; if `state` is `STATE_FINISHED` or `executionState` is `Completed`, it reports the instance completed normally and there is no active runtime error record — avoiding a false alarm.

---

### Instance mode — REST fallback, no MCP server

**Prompt:**
> Instance BPDInstance.5510 of our leave request workflow has been in error state for two hours. The MCP server isn't set up. My BAW server is at https://baw.internal:9443. What can you find out?

**What to expect:** The skill asks for credentials, runs `POST /ops/system/login` via `curl` to obtain a session, then executes `PUT /rest/bpm/wle/v1/process/errors?instanceIds=5510` and `GET /rest/bpm/wle/v1/process/5510?parts=all&taskLimit=100&taskOffset=0` — all directly itself — and produces a diagnosis report from the structured response, or explains exactly what log content to paste if the server is unreachable.

---

### File mode — locally accessible log file

**Prompt:**
> My SystemOut.log is at `/opt/IBM/WebSphere/AppServer/profiles/AppSrv01/logs/server1/SystemOut.log` and I've been seeing errors since about 2:30pm. Can you check it?

**What to expect:** The skill reads the file (last 200 lines first, expanding the window if needed), states exactly which lines it analyzed, and produces a diagnosis report — or clearly says the path is inaccessible and asks you to paste the relevant section.

---

### Live-log mode — Liberty MCP fetch

**Prompt:**
> Something's wrong on the BAW server right now. The MCP server is connected. Can you pull the live logs and see what's happening?

**What to expect:** The skill calls `get_baw_server_logs` to fetch the live `messages.log` directly from BAW, then analyses the content and produces a diagnosis report — or explains why the endpoint is unavailable (not Liberty, HTTP 404, or insufficient privileges) and asks you to paste the log content instead.

---

### Live-log mode — REST path, no MCP

**Prompt:**
> No MCP server set up, but my BAW server is at https://baw.internal:9443. Can you pull the live logs from it directly?

**What to expect:** The skill asks for credentials, logs in via `POST /ops/system/login` using `curl`, then calls `GET /ops/std/bpm/logs` — falling back gracefully with an explanation if the endpoint returns 404 (not wired on this release), 403 (admin rights needed), or an empty body (non-Liberty server).

---

### Container environment — JSON logs via kubectl

**Prompt:**
> Our BAW is running on OpenShift (CP4BA). I'm seeing errors in the pod logs. Here's the relevant kubectl output from the baw-pod-0 pod — can you diagnose it?
>
> ```json
> {"ibm_datetime":"2025-04-02T10:15:03.412+0000","loglevel":"ERROR","ibm_threadId":"000000c1","module":"com.ibm.bpm.bpdengine","ibm_messageId":"CWTBG0019E","message":"The instanceId parameter is missing or not valid.","ibm_hostName":"baw-pod-0","type":"liberty_message"}
> {"ibm_datetime":"2025-04-02T10:15:03:415+0000","loglevel":"ERROR","ibm_threadId":"000000c1","module":"com.ibm.bpm.bpdengine","ibm_messageId":"FFDC1015I","message":"An FFDC Incident has been created: \"com.ibm.bpm.bpdengine.BPDEngineException ...\" at defaultServer_000000c1_25.04.02_10.15.03_0.txt","ibm_hostName":"baw-pod-0","type":"liberty_message"}
> ```

**What to expect:** A diagnosis that reads the JSON log format correctly (using `ibm_threadId` `000000c1` for correlation, `ibm_messageId` for the error code, `ibm_hostName` to identify the pod), explains `CWTBG0019E`, names the FFDC file to retrieve from `/logs/ffdc/` inside `baw-pod-0`, and advises how to retrieve it with `kubectl exec` or `kubectl cp`.

---

### Event Manager — stuck timer or receive task

**Prompt:**
> We have a receive task in our order fulfillment process that's been stuck for hours — no error visible on the instance, but the process isn't moving. Instance ID is 6612.

**What to expect:** The skill calls `GET /ops/std/bpm/event_manager_tasks?states=on_hold&process_id=6612&optional_parts=message` (REST) or the equivalent MCP tool, extracts the serialised event payload from the `message` field, and uses the exception text inside it to diagnose the stuck receive task — explaining the difference between an Event Manager task failure and a process instance error.

---

### Auth failure — LDAP or token error

**Prompt:**
> Users are getting authentication errors trying to reach the BAW portal. I see these lines in messages.log:
>
> ```
> [01/Apr/2025 08:44:11:200 UTC] 00000031 com.ibm.ws.security W CWWKS4000E: Authentication did not succeed for user ID admin. An invalid user ID or password was specified.
> [01/Apr/2025 08:44:12:301 UTC] 00000031 com.ibm.ws.security W CWWKS5207W: The token has expired.
> ```

**What to expect:** A diagnosis that identifies `CWWKS4000E` as an LDAP misconfiguration or wrong bind credentials and `CWWKS5207W` as a token lifetime or clock-skew issue, with concrete remediation steps (verify LDAP bind user, check `server.xml` LDAP config, increase token expiry, synchronise system clocks) and the trace string to enable for deeper investigation (`com.ibm.ws.security.=all`).

---

### Database / connection pool error

**Prompt:**
> Our BAW processes are grinding to a halt. The SystemOut.log is full of these:
>
> ```
> [02/Apr/2025 14:30:05:111 UTC] 00000044 com.ibm.ws.rsadapter E CWWKC0301E: A JDBC data source connection pool has run out of connections.
> [02/Apr/2025 14:30:05:210 UTC] 00000045 com.ibm.db2.jcc.am E SQLCODE=-911, SQLERRMC=2; Error: DEADLOCK
> ```

**What to expect:** A diagnosis explaining connection pool exhaustion (`CWWKC0301E`) and DB2 deadlock (`SQLCODE=-911`) as related symptoms of long-running transactions holding locks, with remediation steps — review JDBC pool `maxPoolSize`, check for connection leaks in the FFDC `exception.log`, and inspect long-running BPD instances for stuck service calls.

---

### Enabling trace before reproducing a failure

**Prompt:**
> I can reproduce a failure in our purchase order process but I don't have enough detail in the current logs. How do I enable BAW trace to capture more information?

**What to expect:** The skill explains the trace specification syntax (`WLE.wle_bpd=all:com.ibm.bpm.=all:=info`), how to apply it on Liberty on-premises via `server.xml` or the admin console, and how to apply it in a CP4BA container via the `trace_specification` field in the CR — along with a reminder to disable trace after reproducing to avoid performance impact.

---

### CWLLG error — not confusing scheduler task ID with instance ID

**Prompt:**
> I'm seeing this in messages.log — is process instance 360 broken?
>
> ```
> [29/Mar/2025 10:05:11:204 UTC] 000000c4 com.ibm.bpm.eventmgr E CWLLG0181E: The following error occurred in the 360 task: com.ibm.bpm.bpdengine.ScriptException
> ```

**What to expect:** The skill explains that `360` in a `CWLLG0181E` message is an Event Manager **scheduler task ID**, not a process instance ID, and shows how to identify the actual process instance by searching for `BPDInstance.<n>` in the surrounding log lines or querying the Event Manager tasks API.

---

### Out-of-scope — live step-through debugging

**Prompt:**
> Can you step through my process execution live in Process Designer and show me what value the `orderData` variable holds at each step?

**What to expect:** The skill explains it cannot interactively step through live process execution (that requires the WebPD debugger or Process Admin Console), redirects you to the appropriate BAW tooling, and offers to analyze any log or error output you already have.
