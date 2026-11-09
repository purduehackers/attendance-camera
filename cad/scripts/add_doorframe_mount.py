from pathlib import Path
"""Add removable padded clamps to the existing v2 camera enclosure.

All geometry inputs are mm. Frame orientation is an interpretation of Ray's
confirmed cross-section; print the separate gauge before making the full mount.
"""
import adsk.core, adsk.fusion, math, json, sys
OUT=str(Path(__file__).resolve().parents[1]) + ''
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_enclosure import component, sketch, box, circles, cuts, extrude, color, appearance, mmpt, VI, NEW, JOIN, CUT

def side_polygon(comp,name,x,points,width):
    s=sketch(comp,name+' profile','x',x)
    pts=[s.modelToSketchSpace(mmpt(x,y,z)) for y,z in points]
    for a,b in zip(pts,pts[1:]+pts[:1]):s.sketchCurves.sketchLines.addByTwoPoints(a,b)
    return extrude(comp,s,width,NEW,name)

def hex_cut(comp,name,x,y,z,af,depth):
    s=sketch(comp,name+' outline',offset=z)
    radius=af/math.sqrt(3)
    pts=[mmpt(x+radius*math.cos(i*math.pi/3),y+radius*math.sin(i*math.pi/3)) for i in range(6)]
    for a,b in zip(pts,pts[1:]+pts[:1]):s.sketchCurves.sketchLines.addByTwoPoints(a,b)
    return extrude(comp,s,depth,CUT,name)

