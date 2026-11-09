from pathlib import Path
"""Smooth nominal M4 hardware envelopes; threads are deliberately not modeled."""
import adsk.core, adsk.fusion, math, sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_enclosure import component, circles, sketch, extrude, color, mmpt, NEW, JOIN, CUT

def nut(comp,name,x,y,z):
    s=sketch(comp,name+' hexagon',offset=z);radius=7/math.sqrt(3)
    ps=[mmpt(x+radius*math.cos(i*math.pi/3),y+radius*math.sin(i*math.pi/3)) for i in range(6)]
    for a,b in zip(ps,ps[1:]+ps[:1]):s.sketchCurves.sketchLines.addByTwoPoints(a,b)
    extrude(comp,s,3.2,NEW,name)
    circles(comp,name+' bore',[(x,y)],4.2,z-.1,3.4,CUT)

def run(_context: str):
    app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct);r=d.rootComponent
    assert 'mounted v3' in app.activeDocument.name
    assert not any('M4 mount fasteners' in o.component.name for o in r.occurrences)
    o,c=component(r,'REFERENCE - M4 mount fasteners - smooth envelopes')
    for side,cx in [('left',-10),('right',152)]:
        nut(c,side+' clamp nut',cx,-24,-62)
        circles(c,side+' washer',[(cx,-24)],9,8,.8,NEW)
        circles(c,side+' washer bore',[(cx,-24)],4.2,7.9,1,CUT)
        circles(c,side+' M4 x 80 shank',[(cx,-24)],4,-71.2,80,NEW)
        circles(c,side+' clamp screw head',[(cx,-24)],7,8.8,4,JOIN)
    for index,y in enumerate([-14,22]):
        nut(c,f'Case nut {index}',132,y,3)
        circles(c,f'Case M4 x 10 shank {index}',[(132,y)],4,2.6,10,NEW)
        circles(c,f'Case screw head {index}',[(132,y)],7,12.6,2.8,JOIN)
    color(c,d.appearances.itemByName('Reference connectors'))
    print('Added reference M4 screws, nuts, and clamp washers. No modeled threads.')
