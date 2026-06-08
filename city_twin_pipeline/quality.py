from __future__ import annotations

from typing import Any

from .config import BBox


def build_quality_report(
    layers: dict[str, dict[str, Any]],
    bbox: BBox,
    minimum_counts: dict[str, int],
) -> dict[str, Any]:
    counts = {name: len(layer.get("features", [])) for name, layer in layers.items()}
    issues: list[str] = []
    warnings: list[str] = []
    invalid_geometry: dict[str, int] = {}
    outside_bbox: dict[str, int] = {}
    boundary_crossing: dict[str, int] = {}

    for layer_name, minimum in minimum_counts.items():
        count = counts.get(layer_name, 0)
        if count < minimum:
            issues.append(f"{layer_name} has {count} features, below required minimum {minimum}")

    for layer_name, layer in layers.items():
        invalid_geometry[layer_name] = 0
        outside_bbox[layer_name] = 0
        boundary_crossing[layer_name] = 0
        for feature in layer.get("features", []):
            geometry = feature.get("geometry", {})
            if not _is_valid_geometry(geometry):
                invalid_geometry[layer_name] += 1
            coords = list(_iter_coords(geometry))
            inside_count = sum(1 for lon, lat in coords if bbox.contains(lon, lat))
            if coords and inside_count == 0:
                outside_bbox[layer_name] += 1
            elif coords and inside_count < len(coords):
                boundary_crossing[layer_name] += 1
        if invalid_geometry[layer_name]:
            issues.append(f"{layer_name} has {invalid_geometry[layer_name]} invalid geometries")
        if outside_bbox[layer_name]:
            issues.append(f"{layer_name} has {outside_bbox[layer_name]} features outside bbox")
        if boundary_crossing[layer_name]:
            warnings.append(
                f"{layer_name} has {boundary_crossing[layer_name]} boundary-crossing features requiring clip/tile handling"
            )

    buildings = layers.get("buildings", {"features": []})
    missing_height_count = sum(
        1
        for feature in buildings.get("features", [])
        if feature.get("properties", {}).get("height_m") is None
    )

    return {
        "status": "pass" if not issues else "fail",
        "counts": counts,
        "minimum_counts": minimum_counts,
        "invalid_geometry": invalid_geometry,
        "outside_bbox": outside_bbox,
        "boundary_crossing": boundary_crossing,
        "buildings": {
            "missing_height_count": missing_height_count,
            "height_coverage_ratio": _coverage_ratio(counts.get("buildings", 0), missing_height_count),
        },
        "issues": issues,
        "warnings": warnings,
    }


def _is_valid_geometry(geometry: dict[str, Any]) -> bool:
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates")
    if geom_type == "Point":
        return _is_coord(coords)
    if geom_type == "LineString":
        return isinstance(coords, list) and len(coords) >= 2 and all(_is_coord(coord) for coord in coords)
    if geom_type == "Polygon":
        if not isinstance(coords, list) or not coords:
            return False
        ring = coords[0]
        return isinstance(ring, list) and len(ring) >= 4 and ring[0] == ring[-1] and all(_is_coord(coord) for coord in ring)
    return False


def _is_coord(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 2
        and isinstance(value[0], (int, float))
        and isinstance(value[1], (int, float))
    )


def _iter_coords(geometry: dict[str, Any]):
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates")
    if geom_type == "Point" and _is_coord(coords):
        yield float(coords[0]), float(coords[1])
    elif geom_type == "LineString" and isinstance(coords, list):
        for coord in coords:
            if _is_coord(coord):
                yield float(coord[0]), float(coord[1])
    elif geom_type == "Polygon" and isinstance(coords, list):
        for ring in coords:
            if isinstance(ring, list):
                for coord in ring:
                    if _is_coord(coord):
                        yield float(coord[0]), float(coord[1])


def _coverage_ratio(total: int, missing: int) -> float:
    if total == 0:
        return 0.0
    return round((total - missing) / total, 4)
