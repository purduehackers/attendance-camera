"""Inspect v12 native geometry, motion and access, then export release artifacts."""
from pathlib import Path
import json, math, sys
import adsk.core, adsk.fusion
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'v12'
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_enclosure import component,box,appearance,color,mmpt,V
from build_upright_v5 import side_shape
from check_v12_cables import run as check_cables

FILES={
    '01':'01-electronics-case.stl','02':'02-front-and-ribbon-cover.stl',
    '03':'03-camera-guard-with-bumpers.stl','04':'04-downward-camera-carrier.stl',
    '05':'05-adjustable-clamp-print-two.stl','06':'06-pressure-shoe-print-two.stl',
    '07':'07-hand-knob-print-two.stl',
}
ORIENT={
    '01':((1,0,0),(0,0,-1),(0,1,0)),
    '02':((1,0,0),(0,0,1),(0,-1,0)),
    '03':((1,0,0),(0,-1,0),(0,0,-1)),
    '04':((0,0,1),(1,0,0),(0,1,0)),
    '05':((0,0,1),(1,0,0),(0,1,0)),
    '06':((1,0,0),(0,-1,0),(0,0,-1)),
    '07':((1,0,0),(0,-1,0),(0,0,-1)),
}

def collisions(d,occurrences):
    oc=adsk.core.ObjectCollection.create()
    for o in occurrences:oc.add(o)
    ip=d.createInterferenceInput(oc);ip.areCoincidentFacesIncluded=False
    return [{'one':h.entityOne.parentComponent.name,'two':h.entityTwo.parentComponent.name,
             'volume_cm3':h.interferenceBody.volume} for h in d.analyzeInterference(ip)
            if h.interferenceBody.volume>1e-7]

def view(a,file,eye,target=(107,0,75),size=(1600,1200)):
    cam=a.activeViewport.camera;cam.cameraType=adsk.core.CameraTypes.OrthographicCameraType
    cam.eye=mmpt(*eye);cam.target=mmpt(*target);cam.upVector=V(0,0,1)
    cam.isSmoothTransition=False;cam.isFitView=True;a.activeViewport.camera=cam
    a.activeViewport.saveAsImageFile(str(OUT/file),*size)

def print_matrix(o,x,y):
    axes=ORIENT[o.component.name[:2]];m=adsk.core.Matrix3D.create()
    m.setWithCoordinateSystem(mmpt(0,0,0),*[V(*axis) for axis in axes])
    b=o.component.bRepBodies.item(0).preciseBoundingBox
    points=[]
    for xx in (b.minPoint.x,b.maxPoint.x):
        for yy in (b.minPoint.y,b.maxPoint.y):
            for zz in (b.minPoint.z,b.maxPoint.z):
                p=adsk.core.Point3D.create(xx,yy,zz);p.transformBy(m);points.append(p.asArray())
    mins=[min(v[i] for v in points) for i in range(3)]
    m.translation=V(x/10-mins[0],y/10-mins[1],-mins[2])
    return m

