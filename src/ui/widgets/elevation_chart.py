from __future__ import annotations

import bisect

import pyqtgraph as pg
from PyQt6.QtCore import QEvent, QPoint, Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.models.activity import Activity
from src.models.metrics import compute_cumulative_data
from src.ui import formatting, theme


class _TooltipItem(pg.TextItem):
    def __init__(self):
        super().__init__(
            text="",
            color=pg.mkColor(20, 20, 20),
            fill=pg.mkBrush(255, 255, 255, 240),
            border=pg.mkPen(100, 100, 100, 180),
        )
        self.setFont(QFont("SF Mono", 9))
        self.setAnchor((0, 0))


class SeriesChart(QWidget):
    """Time-series chart with dual Y axes, crosshair tooltip, and toggleable series.

    Alias as ElevationChart in the import that uses it.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._distances: list[float] = []
        self._plot = pg.PlotWidget()
        self._plot.setBackground("w")
        self._plot.hideButtons()
        self._plot.setMouseEnabled(x=True, y=False)
        self._plot.setStyleSheet(
            f"background-color: white; border: 1.5px solid {theme.CARD_BORDER}; "
            f"border-radius: {theme.RADIUS_MD};"
        )
        left_axis = pg.AxisItem(
            "left", pen={"color": (33, 150, 243), "width": 2}
        )
        left_axis.setLabel("", color=theme.TEXT, size=f"bold {theme.FONT_SIZE_SM}")
        right_axis = pg.AxisItem(
            "right", pen={"color": (128, 128, 128), "width": 1}
        )
        right_axis.setLabel(
            "Elev (m) / HR (bpm) / VS (m/h)",
            color=theme.TEXT_SUBTLE,
            size=f"{theme.FONT_SIZE_SM}",
        )
        bottom_axis = pg.AxisItem("bottom")
        bottom_axis.setLabel("Distance (km)", color=theme.TEXT, size=f"bold {theme.FONT_SIZE_SM}")
        right_axis.setPen(pg.mkPen(0, 0, 0, 0))
        self._plot.setAxisItems(
            {
                "bottom": bottom_axis,
                "left": left_axis,
                "right": right_axis,
            }
        )
        self._plot.showGrid(x=True, y=True, alpha=0.15)
        self._curves: dict = {}
        self._checkboxes: dict = {}
        vb: pg.ViewBox = self._plot.getPlotItem().vb
        vb.setLimits(xMin=0)
        self._vb = vb
        self._vrub = pg.InfiniteLine(
            angle=90,
            movable=False,
            pen=pg.mkPen(120, 120, 120, 160, style=Qt.PenStyle.DashLine),
        )
        self._vrub.setZValue(100)
        self._vrub.hide()
        self._plot.addItem(self._vrub)
        self._tooltip = _TooltipItem()
        vb.addItem(self._tooltip)
        self._tooltip.setZValue(200)
        self._plot.viewport().installEventFilter(self)
        self._destroyed = False

        # ── controls row with "Layers:" header ──
        ctrl_lay = QHBoxLayout()
        ctrl_lay.setContentsMargins(2, 2, 2, 2)
        ctrl_lay.setSpacing(12)

        layers_hdr = QLabel("Layers:")
        layers_hdr.setStyleSheet(
            f"color: {theme.TEXT_SUBTLE}; font-size: {theme.FONT_SIZE_SM}; "
            f"font-weight: 700; padding-right: 4px;"
        )
        ctrl_lay.addWidget(layers_hdr)
        ctrl_lay.addSpacing(4)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)
        layout.addLayout(ctrl_lay)
        layout.addWidget(self._plot)

        self._register(
            "Pace", QColor(33, 150, 243), "left", checked=True, parent=ctrl_lay
        )
        self._register(
            "Elevation",
            QColor(76, 175, 80),
            "left",
            checked=False,
            parent=ctrl_lay,
        )
        self._register(
            "Heart Rate",
            QColor(255, 87, 34),
            "left",
            checked=False,
            parent=ctrl_lay,
        )
        self._register(
            "Vertical Speed",
            QColor(156, 39, 176),
            "left",
            checked=False,
            parent=ctrl_lay,
        )
        ctrl_lay.addStretch()
        self._btn_reset_x = QPushButton("🔄 Reset X")
        self._btn_reset_x.setFixedHeight(24)
        self._btn_reset_x.clicked.connect(self._on_reset_x)
        self._btn_reset_x.setStyleSheet(
            f"QPushButton {{ "
            f"background-color: transparent; "
            f"color: {theme.TEXT}; "
            f"border: 1px solid {theme.CARD_BORDER}; "
            f"border-radius: {theme.RADIUS_SM}; "
            f"padding: 2px 8px; "
            f"font-size: {theme.FONT_SIZE_SM}; "
            f"}} QPushButton:hover {{ "
            f"background-color: {theme.CARD_BORDER}; "
            f"}}"
        )
        ctrl_lay.addWidget(self._btn_reset_x)
        self._x_max = 0.0

    def _register(
        self, name: str, qcolor: QColor, axis: str, checked: bool, parent: QHBoxLayout
    ):
        pen = pg.mkPen(qcolor, width=2)
        sym = "o" if name == "Heart Rate" else None
        curve = self._plot.plot(
            pen=pen, symbol=sym, symbolSize=3, symbolPen=pg.mkPen(qcolor, width=1)
        )
        if axis == "right":
            curve.setZValue(1)
        cb = QCheckBox(f"  {name}")
        cb.setChecked(checked)
        cb.stateChanged.connect(lambda s, n=name: self._on_toggle(n, s))
        parent.addWidget(cb)
        self._curves[name] = {
            "curve": curve,
            "visible": checked,
            "axis": axis,
            "data": [],
            "norm": [],
            "color": qcolor,
        }
        self._checkboxes[name] = cb
        curve.setVisible(checked)

    def _on_toggle(self, name: str, state: int):
        entry = self._curves[name]
        vis = state == Qt.CheckState.Checked.value
        entry["visible"] = vis
        entry["curve"].setVisible(vis)
        if vis:
            self._render_series(name)
        else:
            entry["curve"].clear()
            entry["norm"] = []
        self._plot.setYRange(-0.05, 1.05)

    def _on_reset_x(self):
        if self._x_max > 0:
            self._plot.setXRange(0, self._x_max)

    def _normalise(self, data: list[float]) -> list[float]:
        valid = [v for v in data if v is not None]
        if not valid:
            return [0.5] * len(data)
        mn = min(valid)
        mx = max(valid)
        span = mx - mn if mx != mn else 1.0
        return [(v - mn) / span if v is not None else None for v in data]

    def _render_series(self, name: str):
        entry = self._curves[name]
        x = self._distances
        y = entry["data"]
        normed = self._normalise(y)
        entry["norm"] = normed
        if name == "Heart Rate":
            xr = [x[i] for i in range(len(normed)) if normed[i] is not None]
            yr = [v for v in normed if v is not None]
            entry["curve"].setData(xr, yr)
        else:
            entry["curve"].setData(x, normed)

    def set_activity(self, activity: Activity):
        if not activity.points:
            return
        cumulative = compute_cumulative_data(activity.points)
        self._distances = cumulative["distances"]
        pace_raw = cumulative["pace_per_km"]
        pace_min = [p / 60 for p in pace_raw]
        series_map = {
            "Pace": pace_min,
            "Elevation": cumulative["elevations"],
            "Heart Rate": cumulative["hr_values"],
            "Vertical Speed": cumulative["vs_values"],
        }
        self._plot.disableAutoRange()
        for name, data in series_map.items():
            entry = self._curves[name]
            entry["data"] = data
            if entry["visible"]:
                self._render_series(name)
        self._plot.enableAutoRange()
        self._plot.autoRange()
        self._plot.setYRange(-0.05, 1.05)
        if self._distances:
            self._x_max = self._distances[-1]

    def _interpolate_at(self, data: list[float], x_dist: float) -> float | None:
        if not self._distances or not data:
            return None
        n = len(self._distances)
        if x_dist <= self._distances[0]:
            return data[0] if data[0] is not None else None
        if x_dist >= self._distances[-1]:
            return data[-1] if data[-1] is not None else None
        idx = bisect.bisect_right(self._distances, x_dist)
        lo = idx - 1
        hi = idx
        if hi >= n:
            hi = n - 1
        y_lo = data[lo]
        y_hi = data[hi]
        if y_lo is None or y_hi is None:
            return y_lo if y_lo is not None else y_hi
        x0, x1 = self._distances[lo], self._distances[hi]
        if x1 == x0:
            return y_hi
        t = (x_dist - x0) / (x1 - x0)
        return y_lo + t * (y_hi - y_lo)

    def _fmt_pace(self, v: float) -> str:
        if v is None:
            return "--:--"
        return f"{formatting.format_pace(v * 60)} /km"

    def _handle_mouse(self, sp):
        if self._destroyed or not self._distances:
            return
        view_pos = self._vb.mapSceneToView(sp)
        x = view_pos.x()
        vr = self._vb.viewRange()
        x_min, x_max = vr[0]
        if x < x_min or x > x_max:
            self._hide_tooltip()
            return
        self._vrub.setPos(x)
        self._vrub.show()
        parts = [f"\u23f8 {x:.3f} km"]
        for name, entry in self._curves.items():
            if not entry["visible"]:
                continue
            val = self._interpolate_at(entry["data"], x)
            if val is None:
                parts.append(f"\u2022 {name}: --")
                continue
            if name == "Pace":
                parts.append(f"\u2022 Pace: {self._fmt_pace(val)}")
            elif name == "Elevation":
                parts.append(f"\u2022 Elev: {val:.1f} m")
            elif name == "Heart Rate":
                parts.append(f"\u2022 HR: {val:.0f} bpm")
            elif name == "Vertical Speed":
                parts.append(f"\u2022 VS: {val:.1f} m/h")
        self._tooltip.setText("\n".join(parts))
        self._position_tooltip(sp)

    def _position_tooltip(self, sp):
        vr = self._vb.viewRange()
        x_min, x_max = vr[0]
        y_min, y_max = vr[1]
        x_span = x_max - x_min
        y_span = y_max - y_min
        pixel_margin_x = 0.02 * x_span
        pixel_margin_y = 0.03 * y_span
        view_pos = self._vb.mapSceneToView(sp)
        tx = view_pos.x() + pixel_margin_x
        ty = view_pos.y() - pixel_margin_y
        if tx + 0.05 * x_span > x_max:
            tx = view_pos.x() - 0.07 * x_span
        if ty < y_min + 0.02 * y_span:
            ty = view_pos.y() + pixel_margin_y
        self._tooltip.setPos(tx, ty)

    def _hide_tooltip(self):
        self._vrub.hide()
        self._tooltip.setText("")

    def eventFilter(self, obj, event) -> bool:
        if obj is self._plot.viewport():
            et = event.type()
            if et == QEvent.Type.MouseMove:
                pos = event.position()
                wp = QPoint(int(pos.x()), int(pos.y()))
                sp = self._plot.mapToScene(wp)
                self._handle_mouse(sp)
            elif et == QEvent.Type.Leave:
                self._hide_tooltip()
        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        self._destroyed = True
        self._hide_tooltip()
        super().closeEvent(event)

    def deleteLater(self):
        self._destroyed = True
        super().deleteLater()
