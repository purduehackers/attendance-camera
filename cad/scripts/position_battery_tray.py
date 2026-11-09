import adsk.core, adsk.fusion
def run(_context: str):
    a=adsk.core.Application.get();d=adsk.fusion.Design.cast(a.activeProduct)
    assert 'mounted v3' in a.activeDocument.name
    o=next(o for o in d.rootComponent.occurrences if o.component.name=='01 Battery tray - PRINT')
    if o.isGrounded:o.isGrounded=False
    if o.isGroundToParent:o.isGroundToParent=False
    m=o.transform2;m.translation=adsk.core.Vector3D.create(0,-4,1.02);o.transform2=m
    if d.snapshots.hasPendingSnapshot:d.snapshots.add()
    d.computeAll()
    assert abs(o.transform2.translation.y+4)<.00001
    print('Moved the previously grounded battery tray to the mount assembly position.')
