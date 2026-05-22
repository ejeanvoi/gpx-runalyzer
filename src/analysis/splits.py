from __future__ import annotations

from src.models.activity import TrackPoint
from src.models.metrics import cumulative_distances_m


def compute_best_splits(points: list[TrackPoint], split_distances: list[float]) -> dict:
    if len(points) < 2:
        return {d: None for d in split_distances}
    cum_dists = cumulative_distances_m(points)
    total_dist = cum_dists[-1]
    if total_dist == 0:
        return {d: None for d in split_distances}
    best: dict[float, float | None] = {}
    for split_d in split_distances:
        if split_d > total_dist:
            best[split_d] = None
            continue
        best_time = None
        j = 0
        for i in range(len(points)):
            while j < len(points) and (cum_dists[j] - cum_dists[i]) < split_d:
                j += 1
            if j >= len(points):
                break
            if points[i].time and points[j].time:
                dt = (points[j].time - points[i].time).total_seconds()  # type: ignore[operator]
                if dt > 0 and (best_time is None or dt < best_time):
                    best_time = dt
            if j >= len(points) - 1:
                break
        best[split_d] = best_time
    return best


SPLIT_LABELS = {
    100: "100 m",
    200: "200 m",
    400: "400 m",
    800: "800 m",
    1000: "1 K",
    5000: "5 K",
    10000: "10 K",
    21097.5: "Half",
    42195: "Full",
}


SPLIT_DISTANCES = [100, 200, 400, 800, 1000, 5000, 10000, 21097.5, 42195]

PR_DISTANCES: list[float] = [1000, 5000, 10000, 21097.5, 42195]
