import adsk.core, adsk.fusion, json
def run(_context: str):
    a=adsk.core.Application.get();d=adsk.fusion.Design.cast(a.activeProduct)
    def point(p):return [round(p.x*10,4),round(p.y*10,4),round(p.z*10,4)]
    def bounds(b):return [point(b.minPoint),point(b.maxPoint)]
    print(json.dumps([{'name':o.component.name,'transform':list(o.transform2.asArray()),'world_bounds':bounds(o.boundingBox),'local_bodies':[{'name':b.name,'bounds':bounds(b.boundingBox),'volume':b.volume} for b in o.component.bRepBodies]} for o in d.rootComponent.occurrences]))
