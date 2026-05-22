from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from src.models.activity import Activity
from src.models.gpx_parser import parse_gpx
from src.models.metrics import compute_metrics

logger = logging.getLogger(__name__)


class ActivityStore:
    def __init__(self, root_folder: Path):
        self.root_folder = root_folder.resolve()
        self._activities: list[Activity] = []
        self._metrics_cache: dict[str, dict] = {}
        self._loaded = False

    def load(self):
        self._activities = []
        self._metrics_cache = {}
        if not self.root_folder.exists():
            self._loaded = True
            return
        for type_dir in sorted(self.root_folder.iterdir()):
            if not type_dir.is_dir():
                continue
            for gpx_file in sorted(type_dir.glob("*.gpx")):
                try:
                    act = parse_gpx(gpx_file)
                    self._activities.append(act)
                except Exception as e:
                    logger.warning("Failed to parse %s: %s", gpx_file, e)
        self._loaded = True

    def apply_load_filters(self, settings):
        from src.services.config import AppSettings
        if not isinstance(settings, AppSettings):
            return
        start = None
        end = None
        if settings.start_date:
            try:
                start = datetime.strptime(settings.start_date, "%Y-%m-%d")
            except ValueError:
                pass
        if settings.end_date:
            try:
                end = datetime.strptime(settings.end_date, "%Y-%m-%d")
            except ValueError:
                pass
        types = set(settings.activity_types) if settings.activity_types else None
        self._activities = self.filter(activity_types=types, start_date=start, end_date=end)
        self._metrics_cache.clear()

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def activity_types(self) -> list[str]:
        if not self._loaded:
            return []
        types = set()
        for act in self._activities:
            types.add(act.activity_type)
        return sorted(types)

    def get_all(self) -> list[Activity]:
        return list(self._activities)

    def filter(
        self,
        activity_types: set[str] | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[Activity]:
        result = self._activities
        if activity_types:
            result = [a for a in result if a.activity_type in activity_types]
        if start_date:
            s = start_date.replace(tzinfo=None) if start_date.tzinfo else start_date
            result = [a for a in result if a.date.replace(tzinfo=None) >= s]
        if end_date:
            e = end_date.replace(tzinfo=None) if end_date.tzinfo else end_date
            result = [a for a in result if a.date.replace(tzinfo=None) <= e]
        return sorted(result, key=lambda a: a.date)

    def get_metrics(self, activity: Activity) -> dict:
        if activity.id not in self._metrics_cache:
            self._metrics_cache[activity.id] = compute_metrics(activity)
        return self._metrics_cache[activity.id]

    def clear_metrics_cache(self):
        self._metrics_cache = {}
