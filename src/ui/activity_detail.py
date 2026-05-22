from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.models.activity import Activity
from src.ui import formatting, theme
from src.ui.widgets.elevation_chart import SeriesChart as ElevationChart

if TYPE_CHECKING:
    from src.ui.widgets.map_view import MapView


# ── activity type → badge color / emoji mapping ─────────
_TYPE_META: dict[str, tuple[str, str]] = {
    "running": (theme.SUCCESS, "\U0001f3c3"),
    "cycling": (theme.WARNING, "\U0001f6b4"),
    "walking": (theme.ACCENT, "\U0001f6b6"),
    "hiking": (theme.SUCCESS, "\U0001f97e"),
}
_DEFAULT_TYPE: tuple[str, str] = (theme.TEXT_SUBTLE, "\U0001f3c5")


class ActivityDetailView(QWidget):
    compare_route_requested = pyqtSignal(object)

    def __init__(self, store, parent=None):
        super().__init__(parent)
        self._store = store
        self._activity: Activity | None = None
        self._build_ui()

    # ── UI construction ──────────────────────────────────

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(16, 12, 16, 12)
        main.setSpacing(12)

        # 1 \u2013 Header: date + name + type badge
        header = QHBoxLayout()
        header.setSpacing(12)
        self._header_label = QLabel()
        self._header_label.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_XXL}; font-weight: 700;"
        )
        header.addWidget(self._header_label, 1)
        self._type_badge = QLabel()
        self._type_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(self._type_badge)
        self._header_layout = header
        main.addLayout(header)

        # 2 — Compact metric bar
        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(16)
        metrics_row.setContentsMargins(0, 0, 0, 0)
        self._card_distance = QLabel("📍 0.00 km")
        self._card_pace = QLabel("⏱ --:--/km")
        self._card_elevation = QLabel("⛰ 0 m+")
        self._card_hr = QLabel("❤ HR: --")
        for lbl in (self._card_distance, self._card_pace, self._card_elevation, self._card_hr):
            lbl.setStyleSheet(
                f"color: {theme.TEXT_SUBTLE}; font-size: {theme.FONT_SIZE_BASE}; font-weight: 600; padding: 0;"
            )
            metrics_row.addWidget(lbl)
        metrics_row.addStretch()
        main.addLayout(metrics_row)

        # 3 \u2013 Splits grid
        splits_header = QLabel("Splits")
        splits_header.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_MD}; font-weight: 600; "
            f"color: {theme.TEXT_SUBTLE};"
        )
        main.addWidget(splits_header)
        self._splits_grid = QGridLayout()
        self._splits_grid.setSpacing(6)
        self._split_labels: list[QLabel] = []
        main.addLayout(self._splits_grid)

        # 4 \u2013 Map (stacked widget, lazy MapView)
        self._map_stack = QStackedWidget()
        self._map_placeholder = QLabel("Map will appear when activity is loaded")
        self._map_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._map_placeholder.setStyleSheet(
            f"color: {theme.TEXT_SUBTLE}; font-size: {theme.FONT_SIZE_MD};"
        )
        self._map_stack.addWidget(self._map_placeholder)
        self._map_view: MapView | None = None
        main.addWidget(self._map_stack, stretch=3)

        # 5 \u2013 Elevation chart
        self._chart = ElevationChart()
        main.addWidget(self._chart, stretch=2)

        # 6 \u2013 Bottom button row
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._btn_compare = QPushButton("Find Similar Routes")
        self._btn_compare.clicked.connect(self._on_compare)
        self._btn_compare.setStyleSheet(
            f"background-color: {theme.ACCENT}; color: white; "
            f"border: none; border-radius: {theme.RADIUS_MD}; "
            f"padding: 10px 24px; font-size: {theme.FONT_SIZE_MD}; "
            f"font-weight: 600;"
        )
        btn_row.addWidget(self._btn_compare)
        btn_row.addStretch()
        main.addLayout(btn_row)

    # ── public API ───────────────────────────────────────

    def set_activity(self, activity: Activity):
        self._activity = activity
        metrics = self._store.get_metrics(activity)

        # Header
        date_str = activity.date.strftime("%Y-%m-%d %H:%M")
        self._header_label.setText(f"{date_str} \u2014 {activity.name}")

        # Type badge
        bg, emoji = _TYPE_META.get(activity.activity_type, _DEFAULT_TYPE)
        self._type_badge.setText(f"{emoji} {activity.activity_type.title()}")
        self._type_badge.setStyleSheet(
            f"QLabel {{ background-color: {bg}; color: white; "
            f"border-radius: {theme.RADIUS_SM}; padding: 3px 10px; "
            f"font-size: {theme.FONT_SIZE_SM}; font-weight: 600; }}"
        )

        # Metric bar
        dist_raw = metrics["distance_km"]
        self._card_distance.setText(f"📍 {formatting.format_distance_km(dist_raw)}")

        pace_s = metrics.get("pace_s_per_km", 0)
        pace_display = formatting.format_pace(pace_s)
        if not pace_display or pace_display == "--:--":
            pace_display = "--:--"
        self._card_pace.setText(f"⏱ {pace_display}/km")

        elev_raw = metrics["elevation_gain_m"]
        self._card_elevation.setText(f"⛰ {elev_raw:.0f} m+")

        avg_hr = metrics.get("avg_hr")
        hr_str = f"{avg_hr:.0f}" if avg_hr else "--"
        self._card_hr.setText(f"❤ HR: {hr_str}")

        # Splits
        from src.analysis.splits import (
            SPLIT_DISTANCES,
            SPLIT_LABELS,
            compute_best_splits,
        )

        splits = compute_best_splits(activity.points, SPLIT_DISTANCES)
        self._split_labels.clear()
        while self._splits_grid.count():
            item = self._splits_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        cols = 4
        for idx, d in enumerate(SPLIT_DISTANCES):
            label_text = SPLIT_LABELS.get(d, f"{d}m")
            t = splits.get(d)
            time_str = formatting.format_time_total(t) if t is not None else "--:--"
            split_lbl = QLabel(f"{label_text}: {time_str}")
            split_lbl.setStyleSheet(
                f"font-size: {theme.FONT_SIZE_SM}; padding: 4px 8px; "
                f"background-color: {theme.SURFACE}; "
                f"border-radius: {theme.RADIUS_SM}; "
                f"font-weight: 500;"
            )
            split_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row = idx // cols
            col = idx % cols
            self._splits_grid.addWidget(split_lbl, row, col)
            self._split_labels.append(split_lbl)

        # Map (lazy import)
        if self._map_view is None:
            from src.ui.widgets.map_view import MapView

            self._map_view = MapView()
            self._map_stack.addWidget(self._map_view)
            self._map_stack.setCurrentWidget(self._map_view)
        self._map_view.set_activity_name(activity.name)
        self._map_view.set_route(activity)

        # Chart
        self._chart.set_activity(activity)

    # ── slot ─────────────────────────────────────────────

    def _on_compare(self):
        if self._activity:
            self.compare_route_requested.emit(self._activity)
