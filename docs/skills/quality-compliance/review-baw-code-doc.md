# Review BAW Code — Documentation

> Perform automated, severity-ranked code quality reviews across IBM® BAW artifacts — server scripts, coach (client-side) scripts, integration service scripts, HTML, CSS, and optionally a Checkstyle XML report.

## Purpose

This skill scans JavaScript artifacts extracted from a BAW TWX application and produces a severity-ranked findings report. It is designed for BAW developers who want to catch real issues before deployment — hardcoded credentials and URLs that break across environments, undeclared `tw.local.*` variables, inconsistent or silenced error logging, and performance anti-patterns like synchronous `Thread.sleep` or unbounded loops. Use it whenever you want a structured code quality review of one or more BAW scripts, coach views, or an entire TWX project.

## Setup and configuration

- No special setup required for reviewing pasted scripts, uploaded files, or Checkstyle XML.
- To review a `.twx` file, upload it directly in the chat. The skill will unzip it automatically using the system shell — no additional tools needed on your part.
- To review an already-extracted TWX directory, point the skill at the folder path on disk.

## Compatibility

- No known compatibility constraints. The skill reviews BAW artifacts at the script level and does not require a specific BAW server version.

> **Note:** Credentials shown in prompt examples are for illustration only. Never use real production credentials in prompts. Use environment variables or a secrets manager for sensitive values.

## Prompt examples

### Review a pasted server script

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

**What to expect:** A severity-ranked report flagging the hardcoded credential as Critical (HARD-01), the hardcoded hostname as High (HARD-02), the hardcoded port as Medium (HARD-04), the empty catch block as High (QUAL-01), and the bare `console.log` as Low (LOG-03), each with a recommended fix and a summary table.

---

### Review an uploaded .twx file

**Prompt:**
> I'm uploading my BAW process app before the next deployment. Please review all scripts in it for code quality issues.

*(Attach your `.twx` file to the chat message.)*

**What to expect:** The skill extracts the TWX archive automatically, scans all `.js`, `.html`, and `.css` artifacts it finds, and delivers a full severity-ranked report covering every artifact with a summary table and Top 3 recommendations.

---

### Review an extracted TWX directory

**Prompt:**
> Review all scripts under `/Users/dev/projects/LoanApp/extracted-twx` for hardcoded values, variable issues, and performance anti-patterns.

**What to expect:** The skill lists all files it discovers, reads each one, and returns a consolidated findings report grouped by severity across all artifacts.

---

### Ingest a Checkstyle XML report

**Prompt:**
> Here is the Checkstyle report from our CI pipeline — please map it to BAW rule IDs and give me a severity-ranked report:
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

**What to expect:** All three Checkstyle findings are mapped to BAW rule IDs (QUAL-01, PERF-01, HARD-04), re-ranked by BAW severity, and presented in the standard grouped report with a "Checkstyle findings ingested: 3" header line.

---

### Add custom rules to the review

**Prompt:**
> Review the scripts in `/Users/dev/projects/ClaimsApp/extracted-twx`. In addition to the default rules, also flag any call to `tw.system.findUser` and treat any `DEBUG`-level log call as High severity.

**What to expect:** The skill applies all default rules plus your two custom rules, explicitly stating which custom rules were added, and includes findings for any `tw.system.findUser` calls or DEBUG-level log calls in the final report.

---

### Iterative re-review after fixes

**Prompt:**
> I've fixed the Critical and High issues from your last review. Here is the updated version of `ProcessOrder.js`:
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

**What to expect:** The skill compares this version against any previous findings in the conversation, reports which issues were resolved and which remain, and flags any newly introduced issues, with a delta summary (e.g., "2 of 4 previous issues resolved; 0 new issues introduced").

---

### Out-of-scope request — process flow modeling

**Prompt:**
> Can you review my BPMN process flow and suggest improvements to the gateway logic?

**What to expect:** The skill explains that BPMN process flow modeling is outside its scope and directs you to the `generate-baw-bpmn` skill for that task.

---

### Out-of-scope request — runtime process inspection

**Prompt:**
> Can you check whether any running process instances are stuck in the Approval step right now?

**What to expect:** The skill explains that runtime process inspection is handled by the `inspect-baw-processes` skill and redirects you there.
