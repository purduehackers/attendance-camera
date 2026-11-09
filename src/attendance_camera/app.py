import base64
import binascii
from contextlib import asynccontextmanager
import csv
import hmac
import io
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .config import Calibration, Settings
from .runtime import Runtime
from .store import Store

STATIC = Path(__file__).parent / "static"


class Headcount(BaseModel):
    occupancy: int = Field(ge=0, le=10000, strict=True)


def create_app(settings: Settings, start_worker: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app):
        store = Store(settings.database)
        runtime = Runtime(settings, store)
        app.state.runtime, app.state.store = runtime, store
        if start_worker:
            runtime.start()
        try:
            yield
        finally:
            runtime.stop()
            store.close()

    app = FastAPI(title="Attendance camera", lifespan=lifespan, docs_url=None, redoc_url=None)
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=[*settings.allowed_hosts, settings.host]
    )

    @app.middleware("http")
    async def access(request: Request, call_next):
        if settings.token and request.url.path != "/healthz":
            try:
                scheme, encoded = request.headers.get("authorization", "").split(" ", 1)
                user, password = base64.b64decode(encoded, validate=True).decode().split(":", 1)
                valid = scheme.lower() == "basic" and hmac.compare_digest(
                    user.encode(), b"organizer"
                )
                valid &= hmac.compare_digest(password.encode(), settings.token.encode())
            except (ValueError, UnicodeDecodeError, binascii.Error):
                valid = False
            if not valid:
                return Response(
                    status_code=401, headers={"WWW-Authenticate": 'Basic realm="Attendance camera"'}
                )
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            origin = request.headers.get("origin")
            if origin and origin != f"{request.url.scheme}://{request.url.netloc}":
                return JSONResponse(
                    {"detail": "Cross-origin changes are not allowed."}, status_code=403
                )
            if request.headers.get("sec-fetch-site") == "cross-site":
                return JSONResponse(
                    {"detail": "Cross-site changes are not allowed."}, status_code=403
                )
        response = await call_next(request)
        response.headers.update(
            {
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer",
                "Content-Security-Policy": "default-src 'self'; img-src 'self' blob:; frame-ancestors 'none'; object-src 'none'",
            }
        )
        return response

    @app.get("/healthz")
    def health():
        return {"status": "ok"}

    @app.get("/readyz")
    def ready():
        state = app.state.runtime.status()
        ready = state["fresh"] and state["calibrated"]
        return JSONResponse(
            {"ready": ready, "state": state["state"]}, status_code=200 if ready else 503
        )

    @app.get("/")
    def index():
        return FileResponse(STATIC / "index.html")

    @app.get("/dashboard.js")
    def javascript():
        return FileResponse(STATIC / "dashboard.js", media_type="text/javascript")

    @app.get("/style.css")
    def stylesheet():
        return FileResponse(STATIC / "style.css", media_type="text/css")

    @app.get("/api/status")
    def status():
        return app.state.runtime.status()

    @app.get("/api/preview.jpg")
    def preview():
        runtime = app.state.runtime
        with runtime.lock:
            if not runtime.preview or not runtime.status()["fresh"]:
                raise HTTPException(503, "No fresh camera image available.")
            return Response(runtime.preview, media_type="image/jpeg")

    @app.put("/api/calibration")
    def calibration(value: Calibration):
        app.state.runtime.update_calibration(value)
        return value

    @app.post("/api/sessions", status_code=201)
    def start_session(value: Headcount):
        runtime = app.state.runtime
        with runtime.lock:
            state = runtime.status()
            if not state["fresh"] or not runtime.calibrated:
                raise HTTPException(409, "A fresh feed and saved calibration are required.")
            try:
                result = app.state.store.start(value.occupancy)
            except ValueError as exc:
                raise HTTPException(409, str(exc)) from None
            runtime.counter.reset()
            return result

    @app.post("/api/session/end", status_code=204)
    def end_session():
        with app.state.runtime.lock:
            app.state.store.end()
            app.state.runtime.counter.reset()
        return Response(status_code=204)

    @app.post("/api/session/reconcile")
    def reconcile(value: Headcount):
        with app.state.runtime.lock:
            try:
                result = app.state.store.reconcile(value.occupancy)
            except ValueError as exc:
                raise HTTPException(409, str(exc)) from None
            app.state.runtime.counter.reset()
            return result

    @app.get("/api/sessions")
    def sessions():
        return app.state.store.sessions()

    @app.get("/api/sessions/{session_id}/counts.csv")
    def export(session_id: str):
        # Rows contain only aggregate counters and minute timestamps.
        if not any(item["id"] == session_id for item in app.state.store.sessions()):
            raise HTTPException(404, "Session not found.")
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=["session_id", "minute", "incoming", "outgoing", "correction", "occupancy"],
        )
        writer.writeheader()
        writer.writerows(app.state.store.minutes(session_id))
        return Response(
            output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="attendance-counts.csv"'},
        )

    return app
