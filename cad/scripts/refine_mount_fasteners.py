from pathlib import Path
import adsk.core, adsk.fusion, sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_enclosure import col

def run(_context: str):
    app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct)
    assert 'mounted v3' in app.activeDocument.name
    shift=adsk.core.Matrix3D.create();shift.translation=adsk.core.Vector3D.create(0,-.5,0)
    for o in d.rootComponent.occurrences:
        c=o.component
        if c.name.startswith('07 '):
            s=c.sketches.itemByName('M4 long clamp bolt clearance layout')
            assert s.move(col(list(s.sketchCurves)),shift)
        if c.name.startswith('09 '):
            s=c.sketches.itemByName('Lower clamping jaw outline')
            points=[p for p in s.sketchPoints if abs(p.geometry.y+2.4)<.0001]
            assert len(points)==2,len(points)
            assert s.move(col(points),shift)
            for name in ['M4 long bolt clearance layout','Captive M4 nut outline']:
                s=c.sketches.itemByName(name)
                assert s.move(col(list(s.sketchCurves)),shift)
    d.computeAll()
    print('Moved clamp bolts 5 mm forward to separate them from the case captive-nut channels.')
