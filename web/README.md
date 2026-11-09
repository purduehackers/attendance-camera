# Attendance dashboard

Static Astro pages, served by the Rust relay. Purdue Hackers components and the
theme were copied from the official [registry](https://components.purduehackers.com)
on November 9, 2026, following its [skill](https://components.purduehackers.com/skill/SKILL.md).
The copied components live in `src/components/ph`, with the unmodified theme in
`src/styles/ph.css`. Pixel icons are the HackerNoon Pixel Icon Library, CC BY 4.0.

```bash
bun install --frozen-lockfile
bun test tests
bun run build
```

Commit `built/` with source changes. Rust embeds these generated files so Vercel,
the PH server, and Pi Cargo builds need no JavaScript runtime. CI rebuilds the
dashboard and rejects stale output. Rebuild Rust after changing the assets.

The public relay requires Purdue Hackers ID. The older Python static dashboard
remains available only through the private loopback API for diagnostics.

The camera preview opens automatically at the top of the dashboard. It displays
the latest annotated JPEG about once a second, independently of status polling.
Hiding the preview or switching tabs cancels its request and releases the image.
Connection failures clear the old frame and show a reconnect message; successful
polls clear their own errors without hiding failed organizer actions.
