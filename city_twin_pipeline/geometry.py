from __future__ import annotations

import math
from typing import Any, Iterable

from .config import BBox

EARTH_RADIUS_M = 6_378_137.0


def bbox_center(bbox: BBox) -> tuple[float, float]:
    return ((bbox.west + bbox.east) / 2.0, (bbox.south + bbox.north) / 2.0)


def lonlat_to_local_m(lon: float, lat: float, origin: tuple[float, float]) -> tuple[float, float]:
    origin_lon, origin_lat = origin
    x = math.radians(lon - origin_lon) * EARTH_RADIUS_M * math.cos(math.radians(origin_lat))
    y = math.radians(lat - origin_lat) * EARTH_RADIUS_M
    return x, y


def feature_coordinates(feature: dict[str, Any]) -> list[tuple[float, float]]:
    geometry = feature.get("geometry", {})
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates")
    if geom_type == "Point" and _is_coord(coords):
        return [(float(coords[0]), float(coords[1]))]
    if geom_type == "LineString" and isinstance(coords, list):
        return [(float(coord[0]), float(coord[1])) for coord in coords if _is_coord(coord)]
    if geom_type == "Polygon" and isinstance(coords, list) and coords:
        ring = coords[0]
        if isinstance(ring, list):
            return [(float(coord[0]), float(coord[1])) for coord in ring if _is_coord(coord)]
    return []


def centroid(coords: Iterable[tuple[float, float]]) -> tuple[float, float] | None:
    points = list(coords)
    if not points:
        return None
    return (
        sum(point[0] for point in points) / len(points),
        sum(point[1] for point in points) / len(points),
    )


def feature_centroid(feature: dict[str, Any]) -> tuple[float, float] | None:
    return centroid(feature_coordinates(feature))


def _is_coord(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) >= 2
        and isinstance(value[0], (int, float))
        and isinstance(value[1], (int, float))
    )
