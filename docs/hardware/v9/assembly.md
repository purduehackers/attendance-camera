# Doorframe camera — reinforced PETG v9

**Three installed printed parts, eight screws, eight heat-set inserts, no nuts.** This revision supersedes v6–v8. The case, hanging arms and downward camera holder are one printed body. The front cover and camera guard clip on. All electronics fastening happens at table height; nothing is tightened at the doorframe.

## Parts and files

1. `01-integral-case-mount-and-camera-holder.stl`
2. `02-snap-on-front-cover.stl`
3. `03-snap-on-downward-camera-guard.stl`

The two other STLs are optional test pieces: the upward-step fit gauge and heat-set insert coupon. They are not installed parts.

`doorframe-camera-simple-v9.f3d` is the native editable Fusion design; the STEP file includes reference hardware and frame. `three-parts.png` shows the three installed prints separated. `assembly.png`, `side-profile.png`, `inside.png`, `ribbon-route.png` (cover removed), and `logo-front.png` show the assembled model. `validation.json` and `mesh-validation.json` record the checks.

## Changes in this revision

The camera support now shares the front/back planes of the two outer mounting arms. Its earlier projecting ribs are gone. The camera pod still extends beneath the lip so the lens can face straight downward. The existing front cover has a continuous roof over the ribbon channel, with two small release catches near the bottom; no fourth printed part was added.

The official flat Purdue Hackers logo is recessed into the front cover below the vents, 32 mm wide and 0.6 mm deep, with 1.4 mm wall remaining. A tiny 0.4 mm corner chamfer prevents a nonmanifold point contact in the original artwork. Yellow in the render indicates an optional paint fill. The STL is a single-material solid. Source: https://www.purduehackers.com/ph.svg.

The two hook toes are 7 mm thick, 6.5 mm beneath their pad recesses, with rounded upper roots and inner knees. The cover clip roots are rounded too. These changes improve the geometry for a PETG prototype; they do not establish a load rating.

**Use [printing instructions](printing.md): PETG, 0.20 mm layers, 6 walls, 30% global infill, 6 top/bottom layers, and local solid infill around the hooks.** The main STL is supplied on its side so the hook profiles lie in the print layer planes.

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

The snap cover provides service access to GPIO and ribbon connectors. microSD servicing may require lifting the whole unit off the frame; an external card-eject slot is not modeled. Release the two lower ribbon-roof catches and the cover's four top/bottom clips through their windows before pulling it toward the room. The cover does not carry the camera or hanging loads.

## Printing and assembly

Print the profile gauge first to check the actual frame. The insert coupon is an optional fit check and practice piece: the smaller boss tests M2 and the larger boss tests M2.5. Use it if the insert fit or heat-setting process has not already been verified with the same inserts, material, settings and hole orientation. It does not establish the strength of the whole case. Fit-test the actual camera lens against the guard as well.

The integral body's supplied print orientation is **68.65 × 180.5 × 214 mm**, with the case on its side. This places the hook profiles in the layer planes. It requires removable supports and a brim. The front cover is outer-face-down, **213.6 × 170.8 × 14.4 mm**, with local supports under the raised ribbon-roof extension and clip overhangs as needed. The camera guard is on its side so its clip beams lie in the layer planes. The insert coupon is also on its side to test horizontal holes like those on the main print. Follow the admin notes and inspect the actual slice preview. No G-code or Bambu Studio project is supplied, and no physical print has been tested.

With the electronics removed, install the eight heat-set inserts flush with their mounting faces using the correct installation tip. Allow them to cool before installing the Pi and camera. Do not heat-set an insert against an installed PCB. Mount the boards using the screws listed above, retain the battery with the two straps, lay the ribbon in the open channel and route it through the floor entry with gentle bends, then clip on the guard and the cover with its integrated ribbon roof. The clear tunnel is 18 mm wide and 3.2 mm deep; the illustrative ribbon is assumed to be 16 × 0.35 mm. Its full route to the Pi connector, stiffeners and actual bend radius need physical verification. Verify the ribbon length and orientation; a longer cable may be needed.

The camera uses the Waveshare RPi Camera G PCB, 25×24 mm, with verified 21×13.5 mm hole pitch. The lens points straight downward under the front edge of the frame. The 22 mm guard opening surrounds a simplified lens envelope; the actual lens diameter and extension remain to be fit-tested. The lens must project beyond the guard.

## Doorframe fit and checks

The frame underside is Z=0. Its front face at Y=0 rises 55 mm, followed by a 12 mm ledge, a further 12 mm rise, and an 11 mm upper ledge. Positive Y points toward the wall/door. The model conservatively assumes a wall beyond Y=23 above the upper ledge; the door boundary is Y=52. The case ends at Y=22.4 and the retaining arms at Y=45. Actual door movement still needs checking.

Four pads support the two upward-facing ledges. Two integral arms catch beneath the 52 mm overhang. The pads are modeled as 3 mm stock compressed to 2.5 mm. Slide the preassembled unit on from the room side; there are no mounting screws or adjustable clamps. Fit depends on the real trim, pad hardness and print tolerance. Do not force it; change pad thickness or the model if necessary.

The native model has three single-solid installed parts and no positive-volume interference, including the access corridors. All five STL meshes passed closed-edge, connected-component, consistent-winding and positive-volume checks. The optical axis was checked from the camera transform. These checks do not test actual snap force, printed strength, pad creep, cable bends or thermal behavior. Estimated weight distribution falls over the ledges but has a small forward margin; the underside arms are required for retention. Test the full loaded assembly at a low height before overhead mounting, and use a retaining tether where a fall could hit someone.

Hardware identity sources: [Duckietown components](https://docs.duckietown.com/daffy/opmanual-dd24/preliminaries/dd24-components-description.html#rpi-camera-g-with-fisheye-lens-and-cable), [Waveshare Camera G](https://www.waveshare.com/product/rpi-camera-g.htm), [Pi4 mechanical drawing](https://datasheets.raspberrypi.com/rpi4/raspberry-pi-4-mechanical-drawing.pdf), [INIU P51L-E2](https://iniushop.com/products/iniu-p51l-e2-power-bank-45w-20000mah).
