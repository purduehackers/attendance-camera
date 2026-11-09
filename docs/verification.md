# Verification status — 2026-11-08

This separates observed device behavior, archived CAD checks and work that still needs hardware testing.

| Area | Evidence and limits |
|---|---|
| Deployed service | SSH inspection found `camera-feed.service` active, running and enabled on the Pi. MediaMTX reports v1.21.3; the OS reports Debian 13 / aarch64. No device configuration was changed while preparing this repository. |
| Configuration provenance | The local source config and unit were compared with their deployed counterparts before replacing the private address/account with placeholders. |
| Software binary | The official v1.21.3 ARM64 archive checksum was verified and its extracted binary matches the running Pi's binary checksum. The hashes are in `install/mediamtx-release.json`. |
| Portable configuration | Tests cover substitution, tailnet-only addresses, invalid account names and the intended read-only/non-recording configuration. |
| Installer | Shell syntax and static checks; not yet run on a fresh Pi. No end-to-end installation test is claimed. |
| Fusion client | A read-only request successfully listed open documents from the local Fusion MCP server. Modeling scripts were syntax checked, not replayed from scratch. |
| Native CAD | Archived v9 report: three installed single-solid parts, no unhealthy features and no positive-volume modeled interference. Camera orientation, ribbon clearance and port-access corridors were checked in CAD. |
| STL artifacts | All five meshes rechecked for connected components, closed edges, consistent winding and positive volume; the SHA-256 manifest ties the reports and exports to exact files. |
| Physical prototype | No completed print, slicer project, physical load test, snap-force test, cable-fit test or thermal/creep test is recorded. |
| Battery | No inline power meter or measured runtime. The 4–8 hour goal remains unverified with the intended battery. |
| Attendance | Camera transport only. No counting/detection pipeline, deployment or accuracy result. |

Do not interpret a running systemd service as proof of playback on every client, or closed STL geometry as proof of structural strength. Use the v9 print and assembly instructions for the remaining physical checks.
