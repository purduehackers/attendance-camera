import numpy as np
import supervision as sv

from attendance_camera.config import Calibration
from attendance_camera.counting import CrossingCounter
from attendance_camera.vision import PersonDetector, make_tracker


def test_yolox_person_decode_and_nms():
    detector = PersonDetector.__new__(PersonDetector)
    detector.grid = np.array([[1, 1], [1, 1]], dtype=np.float32)
    detector.scale = np.array([[8], [8]], dtype=np.float32)
    predictions = np.zeros((2, 85), dtype=np.float32)
    predictions[:, 2:4] = np.log(4)
    predictions[:, 4:6] = 0.9
    detected = detector.decode(predictions, 1, 100, 100)
    assert len(detected) == 1
    assert detected.class_id[0] == 0
    assert np.allclose(detected.xyxy[0], [0, 0, 24, 24])
    predictions[:, 5] = 0
    assert len(detector.decode(predictions, 1, 100, 100)) == 0


def test_bytetrack_to_counting_pipeline_with_synthetic_boxes():
    tracker = make_tracker(10, 0.4)
    counter = CrossingCounter(Calibration())
    total = [0, 0]
    for index, y in enumerate(np.linspace(0.2, 0.8, 31)):
        detections = sv.Detections(
            xyxy=np.array([[40, y * 100 - 10, 60, y * 100 + 10]]),
            confidence=np.array([0.9]),
            class_id=np.array([0]),
        )
        tracked = tracker.update(detections, timestamp=index * 0.1)
        centers = [
            (int(key), float((b[0] + b[2]) / 200), float((b[1] + b[3]) / 200))
            for key, b in zip(tracked.tracker_id, tracked.xyxy)
            if key >= 0
        ]
        total = [a + b for a, b in zip(total, counter.update(centers, index * 0.1))]
    assert total == [1, 0]
