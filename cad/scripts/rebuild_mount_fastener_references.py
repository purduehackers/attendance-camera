from pathlib import Path
import adsk.core, adsk.fusion, sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import add_mount_fastener_references

def run(_context: str):
    app=adsk.core.Application.get();d=adsk.fusion.Design.cast(app.activeProduct)
    assert 'mounted v3' in app.activeDocument.name
    for o in list(d.rootComponent.occurrences):
        if o.component.name=='REFERENCE - M4 mount fasteners - smooth envelopes':
            assert o.deleteMe()
    add_mount_fastener_references.run(_context)
