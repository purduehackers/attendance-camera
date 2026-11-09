> Historical revision: superseded by [v9](../v9/). File lists below describe the original export; only native designs and reports are retained here.

# Doorframe camera — simple v6

**Three installed printed parts, eight screws, eight heat-set inserts, no nuts.** This revision supersedes v5. The case, hanging arms and downward camera holder are one printed body. The front cover and camera guard clip on. All electronics fastening happens at table height; nothing is tightened at the doorframe.

## Parts and files

1. `01-integral-case-mount-and-camera-holder.stl`
2. `02-snap-on-front-cover.stl`
3. `03-snap-on-downward-camera-guard.stl`

The two other STLs are optional test pieces: the upward-step fit gauge and heat-set insert coupon. They are not installed parts.

`doorframe-camera-simple-v6.f3d` is the native editable Fusion design; the STEP file includes reference hardware and frame. `three-parts.png` shows the three installed prints separated. `assembly.png`, `side-profile.png`, and `inside.png` show the assembled model. `validation.json` and `mesh-validation.json` record the checks.

## Exact hardware to use

| Quantity | Part | Purpose |
|---|---|---|
| 4 | M2.5 × 6 mm socket-cap screws, ISO 4762 / DIN 912, coarse pitch 0.45 mm | Pi |
| 4 | CNC Kitchen M2.5 × 4 mm heat-set inserts, TC-M2.5x4.0 | Pi mounts |
| 4 | M2 × 4 mm socket-cap screws, ISO 4762 / DIN 912, coarse pitch 0.4 mm | Camera PCB |
| 4 | CNC Kitchen M2 × 3 mm heat-set inserts | Camera mounts |
| 2 | 10 mm hook-and-loop straps | Retain the battery |
| 2 each | 20×10×3, 20×9×3 and 16×14×3 mm soft rubber/neoprene pads | Frame contacts |
| As needed | Soft battery padding and suitable USB-C power lead | Battery support and Pi power |

Screw lengths are measured under the head. The M2 screws use a 1.5 mm hex key; M2.5 uses a 2 mm hex key. Use socket-cap heads, not countersunk heads against the PCBs.

The pockets follow the **specified manufacturer's insert geometry**, which is not interchangeable with every insert sold under the same thread size:

| Insert | Insert outside diameter | Insert length | Printed pocket | Boss outside diameter |
|---|---:|---:|---:|---:|
| CNC Kitchen M2 × 3 | 3.6 mm | 3 mm | Ø3.2 × 4 mm deep | 6.4 mm |
| CNC Kitchen M2.5 × 4 | 4.6 mm | 4 mm | Ø4.0 × 5 mm deep | 8.0 mm |

Both pockets include the manufacturer's 1 mm depth allowance beyond the insert length. Nominal screw projection is 2.8 mm through the camera PCB and 4.4 mm through the Pi PCB, leaving room before each pocket bottom. The camera PCB thickness is an assumed 1.2 mm; check the actual board before tightening.

