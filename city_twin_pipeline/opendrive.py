from __future__ import annotations

import math
from typing import Any
from xml.sax.saxutils import escape

from .config import BBox
from .geometry import bbox_center, lonlat_to_local_m


def build_opendrive_xml(roads_layer: dict[str, Any], bbox: BBox) -> str:
    origin = bbox_center(bbox)
    lines = [
        '<?xml version="1.0" standalone="yes"?>',
        "<OpenDRIVE>",
        '  <header revMajor="1" revMinor="8" name="Shanghai OSM baseline" version="0.1" date="" north="0" south="0" east="0" west="0"/>',
    ]
    road_index = 1
    for feature in roads_layer.get("features", []):
        coords = _line_coords(feature)
        if len(coords) < 2:
            continue
        props = feature.get("properties", {})
        local = [lonlat_to_local_m(lon, lat, origin) for lon, lat in coords]
        segments = _segments(local)
        total_length = sum(segment["length"] for segment in segments)
        if total_length <= 0:
            continue
        road_id = str(road_index)
        road_name = escape(str(props.get("osm_id", f"road/{road_id}")))
        lines.append(f'  <road name="{road_name}" length="{total_length:.3f}" id="{road_id}" junction="-1">')
        lines.append("    <planView>")
        s = 0.0
        for segment in segments:
            lines.append(
                '      <geometry s="{s:.3f}" x="{x:.3f}" y="{y:.3f}" hdg="{hdg:.8f}" length="{length:.3f}"><line/></geometry>'.format(
                    s=s,
                    x=segment["x"],
                    y=segment["y"],
                    hdg=segment["hdg"],
                    length=segment["length"],
                )
            )
            s += segment["length"]
        lines.append("    </planView>")
        lines.append("    <lanes>")
        lines.append('      <laneSection s="0.000">')
        lines.append("        <center>")
        lines.append('          <lane id="0" type="none" level="false"/>')
        lines.append("        </center>")
        lines.append("        <right>")
        lines.append('          <lane id="-1" type="driving" level="false">')
        lines.append('            <width sOffset="0.000" a="3.500" b="0.000" c="0.000" d="0.000"/>')
        lines.append("          </lane>")
        lines.append("        </right>")
        lines.append("      </laneSection>")
        lines.append("    </lanes>")
        lines.append("  </road>")
        road_index += 1
    lines.append("</OpenDRIVE>")
    return "\n".join(lines) + "\n"


def _line_coords(feature: dict[str, Any]) -> list[tuple[float, float]]:
    geometry = feature.get("geometry", {})
    coords = geometry.get("coordinates")
    if geometry.get("type") != "LineString" or not isinstance(coords, list):
        return []
    return [(float(coord[0]), float(coord[1])) for coord in coords if _is_coord(coord)]


def _segments(local: list[tuple[float, float]]) -> list[dict[str, float]]:
    segments: list[dict[str, float]] = []
    for start, end in zip(local, local[1:]):
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.hypot(dx, dy)
        if length <= 0:
            continue
        segments.append({"x": start[0], "y": start[1], "hdg": math.atan2(dy, dx), "length": length})
    return segments


def _is_coord(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) >= 2
        and isinstance(value[0], (int, float))
        and isinstance(value[1], (int, float))
    )
