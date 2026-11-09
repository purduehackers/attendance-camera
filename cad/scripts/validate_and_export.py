from pathlib import Path
import adsk.core, adsk.fusion, json, os, math

OUT=str(Path(__file__).resolve().parents[1]) + ''

def run(_context: str):
    app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);r=d.rootComponent
    assert 'mounted v3' in app.activeDocument.name
    health=[]
    for i in range(d.timeline.count):
        f=d.timeline.item(i)
        if f.healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState:health.append({'feature':f.name,'message':f.errorOrWarningMessage})
    parts=[];entities=adsk.core.ObjectCollection.create()
    for o in r.occurrences:
        entities.add(o)
        if ' - PRINT' in o.component.name:
            assert o.component.bRepBodies.count==1,o.component.name+' is not one continuous part'
            b=o.component.bRepBodies.item(0);assert b.isSolid
            parts.append({'name':o.component.name,'volume_cm3':b.volume})
    assert not health,json.dumps(health)
    check=d.createInterferenceInput(entities);check.areCoincidentFacesIncluded=False
    conflicts=d.analyzeInterference(check)
    interference=[]
    for i in range(conflicts.count):
        hit=conflicts.item(i)
        interference.append({'one':hit.entityOne.name,'two':hit.entityTwo.name,'volume_cm3':hit.interferenceBody.volume})
    report={'health_warnings':health,'parts':parts,'interference':interference,'total_printed_volume_cm3':sum(p['volume_cm3'] for p in parts),'case_body_mm':[142,88,71.4],'platform_mm':[190,92,6],'rubber_pad_projection_mm':2.2,'camera_hole_pitch_mm':[21,13.5],'camera_angle_degrees':45,'doorframe_mount':'Two sliding padded screw jaws grip the first 12 mm return below the 55 mm lip','doorframe_dimensions_mm':[52,55,12,12,11],'minimum_modeled_door_boundary_clearance_mm':2,'physical_fit_tested':False,'fastener_loads_and_door_swing_validated':False}
    with open(OUT+'/validation.json','w') as f:json.dump(report,f,indent=2)
    print(json.dumps(report))
    if interference:raise RuntimeError('Resolve geometric interference before export')
    ex=d.exportManager
    assert ex.execute(ex.createSTEPExportOptions(OUT+'/doorframe-camera-assembly-with-reference-hardware.step'))
    os.makedirs(OUT+'/prototype-stl',exist_ok=True)
    for o in r.occurrences:
        if ' - PRINT' not in o.component.name:continue
        stem=o.component.name.split(' - PRINT')[0].lower().replace(' ','-')
        opts=ex.createSTLExportOptions(o.component,OUT+'/prototype-stl/'+stem+'.stl')
        opts.isBinaryFormat=True
        opts.meshRefinement=adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        opts.unitType=adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        was_visible=o.isLightBulbOn
        o.isLightBulbOn=True
        assert ex.execute(opts)
        o.isLightBulbOn=was_visible
        assert os.path.getsize(OUT+'/prototype-stl/'+stem+'.stl')>84
    cam=app.activeViewport.camera
    cam.cameraType=adsk.core.CameraTypes.OrthographicCameraType
    cam.eye=adsk.core.Point3D.create(32,-36,20)
    cam.target=adsk.core.Point3D.create(7.1,0,0)
    cam.upVector=adsk.core.Vector3D.create(0,0,1)
    cam.isFitView=True;cam.isSmoothTransition=False
    app.activeViewport.camera=cam
    assert app.activeViewport.saveAsImageFile(OUT+'/assembled-preview.png',1600,1000)
    cam=app.activeViewport.camera
    cam.eye=adsk.core.Point3D.create(45,0,-1)
    cam.target=adsk.core.Point3D.create(7.1,0,-1)
    cam.upVector=adsk.core.Vector3D.create(0,0,1)
    cam.isFitView=True;cam.isSmoothTransition=False
    app.activeViewport.camera=cam
    assert app.activeViewport.saveAsImageFile(OUT+'/doorframe-side-preview.png',1400,1100)
    cam.eye=adsk.core.Point3D.create(32,-36,20)
    cam.target=adsk.core.Point3D.create(7.1,0,0)
    cam.isFitView=True;app.activeViewport.camera=cam
    assert ex.execute(ex.createFusionArchiveExportOptions(OUT+'/doorframe-camera-prototype.f3d'))
    assert ex.execute(ex.createFusionArchiveExportOptions(OUT+'/doorframe-camera-mounted-v3.f3d'))
    print('Saved native F3D, STEP assembly, individual prototype STLs, and assembled preview.')
