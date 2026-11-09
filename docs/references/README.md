# Sources and reference measurements

## Hardware and artwork

- [Duckietown DD24 components](https://docs.duckietown.com/daffy/opmanual-dd24/preliminaries/dd24-components-description.html#rpi-camera-g-with-fisheye-lens-and-cable): identifies the Waveshare RPi Camera G with fisheye lens and ribbon.
- [Waveshare Camera G](https://www.waveshare.com/product/rpi-camera-g.htm) and [mechanical drawings](https://www.waveshare.com/w/upload/8/8a/RPi_Camera_E_F_G_H_Mechanical.zip): camera board dimensions. The extracted dimensions are preserved in `cad/v9/camera_verified_dimensions.json`.
- [Raspberry Pi 4 mechanical drawing](https://datasheets.raspberrypi.com/rpi4/raspberry-pi-4-mechanical-drawing.pdf).
- [INIU P51L-E2](https://iniushop.com/products/iniu-p51l-e2-power-bank-45w-20000mah): target battery dimensions; actual pack/port fit remains to be checked.
- CNC Kitchen [insert dimension drawing](https://cnckitchen.store/cdn/shop/files/Table_Metic.png), [M2 × 3](https://cnckitchen.store/products/heat-set-insert-m2-x-3-100-pieces) and [M2.5 × 4](https://cnckitchen.store/products/gewindeeinsatz-threaded-insert-m2-5-standard-100-stk-pcs): specified heat-set geometry. A copy of the dimension drawing is retained with the v9 reference files.
- [Purdue Hackers flat logo](https://www.purduehackers.com/ph.svg): official source artwork, retained as SVG and adapted into the shallow case recess. The logo remains Purdue Hackers artwork.

Doorframe dimensions were supplied for this installation: 52 mm overhang, 55 mm face, 12 mm inset, another 12 mm rise and 11 mm upper ledge. They are site-specific measurements, not a standard frame specification.

## Door-opener comparison

The [Purdue Hackers door-opener repository](https://github.com/purduehackers/door-opener/tree/982af340240c5b371c602d1239cb205c2c0db9e6) was checked as a related project. Its [v2 hardware](https://github.com/purduehackers/door-opener/blob/982af340240c5b371c602d1239cb205c2c0db9e6/docs/hardware/v2/README.md) and [assembly instructions](https://github.com/purduehackers/door-opener/blob/982af340240c5b371c602d1239cb205c2c0db9e6/docs/hardware/v2/assembly.md) describe different electronics: Pi 5, Camera Module 3 Wide, touchscreen and NFC.

[Measurements extracted from the v2 STEP files](door-opener-cad-measurements.json) found camera pockets Ø3.2 × 2.5 mm deep and M3 pockets Ø4.5 × 3 mm deep. These are useful comparisons, but do not validate this case's M2.5 inserts or frame profile. The camera hole pitch in that exported model differs from the Waveshare board; it was not copied into this design. The assembly documentation also notes potential printed-hole alignment issues.

## Software and print guidance

- [MediaMTX v1.21.3 release](https://github.com/bluenviron/mediamtx/releases/tag/v1.21.3) and [upstream source/license](https://github.com/bluenviron/mediamtx/tree/v1.21.3): streaming server. The installer fetches its binary and retains the upstream license; it is not authored by this project.
- [Prusa perimeter/infill guidance](https://help.prusa3d.com/article/infill_42), [PETG guidance](https://help.prusa3d.com/article/petg_2059) and [Formlabs material/orientation guidance](https://formlabs.com/blog/strongest-3d-printing-materials/): supporting context for prototype print preparation, not a load certification.

No project-wide license has been selected yet. Third-party artwork, reference drawings and upstream software retain their respective ownership and terms.
