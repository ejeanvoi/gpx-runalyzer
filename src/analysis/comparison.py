from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta

from src.models.activity import Activity
from src.models.metrics import compute_metrics


class ComparisonEntry:
    def __init__(self, activity: Activity, metrics: dict, similarity: float = 0.0):
        self.activity = activity
        self.metrics = metrics
        self.similarity = similarity

    @property
    def distance_m(self) -> float:
        return float(self.metrics.get("distance_m", 0.0))

    @property
    def distance_km(self) -> float:
        return float(self.metrics.get("distance_km", 0.0))

    @property
    def pace_s_per_km(self) -> float:
        return float(self.metrics.get("pace_s_per_km", 0.0))

    @property
    def elevation_gain_m(self) -> float:
        return float(self.metrics.get("elevation_gain_m", 0.0))

    @property
    def avg_hr(self) -> float | None:
        return self.metrics.get("avg_hr")

    @property
    def max_hr(self) -> float | None:
        return self.metrics.get("max_hr")

    @property
    def moving(self) -> timedelta | None:
        return self.metrics.get("moving")


def build_comparison_with_reference(
    reference: Activity,
    others: list[tuple[Activity, float]],
    metrics_getter: Callable[[Activity], dict] = compute_metrics,
) -> list[ComparisonEntry]:
    ref_m = metrics_getter(reference)
    entries: list[ComparisonEntry] = [ComparisonEntry(reference, ref_m, 1.0)]
    for act, sim in others:
        m = metrics_getter(act)
        entries.append(ComparisonEntry(act, m, sim))
    return entries