Sources: [CNC Kitchen dimension drawing](https://cnckitchen.store/cdn/shop/files/Table_Metic.png), [M2 insert](https://cnckitchen.store/products/heat-set-insert-m2-x-3-100-pieces), [M2.5 insert](https://cnckitchen.store/products/gewindeeinsatz-threaded-insert-m2-5-standard-100-stk-pcs), [M2×4 screw specification](https://www.accu.co.uk/metric-cap-head-screws/3790-SSCF-M2-4-A2), [M2.5×6 screw specification](https://www.accu.co.uk/metric-cap-head-screws/3804-SSCF-M2-5-6-A2). These are dimensional references, not purchases or a claim of current stock.

## Access to charging and Pi ports

The battery sits on the left with its charging/USB end facing the large left opening. That opening spans the battery's full end height, so charging does not require opening the cover. This targets INIU Carry P51L-E2, 115×73×29 mm; confirm the actual pack and its port end before printing.

The Pi sits on the right. USB and Ethernet face upward through a common top opening. USB-C power, micro-HDMI and audio face the right-side opening. Clearance corridors through these openings were checked in CAD. Actual cable housings and bend radii vary and were not modeled. Allow room above and beside the mounted case for connected cables. A short USB power lead can run between the exposed battery and Pi side openings; cable routing is not limited to an enclosed internal path.

The snap cover provides service access to GPIO and ribbon connectors. microSD servicing may require lifting the whole unit off the frame; an external card-eject slot is not modeled. Release the cover's top and bottom clips through their windows, then pull it toward the room. The cover does not carry the camera or hanging loads.

## Printing and assembly

Print the profile gauge and insert coupon first. On the coupon, the smaller boss tests M2 and the larger boss tests M2.5. Heat-set the inserts into the coupon using the same material and print settings before committing to the main body. Fit-test the actual camera lens against the guard as well.

The integral body's oriented bounding box is **214 × 180.5 × 68.65 mm**. It needs removable supports under the elevated case and camera features; fewer assembly joints are the tradeoff for a more supported print. Verify support access in the slicer, especially the heat-set pockets, ribbon channel and under-hooks. A 220 mm bed has little spare room for a brim across the 214 mm width. The front cover and camera guard are supplied flat-face-down with their clips pointing up. PETG is a prototype material choice; use at least five perimeters around the integral retaining arms and inspect the printed layer bonding. No physical print has been tested.

With the electronics removed, install the eight heat-set inserts flush with their mounting faces using the correct installation tip. Allow them to cool before installing the Pi and camera. Do not heat-set an insert against an installed PCB. Mount the boards using the screws listed above, retain the battery with the two straps, route the ribbon with a loose bend through the open camera spine and floor entry, then clip on the guard and cover. Verify the ribbon length and orientation; a longer cable may be needed.

The camera uses the Waveshare RPi Camera G PCB, 25×24 mm, with verified 21×13.5 mm hole pitch. The lens points straight downward under the front edge of the frame. The 22 mm guard opening surrounds a simplified lens envelope; the actual lens diameter and extension remain to be fit-tested. The lens must project beyond the guard.

## Doorframe fit and checks

The frame underside is Z=0. Its front face at Y=0 rises 55 mm, followed by a 12 mm ledge, a further 12 mm rise, and an 11 mm upper ledge. Positive Y points toward the wall/door. The model conservatively assumes a wall beyond Y=23 above the upper ledge; the door boundary is Y=52. The case ends at Y=22.4 and the retaining arms at Y=45. Actual door movement still needs checking.

Four pads support the two upward-facing ledges. Two integral arms catch beneath the 52 mm overhang. The pads are modeled as 3 mm stock compressed to 2.5 mm. Slide the preassembled unit on from the room side; there are no mounting screws or adjustable clamps. Fit depends on the real trim, pad hardness and print tolerance. Do not force it; change pad thickness or the model if necessary.

The native model has three single-solid installed parts and no positive-volume interference, including the access corridors. All five STL meshes passed closed-edge and positive-volume checks. The optical axis was checked from the camera transform. These checks do not test actual snap force, printed strength, pad creep, cable bends or thermal behavior. Estimated weight distribution falls over the ledges but has a small forward margin; the underside arms are required for retention. Test the full loaded assembly at a low height before overhead mounting, and use a retaining tether where a fall could hit someone.

Hardware identity sources: [Duckietown components](https://docs.duckietown.com/daffy/opmanual-dd24/preliminaries/dd24-components-description.html#rpi-camera-g-with-fisheye-lens-and-cable), [Waveshare Camera G](https://www.waveshare.com/product/rpi-camera-g.htm), [Pi4 mechanical drawing](https://datasheets.raspberrypi.com/rpi4/raspberry-pi-4-mechanical-drawing.pdf), [INIU P51L-E2](https://iniushop.com/products/iniu-p51l-e2-power-bank-45w-20000mah).
