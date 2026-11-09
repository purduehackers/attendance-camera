from pathlib import Path
import adsk.core, adsk.fusion, math, json, sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_enclosure import component, sketch, extrude, circles, cuts, transverse_holes, color, mmpt, V, col, VI, NEW, CUT

def run(_context: str):
    app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);r=d.rootComponent
    assert 'prototype v2' in app.activeDocument.name
    assert not any(o.component.name.startswith('06 ') for o in r.occurrences)
    q=math.sqrt(.5)
    m=adsk.core.Matrix3D.create()
    m.setWithCoordinateSystem(mmpt(52,-.5,37),V(1,0,0),V(0,-q,q),V(0,-q,-q))
    for o in r.occurrences:
        if o.component.name.startswith(('04 ','05 ','REFERENCE - Waveshare')):o.transform2=m
    if d.snapshots.hasPendingSnapshot:d.snapshots.add()
    ow,w=component(r,'06 Camera 45 degree bracket - PRINT - provisional aim',m)
    s=sketch(w,'45 degree bracket section','x',-2)
    corners=[(-2,0,-math.sqrt(.5)),(-2,26,-26-math.sqrt(.5)),(-2,26,0),(-2,0,0)]
    ps=[s.modelToSketchSpace(mmpt(*p)) for p in corners]
    for i in range(4):s.sketchCurves.sketchLines.addByTwoPoints(ps[i],ps[(i+1)%4])
    extrude(w,s,42,NEW,'45 degree cradle')
    circles(w,'Carrier M3 pilot holes',[(3.5,11),(34.5,11),(3.5,22),(34.5,22)],2.5,0,-7,CUT)
    # Open channel from the camera cable exit to the case slot.
    cuts(w,'Ribbon routing channel',[(10,-1,28,14)],-32,33)
    circles(w,'Camera M2 nut and screw-tip relief',[(8.5,14.5),(29.5,14.5)],5.2,0,-2,CUT)
    circles(w,'Cap fastener head relief',[(3.5,3.5),(34.5,3.5)],5.5,0,-3.2,CUT)
    inv=m.copy();inv.invert()
    def local(x,y,z):
        p=mmpt(x,y,z);p.transformBy(inv);return p
    ref=w.sketches.add(w.xYConstructionPlane);ref.name='Case mating plane references'
    ps=[ref.sketchPoints.add(local(*p)) for p in [(0,0,0),(100,0,0),(0,0,100)]]
    pi=w.constructionPlanes.createInput();pi.setByThreePoints(*ps)
    pl=w.constructionPlanes.add(pi);pl.name='Case front mating plane';pl.isLightBulbOn=False
    hs=w.sketches.add(pl);hs.name='Case attachment - M3x6'
    for x,z in [(59,49),(83,49),(59,61),(83,61)]:
        hs.sketchCurves.sketchCircles.addByCenterRadius(hs.modelToSketchSpace(local(x,0,z)),.125)
    extrude(w,hs,4.5,CUT,'Case-side M3 pilots')
    ref.isLightBulbOn=False
    color(w,d.appearances.itemByName('PETG - graphite'))
    upper=next(o.component for o in r.occurrences if o.component.name.startswith('02 '))
    cuts(upper,'Camera ribbon entry',[(62,-.5,80,3)],40,3)
    for cp in w.constructionPlanes:cp.isLightBulbOn=False
    for sk in w.sketches:sk.isLightBulbOn=False
    c=app.activeViewport.camera;c.viewOrientation=adsk.core.ViewOrientations.IsoTopRightViewOrientation
    c.isFitView=True;c.isSmoothTransition=False;app.activeViewport.camera=c
    print(json.dumps({'camera_aim':'45 degrees below horizontal - provisional','doorframe_retention':'awaiting ledge measurements','components':r.occurrences.count}))
