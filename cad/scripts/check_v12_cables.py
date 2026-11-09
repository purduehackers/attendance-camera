"""Check v12 plug/bend envelopes without modifying the active Fusion document.

These are specified clearance envelopes, not vendor connector CAD. The INIU
port centers and USB-C housing length require checking against the actual parts.
"""
from pathlib import Path
import hashlib
import json
import math

import adsk.core
import adsk.fusion

OUT = Path(__file__).resolve().parents[1] / 'v12'


def run(_context: str):
    app = adsk.core.Application.get()
    assert app.activeDocument.name == 'Doorframe Camera - enclosed guard and clear straps v12'
    design = adsk.fusion.Design.cast(app.activeProduct)
    manager = adsk.fusion.TemporaryBRepManager.get()
    bodies = [(o.component.name, b) for o in design.rootComponent.occurrences
              for b in o.bRepBodies]
    assert sum('PRINT' in o.component.name for o in design.rootComponent.occurrences) == 10

    def box(low, high):
        bounds = adsk.core.OrientedBoundingBox3D.create(
            adsk.core.Point3D.create(*[(a+b)/20 for a, b in zip(low, high)]),
            adsk.core.Vector3D.create(1, 0, 0),
            adsk.core.Vector3D.create(0, 1, 0),
            *[(b-a)/10 for a, b in zip(low, high)])
        return manager.createBox(bounds)

    def overlap(a, b):
        aa, bb = a.boundingBox, b.boundingBox
        return all(aa.minPoint.asArray()[i] < bb.maxPoint.asArray()[i]
                   and bb.minPoint.asArray()[i] < aa.maxPoint.asArray()[i]
                   for i in range(3))

    probes = [
        ('Pi USB-C housing', [203.1, 7.4, 86.7], [238.1, 17.4, 102.7]),
        ('Battery USB-A housing', [-27.1, -.1, 113], [7.9, 9.9, 129]),
        ('Battery charging housing', [-27.1, -.1, 136], [7.9, 9.9, 152]),
        ('Charging lead straight exit', [-80, 2.9, 142], [-27.1, 6.9, 146]),
        # Access for a hand approaching the housings from outside the case.
        ('Battery plug grip access', [-42, -10, 100], [-1, 19, 158]),
        ('Pi power plug grip access', [215, -3, 80], [250, 21, 109]),
    ]
    # Two semicircular turns and a gentle elevation change across the front.
    # Keep the power cable away from the wall, clamp jaws and camera view.
    route = []
    for i in range(37):
        theta = math.pi*i/36
        route.append([-27.1-20*math.sin(theta), 4.9-20*(1-math.cos(theta)), 121])
    for i in range(1, 81):
        u = i/80
        route.append([-27.1+265.2*u, -35.1, 121-26.3*(3*u*u-2*u*u*u)])
    for i in range(1, 37):
        theta = math.pi*i/36
        route.append([238.1+23.75*math.sin(theta), -35.1+23.75*(1-math.cos(theta)), 94.7])
    # Each segment has an axis-aligned bounding box enlarged by 2 mm. This is
    # conservative for a 3.5 mm round cable, including sampled-arc sagitta.
    for index, (a, b) in enumerate(zip(route, route[1:])):
        probes.append((f'Power cable segment {index}',
                       [min(x, y)-2 for x, y in zip(a, b)],
                       [max(x, y)+2 for x, y in zip(a, b)]))
    hits = []
    for name, low, high in probes:
        probe = box(low, high)
        for component, body in bodies:
            if not overlap(probe, body):
                continue
            intersection = manager.copy(probe)
            assert manager.booleanOperation(intersection, manager.copy(body),
                                            adsk.fusion.BooleanTypes.IntersectionBooleanType)
            if intersection.volume > 1e-7:
                hits.append({'probe': name, 'component': component,
                             'body': body.name, 'volume_mm3': intersection.volume*1000})
    assert not hits, hits
    length = sum(math.dist(a, b) for a, b in zip(route, route[1:]))+70
    assert length < 480, length
    report = {
        'revision': 'v12',
        'check': 'Native solids against conservative plug, grip and external cable envelopes',
        'interference': hits,
        'power_housing_envelope_mm': {'axial_length': 35, 'width': 16, 'thickness': 10},
        'battery_ports_assumed_x_y_z_mm': {'output': [8, 4.9, 121], 'charge': [8, 4.9, 144]},
        'pi_usb_c_reference_face_center_mm': [203, 12.4, 94.7],
        'pi_window_lower_z_mm': 85.5,
        'pi_housing_lower_z_mm': 86.7,
        'pi_lower_housing_clearance_mm': 1.2,
        'pi_window_residual_lower_rail_mm': 5.6,
        'power_cable_nominal_diameter_mm': 3.5,
        'power_cable_test_envelope_diameter_mm': 4,
        'side_turn_centerline_radii_mm': [20, 23.75],
        'power_route_including_housings_mm': round(length, 2),
        'route_centerline_mm': route,
        'route_is_external': True,
        'source': 'https://www.startech.com/en-us/cables/usb2ac50cm',
        'model_builder_sha256': hashlib.sha256((OUT.parent/'scripts/build_clamped_v12.py').read_bytes()).hexdigest(),
        'physical_fit_tested': False,
        'not_verified': [
            'Actual INIU port centers and integral cable exit',
            'Actual connector insertion depth, overmold length and cable bend limit',
            'Full CSI ribbon route to the Pi, including connector stiffeners and bends',
            'Battery charging passthrough or uninterrupted Pi power during charging',
        ],
    }
    (OUT/'cable-clearance.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ('interference', 'pi_lower_housing_clearance_mm',
                                            'power_route_including_housings_mm', 'route_is_external')}))
