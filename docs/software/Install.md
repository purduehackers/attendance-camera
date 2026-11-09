# Camera feed

This captures the working Pi deployment as portable templates, with a new installer for reproducing it. The deployed configuration and binary were checked on 2026-11-08; the installer has not yet been exercised on a fresh Pi. See [verification](../verification.md).

MediaMTX is pinned to [v1.21.3](https://github.com/bluenviron/mediamtx/releases/tag/v1.21.3). The installer downloads the official ARM64 archive, verifies its SHA-256 and the extracted binary against [mediamtx-release.json](../../install/mediamtx-release.json), and installs the upstream license alongside it. No MediaMTX binary is vendored here.

## Configure and install

Run on the Pi from a checkout of this repository. Replace the shell variables with the Pi's Tailscale IPv4 address and an existing local account. Do not commit these values.

```sh
tailscale ip -4
export CAMERA_TAILSCALE_IP='replace-with-pi-tailscale-ip'
export CAMERA_SERVICE_USER='replace-with-existing-linux-user'

# Optional: inspect the rendered files before installation.
python3 src/render_config.py \
  --tailscale-ip "$CAMERA_TAILSCALE_IP" \
  --user "$CAMERA_SERVICE_USER"

sudo bash install/install.sh \
  --tailscale-ip "$CAMERA_TAILSCALE_IP" \
  --user "$CAMERA_SERVICE_USER"
```

The renderer only accepts an IPv4 address in Tailscale's `100.64.0.0/10` range. The installer also checks that the address is assigned to `tailscale0`. It installs:

| Location | Purpose |
|---|---|
| `/opt/camera-feed/mediamtx` | Pinned streaming server |
| `/opt/camera-feed/LICENSE` | MediaMTX upstream license |
| `/etc/camera-feed/mediamtx.yml` | Rendered camera configuration |
| `/etc/systemd/system/camera-feed.service` | Enabled boot service |

It backs up existing configuration and unit files with timestamp suffixes, saves the previous binary as `mediamtx.previous`, and restarts the camera service. Repeated installs replace that single previous-binary backup. Installation does not configure Wi-Fi, authenticate Tailscale or update the operating system.

The service waits for its configured Tailscale address before starting and restarts after failures. Changing the Pi's Tailscale address requires rendering and installing the configuration again.

## Maintenance

```sh
systemctl --no-pager --full status camera-feed.service
journalctl -u camera-feed.service -b --no-pager -n 100
sudo systemctl restart camera-feed.service
sudo systemctl disable --now camera-feed.service
```

For a rollback, stop the service, restore a matching saved unit/config pair and the previous binary, then run `sudo systemctl daemon-reload` and `sudo systemctl start camera-feed.service`. Check the journal after any change. Keep machine-specific diagnostics and generated files under the ignored `local/` or `build/` directories.
