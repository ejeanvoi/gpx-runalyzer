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

VS_WINDOWS: list[int] = [60, 180, 300, 600, 900, 1800]

VS_LABELS: dict[int, str] = {
    60: "1 min",
    180: "3 min",
    300: "5 min",
    600: "10 min",
    900: "15 min",
    1800: "30 min",
}


def compute_best_vertical_speeds(
    points: list[TrackPoint], windows_s: list[int] = VS_WINDOWS
) -> dict[int, tuple[float, float] | None]:
    """Return best (vs_m_per_h, slope_pct) per window, or None if window exceeds activity length."""
    timed = [p for p in points if p.time is not None]
    if len(timed) < 2:
        return {w: None for w in windows_s}

    # Prefix sums of positive elevation gain and cumulative horizontal distance (m)
    cum_gain: list[float] = [0.0]
    for k in range(1, len(timed)):
        diff = timed[k].ele - timed[k - 1].ele
        cum_gain.append(cum_gain[-1] + max(diff, 0.0))
    cum_dist = cumulative_distances_m(timed)

    result: dict[int, tuple[float, float] | None] = {}
    for window in windows_s:
        best_vs: float | None = None
        best_slope: float = 0.0
        j = 0
        for i in range(len(timed)):
            while j < len(timed) - 1 and (timed[j].time - timed[i].time).total_seconds() < window:  # type: ignore[operator]
                j += 1
            dt = (timed[j].time - timed[i].time).total_seconds()  # type: ignore[operator]
            if dt < window:
                break
            gain = cum_gain[j] - cum_gain[i]
            vs = gain / dt * 3600  # m/h
            if best_vs is None or vs > best_vs:
                best_vs = vs
                dist_m = cum_dist[j] - cum_dist[i]
                best_slope = (gain / dist_m * 100) if dist_m > 0 else 0.0
        result[window] = (best_vs, best_slope) if best_vs is not None else None
    return result