def run(_context: str):
    app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);root=d.rootComponent
    assert 'prototype v2' in app.activeDocument.name,app.activeDocument.name
    assert root.occurrences.count==10,root.occurrences.count
    for name,value,note in [
        ('frame_overhang',52,'Confirmed ledge width; positive Y points toward door'),
        ('frame_lip_height',55,'Confirmed first vertical face height'),
        ('frame_inset',12,'Confirmed first underside return'),
        ('frame_step_height',12,'Confirmed second vertical step'),
        ('frame_step_width',11,'Confirmed second underside return'),
        ('frame_fit_clearance',.6,'Gauge clearance; documentation parameter'),
        ('jaw_slide_clearance',.35,'Clearance per guide side; documentation parameter'),
    ]:d.userParameters.add(name,VI(f'{value} mm'),'mm',note)
    # Preserve assembled camera rotation and move the whole enclosure as one unit.
    for o in list(root.occurrences):
        if o.isGrounded:o.isGrounded=False
        if o.isGroundToParent:o.isGroundToParent=False
        m=o.transform2;t=m.translation;t.y-=4;t.z+=1.02;m.translation=t;o.transform2=m
    if d.snapshots.hasPendingSnapshot:d.snapshots.add()
    dark=d.appearances.itemByName('PETG - graphite')
    shell=d.appearances.itemByName('PETG - warm light grey')
    rubber=d.appearances.itemByName('Reference rubber pads')
    frame_mat=appearance(d,'Reference doorframe profile',158,133,103)

    op,p=component(root,'07 Doorframe mounting platform - PRINT')
    box(p,'Six mm platform',-24,-42,166,50,2,6,r=3)
    cuts(p,'Platform lightening windows',[(8,-17,59,27),(69,-17,119,27)],1.9,6.2)
    circles(p,'Case hard mounting bosses',[(132,-14),(132,22)],10,8,2.2,JOIN)
    circles(p,'Case M4 clearance',[(132,-14),(132,22)],4.5,1.9,8.4,CUT)
    cuts(p,'Side-load M4 captive nut channels',[(127.8,y-3.6,167,y+3.6) for y in [-14,22]],3,3.4)
    for index,(x0,y0,x1,y1) in enumerate([
        (10,48.6,30,50),(112,48.6,132,50),
        (10,-41.6,30,-40.4),(112,-41.6,132,-40.4),
        (-1.6,-30,-.4,-20),(-1.6,28,-.4,38),
        (142.4,-30,143.6,-20),(142.4,28,143.6,38),
    ]):box(p,f'Case locating tab {index+1}',x0,y0,x1,y1,8,6,JOIN)
    circles(p,'M4 long clamp bolt clearance',[(-10,-24),(152,-24)],4.5,1.9,6.2,CUT)
    circles(p,'M3 guide attachment clearance',[(cx+dx,-8.5) for cx in [-10,152] for dx in [-5,5]],3.4,1.9,6.2,CUT)
    contact_rects=[(x,y,x+20,y+14) for x in [-21,143] for y in [2,33]]
    cuts(p,'Top-ledge rubber pad recesses',contact_rects,1.9,.6)
    color(p,dark)

    for side,cx in [('left',-10),('right',152)]:
        og,g=component(root,'08 '+side+' clamp guide - PRINT')
        box(g,'Guide beam',cx-10,-11,cx+10,-6,-53,52)
        box(g,'Guide mounting flange',cx-13,-14,cx+13,-3,-1,3,JOIN)
        circles(g,'Two M3 guide pilots',[(cx-5,-8.5),(cx+5,-8.5)],2.5,2.1,-7.1,CUT)
        color(g,dark)

        oj,j=component(root,'09 '+side+' sliding clamp jaw - PRINT')
        box(j,'Lower clamping jaw',cx-13.35,-29,cx+13.35,11.2,-62,5)
        box(j,'Antirotation guide sleeve',cx-13.35,-14.35,cx+13.35,-2.65,-57,16,JOIN)
        box(j,'Sliding guide clearance',cx-10.35,-11.35,cx+10.35,-5.65,-57,16.1,CUT)
        circles(j,'M4 long bolt clearance',[(cx,-24)],4.5,-62.1,5.2,CUT)
        hex_cut(j,'Captive M4 nut',cx,-24,-62.1,7.2,3.5)
        cuts(j,'Jaw rubber pad recess',[(cx-8,1.5,cx+8,10.5)],-57.5,.6)
        color(j,shell)

    orp,rp=component(root,'REFERENCE - six compressed mount rubber pads')
    for i,(x0,y0,x1,y1) in enumerate(contact_rects):
        box(rp,f'Top-ledge pad {i+1} - nominal 3 mm foam',x0,y0,x1,y1,0,2.5)
    for side,cx in [('left',-10),('right',152)]:
        box(rp,side+' underside pad - nominal 3 mm foam',cx-8,1.5,cx+8,10.5,-57.5,2.5)
    color(rp,rubber)

    of,f=component(root,'REFERENCE - measured doorframe profile - assumed orientation')
    side_polygon(f,'52 overhang - 55 lip - 12 inset - 12 x 11 step',-30,
        [(0,0),(52,0),(52,-90),(23,-90),(23,-67),(12,-67),(12,-55),(0,-55)],202)
    color(f,frame_mat)

    ogauge,gauge=component(root,'10 Doorframe fit gauge PRINT FIRST - PRINT')
    side_polygon(gauge,'Stepped profile gauge - 0.6 mm clearance',225,
        [(52,.6),(-.6,.6),(-.6,-55.6),(11.4,-55.6),(11.4,-67.6),(23,-67.6),
         (23,-70),(9,-70),(9,-58),(-3,-58),(-3,3),(52,3)],8)
    color(gauge,shell);ogauge.isLightBulbOn=False

    app.activeDocument.name='Doorframe Camera - Pi4 + INIU + Waveshare G - mounted v3'
    d.computeAll()
    data={
        'source':'Ray confirmed sketch dimensions in conversation; IMG_5177.jpeg',
        'overhang_mm':52,'lip_height_mm':55,'first_inset_mm':12,
        'second_step_height_mm':12,'second_step_width_mm':11,
        'orientation':'Top surface z=0; room is negative Y; first face y=0; door boundary y=52. First inset spans y=0..12 at z=-55. Second underside spans y=12..23 at z=-67.',
        'orientation_physically_verified':False,
        'clamp_contact':'First 12 mm underside return at z=-55',
        'platform_bounds_mm':{'x':[-24,166],'y':[-42,50],'z':[2,14]},
        'case_translation_mm':[0,-40,10.2],
        'minimum_modeled_clearance_to_door_boundary_mm':2,
        'pad_stock_thickness_mm':3,'modeled_compressed_pad_thickness_mm':2.5,
        'jaw_guide_clearance_per_side_mm':.35,
        'physical_fit_and_load_tested':False,
        'parameters_note':'Dimensions recorded as user parameters; sketches contain explicit coordinates and must be regenerated if the frame dimensions change.'
    }
    with open(OUT+'/doorframe_measurements.json','w') as handle:json.dump(data,handle,indent=2)
    print(json.dumps({'document':app.activeDocument.name,'occurrences':root.occurrences.count,'mount':data}))
