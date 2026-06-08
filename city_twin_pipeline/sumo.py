from __future__ import annotations

import math
from typing import Any
from xml.sax.saxutils import escape

from .config import BBox
from .geometry import bbox_center, lonlat_to_local_m


def build_sumo_plain_xml(roads_layer: dict[str, Any], bbox: BBox) -> dict[str, str]:
    origin = bbox_center(bbox)
    nodes: dict[str, tuple[float, float]] = {}
    edges: list[str] = []
    for feature in roads_layer.get("features", []):
        coords = _line_coords(feature)
        if len(coords) < 2:
            continue
        props = feature.get("properties", {})
        osm_id = str(props.get("osm_id", f"road/{len(edges)}"))
        edge_id = _safe_id(osm_id)
        start_id = _node_id(coords[0])
        end_id = _node_id(coords[-1])
        nodes[start_id] = lonlat_to_local_m(coords[0][0], coords[0][1], origin)
        nodes[end_id] = lonlat_to_local_m(coords[-1][0], coords[-1][1], origin)
        shape = _shape(coords, origin)
        attrs = _edge_attrs(edge_id, start_id, end_id, props, shape)
        edges.append(f"  <edge {attrs}/>")
        if _oneway(props) == "reverse":
            edges.pop()
            edges.append(f"  <edge {_edge_attrs(edge_id + '_rev', end_id, start_id, props, list(reversed(shape)))}/>")
        elif _oneway(props) == "no":
            edges.append(f"  <edge {_edge_attrs(edge_id + '_rev', end_id, start_id, props, list(reversed(shape)))}/>")

    node_lines = ["<nodes>"]
    for node_id, (x, y) in sorted(nodes.items()):
        node_lines.append(f'  <node id="{escape(node_id)}" x="{x:.2f}" y="{y:.2f}" type="priority"/>')
    node_lines.append("</nodes>")

    edge_lines = ["<edges>", *edges, "</edges>"]
    return {"nodes": "\n".join(node_lines) + "\n", "edges": "\n".join(edge_lines) + "\n"}


def _edge_attrs(
    edge_id: str,
    start_id: str,
    end_id: str,
    props: dict[str, Any],
    shape: list[tuple[float, float]],
) -> str:
    attrs = {
        "id": edge_id,
        "from": start_id,
        "to": end_id,
        "priority": str(_priority(str(props.get("highway", "")))),
        "numLanes": str(_lanes(props)),
        "speed": f"{_speed_mps(props):.2f}",
        "shape": " ".join(f"{x:.2f},{y:.2f}" for x, y in shape),
    }
    return " ".join(f'{key}="{escape(value)}"' for key, value in attrs.items())


def _line_coords(feature: dict[str, Any]) -> list[tuple[float, float]]:
    geometry = feature.get("geometry", {})
    coords = geometry.get("coordinates")
    if geometry.get("type") != "LineString" or not isinstance(coords, list):
        return []
    return [(float(coord[0]), float(coord[1])) for coord in coords if _is_coord(coord)]


def _shape(coords: list[tuple[float, float]], origin: tuple[float, float]) -> list[tuple[float, float]]:
    return [lonlat_to_local_m(lon, lat, origin) for lon, lat in coords]


def _node_id(coord: tuple[float, float]) -> str:
    return f"n_{coord[0]:.7f}_{coord[1]:.7f}".replace(".", "_").replace("-", "m")


def _safe_id(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value).strip("_") or "edge"


def _oneway(props: dict[str, Any]) -> str:
    value = str(props.get("oneway", "")).strip().lower()
    if value in {"yes", "true", "1"}:
        return "forward"
    if value == "-1":
        return "reverse"
    return "no"


def _lanes(props: dict[str, Any]) -> int:
    lanes = str(props.get("lanes", "")).strip()
    if lanes.isdigit() and int(lanes) > 0:
        return min(int(lanes), 8)
    highway = str(props.get("highway", "")).strip()
    return 2 if highway in {"motorway", "trunk", "primary", "secondary"} else 1


def _speed_mps(props: dict[str, Any]) -> float:
    maxspeed = str(props.get("maxspeed", "")).strip().lower()
    number = "".join(ch for ch in maxspeed if ch.isdigit() or ch == ".")
    if number:
        speed = float(number)
        if "mph" in maxspeed:
            return speed * 0.44704
        return speed / 3.6
    highway = str(props.get("highway", "")).strip()
    defaults = {
        "motorway": 27.78,
        "trunk": 22.22,
        "primary": 16.67,
        "secondary": 13.89,
        "tertiary": 11.11,
        "residential": 8.33,
        "service": 5.56,
    }
    return defaults.get(highway, 8.33)


def _priority(highway: str) -> int:
    order = ["service", "residential", "tertiary", "secondary", "primary", "trunk", "motorway"]
    return order.index(highway) + 1 if highway in order else 1


def _is_coord(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) >= 2
        and isinstance(value[0], (int, float))
        and isinstance(value[1], (int, float))
        and math.isfinite(float(value[0]))
        and math.isfinite(float(value[1]))
    )
