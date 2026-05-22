from __future__ import annotations

from PyQt6.QtCore import QAbstractListModel, QModelIndex, Qt, pyqtSignal
from PyQt6.QtWidgets import QListView

from src.models.activity import Activity
from src.ui.formatting import format_duration, format_pace


class ActivityListModel(QAbstractListModel):
    activity_clicked = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._activities: list[Activity] = []
        self._metrics_map: dict[str, dict] = {}

    def set_activities(self, activities: list[Activity], metrics_map: dict):
        self.beginResetModel()
        self._activities = activities
        self._metrics_map = metrics_map
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self._activities)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        row = index.row()
        if row < 0 or row >= len(self._activities):
            return None
        act = self._activities[row]
        m = self._metrics_map.get(act.id, {})
        return self._format_row(act, m)

    def _format_row(self, act: Activity, m: dict) -> str:
        date_str = act.date.strftime("%Y-%m-%d %H:%M")
        dist_km = m.get("distance_km", 0)
        pace = format_pace(m.get("pace_s_per_km", 0))
        el_gain = m.get("elevation_gain_m", 0)
        avg_hr = m.get("avg_hr")
        hr_str = f"{avg_hr:.0f}" if avg_hr else "--"
        moving = m.get("moving")
        time_str = format_duration(moving) if moving else "--:--"
        return (
            f"{date_str}  |  {act.name}  |  {act.activity_type}  |  "
            f"{dist_km:.2f} km  |  {pace}/km  |  "
            f"{el_gain:.0f} m+  |  HR: {hr_str}  |  {time_str}"
        )

    def activity_at(self, row: int) -> Activity | None:
        if 0 <= row < len(self._activities):
            return self._activities[row]
        return None


class ActivityListView(QListView):
    activity_clicked = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = None
        self.setSelectionMode(QListView.SelectionMode.SingleSelection)

    def set_model(self, model: ActivityListModel):
        self._model = model
        super().setModel(model)
        self.doubleClicked.connect(self._on_double_click)

    def _on_double_click(self, index):
        act = self._model.activity_at(index.row())
        if act:
            self.activity_clicked.emit(act)
