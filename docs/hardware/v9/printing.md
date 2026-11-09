# Camera case v9 — Bambu H2D Pro print request

Please use the **v9 STLs**, in millimeters at **100% scale**. There are three installed parts and two small fit-test pieces. Please print the frame-fit gauge first. The insert coupon is optional if this insert/filament/process combination is already verified. This is a functional prototype, not a tested overhead mounting product.

| Setting | Requested value |
|---|---|
| Material | Unfilled PETG; use a calibrated profile for the actual filament |
| Nozzle | 0.4 mm |
| Layer height | 0.20 mm |
| Walls | 6 |
| Global infill | 30%, gyroid preferred |
| Top / bottom | 6 solid layers each, 1.2 mm nominal |
| Local infill | 100% modifiers around the two retaining arms, including their roots and toes |
| Speed | Normal calibrated profile; no Sport/Ludicrous multiplier |
| Supports | Required on part 01; inspect parts 02, 03 and the coupon for local supports |
| Units / scale | Millimeters / 100%; do not scale parts to compensate for fit |

Use dry filament and the manufacturer's PETG profile. Please inspect the sliced layer preview for missing thin features, unsupported islands and support removal access. No G-code or verified Bambu Studio project is supplied. The STLs are oriented, but support placement and slicing still require operator review.

## Preserve these orientations

| STL | Oriented size X × Y × Z, mm | Orientation and reason |
|---|---|---|
| 01 integral case | 68.65 × 180.50 × 214.00 | On its side: the two hook profiles lie in the layer planes. Do not stand it in the installed orientation or rotate it flat on its back merely to reduce height. |
| 02 front cover | 213.60 × 170.80 × 14.40 | Broad outer face down. Support the raised ribbon-roof extension and any unsupported clip overhangs. This cover carries no mounting load. |
| 03 camera guard | 47.60 × 23.60 × 47.60 | On its side to place the long camera clip beams in the layer planes. Support the opening/overhangs as needed. |
| 07 frame fit gauge | 26 × 70 × 8 | Side profile flat on the plate. |
| 08 insert coupon | 16 × 8 × 35 | On its side, with horizontal insert holes, matching the main body's hole orientation. Support boss overhangs without packing the blind holes. |

Print separate plates as appropriate. All individual part envelopes fit within the H2D Pro build volume. Reserve room for support, brim and any purge tower; this is not a claim that all parts fit one plate.

For part 01, use a brim for the relatively narrow footprint; start around 8 mm and adjust with the actual plate/filament profile. The distant mounting arm, camera cradle, port cutouts and insert bosses need careful support review. Support must be removable through the open front and ports. Do not trap support inside blind insert pockets or the small clip clearances. A compatible dedicated support interface on the second nozzle is useful if available; the operator should select and calibrate that profile.

For local infill modifiers on part 01, the two arms occupy these approximate boxes in the supplied STL coordinates: X=9.65..68.65, Y=4.5..82.7, Z=12..38 and Z=176..202 mm. Extend each modifier slightly to cover the whole root. Other thin walls, clip beams and insert bosses should resolve largely or entirely as solid perimeter paths; verify this in the slice preview.

The front cover's shallow recessed logo needs a clean bridge over each recess with its outer face down. Yellow shown in the CAD is an optional paint fill, not a separate printed part or a required material change. Keep supports away from its cosmetic recess if bridging is adequate.

Please do not substitute PLA for the installed parts without revisiting the snap fits and warm loaded testing. PLA is acceptable for a preliminary dimensional gauge. PETG is selected for its toughness and temperature resistance, not as a guarantee against creep.

## Checks before a full print / overhead installation

1. Check the frame gauge with the intended 3 mm soft pads. Confirm the actual frame profile and door swing; do not force a tight print into place.
2. Optional insert practice: heat-set the specified CNC Kitchen M2 and M2.5 inserts in the coupon. Check insertion, surrounding plastic and screw fit before committing to the full case.
3. Inspect the printed hooks, root fillets, thin clips and insert bosses for gaps or poor layer bonding. Assemble the electronics on a table. The covers should latch without forcing; do not overtighten PCB screws.
4. Test the complete loaded mount at a low height, including operation with the Pi warm and normal cable handling. Inspect for slipping, permanent bending and cracks. A brief test does not establish long-term creep performance. Use an independent retention tether for overhead use.

## What was checked

The native design has three single-solid installed parts, healthy features, and no modeled positive-volume collisions. All five exported meshes have one connected component, closed manifold edges and consistent winding. The main body's hook toes were increased from 5 to 7 mm (6.5 mm under the pad recess), the arm roots and knees have 1.5 mm fillets, and the service-cover clip roots are rounded. The 32 mm logo is recessed 0.6 mm, leaving 1.4 mm of cover behind it.

These are geometry and print-preparation checks. No FEA, slicer simulation, physical print, load rating, thermal measurement or creep test has been completed.

References: [Prusa on perimeter strength](https://help.prusa3d.com/article/infill_42), [Prusa PETG properties and support behavior](https://help.prusa3d.com/article/petg_2059), [Formlabs on FDM load orientation](https://formlabs.com/blog/strongest-3d-printing-materials/), [Bambu H2D Pro manufacturer specification sheet, mirrored by a reseller](https://robu.in/wp-content/uploads/2025/12/Bambu-Lab-H2D-Pro-Datasheet-1.pdf).
