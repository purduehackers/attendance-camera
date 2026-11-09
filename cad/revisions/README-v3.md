> Historical revision: superseded by [v9](../v9/). File lists below describe the original export; only native designs and reports are retained here.

# Doorframe camera enclosure — mounted prototype v3

Created in Autodesk Fusion through the local MCP server on 2026-11-08. Native editable design and individual STL parts are included. **This is a fit-test prototype, now including a removable padded clamp mount sized to the supplied doorframe profile. Physical fit, door movement and loaded retention have not been tested.**

## Files

- `doorframe-camera-mounted-v3.f3d`: native Fusion document with editable sketches/features, reference hardware and measured frame profile. `doorframe-camera-prototype.f3d` is the same revision under the original filename.
- `doorframe-camera-assembly-with-reference-hardware.step`: assembly interchange file. Contains reference battery, PCB, lens, fasteners, pads and doorframe geometry; those are not printed parts.
- `prototype-stl/`: twelve individual printable prototype parts, including a small fit gauge, millimetres, oriented and lowered to the print bed.
- `assembled-preview.png` and `doorframe-side-preview.png`: views rendered from the CAD model.
- `doorframe_measurements.json`: supplied dimensions and explicit coordinate/orientation interpretation.
- `revisions/`: preserved v2 files, without the measured mount.
- `validation.json`: Fusion feature-health and interference results.
- `mesh-validation.json`: STL bounds, positive volumes and closed-edge checks.

## Hardware identification and dimensions

The user's earlier Duckiedrone setup identified a DD24-B kit. The current Duckietown manual identifies that family's supplied camera as the **Waveshare RPi Camera (G), OV5647, 160-degree fisheye**, consistent with the sensor detected on the Pi. It links directly to Waveshare's product. The camera PCB is 25 × 24 mm, with four 2.2 mm mounting holes on a **21 × 13.5 mm** rectangle. These are not the mounting dimensions assumed for a generic original Pi camera.

The original manufacturer's DWG was downloaded from its camera wiki and inspected using LibreDWG. With the ribbon exiting the bottom, the hole centres are (2, 8.5), (23, 8.5), (2, 22), and (23, 22) mm from the PCB's bottom-left corner. The optical axis is at (12.5, 15.65) mm. The source drawing and extracted dimensions are in this folder.

The shared PCB drawing does **not** dimension the G lens barrel or its focus-dependent extension. The model uses a 22 mm front opening and a simplified 16 mm diameter / 18 mm extension lens envelope for review. Those lens envelope dimensions and the assumed 1.2 mm PCB thickness are not verified measurements of the user's hardware. Test the small camera carrier and cap before printing the full case. The lens must protrude beyond the cap to avoid clipping its wide view.

The INIU compartment targets **Carry P51L-E2 45W 20,000 mAh**, whose manufacturer's dimensions are 115 × 73 × 29 mm. It does not fit every INIU 20,000 mAh model. The battery shell's corner radius, cable and button locations are simplified reference geometry; check the actual unit and cable bend before final assembly.

The Pi footprint and 58 × 49 mm mounting pattern use Raspberry Pi's Pi4 mechanical drawing. Connector envelopes are simplified. This revision assumes the bare Pi4 board, without a stacked HAT, tall cooler, or fan assembly. microSD servicing requires removing the lid; there is no external card-eject slot.

## Enclosure and assembly

The main box is 142 × 88 × 71.4 mm, excluding screw heads, camera projection and rubber pads. The battery sits below the Pi, separated by the Pi tray. Four 20 × 10 × 3 mm rubber pads fit 0.8 mm underside recesses and project 2.2 mm below the floor. Use two 10 mm hook-and-loop straps through the lower tray slots to retain the battery, with approximately 2 mm soft padding under it.

The camera sits in a separate protective pod on a removable **45-degree downward bracket**. That angle is a provisional choice for a doorway view, pending the user's viewing direction. The ribbon runs from the pod's bottom opening through the bracket's open channel and the front slot into the Pi chamber. Route it with a loose bend; do not trap it at the tray seam.

Suggested prototype hardware:

| Connection | Hardware |
|---|---|
| Lid and Pi tray to battery tray | 4 × M3×40 screws into printed 2.5 mm pilot holes |
| Pi PCB | 4 × M2.5×8 screws into printed 2.1 mm pilot holes |
| Camera PCB | 4 × M2×8 nylon screws and M2 nuts in rear recesses |
| Camera cap to carrier | 4 × M2.5×8 screws, inserted from the carrier's rear |
| Carrier to sloping bracket | 4 × M3×8 screws |
| Sloping bracket to upper shell | 4 × M3×6 screws from inside the upper shell |
| Battery tray to mounting platform | 2 × M4×10 pan-head screws + 2 M4 nuts in side-load slots |
| Clamp guides to platform | 4 × M3×10 screws into printed 2.5 mm pilots |
| Sliding jaws to platform | 2 × M4×80 screws, 2 M4 nuts, 2 flat washers approximately 0.8 mm thick |
| Platform-to-frame pads | 4 × 20×14×3 mm soft rubber or neoprene pieces |
| Jaw-to-frame pads | 2 × 16×9×3 mm soft rubber or neoprene pieces |

Printed pilot holes are not modeled threads: hand-tap or use compatible plastic-thread hardware, and check actual screw lengths during the fit test. The bracket includes rear clearances for the camera nuts, screw tips, and cap screw heads. Fit the PCB and cap to the carrier before fastening the completed pod to the bracket. Assemble the bracket to the upper shell before stacking the trays and inserting the four long case screws.

## Printing and checks

