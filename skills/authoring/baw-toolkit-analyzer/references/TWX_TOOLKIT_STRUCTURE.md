# TWX Toolkit XML Structure Reference

This document describes the **confirmed** file layout and element schema used by
`analyze_toolkit_deps.py` to parse a BAW TWX export.

---

## TWX archive layout

A TWX file is a standard ZIP archive.  The files relevant to toolkit dependency
analysis are:

| Path | Purpose |
|---|---|
| `META-INF/package.xml` | Master manifest — lists `<dependencies>` and `<objects>` |
| `META-INF/metadata.xml` | Minimal; rarely contains useful data (often empty) |
| `META-INF/properties.json` | Flags like `{"twxWithoutToolkits":"false"}` |
| `objects/<prefix>.<uuid>.xml` | One XML file per artifact (process, service, BO, coach, etc.) |
| `toolkits/<snapshot-id>.zip` | BAW embeds each declared toolkit dependency as a nested ZIP |
| `files/<asset-id>/<uuid>` | Binary managed assets (ignored by this skill) |

---

## `META-INF/package.xml` — master manifest

Root element: `<p:package xmlns:p="http://lombardisoftware.com/schema/teamworks/7.0.0/package.xsd">`

### `<target>` — the exported app / toolkit

```xml
<target>
  <project id="2066.efa60e19-..." name="DependencyMapperTest"
           shortName="DMT" isToolkit="false" isHidden="false" isSystem="false" .../>
  <branch id="2063.66b47776-..." name="Main" acronym="Main"/>
  <snapshot id="2064.ec084090-..." name="1" acronym="1"
            originalCreationDate="2026-08-19T13:21:18.637-04:00"/>
</target>
```

Key attributes used:

| Element | Attribute | Description |
|---|---|---|
| `<project>` | `name` | Full display name of the app or toolkit |
| `<project>` | `shortName` | Acronym / short name (e.g. `DMT`) |
| `<project>` | `isToolkit` | `"true"` if the TWX contains a toolkit, `"false"` for a process app |
| `<snapshot>` | `name` | Snapshot name (e.g. `"1"`, `"2024-11"`) |
| `<snapshot>` | `acronym` | Snapshot acronym (often same as name) |

### `<dependencies>` — toolkit dependency declarations

Each `<dependency>` element represents one toolkit the process app (or toolkit)
depends on.

```xml
<dependencies>
  <dependency rank="0" isManaged="false" id="2069.01f32839-...">
    <project id="2066.1b351583-..." name="System Data"
             shortName="TWSYS" isToolkit="true" isHidden="false" isSystem="true"/>
    <branch id="2063.0798815e-..." name="Main"/>
    <snapshot id="2064.1080ded6-d153-4654-947c-2d16fce170db"
              name="8.6.0.0_TC" originalCreationDate="2015-08-24T20:00:00.000-04:00"/>
  </dependency>
  <dependency rank="1" isManaged="false" id="2069.807f616f-...">
    <project id="2066.ec5973da-..." name="UI Toolkit"
             shortName="SYSBPMUI" isToolkit="true" isHidden="false" isSystem="false"/>
    <branch id="2063.83ee2bb2-..." name="Main"/>
    <snapshot id="2064.304ac881-16c3-47d2-97d5-6e4c4a893177"
              name="8.6.0.0" originalCreationDate="2017-05-24T19:23:53.574-04:00"/>
  </dependency>
</dependencies>
```

Key attributes extracted by the script:

| XPath | Attribute | Maps to |
|---|---|---|
| `dependency/project` | `name` | Toolkit display name |
| `dependency/project` | `shortName` | Toolkit acronym (e.g. `TWSYS`) |
| `dependency/project` | `isSystem` | `"true"` for built-in IBM toolkits |
| `dependency/branch` | `name` | Branch name (usually `"Main"`) |
| `dependency/snapshot` | `name` | Snapshot name referenced by this app |
| `dependency/snapshot` | `id` | `"2064.<uuid>"` — the embedded ZIP filename is `toolkits/<uuid>.zip` |
| `dependency/snapshot` | `originalCreationDate` | ISO 8601 creation date |

> **Important:** There is **no** `<toolkitDependency>` or `<dependency type="toolkit">`
> element in this version of BAW.  All dependency declarations use the nested
> `<project>` / `<branch>` / `<snapshot>` element structure shown above.

---

## Embedded toolkit ZIPs (`toolkits/`)

BAW embeds each toolkit listed in `<dependencies>` as a nested ZIP:

```
toolkits/2064.1080ded6-d153-4654-947c-2d16fce170db.zip   ← System Data
toolkits/2064.304ac881-16c3-47d2-97d5-6e4c4a893177.zip   ← UI Toolkit
```

The filename is `toolkits/<snapshot-id>.zip` where `<snapshot-id>` matches the
`id` attribute of the `<snapshot>` element in `package.xml`.

Each embedded ZIP is itself a full TWX-format archive containing its own
`META-INF/package.xml`.  The script reads each embedded ZIP to resolve
transitive dependencies (the toolkit's own `<dependencies>` section).

---

## Artifact object files (`objects/`)

BAW serializes each artifact in the process app as an individual XML file with
a numeric type prefix and UUID:

| Prefix | Artifact type |
|---|---|
| `1.` | Process / service flow |
| `12.` | Business Object (`twClass`) |
| `25.` | BPD (BPMN process) |
| `50.` | Resource bundle group |
| `61.` | Managed asset (file/JS/CSS) |
| `62.` | Environment variable set |
| `63.` | Project defaults |

Each file is wrapped in a `<teamworks>` root element:

```xml
<teamworks>
  <twClass id="12.023fa9af-..." name="ClaimLine">
    ...
    <definition>
      <property>
        <name>lineId</name>
        <classRef>01f32839-70a0-4098-ad79-3106733b99b6/12.db884a3c-...</classRef>
        ...
      </property>
    </definition>
  </twClass>
</teamworks>
```

The script identifies the artifact type and name from the first child element of
`<teamworks>`.

---

## Artifact-level toolkit references

### How toolkit types are referenced in artifact XML

Artifact XML represents cross-toolkit type references as `classRef` values that begin with
the dependency's project UUID:

```xml
<classRef>01f32839-70a0-4098-ad79-3106733b99b6/12.db884a3c-...</classRef>
```

The UUID `01f32839-...` is the `id` value of the dependency's `<dependency>`
element in `package.xml` (the `id` on the `<dependency>` element itself, not
on `<project>` or `<snapshot>`).

### Cross-toolkit reference resolution

The analyzer indexes all exported artifacts (Coach Views, Business Objects,
Services, System types, and Themes) from embedded toolkit ZIPs (`toolkits/*.zip`)
and direct dependency records in `package.xml`. It cross-references artifact UUIDs,
dependency IDs, and short-name script calls across process application objects to
accurately map usage and distinguish active from unused toolkits.

---

## Notes on tip snapshot detection

The `package.xml` format in BAW 8.6.x does **not** include a `tip="true"` flag
on `<dependency>` or `<snapshot>`.  The script detects tip references by
inspecting the snapshot name: a snapshot named `"Tip"` (case-insensitive) is
flagged as a live-branch reference.  Because this detection relies on the
snapshot name string only, references to the live branch under a custom name
will not be flagged.
