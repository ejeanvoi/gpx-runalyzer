from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

if QApplication.instance() is None:
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)

from src.models.gpx_parser import parse_gpx
from src.services.store import ActivityStore

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session", autouse=True)
def _share_gl_context():
    if QApplication.instance() is None:
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)
        QApplication([])
    yield


def _make_test_dir() -> Path:
    base = Path(tempfile.mkdtemp())
    running = base / "running"
    running.mkdir()
    shutil.copy(FIXTURES_DIR / "sample.gpx", running / "run1.gpx")
    trail = base / "trail_running"
    trail.mkdir()
    shutil.copy(FIXTURES_DIR / "sample.gpx", trail / "trail1.gpx")
    return base


def _make_test_store() -> ActivityStore:
    base = _make_test_dir()
    store = ActivityStore(base)
    store.load()
    store._tmpdir = base  # type: ignore[attr-defined]
    return store


@pytest.fixture
def test_dir() -> Path:
    base = _make_test_dir()
    yield base
    shutil.rmtree(base)


@pytest.fixture
def store() -> ActivityStore:
    s = _make_test_store()
    yield s
    shutil.rmtree(s._tmpdir)  # type: ignore[union-attr]


@pytest.fixture
def sample_activity():
    return parse_gpx(FIXTURES_DIR / "sample.gpx")


@pytest.fixture
def store_with_activity():
    s = _make_test_store()
    acts = s.get_all()
    yield s, acts[0]
    shutil.rmtree(s._tmpdir)  # type: ignore[union-attr]
