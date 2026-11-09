from pathlib import Path
"""Narrow upright enclosure, upward stepped support and downward camera.
Frame mounting is a passive slide-on saddle; all screws are bench assembly.
"""
import adsk.core, adsk.fusion, json, math, sys
OUT=str(Path(__file__).resolve().parents[1]) + ''
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_enclosure import component, sketch, box, circles, cuts, extrude, color, appearance, mmpt, V, VI, NEW, JOIN, CUT

def side_shape(c,name,x,pts,width,op=NEW):
    s=sketch(c,name+' outline','x',x)
    ps=[s.modelToSketchSpace(mmpt(x,y,z)) for y,z in pts]
    for a,b in zip(ps,ps[1:]+ps[:1]):s.sketchCurves.sketchLines.addByTwoPoints(a,b)
    return extrude(c,s,width,op,name)

def ycircles(c,name,centres,diam,y,depth,op):
    s=sketch(c,name+' layout','y',y)
    for x,z in centres:s.sketchCurves.sketchCircles.addByCenterRadius(s.modelToSketchSpace(mmpt(x,y,z)),diam/20)
    return extrude(c,s,depth,op,name)

def run(_context: str):
    app=adsk.core.Application.get()
    doc=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(OUT+'/revisions/doorframe-camera-v2.f3d'))
    assert doc;doc.activate();doc.name='Doorframe Camera - upright battery and Pi - downward camera v5'
    d=adsk.fusion.Design.cast(app.activeProduct);r=d.rootComponent
    for o in list(r.occurrences):
        if o.component.name.startswith(('01 ','02 ','03 ','06 ','REFERENCE - four')):assert o.deleteMe()
    dark=d.appearances.itemByName('PETG - graphite');light=d.appearances.itemByName('PETG - warm light grey')
    rubber=d.appearances.itemByName('Reference rubber pads')
    for o in r.occurrences:
        if o.isGrounded:o.isGrounded=False
        if o.isGroundToParent:o.isGroundToParent=False
        m=adsk.core.Matrix3D.create()
        if o.component.name.startswith('REFERENCE - INIU'):
            m.setWithCoordinateSystem(mmpt(70,-14,156.5),V(1,0,0),V(0,0,-1),V(0,1,0))
        elif o.component.name.startswith('REFERENCE - Raspberry'):
            m.setWithCoordinateSystem(mmpt(77,60,69),V(0,0,1),V(-1,0,0),V(0,-1,0))
        else:
            m.setWithCoordinateSystem(mmpt(126,-21.65,-8),V(-1,0,0),V(0,1,0),V(0,0,-1))
        o.transform2=m
    if d.snapshots.hasPendingSnapshot:d.snapshots.add()

    ob,b=component(r,'01 Upright Pi and battery shell - PRINT')
    box(b,'Upright open-front shell',0,-13.8,214,22.4,69,98)
    box(b,'Electronics cavity',2.4,-14,211.6,20,71.4,93.2,CUT)
    panel_corners=[(3,72),(211,72),(3,164),(211,164)]
    ycircles(b,'Front panel screw pillars',panel_corners,6,-13.8,33.8,JOIN)
    ycircles(b,'M2.5 front panel pilots',panel_corners,2.1,-13.9,6,CUT)
    pi_holes=[(9.5,98.5),(58.5,98.5),(9.5,156.5),(58.5,156.5)]
    ycircles(b,'Vertical Pi standoffs',pi_holes,6,20,-4.4,JOIN)
    ycircles(b,'Pi M2.5 pilots',pi_holes,2.1,15.5,4.6,CUT)
    # Only the power/HDMI/audio side is exposed; USB/Ethernet are not needed for
    # this Wi-Fi camera and are serviced with the board removed.
    box(b,'Pi power and HDMI side access',-1,-5,3.2,18,99,58,CUT)
    box(b,'Battery cable and button access',210.8,-10,215,19,92,56,CUT)
    cuts(b,'Top air slots',[(x,-8,x+3,16) for x in range(12,204,12)],164.5,2.6)
    cuts(b,'Battery strap slots',[(x,y,x+12,y+2.2) for x in [116,160] for y in [-10.8,18.6]],68.9,2.6)
    # Feet reach both upward-facing ledges: front ledge at z55, rear at z67.
    for i,cx in enumerate([25,189]):
        box(b,'Lower-ledge foot '+str(i+1),cx-10,.5,cx+10,10.5,57,12,JOIN)
        cuts(b,'Lower-ledge pad recess '+str(i+1),[(cx-10,.5,cx+10,10.5)],56.9,.6)
    cuts(b,'Upper-ledge pad recesses',[(cx-10,13,cx+10,22) for cx in [25,189]],68.9,.6)
    circles(b,'Bench saddle attachment M3 clearance',[(cx+dx,-8.5) for cx in [25,189] for dx in [-5,5]],3.4,68.9,2.6,CUT)
    color(b,light)

    ol,l=component(r,'02 Vented front service panel - PRINT')
    box(l,'Removable front panel',0,-16.2,214,-13.8,69,98)
    ycircles(l,'M2.5 panel clearance',panel_corners,2.8,-16.3,2.6,CUT)
    for x in [12,24,36,48,64,140,152,164,176,188]:
        box(l,'Vertical air slot '+str(x),x,-16.3,x+3,-13.7,112,40,CUT)
    box(l,'Camera ribbon entry',98,-16.3,116,-13.7,110,3,CUT)
    ycircles(l,'Camera support M3 clearance',[(95,84),(119,84),(95,116),(119,116)],3.4,-16.3,2.6,CUT)
    color(l,dark)

    for side,cx in [('left',25),('right',189)]:
        os,s=component(r,'03 '+side+' passive retaining saddle - PRINT')
        side_shape(s,'Fixed retaining saddle',cx-13,
            [(-11,-7),(45,-7),(45,-2),(-1,-2),(-6,7),(-6,66),(-11,66)],26)
        box(s,'Bench attachment flange',cx-13,-14,cx+13,-3,66,3,JOIN)
        circles(s,'M3 saddle pilots',[(cx-5,-8.5),(cx+5,-8.5)],2.5,69.1,-7.1,CUT)
        cuts(s,'Underside rubber pocket',[(cx-8,30,cx+8,44)],-2.5,.6)
        side_shape(s,'Entry lead-in',cx-13.1,[(44.5,-2),(45,-2),(45,-2.5)],26.2,CUT)
        color(s,light)

    oc,c=component(r,'06 Straight-down camera support - PRINT')
    box(c,'Camera support plate',86,-23,128,17.5,-8,4)
    box(c,'Camera hanging spine',86,-20.4,128,-16.2,-4,124,JOIN)
    for x in [86,124]:box(c,'Spine edge rib '+str(x),x,-22.4,x+4,-20.4,-4,124,JOIN)
    # The pod's local +Z (optical direction) is world -Z.
    carrier_holes=[(126-x,-21.65+y) for x in [3.5,34.5] for y in [11,22]]
    circles(c,'Camera carrier M3 pilots',carrier_holes,2.5,-8.1,4.2,CUT)
    circles(c,'Camera nut relief',[(126-x,-21.65+y) for x in [8.5,29.5] for y in [14.5,28]],5.2,-8.1,2.1,CUT)
    circles(c,'Cap screw head relief',[(126-x,-21.65+y) for x in [3.5,34.5] for y in [3.5,34.5]],5.5,-8.1,3.3,CUT)
    box(c,'Ribbon turn opening',98,-24,116,-16,-8.1,4.3,CUT)
    box(c,'Open vertical ribbon groove',98,-20.5,116,-18.8,-4,114,CUT)
    box(c,'Ribbon entry through spine',98,-23,116,-16.1,110,3,CUT)
    ycircles(c,'Panel-side M3 pilots',[(95,84),(119,84),(95,116),(119,116)],2.5,-16.1,-4.4,CUT)
    color(c,dark)

    op,p=component(r,'REFERENCE - six mount pads - compressed')
    for side,cx in [('left',25),('right',189)]:
        box(p,side+' lower-ledge pad - 20 x 10 x 3',cx-10,.5,cx+10,10.5,55,2.5)
        box(p,side+' upper-ledge pad - 20 x 9 x 3',cx-10,13,cx+10,22,67,2.5)
        box(p,side+' underside retaining pad - 16 x 14 x 3',cx-8,30,cx+8,44,-2.5,2.5)
    color(p,rubber)

    of,f=component(r,'REFERENCE - upward-stepped frame - back wall assumed')
    side_shape(f,'Corrected upward frame',-10,
        [(0,0),(52,0),(52,180),(23,180),(23,67),(12,67),(12,55),(0,55)],234)
    color(f,appearance(d,'Upward frame reference',158,133,103))

    og,g=component(r,'07 Upward-step fit gauge PRINT FIRST - PRINT')
    side_shape(g,'Profile fit gauge',245,[(-.6,0),(-.6,55.6),(11.4,55.6),(11.4,67.6),(23,67.6),(23,70),(9,70),(9,58),(-3,58),(-3,0)],8)
    color(g,light);og.isLightBulbOn=False
    d.computeAll()
    meta={'revision':'v5 upright electronics, downward camera, passive retaining saddles',
        'frame_mm':{'overhang':52,'lip_rise':55,'first_ledge':12,'next_rise':12,'upper_ledge':11},
        'orientation':'Underside z=0; front face y=0 rises to z55; ledge y0..12 at z55; next face y12 rises to z67; upper ledge y12..23 at z67. Conservative wall boundary at y23 above z67. Door boundary y52.',
        'case_outer_mm':[214,38.6,98],'case_bounds_mm':{'x':[0,214],'y':[-16.2,22.4],'z':[69,167]},
        'mount_contacts':'Four top pads across both ledges, plus two fixed padded arms under the overhang.',
        'installation':'All assembly screws fitted on a table; slide completed enclosure over the frame from room side; no adjustment or tightening at height.',
        'camera_axis_world':[0,0,-1],'camera_lens_center_xy_mm':[107,0],
        'minimum_door_boundary_clearance_mm':7,'back_wall_clearance_mm':.6,
        'pad_stock_mm':3,'pad_modeled_compressed_mm':2.5,
        'physical_fit_load_and_door_swing_tested':False,
        'assumption':'Top 11 mm ledge meets wall. Model deliberately fits in front of that boundary; wall height is illustrative.',
        'cable_note':'Ribbon follows open front groove to side of Pi; verify actual ribbon length and connector orientation before print.'}
    with open(OUT+'/doorframe_measurements.json','w') as h:json.dump(meta,h,indent=2)
    cam=app.activeViewport.camera;cam.cameraType=adsk.core.CameraTypes.OrthographicCameraType
    cam.eye=adsk.core.Point3D.create(43,-25,23);cam.target=adsk.core.Point3D.create(10.7,0,8)
    cam.upVector=V(0,0,1);cam.isFitView=True;cam.isSmoothTransition=False;app.activeViewport.camera=cam
    app.activeViewport.saveAsImageFile(OUT+'/upright-v5-preview.png',1600,1100)
    print(json.dumps({'document':doc.name,'occurrences':r.occurrences.count,'metadata':meta}))
