from datetime import datetime, timedelta, timezone

from src.analysis.splits import SPLIT_DISTANCES, compute_best_splits
from src.models.activity import TrackPoint


def _make_points(km_distance: float, pace_min_per_km: float, n_segments: int = 20) -> list[TrackPoint]:
    lat, lon = 48.0, 2.0
    base = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    pts = []
    seg_km = km_distance / n_segments
    seg_sec = pace_min_per_km * 60 * seg_km
    deg_per_seg = seg_km / 111.0
    for i in range(n_segments + 1):
        pts.append(TrackPoint(
            lat=lat + i * deg_per_seg,
            lon=lon,
            ele=100.0,
            time=base + timedelta(seconds=i * seg_sec),
            hr=150.0,
        ))
    return pts


class TestSplitTimes:
    def test_1km_split(self):
        pts = _make_points(2.0, 5.0)
        splits = compute_best_splits(pts, [1000])
        assert splits[1000] is not None
        expected_sec = 5.0 * 60
        assert abs(splits[1000] - expected_sec) < 300

    def test_100m_split(self):
        pts = _make_points(1.0, 5.0, 50)
        splits = compute_best_splits(pts, [100])
        assert splits[100] is not None

    def test_split_exceeding_distance(self):
        pts = _make_points(0.5, 5.0)
        splits = compute_best_splits(pts, [1000])
        assert splits[1000] is None

    def test_all_split_distances(self):
        pts = _make_points(50, 5.0, 500)
        splits = compute_best_splits(pts, SPLIT_DISTANCES)
        for d in [100, 200, 400, 800, 1000, 5000, 10000]:
            assert splits[d] is not None
        assert splits[21097.5] is not None
        assert splits[42195] is not None

    def test_empty_points(self):
        splits = compute_best_splits([], [100])
        assert splits[100] is None

    def test_single_point(self):
        p = TrackPoint(0, 0, 0, datetime.now(tz=timezone.utc))
        splits = compute_best_splits([p], [100])
        assert splits[100] is None
