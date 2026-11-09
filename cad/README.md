# CAD sources and exports

**Use `v12/` for the current prototype.** It encloses the camera guard, removes stray roof holes and clears both battery strap routes. The padded hand-adjusted clamps and seven-model print layout remain. See the [hardware and assembly guide](../docs/hardware/v12/README.md).

Open [doorframe-camera-clamped-v12.f3d](v12/doorframe-camera-clamped-v12.f3d) in Autodesk Fusion for editing. The [STEP](v12/doorframe-camera-clamped-v12.step) includes reference electronics, hardware and the frame. The [seven oriented STLs](v12/stl) produce ten installed parts: print 05, 06 and 07 twice, and 01–04 once. No coupons or gauges are included.

The [operator notes](v12/PRINT-ADMIN-NOTES.md) describe printing requirements. Native checks include assembled/released clamp positions and fastener/ribbon/port clearances. All seven meshes are closed and connected. Physical fit and loaded retention remain untested. Reports at this directory's root and in older revisions are historical.

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
| `v11/` | Archived adjustable clamps; superseded camera guard and obstructed battery strap route |
| `v12/` | Current enclosed camera guard, full-width strap routes and clean roof; ten installed pieces, no coupons |

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

## Updating v12 artifacts

`scripts/build_clamped_v12.py` imports the archived v11 native file into a **new** document and builds the cleanup. `scripts/validate_v12.py` checks the assembled and retracted geometry, runs the cable and cleanup probes, then exports native/STEP files, previews and model-coordinate STLs. `scripts/prepare_v12_meshes.py` orients these fresh meshes exactly once and verifies their topology. Do not reorient already prepared STLs.

`scripts/check_v12_cleanup.py` verifies actual solid/void regions at the repaired roof, tether holes, strap slots and channels, plus the guard walls, notch and 45-degree interior. Closed strap envelopes and their front overlaps participate in the full assembly collision check. `scripts/check_v12_cables.py` checks the plug, grip and external cable envelopes; it does not verify actual connector CAD or the full CSI route. Both checks can run read-only on the assembled v12 document.

`scripts/draw_v12_cables.py` generates the cable plan from the native report. `scripts/package_v12.py` creates the ten-STL delivery ZIP and separate plain-text operator notes. After intentional changes, regenerate the manifest and run `python3 scripts/check_artifacts.py`. The native script and layout constants drive the new geometry; inherited informational parameters do not independently drive every sketch.

The scripts use paths relative to `__file__` and should be loaded through the Fusion MCP helper or an equivalent native script import. Read the source before execution. Exporting previews temporarily lays out the occurrences and restores the assembly before saving. The v11 builder and validator remain available for historical reconstruction.

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
