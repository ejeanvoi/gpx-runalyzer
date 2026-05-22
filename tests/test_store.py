import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from src.services.store import ActivityStore

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _create_test_dir() -> Path:
    base = Path(tempfile.mkdtemp())
    running = base / "running"
    running.mkdir()
    shutil.copy(FIXTURES_DIR / "sample.gpx", running / "run1.gpx")
    trail = base / "trail_running"
    trail.mkdir()
    shutil.copy(FIXTURES_DIR / "sample.gpx", trail / "trail1.gpx")
    return base


class TestActivityStore:
    def test_load_activities(self):
        base = _create_test_dir()
        try:
            store = ActivityStore(base)
            store.load()
            assert store.is_loaded
            acts = store.get_all()
            assert len(acts) == 2
        finally:
            shutil.rmtree(base)

    def test_activity_types(self):
        base = _create_test_dir()
        try:
            store = ActivityStore(base)
            store.load()
            types = store.activity_types
            assert "running" in types
            assert "trail_running" in types
        finally:
            shutil.rmtree(base)

    def test_filter_by_type(self):
        base = _create_test_dir()
        try:
            store = ActivityStore(base)
            store.load()
            result = store.filter(activity_types={"running"})
            assert len(result) == 1
            assert result[0].activity_type == "running"
        finally:
            shutil.rmtree(base)

    def test_filter_by_date(self):
        base = _create_test_dir()
        try:
            store = ActivityStore(base)
            store.load()
            start = datetime(2024, 1, 1, tzinfo=timezone.utc)
            end = datetime(2024, 12, 31, tzinfo=timezone.utc)
            result = store.filter(start_date=start, end_date=end)
            assert len(result) == 2
        finally:
            shutil.rmtree(base)

    def test_filter_outside_date(self):
        base = _create_test_dir()
        try:
            store = ActivityStore(base)
            store.load()
            start = datetime(2020, 1, 1, tzinfo=timezone.utc)
            end = datetime(2020, 12, 31, tzinfo=timezone.utc)
            result = store.filter(start_date=start, end_date=end)
            assert len(result) == 0
        finally:
            shutil.rmtree(base)

    def test_metrics_caching(self):
        base = _create_test_dir()
        try:
            store = ActivityStore(base)
            store.load()
            acts = store.get_all()
            m1 = store.get_metrics(acts[0])
            m2 = store.get_metrics(acts[0])
            assert m1 is m2
        finally:
            shutil.rmtree(base)

    def test_nonexistent_directory(self):
        store = ActivityStore(Path("/nonexistent/path"))
        store.load()
        assert store.is_loaded
        assert len(store.get_all()) == 0
