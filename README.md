# GPX Runalyzer

Graphical desktop application that analyzes running sessions stored as GPX files. Displays a dashboard with summaries, filters, activity detail views with maps and elevation profiles, and similar-route comparison.

## Requirements

- Python 3.10+
- Internet connection (for OSM map tiles)
- macOS / Linux / Windows

## Quick Start

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Run the application
python -m src.main /path/to/your/gpx/folder
```

Or use the installed entry point:

```bash
gpx-runalyzer /path/to/your/gpx/folder
```

## GPX Folder Structure

Your GPX files should be organized in subfolders by activity type:

```
my_activities/
  running/
    2024-06-15_morning.gpx
    2024-07-01_evening.gpx
  trail_running/
    2024-08-10_bikeway.gpx
  cycling/
    2024-09-05_weekend.gpx
```

The app uses the subfolder name as the activity type label.

## If No Folder Given

Run without arguments and a folder picker dialog will appear:

```bash
python -m src.main
```

## Running Tests

```bash
source venv/bin/activate
python -m pytest -v
```

## Linting and Type Checking

```bash
ruff check src/ tests/    # Lint check
ruff format --check .     # Format check (if enabled)
mypy src/                 # Type check
```

## Settings

Filter preferences (date range, activity types) are persisted to `~/.config/gpx-runalyzer/config.json`. Open the Settings dialog from the main window toolbar (⚙️ icon) to configure.

## Features

- **Dashboard**: Global summary across all activities (distance, pace, elevation, HR), personal records (100 m to marathon), type/date filters, chronological activity list
- **Activity Detail**: Route on interactive map (OpenStreetMap), elevation/profile chart with toggleable Pace / Elevation / HR / Vertical Speed overlays and crosshair tooltip, best split times
- **Similar Routes**: Discrete Fréchet distance-based route matching with configurable similarity threshold (0–100%), side-by-side comparison table + normalized bar chart
- **Supported GPX formats**: Standard GPX 1.1 with Garmin TrackPoint extensions (`<gpxtpx:hr>`, `<gpxtpx:cad>`)

## Dependencies

| Package | Purpose |
|---------|---------|
| PyQt6 + PyQt6-WebEngine | GUI + map rendering |
| pyqtgraph | Elevation / pace charts |
| lxml | GPX XML parsing |

## License

See [LICENSE](LICENSE).
