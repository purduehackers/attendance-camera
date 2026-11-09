import threading
import time

import cv2
import numpy as np

from .config import Calibration, Settings
from .counting import CrossingCounter
from .store import Store


class Runtime:
    def __init__(self, settings: Settings, store: Store):
        self.settings, self.store = settings, store
        self.lock = threading.RLock()
        saved = store.get_setting("calibration")
        self.calibration = Calibration.model_validate(saved) if saved else settings.calibration
        self.calibrated = bool(saved) or settings.demo
        self.counter = CrossingCounter(self.calibration)
        self.stop_event = threading.Event()
        self.thread = None
        self.state = "demo" if settings.demo else "starting"
        self.detail = ""
        self.last_frame = None
        self.preview = None
        self.processed = 0
        self.inference_ms = None
        self.store.mark_gap()

    def start(self):
        self.thread = threading.Thread(target=self._run, name="attendance-worker", daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=20)

    def gap(self, detail):
        with self.lock:
            if self.state != "disconnected":
                self.store.mark_gap()
            self.counter.reset()
            self.preview = None
            self.state, self.detail = "disconnected", detail

    def update_calibration(self, value: Calibration):
        with self.lock:
            self.store.set_setting("calibration", value.model_dump())
            self.calibration, self.calibrated = value, True
            self.counter = CrossingCounter(value)
            self.store.mark_gap()

    def status(self):
        with self.lock:
            age = time.monotonic() - self.last_frame if self.last_frame is not None else None
            fresh = self.state in ("running", "demo") and age is not None and age < 3
            return {
                "mode": "demo" if self.settings.demo else "camera",
                "state": self.state,
                "detail": self.detail,
                "fresh": fresh,
                "frame_age_seconds": age,
                "processed_frames": self.processed,
                "inference_ms": self.inference_ms,
                "calibrated": self.calibrated,
                "calibration": self.calibration.model_dump(),
                "session": self.store.active(),
            }

    def process(self, centers, frame, captured_at, inference_ms=0):
        with self.lock:
            if (
                self.last_frame is not None
                and captured_at - self.last_frame > self.calibration.max_gap_seconds
            ):
                self.counter.reset()
                self.store.mark_gap()
            counts = self.counter.update(centers, captured_at)
            if self.calibrated:
                self.store.record(*counts)
            self.last_frame = captured_at
            self.processed += 1
            self.inference_ms = round(inference_ms, 1)
            self.state, self.detail = ("demo" if self.settings.demo else "running"), ""
            self.preview = self._preview(frame, centers)

    def _preview(self, frame, centers):
        # A single annotated JPEG stays in RAM and is replaced every frame.
        height, width = frame.shape[:2]
        image = cv2.resize(frame, (800, max(1, round(height * 800 / width))))
        h, w = image.shape[:2]
        c = self.calibration
        a, b = (int(c.x_min * w), int(c.y_min * h)), (int(c.x_max * w), int(c.y_max * h))
        cv2.rectangle(image, a, b, (160, 160, 160), 1)
        if c.axis == "y":
            line = int((c.y_min + c.position * (c.y_max - c.y_min)) * h)
            cv2.line(image, (a[0], line), (b[0], line), (0, 210, 255), 2)
        else:
            line = int((c.x_min + c.position * (c.x_max - c.x_min)) * w)
            cv2.line(image, (line, a[1]), (line, b[1]), (0, 210, 255), 2)
        for _, x, y in centers:
            cv2.circle(image, (int(x * w), int(y * h)), 5, (90, 235, 130), -1)
        ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 70])
        return encoded.tobytes() if ok else None

    def _run(self):
        if self.settings.demo:
            self._demo()
            return
        if not self.settings.camera_url:
            self.state, self.detail = "unconfigured", "Set ATTENDANCE_CAMERA_URL to connect the Pi."
            return
        if not self.settings.model_path.is_file():
            self.state, self.detail = "model_missing", "Run attendance-server fetch-model first."
            return
        capture = None
        try:
            from .capture import LatestFrame
            from .vision import PersonDetector, make_tracker

            detector = PersonDetector(self.settings.model_path, self.settings.inference_threads)
            tracker = make_tracker(self.settings.fps, self.settings.confidence)
            capture = LatestFrame(self.settings.camera_url)
            capture.start()
            previous_sequence = previous_generation = -1
            while not self.stop_event.is_set():
                started = time.monotonic()
                packet, error = capture.snapshot()
                if packet is None or started - packet[2] > 3:
                    self.gap(error or "camera frames are stale")
                    previous_generation = -1
                    self.stop_event.wait(0.1)
                    continue
                sequence, generation, captured_at, frame = packet
                if sequence == previous_sequence:
                    self.stop_event.wait(0.01)
                    continue
                if generation != previous_generation:
                    tracker.reset()
                    with self.lock:
                        self.counter.reset()
                        if previous_sequence != -1:
                            self.store.mark_gap()
                previous_sequence, previous_generation = sequence, generation
                detections = detector.detect(frame)
                tracked = tracker.update(detections, timestamp=captured_at)
                height, width = frame.shape[:2]
                centers = [
                    (
                        int(key),
                        float((box[0] + box[2]) / 2 / width),
                        float((box[1] + box[3]) / 2 / height),
                    )
                    for key, box in zip(tracked.tracker_id, tracked.xyxy)
                    if key >= 0
                ]
                if time.monotonic() - captured_at > 3:
                    self.gap("inference is too slow; newest frame is stale")
                else:
                    self.process(centers, frame, captured_at, (time.monotonic() - started) * 1000)
                self.stop_event.wait(max(0, 1 / self.settings.fps - (time.monotonic() - started)))
        except Exception as exc:
            self.gap(f"processing stopped ({type(exc).__name__}); check model and configuration")
            self.state = "error"
        finally:
            if capture:
                capture.stop()

    def _demo(self):
        # Synthetic rectangles only: no camera, model, real images or network access.
        index = 0
        while not self.stop_event.is_set():
            frame = np.full((450, 800, 3), 30, dtype=np.uint8)
            step = index % 120
            y = 0.15 + 0.7 * min(step, 120 - step) / 60
            centers = [(index // 120 + 1, 0.5, y)]
            cv2.rectangle(
                frame, (375, int(y * 450) - 20), (425, int(y * 450) + 20), (80, 140, 190), -1
            )
            cv2.putText(
                frame, "SYNTHETIC DEMO", (25, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (220, 220, 220), 1
            )
            self.process(centers, frame, time.monotonic())
            index += 1
            self.stop_event.wait(1 / self.settings.fps)
