from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor, QMouseEvent
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from src.analysis.splits import PR_DISTANCES, SPLIT_LABELS, compute_best_splits
from src.models.activity import Activity
from src.services.store import ActivityStore
from src.ui.formatting import (
    format_distance_km,
    format_elevation,
    format_pace,
    format_time_total,
)
from src.ui.theme import (
    ACCENT,
    BORDER,
    CARD_BG,
    FONT_SIZE_BASE,
    FONT_SIZE_SM,
    RADIUS_MD,
    TEXT_SUBTLE,
)
from src.ui.widgets.activity_list import ActivityListModel, ActivityListView
from src.ui.widgets.filters import FiltersWidget


class _PRClickLabel(QLabel):
    clicked = pyqtSignal(object)

    def mousePressEvent(self, event: QMouseEvent | None):
        if event is not None and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self)
        super().mousePressEvent(event)

    def enterEvent(self, event):
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        super().enterEvent(event)


class DashboardView(QWidget):
    activity_selected = pyqtSignal(object)
    compare_route_requested = pyqtSignal(object)

    def __init__(self, store: ActivityStore, parent=None):
        super().__init__(parent)
        self._store = store
        self._metrics_map: dict = {}
        self._build_ui()

    # ── UI construction ──────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(12)

        # Filters (top)
        self._filters = FiltersWidget(self._store.activity_types)
        self._filters.filters_changed.connect(self._on_filters_changed)
        layout.addWidget(self._filters)

        # Compact summary bar
        self._summary_frame = QFrame()
        self._summary_frame.setStyleSheet(
            f"QFrame {{ background-color: {CARD_BG}; border: 1px solid {BORDER}; "
            f"border-radius: {RADIUS_MD}; padding: 0 12px; }}"
        )
        summary_lay = QHBoxLayout(self._summary_frame)
        summary_lay.setContentsMargins(8, 6, 8, 6)
        summary_lay.setSpacing(16)
        self._summary_labels: list[QLabel] = []
        for name in ["Activities", "Distance", "Elev. Gain", "Avg Pace", "Avg HR"]:
            lbl = QLabel(f"{name}: --")
            lbl.setStyleSheet(
                f"QLabel {{ color: {TEXT_SUBTLE}; font-size: {FONT_SIZE_BASE}; padding: 0; }}"
            )
            summary_lay.addWidget(lbl)
            self._summary_labels.append(lbl)
        summary_lay.addStretch()
        layout.addWidget(self._summary_frame)

        # Personal records (card, same style as summary frame)
        pr_frame = QFrame()
        pr_frame.setStyleSheet(
            f"QFrame {{ background-color: {CARD_BG}; border: 1px solid {BORDER}; "
            f"border-radius: {RADIUS_MD}; padding: 0 12px; }}"
        )
        pr_lay = QHBoxLayout(pr_frame)
        pr_lay.setContentsMargins(8, 6, 8, 6)
        pr_lay.setSpacing(16)
        pr_title = QLabel("🏁 PR")
        pr_title.setStyleSheet(
            f"color: {ACCENT}; font-size: {FONT_SIZE_BASE}; font-weight: 700; padding: 0;"
        )
        pr_lay.addWidget(pr_title)
        self._pr_labels: list[_PRClickLabel] = []
        self._pr_activities: dict[int, Activity | None] = {}
        for idx, dist_km in enumerate(PR_DISTANCES):
            lbl = _PRClickLabel("--:--")
            lbl.setStyleSheet(
                f"color: {TEXT_SUBTLE}; font-size: {FONT_SIZE_SM}; padding: 0;"
            )
            lbl.clicked.connect(self._on_pr_click)
            pr_lay.addWidget(lbl)
            self._pr_labels.append(lbl)
        pr_lay.addStretch()
        layout.addWidget(pr_frame)

        # Activity list (bottom, stretch)
        self._list_model = ActivityListModel()
        self._list_view = ActivityListView()
        self._list_view.set_model(self._list_model)
        self._list_view.activity_clicked.connect(self._on_activity_clicked)
        layout.addWidget(self._list_view, stretch=1)

    # ── signal handlers ──────────────────────────────────────

    def _on_filters_changed(self, filters):
        activities = self._store.filter(**filters)
        self._update(activities)

    def _on_activity_clicked(self, activity: Activity):
        self.activity_selected.emit(activity)

    def _on_pr_click(self, label: _PRClickLabel):
        idx = list(self._pr_labels).index(label)
        activity = self._pr_activities.get(idx)
        if activity:
            self.activity_selected.emit(activity)

    # ── data updates ─────────────────────────────────────────

    def _update(self, activities: list[Activity]):
        self._metrics_map = {}
        for act in activities:
            self._metrics_map[act.id] = self._store.get_metrics(act)
        self._list_model.set_activities(list(reversed(activities)), self._metrics_map)
        self._update_summary(activities)
        self._update_pr(activities)

    def _update_summary(self, activities: list[Activity]):
        if not activities:
            self._summary_labels[0].setText("Activities: 0")
            self._summary_labels[1].setText("Distance: --")
            self._summary_labels[2].setText("Elev. Gain: --")
            self._summary_labels[3].setText("Avg Pace: --:--")
            self._summary_labels[4].setText("Avg HR: --")
            return

        total_dist = 0.0
        total_el_gain = 0.0
        all_paces: list[float] = []
        all_hrs: list[float] = []
        count = len(activities)

        for act in activities:
            m = self._metrics_map.get(act.id, {})
            total_dist += m.get("distance_km", 0)
            total_el_gain += m.get("elevation_gain_m", 0)
            pace = m.get("pace_s_per_km")
            if pace and pace > 0:
                all_paces.append(pace)
            hr = m.get("avg_hr")
            if hr:
                all_hrs.append(hr)

        avg_pace = sum(all_paces) / len(all_paces) if all_paces else 0
        avg_hr = sum(all_hrs) / len(all_hrs) if all_hrs else 0

        hr_str = f"{avg_hr:.0f}" if avg_hr else "--"
        texts = [
            f"Activities: {count}",
            f"Distance: {format_distance_km(total_dist)}",
            f"Elev. Gain: {format_elevation(total_el_gain)}",
            f"Avg Pace: {format_pace(avg_pace)}",
            f"Avg HR: {hr_str}",
        ]
        active_style = (
            f"QLabel {{ color: {ACCENT}; font-size: {FONT_SIZE_BASE}; font-weight: 600; padding: 0; }}"
        )
        for lbl, text in zip(self._summary_labels, texts):
            lbl.setText(text)
            lbl.setStyleSheet(active_style)

    def _update_pr(self, activities: list[Activity]):
        best: dict[float, float] = {}
        best_activity: dict[float, Activity] = {}
        for act in activities:
            splits = compute_best_splits(act.points, PR_DISTANCES)
            for d, t in splits.items():
                if t is not None and (d not in best or t < best[d]):
                    best[d] = t
                    best_activity[d] = act
        for i, dist in enumerate(PR_DISTANCES):
            label = SPLIT_LABELS.get(dist, f"{dist}m")
            if dist in best:
                self._pr_labels[i].setText(f"{label}: {format_time_total(best[dist])}")
                self._pr_labels[i].setStyleSheet(
                    f"color: {ACCENT}; font-size: {FONT_SIZE_SM}; font-weight: 600; padding: 0;"
                )
                self._pr_activities[i] = best_activity[dist]
            else:
                self._pr_labels[i].setText(f"{label}: --")
                self._pr_labels[i].setStyleSheet(
                    f"color: {TEXT_SUBTLE}; font-size: {FONT_SIZE_SM}; padding: 0;"
                )
                self._pr_activities[i] = None
