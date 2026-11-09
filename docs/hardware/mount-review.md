# Mount review after makerspace feedback

Reviewed 2026-11-09 against the active Fusion v10 document, its construction scripts, and the exported STL orientations. This records the findings that led to [v11](./v11/README.md), now implemented with adjustable padded clamps and a revised print layout. Existing v10 files remain prototype history. The original review below describes the decisions; v11's guide and validation reports describe the delivered geometry and its remaining physical checks.

## What the current geometry establishes

- The two arms are fixed hooks. There is no movable jaw, adjustment screw, latch, or other mechanism to set their gripping force.
- Each 3 mm rubber pad is modeled at 2.5 mm thickness. Grip therefore depends on real frame dimensions, pad stiffness, pad compression and printed dimensions. No clamping-force or retention measurement has been made. Geometric contact is not proof of clamping force.
- The ledges carry weight, but there is no independent latch blocking withdrawal toward the room. The mount can be removed by reversing the installation slide, subject to friction.
- The simplified camera lens extends to Z=-32.7 mm; the guard bottom is Z=-29 mm. The model consequently leaves 3.7 mm of lens protruding. Actual lens extension was never dimensioned by the shared PCB drawing, so this is a model finding, not an actual lens measurement.
- The main STL prints on its side, with world X becoming print Z. Its size is 68.65 x 180.5 x 214 mm. That keeps the hook profiles in the layer planes, but the second integral hook and camera holder create substantial support requirements. The part is not optimized for minimal supports.

## Proposed retention revision

Use two identical removable C-shaped clamp brackets. Each should carry the enclosure through a mechanically captured, bench-assembled connection, with a padded fixed upper jaw and an adjustable lower pressure shoe pressing upward against the underside of the frame. Position the opposed contact patches over one another where the measured frame allows, reducing the twisting caused by offset contacts.

If hand tightening underneath the installed frame is acceptable, use a metal screw and captive metal nut in each bracket, a hand knob and a captive padded shoe. The screw moves the shoe; it does not screw into the frame. Do not use direct plastic threads for the regularly adjusted clamp. Exact screw size, length, jaw travel and nut pockets must be dimensioned in the new revision; no hardware purchase list is released by this review.

The previous requirement was no tightening at height. A screw clamp cannot be fully tightened on a table and then slid onto the frame while retaining that same grip. Reachability of two hand knobs is therefore still an open requirement. If no tightening is possible, investigate a reachable, positively locking lever mechanism instead. A lever still needs an accessible actuation point and verified frame fit.

Provide an attachment for an independent tether to a suitable separate anchor. Lens protection also needs revision, with any guard checked against the actual fisheye view. Neither filament choice nor a snap-on guard establishes drop protection.

## Proposed print layout

| Part | Design and orientation target |
| --- | --- |
| Two identical clamp brackets | Broad side flat on the bed, C profile in each layer; keep roots rounded within that plane. Avoid making the clamp load peel the layers apart. |
| Electronics case | Flat back on the bed, cavity opening upward, after separating the projecting mount/camera geometry that prevents this orientation in v10. |
| Cover | Broad outer face down; design clips and ribbon-roof transitions for that orientation. |
| Camera support/guard | Give these a separate suitable flat print face if retaining them on the case would require large support structures; preserve the straight-down view and covered ribbon route. |
| Knobs and pressure shoes, if used | Flat base down, accessible captive-nut/head pockets and no trapped support. |

Use 45-degree sloping undersides at print overhangs, teardrop or chamfered roofs over horizontal holes, and short bridges with material anchored at both ends. A free-ended hook is a cantilever, not a bridge. Do not bridge the large gap between mounting arms or trade away root strength just to remove supports. Keep fillets where they relieve structural stress; use chamfers for bed-facing transitions where a fillet would create a steep overhang.

These changes may add a few simple, repeated parts and bench assembly steps while reducing tall supported prints and making an individual clamp replaceable. The H2D Pro slice preview must still confirm printable starts, bridge direction, support removal and layer orientation; no support-volume or print-time reduction has yet been measured. Bambu Studio is not installed on the Mac used for this review.

The user has explicitly declined coupons. Do not include coupons or frame gauges in the next print package. Physical checks can use the actual revised components and a low-height loaded assembly.

## Material choice

Recommend unfilled PETG for the brackets, snap features and warm electronics enclosure because of its toughness, flexibility and heat tolerance. PLA is an option for fit mockups or non-flexing, non-load-bearing pieces if temperature permits. Material choice does not resolve the missing adjustable grip, and neither material gives a fall-survival guarantee. The actual print profile, orientation and joints matter as well.

Sources: [Prusa PETG guidance](https://help.prusa3d.com/article/petg_2059), [Prusa PLA guidance](https://help.prusa3d.com/article/pla_2062), [modeling for printing](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135), and [bridging guidance](https://help.prusa3d.com/article/poor-bridging_1802). The design proposals above are engineering judgments applied to the local model, not a validated load rating.
