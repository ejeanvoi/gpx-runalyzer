from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "gpx-runalyzer"
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class AppSettings:
    start_date: str | None = None
    end_date: str | None = None
    activity_types: list[str] = field(default_factory=list)


def _make_directory() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_settings() -> AppSettings:
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text())
            return AppSettings(**data)
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    return AppSettings()


def save_settings(settings: AppSettings) -> None:
    _make_directory()
    CONFIG_FILE.write_text(json.dumps(asdict(settings), indent=2))
