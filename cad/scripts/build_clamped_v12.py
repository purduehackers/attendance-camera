"""Clean up v11 in a NEW document; preserve its native archive.

All geometry dimensions are millimetres. The guard prints open rim down.
"""
from pathlib import Path
import json, math, shutil, sys
import adsk.core, adsk.fusion

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'v12'
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_enclosure import component, box, circles, sketch, color, appearance, col, mmpt, V, JOIN, CUT, NEW
from build_upright_v5 import side_shape
from build_simple_v7 import xy_poly, xz_poly


def combine(c, name, target, tool, operation):
    inp = c.features.combineFeatures.createInput(target, col([tool]))
    inp.operation = operation
    inp.isKeepToolBodies = False
    result = c.features.combineFeatures.add(inp)
    result.name = name
    return result


def band_profiles(points, half_thickness):
    """Closed polygon miter offsets, for a conservative strap envelope."""
    normals = []
    for p, q in zip(points, points[1:] + points[:1]):
        dy, dz = q[0]-p[0], q[1]-p[1]
        length = math.hypot(dy, dz)
        normals.append((-dz/length, dy/length))
    aa, bb = [], []
    for i, p in enumerate(points):
        normal = [normals[i-1][j]+normals[i][j] for j in (0, 1)]
        length = math.hypot(*normal)
        normal = [n/length for n in normal]
        scale = half_thickness/sum(normal[j]*normals[i][j] for j in (0, 1))
        aa.append(tuple(p[j]+normal[j]*scale for j in (0, 1)))
        bb.append(tuple(p[j]-normal[j]*scale for j in (0, 1)))
    def area(poly):
        return abs(sum(p[0]*q[1]-p[1]*q[0] for p, q in zip(poly, poly[1:]+poly[:1])))
    return sorted([aa, bb], key=area, reverse=True)


