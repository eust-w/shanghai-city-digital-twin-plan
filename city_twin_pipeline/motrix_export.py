from __future__ import annotations

import json
import math
import shutil
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET

from .config import BBox
from .geometry import bbox_center, lonlat_to_local_m


def build_motrix_package(
    layers: dict[str, dict[str, Any]],
    bbox: BBox,
    output_root: Path,
    max_scene_extent_m: float = 900.0,
) -> dict[str, Any]:
    package_dir = output_root / "motrix_scene"
    if package_dir.exists():
        shutil.rmtree(package_dir)
    (package_dir / "meshes").mkdir(parents=True, exist_ok=True)
    (package_dir / "textures").mkdir(parents=True, exist_ok=True)
    (package_dir / "metadata").mkdir(parents=True, exist_ok=True)
    (package_dir / "raw").mkdir(parents=True, exist_ok=True)

    scale = _source_to_motrix_scale(bbox, max_scene_extent_m)
    visual_obj, collision_obj, mesh_manifest = _build_meshes(layers.get("buildings", {"features": []}), bbox, scale)
    (package_dir / "meshes" / "scene_visual.obj").write_text(visual_obj, encoding="utf-8")
    (package_dir / "meshes" / "scene_collision.obj").write_text(collision_obj, encoding="utf-8")

    manifest = _asset_manifest(bbox, scale, mesh_manifest)
    source_info = _source_info(bbox, scale, mesh_manifest)
    _write_scene_files(package_dir, manifest, source_info)
    validation = validate_motrix_package(package_dir)
    zip_path = _zip_package(package_dir)

    result = {
        "package_dir": str(package_dir),
        "zip": str(zip_path),
        "validation": validation,
        "manifest": manifest,
    }
    (package_dir / "metadata" / "export_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result


def validate_motrix_package(package_dir: Path) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    summary: dict[str, Any] = {}
    package_dir = Path(package_dir)

    for rel in ["scene.xml", "scene.urdf", "scene.json", "metadata/asset_manifest.json"]:
        if not (package_dir / rel).exists():
            issues.append({"level": "error", "message": f"missing required file: {rel}"})

    _parse_xml(package_dir / "scene.xml", issues, "scene.xml")
    _parse_xml(package_dir / "scene.urdf", issues, "scene.urdf")
    scene_json = _parse_json(package_dir / "scene.json", issues, "scene.json")
    asset_manifest = _parse_json(package_dir / "metadata" / "asset_manifest.json", issues, "metadata/asset_manifest.json")

    refs = set()
    if isinstance(scene_json, dict):
        for value in _walk_strings(scene_json.get("assets", {})):
            if value.endswith(".obj"):
                refs.add(value)
            _check_relative(value, issues, "scene.json asset")
    if isinstance(asset_manifest, dict):
        scene = asset_manifest.get("scene", {})
        if isinstance(scene, dict):
            for key in ("visual_mesh", "collision_mesh"):
                value = scene.get(key)
                if isinstance(value, str):
                    refs.add(value)
                    _check_relative(value, issues, f"asset_manifest scene {key}")

    for ref in sorted(refs):
        candidate = _resolve_relative(package_dir, ref, issues)
        if not candidate.exists():
            issues.append({"level": "error", "message": f"referenced mesh missing: {ref}"})

    visual_counts = _obj_counts(package_dir / "meshes" / "scene_visual.obj")
    collision_counts = _obj_counts(package_dir / "meshes" / "scene_collision.obj")
    summary["scene_visual_faces"] = visual_counts["faces"]
    summary["scene_collision_faces"] = collision_counts["faces"]
    summary["scene_visual_vertices"] = visual_counts["vertices"]
    summary["scene_collision_vertices"] = collision_counts["vertices"]
    summary["object_count"] = 0

    if visual_counts["faces"] <= 0:
        issues.append({"level": "error", "message": "visual mesh is empty or unsupported: meshes/scene_visual.obj"})
    if collision_counts["faces"] <= 0:
        issues.append({"level": "error", "message": "collision mesh is empty or unsupported: meshes/scene_collision.obj"})
    if collision_counts["faces"] > visual_counts["faces"]:
        issues.append({"level": "error", "message": "collision mesh must not have more faces than visual mesh"})

    bbox = _obj_bounds(package_dir / "meshes" / "scene_visual.obj")
    if bbox is not None:
        summary["bbox"] = bbox
        extents = [bbox["max"][axis] - bbox["min"][axis] for axis in ("x", "y", "z")]
        if any(value <= 0 for value in extents):
            issues.append({"level": "error", "message": "visual mesh bbox has non-positive extent"})
        if any(value > 1000 for value in extents):
            issues.append({"level": "error", "message": "visual mesh bbox is larger than 1000 meters"})
        if bbox["min"]["z"] < -0.01:
            issues.append({"level": "error", "message": "visual mesh lowest z must be aligned near 0"})

    report = {"valid": not any(issue["level"] == "error" for issue in issues), "issues": issues, "summary": summary}
    (package_dir / "metadata").mkdir(parents=True, exist_ok=True)
    (package_dir / "metadata" / "validation_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return report


def _build_meshes(buildings_layer: dict[str, Any], bbox: BBox, scale: float) -> tuple[str, str, dict[str, Any]]:
    origin = bbox_center(bbox)
    visual_vertices: list[tuple[float, float, float]] = []
    visual_faces: list[tuple[int, int, int]] = []
    collision_vertices: list[tuple[float, float, float]] = []
    collision_faces: list[tuple[int, int, int]] = []
    exported = 0
    skipped_missing_height = 0
    skipped_invalid_geometry = 0

    for feature in buildings_layer.get("features", []):
        height = feature.get("properties", {}).get("height_m")
        if not isinstance(height, (int, float)) or height <= 0:
            skipped_missing_height += 1
            continue
        ring = _outer_ring(feature)
        if len(ring) < 3:
            skipped_invalid_geometry += 1
            continue
        local = [_scaled_local(lon, lat, origin, scale) for lon, lat in ring]
        height_m = float(height) * scale
        _append_extruded_polygon(visual_vertices, visual_faces, local, height_m)
        _append_collision_box(collision_vertices, collision_faces, local, height_m)
        exported += 1

    visual_obj = _obj_text("motrix_scene_visual", visual_vertices, visual_faces)
    collision_obj = _obj_text("motrix_scene_collision", collision_vertices, collision_faces)
    manifest = {
        "exported_buildings": exported,
        "skipped_missing_height": skipped_missing_height,
        "skipped_invalid_geometry": skipped_invalid_geometry,
        "source_to_motrix_scale": scale,
        "visual_bbox": _points_bounds(visual_vertices),
        "visual_vertices": len(visual_vertices),
        "visual_faces": len(visual_faces),
        "collision_vertices": len(collision_vertices),
        "collision_faces": len(collision_faces),
    }
    manifest["visual_extent_m"] = _bbox_extent(manifest["visual_bbox"])
    return visual_obj, collision_obj, manifest


def _append_extruded_polygon(
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, int, int]],
    ring: list[tuple[float, float]],
    height: float,
) -> None:
    base_index = len(vertices) + 1
    for x, y in ring:
        vertices.append((x, y, 0.0))
    for x, y in ring:
        vertices.append((x, y, height))
    count = len(ring)
    for i in range(1, count - 1):
        faces.append((base_index + count, base_index + count + i, base_index + count + i + 1))
        faces.append((base_index, base_index + i + 1, base_index + i))
    for i in range(count):
        j = (i + 1) % count
        bottom_i = base_index + i
        bottom_j = base_index + j
        top_i = base_index + count + i
        top_j = base_index + count + j
        faces.append((bottom_i, bottom_j, top_j))
        faces.append((bottom_i, top_j, top_i))


