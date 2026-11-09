from pathlib import Path
import adsk.core, adsk.fusion, sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_upright_v5 import side_shape
from build_enclosure import JOIN,CUT
def run(_context: str):
    a=adsk.core.Application.get();d=adsk.fusion.Design.cast(a.activeProduct)
    assert 'downward camera v5' in a.activeDocument.name
    outline=[(-11,-7),(45,-7),(45,-2),(-1,-2),(-6,7),(-6,66),(-11,66)]
    for name,cx in [('left',25),('right',189)]:
        c=next(o.component for o in d.rootComponent.occurrences if o.component.name=='03 '+name+' passive retaining saddle - PRINT')
        side_shape(c,'Flat print side A',cx-13,outline,3,JOIN)
        side_shape(c,'Flat print side B',cx+10,outline,3,JOIN)
        side_shape(c,'Full-width entry chamfer',cx-13.1,[(44.5,-2),(45,-2),(45,-2.5)],26.2,CUT)
    print('Made both saddles flat on either side for printing, with a 26 mm wide continuous load path.')
