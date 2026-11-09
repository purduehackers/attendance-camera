# Software

This directory documents the camera feed for `attendance-camera`.

MediaMTX on the Pi provides the camera feed. A separate Python server performs local person detection and tracking, counts entrances/exits, and maintains an occupancy estimate. It includes an organizer dashboard and saves aggregate counts to SQLite.

## Contents

- [Setup](./Setup.md)
- [Install](./Install.md)
- [Local Development](./LocalDevelopment.md)
- [Attendance server: deployment and calibration](./Server.md)

`Setup` and `Install` cover the Pi. `Server` covers the PH server that consumes its feed.
