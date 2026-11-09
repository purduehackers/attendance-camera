from pathlib import Path
"""Preserve the official SVG outline as a recessed, printable cover feature."""
import adsk.core, adsk.fusion, sys, os, re, json, hashlib
import xml.etree.ElementTree as ET
ROOT=str(Path(__file__).resolve().parents[1]) + ''
OUT=ROOT+'/v8'
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_simple_v7 import xz_poly
from build_enclosure import CUT, appearance

def source_polygons(path):
    data=ET.parse(path).getroot().find('{http://www.w3.org/2000/svg}path').attrib['d']
    tokens=re.findall(r'[MHVZ]|-?\d+(?:\.\d+)?',data)
    result=[]; poly=[]; i=0; x=y=0
    while i<len(tokens):
        command=tokens[i];i+=1
        if command=='M':
            x,y=float(tokens[i]),float(tokens[i+1]);i+=2;poly=[(x,y)]
        elif command=='H':x=float(tokens[i]);i+=1;poly.append((x,y))
        elif command=='V':y=float(tokens[i]);i+=1;poly.append((x,y))
        elif command=='Z':result.append(poly);poly=[]
        else:raise ValueError('Unexpected SVG command '+command)
    assert len(result)==2
    return result

def run(_context: str):
    os.makedirs(OUT,exist_ok=True)
    a=adsk.core.Application.get()
    doc=a.importManager.importToNewDocument(a.importManager.createFusionArchiveImportOptions(ROOT+'/v7/doorframe-camera-simple-v7.f3d'))
    assert doc;doc.activate();doc.name='Doorframe Camera - covered ribbon and PH logo v8'
    d=adsk.fusion.Design.cast(a.activeProduct);r=d.rootComponent
    cover=next(o.component for o in r.occurrences if o.component.name.startswith('02 '))
    before=cover.bRepBodies.item(0).volume
    width=32.;scale=width/172.;bottom=76.;left=107-width/2
    polygons=source_polygons(ROOT+'/purdue-hackers-flat-source.svg')
    area=0
    for i,poly in enumerate(polygons):
        points=[(left+x*scale,bottom+(166-y)*scale) for x,y in poly]
        area+=abs(sum(p[0]*q[1]-q[0]*p[1] for p,q in zip(points,points[1:]+points[:1])))/2
        xz_poly(cover,'Purdue Hackers official flat logo recess '+str(i+1),points,-16.2,.6,CUT)
    removed=before-cover.bRepBodies.item(0).volume
    assert abs(removed-area*.6/1000)<1e-6,(removed,area)
    assert cover.bRepBodies.count==1 and cover.bRepBodies.item(0).isSolid
    # Colour denotes an optional paint fill, not a separate printed body.
    yellow=appearance(d,'Optional PH yellow paint fill',255,238,0)
    floors=[]
    for f in cover.bRepBodies.item(0).faces:
        bb=f.boundingBox
        if abs(bb.minPoint.y+1.56)<1e-6 and abs(bb.maxPoint.y+1.56)<1e-6:
            if bb.minPoint.x>=left/10-1e-6 and bb.maxPoint.x<=(left+width)/10+1e-6:
                if bb.minPoint.z>=bottom/10-1e-6 and bb.maxPoint.z<=(bottom+166*scale)/10+1e-6:
                    f.appearance=yellow;floors.append(f)
    assert len(floors)==2,len(floors)
    meta={'source':'https://www.purduehackers.com/ph.svg','source_sha256':hashlib.sha256(open(ROOT+'/purdue-hackers-flat-source.svg','rb').read()).hexdigest(),
          'style':'recessed official flat logo','width_mm':width,'height_mm':166*scale,'depth_mm':.6,'minimum_remaining_cover_mm':1.4,
          'x_bounds_mm':[left,left+width],'z_bounds_mm':[bottom,bottom+166*scale],
          'removed_volume_cm3':removed,'floor_faces':2,'colour_note':'Yellow is optional paint-fill visualization. STL remains a single-material solid; no extra part is required.'}
    with open(OUT+'/logo.json','w') as h:json.dump(meta,h,indent=2)
    print(json.dumps(meta))
