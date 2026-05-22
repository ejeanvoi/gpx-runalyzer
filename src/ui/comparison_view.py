from __future__ import annotations

import pyqtgraph as pg
from PyQt6.QtCore import QRectF, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.analysis.comparison import ComparisonEntry, build_comparison_with_reference
from src.analysis.route_similarity import find_similar_routes
from src.ui import formatting, theme
from src.ui.theme import ACCENT, TEXT

pg.setConfigOption("background", "w")
pg.setConfigOption("foreground", TEXT[:7])


def _short_name(name: str, max_len: int = 10) -> str:
    name = name or ""
    return name[:max_len] if len(name) <= max_len else name[:max_len - 1] + "…"


class _RotatedAxisItem(pg.AxisItem):
    """AxisItem that rotates tick labels by a given angle (degrees)."""

    def __init__(self, *args, tick_rotation: float = 90, **kwargs):
        self._tick_rotation = tick_rotation
        super().__init__(*args, **kwargs)

    def drawPicture(self, p, axisSpec, tickSpecs, textSpecs):
        p.setRenderHint(p.RenderHint.Antialiasing, False)
        p.setRenderHint(p.RenderHint.TextAntialiasing, True)
        pen, p1, p2 = axisSpec
        p.setPen(pen)
        p.drawLine(p1, p2)
        for pen, pt1, pt2 in tickSpecs:
            p.setPen(pen)
            p.drawLine(pt1, pt2)
        if self.style["tickFont"] is not None:
            p.setFont(self.style["tickFont"])
        p.setPen(self.textPen())
        bounding = self.boundingRect().toAlignedRect()
        p.setClipRect(bounding)
        for rect, flags, text in textSpecs:
            p.save()
            cx = rect.center().x()
            cy = rect.center().y()
            p.translate(cx, cy)
            p.rotate(self._tick_rotation)
            p.drawText(
                QRectF(0, 0, rect.height(), rect.width()),
                int(flags),
                text,
            )
            p.restore()


