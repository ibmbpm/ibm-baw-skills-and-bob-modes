# Review BAW code — documentation

> Perform automated, severity-ranked code quality reviews across IBM BAW artifacts — server scripts, coach (client-side) scripts, integration service scripts, HTML, CSS, and optionally a Checkstyle XML report.

## Purpose

This skill scans JavaScript artifacts extracted from a BAW TWX application and produces a severity-ranked findings report. BAW developers use it to catch real issues before deployment — hardcoded credentials and URLs that break across environments, undeclared `tw.local.*` variables, inconsistent or silenced error logging, and performance anti-patterns like synchronous `Thread.sleep` or unbounded loops. Use it whenever you want a structured code quality review of one or more BAW scripts, coach views, or an entire TWX project.

## Setup and configuration

- No special setup required for reviewing pasted scripts, uploaded files, or Checkstyle XML.
- The preferred way to supply a TWX is through the **REST export API**: provide your BAW server URL, container acronym, snapshot version, and credentials. The skill logs in, downloads the TWX, and extracts it automatically. This method works for on-premises BAW and CP4BA.
- If server access is unavailable, you can upload the `.twx` file directly or point the skill at a path on disk as a fallback. The skill offers this option only after the REST export has visibly failed — not pre-emptively.
- To review an already-extracted TWX directory or paste scripts directly, point the skill at the folder or paste the content — no TWX or server connection needed.

## Compatibility

- This skill has no known compatibility constraints. The skill reviews BAW artifacts at the script level and does not require a specific BAW server version.

## Prompt examples

### Review a pasted server script

> **Note:** The following script is an intentionally bad example used to demonstrate the HARD-01 (hardcoded credential) detection rule. Do not use this pattern in real scripts.

**Prompt:**
> Review this BAW server script for code quality issues:
>
> ```js
> // Notify Customer script
> var smtpHost = "mail.corp-internal.example.com";
> var smtpPort = 587;
> var smtpPassword = "Welc0me1!";
>
> try {
>     var msg = new JavaMail();
>     msg.send(smtpHost, smtpPort, smtpPassword, tw.local.customerEmail, tw.local.messageBody);
>     tw.local.notificationSent = true;
> } catch(e) {
> }
>
> console.log("Notification script done");
> ```

**What to expect:** The skill returns a severity-ranked report flagging the hardcoded credential as Critical (HARD-01), the hardcoded hostname as High (HARD-02), the hardcoded port as Medium (HARD-04), the empty catch block as High (QUAL-01), and the bare `console.log` as Low (LOG-03), each with a recommended fix and a summary table.

---

### Review a live process app through REST export (preferred)

> **Note:** Replace the placeholder values with your own. Do not share production credentials in prompts.

**Prompt:**
> Review the BAW code for process app `HSS`, snapshot `0.1` on `https://baw.example.com:9443/`. Credentials: `<user>` / `<password>`.

**What to expect:** The skill logs in to obtain a CSRF token, calls `GET /ops/std/bpm/containers/HSS/versions/0.1/export?use_enhanced_filenames=true` to download the TWX, extracts it, then scans all `.js`, `.html`, and `.css` artifacts it finds. The skill returns a full severity-ranked report with a summary table and Top 3 recommendations — no file upload needed.

---

### Review a process app — snapshot unknown

**Prompt:**
> I want to do a code review of the `HSS` process app on `https://baw.example.com:9443/` (`<user>`/`<password>`) but I am not sure what snapshot version to use.

**What to expect:** The skill lists available snapshots through the containers API, lets you pick one, then proceeds with the REST export and review.

---

### Review a locally uploaded or on-disk .twx file (fallback)

**Prompt:**
> Review my BAW code. I do not have server access, but here is my TWX file: `/tmp/HSS_0.1.twx`.

**What to expect:** When you provide no server URL (or the REST export has previously failed), the skill accepts a local file path or an uploaded file, extracts the TWX archive, and delivers the full severity-ranked report. The skill does not ask for server credentials in this path.

---

### Review an extracted TWX directory

**Prompt:**
> Review all scripts under `/Users/dev/projects/LoanApp/extracted-twx` for hardcoded values, variable issues, and performance anti-patterns.

**What to expect:** The skill lists all files it discovers, reads each one, and returns a consolidated findings report grouped by severity across all artifacts.

---

### Ingest a Checkstyle XML report

**Prompt:**
> Here is the Checkstyle report from our CI pipeline. Map it to BAW rule IDs and give me a severity-ranked report:
>
> ```xml
> <?xml version="1.0" encoding="UTF-8"?>
> <checkstyle version="8.45">
>   <file name="src/scripts/CreateCase.js">
>     <error line="8" severity="error" message="Empty catch block."
>            source="com.puppycrawl.tools.checkstyle.checks.blocks.EmptyCatchBlockCheck"/>
>     <error line="22" severity="error" message="Avoid using 'Thread.sleep'."
>            source="com.puppycrawl.tools.checkstyle.checks.regexp.RegexpSinglelineCheck"/>
>     <error line="41" severity="warning" message="Magic number '9443' should be avoided."
>            source="com.puppycrawl.tools.checkstyle.checks.coding.MagicNumberCheck"/>
>   </file>
> </checkstyle>
> ```

**What to expect:** The skill maps all three Checkstyle findings to BAW rule IDs (QUAL-01, PERF-01, HARD-04), re-ranks them by BAW severity, and presents them in the standard grouped report with a "Checkstyle findings ingested: 3" header line.

---

### Add custom rules to the review

**Prompt:**
> Review the scripts in `/Users/dev/projects/ClaimsApp/extracted-twx`. In addition to the default rules, also flag any call to `tw.system.findUser` and treat any `DEBUG`-level log call as High severity.

**What to expect:** The skill applies all default rules plus your two custom rules, explicitly stating which custom rules were added, and includes findings for any `tw.system.findUser` calls or DEBUG-level log calls in the final report.

---

### Iterative re-review after fixes

**Prompt:**
> I fixed the Critical and High issues from your last review. Here is the updated version of `ProcessOrder.js`:
>
> ```js
> // ProcessOrder.js — v2
> var endpoint = tw.env.orderServiceUrl + "/process";
>
> try {
>     var conn = new XMLHttpRequest();
>     conn.open("POST", endpoint, false);
>     conn.send(JSON.stringify({ orderId: tw.local.orderId }));
>     tw.local.orderStatus = JSON.parse(conn.responseText).status;
> } catch(e) {
>     log.error("ProcessOrder failed: " + e.message, e);
> }
>
> log.info("ProcessOrder complete for order " + tw.local.orderId);
> ```

**What to expect:** The skill compares this version against any previous findings in the conversation, reports which issues were resolved and which remain, and flags any newly introduced issues, with a delta summary (for example, "2 of 4 previous issues resolved; 0 new issues introduced").

---

### Out-of-scope request — process flow modelling

**Prompt:**
> Can you review my BPMN process flow and suggest improvements to the gateway logic?

**What to expect:** The skill explains that BPMN process flow modelling is outside its scope and directs you to the `generate-baw-bpmn` skill for that task.

---

### Out-of-scope request — runtime process inspection

**Prompt:**
> Can you check whether any running process instances are stuck in the Approval step right now?

**What to expect:** The skill explains that the [`inspect-baw-processes`](../../../administration-operations/inspect-baw-processes/docs/inspect-baw-processes-doc.md) skill handles runtime process inspection and redirects you there.

## Related information

- [`inspect-baw-processes`](../../../administration-operations/inspect-baw-processes/docs/inspect-baw-processes-doc.md)
