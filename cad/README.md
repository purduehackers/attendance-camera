# CAD sources and exports

**Use `v9/` for the current design.** Open [doorframe-camera-simple-v9.f3d](v9/doorframe-camera-simple-v9.f3d) in Autodesk Fusion for editing. The [STEP](v9/doorframe-camera-simple-v9.step) includes the modeled reference hardware and frame; print only the five individually exported [STLs](v9/stl), of which three are installed parts.

The [assembly guide](../docs/hardware/v9/assembly.md) and [operator notes](../docs/hardware/v9/printing.md) describe hardware, orientations, pads, port access, ribbon routing and untested fit assumptions. The current mesh/geometry reports and checksums are also inside `v9/`. Reports at this directory's root or in older revision folders are historical.

## Development history

The Python files in `scripts/` preserve the modeling and inspection work, including intermediate approaches. They are not a single idempotent build pipeline. Many mutate the active Fusion document, depend on earlier geometry or expect a saved revision. Work on a copy and read the script before running it.

| Revision | Status |
|---|---|
| `revisions/` | Earlier native archives and notes, including superseded mount/frame interpretations |
| `v5/` | Earlier hanging assembly and its reports |
| `v6/` | Three installed parts, with frame fit gauge and insert coupon |
| `v7/` | Flush camera support and covered ribbon route |
| `v8/` | Logo development; superseded due to a nonmanifold point contact. Do not print this revision. |
| `v9/` | Current reinforced hooks, clip-root fillets, corrected logo mesh and oriented exports |

Historical native files and reports are retained; duplicate ZIPs, obsolete preview images and old STL exports are omitted. Opening a native archive does not require replaying the modeling scripts.

## Fusion MCP helper

The checked-in client connects to an already installed/running Fusion MCP server, defaulting to `http://127.0.0.1:27182/mcp`. It negotiates its session at runtime. It does not install the Fusion add-in.

```sh
# Read-only check of the connection and open documents.
python3 cad/scripts/fusion_client.py call fusion_mcp_read \
  '{"queryType":"document","operation":"open"}'

# Example of executing a script inside Fusion; inspect it first.
python3 cad/scripts/fusion_client.py script cad/scripts/inspect.py --read-only
```

Override the endpoint with `FUSION_MCP_URL` if needed. `FUSION_MCP_SESSION` optionally supplies an existing session; do not commit one. The wrapper imports scripts inside Fusion so their `__file__`-relative output paths work. Local Python does not provide the `adsk` API.

## Updating v9 artifacts

`scripts/validate_v9.py` inspects the active design and exports fresh model-coordinate artifacts. `scripts/prepare_v9_meshes.py` transforms those fresh STLs into print orientation. Read both scripts before use, activate the intended v9 document, and run orientation preparation only once on each fresh export. Do not repeatedly transform the already oriented tracked STLs.

After an intentional export or documentation update, regenerate the manifest from the v9 directory:

```sh
python3 - <<'PY'
import hashlib, json
from pathlib import Path
base = Path('cad/v9')
manifest = {
    str(path.relative_to(base)): hashlib.sha256(path.read_bytes()).hexdigest()
    for path in sorted(base.rglob('*'))
    if path.is_file() and path.name != 'manifest-sha256.json'
}
(base / 'manifest-sha256.json').write_text(json.dumps(manifest, indent=2) + '\n')
PY
python3 scripts/check_artifacts.py
```

Review generated diffs and the actual model before committing. Refreshing a checksum only records the new bytes; it does not independently validate the design. The mesh checker is read-only and does not require Fusion.
