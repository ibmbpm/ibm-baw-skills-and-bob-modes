# BPMN + XSD analysis guide

This guide covers parsing the output of the `generate-baw-bpmn` skill: a `.bpmn` file
(BPMN 2.0 XML in BAW's export dialect) and its companion `.xsd` (business object schema).
These files are also bundled together in a `.zip` — unzip first if the user provides a ZIP.

---

## File roles

| File | Contains |
|---|---|
| `<Name>.bpmn` | Process definition: lanes, tasks, gateways, events, sequence flows, variable I/O |
| `<Name>.xsd` | Business object type definitions with field names, types, and cardinality |
| `<Name>.zip` | Both of the above bundled for BAW import — unzip to get the two files |

---

## BPMN file structure

The BPMN uses the `bpmn:` namespace (`http://www.omg.org/spec/BPMN/20100524/MODEL`) and
BAW's own `bpmnid-` UUID identifier convention.

### Key elements to extract

**Process identity** — from `<bpmn:process>`:
- `name` attribute — the process name
- `<bpmn:documentation>` child — plain-text description

**Lanes** — from `<bpmn:laneSet>/<bpmn:lane>`:
- `name` attribute — lane/role name
- `<bpmn:flowNodeRef>` children — IDs of elements assigned to this lane

Build a lookup map: `{ elementId → laneName }` — used to assign every step to its performer.

**Tasks** — `<bpmn:userTask>` and `<bpmn:serviceTask>`:
- `name` — step name
- `<bpmn:documentation>` — step description
- `<bpmn:performer name="..."/>` — role performing this task
- `<bpmn:ioSpecification>` — `<bpmn:dataInput>` and `<bpmn:dataOutput>` with `name` and
  `itemSubjectRef` (links to a `<bpmn:itemDefinition>`)

**Gateways** — `<bpmn:exclusiveGateway>`, `<bpmn:parallelGateway>`, `<bpmn:inclusiveGateway>`:
- `name` — decision label
- `default` attribute — ID of the default outgoing flow
- `<bpmn:documentation>` — description of the decision criteria

**Events** — `<bpmn:startEvent>`, `<bpmn:endEvent>`, `<bpmn:boundaryEvent>`:
- `name` — event label
- For boundary events: `attachedToRef` — the task this event is attached to

**Sequence flows** — `<bpmn:sequenceFlow>`:
- `name` — branch label (especially important for gateway outgoing flows)
- `sourceRef` / `targetRef` — element IDs to build the flow graph
- `<bpmn:conditionExpression>` — gateway branch condition (JavaScript/TWScript)

**Business object item definitions** — `<bpmn:itemDefinition>`:
- `id` — referenced by `itemSubjectRef` on data inputs/outputs
- `structureRef` — fully-qualified BO type name (e.g. `bo:PizzaOrder`)

**Process variables** — derive from `<bpmn:dataInput>` / `<bpmn:dataOutput>` across all
tasks. Group by variable name (`name` attribute) and resolve type via `itemSubjectRef` →
`<bpmn:itemDefinition>` → `structureRef`.

---

## XSD file structure

The XSD defines the business object schemas referenced by the BPMN.

Namespace: `targetNamespace` attribute on `<schema>` root — e.g.
`http://Food%20Service/BusinessObjects`

Each `<complexType name="TypeName">` is one business object:
- `<annotation><documentation>` — BO description
- `<sequence><element>` children — fields:
  - `name` — field name
  - `type` — XSD type (map to BAW primitives: `string`→String, `integer`→Integer,
    `decimal`→Decimal, `boolean`→Boolean, `date`→Date, `dateTime`→DateTime)
  - `minOccurs="0"` → optional; `minOccurs="1"` → required

---

## Parsing approach

Use Python's `xml.etree.ElementTree` (stdlib). Handle the `bpmn:` namespace:

```python
import xml.etree.ElementTree as ET

BPMN = 'http://www.omg.org/spec/BPMN/20100524/MODEL'
NS = {'bpmn': BPMN}

tree = ET.parse('CookPizza.bpmn')
root = tree.getroot()

process = root.find('bpmn:process', NS)
name = process.get('name')
doc = process.findtext('bpmn:documentation', default='', namespaces=NS)

lanes = {}
for lane in process.findall('.//bpmn:lane', NS):
    lane_name = lane.get('name')
    for ref in lane.findall('bpmn:flowNodeRef', NS):
        lanes[ref.text] = lane_name

tasks = []
for task in process.findall('bpmn:userTask', NS):
    tasks.append({
        'id':   task.get('id'),
        'name': task.get('name'),
        'doc':  task.findtext('bpmn:documentation', default='', namespaces=NS),
        'lane': lanes.get(task.get('id'), 'Unassigned'),
    })
```

For the XSD:

```python
XSD_NS = {'xs': 'http://www.w3.org/2001/XMLSchema'}
xsd_tree = ET.parse('CookPizza.xsd')
xsd_root = xsd_tree.getroot()

for ct in xsd_root.findall('xs:complexType', XSD_NS):
    bo_name = ct.get('name')
    desc = ct.findtext('.//xs:documentation', default='', namespaces=XSD_NS)
    fields = []
    for el in ct.findall('.//xs:element', XSD_NS):
        fields.append({
            'name':     el.get('name'),
            'type':     el.get('type', '').split(':')[-1],
            'required': el.get('minOccurs', '0') == '1',
        })
```

---

## What BPMN+XSD covers vs. what it does not

| Section | Available from BPMN+XSD? | Notes |
|---|---|---|
| Process flow, steps, lanes | ✅ Yes | Full diagram data |
| Decision logic / conditions | ✅ Yes | From `conditionExpression` on flows |
| Process variables | ✅ Yes | Derived from task I/O specs |
| Business object schemas | ✅ Yes | From XSD |
| Services (integration, human) | ❌ No | Not present — note in Assumptions & Gaps |
| Coach views / widgets | ❌ No | Not present — note in Assumptions & Gaps |
| Integration endpoints | ❌ No | Not present — note in Assumptions & Gaps |

Always note in Section 7 (Assumptions & Gaps):
> "Source is BPMN + XSD. Services, coach views, and integration endpoint details are not
> available from this input type. Export a TWX from BAW after import for full coverage."
