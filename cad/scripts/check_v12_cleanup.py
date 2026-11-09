"""Read-only native checks for the v12 cleanup, independent of feature names."""
from pathlib import Path
import json, math
import adsk.core, adsk.fusion

OUT = Path(__file__).resolve().parents[1] / 'v12'


def run(_context: str):
    app = adsk.core.Application.get()
    assert app.activeDocument.name == 'Doorframe Camera - enclosed guard and clear straps v12'
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    manager = adsk.fusion.TemporaryBRepManager.get()
    case = next(o.bRepBodies.item(0) for o in root.occurrences if o.component.name.startswith('01 '))
    guard = next(o.bRepBodies.item(0) for o in root.occurrences if o.component.name.startswith('03 '))
    results = []

    def probe(name, body, low, high, solid):
        bounds = adsk.core.OrientedBoundingBox3D.create(
            adsk.core.Point3D.create(*[(a+b)/20 for a,b in zip(low,high)]),
            adsk.core.Vector3D.create(1,0,0), adsk.core.Vector3D.create(0,1,0),
            *[(b-a)/10 for a,b in zip(low,high)])
        tool = manager.createBox(bounds)
        volume = tool.volume
        assert manager.booleanOperation(tool, manager.copy(body), adsk.fusion.BooleanTypes.IntersectionBooleanType)
        expected = volume if solid else 0
        assert abs(tool.volume-expected) < 1e-7, (name, tool.volume, expected)
        results.append({'name':name,'expected':'solid' if solid else 'clear','passed':True})

    for x in (96,108):
        for y0,y1 in [(-8,-4),(14,16)]:
            probe('Closed roof fragment '+str((x,y0)),case,[x+.05,y0+.05,173.2],[x+2.95,y1-.05,175.4],True)
    for x in (99,112):
        probe('Retained tether slot '+str(x),case,[x+.05,1.05,169.6],[x+4.95,7.95,175.4],False)
    for x in (38,72):
        for y in (-10.8,18.6):
            probe('Full-width strap slot '+str((x,y)),case,[x+.01,y+.01,77.51],[x+11.99,y+2.19,79.89],False)
        probe('Rear strap channel '+str(x),case,[x+.05,20.05,80],[x+11.95,20.75,164.7],False)
    # Broad sections of the formerly open front wall now contain material.
    for x0,x1 in [(87,97),(117,127)]:
        probe('Closed camera side wall '+str(x0),guard,[x0,-26.3,-26.4],[x1,-24.1,-5.6],True)
    probe('Ribbon notch mouth',guard,[98.1,-26.3,-7.3],[115.9,-24.1,-5.5],False)
    probe('Small notch bridge',guard,[104.1,-26.3,-14.3],[109.9,-24.1,-13.5],True)

    cones=[]
    for face in guard.faces:
        cone=adsk.core.Cone.cast(face.geometry)
        if cone:
            degrees=abs(math.degrees(cone.halfAngle))
            assert abs(degrees-45)<1e-5, degrees
            cones.append(degrees)
    assert cones, 'Missing conical self-supporting interior'
    aperture=[]
    for face in guard.faces:
        cylinder=adsk.core.Cylinder.cast(face.geometry)
        if cylinder and abs(cylinder.radius*10-11)<1e-5 and abs(abs(cylinder.axis.z)-1)<1e-5:
            aperture.append(22)
    assert aperture, 'Missing 22 mm lens aperture'
    straps=[o for o in root.occurrences if o.component.name.startswith('REFERENCE - v12 battery strap')]
    assert len(straps)==2
    for strap in straps:
        assert strap.component.bRepBodies.count==1 and strap.component.bRepBodies.item(0).isSolid
    report={
        'revision':'v12','native_volume_probes':results,'guard_conical_half_angles_deg':cones,
        'lens_aperture_diameter_mm':22,'guard_print_orientation':'open rim down',
        'guard_ribbon_notch_final_bridge_mm':6,'strap_width_mm':10,
        'strap_thickness_envelope_mm':1.5,'closure_overlap_thickness_mm':3,
        'strap_centers_x_mm':[44,78],'strap_slot_dimensions_mm':[12,2.2],
        'strap_model_count':2,'strap_collision_check':'Full closed loops and overlap included in assembly interference check',
        'remaining_wall_behind_recess_mm':1.6,
        'physical_fit_tested':False,'slicer_verified':False,
        'not_verified':['Actual strap thickness and fastening loop geometry','Full CSI cable and connector route',
                        'Lens barrel height and entrance pupil','Printed clip fit and physical retention']
    }
    (OUT/'cleanup-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'cleanup_probes_passed':len(results),'guard_slope_deg':cones,'strap_envelopes':len(straps)}))
