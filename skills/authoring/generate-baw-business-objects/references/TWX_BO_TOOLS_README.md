# BAW TWX Python Tools

A set of three Python scripts for working with IBM Business Automation Workflow (BAW) TWX files. All scripts are self-contained — they require **Python 3.9+** and no third-party packages.

---

## Contents

| Script | Purpose |
|---|---|
| [`create_empty_twx.py`](#create_empty_twxpy) | Create a brand-new empty TWX from the reference template |
| [`list_bos.py`](#list_bospy) | Inspect all Business Objects inside an existing TWX |
| [`apply_bos.py`](#apply_bospy) | Add or overwrite Business Objects in an existing TWX |

The reference template (`empty-project.twx`) is included in this folder and is required by `create_empty_twx.py`. The other two scripts only need a path to an existing TWX.

---

## Background: what is a TWX?

A TWX file is an IBM BAW process app or toolkit exported from the authoring environment — **Workflow Center** (traditional BAW) or **Business Automation Studio** (CP4BA containerized). It is a ZIP archive containing:

- `META-INF/package.xml` — the project manifest: identity (project/branch/snapshot UUIDs), dependency declarations, and an index of every artifact object
- `objects/<id>.xml` — one XML file per artifact (Business Objects, Service Flows, Coach Views, etc.)
- `toolkits/<snapshotUUID>.zip` — bundled toolkit snapshots (System Data, UI Toolkit)
- `files/<id>/<assetUuid>` — binary managed assets (themes, JS files)

Business Objects use the XML type `twClass`. Every object is identified by a **typed UUID** of the form `<typeCode>.<bare-guid>` — BOs always start with `12.`.

---

## `.bo.json` file format

Used by `apply_bos.py`. The **filename stem** (everything before `.bo.json`) is the Business Object name — the name is never duplicated inside the file.

Two kinds are supported, selected by the required `"kind"` field.

### Complex BO

A record type with named, typed properties.

```json
{
  "kind": "complex",
  "description": "Optional human-readable description.",
  "properties": [
    { "name": "id",        "type": "String"  },
    { "name": "amount",    "type": "Decimal" },
    { "name": "placedOn",  "type": "Date"    },
    { "name": "active",    "type": "Boolean" },
    { "name": "count",     "type": "Integer" },
    { "name": "startTime", "type": "Time"    },
    { "name": "status",    "type": "OrderStatus",  "description": "Current state." },
    { "name": "tags",      "type": "String",        "array": true  },
    { "name": "score",     "type": "Integer",       "required": true },
    { "name": "internal",  "type": "String",        "hidden": true   }
  ]
}
```

**Property fields:**

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Property name. Must be unique within the BO. |
| `type` | Yes | Data type — see type reference below. |
| `array` | No | `true` to make this a list-valued property. Default `false`. |
| `required` | No | `true` to mark the property required. Default `false`. |
| `hidden` | No | `true` to hide the property in BAW tooling. Default `false`. |
| `description` | No | Optional per-property description string. |

**Type reference:**

| Value | Resolves to |
|---|---|
| `"String"` | System Data primitive String |
| `"Integer"` | System Data primitive Integer |
| `"Boolean"` | System Data primitive Boolean |
| `"Decimal"` | System Data primitive Decimal |
| `"Date"` | System Data primitive Date |
| `"Time"` | System Data primitive Time |
| `"SomeName"` | Another local BO already in the TWX, or one being added in the same run |

Primitives are always resolved to System Data. If you have a local BO also named `String`, the primitive still wins for the `"type"` field — they cannot be confused.

Cross-toolkit BO references (e.g. `ref:TWSYS/SomeType`) are **not supported** by this tool. Only local project BOs and primitives can be property types.

### Selection BO

An enumeration (list of value/display pairs). BAW calls these "Selection" type simple BOs.

```json
{
  "kind": "selection",
  "description": "Optional description.",
  "options": [
    { "value": "NEW",       "display": "New"       },
    { "value": "SHIPPED",   "display": "Shipped"   },
    { "value": "DELIVERED", "display": "Delivered" }
  ]
}
```

**Options fields:**

| Field | Required | Description |
|---|---|---|
| `value` | Yes | The stored value written to BAW data, e.g. `"NEW"`. |
| `display` | Yes | The human-readable label shown in BAW UI, e.g. `"New"`. |

At least one option is required.

### What is not supported

BAW has a third BO kind — **simple restricted types** (e.g. a String with a min/max length constraint, like `ItemName` with `minLength=1, maxLength=100`). These are read-only in this toolset: `list_bos.py` will report them as `[Simple]`, but `apply_bos.py` cannot create them. If a TWX contains one, it passes through untouched to the output.

---

## `create_empty_twx.py`

Creates a brand-new empty TWX from the bundled reference template (`empty-project.twx`). Every identity UUID in the template is rewritten to a fresh value, so the generated TWX is a distinct project that can be imported into BAW without colliding with anything.

The output is an empty BAW process app or toolkit ready to have artifacts added to it (e.g. via `apply_bos.py`).

### Usage

```
python create_empty_twx.py --name NAME --acronym ACRONYM --out OUTPUT.twx [options]
```

### Arguments

| Argument | Required | Description |
|---|---|---|
| `--name` | Yes | Project display name shown in BAW, e.g. `"My Toolkit"`. |
| `--acronym` | Yes | Project short name / acronym, e.g. `MYTK`. Used as the namespace prefix and in BAW URLs. |
| `--out` | Yes | Output `.twx` file path, e.g. `dist/MYTK.twx`. Parent directories are created automatically. |
| `--snapshot` | No | Snapshot version name. Defaults to `0.0.0.1`. |
| `--process-app` | No | Emit a process app instead of a toolkit. Default output is a **toolkit**. |
| `--no-ui-toolkit` | No | Drop the SYSBPMUI (UI Toolkit) dependency. Produces a leaner TWX for headless/service projects. |
| `--template` | No | Path to an alternative reference template. Defaults to `empty-project.twx` in the same folder as the script. |

### Examples

```bash
# Create a toolkit (default)
python create_empty_twx.py --name "My Toolkit" --acronym MYTK --out dist/MYTK.twx

# Create a process app
python create_empty_twx.py --name "My App" --acronym MYAPP --out dist/MYAPP.twx --process-app

# Specific snapshot version, no UI Toolkit
python create_empty_twx.py --name "Lean Toolkit" --acronym LEAN \
    --out dist/LEAN.twx --snapshot 1.0.0.0 --no-ui-toolkit
```

### What it does

1. Loads `empty-project.twx` (a BAW 24 / 8.6.8 exported empty process app).
2. Scans `META-INF/package.xml` and every `objects/*.xml` for typed UUIDs.
3. Rewrites every project-owned UUID to a fresh value, preserving IBM-owned system UUIDs (System Data, UI Toolkit, primitive types, the System participant, the default theme).
4. Substitutes project name, acronym, namespace, and snapshot creation date.
5. If `--no-ui-toolkit`, removes the SYSBPMUI dependency block and its bundled toolkit zip.
6. If `--process-app` is NOT set, flips `isToolkit="true"` and renames the settings object.
7. Writes the result as a new ZIP to `--out`.

### BAW version compatibility

The reference template is stamped as BAW 24 (`buildVersion="8.6.8"`, `fixPack="24010"`). BAW imports older TWXes into newer servers, so this template works on BAW 24, 25, 26, and beyond. A BAW 25-stamped TWX would not import into BAW 24 — using the BAW 24 template is the safe universal baseline.

---

## `list_bos.py`

Reads an existing TWX file and prints all Business Objects found inside it, including their properties, types, and options.

### Usage

```
python list_bos.py path/to/app.twx [--json]
```

### Arguments

| Argument | Required | Description |
|---|---|---|
| `path/to/app.twx` | Yes | Path to the TWX file to inspect. |
| `--json` | No | Output as a JSON array instead of human-readable text. |

### Examples

```bash
# Human-readable output
python list_bos.py dist/MyApp.twx

# Machine-readable JSON
python list_bos.py dist/MyApp.twx --json
```

### Human-readable output example

```
Found 4 Business Object(s):

  [Complex] Customer  (12.3cef8268-10e9-4228-8115-37dfc5066d71)
    Description: A customer record.
    • id: String
    • email: String
    • tier: Tier
    • orders: Order  [array]

  [Selection] OrderStatus  (12.4b55f32e-...)
    • 'NEW' = 'New'
    • 'SHIPPED' = 'Shipped'

  [Complex] Order  (12.ada3f0fc-...)
    • id: String
    • amount: Decimal

  [Simple] ItemName  (12.cd493a8b-...)
    Base type: String
```

### JSON output structure

```json
[
  {
    "id": "12.3cef8268-...",
    "name": "Customer",
    "kind": "complex",
    "description": "A customer record.",
    "properties": [
      { "name": "id",     "type": "String",  "classRef": "depGuid/12.db884a3c-..." },
      { "name": "tier",   "type": "Tier",    "classRef": "/12.4b55f32e-..."        },
      { "name": "orders", "type": "Order",   "classRef": "/12.ada3f0fc-...", "array": true }
    ]
  },
  {
    "id": "12.4b55f32e-...",
    "name": "OrderStatus",
    "kind": "selection",
    "baseType": "Selection",
    "options": [
      { "value": "NEW",     "display": "New"     },
      { "value": "SHIPPED", "display": "Shipped" }
    ]
  },
  {
    "id": "12.cd493a8b-...",
    "name": "ItemName",
    "kind": "simple",
    "baseType": "String"
  }
]
```

### Notes on BO kinds

| Kind reported | BAW description | `type` in XML | Notes |
|---|---|---|---|
| `complex` | Complex BO | `1` | Has named typed properties |
| `selection` | Selection (enum) | `0` with `base="Selection"` | Has value/display option pairs |
| `simple` | Restricted simple type | `0` with other base | e.g. length-restricted String; read-only in this toolset |

For `complex` BOs, property types are resolved to friendly names where possible:
- System Data primitives (`String`, `Integer`, etc.) are resolved via a hardcoded UUID table.
- Local project BOs are resolved by looking up the typed UUID in the same project's BO map.
- Cross-toolkit BO references (properties whose type comes from a dependency toolkit) are reported as `null` (the toolkit is not loaded during inspection).

---

## `apply_bos.py`

Applies a set of `.bo.json` descriptor files to an existing TWX, producing a new output TWX. The source TWX is never modified.

- If a `.bo.json` name **matches an existing BO** in the TWX, the old artifact is replaced — using the same `12.<uuid>` — so BAW reads it as an updated version of the same object, not a deletion and re-creation.
- If a `.bo.json` name is **new**, the BO is added with a freshly minted UUID.
- All other objects in the TWX (other artifact types, toolkit dependencies, binary assets) pass through byte-identical.
- The output snapshot gets a new snapshot UUID and the version name you supply via `--version`.

### Usage

```
python apply_bos.py --source SOURCE.twx --version VERSION --out OUTPUT.twx FILE.bo.json [FILE.bo.json ...]
```

### Arguments

| Argument | Required | Description |
|---|---|---|
| `--source` | Yes | Source `.twx` file. Never modified. |
| `--version` | Yes | Snapshot version name for the output TWX, e.g. `1.2.3.4`. |
| `--out` | Yes | Output `.twx` file path. Must differ from `--source`. |
| `FILE.bo.json` | Yes (one or more) | `.bo.json` descriptor files to apply. |

### Examples

```bash
# Add or update three BOs
python apply_bos.py \
    --source dist/MyApp.twx \
    --version 1.1.0.0 \
    --out dist/MyApp-1.1.0.0.twx \
    bos/Customer.bo.json bos/Order.bo.json bos/OrderStatus.bo.json

# All .bo.json files in a directory (bash glob)
python apply_bos.py \
    --source dist/MyApp.twx \
    --version 2.0.0.0 \
    --out dist/MyApp-2.0.0.0.twx \
    bos/*.bo.json
```

### Cross-BO references

If one BO's property references another BO by name (e.g. `Customer.orders` typed as `Order`), both must be resolvable at the time the script runs — either already present in the source TWX, or provided as input files in the same run. The order of the input files does not matter; all IDs are resolved before any XML is generated.

### UUID stability

When overwriting an existing BO, the original `12.<uuid>` is preserved. This is important: BAW tracks an object's history across snapshots by its UUID. If the UUID were re-minted on overwrite, BAW would treat the result as a brand-new object with no history, and the old one as deleted.

When a BO is new (no matching name in the source TWX), a fresh UUID is minted. Because this tool has no lockfile, a BO that is new on one run and absent in the next run's source TWX will receive a different UUID each time. To get stable UUIDs for new BOs across runs, start by importing one output TWX into BAW, then export it back and use that export as the `--source` for subsequent runs — the UUID will then be in the exported TWX and will be preserved on overwrite.

### Output snapshot identity

The output TWX gets a **new snapshot UUID** and the version name from `--version`. The project UUID and branch UUID are preserved from the source TWX, so BAW recognises the import as a new snapshot of the same project rather than a new project.

---

## Typical workflow

### Greenfield: start from scratch

```bash
# 1. Create an empty toolkit
python create_empty_twx.py --name "My Toolkit" --acronym MYTK --out dist/MYTK.twx

# 2. Add Business Objects
python apply_bos.py --source dist/MYTK.twx --version 1.0.0.0 --out dist/MYTK-1.0.0.0.twx \
    bos/Customer.bo.json bos/Order.bo.json bos/OrderStatus.bo.json

# 3. Import dist/MYTK-1.0.0.0.twx into BAW
```

### Incremental: update an existing app

```bash
# Inspect what BOs already exist
python list_bos.py dist/MyApp-1.0.0.0.twx

# Author or edit .bo.json files, then apply them
python apply_bos.py --source dist/MyApp-1.0.0.0.twx --version 1.1.0.0 \
    --out dist/MyApp-1.1.0.0.twx bos/Customer.bo.json

# Import dist/MyApp-1.1.0.0.twx into BAW
```

### Inspect a TWX exported from BAW

```bash
# See all BOs in an exported TWX, including ones created in BAW directly
python list_bos.py exported/Banking_Demo-1.0.0.1.twx --json > bos_inventory.json
```

---

## Limitations

- **Simple restricted types** (e.g. length-restricted strings) cannot be created by `apply_bos.py`. They are read-only and pass through unchanged.
- **Cross-toolkit BO references** in property types are not supported. Properties must reference either a primitive or a local BO in the same project.
- **No lockfile.** Unlike the TypeScript baw-codegen compiler, these scripts do not maintain a `baw-lock.json`. UUID stability for new BOs across multiple runs depends on using a previously-exported TWX as the source (see UUID stability note above).
- **Other artifact types** (Service Flows, Coach Views, BPDs, etc.) cannot be created or modified by these scripts. Only Business Objects are in scope.