class ComparisonView(QWidget):
    go_to_activity = pyqtSignal(object)

    def __init__(self, store, activities: list, parent=None):
        super().__init__(parent)
        self._store = store
        self._all_activities = activities
        self._threshold = 0.5
        self._build_ui()

    # ── UI construction ────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(self._controls_widget())

        self._table = QTableWidget()
        self._table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._table.setSelectionMode(
            QTableWidget.SelectionMode.ExtendedSelection
        )
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        self._table.itemDoubleClicked.connect(self._on_row_double_click)
        layout.addWidget(self._table, stretch=1)

        bottom_axis = _RotatedAxisItem("bottom")
        bottom_axis.setLabel("Date", color=TEXT, size="bold 11")
        self._plot = pg.PlotWidget(axisItems={"bottom": bottom_axis})
        self._plot.setBackground("#FFFFFF")
        self._plot.setLabel("left", "Normalised")
        self._plot.setLabel("bottom", "")
        self._plot.showGrid(x=True, y=True, alpha=0.2)
        layout.addWidget(self._plot, stretch=1)

        self._reference: object = None
        self._entries: list[ComparisonEntry] = []

    def _controls_widget(self) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 4)

        lay.addWidget(QLabel("Similarity threshold:"))

        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(0, 100)
        self._slider.setSingleStep(5)
        self._slider.setValue(50)
        self._slider.valueChanged.connect(self._on_slider_changed)
        lay.addWidget(self._slider, stretch=1)

        self._threshold_label = QLabel("50%")
        self._threshold_label.setMinimumWidth(48)
        self._threshold_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._threshold_label.setStyleSheet(
            f"QLabel {{ color: {ACCENT}; font-weight: 600; font-size: 13px; }}"
        )
        lay.addWidget(self._threshold_label)

        self._btn_find = QPushButton("Find Similar")
        self._btn_find.clicked.connect(self._on_find)
        lay.addWidget(self._btn_find)

        self._btn_reset = QPushButton("Reset")
        self._btn_reset.setProperty("secondary", True)
        self._btn_reset.clicked.connect(self._on_reset)
        lay.addWidget(self._btn_reset)

        lay.addStretch()
        return w

    def _on_slider_changed(self, value: int):
        self._threshold = value / 100
        self._threshold_label.setText(f"{value}%")

    # ── public API ─────────────────────────────────────────

    def set_reference(self, activity):
        self._reference = activity
        self._on_find()

    # ── actions ────────────────────────────────────────────

    def _on_find(self):
        if not self._reference:
            return
        self._threshold = self._slider.value() / 100
        similar = find_similar_routes(
            self._all_activities,
            self._reference,
            self._threshold,
        )
        self._entries = build_comparison_with_reference(
            self._reference, similar, metrics_getter=self._store.get_metrics
        )
        self._update_table()
        self._update_chart()

    def _on_reset(self):
        self._slider.setValue(50)
        self._threshold = 0.5
        self._on_find()

    def _on_selection_changed(self):
        self._update_chart()

    def _get_selected_entries(self) -> list[ComparisonEntry]:
        rows = sorted({item.row() for item in self._table.selectedItems()})
        if not rows:
            return list(self._entries)
        return [self._entries[r] for r in rows if r < len(self._entries)]

    # ── table ──────────────────────────────────────────────

    def _update_table(self):
        headers = [
            "Date", "Name", "Dist (km)", "Pace /km",
            "Elev. Gain (m)", "Avg HR", "Max HR", "Similarity",
        ]
        self._table.setColumnCount(len(headers))
        self._table.setHorizontalHeaderLabels(headers)
        self._table.setRowCount(len(self._entries))

        for i, entry in enumerate(self._entries):
            act = entry.activity
            self._table.setItem(
                i, 0, QTableWidgetItem(act.date.strftime("%Y-%m-%d"))
            )
            self._table.setItem(i, 1, QTableWidgetItem(act.name))
            self._table.setItem(
                i, 2, QTableWidgetItem(
                    formatting.format_distance_km(entry.distance_km)
                )
            )
            self._table.setItem(
                i, 3, QTableWidgetItem(
                    formatting.format_pace(entry.pace_s_per_km)
                )
            )
            self._table.setItem(
                i, 4, QTableWidgetItem(
                    formatting.format_elevation(entry.elevation_gain_m)
                )
            )
            self._table.setItem(
                i, 5, QTableWidgetItem(
                    f"{entry.avg_hr:.0f}" if entry.avg_hr else "--"
                )
            )
            self._table.setItem(
                i, 6, QTableWidgetItem(
                    f"{entry.max_hr:.0f}" if entry.max_hr else "--"
                )
            )

            self._table.setItem(
                i, 7, QTableWidgetItem(_similarity_label(entry.similarity))
            )

        self._table.resizeColumnsToContents()
        self._table.horizontalHeader().setStretchLastSection(True)

    def _normalise(self, data: list[float]) -> list[float]:
        valid = [v for v in data if v is not None and v > 0]
        if not valid:
            return [0.0] * len(data)
        mx = max(valid)
        return [v / mx if v and v > 0 else 0.0 for v in data]

    # ── chart ──────────────────────────────────────────────

    def _update_chart(self):
        self._plot.clear()
        self._plot.setBackground(theme.CARD_BG)
        self._plot.showGrid(x=True, y=True, alpha=0.2)

        entries = self._get_selected_entries()
        if not entries:
            return

        pi = self._plot.getPlotItem()
        n = len(entries)
        dates = [e.activity.date.strftime("%Y-%m-%d") for e in entries]
        x = list(range(n))
        bw = 0.25

        dist_vals = self._normalise([e.distance_km for e in entries])
        pace_vals = self._normalise([e.pace_s_per_km for e in entries])
        elev_vals = self._normalise([e.elevation_gain_m for e in entries])

        from pyqtgraph import BarGraphItem
        pi.addItem(BarGraphItem(x=x, y=[0]*n, y1=dist_vals, width=bw,
            brush=pg.mkBrush(theme.ACCENT), pen=pg.mkPen(theme.ACCENT, width=1), name="Distance"))
        pi.addItem(BarGraphItem(x=[xi + bw + 0.02 for xi in x], y=[0]*n, y1=pace_vals, width=bw,
            brush=pg.mkBrush(theme.SUCCESS), pen=pg.mkPen(theme.SUCCESS, width=1), name="Pace s/km"))
        pi.addItem(BarGraphItem(x=[xi + 2*(bw + 0.02) for xi in x], y=[0]*n, y1=elev_vals, width=bw,
            brush=pg.mkBrush(theme.WARNING), pen=pg.mkPen(theme.WARNING, width=1), name="Elev. m"))

        self._plot.getAxis("bottom").setTicks([list(zip(x, dates)), []])
        leg = self._plot.addLegend()
        leg.setParentItem(self._plot.getPlotItem().vb)
        leg.anchor((1, 0), (1, 0), offset=(-10, 10))
        self._plot.setYRange(0, 1.05)

    # ── signals ────────────────────────────────────────────

    def _on_row_double_click(self, item):
        row = item.row()
        if row < len(self._entries):
            self.go_to_activity.emit(self._entries[row].activity)


def _similarity_label(similarity: float) -> str:
    pct = f"{similarity:.0%}"
    if similarity >= 0.8:
        return f"🟢 {pct}"
    if similarity >= 0.5:
        return f"🟡 {pct}"
    return f"🟠 {pct}"