PETG is a reasonable prototype material. Start with a 0.4 mm nozzle, 0.2 mm layers and four perimeters. The large side connector openings may need local supports; inspect the slicer preview rather than assuming a support-free print. The supplied STLs place the lid and camera cap outer faces on the bed, the bracket's case face on the bed, the clamp guides with their flanges on the bed, and the trays/carrier/platform/jaws upright. The profile gauge lies on its side. The platform is 190 × 92 mm; inspect the 7.2 mm nut-slot bridges and recesses in the slicer. Start with five or six perimeters for the clamp parts, and inspect the guide sleeves and captive-nut pockets after printing.

Fusion reported no unhealthy timeline features or positive-volume interference between the modeled components and hardware envelopes. Each printed component is one solid. Every STL was checked for closed mesh edges, positive signed volume and expected millimetre dimensions. These checks do not establish physical fit, lens clearance, loaded stability, printed fastener strength or temperatures in operation. No printed or thermal test has been performed.

## Doorframe mount and fit test

Ray confirmed: **52 mm overhang (door beyond), 55 mm tall lip, 12 mm inset, then a 12 × 11 mm step.** The model interprets the profile in this order, walking from the top room-facing edge toward the door:

1. Top ledge: 52 mm deep.
2. Front face: down 55 mm.
3. First underside return: inward 12 mm.
4. Next face: down another 12 mm.
5. Next underside return: inward another 11 mm.

The CAD frame uses top surface Z=0, front face Y=0 and door boundary Y=52. The lower continuation to Z=-90 is illustrative only. The side preview and `doorframe_measurements.json` record this interpretation. **Print `10-doorframe-fit-gauge-print-first.stl` first** and check that all steps match the real frame without forcing it. The gauge has 0.6 mm profile clearance; it is not a load-bearing part. Usable frame width must accommodate the 190 mm platform, and the case needs approximately 85 mm clearance above the top ledge, plus assembly access.

The 190 × 92 × 6 mm platform rests on four rubber patches. Two adjustable jaws grip the first 12 mm underside return beneath the 55 mm lip. Each jaw slides on a separate guide and is pulled upward by a long M4 screw. Rubber cushions the frame; the upper platform and lower jaws provide opposing mechanical capture. The smaller second step is represented in the reference frame and fit gauge but is not the clamping surface.

The case projects toward the room. Its back edge is at Y=48; the platform back edge is at Y=50, leaving 2 mm nominal clearance to the indicated door boundary. This only checks the supplied profile, not the actual door's swing, hinges, seals, flex or hardware. The pad model assumes 3 mm foam compresses to 2.5 mm at the recesses; actual compression and grip depend on the material and hand-tightening.

Assembly order:

1. Confirm the fit gauge and print the camera pod for a lens fit check.
2. Fit the four platform pads and two jaw pads; keep the contact surfaces clean.
3. Fit each guide beneath the platform with two M3×10 screws. Slide each jaw onto its guide, with the padded toe pointing toward the door.
4. Place an M4 nut in each jaw's underside hex recess. Insert the M4×80 screws with washers through the platform and thread them into those nuts. The modeled bolts extend about 9 mm below the jaws at nominal fit, entirely on the room side.
5. Slide two M4 nuts into the platform's right-edge channels. Attach the empty battery tray using M4×10 screws from inside the tray. The bosses support the case floor so tightening does not depend on compressing its feet. Check the screw tips remain above the platform's underside; longer screws could contact the frame.
6. Finish the battery, Pi and camera assembly. Place the mount on the ledge with both jaws below the first return. Tighten the clamp screws evenly by hand until the pads hold securely. Do not crush or distort the trim or printed parts.
7. Test with the full battery weight at a low height before overhead use. Check the real door opens and closes freely. Recheck retention after the pads settle; use a separate retaining tether where the installed assembly could fall onto someone.

The fitted assembly remains a prototype. Native checks include the frame, pads and smooth M4 fastener envelopes, but do not simulate threads, printed strength, trim strength, pad creep or loaded retention. The guide screws and internal electronics screws are specified in the hardware list, not included as full CAD hardware.

## Sources

- [Duckietown DD24/DD24-B component description](https://docs.duckietown.com/daffy/opmanual-dd24/preliminaries/dd24-components-description.html#rpi-camera-g-with-fisheye-lens-and-cable)
- [Waveshare RPi Camera (G)](https://www.waveshare.com/product/rpi-camera-g.htm)
- [Waveshare original mechanical DWG archive](https://www.waveshare.com/w/upload/8/8a/RPi_Camera_E_F_G_H_Mechanical.zip)
- [Raspberry Pi4 mechanical drawing](https://datasheets.raspberrypi.com/rpi4/raspberry-pi-4-mechanical-drawing.pdf)
- [INIU P51L-E2 dimensions](https://iniushop.com/products/iniu-p51l-e2-power-bank-45w-20000mah)

## Rebuilding

`build_enclosure.py` creates a new Fusion document. `add_camera_bracket.py` assembles the camera and adds its bracket. `add_doorframe_mount.py` adds the measured platform, guides, jaws and fit gauge. `add_mount_fastener_references.py` adds simplified M4 hardware envelopes. `validate_and_export.py` validates and exports the active prototype; `prepare_meshes.py` then orients and validates freshly exported STLs. Run the geometry scripts through `fusion_client.py script SCRIPT.py` while Fusion's MCP adapter is running. The MCP session ID in the helper is temporary and may need reinitialising after a server restart.

The native timeline is editable and has several named parameters, but not every sketch coordinate is driven by them. Treat major size changes as a redesign and recheck all clearances.
