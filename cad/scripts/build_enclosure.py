from pathlib import Path
"""Fusion-native prototype. All input dimensions are millimetres.

Creates a NEW document. Hardware envelopes are references, not printable parts.
Camera PCB geometry comes from Waveshare's E/F/G/H mechanical DWG.
"""
import adsk.core, adsk.fusion, math, json

OUT = str(Path(__file__).resolve().parents[1]) + ''
P = adsk.core.Point3D.create
V = adsk.core.Vector3D.create
VI = adsk.core.ValueInput.createByString
NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
JOIN = adsk.fusion.FeatureOperations.JoinFeatureOperation
CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

def mmpt(x,y,z=0): return P(x/10,y/10,z/10)
def col(items):
    c=adsk.core.ObjectCollection.create()
    for item in items:c.add(item)
    return c

def sketch(comp,name,axis='z',offset=0):
    base={'z':comp.xYConstructionPlane,'y':comp.xZConstructionPlane,'x':comp.yZConstructionPlane}[axis]
    if offset:
        pi=comp.constructionPlanes.createInput()
        pi.setByOffset(base,VI(f'{offset} mm'))
        base=comp.constructionPlanes.add(pi);base.name=name+' plane';base.isLightBulbOn=False
    s=comp.sketches.add(base);s.name=name
    return s

def rect(s,x0,y0,x1,y1):
    return s.sketchCurves.sketchLines.addTwoPointRectangle(mmpt(x0,y0),mmpt(x1,y1))

def rounded(s,x0,y0,x1,y1,r):
    lines=s.sketchCurves.sketchLines; arcs=s.sketchCurves.sketchArcs
    for a,b in [((x0+r,y0),(x1-r,y0)),((x1,y0+r),(x1,y1-r)),((x1-r,y1),(x0+r,y1)),((x0,y1-r),(x0,y0+r))]:
        lines.addByTwoPoints(mmpt(*a),mmpt(*b))
    for c,a in [((x1-r,y0+r),(x1-r,y0)),((x1-r,y1-r),(x1,y1-r)),((x0+r,y1-r),(x0+r,y1)),((x0+r,y0+r),(x0,y0+r))]:
        arcs.addByCenterStartSweep(mmpt(*c),mmpt(*a),math.pi/2)

def extrude(comp,s,depth,op,name):
    assert s.profiles.count>0,name+' has no closed profile'
    profiles=col([s.profiles.item(i) for i in range(s.profiles.count)])
    inp=comp.features.extrudeFeatures.createInput(profiles,op)
    inp.setDistanceExtent(False,VI(str(depth) if isinstance(depth,str) else f'{depth} mm'))
    if op==CUT:
        inp.participantBodies=[comp.bRepBodies.item(i) for i in range(comp.bRepBodies.count)]
    f=comp.features.extrudeFeatures.add(inp)
    f.name=name;s.isLightBulbOn=False
    return f

def box(comp,name,x0,y0,x1,y1,z,h,op=NEW,r=0):
    s=sketch(comp,name+' outline',offset=z)
    if r:rounded(s,x0,y0,x1,y1,r)
    else:rect(s,x0,y0,x1,y1)
    f=extrude(comp,s,h,op,name)
    if op==NEW:f.bodies.item(0).name=name
    return f

def circles(comp,name,centres,diam,z,h,op):
    s=sketch(comp,name+' layout',offset=z)
    for x,y in centres:s.sketchCurves.sketchCircles.addByCenterRadius(mmpt(x,y),diam/20)
    return extrude(comp,s,h,op,name)

def cuts(comp,name,rects,z,h):
    s=sketch(comp,name+' layout',offset=z)
    for r in rects:rect(s,*r)
    return extrude(comp,s,h,CUT,name)

def transverse_holes(comp,name,axis,offset,centres,diam,length):
    s=sketch(comp,name+' layout',axis,offset)
    for a,b in centres:
        w=mmpt(a,offset,b) if axis=='y' else mmpt(offset,a,b)
        s.sketchCurves.sketchCircles.addByCenterRadius(s.modelToSketchSpace(w),diam/20)
    return extrude(comp,s,length,CUT,name)

