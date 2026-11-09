# CAD sources and exports

**Use `v11/` for the current prototype.** It replaces the fixed friction hooks with padded, hand-adjusted screw clamps and separates the parts for flatter printing. See the [hardware and assembly guide](../docs/hardware/v11/README.md).

Open [doorframe-camera-clamped-v11.f3d](v11/doorframe-camera-clamped-v11.f3d) in Autodesk Fusion for editing. The [STEP](v11/doorframe-camera-clamped-v11.step) includes reference electronics, hardware and the frame. The [seven oriented STLs](v11/stl) produce ten installed parts: print 05, 06 and 07 twice, and 01–04 once. No coupons or gauges are included.

The [operator notes](v11/PRINT-ADMIN-NOTES.md) describe printing requirements. Native checks include assembled/released clamp positions and fastener/ribbon/port clearances. All seven meshes are closed and connected. Physical fit and loaded retention remain untested. Reports at this directory's root and in older revisions are historical.

## Development history

The Python files in `scripts/` preserve the modeling and inspection work, including intermediate approaches. They are not a single idempotent build pipeline. Many mutate the active Fusion document, depend on earlier geometry or expect a saved revision. Work on a copy and read the script before running it.

| Revision | Status |
|---|---|
| `revisions/` | Earlier native archives and notes, including superseded mount/frame interpretations |
| `v5/` | Earlier hanging assembly and its reports |
| `v6/` | Three installed parts, with frame fit gauge and insert coupon |
| `v7/` | Flush camera support and covered ribbon route |
| `v8/` | Logo development; superseded due to a nonmanifold point contact. Do not print this revision. |
| `v9/` | Reinforced hooks, clip-root fillets and corrected logo; archived small heat-set insert variant |
| `v10/` | Archived fixed friction mount; direct PETG PCB screw pilots |
| `v11/` | Current adjustable clamps, ten installed pieces from seven models, flatter print layout; no coupons |

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

## Updating v11 artifacts

`scripts/build_clamped_v11.py` imports the v10 archive into a **new** document and builds the revised parts. `scripts/validate_v11.py` runs once on that fresh document, verifies geometry, and exports the native archive, STEP, previews and model-coordinate meshes. `scripts/prepare_v11_meshes.py` then orients the fresh STLs exactly once and verifies mesh topology. The named native features remain editable; layout constants are in the builder, and its informational `v11_*` parameters do not independently drive every sketch.

`scripts/package_v11.py` creates a delivery ZIP containing ten installed STL files (the repeated parts are duplicated for convenience) and separate operator notes. It does not add coupons. Regenerate the manifest after intentional changes, then run `python3 scripts/check_artifacts.py`.

The scripts use `__file__`-relative paths and should be loaded through the Fusion MCP helper or an equivalent native script import. Read the source before execution; the export/preview step temporarily lays out the installed occurrences and restores the assembly before saving.

## Updating archived v10 artifacts

`scripts/validate_v10.py` inspects the active design and exports fresh model-coordinate artifacts. `scripts/prepare_v10_meshes.py` transforms those fresh STLs into print orientation. Read both scripts before use, activate the intended v10 document, and run orientation preparation only once on each fresh export. Do not repeatedly transform the already oriented tracked STLs.

After an intentional export or documentation update, regenerate the manifest from the v10 directory:

```sh
python3 - <<'PY'
import hashlib, json
from pathlib import Path
base = Path('cad/v10')
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
