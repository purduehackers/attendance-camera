from pathlib import Path
"""PETG prototype revision: printable logo, stronger hooks, rounded roots."""
import adsk.core, adsk.fusion, os, sys, json
ROOT=str(Path(__file__).resolve().parents[1]) + ''
OUT=ROOT+'/v9'
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_enclosure import box, JOIN, col, VI
from build_simple_v7 import xz_poly

def fillet_at(c,name,points,radius,width):
    edges=[]
    for yy,zz in points:
        found=[]
        for e in c.bRepBodies.item(0).edges:
            bb=e.boundingBox;lo=bb.minPoint;hi=bb.maxPoint
            if abs((hi.x-lo.x)*10-width)<1e-4 and abs(hi.y-lo.y)<1e-6 and abs(hi.z-lo.z)<1e-6:
                if abs(lo.y*10-yy)<1e-4 and abs(lo.z*10-zz)<1e-4:found.append(e)
        assert found,(name,yy,zz)
        edges+=found
    fi=c.features.filletFeatures.createInput()
    fi.edgeSetInputs.addConstantRadiusEdgeSet(col(edges),VI(f'{radius} mm'),False)
    f=c.features.filletFeatures.add(fi);f.name=name
    print(name, len(edges), 'edges', radius,'mm')

def run(_context: str):
    os.makedirs(OUT,exist_ok=True)
    a=adsk.core.Application.get()
    doc=a.importManager.importToNewDocument(a.importManager.createFusionArchiveImportOptions(ROOT+'/v8/doorframe-camera-simple-v8.f3d'))
    assert doc;doc.activate();doc.name='Doorframe Camera - PETG reinforced PH v9'
    d=adsk.fusion.Design.cast(a.activeProduct);r=d.rootComponent
    c=next(o.component for o in r.occurrences if o.component.name.startswith('01 '))
    p=next(o.component for o in r.occurrences if o.component.name.startswith('02 '))
    # The source SVG has two pockets meeting at one vertex: four mesh faces
    # would share that vertical edge. Fill a tiny triangle on the square corner.
    x=91+57.333*32/172;z=76+(166-110.667)*32/172
    before=p.bRepBodies.item(0).volume
    xz_poly(p,'Logo corner separation for manifold print',[(x,z),(x-.4,z),(x,z-.4)],-16.2,.6,JOIN)
    assert abs(p.bRepBodies.item(0).volume-before-.000048)<1e-7
    logo=json.load(open(ROOT+'/v8/logo.json'))
    logo['manufacturing_relief']='0.4 mm corner chamfer at the point contact; 0.283 mm minimum separation between recessed regions.'
    logo['removed_volume_cm3']-=.000048
    with open(OUT+'/logo.json','w') as h:json.dump(logo,h,indent=2)
    for cx in (25,189):
        box(c,'7 mm retaining hook thickness '+str(cx),cx-13,-11,cx+13,45,-9,2,JOIN)
    print('Created v9; logo point contact removed; hook toe thickness 7 mm, 6.5 mm under pad pockets.')

def round_roots(_context: str):
    d=adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
    c=next(o.component for o in d.rootComponent.occurrences if o.component.name.startswith('01 '))
    p=next(o.component for o in d.rootComponent.occurrences if o.component.name.startswith('02 '))
    fillet_at(c,'Rounded retaining arm upper roots',[(-11,65),(-6,65)],1.5,26)
    fillet_at(c,'Rounded retaining arm inner knees',[(-6,7),(-1,-2)],1.5,26)
    fillet_at(c,'Rounded retaining arm outside heels',[(-11,-9)],2,26)
    fillet_at(p,'Lower service cover clip root relief',[(-14.2,71.75),(-14.2,72.95)],.6,5)
    fillet_at(p,'Upper service cover clip root relief',[(-14.2,163.45),(-14.2,164.25)],.4,5)
    for cc in (c,p):assert cc.bRepBodies.count==1 and cc.bRepBodies.item(0).isSolid
