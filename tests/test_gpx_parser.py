from datetime import datetime, timezone
from pathlib import Path

import pytest
from src.models.gpx_parser import _parse_datetime, _parse_float, parse_gpx

FIXTURES_DIR = Path(__file__).parent / "fixtures"
TMPDIR = Path(__file__).parent / "temp_gpx"


@pytest.fixture(autouse=True)
def _cleanup_tmpdir():
    import shutil
    if TMPDIR.exists():
        shutil.rmtree(TMPDIR)
    TMPDIR.mkdir()
    yield
    import shutil
    if TMPDIR.exists():
        shutil.rmtree(TMPDIR)


class TestParseDatetime:
    def test_parse_utc_z(self):
        dt = _parse_datetime("2024-06-15T07:30:00Z")
        assert dt == datetime(2024, 6, 15, 7, 30, 0, tzinfo=timezone.utc)

    def test_parse_offset(self):
        dt = _parse_datetime("2024-06-15T07:30:00+02:00")
        assert dt.year == 2024

    def test_parse_none(self):
        assert _parse_datetime(None) is None

    def test_parse_invalid(self):
        assert _parse_datetime("not-a-date") is None


class TestParseFloat:
    def test_parse_number(self):
        assert _parse_float("150") == 150.0

    def test_parse_decimal(self):
        assert _parse_float("35.5") == 35.5

    def test_parse_none(self):
        assert _parse_float(None) is None

    def test_parse_invalid(self):
        assert _parse_float("abc") is None


class TestParseGarminGpx:
    def test_full_parse(self):
        act = parse_gpx(FIXTURES_DIR / "sample.gpx")
        assert act.name == "Sample Morning Run"
        assert len(act.points) == 5
        assert act.date.year == 2024

    def test_all_points_have_hr(self):
        act = parse_gpx(FIXTURES_DIR / "sample.gpx")
        assert all(p.hr is not None for p in act.points)

    def test_all_points_have_cadence(self):
        act = parse_gpx(FIXTURES_DIR / "sample.gpx")
        assert all(p.cadence is not None for p in act.points)

    def test_latitude_longitude_parsed(self):
        act = parse_gpx(FIXTURES_DIR / "sample.gpx")
        first = act.points[0]
        assert abs(first.lat - 48.8566) < 0.0001
        assert abs(first.lon - 2.3522) < 0.0001


class TestMinimalGpx:
    def test_minimal_gpx_no_extensions(self):
        gpx_content = '''<?xml version="1.0" encoding="UTF-8"?>
        <gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1">
          <trk>
            <trkseg>
              <trkpt lat="48.0" lon="2.0">
                <ele>100.0</ele>
                <time>2024-01-01T10:00:00Z</time>
              </trkpt>
            </trkseg>
          </trk>
        </gpx>'''
        fpath = TMPDIR / "minimal.gpx"
        fpath.write_text(gpx_content)
        act = parse_gpx(fpath)
        assert len(act.points) == 1
        assert act.points[0].hr is None
        assert act.points[0].cadence is None


class TestErrors:
    def test_no_track_raises(self):
        gpx_content = '''<?xml version="1.0" encoding="UTF-8"?>
        <gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1">
          <rte>
            <rtept lat="48.0" lon="2.0"/>
          </rte>
        </gpx>'''
        fpath = TMPDIR / "notrack.gpx"
        fpath.write_text(gpx_content)
        with pytest.raises(ValueError, match="No track"):
            parse_gpx(fpath)