def _append_collision_box(
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, int, int]],
    ring: list[tuple[float, float]],
    height: float,
) -> None:
    min_x = min(point[0] for point in ring)
    max_x = max(point[0] for point in ring)
    min_y = min(point[1] for point in ring)
    max_y = max(point[1] for point in ring)
    base = len(vertices) + 1
    vertices.extend(
        [
            (min_x, min_y, 0.0),
            (max_x, min_y, 0.0),
            (max_x, max_y, 0.0),
            (min_x, max_y, 0.0),
            (min_x, min_y, height),
            (max_x, min_y, height),
            (max_x, max_y, height),
            (min_x, max_y, height),
        ]
    )
    faces.extend(
        [
            (base + 4, base + 5, base + 6),
            (base + 4, base + 6, base + 7),
            (base, base + 2, base + 1),
            (base, base + 3, base + 2),
            (base, base + 1, base + 5),
            (base, base + 5, base + 4),
            (base + 1, base + 2, base + 6),
            (base + 1, base + 6, base + 5),
            (base + 2, base + 3, base + 7),
            (base + 2, base + 7, base + 6),
            (base + 3, base, base + 4),
            (base + 3, base + 4, base + 7),
        ]
    )


def _asset_manifest(bbox: BBox, scale: float, mesh_manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "generated_from": "shanghai_city_digital_twin_plan",
        "coordinate_system": "motrix_world",
        "unit": "meter",
        "source_crs": "EPSG:4326",
        "source_to_motrix_scale": scale,
        "scene": {
            "id": "static_scene",
            "role": "environment",
            "visual_mesh": "meshes/scene_visual.obj",
            "collision_mesh": "meshes/scene_collision.obj",
            "visual_faces": mesh_manifest["visual_faces"],
            "collision_faces": mesh_manifest["collision_faces"],
            "bbox": {"south": bbox.south, "west": bbox.west, "north": bbox.north, "east": bbox.east},
            "local_bbox": mesh_manifest["visual_bbox"],
            "local_extent_m": mesh_manifest["visual_extent_m"],
            "binding": {"type": "static_world", "body": "static_scene"},
            "gaussian_splat": None,
        },
        "objects": [],
        "segmentation": {"object_count": 0, "method": "city_static_environment"},
        "mesh_generation": mesh_manifest,
    }


