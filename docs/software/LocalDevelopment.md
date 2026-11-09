# Local development

Use Python 3.12 and [uv](https://docs.astral.sh/uv/) for the attendance server. Dependencies are pinned in `uv.lock`. The older Pi configuration renderer and CAD artifact checker still use only the standard library. Autodesk Fusion scripts require Fusion's own `adsk` API.

```sh
uv sync --locked
uv run attendance-server serve --demo
```

Open `http://127.0.0.1:8000`. Demo mode generates rectangles in memory, makes no camera connection, needs no detector download, and uses a separate `local/demo.sqlite3` database. It is explicitly labeled in the UI. Start a session to see its synthetic crossings counted.

## Files

| Path | Purpose |
|---|---|
| `src/render_config.py` | Validate and substitute the device address/account |
| `src/attendance_camera/` | API, dashboard, capture, inference, counting and aggregate storage |
| `install/mediamtx.yml.in` | Sanitized live MediaMTX configuration |
| `install/camera-feed.service.in` | Sanitized live systemd unit |
| `install/install.sh` | Pinned download, verification, backup and service installation |
| `install/mediamtx-release.json` | Release provenance and archive/binary checksums |
| `cad/scripts/` | Fusion modeling, inspection and export scripts |
| `tests/` | Configuration validation tests |
| `scripts/check_artifacts.py` | Read-only v9 manifest and mesh checks |

## Checks

From the repository root:

```sh
python3 -m unittest discover -s tests -p test_config.py -v
uv run pytest -q
uv run ruff check src/attendance_camera tests/test_counting.py tests/test_store.py tests/test_server.py tests/test_vision.py
python3 scripts/check_artifacts.py
bash -n install/install.sh
shellcheck install/install.sh
```

GitHub Actions runs the unit, artifact and shell syntax checks, the server tests, and parses the Python files without importing Fusion. Server tests cover hysteresis, direction, expired tracks, region exits, synthetic ByteTrack integration, persistence, corrections, exclusive database ownership, authenticated API access and reconnect state. The mesh checker verifies closed edges, consistent winding, a single connected component and positive volume. Neither synthetic tests nor valid meshes establish real-world counting accuracy or printed strength.

For CAD editing, see the [CAD guide](../../cad/README.md). The native v9 F3D is the primary editable artifact; the historical scripts are not a verified one-command rebuild.

## Local configuration

The renderer writes to ignored `build/config/` by default. Keep device addresses, Wi-Fi credentials, Tailscale keys, network profiles, recordings and logs out of commits. Use `local/` for machine-specific notes. The templates intentionally contain no device account or address.

The installer is new and has not been tested on a fresh Pi. See [verification status](../verification.md) for the difference between checks performed on the existing device and local checks.
