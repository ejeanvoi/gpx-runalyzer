from __future__ import annotations

from datetime import timedelta

from src.ui.formatting import (
    format_distance_km,
    format_duration,
    format_elevation,
    format_pace,
    format_time_total,
)


class TestFormatPace:
    def test_zero(self):
        assert format_pace(0) == "--:--"

    def test_negative(self):
        assert format_pace(-1) == "--:--"

    def test_normal(self):
        assert format_pace(300) == "5:00"

    def test_with_seconds(self):
        assert format_pace(315) == "5:15"

    def test_fast(self):
        assert format_pace(120) == "2:00"


class TestFormatTimeTotal:
    def test_none(self):
        assert format_time_total(None) == "--:--"

    def test_normal(self):
        assert format_time_total(315) == "5:15"

    def test_rounds_down(self):
        assert format_time_total(59.9) == "0:59"


class TestFormatDuration:
    def test_none(self):
        assert format_duration(None) == "--:--"

    def test_short(self):
        assert format_duration(timedelta(seconds=125)) == "2:05"

    def test_with_hours(self):
        assert format_duration(timedelta(seconds=3725)) == "1:02:05"

    def test_zero(self):
        assert format_duration(timedelta(0)) == "0:00"

    def test_negative(self):
        assert format_duration(timedelta(seconds=-10)) == "0:00"


class TestFormatDistanceKm:
    def test_under_meter(self):
        assert format_distance_km(0.0005) == "0 m"

    def test_under_10km(self):
        assert format_distance_km(5.123) == "5.12 km"

    def test_over_10km(self):
        assert format_distance_km(15.678) == "15.7 km"


class TestFormatElevation:
    def test_rounds(self):
        assert format_elevation(123.7) == "124 m"

    def test_zero(self):
        assert format_elevation(0) == "0 m"
