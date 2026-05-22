from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.models.activity import TrackPoint
from src.models.gpx_parser import parse_gpx
from src.models.metrics import (
    compute_cumulative_data,
    compute_distance_m,
    compute_elevation_gain_m,
    compute_metrics,
    compute_times,
    compute_vertical_speed,
)

from tests.test_activity import FIXTURES_DIR


class TestDistance:
    def test_zero_points(self):
        assert compute_distance_m([]) == 0.0

    def test_single_point(self):
        p = TrackPoint(0, 0, 0, datetime.now(tz=timezone.utc))
        assert compute_distance_m([p]) == 0.0

    def test_sample_gpx_distance(self):
        act = parse_gpx(FIXTURES_DIR / "sample.gpx")
        d = compute_distance_m(act.points)
        assert d > 0
        assert d < 1000


class TestElevationGain:
    def test_no_gain(self):
        pts = [
            TrackPoint(0, 0, 100, datetime.now(tz=timezone.utc)),
            TrackPoint(0, 0.001, 100, datetime.now(tz=timezone.utc)),
        ]
        assert compute_elevation_gain_m(pts) == 0.0

    def test_with_gain(self):
        base = datetime.now(tz=timezone.utc)
        pts = [
            TrackPoint(0, 0, 100, base),
            TrackPoint(0.001, 0.001, 150, base + timedelta(seconds=30)),
            TrackPoint(0.002, 0.002, 130, base + timedelta(seconds=60)),
        ]
        assert compute_elevation_gain_m(pts) == 50.0

    def test_no_points(self):
        assert compute_elevation_gain_m([]) == 0.0


class TestTimes:
    def test_moving_time(self):
        base = datetime.now(tz=timezone.utc)
        pts = [
            TrackPoint(0, 0, 0, base),
            TrackPoint(0.01, 0.01, 0, base + timedelta(seconds=60)),
        ]
        times = compute_times(pts)
        assert times["moving"].total_seconds() > 0

    def test_empty(self):
        times = compute_times([])
        assert times["moving"].total_seconds() == 0


class TestComputeMetrics:
    def test_full_metrics(self):
        act = parse_gpx(FIXTURES_DIR / "sample.gpx")
        m = compute_metrics(act)
        assert m["distance_m"] > 0
        assert m["distance_km"] > 0
        assert m["elevation_gain_m"] > 0
        assert m["pace_s_per_km"] > 0
        assert m["avg_hr"] is not None
        assert m["max_hr"] is not None
        assert m["min_hr"] is not None
        assert len(m["vertical_speeds"]) > 0


class TestVerticalSpeed:
    def test_vertical_speeds(self):
        act = parse_gpx(FIXTURES_DIR / "sample.gpx")
        vs = compute_vertical_speed(act.points)
        assert len(vs) == 4
        for mid, speed, dist in vs:
            assert isinstance(speed, float)


class TestCumulativeData:
    def test_basic_structure(self):
        act = parse_gpx(FIXTURES_DIR / "sample.gpx")
        cd = compute_cumulative_data(act.points)
        assert "distances" in cd
        assert "elevations" in cd
        assert "pace_per_km" in cd
        assert "hr_values" in cd
        assert "vs_values" in cd
        assert len(cd["distances"]) == len(act.points)

    def test_distance_starts_at_zero(self):
        cd = compute_cumulative_data(parse_gpx(FIXTURES_DIR / "sample.gpx").points)
        assert cd["distances"][0] == 0.0

    def test_pace_starts_at_zero(self):
        cd = compute_cumulative_data(parse_gpx(FIXTURES_DIR / "sample.gpx").points)
        assert cd["pace_per_km"][0] == 0.0

    def test_hr_preserved(self):
        act = parse_gpx(FIXTURES_DIR / "sample.gpx")
        cd = compute_cumulative_data(act.points)
        assert cd["hr_values"][0] == 150.0

    def test_distance_increases(self):
        cd = compute_cumulative_data(parse_gpx(FIXTURES_DIR / "sample.gpx").points)
        for i in range(1, len(cd["distances"])):
            assert cd["distances"][i] >= cd["distances"][i - 1]

    def test_pace_matches_metrics_at_end(self):
        act = parse_gpx(FIXTURES_DIR / "sample.gpx")
        cd = compute_cumulative_data(act.points)
        metrics = compute_metrics(act)
        last_pace = cd["pace_per_km"][-1]
        overall_pace = metrics["pace_s_per_km"]
        assert last_pace > 0
        assert abs(last_pace - overall_pace) / overall_pace < 0.01


    def test_final_distance_matches_total(self):
        act = parse_gpx(FIXTURES_DIR / "sample.gpx")
        cd = compute_cumulative_data(act.points)
        total = compute_distance_m(act.points)
        final_km = cd["distances"][-1]
        assert abs(final_km - total / 1000) < 1e-6
