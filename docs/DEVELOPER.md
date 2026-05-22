# Developer Documentation

## Architecture Overview

The application follows a layered architecture:

```
src/main.py                         Entry point, CLI argument parsing
src/ui/                             PyQt6 views and widgets
  main_window.py                    QMainWindow with stacked views (loading, dashboard, detail, comparison)
  dashboard.py                      Summary bar, PR labels, filters, activity list
  activity_detail.py                Map, elevation chart, metric cards, split times
  comparison_view.py                Similar routes table + normalized bar chart
  settings_dialog.py                Persistent settings: date range, activity types
  formatting.py                     Display formatting: pace, duration, distance, elevation
  theme.py                          Design tokens (colors, sizes) + global stylesheet
  widgets/
    map_view.py                     QWebEngineView + Leaflet.js map
    elevation_chart.py              PyQtGraph dual-axis chart, crosshair, toggleable series
    activity_list.py                QListView + QAbstractListModel
    filters.py                      Date range + activity type filter widget
src/models/                         Data layer
  activity.py                       TrackPoint + Activity dataclasses, activity ID generation
  gpx_parser.py                     GPX file parser (lxml, Garmin GPXTPX extensions)
  metrics.py                        Computed metrics: distance (haversine), elevation, pace, HR, VS, cumulative data
src/services/                       Business logic
  store.py                          ActivityStore: load, filter, metrics cache, parse-error logging
  config.py                         Persistent settings (JSON → ~/.config/gpx-runalyzer/config.json)
src/analysis/                       Algorithms
  splits.py                         Best split times via sliding window over cumulative distance
  route_similarity.py               Discrete Fréchet distance, bbox pre-filter, track resampling
  comparison.py                     ComparisonEntry, build_comparison_with_reference
tests/                              Test suite
  conftest.py                       Fixtures: shared QApplication, ActivityStore, sample GPX
  fixtures/sample.gpx               Garmin-style GPX with HR + cadence extensions
```

## Data Flow

1. **Startup**: `main.py` creates `MainWindow`, which instantiates `ActivityStore`
2. **Loading**: `ActivityStore.load()` scans `root_folder/*/*.gpx`, parses each via `gpx_parser.py`, builds `Activity` objects. Parse errors are logged (not silently dropped)
3. **Settings**: Filter preferences are loaded from `~/.config/gpx-runalyzer/config.json` and applied on startup via `ActivityStore.apply_load_filters()`
4. **Dashboard**: `DashboardView` calls `store.filter()` to get activities, computes metrics via `store.get_metrics()`, populates `ActivityListModel`
5. **Detail**: User double-clicks activity → `ActivityDetailView` loads map route, elevation chart with toggleable series, and best split times
6. **Comparison**: User clicks "Find Similar Routes" → `route_similarity.py` finds similar routes using Fréchet distance → `ComparisonView` displays table + normalized bar chart

## Shared Metric Utilities

All distance computation flows through `src/models/metrics.py`:

- `haversine_km(p1, p2)` — great-circle distance between two track points (used everywhere)
- `cumulative_distances_m(points)` — shared cumulative distance in meters (used by splits, route_similarity, and metrics)
- `STOP_DISTANCE_THRESHOLD_M` — named constant (1.0 m) for moving/stopped detection

This avoids having haversine or distance-accumulator logic duplicated across modules.

## Route Similarity Algorithm

- Each track is resampled to 200 evenly-spaced points by cumulative distance
- Bounding-box pre-filter with 2 km margin avoids unnecessary O(n×m) computation
- Discrete Fréchet distance computed via dynamic programming
- Normalized: `similarity = max(0, 1 - frechet / max(dist_a, dist_b))`, where distances are in meters
- Threshold configurable from UI (0% to 100%)

## Split Times

Computable splits: 100 m, 200 m, 400 m, 800 m, 1 K, 5 K, 10 K, Half (21 097.5 m), Full (42 195 m)

Algorithm: sliding window over cumulative distance. For each split distance, finds the minimum elapsed time across all windows of that distance. Only computed for splits ≤ total track distance.

## Display Formatting

`src/ui/formatting.py` provides shared formatters:

| Function | Input | Output |
|---|---|---|
| `format_pace(pace_s)` | seconds/km | `M:SS` |
| `format_time_total(seconds)` | raw seconds | `M:SS` |
| `format_duration(td)` | `timedelta` | `H:MM:SS` or `M:SS` |
| `format_distance_km(km)` | float km | `X.XX km` or `X m` |
| `format_elevation(m)` | float meters | `X m` |

These are used by the dashboard, activity detail, comparison view, and activity list to ensure consistent display.

## Theme System

`src/ui/theme.py` defines design tokens consumed across the UI:

- **Colors**: `ACCENT`, `ACCENT_LIGHT`, `ACCENT_HOVER`, `BORDER`, `CARD_BG`, `CARD_BORDER`, `SUCCESS`, `WARNING`, `TEXT`, `TEXT_SUBTLE`, `HEADER_BG`, `ROW_HOVER`, `TAB_INACTIVE`
- **Sizes**: `RADIUS_SM`, `RADIUS_MD`, `FONT_SIZE_SM`, `FONT_SIZE_BASE`, `FONT_SIZE_MD`, `FONT_SIZE_XXL`
- `apply_theme(widget)` applies the global stylesheet to the main window

## Adding a New Metric

1. Add computation to `src/models/metrics.py` (e.g., `compute_new_metric(points)`)
2. Include in `compute_metrics()` return dict
3. If displayable in charts, register a series in `elevation_chart.py` via `self._register()`
4. Display in `dashboard.py` or `activity_detail.py` as needed
5. Add tests in `tests/test_metrics.py`

## Adding a New Split Distance

1. Add to `SPLIT_DISTANCES` in `src/analysis/splits.py`
2. Add a label entry in `SPLIT_LABELS`
3. If it should appear on the dashboard PR row, add it to the `pr_distances` list in `DashboardView._update_pr()`

## Testing

```bash
python -m pytest -v                 # All tests
python -m pytest tests/test_ui.py -v  # UI tests only
python -m pytest -xvs -k "split"     # Keyword filter
python -m pytest --cov=src -v       # With coverage
```

Tests use `pytest-qt` for Qt widget testing. A shared `QApplication` is created once per session with `AA_ShareOpenGLContexts` enabled (required for the map widget). Non-UI tests run without displaying a GUI.

## Settings Persistence

User settings are stored as JSON at `~/.config/gpx-runalyzer/config.json`:

```json
{
  "start_date": "2024-01-01",
  "end_date": null,
  "activity_types": ["running"]
}
```

- Empty `activity_types` means all types are loaded
- `null` dates mean no filter on that bound
- Settings are loaded on app startup and after dialog save; both reload the full data and re-apply filters

## Key Design Decisions

- **Online maps**: `QWebEngineView` loads Leaflet.js + OSM tiles from CDN. Requires internet.
- **Garmin GPX**: HR in `<gpxtpx:hr>`, cadence in `<gpxtpx:cad>` inside `< extensions >`
- **Metrics caching**: `ActivityStore` caches computed metrics by activity ID; cache is cleared on filter reload
- **Split times**: Sliding window over cumulative distance, not over time
- **Parse errors**: Logged via standard `logging.warning`, not silently dropped
- **Distance math**: All haversine and cumulative-distance logic lives in `metrics.py`; no module should implement its own distance computation
