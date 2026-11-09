"""CPU-only YOLOX ONNX person detector and ephemeral ByteTrack association.

Tensor conventions follow Megvii's Apache-2.0 YOLOX ONNX deployment documentation.
See docs/software/Server.md for model provenance and the overhead-view limitations.
"""

from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort
import supervision as sv
from trackers import ByteTrackTracker


class PersonDetector:
    def __init__(self, model: Path, threads: int = 2):
        options = ort.SessionOptions()
        options.intra_op_num_threads = threads
        options.inter_op_num_threads = 1
        self.session = ort.InferenceSession(str(model), options, providers=["CPUExecutionProvider"])
        tensor = self.session.get_inputs()[0]
        self.input_name = tensor.name
        if len(tensor.shape) != 4 or tensor.shape[:2] != [1, 3]:
            raise ValueError("Expected a batch-1, three-channel YOLOX ONNX model.")
        self.height, self.width = map(int, tensor.shape[2:])
        grid, scale = [], []
        for stride in (8, 16, 32):
            for y in range(self.height // stride):
                for x in range(self.width // stride):
                    grid.append((x, y))
                    scale.append(stride)
        self.grid = np.asarray(grid, dtype=np.float32)
        self.scale = np.asarray(scale, dtype=np.float32)[:, None]

    def detect(self, frame: np.ndarray) -> sv.Detections:
        height, width = frame.shape[:2]
        ratio = min(self.height / height, self.width / width)
        resized = cv2.resize(frame, (int(width * ratio), int(height * ratio)))
        padded = np.full((self.height, self.width, 3), 114, dtype=np.uint8)
        padded[: resized.shape[0], : resized.shape[1]] = resized
        # This release expects BGR float32 0..255 with top-left letterboxing.
        tensor = np.ascontiguousarray(padded.transpose(2, 0, 1)[None], dtype=np.float32)
        predictions = self.session.run(None, {self.input_name: tensor})[0][0]
        return self.decode(predictions, ratio, width, height)

    def decode(self, predictions, ratio, width, height) -> sv.Detections:
        if predictions.shape != (len(self.grid), 85):
            raise ValueError("Expected the raw COCO YOLOX ONNX output (N, 85).")
        # COCO class zero is person. Keep weak detections for ByteTrack's second pass.
        scores = predictions[:, 4] * predictions[:, 5]
        keep = np.isfinite(predictions).all(axis=1) & (scores >= 0.1)
        keep &= predictions[:, 5:].argmax(axis=1) == 0
        if not keep.any():
            return sv.Detections.empty()
        values = predictions[keep]
        centers = (values[:, :2] + self.grid[keep]) * self.scale[keep]
        sizes = np.exp(np.clip(values[:, 2:4], -20, 20)) * self.scale[keep]
        boxes = np.concatenate((centers - sizes / 2, centers + sizes / 2), axis=1) / ratio
        boxes[:, [0, 2]] = np.clip(boxes[:, [0, 2]], 0, width)
        boxes[:, [1, 3]] = np.clip(boxes[:, [1, 3]], 0, height)
        good = (boxes[:, 2] > boxes[:, 0]) & (boxes[:, 3] > boxes[:, 1])
        detections = sv.Detections(
            xyxy=boxes[good],
            confidence=scores[keep][good],
            class_id=np.zeros(int(good.sum()), dtype=int),
        )
        return detections.with_nms(threshold=0.45)


def make_tracker(fps: float, confidence: float):
    return ByteTrackTracker(
        frame_rate=fps,
        lost_track_buffer=30,
        track_activation_threshold=confidence,
        high_conf_det_threshold=confidence,
        minimum_consecutive_frames=2,
    )
