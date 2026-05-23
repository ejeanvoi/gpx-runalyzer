from datetime import datetime, timedelta, timezone

from src.analysis.splits import (
    SPLIT_DISTANCES,
    VS_WINDOWS,
    compute_best_splits,
    compute_best_vertical_speeds,
)
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


def _make_climbing_points(
    gain_per_min: float, duration_min: int, interval_s: int = 10
) -> list[TrackPoint]:
    """Points climbing at constant rate: gain_per_min m/min, every interval_s seconds."""
    base = datetime(2024, 6, 1, 8, 0, 0, tzinfo=timezone.utc)
    n = duration_min * 60 // interval_s + 1
    ele_per_step = gain_per_min * interval_s / 60
    return [
        TrackPoint(
            lat=48.0,
            lon=6.0,
            ele=1000.0 + i * ele_per_step,
            time=base + timedelta(seconds=i * interval_s),
        )
        for i in range(n)
    ]


class TestBestVerticalSpeeds:
    def test_empty_points(self):
        result = compute_best_vertical_speeds([])
        assert all(v is None for v in result.values())

    def test_no_timestamps(self):
        pts = [TrackPoint(0, 0, 100 + i, None) for i in range(10)]
        result = compute_best_vertical_speeds(pts)
        assert all(v is None for v in result.values())

    def test_constant_climb_1min(self):
        # 600 m/h = 10 m/min constant climb, 5-minute activity
        pts = _make_climbing_points(gain_per_min=10.0, duration_min=5)
        result = compute_best_vertical_speeds(pts, [60])
        assert result[60] is not None
        vs, _slope = result[60]
        assert abs(vs - 600.0) < 1.0  # 10 m/min * 60 = 600 m/h

    def test_window_longer_than_activity(self):
        # 2-minute activity, 30-min window should return None
        pts = _make_climbing_points(gain_per_min=10.0, duration_min=2)
        result = compute_best_vertical_speeds(pts, [1800])
        assert result[1800] is None

    def test_all_windows(self):
        # 35-minute constant climb — all 6 windows should have a value
        pts = _make_climbing_points(gain_per_min=10.0, duration_min=35)
        result = compute_best_vertical_speeds(pts, VS_WINDOWS)
        assert all(v is not None for v in result.values())

    def test_flat_activity(self):
        # No elevation gain — VS is 0.0 m/h (displays as "--" via format_vert_speed)
        base = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        pts = [
            TrackPoint(48.0, 6.0, 500.0, base + timedelta(seconds=i * 30))
            for i in range(120)
        ]
        result = compute_best_vertical_speeds(pts, [60])
        assert result[60] == (0.0, 0.0)

    def test_slope_percentage(self):
        # 10 m gain over 100 m horizontal → 10% slope
        base = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        # ~100 m horizontal distance per segment: 0.001° lat ≈ 111 m
        pts = [
            TrackPoint(
                lat=48.0 + i * 0.0009,  # ~100 m per step
                lon=6.0,
                ele=1000.0 + i * 10.0,  # 10 m gain per step
                time=base + timedelta(seconds=i * 30),
            )
            for i in range(20)
        ]
        result = compute_best_vertical_speeds(pts, [60])
        assert result[60] is not None
        _vs, slope = result[60]
        # ~100 m horiz, 10 m gain per 30-s step → slope ≈ 10%
        assert 5.0 < slope < 20.0
