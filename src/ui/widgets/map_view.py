from __future__ import annotations

import json

from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.models.activity import Activity
from src.ui import theme

MAP_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body { margin: 0; padding: 0; }
        #map { width: 100%; height: 100vh; }
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        var map = L.map('map').setView([0, 0], 12);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(map);
        var routeLayer = null;
        window.handleData = function(data) {
            if (data && data.coords) {
                if (routeLayer) map.removeLayer(routeLayer);
                var geojson = {
                    type: 'Feature',
                    geometry: {
                        type: 'LineString',
                        coordinates: data.coords
                    }
                };
                routeLayer = L.geoJSON(geojson, {
                    style: { color: '#e74c3c', weight: 4 }
                }).addTo(map);
                if (data.bounds) {
                    var sw = L.latLng(data.bounds[0], data.bounds[1]);
                    var ne = L.latLng(data.bounds[2], data.bounds[3]);
                    map.fitBounds(L.latLngBounds(sw, ne), { padding: [30, 30] });
                }
            }
        };
    </script>
</body>
</html>"""


class MapView(QWidget):
    """Map widget with header label overlay and rounded-card styling."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._header_label = QLabel("Route Map")
        self._header_label.setStyleSheet(
            f"font-size: 14px; font-weight: 700; color: {theme.TEXT}; "
            f"padding: 8px 12px 4px 12px;"
        )
        layout.addWidget(self._header_label)

        self._view = QWebEngineView()
        self._view.setStyleSheet(
            f"border: 1.5px solid {theme.CARD_BORDER}; "
            f"border-radius: {theme.RADIUS_MD}; "
            f"background-color: {theme.CARD_BG};"
        )
        layout.addWidget(self._view)

        self.setStyleSheet(
            f"QWidget {{ background-color: {theme.CARD_BG}; "
            f"border: 1.5px solid {theme.CARD_BORDER}; "
            f"border-radius: {theme.RADIUS_MD}; }}"
        )

        self._initialized = False
        self._pending_data = None
        self._view.page().loadFinished.connect(self._on_load_finished)
        self._view.setHtml(MAP_HTML, QUrl("https://unpkg.com"))

    def set_activity_name(self, name: str) -> None:
        """Update the header label with the activity name."""
        self._header_label.setText(name or "Route Map")

    def _on_load_finished(self, ok: bool):
        if not ok:
            return
        if self._initialized:
            return
        self._initialized = True
        if self._pending_data:
            data = self._pending_data
            self._pending_data = None
            self._inject(data)

    def set_route(self, activity: Activity):
        if not activity.points:
            return
        coords = [[p.lon, p.lat] for p in activity.points]
        bounds = [
            min(p.lat for p in activity.points),
            min(p.lon for p in activity.points),
            max(p.lat for p in activity.points),
            max(p.lon for p in activity.points),
        ]
        data = json.dumps({"coords": coords, "bounds": bounds})
        if self._initialized:
            self._inject(data)
        else:
            self._pending_data = data

    def _inject(self, data: str):
        js = f"window.handleData({data});"
        self._view.page().runJavaScript(js)
