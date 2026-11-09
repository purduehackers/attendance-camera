from pathlib import Path
import adsk.core, adsk.fusion, json, os, sys
ROOT=str(Path(__file__).resolve().parents[1]) + ''
OUT=ROOT+'/v6'
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_enclosure import component,box

def run(_context: str):
    a=adsk.core.Application.get();d=adsk.fusion.Design.cast(a.activeProduct);r=d.rootComponent
    assert 'inserts v6' in a.activeDocument.name
    os.makedirs(OUT+'/stl',exist_ok=True)
    # These are deliberately generous access corridors, not vendor plug models.
    tests=[('Pi USB and Ethernet top',144.5,-3.5,202.5,16.5,163.1,27),
           ('Pi power HDMI audio side',203.1,-4.5,235,17.5,79.5,57),
           ('Battery charging end',-25,-11,7.9,20,75.5,76)]
    probes=[]
    for name,x0,y0,x1,y1,z,h in tests:
        o,c=component(r,'TEST ONLY '+name);box(c,name,x0,y0,x1,y1,z,h);probes.append(o)
    bad=[];parts=[];entities=adsk.core.ObjectCollection.create();masses=[]
    for t in d.timeline:
        if t.healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState:bad.append({'feature':t.name,'message':t.errorOrWarningMessage})
    for o in r.occurrences:
        entities.add(o);n=o.component.name
        if 'PRINT' in n:
            assert o.component.bRepBodies.count==1,n+' must be one solid'
            b=o.component.bRepBodies.item(0);assert b.isSolid
            parts.append({'name':n,'volume_cm3':b.volume,'installed':n.startswith(('01 ','02 ','03 '))})
        mass=None
        if n.startswith(('01 ','02 ','03 ')):mass=sum(b.volume for b in o.component.bRepBodies)*1.27
        if n.startswith('REFERENCE - INIU'):mass=326.1
        if n.startswith('REFERENCE - Raspberry'):mass=50
        if n.startswith('REFERENCE - Waveshare'):mass=15
        if mass:
            bodies=list(o.component.bRepBodies);v=sum(b.volume for b in bodies);xyz=[0,0,0]
            for b in bodies:
                p=b.physicalProperties.centerOfMass;p.transformBy(o.transform2)
                for j,k in enumerate([p.x,p.y,p.z]):xyz[j]+=k*10*b.volume/v
            masses.append({'name':n,'assumed_mass_g':mass,'center_mm':xyz})
    inp=d.createInterferenceInput(entities);inp.areCoincidentFacesIncluded=False
    hits=d.analyzeInterference(inp)
    collisions=[{'one':h.entityOne.name,'two':h.entityTwo.name,'volume_cm3':h.interferenceBody.volume} for h in hits]
    # Camera direction is read from the actual hardware occurrence transform.
    cam_o=next(o for o in r.occurrences if o.component.name.startswith('REFERENCE - Waveshare'))
    axis=[cam_o.transform2.getCell(i,2) for i in range(3)]
    assert all(abs(x-y)<1e-8 for x,y in zip(axis,[0,0,-1]))
    total=sum(x['assumed_mass_g'] for x in masses)
    cog=[sum(x['assumed_mass_g']*x['center_mm'][j] for x in masses)/total for j in range(3)]
    assert len([p for p in parts if p['installed']])==3
    report={'revision':'v6','health_warnings':bad,'interference':collisions,'parts':parts,
        'installed_print_count':3,'electronics_screws':8,'heat_set_inserts':8,'nuts':0,
        'camera_direction':axis,'nominal_mass_g':total,'nominal_center_of_mass_mm':cog,
        'mass_assumptions':'Solid PETG 1.27 g/cm3; battery 326.1 g; Pi 50 g; camera 15 g. Cables, inserts, screws, pads and straps excluded. Hardware COM approximated by reference volume.',
        'top_support_y_mm':[.5,22],
        'access_corridors_checked':[{'name':x[0],'x_mm':[x[1],x[3]],'y_mm':[x[2],x[4]],'z_mm':[x[5],x[5]+x[6]]} for x in tests],
        'hardware_stack_checks':{'Pi':{'pcb_mm':1.6,'screw_length_mm':6,'screw_projection_mm':4.4,'insert_length_mm':4,'pocket_depth_mm':5,'tip_clearance_mm':.6},
            'camera':{'pcb_mm':1.2,'screw_length_mm':4,'screw_projection_mm':2.8,'insert_length_mm':3,'pocket_depth_mm':4,'tip_clearance_mm':1.2}},
        'not_tested':['physical snap action','printed strength and creep','loaded mount retention','thermal operation','actual cable housings and bend radii'],
        'insert_note':'Knurl-to-plastic interference is intentional during heat setting; insert/fastener solids are not included in the collision model. Dimensions and source parts are in hardware.json.'}
    with open(OUT+'/validation.json','w') as h:json.dump(report,h,indent=2)
    print(json.dumps(report))
    # Remove diagnostic solids before native export.
    for o in probes:assert o.deleteMe()
    assert not bad,json.dumps(bad)
    assert not collisions,'Resolve interference before export'
    ex=d.exportManager
    assert ex.execute(ex.createSTEPExportOptions(OUT+'/doorframe-camera-simple-v6.step'))
    for o in r.occurrences:
        if 'PRINT' not in o.component.name:continue
        name=o.component.name
        stem=name.split(' - ')[0].lower().replace(' ','-')
        path=OUT+'/stl/'+stem+'.stl';opts=ex.createSTLExportOptions(o.component,path)
        opts.isBinaryFormat=True;opts.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        opts.unitType=adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        on=o.isLightBulbOn;o.isLightBulbOn=True;assert ex.execute(opts);o.isLightBulbOn=on
        assert os.path.getsize(path)>84
    cam=a.activeViewport.camera;cam.cameraType=adsk.core.CameraTypes.OrthographicCameraType
    cam.eye=adsk.core.Point3D.create(43,-25,23);cam.target=adsk.core.Point3D.create(10.7,0,8)
    cam.upVector=adsk.core.Vector3D.create(0,0,1);cam.isFitView=True;cam.isSmoothTransition=False
    a.activeViewport.camera=cam;a.activeViewport.saveAsImageFile(OUT+'/assembly.png',1600,1100)
    cam=a.activeViewport.camera;cam.eye=adsk.core.Point3D.create(45,-1,8);cam.target=adsk.core.Point3D.create(10.7,-1,8)
    cam.isFitView=True;a.activeViewport.camera=cam;a.activeViewport.saveAsImageFile(OUT+'/side-profile.png',1200,1400)
    frame=next(o for o in r.occurrences if o.component.name.startswith('REFERENCE - upward'))
    cover=next(o for o in r.occurrences if o.component.name.startswith('02 '))
    guard=next(o for o in r.occurrences if o.component.name.startswith('03 '))
    frame.isLightBulbOn=False;cover.isLightBulbOn=False;guard.isLightBulbOn=False
    cam.eye=adsk.core.Point3D.create(20,-35,24);cam.target=adsk.core.Point3D.create(10.7,0,8)
    cam.isFitView=True;a.activeViewport.camera=cam;a.activeViewport.saveAsImageFile(OUT+'/inside.png',1600,1100)
    # Show exactly the three installed printed parts separated for assembly review.
    for o in r.occurrences:
        if o.component.name.startswith('REFERENCE'):o.isLightBulbOn=False
    cover.isLightBulbOn=True;guard.isLightBulbOn=True
    m_cover=cover.transform2.copy();m_guard=guard.transform2.copy()
    m=m_cover.copy();t=m.translation;t.y-=5;m.translation=t;cover.transform2=m
    m=m_guard.copy();t=m.translation;t.z-=3;m.translation=t;guard.transform2=m
    cam.eye=adsk.core.Point3D.create(43,-40,23);cam.target=adsk.core.Point3D.create(10.7,-2,6)
    cam.isFitView=True;a.activeViewport.camera=cam;a.activeViewport.saveAsImageFile(OUT+'/three-parts.png',1600,1200)
    cover.transform2=m_cover;guard.transform2=m_guard
    for o in r.occurrences:
        if o.component.name.startswith('REFERENCE'):o.isLightBulbOn=True
    if d.snapshots.hasPendingSnapshot:d.snapshots.add()
    cam.eye=adsk.core.Point3D.create(43,-25,23);cam.target=adsk.core.Point3D.create(10.7,0,8)
    cam.isFitView=True;a.activeViewport.camera=cam
    assert ex.execute(ex.createFusionArchiveExportOptions(OUT+'/doorframe-camera-simple-v6.f3d'))
    print('Saved native v6, STEP, five print/test STLs, and assembly views.')
