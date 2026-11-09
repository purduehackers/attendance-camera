import adsk.core, adsk.fusion

def run(_context: str):
 d=adsk.fusion.Design.cast(adsk.core.Application.get().activeProduct)
 r=d.rootComponent
 print('XY',r.xYConstructionPlane.geometry.normal.asArray())
 print('XZ',r.xZConstructionPlane.geometry.normal.asArray())
 print('YZ',r.yZConstructionPlane.geometry.normal.asArray())
