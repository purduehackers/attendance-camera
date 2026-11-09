#!/usr/bin/env bash
# Install on the Pi only. Requires configured Tailscale and a working camera.
set -euo pipefail
project_install_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
service_user=""
tailnet_ip=""
while (($#)); do
  case "$1" in
    --user) service_user="${2:?Missing --user value}"; shift 2 ;;
    --tailscale-ip) tailnet_ip="${2:?Missing --tailscale-ip value}"; shift 2 ;;
    *) printf 'Usage: sudo %s --user USER --tailscale-ip IP\n' "$0" >&2; exit 2 ;;
  esac
done
[[ $EUID -eq 0 ]] || { printf 'Run with sudo on the Pi.\n' >&2; exit 1; }
[[ "$(uname -s)" == Linux && "$(uname -m)" == aarch64 ]] || { printf 'Requires 64-bit ARM Linux.\n' >&2; exit 1; }
[[ -n "$service_user" && -n "$tailnet_ip" ]] || { printf 'Both --user and --tailscale-ip are required.\n' >&2; exit 2; }
for program in python3 curl sha256sum tar systemctl ip; do command -v "$program" >/dev/null; done
id "$service_user" >/dev/null
getent group video >/dev/null
getent group render >/dev/null
systemctl is-active --quiet tailscaled
ip -4 -o address show dev tailscale0 | grep -Fq " $tailnet_ip/" || { printf 'Address is not assigned to tailscale0.\n' >&2; exit 1; }

project_stage_dir="$(mktemp -d)"
trap 'rm -rf -- "$project_stage_dir"' EXIT
python3 "$project_install_dir/../src/render_config.py" --tailscale-ip "$tailnet_ip" --user "$service_user" --output "$project_stage_dir/config"
readarray -t release < <(python3 - "$project_install_dir/mediamtx-release.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
for key in ('url', 'sha256', 'deployed_binary_sha256'):
    print(r[key])
PY
)
curl --fail --location --proto '=https' --tlsv1.2 "${release[0]}" --output "$project_stage_dir/mediamtx.tar.gz"
printf '%s  %s\n' "${release[1]}" "$project_stage_dir/mediamtx.tar.gz" | sha256sum --check --status
tar -xzf "$project_stage_dir/mediamtx.tar.gz" -C "$project_stage_dir" mediamtx LICENSE
printf '%s  %s\n' "${release[2]}" "$project_stage_dir/mediamtx" | sha256sum --check --status

# Stage and verify everything before replacing the existing service files.
install -d -m 755 /opt/camera-feed /etc/camera-feed
for file in /etc/camera-feed/mediamtx.yml /etc/systemd/system/camera-feed.service; do
  if [[ -f "$file" ]]; then cp -p -- "$file" "$file.backup-$(date +%Y%m%d-%H%M%S)"; fi
done
if [[ -f /opt/camera-feed/mediamtx ]]; then cp -p /opt/camera-feed/mediamtx /opt/camera-feed/mediamtx.previous; fi
systemctl stop camera-feed.service 2>/dev/null || true
install -m 755 "$project_stage_dir/mediamtx" /opt/camera-feed/mediamtx
install -m 644 "$project_stage_dir/LICENSE" /opt/camera-feed/LICENSE
install -m 644 "$project_stage_dir/config/mediamtx.yml" /etc/camera-feed/mediamtx.yml
install -m 644 "$project_stage_dir/config/camera-feed.service" /etc/systemd/system/camera-feed.service
systemctl daemon-reload
systemctl enable --now camera-feed.service
systemctl --no-pager --full status camera-feed.service
printf '\nRTSP: rtsp://%s:8554/cam\nBrowser: http://%s:8889/cam\n' "$tailnet_ip" "$tailnet_ip"
