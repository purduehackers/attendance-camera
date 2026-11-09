# Local development

Python 3.10+ is sufficient for the configuration renderer and local checks. No third-party Python packages are needed. Autodesk Fusion scripts require Fusion's own `adsk` API.

## Files

| Path | Purpose |
|---|---|
| `src/render_config.py` | Validate and substitute the device address/account |
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
python3 -m unittest discover -s tests -v
python3 scripts/check_artifacts.py
bash -n install/install.sh
shellcheck install/install.sh
```

GitHub Actions runs the unit, artifact and shell syntax checks, and parses the Python files without importing Fusion. The mesh checker verifies closed edges, consistent winding, a single connected component and positive volume. It does not establish printed strength.

For CAD editing, see the [CAD guide](../../cad/README.md). The native v9 F3D is the primary editable artifact; the historical scripts are not a verified one-command rebuild.

## Local configuration

The renderer writes to ignored `build/config/` by default. Keep device addresses, Wi-Fi credentials, Tailscale keys, network profiles, recordings and logs out of commits. Use `local/` for machine-specific notes. The templates intentionally contain no device account or address.

The installer is new and has not been tested on a fresh Pi. See [verification status](../verification.md) for the difference between checks performed on the existing device and local checks.
