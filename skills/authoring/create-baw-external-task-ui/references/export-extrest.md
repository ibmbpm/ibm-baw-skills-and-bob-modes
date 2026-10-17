# How to export the task schema file from IBM BAW

> **Skill:** `create-baw-external-task-ui`
>
> The task schema file is an OpenAPI specification exported from a BAW service flow.
> It defines the exact input and output fields for your human task, so the skill can
> derive the form fields precisely rather than relying on verbal descriptions. Providing
> this file is optional but strongly recommended — it eliminates ambiguity about field
> names, types, and which fields are read-only vs editable.

---

## Overview

BAW human tasks configured with a Custom URL use an **External Service** with an
**External Implementation** to define their interface. The interface is a service flow
you create in Process Designer / Business Automation Studio. You expose that service flow
as a REST endpoint and download its OpenAPI specification — the task schema file.

The skill derives form fields from `components/schemas/ioSpec_input` and
`components/schemas/ioSpec_output` in the downloaded spec. **Name the service flow
operation `ioSpec`** so the exported schema uses these key names.

---

## Steps

### 1. Create a service flow with the `ioSpec` operation

**Traditional BAW — Process Designer:**

1. Open your process application in Workflow Center and click **Open in Designer**.
2. In the left palette, click **+** next to **Services** and select **Service Flow**.
3. Name the service flow descriptively (e.g. `ManagerApprovalIO`).
4. In the service flow, rename the default operation to **`ioSpec`** exactly.
5. Add **input variables** to the `ioSpec` operation to match the data your human task
   receives from the BAW process (these become the read-only display fields in the UI).
6. Add **output variables** to the `ioSpec` operation to match the data the user fills
   in and submits back (these become the editable form fields).

**CP4BA — Business Automation Studio (BAStudio):**

1. Open **Business Automation Studio** and open your process application.
2. In the left palette, click **+** next to **Services** and select **Service Flow**.
3. Name the service flow descriptively (e.g. `ManagerApprovalIO`).
4. In the service flow, rename the default operation to **`ioSpec`** exactly.
5. Add **input variables** and **output variables** as above.

> **Tip:** Variable names and types must exactly match the human task's interface
> variables. Open the human task in Process Designer / BAStudio to verify — any mismatch
> causes data binding errors at runtime.

### 2. Expose the service flow as a REST endpoint

**Traditional BAW — Process Designer:**

1. Open the service flow and go to the **Overview** tab.
2. Under **Exposed As**, select **REST service**.
3. Check the box to expose the service flow externally.
4. Save the service flow.
5. In **Workflow Center**, create a snapshot of the process application so the REST
   endpoint becomes accessible. On Workflow Server, the endpoint is available once
   the snapshot is deployed and activated.

**CP4BA — Business Automation Studio:**

1. Open the service flow and go to the **Overview** tab.
2. Under **Exposed As**, select **REST service**.
3. Check the box to expose the service flow externally.
4. Save the service flow.
5. In **Business Automation Studio**, create a snapshot (or publish the current version)
   so the REST endpoint becomes accessible.

### 3. Navigate to the REST API Explorer

**Traditional BAW:**

1. In a browser, navigate to:
   ```
   https://<your-baw-server>:9443/bpm/explorer/?url=/bpm/docs
   ```
2. The BAW REST API Explorer opens. Under **User-Defined Services**, locate the
   endpoint for your service flow. It will appear as:
   ```
   POST /automationservices/rest/{container}/{service_flow_name}
   ```
   where `{container}` is your process application acronym and `{service_flow_name}`
   is the name of your service flow.

**CP4BA — Business Automation Studio:**

1. In a browser, navigate to:
   ```
   https://<your-cpd-host>/bas/bpm/explorer/?url=/bpm/docs
   ```
   Replace `<your-cpd-host>` with your CP4BA Cloud Pak for Data host (e.g.
   `cpd-cp4ba.apps.mycluster.example.com`).
2. The REST API Explorer opens. Under **User-Defined Services**, locate the
   endpoint for your service flow — the path format is the same as traditional BAW.

### 4. Download the OpenAPI specification

**Option A — From the REST API Explorer:**
1. In the API Explorer, locate your service flow endpoint.
2. Click the endpoint name to expand it.
3. Look for a **Download** or **Export OpenAPI** link, or navigate directly to:
   ```
   https://<your-baw-server>:9443/automationservices/rest/{container}/openapi.json
   ```
