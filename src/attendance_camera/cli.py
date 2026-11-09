import argparse
import hashlib
import os
from pathlib import Path
import tempfile
import urllib.request

MODEL_BASE = "https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0"
MODEL_HASHES = {
    "tiny": "427cc366d34e27ff7a03e2899b5e3671425c262ea2291f88bb942bc1cc70b0f7",
    "nano": "c789161ed43c8269fcd4e67c67eeeb4e80c622da2eb296a20bc6007bd18a0b7d",
    "s": "c5c2d13e59ae883e6af3b45daea64af4833a4951c92d116ec270d9ddbe998063",
}


def fetch_model(target: Path, variant: str = "tiny"):
    checksum = MODEL_HASHES[variant]
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == checksum:
        print("Model already present and verified.")
        return
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as output:
            temporary = Path(output.name)
            with urllib.request.urlopen(
                f"{MODEL_BASE}/yolox_{variant}.onnx", timeout=60
            ) as response:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
        if hashlib.sha256(temporary.read_bytes()).hexdigest() != checksum:
            raise RuntimeError("Model checksum mismatch; the downloaded file was not installed.")
        temporary.replace(target)
        print(f"Verified model installed at {target}")
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Local camera occupancy estimates")
    sub = parser.add_subparsers(dest="command", required=True)
    server = sub.add_parser("serve")
    server.add_argument("--config", type=Path)
    server.add_argument(
        "--demo", action="store_true", help="Synthetic rectangles; separate demo database"
    )
    model = sub.add_parser("fetch-model")
    model.add_argument("--variant", choices=MODEL_HASHES, default="tiny")
    model.add_argument("--output", type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    if args.command == "fetch-model":
        fetch_model(args.output or Path(f"local/models/yolox_{args.variant}.onnx"), args.variant)
        return
    from .app import create_app
    from .config import load_settings
    import uvicorn

    settings = load_settings(args.config, args.demo)
    uvicorn.run(
        create_app(settings),
        host=settings.host,
        port=settings.port,
        workers=1,
        access_log=False,
        proxy_headers=False,
    )


if __name__ == "__main__":
    main()
