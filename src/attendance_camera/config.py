from __future__ import annotations

import ipaddress
import os
from pathlib import Path
import tomllib
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Calibration(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    x_min: float = Field(0.1, ge=0, le=1)
    y_min: float = Field(0.1, ge=0, le=1)
    x_max: float = Field(0.9, ge=0, le=1)
    y_max: float = Field(0.9, ge=0, le=1)
    axis: Literal["x", "y"] = "y"
    position: float = Field(0.5, ge=0.1, le=0.9)
    inside: Literal["positive", "negative"] = "positive"
    deadband: float = Field(0.04, ge=0.005, le=0.15)
    confirmation_frames: int = Field(2, ge=1, le=10)
    max_gap_seconds: float = Field(1.5, ge=0.2, le=5)

    @model_validator(mode="after")
    def valid_geometry(self):
        if self.x_max - self.x_min < 0.1 or self.y_max - self.y_min < 0.1:
            raise ValueError("The counting region must span at least 10% of each image dimension.")
        if self.deadband >= min(self.position, 1 - self.position):
            raise ValueError("The deadband must leave room on both sides of the counting line.")
        return self


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    host: str = "127.0.0.1"
    port: int = Field(8000, ge=1, le=65535)
    camera_url: str = Field("", repr=False)
    database: Path = Path("local/attendance.sqlite3")
    model_path: Path = Path("local/models/yolox_tiny.onnx")
    token: str = Field("", repr=False)
    allowed_hosts: list[str] = Field(default_factory=lambda: ["localhost", "127.0.0.1", "[::1]"])
    demo: bool = False
    fps: float = Field(6, ge=2, le=30)
    confidence: float = Field(0.4, ge=0.15, le=0.9)
    inference_threads: int = Field(3, ge=1, le=32)
    calibration: Calibration = Field(default_factory=Calibration)

    @model_validator(mode="after")
    def validate_network(self):
        address = ipaddress.ip_address(self.host)
        if not address.is_loopback and len(self.token) < 24:
            raise ValueError(
                "A non-loopback listener requires ATTENDANCE_TOKEN of at least 24 characters."
            )
        if self.camera_url:
            source = urlsplit(self.camera_url)
            if source.scheme not in ("rtsp", "rtsps") or not source.hostname:
                raise ValueError("camera_url must be an RTSP camera URL.")
        return self


def load_settings(path: Path | None, demo: bool = False) -> Settings:
    values = tomllib.loads(path.read_text()) if path else {}
    for env, key in (
        ("ATTENDANCE_TOKEN", "token"),
        ("ATTENDANCE_CAMERA_URL", "camera_url"),
        ("ATTENDANCE_HOST", "host"),
    ):
        if env in os.environ:
            values[key] = os.environ[env]
    if demo:
        values.update(demo=True, database="local/demo.sqlite3")
    return Settings.model_validate(values)