def component(root,name,matrix=None):
    o=root.occurrences.addNewComponent(matrix or adsk.core.Matrix3D.create())
    o.component.name=name
    return o,o.component

def appearance(design,name,r,g,b):
    a=design.appearances.add(name)
    a.color=adsk.core.Color.create(r,g,b,255);a.roughness=.65
    return a

def color(comp,a):
    for b in comp.bRepBodies:b.appearance=a

def run(_context: str):
    app=adsk.core.Application.get()
    existing=adsk.fusion.Design.cast(app.activeProduct)
    if existing and existing.rootComponent.occurrences.count==0 and existing.timeline.count==0 and app.activeDocument.name.startswith('Doorframe Camera - Pi4'):
        doc=app.activeDocument
    else:
        doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name='Doorframe Camera - Pi4 + INIU + Waveshare G - prototype v2'
    d=adsk.fusion.Design.cast(app.activeProduct)
    d.designType=adsk.fusion.DesignTypes.ParametricDesignType
    root=d.rootComponent
    d.unitsManager.distanceDisplayUnits=adsk.fusion.DistanceUnits.MillimeterDistanceUnits
    for name,expr,note in [
        ('wall','2.4 mm','Printed shell wall and tray thickness'),
        ('battery_tray_height','37 mm','Battery chamber outside height'),
        ('upper_height','32 mm','Pi chamber height above battery tray'),
        ('lid_thickness','2.4 mm','Removable lid'),
        ('pi_standoff_height','5 mm','Pi underside clearance'),
        ('pad_recess_depth','0.8 mm','Use 3 mm rubber pads; 2.2 mm projects below case'),
        ('camera_carrier_thickness','3 mm','Camera backplate'),
        ('camera_standoff_height','2.5 mm','Clearance under camera PCB'),
        ('camera_lens_opening','22 mm','Generous opening; check actual lens barrel before final print'),
        ('camera_cap_height','17 mm','Cap height above carrier; lens must project beyond the front'),
    ]:d.userParameters.add(name,VI(expr),'mm',note)
    shell=appearance(d,'PETG - warm light grey',206,211,214)
    dark=appearance(d,'PETG - graphite',45,52,59)
    pcb=appearance(d,'Reference PCB green',27,104,66)
    bat=appearance(d,'Reference INIU battery',40,43,47)
    rubber=appearance(d,'Reference rubber pads',30,30,30)
    metal=appearance(d,'Reference connectors',155,161,169)
    corner=[(5,5),(137,5),(5,83),(137,83)]

    # Battery is lowest in the assembly to keep its mass near the support surface.
    ob,b=component(root,'01 Battery tray - PRINT')
    box(b,'Battery tray shell',0,0,142,88,0,'battery_tray_height',r=4)
    box(b,'Battery chamber',2.4,2.4,139.6,85.6,2.4,37,CUT,r=1.6)
    circles(b,'Four corner screw pillars',corner,8,2.4,34.6,JOIN)
    circles(b,'M3 pilot holes - hand tap or plastic screws',corner,2.5,22,16,CUT)
    cuts(b,'Battery strap slots - two 10 mm straps',[(41,4,53,6.2),(41,81.8,53,84),(94,4,106,6.2),(94,81.8,106,84)],0,3)
    cuts(b,'Rubber pad pockets - 20 x 10 mm',[(12,7,32,17),(110,7,130,17),(12,71,32,81),(110,71,130,81)],0,'pad_recess_depth')
    cuts(b,'Battery air slots',[(x,-1,x+3,3.2) for x in range(18,121,10)]+[(x,84.8,x+3,89) for x in range(18,121,10)],12,17)
    cuts(b,'Battery connector access',[(139,12,143,76)],8,25)
    # Rails retain the pack without squeezing it; foam pads and straps take up tolerance.
    box(b,'Battery end stop',3.0,18,5.0,70,2.4,4,JOIN)
    box(b,'Battery cable-side stop',122.5,18,124.5,70,2.4,4,JOIN)
    # Two mounting holes remain outside the battery footprint in the cable channel.
    circles(b,'M4 mounting interface',[(132,26),(132,62)],4.5,0,3,CUT)
    color(b,shell)

    ou,u=component(root,'02 Pi tray and upper shell - PRINT')
    box(u,'Upper shell',0,0,142,88,37,'upper_height',r=4)
    box(u,'Pi chamber',2.4,2.4,139.6,85.6,39.4,32,CUT,r=1.6)
    circles(u,'Upper corner pillars',corner,8,39.4,29.6,JOIN)
    circles(u,'M3 long-screw clearance',corner,3.4,36.8,33,CUT)
    # Pi rotated 180 degrees, with USB/Ethernet on the left, power/HDMI at the rear.
    pi_holes=[(87.5,67.5),(29.5,67.5),(87.5,18.5),(29.5,18.5)]
    circles(u,'Pi4 mounting standoffs - 58 x 49 mm',pi_holes,6,39.4,'pi_standoff_height',JOIN)
    circles(u,'M2.5 Pi screw pilot holes',pi_holes,2.1,38.0,7.4,CUT)
    cuts(u,'USB and Ethernet access', [(-1,12,3.2,76)],43.6,20)
    cuts(u,'USB-C and micro-HDMI access',[(24,84.8,92,89)],43.5,13)
    cuts(u,'Power and ribbon cable passage',[(125,20,135,68)],36.9,3)
    cuts(u,'Ventilation front',[(x,-1,x+3,3.2) for x in [13,23,33,43,101,111,121]],47,15)
    cuts(u,'Ventilation right',[(139,12,143,22),(139,31,143,41),(139,50,143,60),(139,69,143,79)],49,12)
    # Camera bracket bolt pattern, on front wall; keep clear of connector windows.
    transverse_holes(u,'Camera bracket M3 clearance','y',0,[(59,49),(83,49),(59,61),(83,61)],3.4,3)
    color(u,shell)

    ol,l=component(root,'03 Vented lid - PRINT')
    box(l,'Lid',0,0,142,88,69,'lid_thickness',r=4)
    circles(l,'M3 lid clearance',corner,3.4,68.9,3,CUT)
    cuts(l,'Lid ventilation',[(x,12,x+3,76) for x in range(14,129,8)],68.9,3)
    # Four small registration tabs, 0.4 mm lateral clearance from shell.
    for i,(x0,y0,x1,y1) in enumerate([(15,2.8,30,4.0),(111,2.8,126,4.0),(15,84,30,85.2),(111,84,126,85.2)]):
        box(l,'Lid alignment tab '+str(i+1),x0,y0,x1,y1,66.5,2.5,JOIN)
    color(l,dark)

    # Hardware envelopes, intentionally simplified and excluded from printable export.
    oh,h=component(root,'REFERENCE - INIU P51L-E2 115 x 73 x 29 mm')
    box(h,'INIU envelope - check supplied cable position',6,7.5,121,80.5,4.4,29,r=5)
    color(h,bat)
    op,pr=component(root,'REFERENCE - Raspberry Pi4 rotated ports')
    box(pr,'Pi PCB 85 x 56 x 1.6',6,15,91,71,44.4,1.6,r=3)
    circles(pr,'Pi mounting holes',pi_holes,2.75,44.3,2,CUT)
    color(pr,pcb)
    for name,x0,y0,x1,y1,ht in [('USB3',3,55.4,20.5,68.6,16),('USB2',3,37.4,20.5,50.6,16),('Ethernet',3,17.5,24.5,33.5,13.5),('USB-C',73.5,64,86.1,72,3.2),('HDMI0',60.5,64,69.5,72,3),('HDMI1',47,64,56,72,3),('Audio',33.5,58,40.5,72,6)]:
        f=box(pr,name,x0,y0,x1,y1,46,ht);f.bodies.item(0).appearance=metal
    opad,pads=component(root,'REFERENCE - four 20 x 10 x 3 mm rubber pads')
    for i,(x,y) in enumerate([(12,7),(110,7),(12,71),(110,71)]):
        box(pads,'Rubber pad '+str(i+1),x,y,x+20,y+10,-2.2,3,r=1)
    color(pads,rubber)

    # Camera components are initially laid out beside the main enclosure.
    # Placement will be updated once the doorframe viewing direction is confirmed.
    m=adsk.core.Matrix3D.create();m.translation=V(16.5,0,0)
    oc,carrier=component(root,'04 Camera G carrier - PRINT',m)
    box(carrier,'Camera carrier',0,0,38,38,0,'camera_carrier_thickness',r=3)
    camholes=[(8.5,14.5),(29.5,14.5),(8.5,28),(29.5,28)]
    circles(carrier,'Waveshare G PCB supports',camholes,4.6,3,'camera_standoff_height',JOIN)
    circles(carrier,'M2 camera through holes - 21 x 13.5 mm',camholes,2.3,0,6,CUT)
    circles(carrier,'M2 nut recesses',camholes,4.7,0,1.7,CUT)
    # M2 nylon hardware fits through the camera and standoffs into rear nuts.
    capholes=[(3.5,3.5),(34.5,3.5),(3.5,34.5),(34.5,34.5)]
    circles(carrier,'Camera cap M2.5 clearance',capholes,2.8,0,3.2,CUT)
    circles(carrier,'Camera bracket M3 clearance',[(3.5,11),(34.5,11),(3.5,22),(34.5,22)],3.4,0,3.2,CUT)
    color(carrier,dark)
    ocap,cap=component(root,'05 Camera G protective cap - PRINT',m)
    box(cap,'Camera cap shell',0,0,38,38,3,'camera_cap_height',r=3)
    box(cap,'Camera body clearance',2.4,2.4,35.6,35.6,2.9,14.7,CUT,r=.6)
    # Give the lens room to protrude; no hood ahead of a 160 degree fisheye.
    s=sketch(cap,'Fisheye clearance',offset=17.5)
    c=s.sketchCurves.sketchCircles.addByCenterRadius(mmpt(19,21.65),1.1)
    dim=s.sketchDimensions.addDiameterDimension(c,mmpt(33,25));dim.parameter.expression='camera_lens_opening'
    extrude(cap,s,3,CUT,'Fisheye aperture')
    circles(cap,'Cap screw pillars',capholes,6,3,14.6,JOIN)
    circles(cap,'M2.5 cap pilots',capholes,2.1,2.9,8,CUT)
    cuts(cap,'Ribbon cable exit',[(10,-1,28,3)],3,5)
    color(cap,shell)
    ocam,cr=component(root,'REFERENCE - Waveshare RPi Camera G PCB and lens',m)
    box(cr,'Camera PCB 25 x 24',6.5,6,31.5,30,5.5,1.2)
    circles(cr,'Camera mounting holes',camholes,2.2,5.4,1.5,CUT)
    color(cr,pcb)
    # Barrel is a clearance reference; height and diameter require a physical fit check.
    cf=circles(cr,'Approximate fisheye barrel - verify height',[(19,21.65)],16,6.7,18,NEW)
    cf.bodies.item(0).appearance=bat

    for comp in root.allOccurrences:
        for sk in comp.component.sketches:sk.isLightBulbOn=False
        for cp in comp.component.constructionPlanes:cp.isLightBulbOn=False
    app.activeViewport.camera=fit_camera(app)
    print(json.dumps({'document':doc.name,'components':root.occurrences.count,'timeline_features':d.timeline.count,'case_mm':[142,88,71.4],'camera':'Waveshare RPi Camera G','mount_pitch_mm':[21,13.5],'doorframe_mount':'Pending frame dimensions and retention choice'}))

def fit_camera(app):
    c=app.activeViewport.camera
    c.viewOrientation=adsk.core.ViewOrientations.IsoTopRightViewOrientation
    c.isFitView=True;c.isSmoothTransition=False
    return c
