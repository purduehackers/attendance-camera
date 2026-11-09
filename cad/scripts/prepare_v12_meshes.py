"""Orient only fresh v12 Fusion STLs. Mesh verification is read-only afterward."""
from pathlib import Path
import collections,json,math,struct,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from check_artifacts import check_mesh
base=ROOT/'cad/v12';reports=[]
for path in sorted((base/'stl').glob('*.stl')):
    data=path.read_bytes();assert not data.startswith(b'Attendance camera v12'), 'Already oriented; use fresh Fusion exports'
    count=struct.unpack_from('<I',data,80)[0];assert len(data)==84+50*count
    triangles=[];key=path.name[:2]
    for i in range(count):
        face=struct.unpack_from('<12fH',data,84+50*i)
        vs=[tuple(face[j:j+3]) for j in (3,6,9)]
        if key == '01':vs=[(x,z,-y) for x,y,z in vs]
        elif key=='02':vs=[(x,-z,y) for x,y,z in vs]
        elif key in ('04','05'):vs=[(y,z,x) for x,y,z in vs]
        elif key in ('03','06','07'):vs=[(x,-y,-z) for x,y,z in vs]
        else:raise ValueError(key)
        triangles.append(vs)
    low=[min(v[j] for tri in triangles for v in tri) for j in range(3)]
    high=[max(v[j] for tri in triangles for v in tri) for j in range(3)]
    result=bytearray(b'Attendance camera v12 - mm - oriented installed part'.ljust(80,b' '))+struct.pack('<I',count)
    overhang_area=0
    for tri in triangles:
        a,b,c=[tuple(v[j]-low[j] for j in range(3)) for v in tri]
        u=[b[j]-a[j] for j in range(3)];v=[c[j]-a[j] for j in range(3)]
        normal=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
        length=math.sqrt(sum(n*n for n in normal));assert length>0
        norm=[n/length for n in normal]
        if norm[2]<-math.sqrt(.5)-.001 and max(a[2],b[2],c[2])>.21:overhang_area+=length/2
        result+=struct.pack('<12fH',*norm,*a,*b,*c,0)
    path.write_bytes(result);check_mesh(path)
    reports.append({'file':path.name,'triangles':count,'size_mm':[round(high[j]-low[j],3) for j in range(3)],
                    'connected_components':1,'closed_manifold':True,'consistent_winding':True,
                    'downward_surface_area_over_45deg_mm2':round(overhang_area,2),
                    'overhang_metric_note':'Geometric area only, includes printable bridges and holes; not slicer support volume.'})
(base/'mesh-validation.json').write_text(json.dumps(reports,indent=2)+'\n')
print(json.dumps(reports,indent=2))