def run(_context: str):
    a=adsk.core.Application.get();d=adsk.fusion.Design.cast(a.activeProduct);r=d.rootComponent
    assert a.activeDocument.name=='Doorframe Camera - enclosed guard and clear straps v12'
    (OUT/'stl').mkdir(exist_ok=True)
    # No coupons, gauges, or test prints are present in this revision.
    prints=[o for o in r.occurrences if 'PRINT' in o.component.name]
    assert len(prints)==10
    unique={o.component.name[:2]:o for o in prints};assert len(unique)==7
    for o in prints:
        assert o.component.bRepBodies.count==1 and o.component.bRepBodies.item(0).isSolid,o.name
    health=[{'feature':t.name,'message':t.errorOrWarningMessage} for t in d.timeline
            if t.healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]
    assert not health,health

    # Ribbon envelope excludes connector/stiffener and is explicitly illustrative.
    route=[(-17.5,-13),(-17.5,-9),(-14.5,-7),(-13,-7),(-10.8,-3.5),(-10.8,81.5)]
    assert sum(o.component.name.startswith('REFERENCE - v11 ribbon') for o in r.occurrences)==1

    tests=[('Pi USB Ethernet',144.5,-3.5,202.5,16.5,171.6,27),
           ('Pi USB-C HDMI audio',203.1,-4.5,235,17.5,86.5,59),
           ('Battery charging',-25,-11,7.9,20,84,76)]
    probes=[]
    for name,x0,y0,x1,y1,z,h in tests:
        o,c=component(r,'TEST access '+name);box(c,name,x0,y0,x1,y1,z,h);probes.append(o)
    hits=collisions(d,list(r.occurrences))
    print(json.dumps({'closed_interference':hits}));assert not hits,hits
    for o in probes:assert o.deleteMe()
    check_cables(_context)
    from check_v12_cleanup import run as check_cleanup
    check_cleanup(_context)

    camera=next(o for o in r.occurrences if o.component.name.startswith('REFERENCE - Waveshare'))
    axis=[camera.transform2.getCell(i,2) for i in range(3)];assert axis==[0,0,-1],axis
    # Read actual native pilot surfaces, not merely names or parameter metadata.
    pilots={}
    for key,part,rad,dim,span in [('Pi','01',1.05,1,4.8),('camera','04',.85,2,3.8)]:
        faces=[]
        for f in unique[part].component.bRepBodies.item(0).faces:
            cylinder=adsk.core.Cylinder.cast(f.geometry)
            if not cylinder or abs(cylinder.radius*10-rad)>1e-5 or abs(abs(cylinder.axis.asArray()[dim])-1)>1e-6:continue
            b=f.boundingBox;length=(b.maxPoint.asArray()[dim]-b.minPoint.asArray()[dim])*10
            assert abs(length-span)<1e-4,(key,length)
            faces.append({'diameter_mm':rad*2,'straight_length_mm':length})
        assert len(faces)==4,(key,faces);pilots[key]=faces

    # Check retracted shoes/bolts as well as the clamped position. Exclude static
    # rubber references from this pose test; restore the assembled positions.
    moving=[o for o in r.occurrences if o.component.name.startswith(('06 ','07 ','REFERENCE - M5 x 30'))]
    saved=[(o,o.transform2.copy()) for o in moving]
    for o,_ in saved:
        m=o.transform2;t=m.translation;t.z-=.35 if o.component.name.startswith('06 ') else .4;m.translation=t;o.transform2=m
    if d.snapshots.hasPendingSnapshot:d.snapshots.add()
    opened=collisions(d,[o for o in r.occurrences if not o.component.name.startswith('REFERENCE - v11 rubber')])
    for o,m in saved:o.transform2=m
    if d.snapshots.hasPendingSnapshot:d.snapshots.add()
    assert not opened,opened
    # Nominal downward cone, using the approximate lens nose as cone origin.
    radial=math.hypot(17.8,15.15);cone_radius=3*math.tan(math.radians(80))
    assert radial>cone_radius

    parts=[]
    for key,o in sorted(unique.items()):
        parts.append({'id':key,'name':o.component.name,'file':FILES[key],
                      'quantity':sum(p.component==o.component for p in prints),
                      'volume_cm3':o.component.bRepBodies.item(0).volume})
    report={'revision':'v12','health_warnings':health,'interference':hits,'open_pose_interference':opened,
            'installed_print_count':10,'unique_print_count':7,'parts':parts,'camera_direction':axis,
            'pilot_cylinder_checks':pilots,'bench_screws':6,'clamp_screws':2,'electronics_screws':8,
            'heat_set_inserts':0,'nuts':8,'access_corridors_checked':[t[0] for t in tests],
            'ribbon_route_yz_mm':route,'ribbon_envelope_mm':[16,.35],'ribbon_dimensions_assumed':True,
            'clamp_contacts':{'upper_pad_y_mm':[13,22],'lower_shoe_y_mm':[9.5,25.5],'screw_y_mm':17.5},
            'retracted_shoe_travel_mm':3.5,'free_pad_opening_note':'3 mm free lower pad leaves about 3 mm under the nominal frame before upper-pad relaxation.',
            'fastener_stack_mm':{'case_floor':2.4,'bracket_top':8,'M3_washer':.5,'M3_screw_length':10,
                                 'M3_head_z':[80.4,82.05],'M3_tip_z':70.4,'frame_upper_z':67,
                                 'M3_tip_frame_clearance':3.4,'M3_tip_recess_above_jaw_bottom':.9,
                                 'M3_nut_z':[71.1,73.5],'M3_thread_projection_past_nut':.7},
            'optical_reference':{'lens_tip_z_mm':-32.7,'bumper_tip_z_mm':-35.7,'nominal_front_clearance_mm':3,
                                 'cone_full_angle_deg':160,'bumper_min_radius_mm':radial,'cone_radius_at_bumper_mm':cone_radius,
                                 'actual_entrance_pupil_and_view_unverified':True},
            'cable_clearance_report':'cable-clearance.json','cleanup_report':'cleanup-validation.json',
            'not_tested':['physical clamp retention and creep','actual trim strength and attachment to wall','screw and snap fit','actual lens extent and field of view','physical cable fit, exact INIU port centers and full CSI route','slicer support volume and print time'],
            'coupon_files':[]}
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    ex=d.exportManager
    assert ex.execute(ex.createSTEPExportOptions(str(OUT/'doorframe-camera-clamped-v12.step')))
    for key,o in sorted(unique.items()):
        opt=ex.createSTLExportOptions(o.component,str(OUT/'stl'/FILES[key]));opt.isBinaryFormat=True
        opt.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        opt.unitType=adsk.fusion.DistanceUnits.MillimeterDistanceUnits;assert ex.execute(opt)

    view(a,'assembly.png',(400,-280,240))
    view(a,'side-profile.png',(480,0,75),size=(1100,1500))
    original=[(o,o.transform2.copy(),o.isLightBulbOn) for o in r.occurrences]
    for o in r.occurrences:
        if o.component.name.startswith(('02 ','03 ','REFERENCE - upward')):o.isLightBulbOn=False
    view(a,'inside.png',(380,-310,220))
    for o,m,on in original:o.isLightBulbOn=on
    # Two layout previews: all parts are placed on Z=0 in their export rotation.
    placements={
        'plate-1.png':{'01':[(0,0)],'02':[(0,110)]},
        'plate-2.png':{'05':[(0,0),(55,0)],'04':[(110,0)],'03':[(165,0)],
                       '07':[(165,60),(200,60)],'06':[(165,100),(195,100)]},
    }
    for file,places in placements.items():
        indices={}
        for o in r.occurrences:
            key=o.component.name[:2];o.isLightBulbOn=False
            if 'PRINT' not in o.component.name or key not in places:continue
            i=indices.get(key,0);indices[key]=i+1
            x,y=places[key][i];o.transform2=print_matrix(o,x,y);o.isLightBulbOn=True
        if d.snapshots.hasPendingSnapshot:d.snapshots.add()
        view(a,file,(350,-250,400),target=(110,130 if file=='plate-1.png' else 60,0),size=(1600,1200))
    for o,m,on in original:o.transform2=m;o.isLightBulbOn=on
    if d.snapshots.hasPendingSnapshot:d.snapshots.add()
    view(a,'assembly.png',(400,-280,240))
    assert ex.execute(ex.createFusionArchiveExportOptions(str(OUT/'doorframe-camera-clamped-v12.f3d')))
    print(json.dumps({'native_checks':'passed','installed_parts':10,'unique_STLs':7,'output':str(OUT)}))
