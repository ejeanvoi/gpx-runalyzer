from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from lxml import etree

from src.models.activity import Activity, TrackPoint, compute_activity_id

GPX_NS = "http://www.topografix.com/GPX/1/1"
Gpxtpx_NS = "http://www.garmin.com/xmlschemas/TrackPointExtension/v1"


def _parse_datetime(ts_str: str | None) -> datetime | None:
    if not ts_str:
        return None
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt
    except ValueError:
        return None


def _parse_float(val: str | None) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _extract_extension_data(ext_elem: etree._Element | None) -> dict[str, float]:
    data: dict[str, float] = {}
    if ext_elem is None:
        return data
    tpx_elem = ext_elem.find(f"{{{Gpxtpx_NS}}}TrackPointExtension")
    if tpx_elem is not None:
        hr_elem = tpx_elem.find(f"{{{Gpxtpx_NS}}}hr")
        if hr_elem is not None and hr_elem.text:
            hr_val = _parse_float(hr_elem.text)
            if hr_val is not None:
                data["hr"] = hr_val
        cad_elem = tpx_elem.find(f"{{{Gpxtpx_NS}}}cad")
        if cad_elem is not None and cad_elem.text:
            cad_val = _parse_float(cad_elem.text)
            if cad_val is not None:
                data["cadence"] = cad_val
    return data


def _extract_track_points(trkseg_elem: etree._Element) -> list[TrackPoint]:
    points = []
    for trkpt in trkseg_elem.iterfind(f"{{{GPX_NS}}}trkpt"):
        lat = _parse_float(trkpt.get("lat"))
        lon = _parse_float(trkpt.get("lon"))
        if lat is None or lon is None:
            continue
        ele = 0.0
        ele_elem = trkpt.find(f"{{{GPX_NS}}}ele")
        if ele_elem is not None and ele_elem.text:
            ele = _parse_float(ele_elem.text) or 0.0
        time_elem = trkpt.find(f"{{{GPX_NS}}}time")
        time = _parse_datetime(time_elem.text) if time_elem is not None else None
        ext_elem = trkpt.find(f"{{{GPX_NS}}}extensions")
        ext_data = _extract_extension_data(ext_elem)
        point = TrackPoint(
            lat=lat,
            lon=lon,
            ele=ele,
            time=time,
            hr=ext_data.get("hr"),
            cadence=ext_data.get("cadence"),
        )
        points.append(point)
    return points


def parse_gpx(filepath: Path) -> Activity:
    tree = etree.parse(str(filepath))
    root = tree.getroot()

    name = filepath.stem
    meta_name = root.find(f"{{{GPX_NS}}}metadata/{{{GPX_NS}}}name")
    if meta_name is not None and meta_name.text:
        name = meta_name.text.strip()
    trk_name = root.find(f"{{{GPX_NS}}}trk/{{{GPX_NS}}}name")
    if trk_name is not None and trk_name.text:
        name = trk_name.text.strip()

    time_elem = root.find(f"{{{GPX_NS}}}metadata/{{{GPX_NS}}}time")
    activity_date = _parse_datetime(time_elem.text) if time_elem is not None else None
    if activity_date is None:
        activity_date = datetime.fromtimestamp(filepath.stat().st_mtime, tz=timezone.utc)

    trk = root.find(f"{{{GPX_NS}}}trk")
    if trk is None:
        raise ValueError(f"No track found in {filepath}")

    activity_type = filepath.parent.name
    points = []
    for child in trk:
        local_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if local_tag == "trkseg":
            points.extend(_extract_track_points(child))

    aid = compute_activity_id(filepath, activity_date)

    return Activity(
        id=aid,
        name=name,
        date=activity_date,
        activity_type=activity_type,
        filepath=filepath,
        points=points,
    )
