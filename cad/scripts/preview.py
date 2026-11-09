from pathlib import Path
import adsk.core, adsk.fusion

def run(_context: str):
 app=adsk.core.Application.get()
 c=app.activeViewport.camera
 c.viewOrientation=adsk.core.ViewOrientations.IsoTopRightViewOrientation
 c.isFitView=True;c.isSmoothTransition=False
 app.activeViewport.camera=c
 print(app.activeViewport.saveAsImageFile(str(Path(__file__).resolve().parents[1]) + '/prototype-preview.png',1600,1000))
