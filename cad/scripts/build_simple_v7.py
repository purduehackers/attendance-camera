from pathlib import Path
"""Three installed prints: integral structure, snap cover, snap camera guard.
Only electronics use screws: M2.5 x 6 / M2 x 4 with specified heat-set inserts.
"""
import adsk.core, adsk.fusion, sys, json, os
ROOT=str(Path(__file__).resolve().parents[1]) + ''
OUT=ROOT+'/v7'
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_enclosure import component, sketch, box, circles, cuts, extrude, color, appearance, mmpt, V, VI, NEW, JOIN, CUT
from build_upright_v5 import side_shape, ycircles

def xy_poly(c,name,pts,z,h,op=JOIN):
    s=sketch(c,name+' outline',offset=z)
    ps=[mmpt(x,y) for x,y in pts]
    for a,b in zip(ps,ps[1:]+ps[:1]):s.sketchCurves.sketchLines.addByTwoPoints(a,b)
    return extrude(c,s,h,op,name)

def xz_poly(c,name,pts,y,h,op=JOIN):
    s=sketch(c,name+' outline','y',y)
    ps=[s.modelToSketchSpace(mmpt(x,y,z)) for x,z in pts]
    for a,b in zip(ps,ps[1:]+ps[:1]):s.sketchCurves.sketchLines.addByTwoPoints(a,b)
    return extrude(c,s,h,op,name)

