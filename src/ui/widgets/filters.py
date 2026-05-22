from __future__ import annotations

from datetime import datetime, timezone

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from src.ui.theme import (
    ACCENT_HOVER,
    BORDER,
    CARD_BG,
    FONT_SIZE_MD,
    RADIUS_MD,
    TEXT,
    TEXT_SUBTLE,
)


class FiltersWidget(QWidget):
    filters_changed = pyqtSignal(object)

    def __init__(self, activity_types: list[str] = [], parent=None):
        super().__init__(parent)
        self._activity_types = list(activity_types)
        self._build_ui()

    def _build_ui(self):
        # Card-style container
        self.setStyleSheet(
            f"QWidget {{ "
            f"background-color: {CARD_BG}; "
            f"border: 1px solid {BORDER}; "
            f"border-radius: {RADIUS_MD}; "
            f"padding: 12px; }}"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Section header
        header = QLabel("Filters")
        header.setStyleSheet(
            f"color: {TEXT}; font-size: 13px; font-weight: 700;"
        )
        layout.addWidget(header)

        layout.addSpacing(4)

        # Type selector
        self._combo_type = QComboBox()
        self._combo_type.addItem("All", None)
        for t in self._activity_types:
            self._combo_type.addItem(t, t)
        layout.addWidget(self._combo_type)

        # Date range
        from_label = QLabel("From")
        from_label.setStyleSheet(
            f"color: {TEXT_SUBTLE}; font-size: 12px;"
        )
        layout.addWidget(from_label)

        self._date_start = QDateEdit()
        self._date_start.setDate(datetime(2020, 1, 1, tzinfo=timezone.utc).date())
        self._date_start.setCalendarPopup(True)
        self._date_start.setDisplayFormat("yyyy-MM-dd")
        layout.addWidget(self._date_start)

        to_label = QLabel("To")
        to_label.setStyleSheet(
            f"color: {TEXT_SUBTLE}; font-size: 12px;"
        )
        layout.addWidget(to_label)

        self._date_end = QDateEdit()
        self._date_end.setDate(datetime.now(tz=timezone.utc).date())
        self._date_end.setCalendarPopup(True)
        self._date_end.setDisplayFormat("yyyy-MM-dd")
        layout.addWidget(self._date_end)

        layout.addStretch()

        # Apply button
        self._btn_apply = QPushButton("🔍  Apply")
        self._btn_apply.clicked.connect(self._apply)
        self._btn_apply.setFixedHeight(32)
        self._btn_apply.setStyleSheet(
            f"QPushButton {{ font-size: {FONT_SIZE_MD}; padding: 0 12px; }}"
            f"QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}"
            f"QPushButton:pressed {{ background-color: #1E3A8A; }}"
        )
        layout.addWidget(self._btn_apply)

    def _apply(self):
        type_key = self._combo_type.currentData()
        active_types = set(self._activity_types) if type_key is None else {type_key}
        start = self._date_start.date().toPyDate()
        end = self._date_end.date().toPyDate()
        filters = {
            "activity_types": active_types,
            "start_date": datetime(start.year, start.month, start.day, tzinfo=timezone.utc),
            "end_date": datetime(end.year, end.month, end.day, 23, 59, 59, tzinfo=timezone.utc),
        }
        self.filters_changed.emit(filters)

    def set_activity_types(self, types: list[str]):
        self._activity_types = list(types)
        self._combo_type.clear()
        self._combo_type.addItem("All", None)
        for t in types:
            self._combo_type.addItem(t, t)
