"""Run immediately after Fusion export: orient STLs and check closed mesh edges."""
from pathlib import Path
import struct, collections, math, json

base=Path(__file__).parents[1]/'v10'
reports=[]
for p in sorted((base/'stl').glob('*.stl')):
    data=p.read_bytes()
    if data.startswith(b'Doorframe camera PROTOTYPE'):
        raise RuntimeError('Already oriented: run only on fresh Fusion exports')
    n=struct.unpack_from('<I',data,80)[0]
    assert len(data)==84+n*50
    tris=[]
    for i in range(n):
        f=struct.unpack_from('<12fH',data,84+i*50)
        vs=[tuple(f[3+j*3:6+j*3]) for j in range(3)]
        if p.name.startswith('01-'):vs=[(y,z,x) for x,y,z in vs]
        if p.name.startswith('02-'):vs=[(x,-z,y) for x,y,z in vs]
        if p.name.startswith('03-'):vs=[(x,z,-y) for x,y,z in vs]
        if p.name.startswith(('07-','08-')):vs=[(y,z,x) for x,y,z in vs]
        tris.append(vs)
    mins=[min(v[j] for t in tris for v in t) for j in range(3)]
    maxs=[max(v[j] for t in tris for v in t) for j in range(3)]
    out=bytearray(b'Doorframe camera PROTOTYPE - mm - oriented for print'.ljust(80,b' '))
    out+=struct.pack('<I',n)
    edges=collections.Counter();vol=0
    for t in tris:
        t=[tuple(v[j]-mins[j] for j in range(3)) for v in t]
        a,b,c=t;u=[b[j]-a[j] for j in range(3)];v=[c[j]-a[j] for j in range(3)]
        norm=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
        length=math.sqrt(sum(x*x for x in norm))
        normal=tuple(x/length for x in norm) if length else (0,0,0)
        out+=struct.pack('<12fH',*normal,*a,*b,*c,0)
        key=[tuple(round(x,5) for x in v) for v in t]
        for i in range(3):edges[tuple(sorted((key[i],key[(i+1)%3])))]+=1
        vol+=(a[0]*(b[1]*c[2]-b[2]*c[1])-a[1]*(b[0]*c[2]-b[2]*c[0])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6
    report={'file':p.name,'triangles':n,'size_mm':[round(maxs[j]-mins[j],3) for j in range(3)],'nonmanifold_edges':sum(v!=2 for v in edges.values()),'mesh_volume_cm3':round(vol/1000,4)}
    assert report['nonmanifold_edges']==0,report
    assert vol>0,report
    p.write_bytes(out);reports.append(report)
(base/'mesh-validation.json').write_text(json.dumps(reports,indent=2))
print(json.dumps(reports,indent=2))
