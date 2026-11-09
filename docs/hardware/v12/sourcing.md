# v12 hardware shopping list

All four screw lengths are catalog sizes: **30, 10, 6 and 4 mm**. No screw cutting, printed screw threads or heat-set inserts are needed. Length means from the underside of the head to the tip. Supplier listings checked November 9, 2026; local stock, shipping and final prices are not confirmed.

| Need | Exact item | US purchase source / selection |
| ---: | --- | --- |
| 2 | M5-0.8 × 30 mm **fully threaded external hex-head** bolt, DIN 933 | [NutsandBolts.com MCS530CFZ88](https://nutsandbolts.com/products/m5x-8x30-hex-cap-screw-grade-8-8-zinc-plated). The page lists a 25-piece starting tier; buy spares together or match this specification from the makerspace bins. |
| 6 | M3-0.5 × 10 mm **button-head socket** screw | [Home Depot / Hillman 44456, 20-pack](https://www.homedepot.com/p/Hillman-M3-0-5-x-10-mm-Internal-Hex-Button-Head-Cap-Screws-20-Pack-44456/204801187). Listed at $5.98 per pack when checked. |
| 4 | M2.5-0.45 × 6 mm metal socket-cap screw | Check the existing Duckietown hardware first. [Home Depot / FOREVERBOLT FB3MSHCS25456P50, 50-pack](https://www.homedepot.com/p/FOREVERBOLT-M2-5-x-6-mm-Hex-Socket-Cap-Head-Stainless-Steel-Socket-Head-Cap-Screws-Treated-with-NL-19-50-Pack-FB3MSHCS25456P50/342136664) is a catalog fallback; the 50-pack is more than one camera needs. |
| 4 | M2-0.4 × 4 mm metal socket-cap screw, DIN 912 / ISO 4762 | Check the existing kit first. [Monster Bolts M2 socket caps](https://monsterbolts.com/products/socket-cap-b12-9-m2): select **M2 × 4 mm**, quantity **10**. The page defaults to a different length. |
| 2 M5 + 6 M3 | Ordinary DIN 934 metal hex nuts | Existing metric assortment, or [Monster Bolts DIN 934 nuts](https://monsterbolts.com/products/nuts-din934-316): select each size separately. |
| 6 | M3 DIN 125A flat washers | Existing assortment, or [Monster Bolts DIN 125A washers](https://monsterbolts.com/products/washers-din125a-a2): select **M3**. |

The previously linked Fgruh assortments have not been physically checked. Use their pieces only if they match the dimensions below. In particular, an assortment of socket-cap bolts does not replace the external-hex clamp bolts. The Yaocom inserts are not used.

## Match the head and nut shape

- **M5 clamp:** 8 mm across flats, 3.5 mm-high bolt head; ordinary nut 8 mm across flats × 4 mm thick. The printed knob grips the hex head. Fully threaded DIN 933 is required; a partly threaded DIN 931 bolt may run out of adjustment.
- **M3 attachment:** low button head, nominal Ø5.7 × 1.65 mm; nut 5.5 mm across flats × 2.4 mm thick. Keep the specified 10 mm length. A 12 mm screw projects into the contact-pad region.
- **M3 washer:** nominal 3.2 mm bore × 7 mm outside diameter × 0.5 mm thickness. A thicker washer reduces nut engagement.
- **PCB screws:** use the metal M2.5 × 6 and M2 × 4 screws. Nylon kit screws cannot form the plastic pilot threads. These are small, infrequently serviced direct-plastic joints; tighten gently after forming the threads with the boards removed.
- Use ordinary hex nuts in the modeled pockets. Flanged nuts, tall nuts and nylon-insert locknuts have different envelopes.

Tools: 2 mm Allen key for the M3 button heads and M2.5 socket caps, 1.5 mm for the M2 socket caps. The printed M5 knobs are hand-tightened during frame installation.

The [assembly BOM](README.md#hardware) also lists the rubber pads, battery straps, shoe retainers and independent tether. The [cable guide](cables.md) specifies the power lead and what remains to measure on the real hardware.
