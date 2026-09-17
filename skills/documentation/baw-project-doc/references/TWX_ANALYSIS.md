# TWX file analysis guide

A `.twx` file is a BAW process application or toolkit export. It is a ZIP archive
analyzable offline — no live server connection required.

---

## TWX file structure

A TWX is a ZIP archive. Modern BAW (≥ 8.6.x / CP4A) uses a **flat objects layout**:

```
<AppName>.twx  (ZIP)
├── META-INF/
│   ├── package.xml          — authoritative: app name, acronym, snapshot, toolkit deps, object index
│   ├── MANIFEST.MF          — legacy only; typically empty in modern exports
│   └── metadata.xml         — minimal; not used for extraction
├── objects/
│   ├── <prefix>.<uuid>.xml  — one file per artifact, type identified by XML root-child tag
│   └── ...
├── files/
│   └── <asset-id>/...       — binary managed assets (images, ZIPs, CSS)
└── toolkits/
    └── <id>.zip             — toolkit snapshots referenced as dependencies
```

### Flat layout: numeric prefix → artifact type

The numeric prefix in the filename (`1.`, `2051.`, `61.`, etc.) is **not reliable** as
a type discriminator — use the XML root-child tag instead. The `package.xml` `<objects>`
section provides the definitive `type` attribute for every object ID.

---

## Legacy subfolder layout (BAW ≤ 8.5 / older exports)

Some older TWX exports use subfolders instead of the flat layout:

```
objects/
├── process/                 — BPD definitions
├── service/                 — Integration / Ajax / General System Service XML
├── human-service/           — Client-Side Human Service XML
├── heritage-human-service/  — Heritage Human Service XML
├── business-object/         — Business Object type definitions
└── coach-view/              — Coach View (widget) definitions
```

The extraction script handles both layouts automatically.

---

## META-INF/package.xml (primary metadata source)

Always read `package.xml` first. `MANIFEST.MF` is typically empty in modern exports.

```xml
<p:package buildVersion="8.6.11" ...>
  <target>
    <project name="MyApp" shortName="MA" isToolkit="false" .../>
    <branch name="Main" .../>
    <snapshot name="v1" acronym="V1" .../>
  </target>
  <dependencies>
    <dependency ...>
      <project name="System Data" shortName="TWSYS" isToolkit="true"/>
      <snapshot name="8.6.0.0_TC" .../>
    </dependency>
  </dependencies>
  <objects>
    <object id="1.<uuid>" type="process"   name="MyProcess"/>
    <object id="2051.<uuid>" type="restService" name="MyAPI"/>
    ...
  </objects>
</p:package>
```

**Critical:** Only read `<project>` from the `<target>` section for the app name.
Toolkit `<project>` elements appear inside `<dependencies>/<dependency>` and must
not overwrite the app identity.

---

## Artifact types and XML root tags

| XML root-child tag       | Meaning                               | Key data source |
|--------------------------|---------------------------------------|-----------------|
| `process`                | BPD or service flow (see processType) | `<processType>` child + `<jsonData>` |
| `restService`            | REST API exposure definition          | `<jsonData>` |
| `webService` / `soapService` | SOAP web service reference        | `<jsonData>`, `<wsdlUrl>` |
| `businessObject`         | Business Object type definition       | `<jsonData>` or XML children |
| `businessObjectType`     | Alternate BO root tag (older format)  | XML children |
| `coachView`              | Coach View (widget) definition        | `<jsonData>` |
| `environmentVariableSet` | Environment variables set             | `<jsonData>` |
| `managedAsset`           | Binary file (image, ZIP, CSS)         | Skip — no documentation value |
| `projectDefaults`        | Process App Settings                  | Skip |
| `participantGroup`       | Participant/lane group                | Skip |

### processType integer mapping (for `<process>` artifacts)

| processType | Meaning |
|---|---|
| 0 | BPD (Business Process Definition) |
| 1 | Integration Service |
| 2 | Ajax Service |
| 3 | General System Service |
| 4 | Heritage Human Service |
| 5 | Decision Service |
| 6 | External Implementation |
| 7 | Event Sub-Process |
| 8–9 | Case Activity |
| 10–11 | Client-Side Human Service |
| 12 | Service Flow (Ajax-exposed microflow) |
| 13 | Service Flow (non-Ajax microflow) |
| 14 | REST Service Flow |
| 15 | External Service |

Additionally check the `otherAttributes` in `jsonData.rootElement[0]` for:
- `executionMode`: if present and set to `"microflow"`, treat as a service flow; if absent, treat as a BPD. This is an observed field — use it as a heuristic, not a guaranteed discriminator.

---

## jsonData parsing (primary data container)

All flow logic, variables, and parameters live inside the `<jsonData>` child element
as an **escaped JSON string**, not as XML child elements. Always parse `jsonData` first.

```python
import json, xml.etree.ElementTree as ET

root = ET.parse(xml_path).getroot()
art_el = list(root)[0]           # the artifact element inside <teamworks>
jd_el = art_el.find("jsonData")
jd = json.loads(jd_el.text)      # dict with rootElement, operations, etc.
```

### jsonData structure for process / service flow

