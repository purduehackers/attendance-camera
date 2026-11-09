> Historical revision: superseded by [v9](../v9/). File lists below describe the original export; only native designs and reports are retained here.

# Doorframe camera — upward steps, passive hanging mount, downward camera

This v5 replaces the earlier wide box and adjustable screw clamps. The Pi and INIU battery sit upright beside each other above the frame. The Waveshare G camera hangs beneath the lip and points vertically downward. The mount uses fixed padded retaining arms: there is nothing to tighten at installation height.

**Fit-test prototype. CAD clearances and closed meshes do not establish printed strength, friction, door clearance or loaded retention. Do not print the earlier v3 files for this corrected profile.**

## What changed

- Corrected the frame: the 55 mm face rises from the underside, followed by a 12 mm ledge, another 12 mm rise and an 11 mm upper ledge.
- Replaced the 88 mm deep horizontal electronics stack with a 214 × 38.6 × 98 mm upright enclosure, excluding its feet and camera support.
- Four pads support the case across both upward-facing ledges. Two fixed C-shaped arms reach beneath the overhang to resist lifting and tipping.
- The camera optical axis is exactly world −Z. Its optical centre is under the front edge of the frame, at X=107, Y=0 in the CAD coordinates.
- A removable front panel gives access to the battery, Pi and assembly screws. The ribbon runs up an open groove in the camera support and through a front slot.

## Frame interpretation

The frame underside is Z=0. Its front face is Y=0 and rises to Z=55. The first ledge occupies Y=0…12 at Z=55. The next face, at Y=12, rises to Z=67. The upper ledge occupies Y=12…23 at Z=67. The door boundary is at Y=52. Positive Y points toward the door/wall; negative Y points into the room.

The model conservatively assumes the 11 mm upper ledge ends at a wall. The wall shown above it is illustrative, not a measured height. The electronics case ends at Y=22.4, giving 0.6 mm nominal wall clearance. Lower retaining arms end at Y=45, 7 mm before the indicated door boundary. These are profile clearances only; actual door movement and tolerances still need checking.

Top pads contact the ledges at Y=0.5…10.5 and Y=13…22. Underneath, pads contact Y=30…44. Nominal 3 mm soft rubber/neoprene is modeled compressed to 2.5 mm in 0.5 mm recesses. Actual material hardness, paint, print tolerance and frame dimensions determine the fit. Do not force a tight saddle onto the trim. Change pad thickness or the model if necessary.

## Files

- `doorframe-camera-hanging-v5.f3d`: editable native Fusion design.
- `doorframe-camera-v5-with-reference-hardware.step`: assembly, including nonprinted reference electronics, pads and frame.
- `stl/`: eight oriented print files, including the small profile gauge.
- `assembly.png`, `side-profile.png`, `inside.png`: actual CAD views.
- `validation.json`: feature health, collision results and a nominal weight-distribution estimate.
- `mesh-validation.json`: STL sizes, signed volumes and closed-edge checks.
- `doorframe_measurements.json`: dimensions, coordinate interpretation and assumptions.

## Print and fit sequence

1. Print `07-upward-step-fit-gauge-print-first.stl`. It has 0.6 mm profile clearance; check the upward ledges match the actual frame.
2. Print one retaining saddle and check its underside reach, pad fit and installation path against the real trim. It is a fit check, not a complete load-bearing mount on its own.
3. Fit-test the small camera carrier/cap against the actual camera, particularly the lens barrel. Its PCB mounting pattern is verified; the lens envelope is approximate.
4. Print the remaining parts. The shell is oriented back-down; its projecting feet and connector openings need local supports. The panel lies outer-face down. Retaining saddles and the camera support lie on their sides so perimeters can follow their bends. The camera carrier is upright and its cap is front-face down. Check the slicer preview before printing.
5. Assemble the entire unit at table height, including all screws, straps, foam pads, Pi, battery and ribbon. Slide the finished padded mount onto the frame from the room side. There are no long clamp screws, adjustable jaws or frame screws.
6. Test the fully loaded assembly on the profile at a low height first. Confirm it cannot tip, slide outward, or release when lightly disturbed, and that the printed arms do not visibly bend or creep. Check actual door travel. Use a separate retaining tether for an overhead installation where a fall could hit someone.

