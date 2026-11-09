# Attendance server

The server reads the Pi's RTSP feed, detects people with YOLOX on the CPU, associates detections with ByteTrack, and counts movement across a calibrated boundary. FastAPI serves the organizer dashboard and API. SQLite stores sessions and per-minute counts.

The [project proposal](https://app.notion.com/p/309181f3b6ed810da202d23c8989e9c7) calls for rolling occupancy, local computation on PH-owned hardware and no stored personal data. This implementation does not identify people or estimate unique visitors. Someone leaving and returning creates an exit and another entrance.

## Run

Use Python 3.12 and uv on the PH server:

```sh
git clone https://github.com/purduehackers/attendance-camera.git
cd attendance-camera
uv sync --locked --no-dev
uv run attendance-server fetch-model
mkdir -p local
cp install/server.example.toml local/server.toml
```

Set `ATTENDANCE_CAMERA_URL` to a reachable RTSP URL, and `ATTENDANCE_TOKEN` to a randomly generated password of at least 24 characters. Put them in a private `local/server.env`, with mode 600; never commit it. The dashboard username is `organizer`. The systemd unit reads that file directly. For an interactive shell, export these variables before running:

```sh
uv run attendance-server serve --config local/server.toml
```

The default listener is **127.0.0.1:8000**. Use an SSH tunnel to view it:

```sh
ssh -N -L 18000:127.0.0.1:8000 <account>@<server>
```

Then open `http://127.0.0.1:18000` and authenticate as `organizer`. Use your configured SSH host alias/port. No public HTTP listener or proxy route is installed. A non-loopback listener requires a token; if adding a reverse proxy, also configure `allowed_hosts` and review origin/proxy handling. The current CLI deliberately does not trust forwarded headers.

## Boot service on the PH server

The [server admin guide](https://app.notion.com/p/3ea181f3b6ed8002bc2acc1b1c179ebf) supports systemd user services. The deployed backend belongs to **`p-attendance`**, with its checkout at **`/proj/attendance/attendance-camera`**. Project members manage it from the project account:

```sh
sudo -u p-attendance -i
cd ~/attendance-camera
loginctl enable-linger "$USER"
loginctl show-user "$USER" -p Linger
```

The last command should report `Linger=yes`. Run the enable command with the explicit username from inside the project account. This keeps its user service manager running after logout and starts it at boot.

The supplied unit assumes the checkout is `~/attendance-camera`. Install and enable it as the project user:

```sh
mkdir -p ~/.config/systemd/user
cp install/attendance-server.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now attendance-server.service
systemctl --user status attendance-server.service
```

If a non-login automation shell cannot connect to the user bus, set `XDG_RUNTIME_DIR=/run/user/$(id -u)` and `DBUS_SESSION_BUS_ADDRESS=unix:path=$XDG_RUNTIME_DIR/bus` in that project-user shell. The unit has a 2 GiB memory cap and four-CPU quota. It runs one application worker. A database file lock prevents a second process from counting the same camera into that database.

Use `journalctl --user -u attendance-server.service` for diagnostics. Stop it with `systemctl --user disable --now attendance-server.service`. To update, stop the unit, update the checkout, run `~/.local/bin/uv sync --locked --no-dev`, then restart it. The deployed project account has its own uv and Python installation. Back up the aggregate database while stopped. Camera passwords and model binaries are not part of a source backup.

## When the server cannot reach the Pi's tailnet

The Pi can maintain an SSH reverse tunnel to the server's loopback interface. The server then reads `rtsp://127.0.0.1:18554/cam`, using interleaved TCP. This leaves the Pi's existing Tailscale-bound camera service in place.

1. Generate a dedicated Ed25519 key on the Pi; keep its private key there.
2. Pin the server's SSH host key from a trusted connection in a dedicated known-hosts file.
3. Append the public key to the intended server account's `authorized_keys`, with restrictions. Use `p-attendance` for this project; preserve the managed `~/.ssh/authorized_keys` symlink and append through it rather than replacing it:

   ```text
   restrict,port-forwarding,permitlisten="127.0.0.1:18554",permitopen="127.0.0.1:9",command="/usr/bin/false" ssh-ed25519 <PUBLIC_KEY> attendance-camera-tunnel
   ```

4. Fill the placeholders in [`camera-tunnel.service.in`](../../install/camera-tunnel.service.in) locally. Install the rendered unit on the Pi as `/etc/systemd/system/attendance-camera-tunnel.service`, reload systemd and enable it.
5. Verify the server is listening only on `127.0.0.1:18554`. Use a different unused loopback port if needed, changing both the unit and key restriction.

The key cannot open an interactive shell and its remote listener is restricted to that loopback port. The tunnel reconnects after network failures and starts after the Pi camera service. Revoke it by stopping the Pi tunnel unit and removing only its dedicated public-key line from the server. Do not replace existing authorized keys or alter the server's tailnet configuration.

## Calibrate and count

1. Mount the camera in its final position, pointing down. Open **Show live preview**.
2. Set the rectangular region around the passage. The line spans that region. Select horizontal/vertical and which side is inside. Position and buffer are percentages of the selected region along the counting axis.
3. Save calibration. Walk through in each direction and verify the direction against a manually observed test session. Two people together, pauses, reversals, partial occlusion, lighting and clothing need testing too.
4. Start a session with an actual current headcount. Starting does not infer how many people are already in the room.
5. Use **Correct occupancy** when a manual headcount differs, or after a camera/network interruption. Corrections are recorded separately from entrances/exits.
6. End the session and download its per-minute CSV. Times are Unix seconds in UTC; the dashboard displays the browser's local time. Empty minutes have no row.

Tracks must be seen clearly on opposite sides of a deadband before a crossing counts. Initial sightings, leaving the region, long gaps and tracker resets do not themselves produce crossings. Short-term track identifiers remain in memory only. The anchor is the detected box center, appropriate for the intended overhead view.

A session survives application restart, but is flagged for reconciliation. Disconnects, stale frames and calibration changes also mark an active session uncertain. A negative net balance is retained internally for correction; displayed occupancy is clamped to zero and flagged. The system never silently treats an outage as an empty room.

## Models and performance

Default: **YOLOX-Tiny ONNX, 416 × 416**, CPU inference with three threads, processing target 6 fps. The source feed remains 1080p30. A capture thread drains it into one latest-frame slot instead of building an inference backlog.

The model is fetched from the [official YOLOX ONNX release](https://github.com/Megvii-BaseDetection/YOLOX/releases/tag/0.1.1rc0). The downloader verifies a pinned SHA-256 before installing it. This older release is the upstream's published ONNX deployment artifact. Model files are not committed. [YOLOX](https://github.com/Megvii-BaseDetection/YOLOX) is Apache-2.0; [ONNX Runtime](https://github.com/microsoft/onnxruntime) is MIT; [Trackers](https://github.com/roboflow/trackers) and [Supervision](https://github.com/roboflow/supervision) retain their upstream licenses. No model service, API key, remote inference, appearance embedding or facial recognition is used.

`fetch-model --variant nano` and `--variant s` install alternatives. Also change `model_path` in the local config before restarting. The detector supports these raw COCO YOLOX exports, not arbitrary ONNX models. It follows upstream BGR 0–255 preprocessing and grid decoding; changing export format requires updating the adapter.

On the PH server's Xeon X5650 CPUs, synthetic blank-frame detector benchmarks measured approximately 1.3 fps for S with two threads, 7.3 fps for Tiny with three threads, and 19.1 fps for Nano with two threads. These are detector-only timings, not end-to-end throughput or counting accuracy. Tiny was selected as a starting compromise.

**The pretrained model has not been validated for this downward fisheye view.** Accuracy can fail with occlusion, groups, track fragmentation or people too close to image edges. A missed detection cannot be repaired by the counting logic. Tune position, region, confidence and model using manually observed traversals; custom overhead training may be needed. Do not present estimates as audited attendance.

## Data and API

Only aggregate sessions, minute counts, corrections and calibration are written to SQLite. No raw detection boxes, track IDs, pictures, video, names or appearance features are persisted. The live preview is a single in-memory JPEG, authenticated and served with `Cache-Control: no-store`. MediaMTX recording remains disabled. Application access logging is disabled; exception details exposed to the UI exclude camera URLs and credentials.

| Endpoint | Purpose |
|---|---|
| `GET /healthz` | Process liveness; no attendance data |
| `GET /readyz` | 200 only with a fresh processed frame and saved calibration |
| `GET /api/status` | Connection, calibration and active aggregate counts |
| `PUT /api/calibration` | Save normalized region, axis, line, direction and deadband |
| `POST /api/sessions` | Start with JSON `{"occupancy": 0}` |
| `POST /api/session/reconcile` | Set the current observed headcount |
| `POST /api/session/end` | End the active session |
| `GET /api/sessions` | Most recent 100 session summaries |
| `GET /api/sessions/{id}/counts.csv` | Aggregate minute export |
| `GET /api/preview.jpg` | Current in-memory annotated frame; 503 if stale |

With a token configured, everything except `/healthz` requires HTTP Basic authentication. Keep access behind SSH, Tailscale or a correctly configured HTTPS proxy. The API rejects cross-origin browser mutations and unrecognized Host headers.
