# BAW Code Review — Rule Definitions

This file is the authoritative rule reference for the `review-baw-code` skill.
For every finding you emit, look up the rule here to confirm the severity, pattern,
and fix template before writing it into the report.

---

## Severity scale

| Level | Label | Meaning |
|---|---|---|
| 1 | **Critical** | Will cause a security incident, data loss, or environment failure if deployed as-is. Fix before merging. |
| 2 | **High** | Will cause failures in non-development environments or meaningfully impair production supportability. Fix before deployment. |
| 3 | **Medium** | Degrades maintainability, reliability, or performance but will not fail immediately. Fix in the current sprint if possible. |
| 4 | **Low** | Style / consistency issue or minor code smell. Address at the next refactor opportunity. |

---

## Hardcoded value rules (HARD-*)

### HARD-01 — Hardcoded credential
**Severity:** Critical  
**Applies to:** JS (server, coach, integration)  
**Pattern:** A variable whose name contains any of `password`, `passwd`, `secret`,
`apikey`, `api_key`, `token`, `authtoken`, `auth_token`, `credential`, `private_key`
(case-insensitive) is assigned a non-empty string literal.  
```js
// Example violations
var password = "P@ssw0rd!";
var apiKey = "sk-abc123";
var dbSecret = 'prod-secret-XYZ';
```
**Fix template:** Replace the literal with a BAW managed team/environment variable
read via `tw.env.*` or a process variable initialised from a BAW configuration
property (`tw.system.findManagedFile` / config property lookup). Never store
credentials in scripts.

---

### HARD-02 — Hardcoded URL / hostname
**Severity:** High  
**Applies to:** JS, HTML  
**Pattern:** A string literal that matches `https?://[A-Za-z0-9][^ "']+` or
`ftp://[^ "']+` appears outside a comment. Environment-neutral `localhost` references
used in tests are Low, not High.  
```js
// Violation
var endpoint = "http://internal-srv.corp.example.com:8080/api/process";
```
**Fix template:** Define the base URL as a BAW server-side environment variable or
an IBM BAW environment-specific property, and read it at runtime:
```js
var endpoint = tw.env.integrationBaseUrl + "/api/process";
```

---

### HARD-03 — Hardcoded IP address
**Severity:** High  
**Applies to:** JS, HTML  
**Pattern:** A string literal that matches the regex `\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b`
(IPv4 dotted-decimal notation).  
**Fix template:** Replace with a hostname resolved via DNS, or store in an environment
variable as for HARD-02.

---

### HARD-04 — Hardcoded environment-specific port
**Severity:** Medium  
**Applies to:** JS, HTML  
**Pattern:** A string literal that ends with `:<port>` where port is not 80 or 443,
or a numeric literal assigned to a variable named `port`, `portNumber`, `serverPort`
(case-insensitive). Exempt: well-known ports (80, 443, 8080 is borderline — flag as Low).  
**Fix template:** Externalise to an environment variable or BAW configuration property.

---

## Variable discipline rules (VAR-*)

### VAR-01 — tw.local.* read before declared / assigned
**Severity:** High  
**Applies to:** JS (server, integration)  
**Pattern:** A `tw.local.<name>` reference appears as a read (right-hand side of
assignment, passed as argument, used in condition) at a line that precedes any
assignment `tw.local.<name> = ...` in the same script scope. Does not apply to
variables declared in the process model and legitimately passed into the script as
inputs — if there is any plausible input mapping, downgrade to Medium and note
"Verify this is an output variable, not a process input."  
**Fix template:** Declare and assign the variable before first use:
```js
tw.local.result = "";   // declare/initialise first
// … logic …
tw.local.result = computedValue;
```

---

### VAR-02 — tw.local.* assigned but never read (unused output)
**Severity:** Low  
**Applies to:** JS (server, integration)  
**Pattern:** A `tw.local.<name> = ...` assignment exists but `tw.local.<name>` never
appears as a read in the same script. May indicate dead code or a forgotten output
mapping.  
**Fix template:** Either remove the assignment if the variable is truly unused, or
confirm that the output is mapped in the containing service/process and the variable
is intentionally written for downstream consumption.

---

## Logging rules (LOG-*)

### LOG-01 — Inconsistent logging idiom
**Severity:** Medium  
**Applies to:** JS  
**Pattern:** Multiple logging idioms coexist across the artefact set or within a
single script. Detect the dominant idiom across all reviewed scripts (the idiom used
by >50% of log calls). Any script using a different idiom is flagged. Common idioms:
`log.info` / `log.error`, `tw.system.log`, `console.log`, a custom `logger.*` wrapper.  
**Fix template:** Standardise on the project's dominant idiom. If no convention
exists, adopt `log.info` / `log.error` from the BAW Script Logger API, which writes
to the BAW system log and supports severity levels.

---

### LOG-02 — Exception swallowed in catch block
**Severity:** High  
**Applies to:** JS  
**Pattern:** A `catch(e)` or `catch(err)` block contains a log call but does not
include the caught exception variable in the message or as a second argument. Also
matches catch blocks that are entirely empty.  
```js
// Violations
try { … } catch(e) { log.error("Something went wrong"); }   // e not logged
try { … } catch(e) { }                                        // empty catch
```
**Fix template:**
```js
try {
    …
} catch(e) {
    log.error("Operation failed: " + e.message, e);
}
```

