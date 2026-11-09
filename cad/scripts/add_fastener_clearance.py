from pathlib import Path
import adsk.core, adsk.fusion, sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_enclosure import circles, CUT

def run(_context: str):
    d=adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    w=next(o.component for o in d.rootComponent.occurrences if o.component.name.startswith('06 '))
    circles(w,'Camera M2 nut and screw-tip relief',[(8.5,14.5),(29.5,14.5)],5.2,0,-2,CUT)
    circles(w,'Cap fastener head relief',[(3.5,3.5),(34.5,3.5)],5.5,0,-3.2,CUT)
    print('Added clearance for the rear camera nuts, screw tips, and cap screw heads.')
