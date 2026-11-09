"""Drain RTSP or the local MPEG-TS bridge into one current in-memory frame."""

import threading
import time

import av


class LatestFrame:
    def __init__(self, url: str):
        self.url = url
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._read, name="camera-capture", daemon=True)
        self.latest = None
        self.sequence = 0
        self.generation = 0
        self.error = "connecting"

    def start(self):
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        self.thread.join(timeout=12)

    def snapshot(self):
        with self.lock:
            return self.latest, self.error

    def _read(self):
        while not self.stop_event.is_set():
            try:
                options = {"fflags": "nobuffer", "max_delay": "500000"}
                if self.url.startswith(("rtsp://", "rtsps://")):
                    options["rtsp_transport"] = "tcp"
                with av.open(
                    self.url,
                    timeout=(5, 5),
                    options=options,
                ) as source:
                    with self.lock:
                        self.generation += 1
                    for frame in source.decode(video=0):
                        if self.stop_event.is_set():
                            break
                        image = frame.to_ndarray(format="bgr24")
                        with self.lock:
                            self.sequence += 1
                            self.latest = (self.sequence, self.generation, time.monotonic(), image)
                            self.error = None
                if not self.stop_event.is_set():
                    raise EOFError("Stream ended")
            except Exception as exc:
                with self.lock:
                    self.latest = None
                    # Never put a URL or embedded credentials in the dashboard/log.
                    self.error = f"camera disconnected ({type(exc).__name__})"
                self.stop_event.wait(2)
