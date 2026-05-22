from pathlib import Path

from src.models.activity import Activity, TrackPoint, compute_activity_id
from src.models.gpx_parser import parse_gpx

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestComputeActivityId:
    def test_deterministic(self):
        from datetime import datetime
        fp = Path("/test/run.gpx")
        dt = datetime.fromisoformat("2024-01-01T00:00:00+00:00")
        id1 = compute_activity_id(fp, dt)
        id2 = compute_activity_id(fp, dt)
        assert id1 == id2

    def test_different_file_different_id(self):
        from datetime import datetime
        dt = datetime.fromisoformat("2024-01-01T00:00:00+00:00")
        id1 = compute_activity_id(Path("/a.gpx"), dt)
        id2 = compute_activity_id(Path("/b.gpx"), dt)
        assert id1 != id2


class TestTrackPoint:
    def test_creation(self):
        from datetime import datetime
        tp = TrackPoint(
            lat=48.85,
            lon=2.35,
            ele=50.0,
            time=datetime.fromisoformat("2024-01-01T00:00:00+00:00"),
            hr=150.0,
        )
        assert tp.lat == 48.85
        assert tp.lon == 2.35
        assert tp.hr == 150.0


class TestActivity:
    def test_creation(self):
        from datetime import datetime
        act = Activity(
            id="abc123",
            name="Test Run",
            date=datetime.fromisoformat("2024-01-01T00:00:00+00:00"),
            activity_type="running",
            filepath=Path("/test/run.gpx"),
        )
        assert act.id == "abc123"
        assert act.activity_type == "running"


class TestGpxParser:
    def test_parse_sample_gpx(self):
        act = parse_gpx(FIXTURES_DIR / "sample.gpx")
        assert act is not None
        assert act.name == "Sample Morning Run"
        assert len(act.points) == 5

    def test_parses_heart_rate(self):
        act = parse_gpx(FIXTURES_DIR / "sample.gpx")
        hrs = [p.hr for p in act.points if p.hr is not None]
        assert len(hrs) == 5
        assert hrs[0] == 150.0
        assert hrs[-1] == 162.0

    def test_parses_cadence(self):
        act = parse_gpx(FIXTURES_DIR / "sample.gpx")
        cads = [p.cadence for p in act.points if p.cadence is not None]
        assert len(cads) == 5
        assert cads[0] == 80.0

    def test_parses_elevation(self):
        act = parse_gpx(FIXTURES_DIR / "sample.gpx")
        elevs = [p.ele for p in act.points]
        assert elevs[0] == 35.0
        assert elevs[-1] == 40.0

    def test_parses_timestamps(self):
        act = parse_gpx(FIXTURES_DIR / "sample.gpx")
        times = [p.time for p in act.points]
        assert all(t is not None for t in times)

    def test_activity_type_from_parent_dir(self):
        act = parse_gpx(FIXTURES_DIR / "sample.gpx")
        assert act.activity_type == "fixtures"

    def test_activity_id_generated(self):
        act = parse_gpx(FIXTURES_DIR / "sample.gpx")
        assert act.id is not None
        assert len(act.id) == 12

    def test_activity_date_from_metadata(self):
        act = parse_gpx(FIXTURES_DIR / "sample.gpx")
        assert act.date.year == 2024
        assert act.date.month == 6
        assert act.date.day == 15