4. Save the file as `task-schema.json` (or any name you prefer) in your working folder.

**Option B — Direct URL:**
```
https://<your-baw-server>:9443/automationservices/rest/{container}/{service_flow_name}/openapi.json
```
Replace `{container}` with your process application acronym and `{service_flow_name}`
with the name of your service flow (URL-encoded if it contains spaces, e.g.
`REST%20service` for a flow named `REST service`). This URL returns the OpenAPI
specification directly. Save it with any name — `task-schema.json` is a good default.

> **Note on self-signed certificates (traditional BAW):** If your BAW server uses a
> self-signed SSL certificate, accept it in the browser or use `curl -k`:
> ```bash
> curl -k -u "username:password" \
>   "https://<your-baw-server>:9443/automationservices/rest/<container>/<service_flow_name>/openapi.json" \
>   -o task-schema.json
> ```
>
> **CP4BA:** Use a Bearer token instead of Basic Auth:
> ```bash
> curl -k -H "Authorization: Bearer <zen-token>" \
>   "https://<your-cpd-host>/bas/automationservices/rest/<container>/<service_flow_name>/openapi.json" \
>   -o task-schema.json
> ```

---

### 5. Associate the External Implementation URL with the User Task

To configure the User Task in BAW Process Designer / BAStudio to open your external UI:

1. Open your process model and select the **User Task** activity on the canvas.
2. In the properties panel, switch to the **Implementation** tab.
3. Change the **Implementation type** to **External Implementation** (or **Custom URL**).
4. In the **External URL** / **URL Template** field, enter:
   ```
   http://localhost:3000/?taskId={tw.system.task_id}
   ```
   - `{tw.system.task_id}` is a runtime token substituted by BAW with the current numeric task ID.
   - For remote deployments, replace `localhost:3000` with the public host where the app is accessible to end users.
5. Save the process application and create a **Snapshot** to deploy the changes.

> ⚠️ **Deprecation notice (BAW 26.x):** The External Implementation property on user tasks is deprecated in BAW 26.x. It remains fully supported for backward compatibility; for 26.x+ IBM recommends modern task completion SPAs communicating over standard REST APIs.

---

## What the file should look like

A valid task schema file for an external task UI has this structure:

```json
{
  "openapi": "3.0.1",
  "info": { "title": "...", "version": "1.0.0" },
  "paths": {
    "/ioSpec": {
      "post": { ... }
    }
  },
  "components": {
    "schemas": {
      "ioSpec_input": {
        "type": "object",
        "properties": {
          "fieldName": { "type": "string", "description": "..." },
          "@metadata": { "type": "object", "description": "Metadata (hidden)" }
        }
      },
      "ioSpec_output": {
        "type": "object",
        "properties": {
          "approved":      { "type": "boolean" },
          "justification": { "type": "string" }
        },
        "required": ["approved"]
      }
    }
  }
}
```

Key points:
- `ioSpec_input` properties → read-only display fields (data from the BAW process)
- `ioSpec_output` properties → editable form fields (data the user submits)
- `@metadata` fields → always filtered out; never shown in the UI
- `required` array on `ioSpec_output` → marks which output fields are mandatory

---

## Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| API Explorer shows no user-defined services | Service flow not exposed as REST, or no snapshot created/published | Expose as REST service and create or publish a snapshot |
| CP4BA API Explorer returns 404 | Wrong base path | Use `/bas/bpm/explorer/` (not `/bpm/explorer/`) for CP4BA |
| `ioSpec_input` / `ioSpec_output` missing from schema | Operation not named `ioSpec` | Rename the operation exactly to `ioSpec` in the service flow |
| Schema shows `$ref` pointers instead of fields | Schema uses `$ref` internally | Provide the raw downloaded JSON — the skill resolves `$ref` references automatically via `/api/schema` |
| 401 on the openapi.json URL (traditional BAW) | Missing credentials | Add `-u "username:password"` to curl, or log in to the BAW server first |
| 401 / 403 on the openapi.json URL (CP4BA) | Basic Auth not accepted | Use a Bearer token — obtain from `POST https://<cpd-host>/icp4d-api/v1/authorize` |
| SSL certificate error | Self-signed cert | Use `curl -k` or accept the cert in the browser |
