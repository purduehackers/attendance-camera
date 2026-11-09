"""Create a NEW v11 document from v10; never modifies the v10 archive.

Assembly coordinates are mm: X across the door, Y toward wall, Z up.
Print orientations are exported separately by prepare_v11_meshes.py.
"""
from pathlib import Path
import json, math, shutil, sys
import adsk.core, adsk.fusion

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'v11'
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_enclosure import component, box, circles, cuts, color, appearance, col, mmpt, V, VI, JOIN, CUT, NEW
from build_upright_v5 import side_shape, ycircles
from build_simple_v7 import xy_poly, xz_poly
from reinforce_v9 import fillet_at

RAISE = 8.5
MOUNTS = [(cx + dx, 16) for cx in (25, 189) for dx in (-7, 7)] + [(92, -2.5), (122, -2.5)]

def shift(x=0, y=0, z=0):
    m = adsk.core.Matrix3D.create(); m.translation = V(x/10, y/10, z/10)
    return m

def hexagon(c, name, x, y, af, z, h, op=CUT):
    rr = af / math.sqrt(3)
    pts = [(x + rr*math.cos(i*math.pi/3), y + rr*math.sin(i*math.pi/3)) for i in range(6)]
    return xy_poly(c, name, pts, z, h, op)

def copies(r, c, centers):
    return [r.occurrences.addExistingComponent(c, shift(x=x)) for x in centers]

