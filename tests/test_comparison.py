from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.analysis.comparison import (
    ComparisonEntry,
    build_comparison_with_reference,
)
from src.models.activity import Activity, TrackPoint


def _make_activity(pts: list[TrackPoint], aid: str = "x") -> Activity:
    return Activity(
        id=aid,
        name="Test",
        date=datetime.now(tz=timezone.utc),
        activity_type="running",
        filepath=__file__ / Path("") / "d.gpx",
        points=pts,
    )


def _make_pts(offset: float = 0.0) -> list[TrackPoint]:
    base = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    return [
        TrackPoint(48.0 + offset, 2.0, 100, base, hr=150.0),
        TrackPoint(48.01 + offset, 2.01, 120, base + timedelta(seconds=300), hr=155.0),
    ]


class TestComparisonEntry:
    def test_properties(self):
        pts = _make_pts()
        act = _make_activity(pts)
        from src.models.metrics import compute_metrics
        m = compute_metrics(act)
        entry = ComparisonEntry(act, m, 0.9)
        assert entry.distance_m > 0
        assert entry.similarity == 0.9


class TestBuildComparison:
    def test_with_reference(self):
        pts1 = _make_pts()
        pts2 = _make_pts(offset=0.001)
        ref = _make_activity(pts1, "ref")
        others = [(_make_activity(pts2, "a"), 0.85)]
        entries = build_comparison_with_reference(ref, others)
        assert len(entries) == 2
        assert entries[0].similarity == 1.0
        assert entries[1].similarity == 0.85
