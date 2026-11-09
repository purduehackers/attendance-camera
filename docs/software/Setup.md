# Setup

## Requirements

- Raspberry Pi 4 running 64-bit Raspberry Pi OS / Debian with the Raspberry Pi camera stack. The observed device runs Debian 13 (trixie), architecture `aarch64`.
- A working CSI camera. With power disconnected, connect the ribbon in the correct orientation. After boot, check detection with `rpicam-hello --list-cameras`.
- Network access configured on the Pi and an authenticated, running Tailscale installation. PAL3.0 enterprise Wi-Fi credentials and authentication settings must be configured locally; this repo does not install a campus network profile.
- An existing non-root Linux account able to use the camera, plus the `video` and `render` groups. Python 3, curl, tar, coreutils, iproute2 and systemd are required.

## View the feed

Connect the viewing device to the same tailnet, with access allowed by its policy:

- Browser/WebRTC: `http://<PI_TAILSCALE_IP>:8889/cam`
- VLC or another RTSP client: `rtsp://<PI_TAILSCALE_IP>:8554/cam` using RTSP-over-TCP.

All listener addresses bind to the Pi's Tailscale IP. RTSP uses TCP 8554; WebRTC uses HTTP 8889 and media on UDP/TCP 8189. Configure tailnet grants/ACLs for the intended viewers. The MediaMTX read permission accepts any allowed source in the Tailscale IPv4 range; there is no separate viewer password. Tailscale supplies transport encryption and access control. Do not expose these ports publicly or enable Funnel for this configuration.

The `cam` path runs continuously at 1920 × 1080, 30 fps, 8 Mbps, hardware H.264 baseline with a 30-frame keyframe interval. Recording, RTMP, HLS, SRT, MoQ, API, metrics and profiling are disabled. The separate [attendance server](Server.md) consumes RTSP and stores counts, without recording footage.


Next: [install the feed](Install.md).
