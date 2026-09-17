# BPMConfig properties reference

This file documents the key properties extracted from a BPMConfig `-export` output
that are relevant to environment transition and endpoint validation.

Source: IBM Docs — Configuration properties for the BPMConfig command (BAW 26.0.x):
https://www.ibm.com/docs/en/baw/26.0.x?topic=utility-configuration-properties-bpmconfig-command

## Exporting the properties file

Run on the deployment manager machine (the dmgr must be accessible):

**Linux / AIX:**
```
<install_root>/bin/BPMConfig.sh -export \
  -profile <DmgrProfile> \
  -de <DeploymentEnvironmentName> \
  -outputDir /tmp/baw-config-export
```

**Windows:**
```
<install_root>\bin\BPMConfig.bat -export ^
  -profile <DmgrProfile> ^
  -de <DeploymentEnvironmentName> ^
  -outputDir C:\baw-config-export
```

The `-de` flag may be omitted if there is only one deployment environment in the cell.
The output is a `<DE_name>.properties` file plus optional `fileRegistry.xml` and `ltpa.jceks`.

## Key properties for endpoint transition

### Deployment manager

| Property | Description |
|---|---|
| `bpm.dmgr.hostname` | Deployment manager hostname — the primary server address |
| `bpm.dmgr.nodeName` | Deployment manager node name |
| `bpm.dmgr.installPath` | BAW installation root on the dmgr host |
| `bpm.dmgr.profileName` | Deployment manager profile name |
| `bpm.dmgr.profilePath` | Fully-qualified path to the dmgr profile directory |

### Managed nodes

Nodes are numbered from 1. For node N:

| Property | Description |
|---|---|
| `bpm.de.node.N.hostname` | Managed node hostname |
| `bpm.de.node.N.name` | Managed node name |
| `bpm.de.node.N.installPath` | BAW installation root on the managed node |
| `bpm.de.node.N.profilePath` | Managed node profile path |
| `bpm.de.node.N.profileName` | Managed node profile name |

### Databases

Databases are numbered from 1. For database N:

| Property | Description |
|---|---|
| `bpm.de.db.N.hostname` | Database server hostname |
| `bpm.de.db.N.portNumber` | Database server port |
| `bpm.de.db.N.databaseName` | Database name |
| `bpm.de.db.N.type` | Database type (DB2, Oracle, SQLServer) |
| `bpm.de.db.N.schema` | Database schema |
| `bpm.de.db.N.roleMapping.1.alias` | Authentication alias for the DbUser role |

### Process Server / Process Center

| Property | Description |
|---|---|
| `bpm.de.psServerName` | Process Server environment name (Process Server environments) |
| `bpm.de.pcServerName` | Process Center environment name (Process Center / Workflow Center) |
| `bpm.de.hostname` | Optional virtual hostname for the PS/PC endpoint |

## Comparing source and target properties files

Export from both environments and diff the resulting `.properties` files (see [BPMConfig command-line utility](https://www.ibm.com/docs/en/baw/26.0.x?topic=utilities-bpmconfig-command-line-utility)):

1. Source: `BPMConfig.sh -export -profile DmgrProfile -de DE1 -outputDir /tmp/source-cfg`
2. Target: `BPMConfig.sh -export -profile DmgrProfile -de DE1 -outputDir /tmp/target-cfg`
3. Diff the two `.properties` files to identify all differences.

## Properties that encode hostnames (scan targets)

When building the `--source-map` for `scan_twx_endpoints.py`, include the values from:

- `bpm.dmgr.hostname`
- `bpm.de.node.*.hostname`
- `bpm.de.db.*.hostname`
- Any virtual hostname set in `bpm.de.hostname`
- Any IP address variant of the above (resolve if needed)

These are the values most likely to appear hardcoded inside TWX service configurations,
web service bindings, REST server definitions, or JDBC datasource references.

## Properties NOT relevant to endpoint transition

The following properties are environment-specific configuration that does not leak
into TWX artifacts and does not need to be scanned in the TWX:

- `bpm.dmgr.profilePath` / `bpm.de.node.*.profilePath` — filesystem paths; not embedded in TWX
- `bpm.de.db.*.schema` — DB schema names; encoded in JDBC but not in TWX source files
- `bpm.dmgr.installPath` / `bpm.de.node.*.installPath` — installation directories; not referenced inside TWX
- Password / authentication alias values — masked in export output
