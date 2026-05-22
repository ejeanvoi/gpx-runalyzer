from __future__ import annotations

import sys

# ── color tokens ───────────────────────────────────────────
BG = "#FFFFFF"
SURFACE = "#F8FAFC"
CARD_BG = "#FFFFFF"
CARD_BORDER = "#E2E8F0"
TEXT = "#1E293B"
TEXT_SUBTLE = "#64748B"
ACCENT = "#2563EB"
ACCENT_LIGHT = "#DBEAFE"
ACCENT_HOVER = "#1D4ED8"
BORDER = "#E2E8F0"
SUCCESS = "#16A34A"
WARNING = "#D97706"
HEADER_BG = "#F1F5F9"
ROW_HOVER = "#EFF6FF"
TAB_INACTIVE = "#94A3B8"


# ── typography ─────────────────────────────────────────────
if sys.platform == "darwin":
    _FONT_FAMILY = '".AppleSystemUIFont", Helvetica, Arial, sans-serif'
elif sys.platform == "win32":
    _FONT_FAMILY = '"Segoe UI", Arial, sans-serif'
else:
    _FONT_FAMILY = '"Ubuntu", "Cantarell", Arial, sans-serif'

# ── dimensions ─────────────────────────────────────────────
RADIUS_SM = "4px"
RADIUS_MD = "8px"
FONT_SIZE_SM = "12px"
FONT_SIZE_BASE = "13px"
FONT_SIZE_MD = "14px"
FONT_SIZE_LG = "16px"
FONT_SIZE_XXL = "24px"

# ── chart series colours ────────────────────────────────────
SERIES_PACE = "#2196F3"
SERIES_ELEV = "#4CAF50"
SERIES_HR   = "#FF5722"
SERIES_VS   = "#9C27B0"


