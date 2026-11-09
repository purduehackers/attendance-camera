from pathlib import Path
import adsk.core, adsk.fusion, json, os
OUT=str(Path(__file__).resolve().parents[1]) + '/v5'

def run(_context: str):
    a=adsk.core.Application.get();d=adsk.fusion.Design.cast(a.activeProduct);r=d.rootComponent
    assert 'downward camera v5' in a.activeDocument.name
    os.makedirs(OUT+'/stl',exist_ok=True)
    bad=[]
    for t in d.timeline:
        if t.healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState:bad.append({'name':t.name,'message':t.errorOrWarningMessage})
    ent=adsk.core.ObjectCollection.create();parts=[];mass_items=[]
    for o in r.occurrences:
        ent.add(o);name=o.component.name
        if ' - PRINT' in name:
            assert o.component.bRepBodies.count==1,name
            body=o.component.bRepBodies.item(0);assert body.isSolid
            parts.append({'name':name,'volume_cm3':body.volume})
        # This is a nominal estimate, not an actual measured mass or load test.
        mass=None
        if ' - PRINT' in name and not name.startswith('07 '):mass=sum(b.volume for b in o.component.bRepBodies)*1.27
        if name.startswith('REFERENCE - INIU'):mass=326.1
        if name.startswith('REFERENCE - Raspberry'):mass=50
        if name.startswith('REFERENCE - Waveshare'):mass=15
        if mass:
            bodies=list(o.component.bRepBodies);total=sum(b.volume for b in bodies)
            xyz=[0,0,0]
            for b in bodies:
                p=b.physicalProperties.centerOfMass;p.transformBy(o.transform2)
                for j,v in enumerate([p.x,p.y,p.z]):xyz[j]+=v*10*b.volume/total
            mass_items.append({'name':name,'nominal_mass_g':mass,'center_mm':xyz})
    assert not bad,json.dumps(bad)
    inp=d.createInterferenceInput(ent);inp.areCoincidentFacesIncluded=False
    hits=d.analyzeInterference(inp);collisions=[]
    for hit in hits:collisions.append({'one':hit.entityOne.name,'two':hit.entityTwo.name,'volume_cm3':hit.interferenceBody.volume})
    mass_total=sum(x['nominal_mass_g'] for x in mass_items)
    cog=[sum(x['nominal_mass_g']*x['center_mm'][j] for x in mass_items)/mass_total for j in range(3)]
    report={'revision':'v5','health_warnings':bad,'interference':collisions,'parts':parts,
        'camera_direction':[0,0,-1],'top_contact_y_range_mm':[.5,22],
        'nominal_center_of_mass_mm':cog,'nominal_mass_g':mass_total,'mass_items':mass_items,
        'estimate_assumptions':'Printed geometry treated as solid PETG at assumed 1.27 g/cm3; battery 326.1 g; Pi 50 g; camera 15 g. Reference hardware centers use uniform geometric density. Screws, pads, cable and straps excluded. Slicing and actual hardware change results.',
        'physical_fit_load_retention_door_swing_tested':False}
    with open(OUT+'/validation.json','w') as h:json.dump(report,h,indent=2)
    print(json.dumps(report))
    assert not collisions,'Resolve interference before export'
    ex=d.exportManager
    assert ex.execute(ex.createSTEPExportOptions(OUT+'/doorframe-camera-v5-with-reference-hardware.step'))
    for o in r.occurrences:
        if ' - PRINT' not in o.component.name:continue
        stem=o.component.name.split(' - PRINT')[0].lower().replace(' ','-')
        path=OUT+'/stl/'+stem+'.stl';opts=ex.createSTLExportOptions(o.component,path)
        opts.isBinaryFormat=True;opts.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        opts.unitType=adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        visible=o.isLightBulbOn;o.isLightBulbOn=True
        assert ex.execute(opts);o.isLightBulbOn=visible
        assert os.path.getsize(path)>84
    cam=a.activeViewport.camera;cam.cameraType=adsk.core.CameraTypes.OrthographicCameraType
    cam.eye=adsk.core.Point3D.create(43,-25,23);cam.target=adsk.core.Point3D.create(10.7,0,8)
    cam.upVector=adsk.core.Vector3D.create(0,0,1);cam.isFitView=True;cam.isSmoothTransition=False
    a.activeViewport.camera=cam;a.activeViewport.saveAsImageFile(OUT+'/assembly.png',1600,1100)
    cam=a.activeViewport.camera;cam.eye=adsk.core.Point3D.create(45,-1,8);cam.target=adsk.core.Point3D.create(10.7,-1,8)
    cam.upVector=adsk.core.Vector3D.create(0,0,1);cam.isFitView=True;cam.isSmoothTransition=False
    a.activeViewport.camera=cam;a.activeViewport.saveAsImageFile(OUT+'/side-profile.png',1200,1400)
    frame=next(o for o in r.occurrences if o.component.name.startswith('REFERENCE - upward'))
    panel=next(o for o in r.occurrences if o.component.name.startswith('02 '))
    frame.isLightBulbOn=False;panel.isLightBulbOn=False
    cam.eye=adsk.core.Point3D.create(20,-35,24);cam.target=adsk.core.Point3D.create(10.7,0,8)
    cam.isFitView=True;a.activeViewport.camera=cam
    a.activeViewport.saveAsImageFile(OUT+'/inside.png',1600,1100)
    frame.isLightBulbOn=True;panel.isLightBulbOn=True
    cam.eye=adsk.core.Point3D.create(43,-25,23);cam.target=adsk.core.Point3D.create(10.7,0,8)
    cam.isFitView=True;a.activeViewport.camera=cam
    assert ex.execute(ex.createFusionArchiveExportOptions(OUT+'/doorframe-camera-hanging-v5.f3d'))
    print('Exported v5 CAD, STLs, previews and validation.')