def _source_info(bbox: BBox, scale: float, mesh_manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": "OpenStreetMap via Overpass API",
        "license": "ODbL-1.0",
        "attribution": "© OpenStreetMap contributors",
        "bbox": {"south": bbox.south, "west": bbox.west, "north": bbox.north, "east": bbox.east},
        "source_to_motrix_scale": scale,
        "mesh_generation": mesh_manifest,
        "note": "Buildings without real height_m were not extruded into Motrix meshes.",
    }


def _write_scene_files(package_dir: Path, manifest: dict[str, Any], source_info: dict[str, Any]) -> None:
    scene = manifest["scene"]
    (package_dir / "scene.xml").write_text(_build_mjcf(scene), encoding="utf-8")
    (package_dir / "scene.urdf").write_text(_build_urdf(scene), encoding="utf-8")
    (package_dir / "scene.json").write_text(
        json.dumps(_build_scene_index(scene), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    metadata_dir = package_dir / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    (metadata_dir / "asset_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (metadata_dir / "scene_manifest.json").write_text(json.dumps(scene, ensure_ascii=False, indent=2), encoding="utf-8")
    (metadata_dir / "object_manifest.json").write_text(
        json.dumps(
            {
                "objects": [],
                "count": 0,
                "segmentation": manifest.get("segmentation", {}),
                "coordinate_system": "motrix_world",
                "unit": "meter",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (metadata_dir / "semantic.json").write_text(
        json.dumps(
            {
                "labels": [{"id": "static_scene", "label": "city_static_environment", "source": "osm_building_layer"}],
                "coordinate_system": "motrix_world",
                "unit": "meter",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (metadata_dir / "reconstruction_report.json").write_text(
        json.dumps(
            {
                "pipeline": "city_twin_osm_to_motrix",
                "status": "generated_from_existing_city_layers",
                "mesh_generation": manifest["mesh_generation"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (package_dir / "raw" / "source_info.json").write_text(json.dumps(source_info, ensure_ascii=False, indent=2), encoding="utf-8")
    (package_dir / "README.md").write_text(_readme(), encoding="utf-8")
    (package_dir / "review.html").write_text(_review_html(), encoding="utf-8")


def _build_mjcf(scene: dict[str, Any]) -> str:
    view = _scene_view(scene)
    return "\n".join(
        [
            '<mujoco model="shanghai_city_twin_scene">',
            '  <compiler angle="radian" meshdir="meshes"/>',
            '  <option timestep="0.002" gravity="0 0 -9.81"/>',
            f'  <statistic center="{view["center"]}" extent="{view["extent"]}"/>',
            "  <visual>",
            '    <headlight ambient="0.35 0.35 0.35" diffuse="0.75 0.75 0.72" specular="0.1 0.1 0.1"/>',
            f'    <map znear="0.1" zfar="{view["zfar"]}"/>',
            '    <global offwidth="1280" offheight="720"/>',
            "  </visual>",
            "  <asset>",
            '    <texture type="skybox" builtin="gradient" rgb1="0.92 0.96 1" rgb2="0.64 0.72 0.82" width="512" height="512"/>',
            '    <mesh name="scene_visual" file="scene_visual.obj"/>',
            '    <mesh name="scene_collision" file="scene_collision.obj"/>',
            "  </asset>",
            "  <worldbody>",
            f'    <light name="city_key_light" pos="{view["key_light_pos"]}" dir="{view["key_light_dir"]}" directional="true" diffuse="0.9 0.88 0.8"/>',
            f'    <light name="city_fill_light" pos="{view["fill_light_pos"]}" dir="{view["fill_light_dir"]}" directional="true" diffuse="0.35 0.42 0.5"/>',
            f'    <camera name="overview" pos="{view["camera_pos"]}" xyaxes="1 0 0 0 0.45 0.89"/>',
            f'    <geom name="review_ground" type="plane" pos="{view["ground_pos"]}" size="{view["ground_size"]}" rgba="0.88 0.91 0.94 1" contype="0" conaffinity="0"/>',
            '    <body name="static_scene" pos="0 0 0">',
            '      <geom name="scene_collision_geom" type="mesh" mesh="scene_collision" contype="1" conaffinity="1" friction="0.8 0.1 0.1" rgba="0.18 0.24 0.32 0.16"/>',
            '      <geom name="scene_visual_geom" type="mesh" mesh="scene_visual" contype="0" conaffinity="0" rgba="0.74 0.82 0.9 1"/>',
            "    </body>",
            "  </worldbody>",
            "</mujoco>",
            "",
        ]
    )


def _build_urdf(scene: dict[str, Any]) -> str:
    return "\n".join(
        [
            '<robot name="shanghai_city_twin_scene">',
            '  <link name="static_scene">',
            "    <visual>",
            "      <geometry>",
            f'        <mesh filename="{_xml_attr(scene["visual_mesh"])}"/>',
            "      </geometry>",
            "    </visual>",
            "    <collision>",
            "      <geometry>",
            f'        <mesh filename="{_xml_attr(scene["collision_mesh"])}"/>',
            "      </geometry>",
            "    </collision>",
            "  </link>",
            "</robot>",
            "",
        ]
    )


def _build_scene_index(scene: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": "shanghai_city_twin_scene",
        "type": "motrix_scene_package",
        "entry": "scene.xml",
        "entries": {"mjcf": "scene.xml", "urdf": "scene.urdf"},
        "assets": {
            "visual_mesh": scene["visual_mesh"],
            "collision_mesh": scene["collision_mesh"],
            "scene_manifest": "metadata/scene_manifest.json",
            "object_manifest": "metadata/object_manifest.json",
            "objects": {},
        },
        "metadata": "metadata/asset_manifest.json",
    }


def _source_to_motrix_scale(bbox: BBox, max_scene_extent_m: float) -> float:
    origin = bbox_center(bbox)
    corners = [
        lonlat_to_local_m(bbox.west, bbox.south, origin),
        lonlat_to_local_m(bbox.east, bbox.south, origin),
        lonlat_to_local_m(bbox.east, bbox.north, origin),
        lonlat_to_local_m(bbox.west, bbox.north, origin),
    ]
    width = max(point[0] for point in corners) - min(point[0] for point in corners)
    height = max(point[1] for point in corners) - min(point[1] for point in corners)
    extent = max(width, height)
    if extent <= 0:
        return 1.0
    return round(min(1.0, max_scene_extent_m / extent), 8)


def _scene_view(scene: dict[str, Any]) -> dict[str, str]:
    bbox = scene.get("local_bbox") if isinstance(scene.get("local_bbox"), dict) else None
    if not bbox:
        bbox = {"min": {"x": -50.0, "y": -50.0, "z": 0.0}, "max": {"x": 50.0, "y": 50.0, "z": 50.0}}
    min_pt = bbox["min"]
    max_pt = bbox["max"]
    center_x = (float(min_pt["x"]) + float(max_pt["x"])) / 2.0
    center_y = (float(min_pt["y"]) + float(max_pt["y"])) / 2.0
    center_z = (float(min_pt["z"]) + float(max_pt["z"])) / 2.0
    extent = max(_bbox_extent(bbox), 10.0)
    zfar = max(extent * 8.0, 1000.0)
    camera_z = max(center_z + extent * 0.75, float(max_pt["z"]) + extent * 0.25)
    camera_y = center_y - extent * 1.35
    return {
        "center": _triple(center_x, center_y, center_z),
        "extent": _fmt(extent),
        "zfar": _fmt(zfar),
        "camera_pos": _triple(center_x, camera_y, camera_z),
        "key_light_pos": _triple(center_x - extent * 0.25, center_y - extent * 0.8, center_z + extent * 1.4),
        "key_light_dir": _triple(0.15, 0.65, -1.0),
        "fill_light_pos": _triple(center_x + extent * 0.8, center_y + extent * 0.6, center_z + extent),
        "fill_light_dir": _triple(-0.55, -0.45, -1.0),
        "ground_pos": _triple(center_x, center_y, -0.05),
        "ground_size": f"{_fmt(extent * 0.75)} {_fmt(extent * 0.75)} 0.1",
    }


def _scaled_local(lon: float, lat: float, origin: tuple[float, float], scale: float) -> tuple[float, float]:
    x, y = lonlat_to_local_m(lon, lat, origin)
    return x * scale, y * scale


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


def _is_coord(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) >= 2
        and isinstance(value[0], (int, float))
        and isinstance(value[1], (int, float))
    )


def _obj_text(name: str, vertices: list[tuple[float, float, float]], faces: list[tuple[int, int, int]]) -> str:
    lines = [f"o {name}"]
    lines.extend(f"v {x:.6f} {y:.6f} {z:.6f}" for x, y, z in vertices)
    lines.extend(f"f {a} {b} {c}" for a, b, c in faces)
    return "\n".join(lines) + "\n"


def _obj_counts(path: Path) -> dict[str, int]:
    if not path.exists():
        return {"vertices": 0, "faces": 0}
    vertices = 0
    faces = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("v "):
            vertices += 1
        elif line.startswith("f "):
            faces += 1
    return {"vertices": vertices, "faces": faces}


def _points_bounds(points: list[tuple[float, float, float]]) -> dict[str, dict[str, float]]:
    if not points:
        return {"min": {"x": 0.0, "y": 0.0, "z": 0.0}, "max": {"x": 0.0, "y": 0.0, "z": 0.0}}
    return {
        "min": {"x": min(p[0] for p in points), "y": min(p[1] for p in points), "z": min(p[2] for p in points)},
        "max": {"x": max(p[0] for p in points), "y": max(p[1] for p in points), "z": max(p[2] for p in points)},
    }


def _bbox_extent(bbox: dict[str, dict[str, float]] | None) -> float:
    if not bbox:
        return 0.0
    return max(float(bbox["max"][axis]) - float(bbox["min"][axis]) for axis in ("x", "y", "z"))


def _obj_bounds(path: Path) -> dict[str, dict[str, float]] | None:
    if not path.exists():
        return None
    points: list[tuple[float, float, float]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("v "):
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        points.append((float(parts[1]), float(parts[2]), float(parts[3])))
    if not points:
        return None
    return {
        "min": {"x": min(p[0] for p in points), "y": min(p[1] for p in points), "z": min(p[2] for p in points)},
        "max": {"x": max(p[0] for p in points), "y": max(p[1] for p in points), "z": max(p[2] for p in points)},
    }


def _parse_xml(path: Path, issues: list[dict[str, str]], label: str):
    if not path.exists():
        return None
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        issues.append({"level": "error", "message": f"{label} is not valid XML: {exc}"})
        return None


def _parse_json(path: Path, issues: list[dict[str, str]], label: str):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append({"level": "error", "message": f"{label} is not valid JSON: {exc}"})
        return None


def _walk_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from _walk_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_strings(child)


def _check_relative(value: str, issues: list[dict[str, str]], label: str) -> None:
    posix = PurePosixPath(value)
    if posix.is_absolute() or ".." in posix.parts:
        issues.append({"level": "error", "message": f"{label} path must be relative and portable: {value}"})


def _resolve_relative(root: Path, value: str, issues: list[dict[str, str]]) -> Path:
    posix = PurePosixPath(value)
    candidate = (root / Path(*posix.parts)).resolve()
    root_resolved = root.resolve()
    if root_resolved != candidate and root_resolved not in candidate.parents:
        issues.append({"level": "error", "message": f"path escapes package root: {value}"})
    return candidate


def _zip_package(package_dir: Path) -> Path:
    zip_path = package_dir.parent / "motrix_scene.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(package_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(package_dir.parent))
    return zip_path


def _xml_attr(value: Any) -> str:
    return escape(str(value), {'"': "&quot;"})


def _fmt(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".")


def _triple(x: float, y: float, z: float) -> str:
    return f"{_fmt(x)} {_fmt(y)} {_fmt(z)}"


def _readme() -> str:
    return """# Shanghai City Digital Twin MotrixSim Package

This folder is a MotrixSim-compatible scene package generated from real OpenStreetMap data.

Import steps:
1. Open MotrixSim Web Viewer.
2. Drag this entire `motrix_scene` folder into the viewer, or unzip `motrix_scene.zip`.
3. Load `scene.xml`, `scene.urdf`, or `scene.json`.

Notes:
- `meshes/scene_visual.obj` contains real height-tagged building geometry.
- `meshes/scene_collision.obj` contains simplified box collision per exported building.
- Buildings without real `height_m` were not extruded.
- The package may be scaled to satisfy MotrixSim bbox limits. See `metadata/asset_manifest.json`.
- `review.html` is a self-contained browser preview for quick visual review.
"""


def _review_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Motrix Scene Review</title>
  <style>
    html, body { margin: 0; height: 100%; background: #f5f7fb; color: #17202a; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    #wrap { display: grid; grid-template-columns: 1fr 300px; height: 100%; }
    canvas { width: 100%; height: 100%; display: block; background: linear-gradient(#ffffff, #e6ecf5); }
    aside { border-left: 1px solid #ccd5e1; background: #ffffff; padding: 16px; overflow: auto; }
    h1 { font-size: 18px; margin: 0 0 14px; }
    dl { display: grid; grid-template-columns: auto 1fr; gap: 8px 12px; font-size: 13px; }
    dt { color: #5b6675; }
    dd { margin: 0; font-variant-numeric: tabular-nums; }
    button { border: 1px solid #b7c2d0; background: #f8fafc; border-radius: 6px; padding: 7px 10px; margin: 4px 4px 4px 0; cursor: pointer; }
    #status { font-size: 13px; color: #516071; margin-top: 12px; white-space: pre-wrap; }
    @media (max-width: 820px) { #wrap { grid-template-columns: 1fr; grid-template-rows: 1fr auto; } aside { border-left: 0; border-top: 1px solid #ccd5e1; max-height: 34vh; } }
  </style>
</head>
<body>
  <div id="wrap">
    <canvas id="view"></canvas>
    <aside>
      <h1>Shanghai Motrix Scene</h1>
      <p style="font-size:13px;color:#516071;margin-top:0">Drag to rotate. Wheel to zoom.</p>
      <button id="iso">Iso</button><button id="top">Top</button><button id="fit">Fit</button>
      <dl id="stats"></dl>
      <div id="status">Loading OBJ...</div>
    </aside>
  </div>
  <script>
    const canvas = document.getElementById("view");
    const ctx = canvas.getContext("2d");
    const statusEl = document.getElementById("status");
    const statsEl = document.getElementById("stats");
    let verts = [], faces = [], bounds = null;
    let yaw = -0.75, pitch = 0.9, zoom = 1, dragging = false, last = [0, 0];

    function resize() {
      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.max(1, Math.floor(canvas.clientWidth * dpr));
      canvas.height = Math.max(1, Math.floor(canvas.clientHeight * dpr));
      draw();
    }
    window.addEventListener("resize", resize);

    function parseObj(text) {
      const vs = [], fs = [];
      for (const line of text.split(/\\r?\\n/)) {
        if (line.startsWith("v ")) {
          const p = line.trim().split(/\\s+/).slice(1).map(Number);
          if (p.length >= 3 && p.every(Number.isFinite)) vs.push(p);
        } else if (line.startsWith("f ")) {
          const idx = line.trim().split(/\\s+/).slice(1).map(v => Number(v.split("/")[0]) - 1);
          if (idx.length >= 3 && idx.every(i => Number.isInteger(i) && i >= 0)) fs.push(idx.slice(0, 3));
        }
      }
      return [vs, fs];
    }

    function computeBounds(vs) {
      const b = {min:[Infinity,Infinity,Infinity], max:[-Infinity,-Infinity,-Infinity]};
      for (const v of vs) for (let i = 0; i < 3; i++) { b.min[i] = Math.min(b.min[i], v[i]); b.max[i] = Math.max(b.max[i], v[i]); }
      b.center = b.min.map((v, i) => (v + b.max[i]) / 2);
      b.extent = Math.max(...b.max.map((v, i) => v - b.min[i]));
      return b;
    }

    function transform(v) {
      const x0 = v[0] - bounds.center[0], y0 = v[1] - bounds.center[1], z0 = v[2] - bounds.center[2];
      const cy = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch);
      const x1 = x0 * cy - y0 * sy;
      const y1 = x0 * sy + y0 * cy;
      const z1 = z0;
      return [x1, y1 * cp - z1 * sp, y1 * sp + z1 * cp];
    }

    function draw() {
      if (!bounds) return;
      const w = canvas.width, h = canvas.height;
      ctx.clearRect(0, 0, w, h);
      const scale = 0.78 * Math.min(w, h) / bounds.extent * zoom;
      const projected = verts.map(v => {
        const t = transform(v);
        return [w / 2 + t[0] * scale, h / 2 - t[1] * scale, t[2]];
      });
      const items = faces.map(f => {
        const a = projected[f[0]], b = projected[f[1]], c = projected[f[2]];
        const z = (a[2] + b[2] + c[2]) / 3;
        const height = (verts[f[0]][2] + verts[f[1]][2] + verts[f[2]][2]) / 3;
        return {f, z, height};
      }).sort((a, b) => a.z - b.z);
      for (const item of items) {
        const p = item.f.map(i => projected[i]);
        const shade = Math.max(0, Math.min(1, item.height / Math.max(1, bounds.max[2])));
        ctx.beginPath();
        ctx.moveTo(p[0][0], p[0][1]);
        ctx.lineTo(p[1][0], p[1][1]);
        ctx.lineTo(p[2][0], p[2][1]);
        ctx.closePath();
        ctx.fillStyle = `rgb(${Math.round(120 + shade * 70)}, ${Math.round(155 + shade * 55)}, ${Math.round(190 + shade * 35)})`;
        ctx.fill();
        ctx.strokeStyle = "rgba(46, 59, 78, 0.12)";
        ctx.lineWidth = Math.max(1, window.devicePixelRatio || 1);
        ctx.stroke();
      }
    }

    canvas.addEventListener("pointerdown", e => { dragging = true; last = [e.clientX, e.clientY]; canvas.setPointerCapture(e.pointerId); });
    canvas.addEventListener("pointermove", e => {
      if (!dragging) return;
      yaw += (e.clientX - last[0]) * 0.006;
      pitch = Math.max(0.15, Math.min(1.45, pitch + (e.clientY - last[1]) * 0.006));
      last = [e.clientX, e.clientY];
      draw();
    });
    canvas.addEventListener("pointerup", () => { dragging = false; });
    canvas.addEventListener("wheel", e => { e.preventDefault(); zoom *= Math.exp(-e.deltaY * 0.001); zoom = Math.max(0.25, Math.min(8, zoom)); draw(); }, {passive:false});
    document.getElementById("iso").onclick = () => { yaw = -0.75; pitch = 0.9; draw(); };
    document.getElementById("top").onclick = () => { yaw = 0; pitch = 0.01; draw(); };
    document.getElementById("fit").onclick = () => { zoom = 1; draw(); };

    async function load() {
      const [manifest, obj] = await Promise.all([
        fetch("metadata/asset_manifest.json").then(r => r.json()),
        fetch("meshes/scene_visual.obj").then(r => r.text())
      ]);
      [verts, faces] = parseObj(obj);
      bounds = computeBounds(verts);
      statsEl.innerHTML = [
        ["Buildings", manifest.mesh_generation.exported_buildings],
        ["Visual faces", manifest.mesh_generation.visual_faces],
        ["Collision faces", manifest.mesh_generation.collision_faces],
        ["Scale", manifest.source_to_motrix_scale],
        ["Extent", bounds.extent.toFixed(2) + " m"],
        ["Height", bounds.max[2].toFixed(2) + " m"]
      ].map(([k,v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("");
      statusEl.textContent = "Loaded. Use the buttons or drag the scene.";
      resize();
    }
    load().catch(err => { statusEl.textContent = "Failed to load scene: " + err.message; });
  </script>
</body>
</html>
"""