GLOBAL_STYLESHEET = f"""
/* ── global ─────────────────────────────────────────────── */
QWidget {{
    background-color: {SURFACE};
    color: {TEXT};
    font-family: {_FONT_FAMILY};
    font-size: {FONT_SIZE_BASE};
}}

QMainWindow {{
    background-color: {SURFACE};
}}

/* ── labels ─────────────────────────────────────────────── */
QLabel {{
    color: {TEXT};
    font-size: {FONT_SIZE_BASE};
}}

/* ── buttons ────────────────────────────────────────────── */
QPushButton {{
    background-color: {ACCENT};
    color: white;
    border: none;
    border-radius: {RADIUS_SM};
    padding: 8px 16px;
    font-size: {FONT_SIZE_BASE};
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: {ACCENT_HOVER};
}}
QPushButton:pressed {{
    background-color: #1E3A8A;
}}
QPushButton:checked {{
    background-color: {ACCENT_LIGHT};
    color: {ACCENT};
    border: 1.5px solid {ACCENT};
}}
QPushButton:checked:hover {{
    background-color: {ACCENT_LIGHT};
    border-color: {ACCENT_HOVER};
}}
QPushButton:disabled {{
    background-color: {TAB_INACTIVE};
    color: white;
}}

/* ── secondary button (outline) ────────────────────────── */
QPushButton[secondary="true"] {{
    background-color: transparent;
    color: {ACCENT};
    border: 1.5px solid {ACCENT};
}}
QPushButton[secondary="true"]:hover {{
    background-color: {ACCENT_LIGHT};
}}

/* ── combo box ─────────────────────────────────────────── */
QComboBox {{
    background-color: {CARD_BG};
    border: 1.5px solid {BORDER};
    border-radius: {RADIUS_SM};
    padding: 6px 12px;
    min-width: 120px;
    font-size: {FONT_SIZE_BASE};
    color: {TEXT};
}}
QComboBox:hover {{
    border-color: {ACCENT};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox::down-arrow {{
    image: none;
    border: none;
}}
QComboBox QAbstractItemView {{
    background-color: {CARD_BG};
    border: 1.5px solid {BORDER};
    border-radius: {RADIUS_SM};
    selection-background-color: {ACCENT_LIGHT};
    selection-color: {ACCENT};
    outline: none;
    padding: 2px;
}}
QComboBox QAbstractItemView::item {{
    padding: 6px 12px;
}}
QComboBox QAbstractItemView::item:selected {{
    background-color: {ACCENT_LIGHT};
    color: {ACCENT};
    font-weight: 600;
}}

/* ── date edit ─────────────────────────────────────────── */
QDateEdit {{
    background-color: {CARD_BG};
    border: 1.5px solid {BORDER};
    border-radius: {RADIUS_SM};
    padding: 6px 12px;
    font-size: {FONT_SIZE_BASE};
    color: {TEXT};
    min-width: 140px;
}}
QDateEdit:hover {{
    border-color: {ACCENT};
}}
QDateEdit::drop-down {{
    border: none;
}}

/* ── date-edit calendar popup ─────────────────────────── */
QCalendarWidget QTableView {{
    border: none;
    selection-background-color: {ACCENT_LIGHT};
    selection-color: {ACCENT};
}}
QCalendarWidget QToolButton {{
    color: {ACCENT};
    font-weight: 600;
    font-size: {FONT_SIZE_MD};
}}

/* ── spin box / double spin box ───────────────────────── */
QDoubleSpinBox, QSpinBox {{
    background-color: {CARD_BG};
    border: 1.5px solid {BORDER};
    border-radius: {RADIUS_SM};
    padding: 6px 12px;
    font-size: {FONT_SIZE_BASE};
    color: {TEXT};
}}
QDoubleSpinBox:hover, QSpinBox:hover {{
    border-color: {ACCENT};
}}
QDoubleSpinBox::up-button, QSpinBox::up-button,
QDoubleSpinBox::down-button, QSpinBox::down-button {{
    background: transparent;
    border: none;
    width: 20px;
}}

/* ── line edit ─────────────────────────────────────────── */
QLineEdit {{
    background-color: {CARD_BG};
    border: 1.5px solid {BORDER};
    border-radius: {RADIUS_SM};
    padding: 6px 12px;
    font-size: {FONT_SIZE_BASE};
    color: {TEXT};
}}
QLineEdit:hover {{
    border-color: {ACCENT};
}}
QLineEdit:focus {{
    border-color: {ACCENT};
    outline: none;
}}

/* ── slider ───────────────────────────────────────────── */
QSlider::groove:horizontal {{
    border: none;
    height: 6px;
    background: {BORDER};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {ACCENT};
    border: 2px solid white;
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
}}
QSlider::handle:horizontal:hover {{
    background: {ACCENT_HOVER};
}}
QSlider::sub-page:horizontal {{
    background: {ACCENT};
    border-radius: 3px;
}}

/* ── table widget ─────────────────────────────────────── */
QTableWidget {{
    background-color: {CARD_BG};
    border: 1.5px solid {BORDER};
    border-radius: {RADIUS_MD};
    gridline-color: {BORDER};
    selection-background-color: {ACCENT_LIGHT};
    selection-color: {ACCENT};
    font-size: {FONT_SIZE_BASE};
}}
QTableWidget::item {{
    padding: 6px 8px;
    border-bottom: 1px solid {BORDER};
}}
QTableWidget::item:hover {{
    background-color: {ROW_HOVER};
}}
QHeaderView::section {{
    background-color: {HEADER_BG};
    color: {TEXT};
    padding: 8px 12px;
    border: none;
    border-bottom: 2px solid {BORDER};
    font-weight: 600;
    font-size: {FONT_SIZE_SM};
}}
QHeaderView::section:first {{
    border-top-left-radius: {RADIUS_MD};
}}
QHeaderView::section:last {{
    border-top-right-radius: {RADIUS_MD};
}}

/* ── list view ────────────────────────────────────────── */
QListView {{
    background-color: {CARD_BG};
    border: 1.5px solid {BORDER};
    border-radius: {RADIUS_MD};
    outline: none;
    font-size: {FONT_SIZE_BASE};
}}
QListView::item {{
    padding: 8px 12px;
    border-bottom: 1px solid {BORDER};
}}
QListView::item:hover {{
    background-color: {ROW_HOVER};
}}
QListView::item:selected {{
    background-color: {ACCENT_LIGHT};
    color: {ACCENT};
}}

/* ── scroll bar ───────────────────────────────────────── */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: #CBD5E1;
}}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: none;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER};
    border-radius: 4px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background: #CBD5E1;
}}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0;
}}
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {{
    background: none;
}}

/* ── tab widget ───────────────────────────────────────── */
QTabBar::tab {{
    background-color: transparent;
    color: {TEXT_SUBTLE};
    padding: 8px 16px;
    border-bottom: 2px solid transparent;
    font-size: {FONT_SIZE_BASE};
    font-weight: 500;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background-color: transparent;
    color: {ACCENT};
    border-bottom: 2px solid {ACCENT};
    font-weight: 600;
}}
QTabBar::tab:hover:!selected {{
    color: {TEXT};
}}

/* ── checkbox ─────────────────────────────────────────── */
QCheckBox {{
    color: {TEXT};
    font-size: {FONT_SIZE_BASE};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid {BORDER};
    background: {CARD_BG};
}}
QCheckBox::indicator:checked {{
    background-color: {ACCENT};
    border-color: {ACCENT};
}}
QCheckBox::indicator:hover {{
    border-color: {ACCENT};
}}

/* ── progress bar ─────────────────────────────────────── */
QProgressBar {{
    background-color: {BORDER};
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background-color: {ACCENT};
    border-radius: 4px;
}}

/* ── message box ──────────────────────────────────────── */
QMessageBox {{
    background-color: {CARD_BG};
}}
QMessageBox QLabel {{
    color: {TEXT};
    font-size: {FONT_SIZE_BASE};
}}

/* ── file dialog ──────────────────────────────────────── */
QFileDialog {{
    background-color: {CARD_BG};
}}
"""


def apply_theme(widget) -> None:
    """Apply the global light theme stylesheet to a widget."""
    widget.setStyleSheet(GLOBAL_STYLESHEET)
