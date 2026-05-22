from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class TrackPoint:
    lat: float
    lon: float
    ele: float
    time: datetime | None
    hr: float | None = None
    cadence: float | None = None


@dataclass
class Activity:
    id: str
    name: str
    date: datetime
    activity_type: str
    filepath: Path
    points: list[TrackPoint] = field(default_factory=list)


def compute_activity_id(filepath: Path, date: datetime) -> str:
    raw = f"{filepath.name}:{date.isoformat()}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]