---

### LOG-03 — Bare console.log in production script
**Severity:** Low  
**Applies to:** JS  
**Pattern:** `console.log(`, `console.warn(`, `console.error(` appear in a script
that is not clearly a test or development utility (filename does not contain `test`,
`spec`, `dev`).  
**Fix template:** Replace with the project's standard logging idiom. `console.log`
output is not captured in BAW server logs and disappears in server-side scripts.

---

## Performance rules (PERF-*)

### PERF-01 — Synchronous Thread.sleep
**Severity:** Critical  
**Applies to:** JS (server, integration)  
**Pattern:** `java.lang.Thread.sleep(`, `Thread.sleep(`, or the alias pattern
`Packages.java.lang.Thread.sleep(` appears in a script.  
**Fix template:** Remove the sleep entirely. If a delay is needed between retry
attempts, implement a BAW timer boundary event on the containing process/service task.
If polling an external system, use a BAW intermediate timer event or an integration
pattern with a callback. `Thread.sleep` blocks the BAW thread pool and can cause
server-wide thread exhaustion.

---

### PERF-02 — Unbounded loop
**Severity:** High  
**Applies to:** JS  
**Pattern:** Any of:
- `while(true)` or `while(1)` with no `break` or `return` reachable from a static
  path analysis.
- `for(;;)` with no `break` or `return`.
- A `while` or `for` loop whose condition variable is never modified inside the loop
  body.  
**Fix template:** Add an explicit iteration limit or a clear exit condition:
```js
var maxIterations = 100;
var count = 0;
while (condition && count < maxIterations) {
    // …
    count++;
}
if (count >= maxIterations) {
    log.warn("Loop reached max iterations — possible infinite loop");
}
```

---

### PERF-03 — Deeply nested loops
**Severity:** Medium  
**Applies to:** JS  
**Pattern:** Three or more `for`/`while`/`do-while` loops nested inside each other
(nesting depth ≥ 3).  
**Fix template:** Extract the inner loop(s) into a named helper function, or
reconsider the algorithm. Deeply nested loops are O(n³) or worse and are the most
common cause of BAW server timeouts on large datasets.

---

## Code quality rules (QUAL-*)

### QUAL-01 — Empty catch block
**Severity:** High  
**Applies to:** JS  
**Pattern:** `catch` block whose body contains nothing (or only whitespace/comments)
after stripping comments.  
**Fix template:** At minimum, log the exception and re-throw or set an error flag:
```js
} catch(e) {
    log.error("Unexpected error: " + e.message, e);
    throw e;
}
```
Do not silently swallow exceptions in server-side BAW scripts — they make failure
diagnosis extremely difficult.

---

### QUAL-02 — eval() call
**Severity:** Critical  
**Applies to:** JS  
**Pattern:** `eval(` appears as a function call (not in a string or comment).  
**Fix template:** Replace with explicit logic. If deserialising JSON,
use `JSON.parse(...)`. If dynamically selecting a function, use a lookup object or
`switch` statement. `eval()` is a security risk and prevents static analysis.

---

### QUAL-03 — Unreachable code after return/throw
**Severity:** Low  
**Applies to:** JS  
**Pattern:** Executable statements (not closing braces or comments) appear on lines
immediately after a `return` or `throw` statement at the same nesting level.  
**Fix template:** Remove the unreachable code. It is dead code and will never execute.

---

### QUAL-04 — Inline style attribute in HTML coach view
**Severity:** Low  
**Applies to:** HTML  
**Pattern:** `style="` or `style='` attribute on any HTML element in a BAW coach
view template.  
**Fix template:** Move the style declaration to the coach view's CSS section or to a
shared stylesheet. Inline styles bypass theming and make accessibility audits harder.

---

### QUAL-05 — !important in CSS
**Severity:** Low  
**Applies to:** CSS  
**Pattern:** `!important` appears in a CSS property value.  
**Fix template:** Increase specificity of the selector instead of using `!important`.
Overuse of `!important` makes stylesheet overrides unpredictable and breaks Carbon
Design System theming in Process Portal.

---

## Checkstyle mapping guide

When ingesting a Checkstyle XML report, map `source` class names to BAW rule IDs
using this table. If a Checkstyle source is not in the table, surface the finding
under the synthetic ID `CS-<last_segment_of_source_class>` at the Checkstyle severity.

| Checkstyle source class (suffix) | Closest BAW rule | Notes |
|---|---|---|
| `MagicNumberCheck` | HARD-04 | Hardcoded numeric constant |
| `AvoidInlineConditionalsCheck` | QUAL-03 | Code clarity |
| `EmptyCatchBlockCheck` | QUAL-01 | Direct match |
| `IllegalCatchCheck` | QUAL-01 | Catching `Throwable`/`Exception` broadly |
| `NestedForDepthCheck` | PERF-03 | Direct match |
| `NestedTryDepthCheck` | QUAL-01 | Overly complex exception handling |
| `RegexpSinglelineCheck` (pattern `Thread.sleep`) | PERF-01 | Direct match |
| `RegexpSinglelineCheck` (pattern `console.log`) | LOG-03 | Direct match |
| `UnusedImportsCheck` | VAR-02 | Treat as Low — unused import |
| `VisibilityModifierCheck` | HARD-01 | Public field may expose credential |
