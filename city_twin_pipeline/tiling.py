from __future__ import annotations

import copy
from typing import Any

from .config import BBox
from .geometry import feature_centroid


def assign_tile_ids(
    layers: dict[str, dict[str, Any]],
    bbox: BBox,
    rows: int = 2,
    cols: int = 2,
) -> dict[str, dict[str, Any]]:
    if rows <= 0 or cols <= 0:
        raise ValueError("rows and cols must be positive")

    result = copy.deepcopy(layers)
    lat_step = (bbox.north - bbox.south) / rows
    lon_step = (bbox.east - bbox.west) / cols
    for layer in result.values():
        for feature in layer.get("features", []):
            center = feature_centroid(feature)
            if center is None:
                continue
            lon, lat = center
            col = _clamp(int((lon - bbox.west) / lon_step), 0, cols - 1)
            row = _clamp(int((lat - bbox.south) / lat_step), 0, rows - 1)
            feature.setdefault("properties", {})["tile_id"] = f"r{row}_c{col}"
    return result


def tile_metadata(bbox: BBox, rows: int = 2, cols: int = 2) -> list[dict[str, float | str]]:
    lat_step = (bbox.north - bbox.south) / rows
    lon_step = (bbox.east - bbox.west) / cols
    tiles: list[dict[str, float | str]] = []
    for row in range(rows):
        for col in range(cols):
            tiles.append(
                {
                    "tile_id": f"r{row}_c{col}",
                    "south": bbox.south + row * lat_step,
                    "west": bbox.west + col * lon_step,
                    "north": bbox.south + (row + 1) * lat_step,
                    "east": bbox.west + (col + 1) * lon_step,
                }
            )
    return tiles


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))
