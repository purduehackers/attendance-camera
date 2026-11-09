"""Direction counting from transient track centers, with no identity persistence."""

from dataclasses import dataclass

from .config import Calibration


@dataclass
class TrackState:
    last_seen: float
    stable_side: int = 0
    candidate_side: int = 0
    candidate_frames: int = 0


class CrossingCounter:
    def __init__(self, calibration: Calibration):
        self.calibration = calibration
        self.tracks: dict[int, TrackState] = {}

    def reset(self):
        self.tracks.clear()

    def update(self, centers: list[tuple[int, float, float]], now: float) -> tuple[int, int]:
        c = self.calibration
        self.tracks = {
            key: state
            for key, state in self.tracks.items()
            if 0 <= now - state.last_seen <= c.max_gap_seconds
        }
        incoming = outgoing = 0
        for key, x, y in centers:
            if not (c.x_min <= x <= c.x_max and c.y_min <= y <= c.y_max):
                self.tracks.pop(key, None)
                continue
            coordinate = (
                (x - c.x_min) / (c.x_max - c.x_min)
                if c.axis == "x"
                else (y - c.y_min) / (c.y_max - c.y_min)
            )
            distance = coordinate - c.position
            state = self.tracks.setdefault(key, TrackState(now))
            state.last_seen = now
            if abs(distance) <= c.deadband:
                state.candidate_frames = 0
                continue
            side = 1 if distance > 0 else -1
            if state.candidate_side != side:
                state.candidate_side, state.candidate_frames = side, 0
            state.candidate_frames += 1
            if state.candidate_frames < c.confirmation_frames:
                continue
            if state.stable_side and state.stable_side != side:
                entering = (side == 1) == (c.inside == "positive")
                incoming += int(entering)
                outgoing += int(not entering)
            state.stable_side = side
        return incoming, outgoing