def run(_context: str):
    OUT.mkdir(exist_ok=True)
    a = adsk.core.Application.get()
    doc = a.importManager.importToNewDocument(a.importManager.createFusionArchiveImportOptions(str(ROOT/'v10/doorframe-camera-simple-v10.f3d')))
    assert doc; doc.activate(); doc.name = 'Doorframe Camera - adjustable flat-print clamps v11'
    d = adsk.fusion.Design.cast(a.activeProduct); r = d.rootComponent
    light = d.appearances.itemByName('PETG - warm light grey')
    dark = d.appearances.itemByName('PETG - graphite')
    metal = d.appearances.itemByName('Reference connectors')
    rubber = d.appearances.itemByName('Reference rubber pads')
    for o in list(r.occurrences):
        if o.component.name.startswith(('07 ', '08 ', 'REFERENCE - six mount pads', 'REFERENCE - nominal ribbon')):
            assert o.deleteMe()
    case_o = next(o for o in r.occurrences if o.component.name.startswith('01 '))
    cover_o = next(o for o in r.occurrences if o.component.name.startswith('02 '))
    guard_o = next(o for o in r.occurrences if o.component.name.startswith('03 '))
    c, p, g = case_o.component, cover_o.component, guard_o.component
    c.name = '01 Electronics case - PRINT 1'
    p.name = '02 Flat front and ribbon cover - PRINT 1'
    g.name = '03 Camera guard with corner bumpers - PRINT 1'

    # Separate the old integral arms and camera carrier from the electronics box.
    box(c, 'Remove integral mount below case floor', -2, -30, 216, 50, -50, 119, CUT)
    for cx in (25, 189):
        box(c, 'Restore flat mounting floor '+str(cx), cx-10, 13, cx+10, 22, 69, .5, JOIN)
    box(c, 'Remove obsolete camera-root stub', 85.99, -11.01, 128.01, -4.99, 71.4, .71, CUT)
    circles(c, 'Six M3 bench assembly clearance holes', MOUNTS, 3.4, 68.9, 2.6, CUT)
    # Open service windows to the separate cover edge, removing 58-77 mm
    # lintels that otherwise need support when the case prints back-down.
    box(c,'Battery port open to front edge',-1,-14.1,3.2,20.5,75,77,CUT)
    box(c,'Pi side ports open to front edge',210.8,-14.1,215,18,79,58,CUT)
    box(c,'Pi top ports open to front edge',144,-14.1,203,17,164.5,2.6,CUT)
    box(c,'Relocated upper-right cover latch',205,-10,211,-5.5,164.5,2.6,CUT)
    # Thread the tether through these roof slots on the bench. This avoids an
    # inaccessible eye in the 0.6 mm clearance between the case and the wall.
    box(c, 'Reinforced 6 mm roof tether bridge', 96, -4, 120, 14, 161, 6, JOIN)
    cuts(c, 'Two accessible roof tether slots', [(99,1,104,8),(112,1,117,8)],160.9,6.2)

    # All of this cover's broad exterior now lies on one print plane.
    box(p, 'Continuous flat ribbon-cover exterior', 96, -16.2, 118, -12.6, -12.5, 86.8, JOIN)
    box(p, 'Flat base beneath lower release bridge', 84.4, -16.2, 129.6, -12.6, 1, 6, JOIN)
    for x0 in (96, 116):
        box(p, 'Extend ribbon edge flange '+str(x0), x0, -12.6, x0+2, -11.2, -12.5, 8.6, JOIN)
    box(p,'Remove old top snap over USB opening',156,-14.2,162,-5.5,162.9,2.5,CUT)
    upper=[(-14.2,163.45),(-14.2,164.25),(-9,164.25),(-9,165.2),(-8.2,165.2),(-6.8,164.25),(-6.8,163.45)]
    side_shape(p,'Relocated upper-right snap clear of ports',205.5,upper,5,JOIN)
    fillet_at(p,'Relocated snap rounded roots',[(-14.2,163.45),(-14.2,164.25)],.4,5)

    # Corner feet are 3 mm below the approximate lens nose. Remove the long
    # front-wall roof and give the aperture a 45-degree closing roof in print.
    for x0 in (83.2, 124.8):
        for y0 in (-26.45, 15.15):
            box(g, 'Flat-surface lens bumper '+str((x0,y0)), x0, y0, x0+6, y0+6, -35.7, 6.7, JOIN)
    box(g, 'Open ribbon-facing wall to eliminate large bridge', 85.6, -26.6, 128.4, -23.9, -26.6, 16.3, CUT)
    q = 11 / math.sqrt(2)
    xy_poly(g, '45 degree aperture roof for side printing', [(107-q,-q),(107+q,-q),(107,-2*q)], -29.1, 2.6, CUT)

    # New camera carrier: broad side prints flat. Root and screw supports are
    # continuous profiles; camera PCB and lens remain in their v10 positions.
    camera_o, camera = component(r, '04 Downward camera carrier - PRINT 1')
    box(camera, 'Camera spine', 86, -11, 128, -6, -6, 83.5)
    box(camera, 'Bench attachment shelf', 86, -11, 128, 4, 69.5, 8, JOIN)
    box(camera, 'Camera backplate', 86, -23.65, 128, 18.35, -10, 4, JOIN)
    cam_holes = [(x,y) for x in (96.5,117.5) for y in (-7.15,6.35)]
    for x,y in cam_holes:
        xz_poly(camera, '45 degree camera screw support '+str((x,y)),
                [(x-6.7,-10),(x-3.2,-13.5),(x+3.2,-13.5),(x+3.2,-10)], y-3.2, 6.4, JOIN)
    circles(camera, 'M2 direct screw pilots', cam_holes, 1.7, -13.5, 4, CUT)
    circles(camera, 'M2 screw entry relief', cam_holes, 2.2, -13.5, .2, CUT)
    box(camera, 'Recessed ribbon channel', 98, -11.1, 116, -9.4, -6, 83.6, CUT)
    xy_poly(camera, 'Ribbon turn with 45 degree printed roof',
            [(98,-24),(128.5,-24),(116,-11.5),(98,-11.5)], -10.1, 4.2, CUT)
    circles(camera, 'Camera shelf M3 clearance', [(92,-2.5),(122,-2.5)], 3.4, 69.4, 8.2, CUT)
    for x in (92,122): hexagon(camera, 'Camera shelf captive M3 nut '+str(x), x,-2.5,5.8,69.4,4.1)
    for side,x0,x1 in [('L',85.9,87.1),('R',126.9,128.1)]:
        box(camera, side+' camera guard latch pocket', x0,-3.4,x1,3.4,-9,3.1,CUT)
    color(camera,light)

    # Identical C-clamp brackets. Opposed pressure shoe centered under upper pad.
    left, clamp = component(r, '05 Adjustable C clamp - PRINT 2', shift(x=25))
    outline = [(-14,-24),(31,-24),(31,-12),(-4,-12),(-4,57.5),
               (11.5,57.5),(11.5,69.5),(22.4,69.5),(22.4,77.5),(-14,77.5)]
    side_shape(clamp,'10 mm web and 12 mm lower jaw',-13,outline,26)
    fillet_at(clamp,'4 mm upper and lower inner roots',[(-4,-12),(-4,57.5)],4,26)
    fillet_at(clamp,'2 mm outer clamp corners',[(-14,-24),(-14,77.5),(31,-24),(31,-12)],2,26)
    circles(clamp,'M5 sliding screw clearance',[(0,17.5)],5.6,-24.1,12.2,CUT)
    hexagon(clamp,'Captive DIN 934 M5 nut pocket',0,17.5,8.3,-24.1,4.4)
    circles(clamp,'Two M3 shelf fasteners',[(-7,16),(7,16)],3.4,69.4,8.2,CUT)
    for x in (-7,7):hexagon(clamp,'Captive shelf M3 nut '+str(x),x,16,5.8,69.4,4.1)
    # Only a loose retaining loop, not structural clamping hardware.
    cuts(clamp,'Pressure-shoe retainer tie slot',[(-3,3,3,5.5)],-24.1,12.2)
    color(clamp,light); copies(r,clamp,[189])

    shoe_o, shoe = component(r,'06 Padded pressure shoe - PRINT 2',shift(x=25))
    box(shoe,'Pressure spreader',-10,9.5,10,25.5,-8.5,6,r=2)
    box(shoe,'Loose retaining-tie tab',-4,5.5,4,11,-8.5,6,JOIN)
    cuts(shoe,'Retaining tie slot',[(-2.5,7,2.5,9)],-8.6,6.2)
    circles(shoe,'Blind seat for M5 screw tip',[(0,17.5)],5.8,-8.6,2.1,CUT)
    color(shoe,dark); copies(r,shoe,[189])

    knob_o, knob = component(r,'07 M5 hex bolt hand knob - PRINT 2',shift(x=25))
    circles(knob,'28 mm hand knob',[(0,17.5)],28,-40.5,9,NEW)
    # Rounded scallops leave a generous ring around the captured metal head.
    scallops=[(15.5*math.cos(i*math.pi/3),17.5+15.5*math.sin(i*math.pi/3)) for i in range(6)]
    circles(knob,'Six finger scallops',scallops,7,-40.6,9.2,CUT)
    circles(knob,'M5 shank clearance',[(0,17.5)],5.6,-40.6,9.2,CUT)
    hexagon(knob,'DIN 933 hex bolt head pocket',0,17.5,8.3,-40.6,4.1)
    color(knob,dark); copies(r,knob,[189])

    # Keep electronics in exactly the same case-relative positions.
    case_o.transform2 = shift(z=RAISE)
    cover_o.transform2 = shift(z=RAISE)
    for o in r.occurrences:
        if o.component.name.startswith(('REFERENCE - INIU','REFERENCE - Raspberry')):
            m=o.transform2; t=m.translation; t.z+=RAISE/10; m.translation=t; o.transform2=m
    if d.snapshots.hasPendingSnapshot:d.snapshots.add()

    # Nominal pad compression is illustrative; the screw now supplies adjustment.
    _, pads=component(r,'REFERENCE - v11 rubber contact pads')
    for cx in (25,189):
        box(pads,'Lower ledge pad '+str(cx),cx-10,.5,cx+10,10.5,55,2.5)
        box(pads,'Upper ledge pad '+str(cx),cx-10,13,cx+10,22,67,2.5)
        box(pads,'Moving shoe rubber pad '+str(cx),cx-10,9.5,cx+10,25.5,-2.5,2.5,r=2)
    color(pads,rubber)

    # Smooth fastener envelopes, not modeled helical threads.
    _, bolts=component(r,'REFERENCE - M5 x 30 DIN 933 clamp bolts')
    _, nuts=component(r,'REFERENCE - M5 DIN 934 captive nuts')
    for cx in (25,189):
        hexagon(bolts,'M5 hex head '+str(cx),cx,17.5,8,-40,3.5,NEW)
        circles(bolts,'M5 full-thread envelope '+str(cx),[(cx,17.5)],5,-36.5,30,JOIN)
        hexagon(nuts,'M5 nut '+str(cx),cx,17.5,8,-23.7,4,NEW)
        circles(nuts,'M5 thread clearance envelope '+str(cx),[(cx,17.5)],5.2,-23.8,4.2,CUT)
    color(bolts,metal);color(nuts,metal)
    _, bench=component(r,'REFERENCE - six M3 x 10 button screws and washers')
    _, mn=component(r,'REFERENCE - six M3 DIN 934 nuts')
    for x,y in MOUNTS:
        circles(bench,'M3 button head envelope '+str((x,y)),[(x,y)],5.7,80.4,1.65,NEW)
        circles(bench,'M3 screw shaft '+str((x,y)),[(x,y)],3,70.4,10,JOIN)
        circles(bench,'M3 washer OD '+str((x,y)),[(x,y)],7,79.9,.5,JOIN)
        hexagon(mn,'M3 nut '+str((x,y)),x,y,5.5,71.1,2.4,NEW)
        circles(mn,'M3 thread clearance envelope '+str((x,y)),[(x,y)],3.2,71,2.6,CUT)
    color(bench,metal);color(mn,metal)

    assert d.computeAll()
    for o in r.occurrences:
        for s in o.component.sketches:s.isLightBulbOn=False
        for plane in o.component.constructionPlanes:plane.isLightBulbOn=False
        if 'PRINT' in o.component.name:
            assert o.component.bRepBodies.count==1 and o.component.bRepBodies.item(0).isSolid,o.component.name
    for name,val,note in [('v11_clamp_web',10,'YZ profile web; print broad X face down'),
                          ('v11_clamp_jaw',12,'Lower jaw thickness'),
                          ('v11_upper_jaw',8,'Upper ledge thickness'),
                          ('v11_case_raise',RAISE,'Electronics elevation above v10')]:
        d.userParameters.add(name,VI(f'{val} mm'),'mm',note+'; rebuild geometry through script to change layout')
    for file in ['camera_verified_dimensions.json','logo.json']:
        shutil.copy2(ROOT/'v10'/file,OUT/file)
    logo=json.loads((OUT/'logo.json').read_text());logo['assembly_z_offset_mm']=RAISE
    (OUT/'logo.json').write_text(json.dumps(logo,indent=2)+'\n')
    (OUT/'layout.json').write_text(json.dumps({
        'revision':'v11','frame_mm':{'overhang':52,'lip_rise':55,'first_ledge':12,'next_rise':12,'upper_ledge':11},
        'case_raise_mm':RAISE,'case_floor_z_mm':77.5,'clamp_centers_x_mm':[25,189],
        'clamp_screw_axis_y_mm':17.5,'bench_mount_centers_xy_mm':MOUNTS,
        'clamp_shape_yz_mm':outline,'pad_stock_mm':3,'modeled_pad_mm':2.5,
        'shoe_nominal_z_mm':[-8.5,-2.5],'shoe_retracted_bottom_mm':-12,
        'nominal_lower_open_clearance_mm':3.5,'lens_reference_tip_z_mm':-32.7,
        'bumper_tip_z_mm':-35.7,'lens_extension_is_assumed':True,
        'tether':'Two 5 x 7 mm roof slots around an 8 x 6 mm bridge; independent anchor required',
        'shoe_retainers':'Two small loose cable-tie loops through shoe and bracket slots; retain loose shoes only',
        'installation':'Bench-assemble. Slide onto ledges, then hand-tighten two padded M5 clamps from below. No drilling.',
        'physical_load_tested':False,'physical_fit_tested':False,'coupon_files':[]
    },indent=2)+'\n')
    cam=a.activeViewport.camera;cam.cameraType=adsk.core.CameraTypes.OrthographicCameraType
    cam.eye=mmpt(400,-280,240);cam.target=mmpt(107,0,75);cam.upVector=V(0,0,1)
    cam.isFitView=True;cam.isSmoothTransition=False;a.activeViewport.camera=cam
    a.activeViewport.saveAsImageFile(str(OUT/'first-preview.png'),1600,1200)
    print(json.dumps({'document':doc.name,'installed_print_occurrences':sum('PRINT' in o.component.name for o in r.occurrences),'output':str(OUT)}))
