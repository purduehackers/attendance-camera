from pathlib import Path
"""Upward-stepped frame and passive rubber-lined slide-on saddle.

Imports preserved v2 into a separate document. There are no adjustment screws
at the frame: four bracket screws and two case screws are fitted on the bench.
"""
import adsk.core, adsk.fusion, math, sys, json
OUT=str(Path(__file__).resolve().parents[1]) + ''
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_enclosure import component, sketch, box, circles, cuts, extrude, color, appearance, mmpt, VI, NEW, JOIN, CUT

def side_shape(c,name,x,pts,width,op=NEW):
    s=sketch(c,name+' outline','x',x)
    vs=[s.modelToSketchSpace(mmpt(x,y,z)) for y,z in pts]
    for a,b in zip(vs,vs[1:]+vs[:1]):s.sketchCurves.sketchLines.addByTwoPoints(a,b)
    return extrude(c,s,width,op,name)

def run(_context: str):
    app=adsk.core.Application.get()
    opts=app.importManager.createFusionArchiveImportOptions(OUT+'/revisions/doorframe-camera-v2.f3d')
    doc=app.importManager.importToNewDocument(opts);assert doc
    doc.activate();doc.name='Doorframe Camera - upward steps - slide-on saddle v4'
    d=adsk.fusion.Design.cast(app.activeProduct);r=d.rootComponent
    assert r.occurrences.count==10
    for name,value,note in [
        ('frame_overhang',52,'Bottom overhang ends at indicated door boundary'),
        ('frame_lip_height',55,'Front face rises 55 mm from overhang underside'),
        ('frame_inset',12,'First upward-facing ledge, y=0..12 at z=55'),
        ('frame_step_height',12,'Next step rises to z=67'),
        ('frame_step_width',11,'Upper ledge, y=12..23 at z=67'),
        ('mount_pad_stock',3,'Soft rubber or neoprene pad stock'),
        ('mount_pad_compressed',2.5,'Nominal modeled thickness; fit-test actual foam'),
    ]:d.userParameters.add(name,VI(f'{value} mm'),'mm',note)
    for o in list(r.occurrences):
        if o.isGrounded:o.isGrounded=False
        if o.isGroundToParent:o.isGroundToParent=False
        m=o.transform2;t=m.translation;t.y-=8;t.z+=6.52;m.translation=t;o.transform2=m
    if d.snapshots.hasPendingSnapshot:d.snapshots.add()
    dark=d.appearances.itemByName('PETG - graphite');light=d.appearances.itemByName('PETG - warm light grey')
    rubber=d.appearances.itemByName('Reference rubber pads')
    frame_mat=appearance(d,'Reference upward-stepped doorframe',158,133,103)

    op,p=component(r,'07 Slide-on mounting platform - PRINT')
    box(p,'Six mm mounting platform',-24,-82,166,10,57,6,r=3)
    cuts(p,'Platform lightening windows',[(8,-57,59,-13),(69,-57,119,-13)],56.9,6.2)
    circles(p,'Case support bosses',[(132,-54),(132,-18)],10,63,2.2,JOIN)
    circles(p,'Bench-assembly M4 case holes',[(132,-54),(132,-18)],4.5,56.9,8.4,CUT)
    cuts(p,'Side-load M4 nut channels',[(127.8,y-3.6,167,y+3.6) for y in [-54,-18]],58,3.4)
    for i,(x0,y0,x1,y1) in enumerate([
        (10,8.6,30,10),(112,8.6,132,10),(10,-81.6,30,-80.4),(112,-81.6,132,-80.4),
        (-1.6,-70,-.4,-60),(-1.6,-12,-.4,-2),(142.4,-70,143.6,-60),(142.4,-12,143.6,-2)
    ]):box(p,'Case locating tab '+str(i+1),x0,y0,x1,y1,63,6,JOIN)
    circles(p,'Bench-assembly M3 saddle holes',[(cx+dx,-8.5) for cx in [-10,152] for dx in [-5,5]],3.4,56.9,6.2,CUT)
    # Top contact on first narrow ledge. End 2 mm before the upward riser.
    cuts(p,'Upper ledge pad pockets',[(cx-10,1,cx+10,10) for cx in [-10,152]],56.9,.6)
    color(p,dark)

    for side,cx in [('left',-10),('right',152)]:
        ob,b=component(r,'08 '+side+' fixed saddle - PRINT')
        # Main C-shaped side profile, printed lying on its side for continuous
        # perimeters around the load path. 5 mm arm thickness permits some flex.
        side_shape(b,'Fixed C saddle',cx-10,
            [(-11,-7),(45,-7),(45,-2),(-1,-2),(-6,7),(-6,54),(-11,54)],20)
        box(b,'Platform attachment flange',cx-13,-14,cx+13,-3,54,3,JOIN)
        circles(b,'M3 pilot holes',[(cx-5,-8.5),(cx+5,-8.5)],2.5,57.1,-7.1,CUT)
        cuts(b,'Underside pad pocket',[(cx-8,30,cx+8,44)],-2.5,.6)
        # A small lead-in ramp prevents the pad's entering edge from being square.
        side_shape(b,'Lower arm entry chamfer',cx-10.1,[(43,-2),(45,-2),(45,-4)],20.2,CUT)
        color(b,light)

    pads,rp=component(r,'REFERENCE - four saddle rubber pads - compressed')
    for side,cx in [('left',-10),('right',152)]:
        box(rp,side+' upper pad - 20 x 9 x 3 stock',cx-10,1,cx+10,10,55,2.5)
        box(rp,side+' lower pad - 16 x 14 x 3 stock',cx-8,30,cx+8,44,-2.5,2.5)
    color(rp,rubber)

    of,f=component(r,'REFERENCE - corrected upward-stepped frame')
    side_shape(f,'52 bottom overhang - 55 rise - 12 ledge - 12 rise - 11 ledge',-30,
        [(0,0),(52,0),(52,90),(23,90),(23,67),(12,67),(12,55),(0,55)],202)
    color(f,frame_mat)

    og,g=component(r,'09 Upward-step fit gauge PRINT FIRST - PRINT')
    # Covers first two exposed ledges with 0.6 mm clearance. The lower arm of
    # the actual saddle is a separate contact and the frame underside is z=0.
    side_shape(g,'Upward profile gauge',225,
        [(-.6,0),(-.6,55.6),(11.4,55.6),(11.4,67.6),(23,67.6),
         (23,70),(9,70),(9,58),(-3,58),(-3,0)],8)
    color(g,light);og.isLightBulbOn=False
    d.computeAll()
    data={'revision':'v4 upward steps, passive slide-on saddle',
        'source':'User corrected the steps to go up and requested friction fit or hanging, with no screws to tighten at height.',
        'overhang_mm':52,'lip_height_mm':55,'first_ledge_depth_mm':12,
        'second_step_height_mm':12,'upper_ledge_depth_mm':11,
        'orientation':'Underside z=0; room is negative Y; front face y=0 rises to z=55. First ledge y=0..12 at z=55, next riser y=12 rises to z=67, upper ledge y=12..23 at z=67. Door boundary y=52. Back continuation above z=67 is illustrative.',
        'contacts':'Upper pads on first ledge z=55, y=1..10; lower pads under overhang z=0, y=30..44.',
        'installation':'Preassemble at table height, then push the two rubber-lined fixed C saddles over the lip from the room side. No installation or adjustment screws at the frame.',
        'case_translation_mm':[0,-80,65.2],
        'clearance_to_upward_riser_mm':2,'minimum_modeled_clearance_to_door_boundary_mm':7,
        'pad_stock_thickness_mm':3,'modeled_compressed_pad_thickness_mm':2.5,
        'physical_fit_and_load_tested':False,
        'note':'Nominal 1 mm total pad compression across both contacts. Print one saddle and check actual frame and foam fit before the full enclosure. Parameters document dimensions; explicit sketch coordinates require regeneration for changes.'}
    with open(OUT+'/doorframe_measurements.json','w') as h:json.dump(data,h,indent=2)
    cam=app.activeViewport.camera;cam.cameraType=adsk.core.CameraTypes.OrthographicCameraType
    cam.eye=adsk.core.Point3D.create(45,-2,6);cam.target=adsk.core.Point3D.create(7.1,-2,6)
    cam.upVector=adsk.core.Vector3D.create(0,0,1);cam.isFitView=True;cam.isSmoothTransition=False
    app.activeViewport.camera=cam
    app.activeViewport.saveAsImageFile(OUT+'/upward-saddle-side-check.png',1400,1100)
    print(json.dumps({'document':doc.name,'occurrences':r.occurrences.count,'measurements':data}))