def run(_context: str):
    a=adsk.core.Application.get();os.makedirs(OUT,exist_ok=True)
    doc=a.importManager.importToNewDocument(a.importManager.createFusionArchiveImportOptions(ROOT+'/v5/doorframe-camera-hanging-v5.f3d'))
    assert doc;doc.activate();doc.name='Doorframe Camera - three parts - covered ribbon v7'
    d=adsk.fusion.Design.cast(a.activeProduct);r=d.rootComponent
    # Keep verified hardware placement, pads, corrected frame and the small gauge.
    for o in list(r.occurrences):
        if ' - PRINT' in o.component.name and not o.component.name.startswith('07 '):assert o.deleteMe()
    for o in r.occurrences:
        if o.component.name.startswith('REFERENCE - Raspberry'):
            m=adsk.core.Matrix3D.create()
            m.setWithCoordinateSystem(mmpt(131,60,166),V(0,0,-1),V(1,0,0),V(0,-1,0))
            o.transform2=m
        if o.component.name.startswith('REFERENCE - INIU'):
            m=adsk.core.Matrix3D.create()
            m.setWithCoordinateSystem(mmpt(129,-14,68.5),V(-1,0,0),V(0,0,1),V(0,1,0))
            o.transform2=m
    if d.snapshots.hasPendingSnapshot:d.snapshots.add()
    light=d.appearances.itemByName('PETG - warm light grey');dark=d.appearances.itemByName('PETG - graphite')
    for name,value,note in [
        ('insert_M2_hole',3.2,'CNC Kitchen M2 x 3: D1=3.6, pilot=3.2, blind depth >=4'),
        ('insert_M25_hole',4,'CNC Kitchen M2.5 x 4: D1=4.6, pilot=4, blind depth >=5'),
        ('snap_clearance',.35,'Nominal printed locator clearance; fit-test before assembly'),
    ]:
        if not d.userParameters.itemByName(name):d.userParameters.add(name,VI(f'{value} mm'),'mm',note)

    om,b=component(r,'01 Integral case mount and camera holder - PRINT')
    box(b,'Open-front case',0,-13.8,214,22.4,69,98)
    box(b,'Electronics cavity',2.4,-14,211.6,20,71.4,93.2,CUT)
    pi_holes=[(149.5,78.5),(198.5,78.5),(149.5,136.5),(198.5,136.5)]
    ycircles(b,'Pi heat-set bosses - 8 mm OD',pi_holes,8,20,-4.4,JOIN)
    ycircles(b,'Pi M2.5 insert pockets - 4 mm x 5 mm',pi_holes,4,15.6,5,CUT)
    box(b,'Pi power HDMI and audio side access',210.8,-5,215,18,79,58,CUT)
    box(b,'Battery charging-end access',-1,-11.5,3.2,20.5,75,77,CUT)
    cuts(b,'Roof vents',[(x,-8,x+3,16) for x in range(12,204,12)],164.5,2.6)
    # USB/Ethernet face up; generous common opening admits standard plug bodies.
    box(b,'Pi USB and Ethernet top access',144,-4,203,17,164.5,2.6,CUT)
    cuts(b,'Battery strap slots',[(x,y,x+12,y+2.2) for x in [38,80] for y in [-10.8,18.6]],68.9,2.6)
    for i,cx in enumerate([25,189]):
        box(b,'First-ledge foot '+str(i+1),cx-10,.5,cx+10,10.5,57.5,11.5,JOIN)
        # Upper flange and arm are one continuous part of the case.
        box(b,'Integral arm root '+str(i+1),cx-13,-14,cx+13,-3,65,4.2,JOIN)
        side_shape(b,'Integral retaining arm '+str(i+1),cx-13,
            [(-11,-7),(45,-7),(45,-2),(-1,-2),(-6,7),(-6,66),(-11,66)],26,JOIN)
        cuts(b,'Underside pad pocket '+str(i+1),[(cx-8,30,cx+8,44)],-2.5,.6)
        side_shape(b,'Arm lead-in '+str(i+1),cx-13.1,[(44.5,-2),(45,-2),(45,-2.5)],26.2,CUT)
    cuts(b,'Upper-ledge pad recesses',[(cx-10,13,cx+10,22) for cx in [25,189]],68.9,.6)
    # Clips engage roof/floor, leaving the battery and Pi side ports unobstructed.
    # The right top clip is forward of the USB/Ethernet opening.
    for cx in [55,159]:
        box(b,'Bottom cover latch window '+str(cx),cx-3,-5,cx+3,-.5,68.9,2.6,CUT)
        box(b,'Top cover latch window '+str(cx),cx-3,-10,cx+3,-5.5,164.5,2.6,CUT)

    # Camera stem has the same front/back planes as the two mounting arms.
    # The ribbon roof belongs to the removable front cover, not to this stem.
    box(b,'Camera stem floor connection',86,-11,128,-5,69,3,JOIN)
    box(b,'Flush camera stem',86,-11,128,-6,-6,75.2,JOIN)
    box(b,'Integral camera backplate',86,-23.65,128,18.35,-10,4,JOIN)
    cam_holes=[(126-x,-21.65+y) for x in [8.5,29.5] for y in [14.5,28]]
    circles(b,'Camera M2 insert bosses - 6.4 mm OD',cam_holes,6.4,-13.5,3.5,JOIN)
    circles(b,'Camera M2 insert pockets - 3.2 mm x 4 mm',cam_holes,3.2,-13.5,4,CUT)
    box(b,'Ribbon lower turn opening',98,-24,116,-11.5,-10.1,4.2,CUT)
    box(b,'Recessed ribbon channel',98,-11.1,116,-9.4,-6,75,CUT)
    # Bring the ribbon forward gently before it enters beside the battery.
    side_shape(b,'Ribbon entry guide ramp',98,[(-9.4,63),(-9.4,69),(-10,69)],18,JOIN)
    box(b,'Covered ribbon entry through floor',95.6,-14,118.4,-9.8,68.9,3.2,CUT)
    # Camera guard hooks engage these pockets from outside the base.
    for side,x0,x1 in [('L',85.9,87.1),('R',126.9,128.1)]:
        box(b,side+' camera guard latch pocket',x0,-3.4,x1,3.4,-9,3.1,CUT)
    color(b,light)

    op,p=component(r,'02 Snap-on front cover - PRINT')
    box(p,'Front cover',.2,-16.2,213.8,-14.2,69.2,97.6)
    box(p,'Clearance over integral camera root',85.6,-16.3,128.4,-14.1,69.1,3.4,CUT)
    for x in [12,24,36,48,64,88,100,112,140,152,164,176,188]:
        box(p,'Front air slot '+str(x),x,-16.3,x+4,-14.1,112,40,CUT)
    for x0,x1 in [(15,35),(180,200)]:
        box(p,'Bottom locating tab '+str(x0),x0,-14.2,x1,-10.8,71.75,1.2,JOIN)
        box(p,'Top locating tab '+str(x0),x0,-14.2,x1,-10.8,163,1.25,JOIN)
    lower=[(-14.2,71.75),(-14.2,72.95),(-1.8,72.95),(-1.8,71.75),(-3.2,70.8),(-4,70.8),(-4,71.75)]
    # Top tongues use a 0.8 mm section to flex over the shorter forward reach.
    upper=[(-14.2,163.45),(-14.2,164.25),(-9,164.25),(-9,165.2),(-8.2,165.2),(-6.8,164.25),(-6.8,163.45)]
    for cx in [55,159]:
        side_shape(p,'Bottom cover snap '+str(cx),cx-2.5,lower,5,JOIN)
        side_shape(p,'Top cover snap '+str(cx),cx-2.5,upper,5,JOIN)
    # One-piece extension of the existing cover forms a roof over the cable.
    # Its flanges stop 0.2 mm short of the fixed stem; the ribbon is not clamped.
    box(p,'Ribbon roof attachment',96,-16.2,118,-12.6,72.3,2,JOIN)
    box(p,'Continuous ribbon roof',96,-13.8,118,-12.6,-4,78.3,JOIN)
    for x0 in [96,116]:
        box(p,'Ribbon roof side flange '+str(x0),x0,-12.6,x0+2,-11.2,-4,76.3,JOIN)
    box(p,'Lower ribbon cover catch bridge',84.4,-13.8,129.6,-12.6,1,6,JOIN)
    catch=[(84.4,-13.8),(85.6,-13.8),(85.6,-5.8),(86.6,-5.8),(86.6,-5.2),(85.6,-4.8),(84.4,-4.8)]
    xy_poly(p,'Left ribbon cover release catch',catch,1.5,5)
    xy_poly(p,'Right ribbon cover release catch',[(214-x,y) for x,y in catch],1.5,5)
    color(p,dark)

    og,g=component(r,'03 Snap-on downward camera guard - PRINT')
    box(g,'Camera guard shell',83.2,-26.45,130.8,21.15,-29,18.6,r=2)
    box(g,'Camera cavity',85.6,-24.05,128.4,18.75,-26.6,16.3,CUT)
    circles(g,'Fisheye aperture',[(107,0)],22,-29.1,2.6,CUT)
    box(g,'Ribbon exit',98,-26.6,116,-23.9,-19,8.7,CUT)
    for side,x0,x1 in [('L',83.1,85.7),('R',128.3,130.9)]:
        box(g,side+' flexible tongue clearance',x0,-3.6,x1,3.6,-25,14.7,CUT)
    left=[(84.4,-25),(85.6,-25),(85.6,-8.5),(86.7,-8.5),(86.7,-7),(85.6,-5.4),(84.4,-5.4)]
    xz_poly(g,'Left releasable camera snap',left,-3,6)
    xz_poly(g,'Right releasable camera snap',[(214-x,z) for x,z in left],-3,6)
    color(g,dark)

    # Test-only heat-set coupon: verify holes using the same print/material.
    oq,q=component(r,'08 Heat-set test coupon - TEST PRINT')
    box(q,'Insert coupon base',245,0,280,16,0,2)
    circles(q,'M2 coupon boss',[(253,8)],6.4,2,5,JOIN)
    circles(q,'M2 coupon 3.2 x 4 hole',[(253,8)],3.2,7,-4,CUT)
    circles(q,'M2.5 coupon boss',[(271,8)],8,2,6,JOIN)
    circles(q,'M2.5 coupon 4 x 5 hole',[(271,8)],4,8,-5,CUT)
    color(q,light);oq.isLightBulbOn=False
    # Product designation, not a generic insert size: alternatives need resizing.
    spec={'revision':'v7 flush support and captive ribbon cover',
        'installed_prints':['integral case, retaining arms and camera holder','snap-on front cover with integral ribbon roof','snap-on camera guard'],
        'screws':[{'quantity':4,'size':'M2.5 x 6','pitch_mm':.45,'standard':'ISO 4762 / DIN 912','head_diameter_mm':4.5,'head_height_mm':2.5,'hex_key_mm':2,'purpose':'Pi'},
                  {'quantity':4,'size':'M2 x 4','pitch_mm':.4,'standard':'ISO 4762 / DIN 912','head_diameter_mm':3.8,'head_height_mm':2,'hex_key_mm':1.5,'purpose':'camera'}],
        'inserts':[{'quantity':4,'manufacturer':'CNC Kitchen','type':'M2.5 x 4','part':'TC-M2.5x4.0','length_mm':4,'outer_diameter_mm':4.6,'pilot_mm':4,'depth_mm':5,'boss_od_mm':8},
                   {'quantity':4,'manufacturer':'CNC Kitchen','type':'M2 x 3','length_mm':3,'outer_diameter_mm':3.6,'pilot_mm':3.2,'depth_mm':4,'boss_od_mm':6.4}],
        'source_insert_drawing':'https://cnckitchen.store/cdn/shop/files/Table_Metic.png',
        'source_insert_M2':'https://cnckitchen.store/products/heat-set-insert-m2-x-3-100-pieces',
        'source_insert_M25':'https://cnckitchen.store/products/gewindeeinsatz-threaded-insert-m2-5-standard-100-stk-pcs',
        'source_screw_M2':'https://www.accu.co.uk/metric-cap-head-screws/3790-SSCF-M2-4-A2',
        'source_screw_M25':'https://www.accu.co.uk/metric-cap-head-screws/3804-SSCF-M2-5-6-A2',
        'physical_fit_tested':False,'snap_fit_tested':False,'ribbon_channel_mm':{'clear_width':18,'floor_y':-9.4,'roof_inner_y':-12.6,'clear_depth':3.2,'cable_envelope_assumption':[16,.35]},
        'printing_note':'The integral body trades assembly joints for supports. Print with removable supports; largest body footprint is about 214 by 181 mm in the supplied orientation.'}
    with open(OUT+'/hardware.json','w') as h:json.dump(spec,h,indent=2)
    d.computeAll()
    cam=a.activeViewport.camera;cam.cameraType=adsk.core.CameraTypes.OrthographicCameraType
    cam.eye=mmpt(430,-250,230);cam.target=mmpt(107,0,80);cam.upVector=V(0,0,1)
    cam.isFitView=True;cam.isSmoothTransition=False;a.activeViewport.camera=cam
    a.activeViewport.saveAsImageFile(OUT+'/first-preview.png',1600,1100)
    print(json.dumps({'document':doc.name,'occurrences':r.occurrences.count,'hardware':spec}))
