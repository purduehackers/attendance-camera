"""Create a print-only delivery ZIP and separate plain-text operator notes."""
import argparse,hashlib,json,zipfile
from pathlib import Path

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=Path.home()/'Downloads')
    args=parser.parse_args();base=Path(__file__).resolve().parents[1]/'v12'
    manifest=json.loads((base/'manifest-sha256.json').read_text())
    parts=json.loads((base/'validation.json').read_text())['parts']
    archive=args.output/'attendance-camera-v12-print.zip';args.output.mkdir(parents=True,exist_ok=True)
    expected={}
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for part in parts:
            source=base/'stl'/part['file'];data=source.read_bytes()
            assert hashlib.sha256(data).hexdigest()==manifest[str(source.relative_to(base))]
            for i in range(part['quantity']):
                stem=source.stem.replace('-print-two','')
                name=stem+(f'-{i+1}' if part['quantity']>1 else '')+'.stl'
                assert name not in expected;z.writestr(name,data);expected[name]=hashlib.sha256(data).hexdigest()
    with zipfile.ZipFile(archive) as z:
        assert len(z.namelist())==10 and set(z.namelist())==set(expected) and z.testzip() is None
        for name,digest in expected.items():assert hashlib.sha256(z.read(name)).hexdigest()==digest
    notes=args.output/'attendance-camera-v12-print-notes.txt'
    notes.write_text((base/'PRINT-ADMIN-NOTES.md').read_text().split('\n',2)[2])
    print(f'{archive}\n{notes}\nVerified: ten installed STL files, no coupons or other test pieces.')

if __name__=='__main__':main()
