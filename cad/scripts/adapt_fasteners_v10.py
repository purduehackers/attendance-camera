"""Create a v10 copy of v9 for infrequently removed, directly threaded PCB screws."""
from pathlib import Path
import json
import math
import shutil
import sys

import adsk.core
import adsk.fusion

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'v10'
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_enclosure import box, circles, color, component, extrude, mmpt, rect, sketch, CUT, JOIN, VI
from build_upright_v5 import ycircles


def label(comp, text, x, y):
    # Font-independent 5 mm lettering with >=0.5 mm strokes. The small gaps
    # between segments avoid point-contact/nonmanifold raised geometry.
    s = sketch(comp, 'Coupon label ' + text, offset=2)
    segments = {
        'a': (.65, 4.5, 2.35, 5), 'b': (2.5, 2.9, 3, 4.35),
        'c': (2.5, .65, 3, 2.1), 'd': (.65, 0, 2.35, .5),
        'e': (0, .65, .5, 2.1), 'f': (0, 2.9, .5, 4.35),
        'g': (.65, 2.25, 2.35, 2.75),
    }
    glyphs = {'0':'abcdef', '1':'bc', '2':'abdeg', '3':'abcdg', '4':'bcfg',
              '5':'acdfg', '6':'acdefg', '7':'abc', '8':'abcdefg', '9':'abcdfg'}
    cursor = x
    for char in text:
        if char == '.':
            s.sketchCurves.sketchCircles.addByCenterRadius(mmpt(cursor + .3, y + .3), .03)
            cursor += 1.4
        elif char == 'M':
            rect(s, cursor, y, cursor + .5, y + 5)
            rect(s, cursor + 3.5, y, cursor + 4, y + 5)
            for poly in [[(.65,5),(1.9,3.2),(1.55,2.7),(.65,4.0)],
                         [(3.35,5),(2.1,3.2),(2.45,2.7),(3.35,4.0)]]:
                points=[mmpt(cursor + u, y + v) for u,v in poly]
                for a,b in zip(points,points[1:]+points[:1]):
                    s.sketchCurves.sketchLines.addByTwoPoints(a,b)
            cursor += 5
        else:
            for segment in glyphs[char]:
                x0,y0,x1,y1 = segments[segment]
                rect(s, cursor+x0, y+y0, cursor+x1, y+y1)
            cursor += 4
    extrude(comp, s, .4, JOIN, 'Raised coupon label ' + text)


def resize_pilots(design, comp, old_name, name, parameter, diameter, depth):
    s = comp.sketches.itemByName(old_name + ' layout')
    f = comp.features.extrudeFeatures.itemByName(old_name)
    assert s and f and s.sketchCurves.sketchCircles.count == 4
    design.userParameters.add(parameter, VI(f'{diameter} mm'), 'mm',
                              'Provisional PETG pilot. Fit-test with actual screws before the full print.')
    for circle in s.sketchCurves.sketchCircles:
        circle.radius = diameter / 20
        point = circle.centerSketchPoint.geometry
        dim = s.sketchDimensions.addDiameterDimension(circle,
            adsk.core.Point3D.create(point.x + .5, point.y + .5, 0))
        assert dim
        dim.parameter.expression = parameter
    s.name = name + ' layout'
    f.name = name
    return {'parameter': parameter, 'diameter_mm': diameter, 'depth_mm': depth,
            'centers_mm': [[v.centerSketchPoint.worldGeometry.x * 10,
                            v.centerSketchPoint.worldGeometry.y * 10,
                            v.centerSketchPoint.worldGeometry.z * 10]
                           for v in s.sketchCurves.sketchCircles]}


def build_coupon(d, r):
    old_coupon = next(o for o in r.occurrences if o.component.name.startswith('08 '))
    assert old_coupon.deleteMe()
    oq, q = component(r, '08 Screw-fit test coupon - TEST PRINT')
    box(q, 'Screw-fit coupon base', 245, 0, 297, 44, 0, 2)
    choices = []
    # Each clearance neck simulates the board thickness plus the 0.2 mm entry relief,
    # so the actual M2x4 / M2.5x6 screws exercise the same engagement and tip clearance.
    for thread, y, top, pcb, od, depth, clearance, pilots in [
        ('M2', 9, 9, 1.2, 6.4, 4, 2.2, [1.6, 1.7, 1.8]),
        ('M2.5', 31, 10, 1.6, 8, 5, 2.8, [2.0, 2.1, 2.2]),
    ]:
        label(q, thread, 246, max(.2, y - 10.5))
        for x, diameter in zip([253, 271, 289], pilots):
            name = f'{thread} pilot {diameter:.1f}'
            circles(q, name + ' boss', [(x, y)], od, 2, top - 2, JOIN)
            circles(q, name + ' bore', [(x, y)], diameter, top, -(pcb + depth), CUT)
            circles(q, name + ' board clearance', [(x, y)], clearance, top, -(pcb + .2), CUT)
            label(q, f'{diameter:.1f}', x - 5, y + 5)
            choices.append({'thread': thread, 'pilot_mm': diameter, 'center_mm': [x, y, top],
                            'simulated_pcb_mm': pcb, 'entry_relief_mm': .2,
                            'clearance_diameter_mm': clearance, 'pilot_depth_below_pcb_mm': depth})
    color(q, d.appearances.itemByName('PETG - warm light grey'))
    oq.isLightBulbOn = False
    assert d.computeAll()
    assert q.bRepBodies.count == 1 and q.bRepBodies.item(0).isSolid
    return choices


