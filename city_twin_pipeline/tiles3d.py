from __future__ import annotations

import math
from typing import Any

from .config import BBox


def build_tileset_json(
    bbox: BBox,
    content_uri: str,
    min_height: float,
    max_height: float,
) -> dict[str, Any]:
    return {
        "asset": {
            "version": "1.1",
            "tilesetVersion": "0.1.0",
        },
        "geometricError": 500,
        "root": {
            "boundingVolume": {
                "region": [
                    math.radians(bbox.west),
                    math.radians(bbox.south),
                    math.radians(bbox.east),
                    math.radians(bbox.north),
                    float(min_height),
                    float(max_height),
                ]
            },
            "geometricError": 0,
            "refine": "ADD",
            "content": {"uri": content_uri},
        },
    }
