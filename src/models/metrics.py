from __future__ import annotations

import math
from datetime import timedelta

from src.models.activity import Activity, TrackPoint

STOP_DISTANCE_THRESHOLD_M = 1.0


def haversine_km(p1: TrackPoint, p2: TrackPoint) -> float:
    R = 6371.0
    lat1, lon1 = math.radians(p1.lat), math.radians(p1.lon)
    lat2, lon2 = math.radians(p2.lat), math.radians(p2.lon)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def cumulative_distances_m(points: list[TrackPoint]) -> list[float]:
    """Build cumulative distance in meters from the start of the track."""
    dists = [0.0]
    for i in range(1, len(points)):
        d = haversine_km(points[i - 1], points[i]) * 1000
        dists.append(dists[-1] + d)
    return dists


def compute_distance_m(points: list[TrackPoint]) -> float:
    if len(points) < 2:
        return 0.0
    return cumulative_distances_m(points)[-1]


def compute_elevation_gain_m(points: list[TrackPoint]) -> float:
    gain = 0.0
    for i in range(1, len(points)):
        diff = points[i].ele - points[i - 1].ele
        if diff > 0:
            gain += diff
    return gain


def compute_times(points: list[TrackPoint]) -> dict:
    if len(points) < 2:
        return {"elapsed": timedelta(0), "moving": timedelta(0), "stopped": timedelta(0)}
    moving = timedelta(0)
    stopped = timedelta(0)
    for i in range(1, len(points)):
        prev_time = points[i - 1].time
        cur_time = points[i].time
        if prev_time and cur_time:
            dt = cur_time - prev_time
            dist = haversine_km(points[i - 1], points[i]) * 1000
            if dist > STOP_DISTANCE_THRESHOLD_M:
                moving += dt
            else:
                stopped += dt
    elapsed = points[-1].time - points[0].time if points[-1].time and points[0].time else timedelta(0)
    return {"elapsed": elapsed, "moving": moving, "stopped": stopped}


def _avg_value(points: list[TrackPoint], attr: str) -> float | None:
    vals: list[float] = [getattr(p, attr) for p in points if getattr(p, attr) is not None]  # type: ignore[misc]
    if not vals:
        return None
    return sum(vals) / len(vals)


def _min_value(points: list[TrackPoint], attr: str) -> float | None:
    vals: list[float] = [getattr(p, attr) for p in points if getattr(p, attr) is not None]  # type: ignore[misc]
    if not vals:
        return None
    return min(vals)


def _max_value(points: list[TrackPoint], attr: str) -> float | None:
    vals: list[float] = [getattr(p, attr) for p in points if getattr(p, attr) is not None]  # type: ignore[misc]
    if not vals:
        return None
    return max(vals)


def compute_vertical_speed(points: list[TrackPoint]) -> list[tuple[float, float, float]]:
    segs = []
    dist_so_far = 0.0
    for i in range(1, len(points)):
        seg_dist = haversine_km(points[i - 1], points[i]) * 1000
        dist_to = dist_so_far + seg_dist
        mid = (dist_so_far + dist_to) / 2
        vs = 0.0
        prev_time = points[i - 1].time
        cur_time = points[i].time
        if prev_time and cur_time and seg_dist > 0:
            dt_min = (cur_time - prev_time).total_seconds() / 60
            if dt_min > 0:
                vs = (points[i].ele - points[i - 1].ele) / dt_min * 60
        segs.append((mid, vs, seg_dist))
        dist_so_far = dist_to
    return segs


def compute_cumulative_data(points: list[TrackPoint]) -> dict:
    """Build cumulative distance, pace, HR, VS, elevation series at each point."""
    distances = []
    elevations = []
    pace_per_km = []
    hr_values = []
    vs_values = []
    dist_so_far = 0.0
    moving_time = 0.0
    for i, p in enumerate(points):
        if i == 0:
            distances.append(0.0)
            elevations.append(p.ele)
            hr_values.append(p.hr)
            pace_per_km.append(0.0)
            vs_values.append(0.0)
        else:
            seg_dist = haversine_km(points[i - 1], p) * 1000
            prev_time = points[i - 1].time
            if p.time and prev_time:
                dt_s = (p.time - prev_time).total_seconds()
                if seg_dist > STOP_DISTANCE_THRESHOLD_M:
                    moving_time += dt_s
                dt_min = dt_s / 60
                vs = (p.ele - points[i - 1].ele) / dt_min * 60 if dt_min > 0 else 0.0
            else:
                dt_s = 0
                dt_min = 0
                vs = 0.0
                seg_dist = 0
            dist_so_far += seg_dist
            distances.append(dist_so_far / 1000)
            elevations.append(p.ele)
            hr_values.append(p.hr)
            vs_values.append(vs)
            if moving_time > 0:
                pace_per_km.append(moving_time / dist_so_far * 1000 if dist_so_far > 0 else 0)
            else:
                pace_per_km.append(0.0)
    return {
        "distances": distances,
        "elevations": elevations,
        "pace_per_km": pace_per_km,
        "hr_values": hr_values,
        "vs_values": vs_values,
    }


def compute_metrics(activity: Activity) -> dict:
    pts = activity.points
    dist_m = compute_distance_m(pts)
    el_gain = compute_elevation_gain_m(pts)
    times = compute_times(pts)
    moving_secs = times["moving"].total_seconds()
    pace_secs = moving_secs / dist_m * 1000 if dist_m > 0 else 0
    return {
        "distance_m": dist_m,
        "distance_km": dist_m / 1000,
        "elevation_gain_m": el_gain,
        "elapsed": times["elapsed"],
        "moving": times["moving"],
        "stopped": times["stopped"],
        "pace_s_per_km": pace_secs,
        "avg_hr": _avg_value(pts, "hr"),
        "min_hr": _min_value(pts, "hr"),
        "max_hr": _max_value(pts, "hr"),
        "avg_cadence": _avg_value(pts, "cadence"),
        "vertical_speeds": compute_vertical_speed(pts),
    }
