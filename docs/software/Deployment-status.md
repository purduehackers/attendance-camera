# Deployment handoff — November 9, 2026

The authenticated dashboard is live at **https://attendance.purduehackers.com**. Sign in with Purdue Hackers ID; only the signed `organizer` or `admin` role is accepted. Sessions expire after one hour. The Vercel project is `attendance-camera` in the `purdue-hackers` team and deploys from this repository's `main` branch.

Both `attendance-server.service` and `attendance-bridge.service` run as enabled systemd user services under `p-attendance`. The Redis service is the existing shared PH instance; nothing was provisioned on Upstash. Video uses transient Pub/Sub messages, while the counting worker keeps aggregate records in its existing SQLite database.

## ID, dashboard, and Redis

The public dashboard uses the official Purdue Hackers Astro components and theme.
The Rust relay handles OpenID Connect with PKCE, browser-bound state, nonce and
signature verification. The registered callback is
`https://attendance.purduehackers.com/api/auth/callback/purduehackers` and the
requested scopes are `openid profile roles`. Client secrets stay in private
Vercel environment variables. The old shared browser password is no longer
accepted by the public relay; the worker keeps its separate loopback credential.

The `attendance` user now exists in `/etc/redis/acl.conf`. Its saved credential
has been verified over TLS, loaded into the bridge and Vercel, and synchronized
with the running Redis user. The temporary previous password was removed.
The old generated `local/redis-attendance.acl` is superseded; do not append it.
Short-lived authentication state uses expiring `attendance:v1:auth:*` keys.
Video and control messages continue to use transient Pub/Sub.

## Remaining: install the Pi publisher

The Pi still provides its H.264 1920×1080 30 fps feed, but SSH closes before authentication. An earlier shell also reported an I/O error. The new publisher cannot be installed until shell access is restored.

An ARM64 binary, systemd unit, private publisher configuration and installer are ready in `local/pi-publisher/` on the development Mac and `/proj/attendance/attendance-camera/local/pi-publisher/` on the PH server. This directory contains the camera publishing token and must not be committed or published. The Pi receives no Redis credential or organizer password.

Once SSH works:

1. Install FFmpeg on the Pi if absent, transfer the private bundle, and run its `install.sh` with sudo.
2. Verify the publisher's service and a live decode at the PH bridge's loopback `http://127.0.0.1:18555/cam.ts`.
3. Set `ATTENDANCE_CAMERA_URL=http://127.0.0.1:18555/cam.ts` in the worker's private `local/server.env`, then restart `attendance-server.service` as `p-attendance`.
4. Verify fresh status and preview through the website. Run controlled entry/exit checks after the camera is mounted and calibrated.
5. Disable the Pi's old `attendance-camera-tunnel.service`, verify the new path remains healthy, then remove only its dedicated restricted key from the original SSH account.

Until these steps are completed, the normal feed keeps using its existing SSH tunnel. The new video path was tested using a **temporary Mac publisher**, which was stopped afterward; normal operation does not depend on that test process. The public dashboard already communicates with the PH worker through the new Redis bridge.

See [Transport](./Transport.md) for configuration, architecture and rollback details, and [verification status](../verification.md) for measured results and remaining hardware validation.