def run(_context: str):
    OUT.mkdir(exist_ok=True)
    app = adsk.core.Application.get()
    doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(
        str(ROOT/'v11/doorframe-camera-clamped-v11.f3d')))
    assert doc
    doc.activate()
    doc.name = 'Doorframe Camera - enclosed guard and clear straps v12'
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    case = next(o.component for o in root.occurrences if o.component.name.startswith('01 '))
    carrier = next(o.component for o in root.occurrences if o.component.name.startswith('04 '))
    old_guard = next(o for o in root.occurrences if o.component.name.startswith('03 '))
    assert old_guard.deleteMe()

    # Fill only vestigial roof vents around the reinforcement, not the tether.
    for x in (96, 108):
        box(case, 'Close obsolete roof vent fragments '+str(x), x, -8, x+3, 16, 164.5, 2.5, JOIN)

    # The old X80..92 strap pair overlapped the camera carrier at X86..128.
    for y0, y1 in [(-10.8, -8.6), (18.6, 20.8)]:
        box(case, 'Close obstructed strap slot '+str(y0), 80, y0, 92, y1, 69, 2.4, JOIN)
    box(case, 'Restore rear wall at old strap slot', 80, 20, 92, 20.8, 71.4, .1, JOIN)
    for y0, y1 in [(-10.8, -8.6), (18.6, 20.8)]:
        box(case, 'Relocated full-width battery strap slot '+str(y0), 72, y0, 84, y1, 68.9, 2.6, CUT)
    # Shallow inner-wall recesses make room for the rear runs of the straps.
    for x in (38, 72):
        box(case, 'Rear battery strap recess '+str(x), x, 20, x+12, 20.8, 71.3, 85, CUT)

    battery = next(o for o in root.occurrences if o.component.name.startswith('REFERENCE - INIU'))
    matrix = battery.transform2
    translation = matrix.translation
    translation.y -= .05  # 0.5 mm, preserving the ribbon and front-cover clearances.
    matrix.translation = translation
    battery.transform2 = matrix
    if design.snapshots.hasPendingSnapshot:
        design.snapshots.add()

    # Clip off the carrier corners to fit the 45-degree interior of the guard.
    for x, sx in [(86, 1), (128, -1)]:
        for y, sy in [(-23.65, 1), (18.35, -1)]:
            xy_poly(carrier, 'Guard clearance corner '+str((x, y)),
                    [(x, y), (x+sx*8, y), (x, y+sy*8)], -10.1, 4.2, CUT)

    _, guard = component(root, '03 Enclosed camera guard with corner bumpers - PRINT 1')
    outer = box(guard, 'Continuous protective camera walls', 83.2, -26.45, 130.8, 21.15,
                -29, 23.6, r=2).bodies.item(0)
    cavity = box(guard, 'Rectangular cavity tool', 85.6, -24.05, 128.4, 18.75,
                 -26.6, 21.3).bodies.item(0)
    sections = []
    for z, radius in [(-26.6, 11), (-5.3, 32.3)]:
        s = sketch(guard, '45 degree cavity section '+str(z), offset=z)
        s.sketchCurves.sketchCircles.addByCenterRadius(mmpt(107, 0), radius/10)
        sections.append(s)
    loft_in = guard.features.loftFeatures.createInput(NEW)
    for s in sections:
        loft_in.loftSections.add(s.profiles.item(0))
    loft = guard.features.loftFeatures.add(loft_in)
    loft.name = '45 degree self-supporting interior tool'
    cone = loft.bodies.item(0)
    combine(guard, 'Limit cone to rectangular interior', cavity, cone,
            adsk.fusion.FeatureOperations.IntersectFeatureOperation)
    combine(guard, 'Sloped interior around camera and lens', outer, cavity, CUT)
    circles(guard, 'Round lens aperture - no printed lens cap', [(107, 0)], 22, -29.1, 2.6, CUT)
    for x in (83.2, 124.8):
        for y in (-26.45, 15.15):
            box(guard, 'Flat-surface lens bumper '+str((x, y)), x, y, x+6, y+6, -35.7, 6.7, JOIN)
    # Open-rim service notch: 45-degree shoulders leave a 6 mm final bridge.
    xz_poly(guard, 'Small chamfered ribbon service notch',
            [(98, -5.3), (116, -5.3), (116, -7.4), (110, -13.4), (104, -13.4), (98, -7.4)],
            -26.6, 2.8, CUT)
    for x0, x1 in [(83.1, 87.4), (126.6, 130.9)]:
        box(guard, 'Guard clip movement clearance '+str(x0), x0, -3.6, x1, 3.6, -25, 19.7, CUT)
    tongue = [(84, -25), (85.6, -25), (85.6, -8.5), (86.7, -8.5),
              (86.7, -7), (85.6, -5.4), (84, -5.4)]
    xz_poly(guard, 'Left 1.6 mm snap tongue', tongue, -3, 6, JOIN)
    xz_poly(guard, 'Right 1.6 mm snap tongue', [(214-x, z) for x, z in tongue], -3, 6, JOIN)
    color(guard, design.appearances.itemByName('PETG - graphite'))

    route = [(-9.7, 76.5), (-9.7, 81), (-11.2, 83), (-11.2, 158.5),
             (19.9, 158.5), (19.9, 76.5)]
    exterior, interior = band_profiles(route, .75)
    strap_color = appearance(design, 'Reference straps teal', 36, 137, 143)
    for x in (44, 78):
        _, strap = component(root, 'REFERENCE - v12 battery strap 10 x 1.5 mm at X'+str(x))
        side_shape(strap, 'Strap outside envelope', x-5, exterior, 10)
        side_shape(strap, 'Strap inside opening', x-5.1, interior, 10.2, CUT)
        box(strap, 'Front closure overlap envelope', x-5, -13.45, x+5, -11.95, 110, 30, JOIN)
        color(strap, strap_color)

    camera = next(o.component for o in root.occurrences if o.component.name.startswith('REFERENCE - Waveshare'))
    for b in camera.bRepBodies:
        if b.name == 'Body2':
            b.name = 'Approximate existing lens barrel - REFERENCE ONLY'
    for o in root.occurrences:
        for s in o.component.sketches:
            s.isLightBulbOn = False
        for plane in o.component.constructionPlanes:
            plane.isLightBulbOn = False
    assert design.computeAll()
    for o in root.occurrences:
        if 'PRINT' in o.component.name:
            assert o.component.bRepBodies.count == 1 and o.component.bRepBodies.item(0).isSolid, o.name
    for file in ('camera_verified_dimensions.json', 'logo.json', 'hardware.json', 'print-settings.json'):
        shutil.copy2(ROOT/'v11'/file, OUT/file)
    hardware = json.loads((OUT/'hardware.json').read_text())
    hardware.update(revision='v12', battery_strap_max_thickness_mm=1.5,
                    battery_strap_max_closure_thickness_mm=3)
    (OUT/'hardware.json').write_text(json.dumps(hardware, indent=2)+'\n')
    layout = json.loads((ROOT/'v11/layout.json').read_text())
    layout.update(revision='v12', battery_shift_y_mm=-.5, strap_centers_x_mm=[44, 78],
                  strap_width_mm=10, strap_thickness_envelope_mm=1.5, strap_closure_thickness_envelope_mm=3,
                  strap_route_yz_mm=route, strap_rear_recess_depth_mm=.8,
                  guard_print_face='Open rim down', guard_interior_slope_deg=45,
                  guard_service_notch_final_bridge_mm=6, carrier_corner_chamfer_mm=8)
    (OUT/'layout.json').write_text(json.dumps(layout, indent=2)+'\n')
    print(json.dumps({'document': doc.name, 'printed_components': 7, 'strap_envelopes': 2,
                      'guard_volume_cm3': guard.bRepBodies.item(0).volume}))