def run(_context: str):
    OUT.mkdir(exist_ok=True)
    a = adsk.core.Application.get()
    doc = a.importManager.importToNewDocument(a.importManager.createFusionArchiveImportOptions(
        str(ROOT / 'v9' / 'doorframe-camera-simple-v9.f3d')))
    assert doc
    doc.activate()
    doc.name = 'Doorframe Camera - PETG direct screw mounts v10'
    d = adsk.fusion.Design.cast(a.activeProduct)
    r = d.rootComponent
    c = next(o.component for o in r.occurrences if o.component.name.startswith('01 '))
    before = c.bRepBodies.item(0).volume
    original_volumes = {o.component.name: o.component.bRepBodies.item(0).volume
                        for o in r.occurrences if o.component.name.startswith(('02 ', '03 '))}
    pi = resize_pilots(d, c, 'Pi M2.5 insert pockets - 4 mm x 5 mm',
        'Pi M2.5 direct screw pilots', 'pi_screw_pilot', 2.1, 5)
    camera = resize_pilots(d, c, 'Camera M2 insert pockets - 3.2 mm x 4 mm',
        'Camera M2 direct screw pilots', 'camera_screw_pilot', 1.7, 4)
    for old in ['insert_M2_hole', 'insert_M25_hole']:
        p = d.userParameters.itemByName(old)
        assert p and p.deleteMe()
    c.features.extrudeFeatures.itemByName('Pi heat-set bosses - 8 mm OD').name = 'Pi screw bosses - 8 mm OD'
    c.features.extrudeFeatures.itemByName('Camera M2 insert bosses - 6.4 mm OD').name = 'Camera screw bosses - 6.4 mm OD'
    c.sketches.itemByName('Pi heat-set bosses - 8 mm OD layout').name = 'Pi screw bosses - 8 mm OD layout'
    c.sketches.itemByName('Camera M2 insert bosses - 6.4 mm OD layout').name = 'Camera screw bosses - 6.4 mm OD layout'
    ycircles(c, 'Pi screw entry relief - 0.2 mm deep',
             [(x, z) for x, _, z in pi['centers_mm']], 2.8, 15.6, .2, CUT)
    circles(c, 'Camera screw entry relief - 0.2 mm deep',
            [(x, y) for x, y, _ in camera['centers_mm']], 2.2, -13.5, .2, CUT)
    assert d.computeAll()
    expected = 4 * math.pi * ((2**2 - 1.05**2) * 5 + (1.6**2 - .85**2) * 4
                              - ((1.4**2 - 1.05**2) + (1.1**2 - .85**2)) * .2) / 1000
    measured = c.bRepBodies.item(0).volume - before
    assert abs(measured - expected) < 1e-5, (measured, expected)
    for o in r.occurrences:
        if o.component.name in original_volumes:
            assert abs(o.component.bRepBodies.item(0).volume - original_volumes[o.component.name]) < 1e-8

    choices = build_coupon(d, r)
    for name in ['camera_verified_dimensions.json', 'doorframe_measurements.json', 'logo.json']:
        shutil.copyfile(ROOT / 'v9' / name, OUT / name)
    settings = json.loads((ROOT / 'v9' / 'print-settings.json').read_text())
    settings['revision'] = 'v10'
    (OUT / 'print-settings.json').write_text(json.dumps(settings, indent=2) + '\n')
    spec = json.loads((ROOT / 'v9' / 'hardware.json').read_text())
    spec['revision'] = 'v10 direct PETG screw mounts; no heat-set inserts or nuts'
    spec['inserts'] = []
    spec['nuts'] = []
    for key in list(spec):
        if key.startswith('source_insert_'):
            del spec[key]
    spec['direct_screw_mounts'] = [
        {'purpose': 'Pi', 'thread': 'M2.5', 'pilot_mm': 2.1, 'depth_mm': 5, 'boss_od_mm': 8,
         'pcb_mm': 1.6, 'screw_projection_mm': 4.4, 'entry_relief_mm': .2,
         'nominal_thread_engagement_mm': 4.2, 'tip_clearance_mm': .6},
        {'purpose': 'camera', 'thread': 'M2', 'pilot_mm': 1.7, 'depth_mm': 4, 'boss_od_mm': 6.4,
         'pcb_mm': 1.2, 'screw_projection_mm': 2.8, 'entry_relief_mm': .2,
         'nominal_thread_engagement_mm': 2.6, 'tip_clearance_mm': 1.2},
    ]
    spec['screw_fit_coupon'] = choices
    spec['fastening_note'] = 'Use steel socket-cap machine screws gently to form the threads before fitting electronics; these are not modeled helical threads. Pilot diameters are provisional and require a PETG coupon check. Direct plastic threads are for infrequent assembly; use a captive-nut revision for repeated board servicing. Do not put M3 screws through the PCBs.'
    spec['source_plastic_threads'] = 'https://ftc-docs.firstinspires.org/en/latest/manufacturing/3d_printing/designing_and_slicing/working_with_screws/working_with_screws.html'
    spec['printing_note'] = 'PETG, 6 walls, 30% global infill, solid hook modifiers. Print the screw-fit coupon and frame gauge before the large body; do not put supports in pilot holes. See PRINT-ADMIN-NOTES.md.'
    (OUT / 'hardware.json').write_text(json.dumps(spec, indent=2) + '\n')
    (OUT / 'fastener-change.json').write_text(json.dumps({
        'base_revision': 'v9', 'pi': pi, 'camera': camera,
        'expected_added_volume_cm3': expected, 'measured_added_volume_cm3': measured,
        'unchanged_cover_and_guard_volumes_cm3': original_volumes,
        'physical_screw_fit_tested': False,
    }, indent=2) + '\n')
    print(json.dumps({'document': doc.name, 'added_volume_cm3': measured,
                      'installed_screws': 8, 'heat_set_inserts': 0, 'nuts': 0,
                      'coupon_choices': choices}))
