from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.ui.theme import (
    ACCENT,
    BORDER,
    CARD_BG,
    FONT_SIZE_LG,
    TEXT_SUBTLE,
    apply_theme,
)


class MainWindow(QMainWindow):
    def __init__(self, root_folder: str | None = None):
        super().__init__()
        self.setWindowTitle("GPX Runalyzer")
        self.resize(1200, 800)
        self._root_folder = Path(root_folder) if root_folder else None
        self._store = None
        self._current_view = "loading"
        apply_theme(self)
        self._create_actions()
        self._create_ui()
        self._load_data()

    def _create_actions(self):
        back_action = QAction("\u2190 Dashboard", self)
        back_action.setShortcut(Qt.Key.Key_Escape)
        back_action.setToolTip("Back to Dashboard")
        back_action.triggered.connect(self._go_dashboard)
        self.addAction(back_action)
        self._back_action = back_action

    def _create_ui(self):
        from PyQt6.QtWidgets import QLabel, QStackedWidget

        central = QWidget()
        self._central_layout = QVBoxLayout(central)
        self._central_layout.setContentsMargins(0, 0, 0, 0)
        self._central_layout.setSpacing(0)

        # ── Nav bar ───────────────────────────────────────
        self._nav_bar = QWidget()
        self._nav_bar.setStyleSheet(
            f"background-color: {CARD_BG}; border-bottom: 1px solid {BORDER}; min-height: 48px;"
        )
        nav_layout = QHBoxLayout(self._nav_bar)
        nav_layout.setContentsMargins(16, 8, 16, 8)
        nav_layout.setSpacing(12)

        # Left: app title + settings
        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        self._title_label = QLabel("GPX Runalyzer")
        self._title_label.setStyleSheet(
            f"color: {ACCENT}; font-size: {FONT_SIZE_LG}; font-weight: 700;"
        )
        title_row.addWidget(self._title_label)

        self._btn_settings = QPushButton("⚙️")
        self._btn_settings.setToolTip("Settings")
        self._btn_settings.setFixedHeight(32)
        self._btn_settings.setMinimumWidth(32)
        self._btn_settings.setStyleSheet(
            f"QPushButton {{ "
            f"background-color: transparent; border: none; "
            f"font-size: 18px; padding: 0 4px; }}"
            f"QPushButton:hover {{ background-color: {BORDER}; border-radius: 4px; }}"
            f"QPushButton:pressed {{ background-color: #CBD5E1; border-radius: 4px; }}"
        )
        self._btn_settings.clicked.connect(self._show_settings)
        self._btn_settings.setVisible(False)
        title_row.addWidget(self._btn_settings)

        nav_layout.addLayout(title_row)

        # Center: stretch
        nav_layout.addStretch()

        # Right: data folder status
        self._folder_label = QLabel("")
        self._folder_label.setStyleSheet(
            f"color: {TEXT_SUBTLE}; font-size: 12px;"
        )
        self._folder_label.setMaximumWidth(320)
        self._folder_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        nav_layout.addWidget(self._folder_label)

        # Back button (right-side, before stretch takes over)
        self._back_button = QPushButton("\u2190")
        self._back_button.setToolTip("Back to Dashboard")
        self._back_button.setFixedHeight(32)
        self._back_button.setMinimumWidth(32)
        self._back_button.setStyleSheet(
            f"background-color: {ACCENT}; color: #FFFFFF; "
            f"border: none; border-radius: 20px; padding: 0 12px; "
            f"font-size: 14px;"
        )
        self._back_button.clicked.connect(self._go_dashboard)
        self._back_button.setVisible(False)
        nav_layout.insertWidget(nav_layout.count() - 1, self._back_button)

        self._central_layout.addWidget(self._nav_bar)

        # ── Stacked views ─────────────────────────────────
        self._stack = QStackedWidget()

        loading = QWidget()
        lay = QVBoxLayout(loading)
        self._loading_label = QLabel("Loading GPX files...")
        self._loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._loading_label)
        self._stack.addWidget(loading)
        self._loading_idx = 0

        self._central_layout.addWidget(self._stack)
        self.setCentralWidget(central)

        # ── Status bar ────────────────────────────────────
        sb = self.statusBar()
        sb.showMessage("Ready")

    def _update_back_button(self):
        show = self._current_view in ("detail", "comparison")
        self._back_button.setVisible(show)

    def _load_data(self):
        from src.services.config import load_settings
        from src.services.store import ActivityStore
        if self._root_folder and self._root_folder.exists():
            self._store = ActivityStore(self._root_folder)
            self._store.load()
            settings = load_settings()
            self._store.apply_load_filters(settings)
            self._init_views()
        else:
            self._show_folder_dialog()

    def _reload_data(self):
        if self._store and self._root_folder:
            self._store.load()
            from src.services.config import load_settings
            settings = load_settings()
            self._store.apply_load_filters(settings)
            # Re-init views with updated data
            self._stack.setCurrentWidget(self._dashboard)
            self._current_view = "dashboard"
            self._update_back_button()
            self._update_status()

    def _show_folder_dialog(self):
        from PyQt6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, "Select GPX Root Folder")
        if folder:
            self._root_folder = Path(folder)
            from src.services.config import load_settings
            from src.services.store import ActivityStore
            self._store = ActivityStore(self._root_folder)
            self._store.load()
            settings = load_settings()
            self._store.apply_load_filters(settings)
            self._init_views()
        else:
            QMessageBox.warning(self, "No Folder", "Please select a folder containing GPX activity subfolders.")

    def _init_views(self):
        from src.ui.activity_detail import ActivityDetailView
        from src.ui.comparison_view import ComparisonView
        from src.ui.dashboard import DashboardView

        self._dashboard = DashboardView(self._store)
        self._dashboard.activity_selected.connect(self._show_detail)
        self._dashboard.compare_route_requested.connect(self._show_comparison_from)

        self._detail = ActivityDetailView(self._store)
        self._detail.compare_route_requested.connect(self._show_comparison_from)

        self._comparison = ComparisonView(self._store, self._store.get_all())
        self._comparison.go_to_activity.connect(self._show_detail)

        self._stack.addWidget(self._dashboard)
        self._stack.addWidget(self._detail)
        self._stack.addWidget(self._comparison)
        self._stack.setCurrentWidget(self._dashboard)
        self._current_view = "dashboard"
        self._update_back_button()
        self._update_status()
        self._btn_settings.setVisible(True)

    def _update_status(self):
        if self._store is None:
            return
        count = len(self._store.get_all())
        folder_str = str(self._root_folder) if self._root_folder else ""
        # Truncate folder path with ellipsis if too long
        if len(folder_str) > 40:
            folder_str = "..." + folder_str[-37:]
        status_text = f"{count} activities loaded"
        if folder_str:
            status_text += f"  |  {folder_str}"
        self.statusBar().showMessage(status_text)

        # Update nav bar folder label
        if self._root_folder:
            display = str(self._root_folder)
            if len(display) > 40:
                display = "..." + display[-37:]
            self._folder_label.setText(display)

    def _show_detail(self, activity):
        self._detail.set_activity(activity)
        self._stack.setCurrentWidget(self._detail)
        self._current_view = "detail"
        self._update_back_button()
        self._update_status()

    def _show_comparison_from(self, reference_activity):
        self._comparison.set_reference(reference_activity)
        self._stack.setCurrentWidget(self._comparison)
        self._current_view = "comparison"
        self._update_back_button()
        self._update_status()

    def _go_dashboard(self):
        if self._dashboard is not None:
            self._current_view = "dashboard"
            self._stack.setCurrentWidget(self._dashboard)
            self._update_back_button()
            self._update_status()

    def _show_settings(self):
        from PyQt6.QtWidgets import QDialog

        from src.ui.settings_dialog import SettingsDialog
        types = self._store.activity_types if self._store else []
        dialog = SettingsDialog(types, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._reload_data()
