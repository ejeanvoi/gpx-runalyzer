from __future__ import annotations

from src.models.activity import Activity, TrackPoint
from src.models.metrics import cumulative_distances_m, haversine_km


def _resample(points: list[TrackPoint], n: int = 200) -> list[TrackPoint]:
    if len(points) <= n:
        return list(points)
    dists = cumulative_distances_m(points)
    total = dists[-1]
    if total == 0:
        return [points[0]]
    resampled = [points[0]]
    idx = 1
    for i in range(1, n):
        target_dist = (i / (n - 1)) * total
        while idx < len(dists) - 1 and dists[idx] < target_dist:
            idx += 1
        if idx < len(points):
            resampled.append(points[idx])
    if resampled[-1] is not points[-1]:
        resampled.append(points[-1])
    return resampled


def _bbox(points: list[TrackPoint]) -> tuple[float, float, float, float]:
    lats = [p.lat for p in points]
    lons = [p.lon for p in points]
    return min(lats), max(lats), min(lons), max(lons)


def _bboxes_overlap(
    b1: tuple[float, float, float, float],
    b2: tuple[float, float, float, float],
    margin_km: float = 2.0,
) -> bool:
    deg_margin = margin_km / 111.0
    if b1[1] + deg_margin < b2[0] - deg_margin or b2[1] + deg_margin < b1[0] - deg_margin:
        return False
    return not (b1[3] + deg_margin < b2[2] - deg_margin or b2[3] + deg_margin < b1[2] - deg_margin)


def _frechet_discrete(
    A: list[TrackPoint],
    B: list[TrackPoint],
) -> float:
    n = len(A)
    m = len(B)

    def dist(i: int, j: int) -> float:
        return haversine_km(A[i], B[j]) * 1000

    INF = float("inf")
    dp = [[INF] * m for _ in range(n)]
    dp[0][0] = dist(0, 0)
    for i in range(1, n):
        dp[i][0] = max(dp[i - 1][0], dist(i, 0))
    for j in range(1, m):
        dp[0][j] = max(dp[0][j - 1], dist(0, j))
    for i in range(1, n):
        for j in range(1, m):
            dp[i][j] = max(dist(i, j), min(dp[i - 1][j - 1], dp[i][j - 1], dp[i - 1][j]))
    return dp[n - 1][m - 1]


def route_similarity(activity_a: Activity, activity_b: Activity) -> float:
    pts_a = _resample(activity_a.points, 200)
    pts_b = _resample(activity_b.points, 200)
    bb_a = _bbox(pts_a)
    bb_b = _bbox(pts_b)
    if not _bboxes_overlap(bb_a, bb_b):
        return 0.0
    fr = _frechet_discrete(pts_a, pts_b)
    dist_a = cumulative_distances_m(pts_a)[-1]
    dist_b = cumulative_distances_m(pts_b)[-1]
    ref = max(dist_a, dist_b)
    if ref == 0:
        return 1.0 if fr == 0 else 0.0
    similarity = max(0.0, 1.0 - fr / ref)
    return round(similarity, 4)


def find_similar_routes(
    activities: list[Activity],
    reference: Activity,
    threshold: float = 0.5,
) -> list[tuple[Activity, float]]:
    ref_pts = _resample(reference.points, 200)
    ref_bb = _bbox(ref_pts)
    results = []
    for act in activities:
        if act.id == reference.id:
            continue
        if not act.points:
            continue
        act_bb = _bbox(_resample(act.points, 200))
        if not _bboxes_overlap(ref_bb, act_bb):
            continue
        sim = route_similarity(reference, act)
        if sim >= threshold:
            results.append((act, sim))
    results.sort(key=lambda x: x[1], reverse=True)
    return results
