# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.28,<1", "websockets>=15,<17", "redis>=6,<8"]
# ///
"""Exercise real Redis + two Rust relay processes + bridge, without camera footage.

Run: cargo build --bins && uv run scripts/test_transport.py
Requires redis-server on PATH. Creates isolated processes/ports and deletes test state.
"""
import asyncio
import base64
from contextlib import ExitStack
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import socket
import struct
import subprocess
import tempfile
import threading
import time
import uuid

import httpx
import redis.asyncio as redis
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed, InvalidStatus


def port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class Backend(BaseHTTPRequestHandler):
    mutations = 0

    def log_message(self, *_):
        pass

    def do_GET(self):
        body = json.dumps({"source": "fixture", "path": self.path}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        Backend.mutations += 1
        self.do_GET()


async def wait_ready(http, url):
    for _ in range(100):
        try:
            if (await http.get(url + "/healthz")).status_code == 200:
                return
        except httpx.TransportError:
            pass
        await asyncio.sleep(0.05)
    raise AssertionError(f"Service failed to start: {url}")


async def check(stack, directory):
    redis_port, bridge_port, backend_port, a_port, b_port = [port() for _ in range(5)]
    namespace = "attendance:test-" + uuid.uuid4().hex
    token, camera = "organizer-test-" + "x" * 32, "camera-test-" + "y" * 32
    processes = []

    def spawn(args, env=None):
        log = stack.enter_context(open(Path(directory) / f"process-{len(processes)}.log", "w+"))
        process = subprocess.Popen(args, env=env, stdout=log, stderr=log)
        processes.append(process)

        def cleanup():
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            if process.returncode not in (0, -15):
                log.seek(0)
                print(log.read()[-2000:])
        stack.callback(cleanup)

    spawn([shutil.which("redis-server"), "--bind", "127.0.0.1", "--port", str(redis_port),
           "--save", "", "--appendonly", "no", "--dir", directory])
    backend = ThreadingHTTPServer(("127.0.0.1", backend_port), Backend)
    threading.Thread(target=backend.serve_forever, daemon=True).start()
    stack.callback(backend.server_close)
    stack.callback(backend.shutdown)
    env = {**os.environ, "REDIS_URL": f"redis://127.0.0.1:{redis_port}",
           "REDIS_NAMESPACE": namespace, "ATTENDANCE_TOKEN": token, "CAMERA_TOKEN": camera,
           "BRIDGE_BIND": f"127.0.0.1:{bridge_port}",
           "ATTENDANCE_BACKEND": f"http://127.0.0.1:{backend_port}",
           "RELAY_SESSION_SECONDS": "3", "PUBLIC_ORIGIN": f"http://127.0.0.1:{a_port}"}
    await asyncio.sleep(0.15)
    spawn(["target/debug/attendance-bridge"], env)
    for number in (a_port, b_port):
        spawn(["target/debug/relay"], {**env, "RELAY_BIND": f"127.0.0.1:{number}"})
    a, b, bridge = [f"http://127.0.0.1:{p}" for p in (a_port, b_port, bridge_port)]
    async with httpx.AsyncClient(timeout=5) as http:
        await asyncio.gather(*(wait_ready(http, url) for url in (a, b, bridge)))
        auth = ("organizer", token)
        assert (await http.get(a + "/api/status")).status_code == 401
        assert (await http.get(a + "/", auth=auth)).status_code == 200
        for endpoint in (a, b):
            response = await http.get(endpoint + "/api/status", auth=auth)
            assert response.status_code == 200 and response.json()["source"] == "fixture"
            assert response.headers["cache-control"] == "no-store"
        assert (await http.post(a + "/api/session/end", auth=auth, headers={"Origin": "https://evil.example"})).status_code == 403
        assert (await http.post(a + "/api/session/end", auth=auth, content=b"x" * 17_000)).status_code == 413
        assert (await http.get(a + "/api/status?url=http://example.com", auth=auth)).status_code == 404
        try:
            async with connect(a.replace("http", "ws") + "/ingest", additional_headers={"Authorization": "Bearer invalid"}):
                raise AssertionError("Unauthenticated publisher accepted")
        except InvalidStatus as exc:
            assert exc.response.status_code == 401
        print("PASS: private dashboard, two relay instances, CSRF, body limits, publisher authentication")

        frames = asyncio.Queue()

        async def consume():
            async with http.stream("GET", bridge + "/cam.ts") as response:
                async for chunk in response.aiter_bytes():
                    await frames.put(chunk)
            await frames.put(None)

        reader = asyncio.create_task(consume())
        stream = uuid.uuid4()
        payload = b"\x47" + b"fixture" * 26 + b"12345"

        def packet(sequence):
            return b"PHC1" + stream.bytes + struct.pack(">QQ", sequence, int(time.time() * 1000)) + payload

        headers = {"Authorization": "Bearer " + camera}
        await asyncio.sleep(0.2)
        async with connect(a.replace("http", "ws") + "/ingest", additional_headers=headers) as ws:
            await ws.send(packet(1))
            assert json.loads(await ws.recv())["sequence"] == 1
            assert await asyncio.wait_for(frames.get(), 2) == payload
        # Resume on a different relay instance. Duplicate packets are acknowledged,
        # but never sent twice to the decoder; the HTTP stream stays open.
        async with connect(b.replace("http", "ws") + "/ingest", additional_headers=headers) as ws:
            await ws.send(packet(1))
            assert json.loads(await ws.recv())["sequence"] == 1
            await ws.send(packet(2))
            assert json.loads(await ws.recv())["sequence"] == 2
            assert await asyncio.wait_for(frames.get(), 2) == payload
            await ws.send(packet(4))
            assert json.loads(await ws.recv())["sequence"] == 4
            assert await asyncio.wait_for(frames.get(), 2) is None
            try:
                await asyncio.wait_for(ws.recv(), 5)
                raise AssertionError("Expected periodic reconnect")
            except ConnectionClosed:
                pass
        await reader
        print("PASS: cross-instance reconnect, ordered delivery, duplicate suppression, gap reset, socket rotation")

    broker = redis.from_url(env["REDIS_URL"])
    request = {"id": str(uuid.uuid4()), "method": "POST", "path": "/api/session/end",
               "created": int(time.time() * 1000), "body": base64.b64encode(b"{}").decode()}
    async with broker.pubsub() as replies:
        await replies.subscribe(f"{namespace}:reply:{request['id']}")
        for _ in range(2):
            await broker.publish(f"{namespace}:requests", json.dumps(request))
            async with asyncio.timeout(5):
                async for message in replies.listen():
                    if message["type"] == "message":
                        assert json.loads(message["data"])["status"] == 200
                        break
    assert Backend.mutations == 1
    assert await broker.dbsize() == 0, "Video/control transport must never create Redis keys"
    await broker.aclose()
    print("PASS: repeated command executes once; Redis contains no stored footage or RPC records")


if __name__ == "__main__":
    with ExitStack() as stack, tempfile.TemporaryDirectory(prefix="attendance-transport-") as directory:
        asyncio.run(check(stack, directory))
