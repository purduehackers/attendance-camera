# Verification status — 2026-11-09

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
| Attendance backend | Local YOLOX/ByteTrack pipeline, directional counter, SQLite aggregates, authenticated dashboard and CSV export implemented. Twenty tests pass, including synthetic tracking-to-counting integration, API access and persistence. Real overhead counting accuracy remains unmeasured. |
| Server deployment | `attendance-server.service` is active and enabled under the managed `p-attendance` account, with `Linger=yes` and a project-owned checkout, Python runtime and database in `/proj/attendance`. The former personal-account service is disabled. After migration, fresh frames and about 146 ms inference were observed with zero restarts. The host runs Rocky Linux 9.8 with Xeon X5650 CPUs. No session was started or calibration asserted on the uninstalled camera view. |
| Camera transport to server | A dedicated restricted SSH key and boot-enabled reverse tunnel on the Pi provide a server-loopback RTSP endpoint. The tunnel still authenticates to the original account; the project key and replacement unit are staged, but changing the Pi unit is blocked by SSH closing before authentication after an earlier shell I/O error. The existing feed remains live. The server's current Tailscale state did not provide connectivity to the Pi. |
| Browser dashboard | Synthetic demo tested in Chromium: preview, session start and responsive layout; no JavaScript errors or horizontal overflow at 390 px. These UI tests do not validate person detection. |

Do not interpret a running systemd service as proof of playback on every client, or closed STL geometry as proof of structural strength. Use the v9 print and assembly instructions for the remaining physical checks.
