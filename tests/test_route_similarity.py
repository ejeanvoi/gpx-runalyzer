from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.analysis.route_similarity import (
    _bbox,
    _bboxes_overlap,
    _resample,
    find_similar_routes,
    route_similarity,
)
from src.models.activity import Activity, TrackPoint


def _make_route(offset: float = 0.0, jitter: float = 0.0) -> list[TrackPoint]:
    base = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    pts = []
    for i in range(10):
        lat = 48.0 + i * 0.001 + offset + (jitter * (i % 3 - 1))
        lon = 2.0 + i * 0.001
        pts.append(TrackPoint(lat, lon, 100 + i * 5, base + timedelta(seconds=i * 30), hr=150.0))
    return pts


def _make_activity(pts: list[TrackPoint]) -> Activity:
    return Activity(
        id=f"act_{id(pts)}",
        name="Test",
        date=datetime.now(tz=timezone.utc),
        activity_type="running",
        filepath=__file__ / Path("") / "dummy.gpx",
        points=pts,
    )


class TestResample:
    def test_no_change_small(self):
        pts = _make_route()
        res = _resample(pts, 50)
        assert len(res) == len(pts)

    def test_reduces(self):
        pts = _make_route()
        res = _resample(pts, 5)
        assert len(res) <= 5


class TestBbox:
    def test_bbox_bounds(self):
        pts = _make_route()
        mnlat, mxlat, mnlon, mxlon = _bbox(pts)
        assert mnlat < mxlat
        assert mnlon < mxlon

    def test_bboxes_overlap_same(self):
        pts = _make_route()
        bb = _bbox(pts)
        assert _bboxes_overlap(bb, bb)

    def test_bboxes_overlap_nearby(self):
        bb1 = _bbox(_make_route(offset=0))
        bb2 = _bbox(_make_route(offset=0.005))
        assert _bboxes_overlap(bb1, bb2)

    def test_bboxes_no_overlap_far(self):
        bb1 = _bbox(_make_route(offset=0))
        bb2 = _bbox(_make_route(offset=1.0))
        assert not _bboxes_overlap(bb1, bb2)


class TestRouteSimilarity:
    def test_identical_routes(self):
        pts = _make_route()
        a = _make_activity(pts)
        b = _make_activity(list(pts))
        sim = route_similarity(a, b)
        assert sim >= 0.9

    def test_slightly_different(self):
        pts = _make_route()
        pts2 = _make_route(jitter=0.0001)
        a = _make_activity(pts)
        b = _make_activity(pts2)
        sim = route_similarity(a, b)
        assert sim > 0

    def test_far_apart_routes(self):
        pts = _make_route(offset=0)
        pts2 = _make_route(offset=1.0)
        a = _make_activity(pts)
        b = _make_activity(pts2)
        sim = route_similarity(a, b)
        assert sim == 0.0


class TestFindSimilar:
    def test_finds_similar(self):
        pts1 = _make_route()
        pts2 = _make_route(jitter=0.0001)
        pts3 = _make_route(offset=1.0)
        ref = _make_activity(pts1)
        ref.id = "ref"
        others = [_make_activity(pts2), _make_activity(pts3)]
        others[0].id = "a"
        others[1].id = "b"
        results = find_similar_routes(others, ref, threshold=0.1)
        ids = [r[0].id for r in results]
        assert "a" in ids
        assert "b" not in ids

    def test_excludes_reference(self):
        pts = _make_route()
        ref = _make_activity(list(pts))
        ref.id = "ref"
        dup = _make_activity(list(pts))
        dup.id = "ref"
        results = find_similar_routes([dup], ref, threshold=0.5)
        assert len(results) == 0