```
jd["rootElement"][0]
  ├── name                        — process / service name
  ├── documentation[]             — description entries
  ├── laneSet[].lane[]            — swimlanes with name, isSystemLane, flowNodeRef[]
  ├── flowElement[]               — all BPMN elements (tasks, events, gateways, flows)
  │   ├── declaredType            — "startEvent", "userTask", "scriptTask", etc.
  │   ├── name
  │   ├── id
  │   ├── incoming[] / outgoing[] — sequence flow IDs
  │   └── extensionElements       — visual info, implementation refs
  ├── ioSpecification
  │   ├── dataInput[]             — input parameters (name, itemSubjectRef, isCollection)
  │   └── dataOutput[]            — output parameters
  ├── property[]                  — BPD private variables
  └── otherAttributes             — executionMode, etc.
```

### flowElement declaredType → readable step type

| declaredType | Type |
|---|---|
| `startEvent` | Start Event |
| `endEvent` | End Event |
| `userTask` | Human Task |
| `serviceTask` | Service Task |
| `scriptTask` | Script Task |
| `callActivity` | Sub-Process / Call Activity |
| `subProcess` | Embedded Sub-Process |
| `exclusiveGateway` | Exclusive Gateway |
| `inclusiveGateway` | Inclusive Gateway |
| `parallelGateway` | Parallel Gateway |
| `boundaryEvent` | Boundary Event |
| `intermediateCatchEvent` | Intermediate Catch Event |

### Variable / parameter extraction

1. **Input parameters** — `ioSpecification.dataInput[]` → `isInput: true`
2. **Output parameters** — `ioSpecification.dataOutput[]` → `isOutput: true`
3. **Private BPD variables** — `property[]` in `rootElement[0]`
4. **Data objects** (older format) — `dataObject[]` in `rootElement[0]`

The `itemSubjectRef` field holds a type reference in the form `itm.<num>.<uuid>`. Strip
the `itm.<num>.` prefix to surface the UUID. If the UUID resolves to an artifact in the
same TWX, it's a local BO reference. If not, it's defined in a toolkit dependency.

### jsonData structure for restService

```
jd
  ├── name
  ├── description
  ├── operations[]
  │   ├── name
  │   ├── interactionPattern    — "1"=REQUEST_RESPONSE_SYNC, "2"=REQUEST_ONLY
  │   └── implementation        — ID of the backing process/service flow
  └── openAPIDefinitionURLTemplate
```

---

## Artifact types and what to extract

### BPDs (processType = 0)

Extract from `jsonData.rootElement[0]`:
- Process name and description
- Swimlane names (from `laneSet[].lane[].name`) and whether each is a system lane
- All `flowElement` entries: name, `declaredType` (mapped to step type), lane (resolved
  via `lane.flowNodeRef`), description from `documentation[]`
- Sequence flows: source → target, optional label
- Gateways: type, outgoing branch labels
- Boundary events: type (timer / error / escalation), `attachedToRef`, `isInterrupting`
- Timers: boundary events where `eventDefinition` contains `timerEventDefinition`
- Variables: from `ioSpecification.dataInput`, `dataOutput`, `property[]`, `dataObject[]`

### Service flows / Integration Services / etc.

Same structure as BPDs. Key differences:
- No human tasks (all lanes are typically `isSystemLane: true`)
- Parameters via `ioSpecification.dataInput` / `dataOutput`
- Endpoints may appear as extension attributes in individual step `flowElement` entries

### REST service definitions (`restService`)

- Name, description
- Operations: name, interaction pattern, backed-by service flow name (resolve `implementation` ID via objectIndex)
- OpenAPI URL template (clean up `{SNAPSHOT_START:...:SNAPSHOT_END}` placeholders)

### SOAP / web services (`webService`, `soapService`)

- Name, description
- `wsdlUrl` / `wsdlLocation` child element
- Operations from `jsonData.operations` or `jsonData.portTypeOperation`

### Business Objects (`businessObject`, `businessObjectType`)

- Modern format: `jsonData.businessObjectType[]` → fields from `parameter[]` / `field[]`
- Legacy format: XML children tagged `<parameter>`, `<field>`, or `<property>`
- Extract: field name, type, isCollection/isList, isRequired, description

### Coach Views (`coachView`)

- `jsonData.configOption[]` → exposed configuration properties (name, type, description)
- `jsonData.eventHandler[]` → event handler names (load, change, view, validate, etc.)
- `jsonData.binding[]` → bound business object types

### Environment Variables (`environmentVariableSet`)

- `jsonData.variable[]` or `jsonData.environmentVariable[]`
- Extract: name, type, default value, description

---

## XML parsing approach

All TWX object files use `<teamworks>` as root, wrapping the artifact element:

```python
import xml.etree.ElementTree as ET

root = ET.parse(xml_path).getroot()   # <teamworks>
art_el = list(root)[0]                # the artifact element (e.g. <process>, <restService>)
art_tag = art_el.tag                  # use this to dispatch to the right parser
```

No namespace prefix needed for direct attribute access. Namespace-aware XPath is only
required if querying nested elements that carry the `lombardi/7.5` namespace, which
does not apply to `jsonData`-based parsing.

---

## Error handling

- Log a warning for each unreadable or malformed file (name + reason).
- Continue processing remaining artifacts — one bad file must not abort the full run.
- Include a "Skipped artifacts" note in the documentation output listing what was
  skipped and why.
- Unknown XML root-child tags should be logged to `skipped` with the tag name so
  support can be added in the future.
