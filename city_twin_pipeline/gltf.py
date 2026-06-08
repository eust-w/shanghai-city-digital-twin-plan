from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Any

from .config import BBox
from .geometry import bbox_center, lonlat_to_local_m


def build_buildings_gltf(buildings_layer: dict[str, Any], bbox: BBox, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    origin = bbox_center(bbox)
    positions: list[tuple[float, float, float]] = []
    indices: list[int] = []
    exported = 0
    skipped_missing_height = 0
    skipped_invalid_geometry = 0
    max_height = 0.0

    for feature in buildings_layer.get("features", []):
        height = feature.get("properties", {}).get("height_m")
        if not isinstance(height, (int, float)) or height <= 0:
            skipped_missing_height += 1
            continue
        ring = _outer_ring(feature)
        if len(ring) < 3:
            skipped_invalid_geometry += 1
            continue
        base_index = len(positions)
        local = [lonlat_to_local_m(lon, lat, origin) for lon, lat in ring]
        for x, y in local:
            positions.append((x, 0.0, -y))
        for x, y in local:
            positions.append((x, float(height), -y))
        count = len(local)

        # Top and bottom fan triangulation. This is LOD1 geometry for operational
        # export, not a cadastral-quality polygon triangulator.
        for i in range(1, count - 1):
            indices.extend([base_index + count, base_index + count + i, base_index + count + i + 1])
            indices.extend([base_index, base_index + i + 1, base_index + i])
        for i in range(count):
            j = (i + 1) % count
            bottom_i = base_index + i
            bottom_j = base_index + j
            top_i = base_index + count + i
            top_j = base_index + count + j
            indices.extend([bottom_i, bottom_j, top_j, bottom_i, top_j, top_i])
        exported += 1
        max_height = max(max_height, float(height))

    bin_payload = _pack_positions(positions)
    index_offset = len(bin_payload)
    bin_payload += _pack_indices(indices)
    (output_dir / "buildings.bin").write_bytes(bin_payload)

    gltf = _build_gltf_json(positions, indices, index_offset)
    (output_dir / "buildings.gltf").write_text(json.dumps(gltf, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest = {
        "gltf": "buildings.gltf",
        "binary": "buildings.bin",
        "exported_buildings": exported,
        "skipped_missing_height": skipped_missing_height,
        "skipped_invalid_geometry": skipped_invalid_geometry,
        "origin_lon": origin[0],
        "origin_lat": origin[1],
        "max_height_m": round(max_height, 2),
        "vertex_count": len(positions),
        "triangle_count": len(indices) // 3,
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def _outer_ring(feature: dict[str, Any]) -> list[tuple[float, float]]:
    geometry = feature.get("geometry", {})
    coords = geometry.get("coordinates")
    if geometry.get("type") != "Polygon" or not isinstance(coords, list) or not coords:
        return []
    ring = coords[0]
    if not isinstance(ring, list):
        return []
    clean = [(float(coord[0]), float(coord[1])) for coord in ring if _is_coord(coord)]
    if len(clean) > 1 and clean[0] == clean[-1]:
        clean = clean[:-1]
    return clean


def _pack_positions(positions: list[tuple[float, float, float]]) -> bytes:
    return b"".join(struct.pack("<fff", *position) for position in positions)


def _pack_indices(indices: list[int]) -> bytes:
    return b"".join(struct.pack("<I", index) for index in indices)


def _build_gltf_json(
    positions: list[tuple[float, float, float]],
    indices: list[int],
    index_offset: int,
) -> dict[str, Any]:
    position_length = len(positions) * 12
    index_length = len(indices) * 4
    if positions:
        mins = [min(p[i] for p in positions) for i in range(3)]
        maxs = [max(p[i] for p in positions) for i in range(3)]
    else:
        mins = [0.0, 0.0, 0.0]
        maxs = [0.0, 0.0, 0.0]
    return {
        "asset": {"version": "2.0", "generator": "shanghai-city-digital-twin-plan"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "OSM height-tagged LOD1 buildings"}],
        "meshes": [
            {
                "primitives": [
                    {
                        "attributes": {"POSITION": 0},
                        "indices": 1,
                        "mode": 4,
                        "material": 0,
                    }
                ]
            }
        ],
        "materials": [
            {
                "name": "neutral-building",
                "pbrMetallicRoughness": {
                    "baseColorFactor": [0.72, 0.76, 0.78, 1.0],
                    "metallicFactor": 0.0,
                    "roughnessFactor": 0.85,
                },
            }
        ],
        "buffers": [{"uri": "buildings.bin", "byteLength": position_length + index_length}],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": position_length, "target": 34962},
            {"buffer": 0, "byteOffset": index_offset, "byteLength": index_length, "target": 34963},
        ],
        "accessors": [
            {
                "bufferView": 0,
                "byteOffset": 0,
                "componentType": 5126,
                "count": len(positions),
                "type": "VEC3",
                "min": mins,
                "max": maxs,
            },
            {
                "bufferView": 1,
                "byteOffset": 0,
                "componentType": 5125,
                "count": len(indices),
                "type": "SCALAR",
                "min": [min(indices) if indices else 0],
                "max": [max(indices) if indices else 0],
            },
        ],
    }


def _is_coord(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) >= 2
        and isinstance(value[0], (int, float))
        and isinstance(value[1], (int, float))
    )
