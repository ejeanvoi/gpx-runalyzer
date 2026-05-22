from __future__ import annotations

from datetime import timedelta


def format_pace(pace_s: float) -> str:
    """Format pace in seconds/km as 'M:SS'."""
    if pace_s <= 0:
        return "--:--"
    total_s = int(pace_s)
    mins = total_s // 60
    secs = total_s % 60
    return f"{mins}:{secs:02d}"


def format_time_total(seconds: float | None) -> str:
    """Format raw seconds as 'M:SS'."""
    if seconds is None:
        return "--:--"
    total = int(seconds)
    m = total // 60
    s = total % 60
    return f"{m}:{s:02d}"


def format_duration(td: timedelta | None) -> str:
    """Format a timedelta as 'H:MM:SS' or 'M:SS'."""
    if td is None:
        return "--:--"
    total = int(td.total_seconds())
    if total < 0:
        total = 0
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def format_distance_km(km: float, precision: int = 2) -> str:
    """Format distance with appropriate unit."""
    if km < 0.001:
        return f"{km * 1000:.0f} m"
    if km < 10:
        return f"{km:.{precision}f} km"
    return f"{km:.1f} km"


def format_elevation(m: float) -> str:
    """Format elevation gain."""
    return f"{m:.0f} m"


def format_vert_speed(vs_m_per_h: float | None) -> str:
    if not vs_m_per_h:
        return "--"
    return f"{vs_m_per_h:.0f} m/h"
