from __future__ import annotations

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from src.services.config import AppSettings, load_settings, save_settings
from src.ui.theme import ACCENT, FONT_SIZE_BASE, TEXT, TEXT_SUBTLE


class SettingsDialog(QDialog):
    def __init__(self, activity_types: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(520, 280)
        self._activity_types = list(activity_types)
        self._settings = load_settings()
        self._types_list: list[str] = list(self._settings.activity_types)
        self._build_ui()

    # ── UI construction ──────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(12)

        # ── Date range section ───────────────────────────────
        dates_title = QLabel("Date Range")
        dates_title.setStyleSheet(
            f"color: {TEXT}; font-weight: 700; font-size: {FONT_SIZE_BASE};"
        )
        layout.addWidget(dates_title)

        date_row = QHBoxLayout()
        date_row.setSpacing(12)

        self._date_start = QDateEdit()
        self._date_start.setCalendarPopup(True)
        self._date_start.setDate(QDate.currentDate())
        self._date_start.setDisplayFormat("yyyy-MM-dd")
        self._date_start.setMinimumDate(QDate(1990, 1, 1))
        self._date_start.setMaximumDate(QDate.currentDate().addYears(2))
        date_row.addWidget(QLabel("from:"))
        date_row.addWidget(self._date_start, stretch=1)

        self._date_end = QDateEdit()
        self._date_end.setCalendarPopup(True)
        self._date_end.setDate(QDate.currentDate())
        self._date_end.setDisplayFormat("yyyy-MM-dd")
        self._date_end.setMinimumDate(QDate(1990, 1, 1))
        self._date_end.setMaximumDate(QDate.currentDate().addYears(2))
        date_row.addWidget(QLabel("to:"))
        date_row.addWidget(self._date_end, stretch=1)

        self._cb_from = QPushButton("clear")
        self._cb_from.setCheckable(True)
        self._cb_from.toggled.connect(lambda c, e=self._date_start: e.setEnabled(not c))
        self._cb_from.setChecked(True)
        date_row.addWidget(self._cb_from)

        self._cb_to = QPushButton("clear")
        self._cb_to.setCheckable(True)
        self._cb_to.toggled.connect(lambda c, e=self._date_end: e.setEnabled(not c))
        self._cb_to.setChecked(True)
        date_row.addWidget(self._cb_to)

        layout.addLayout(date_row)

        # Restore saved values
        if self._settings.start_date:
            try:
                self._date_start.setDate(QDate.fromString(self._settings.start_date, "yyyy-MM-dd"))
                self._cb_from.setChecked(False)
                self._date_start.setEnabled(True)
            except ValueError:
                pass
        if self._settings.end_date:
            try:
                self._date_end.setDate(QDate.fromString(self._settings.end_date, "yyyy-MM-dd"))
                self._cb_to.setChecked(False)
                self._date_end.setEnabled(True)
            except ValueError:
                pass

        # ── Activity types section ───────────────────────────
        types_title = QLabel("Activity Types to Load")
        types_title.setStyleSheet(
            f"color: {TEXT}; font-weight: 700; font-size: {FONT_SIZE_BASE};"
        )
        layout.addWidget(types_title)

        types_row = QHBoxLayout()
        types_row.setSpacing(6)

        self._cb_all_types = QPushButton("All Types")
        self._cb_all_types.setCheckable(True)
        self._cb_all_types.setFixedWidth(80)
        self._cb_all_types.toggled.connect(self._on_toggle_all_types)
        self._cb_all_types.setChecked(not bool(self._types_list))
        types_row.addWidget(self._cb_all_types)

        self._cb_type_picker = QComboBox()
        self._cb_type_picker.setEditable(True)
        for t in self._activity_types:
            self._cb_type_picker.addItem(t)
        all_types = set(self._activity_types) | set(self._types_list)
        for t in sorted(all_types):
            if t not in self._activity_types:
                self._cb_type_picker.addItem(t)
        types_row.addWidget(self._cb_type_picker, stretch=1)

        self._btn_add = QPushButton("+")
        self._btn_add.setFixedHeight(28)
        self._btn_add.setFixedWidth(28)
        self._btn_add.clicked.connect(self._add_type)
        types_row.addWidget(self._btn_add)

        self._btn_remove = QPushButton("-")
        self._btn_remove.setFixedHeight(28)
        self._btn_remove.setFixedWidth(28)
        self._btn_remove.clicked.connect(self._remove_type)
        types_row.addWidget(self._btn_remove)

        layout.addLayout(types_row)

        self._types_display = QLabel("")
        self._types_display.setStyleSheet(
            f"color: {TEXT_SUBTLE}; font-size: {FONT_SIZE_BASE};"
        )
        self._types_display.setWordWrap(True)
        layout.addWidget(self._types_display)
        self._update_types_display()

        # ── Actions ──────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._btn_cancel = QPushButton("Cancel")
        self._btn_cancel.setFixedHeight(32)
        self._btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(self._btn_cancel)

        self._btn_save = QPushButton("Save")
        self._btn_save.setFixedHeight(32)
        self._btn_save.setStyleSheet(
            f"background-color: {ACCENT}; color: #FFFFFF; "
            f"border: none; border-radius: 4px; padding: 0 24px; "
            f"font-size: {FONT_SIZE_BASE}; font-weight: 600;"
        )
        self._btn_save.clicked.connect(self._save)
        btn_row.addWidget(self._btn_save)

        layout.addLayout(btn_row)

    # ── signal handlers ──────────────────────────────────────

    def _on_toggle_all_types(self, checked: bool):
        if checked:
            self._types_list.clear()
        self._update_types_display()

    def _add_type(self):
        t = self._cb_type_picker.currentText().strip()
        if t and t not in self._types_list:
            self._types_list.append(t)
            self._cb_all_types.setChecked(False)
            self._update_types_display()

    def _remove_type(self):
        t = self._cb_type_picker.currentText().strip()
        if t in self._types_list:
            self._types_list.remove(t)
            self._update_types_display()

    def _update_types_display(self):
        self._cb_all_types.setEnabled(not bool(self._types_list))
        if not self._types_list:
            self._types_display.setText("(all types will be loaded)")
            self._types_display.setStyleSheet(
                f"color: {TEXT_SUBTLE}; font-size: {FONT_SIZE_BASE};"
            )
            self._cb_all_types.setChecked(True)
        else:
            self._types_display.setText(", ".join(self._types_list))
            self._types_display.setStyleSheet(
                f"color: {ACCENT}; font-size: {FONT_SIZE_BASE}; font-weight: 600;"
            )
            self._cb_all_types.setChecked(False)

    # ── save action ──────────────────────────────────────────

    def _save(self):
        settings = AppSettings(
            start_date=(
                self._date_start.date().toString("yyyy-MM-dd")
                if not self._cb_from.isChecked() else None
            ),
            end_date=(
                self._date_end.date().toString("yyyy-MM-dd")
                if not self._cb_to.isChecked() else None
            ),
            activity_types=(
                self._types_list if not self._cb_all_types.isChecked() else []
            ),
        )
        save_settings(settings)
        self.accept()
