import adsk.core, adsk.fusion, json

def run(_context: str):
 d=adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
 for o in d.rootComponent.occurrences:
  c=o.component
  print(c.name, 'bodies',c.bRepBodies.count,'sketches',c.sketches.count)
  for b in c.bRepBodies:
   bb=b.boundingBox
   print(b.name, 'solid',b.isSolid,'volume_cm3',b.volume,'bounds_cm',bb.minPoint.asArray(),bb.maxPoint.asArray())
  if c.sketches.count:
   s=c.sketches.item(c.sketches.count-1)
   print('LASTSKETCH',s.name,'origin',s.sketchToModelSpace(adsk.core.Point3D.create(0,0,0)).asArray(),'normal_point',s.sketchToModelSpace(adsk.core.Point3D.create(0,0,1)).asArray())
 print('health',[(d.timeline.item(i).name,d.timeline.item(i).errorOrWarningMessage) for i in range(d.timeline.count) if d.timeline.item(i).healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState])