PETG is a prototype material choice, not a load rating. Start with 0.2 mm layers and at least five perimeters for the retaining arms and camera support. Inspect the load-path layers, pad pockets and pilot holes after printing.

## Bench-assembly hardware

| Connection | Hardware |
|---|---|
| Pi board to back-shell standoffs | 4 × M2.5×6 |
| Front panel to shell | 4 × M2.5×8 |
| Fixed retaining saddles to shell floor | 4 × M3×8 |
| Camera spine to front panel | 4 × M3×6, inserted from the panel's inside |
| Camera carrier to downward support | 4 × M3×6 |
| Camera PCB to carrier | 4 × M2×8 nylon screws and M2 nuts |
| Camera cap to carrier | 4 × M2.5×8, inserted from the carrier's back |
| Battery retention | Two 10 mm hook-and-loop straps through floor slots; soft padding under battery |
| Lower-ledge pads | 2 × 20×10×3 mm soft rubber/neoprene |
| Upper-ledge pads | 2 × 20×9×3 mm soft rubber/neoprene |
| Underside retaining pads | 2 × 16×14×3 mm soft rubber/neoprene |

Printed holes are pilots, not modeled threads. Hand-tap or use suitable plastic-thread hardware and check real screw lengths during assembly. Screw geometry is not included in this revision's interference check.

Install the Pi and battery straps before closing the front panel. Attach the camera PCB and cap to the carrier, then fasten the pod to the support and the support to the front panel. The ribbon exits toward the room, bends gently into the support groove, enters through the front slot and routes to the Pi. Verify actual cable length and connector orientation; a longer ribbon may be needed. Do not crease or tension it. The USB-C/HDMI/audio side is accessible; the bottom-facing USB/Ethernet connectors require board removal for service.

## Hardware and evidence limits

The enclosure targets INIU Carry **P51L-E2 45W 20,000 mAh, 115 × 73 × 29 mm**, not every INIU pack. The upright battery reference is X=76…191, Y=−9.6…19.4, Z=76…149. There is a cable bay at its right end, but actual USB plug shape, button position and cable bend must be checked.

The camera carrier uses the **Waveshare RPi Camera G (OV5647 fisheye)** 25 × 24 mm PCB and verified 21 × 13.5 mm hole pitch. The cap has a 22 mm lens opening. The simplified lens reference (16 mm diameter, 18 mm extension) is not a verified measurement of the actual lens. The lens must project past the cap to preserve its wide view.

The nominal centre of mass is calculated in `validation.json`, using assumed solid PETG density, manufacturer battery mass and estimated Pi/camera masses. Its vertical projection lies over the top contacts, but the forward margin is small. This does not establish stability under vibration, pad slip, printed creep or door impacts. The fixed underside arms are part of the retention, not optional decorations. This assembly has not been load-tested or thermally tested.

Sources: [Duckietown DD24/DD24-B components](https://docs.duckietown.com/daffy/opmanual-dd24/preliminaries/dd24-components-description.html#rpi-camera-g-with-fisheye-lens-and-cable), [Waveshare Camera G](https://www.waveshare.com/product/rpi-camera-g.htm), [Waveshare mechanical drawings](https://www.waveshare.com/w/upload/8/8a/RPi_Camera_E_F_G_H_Mechanical.zip), [Pi4 mechanical drawing](https://datasheets.raspberrypi.com/rpi4/raspberry-pi-4-mechanical-drawing.pdf), [INIU P51L-E2](https://iniushop.com/products/iniu-p51l-e2-power-bank-45w-20000mah).
