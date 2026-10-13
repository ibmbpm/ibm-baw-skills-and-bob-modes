# TWX XML structure reference

A `.twx` file is a ZIP archive. The structure documented here is based on direct inspection of real BAW TWX exports. IBM does not publish a formal XML schema for TWX internals in the public product documentation, so the dependency-mapper script uses these paths as heuristics — validate results against the actual artifacts in the specific TWX version being analyzed.

## Archive layout

```
<process-app>.twx
├── META-INF/
│   └── ibm-process-app.xml       ← app metadata (name, version, toolkit dependencies)
├── objects/
│   └── <uuid>/
│       └── <artifact>.xml        ← one XML file per artifact
└── snapshots/
    └── <snapshot-id>/            ← present only on snapshot exports
```

All artifact XML files live under `objects/`. Each file contains **one** artifact.

## Root element

Every artifact XML file has `<teamworks>` as its root element — not the artifact type. The artifact itself is a **direct child** of `<teamworks>`:

```xml
<teamworks>
  <twClass name="ClaimRequest">   ← artifact child element
    …
  </twClass>
</teamworks>
```

## Child element tags by artifact type

| Artifact type                  | Child element tag |
|--------------------------------|-------------------|
| Business Object (BO)           | `twClass`         |
| BPD (heritage process)         | `bpd`             |
| Service flow / CSHS / General  | `process`         |

`<process>` elements are disambiguated by their `<processType>` child text:

| `processType` value | Meaning                                     |
|---------------------|---------------------------------------------|
| `10`                | Client-Side Human Service (CSHS) — has coach UI |
| `12`                | Service flow / General system service       |
| `13`                | Deployment service — skipped by the analyser |

## Business Object (`<twClass>`)

BO field definitions are stored in **XML** child elements, not JSON:

```xml
<teamworks>
  <twClass name="ClaimRequest">
    <classId>12.bac3e1d1-a533-422b-b17e-5d8b24622dac</classId>
    <definition>
      <property>
        <name>claimId</name>
        <classRef>String</classRef>
      </property>
      <property>
        <name>amount</name>
        <classRef>Decimal</classRef>
      </property>
      <property>
        <name>claimant</name>
        <classRef>/12.023fa9af-0a39-42fb-8e4c-2f8d4b7c1e88</classRef>  ← BO reference
      </property>
    </definition>
  </twClass>
</teamworks>
```

Key points:
- `<classId>` gives the BO's unique identifier in the form `12.<uuid>`. Used to resolve `itemSubjectRef` cross-references from variable declarations.
- Field type in `<classRef>` is a **plain string** for primitives (`String`, `Decimal`, `Boolean`, etc.) or a **path ending in a UUID** for BO references (e.g., `/12.<uuid>` or `01f32839-.../12.db884a3c-...`).
- The analyser builds the BO type graph by extracting non-primitive `<classRef>` values and resolving them to BO names via the `classId` index.

## Process flows (`<bpd>` and `<process>`)

Flow data is stored as **JSON** inside a `<jsonData>` child element. There are no XML child elements for activities, variables, or sequence flows — they are all inside the JSON blob.

```xml
<teamworks>
  <process name="ValidateClaim" processType="12">
    <processType>12</processType>
    <jsonData>{"rootElement":[{"flowElement":[…]}],"ioSpecification":{…}}</jsonData>
  </process>
</teamworks>
```

### Variable declarations in JSON

Variables are `flowElement` entries with `"declaredType": "dataObject"`:

```json
{
  "declaredType": "dataObject",
  "name": "claimRequest",
  "itemSubjectRef": "itm.12.bac3e1d1-a533-422b-b17e-5d8b24622dac"
}
```

`itemSubjectRef` uses `itm.12.<uuid>` form — resolved to a BO name via the `classId` index built from `<twClass>` files.

### Script tasks in JSON

```json
{
  "declaredType": "scriptTask",
  "name": "Set Status",
  "id": "bf4c8a12-...",
  "script": {
    "content": ["tw.local.claimRequest.status = \"Approved\";"]
  }
}
```

### Sequence flows in JSON

```json
{
  "declaredType": "sequenceFlow",
  "sourceRef": "bf4c8a12-...",
  "targetRef": "c72d9f3e-..."
}
```

### Service I/O parameters

Found in `ioSpecification` at the top level of the JSON (or inside `rootElement[0]`):

```json
{
  "ioSpecification": {
    "dataInput": [
      { "name": "claimRequest", "itemSubjectRef": "itm.12.bac3e1d1-..." }
    ],
    "dataOutput": [
      { "name": "result", "itemSubjectRef": "itm.12.db884a3c-..." }
    ]
  }
}
```

### Coach bindings (CSHS)

Coach bindings appear inside `formDefinition` within CSHS flow elements. The analyser recurses through the nested `coachDefinition.layout.layoutItem[]` structure looking for `"binding"` keys:

```json
{
  "formDefinition": {
    "coachDefinition": {
      "layout": {
        "layoutItem": [
          {
            "binding": "tw.local.claimRequest.claimId"
          }
        ]
      }
    }
  }
}
```

Binding paths use the **variable name**, not the BO type name. The analyser matches the target (bare or qualified) anywhere in the binding string.

## Script analysis heuristics

Script scanning matches the target name by whole-word, case-insensitive comparison. This means a search for `ClaimRequest` detects `tw.local.ClaimRequest.status` but not `tw.local.claim.status` — the variable name `claim` does not match the type name.

For complete variable-level tracing, use the Declarations section to identify variable names of the target type, then re-run the analysis for each variable name.

## What the script does NOT parse

- Binary or image files inside the TWX.
- `META-INF/ibm-process-app.xml` — used only for archive identification, not artifact scanning.
- Toolkit dependency objects — only artifacts in the current process app (under `objects/`) are scanned. Cross-toolkit usages are outside the static analysis boundary.
- `<process processType="13">` deployment service flows — intentionally skipped.
