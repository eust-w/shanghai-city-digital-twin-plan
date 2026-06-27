from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .config import BBox
from .geometry import bbox_center, lonlat_to_local_m


def build_unreal_obj(buildings_layer: dict[str, Any], bbox: BBox) -> tuple[str, str, dict[str, Any]]:
    origin = bbox_center(bbox)
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int]] = []
    exported = 0
    skipped_missing_height = 0
    skipped_invalid_geometry = 0
    max_height_cm = 0.0

    for feature in buildings_layer.get("features", []):
        height = feature.get("properties", {}).get("height_m")
        if not isinstance(height, (int, float)) or height <= 0:
            skipped_missing_height += 1
            continue
        ring = _outer_ring(feature)
        if len(ring) < 3:
            skipped_invalid_geometry += 1
            continue
        base_index = len(vertices) + 1
        local = [lonlat_to_local_m(lon, lat, origin) for lon, lat in ring]
        height_cm = float(height) * 100.0
        for x, y in local:
            vertices.append((x * 100.0, y * 100.0, 0.0))
        for x, y in local:
            vertices.append((x * 100.0, y * 100.0, height_cm))
        count = len(local)
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
        exported += 1
        max_height_cm = max(max_height_cm, height_cm)

    obj_lines = [
        "# Shanghai City Digital Twin POC buildings for Unreal Engine",
        "# Units: centimeters; X/Y are local projected meters scaled to cm, Z is height cm.",
        "mtllib shanghai_city_twin_buildings.mtl",
        "o shanghai_city_twin_buildings",
        "usemtl building_neutral",
    ]
    obj_lines.extend(f"v {x:.3f} {y:.3f} {z:.3f}" for x, y, z in vertices)
    obj_lines.extend(f"f {a} {b} {c}" for a, b, c in faces)
    mtl = "\n".join(
        [
            "newmtl building_neutral",
            "Ka 0.55 0.58 0.60",
            "Kd 0.55 0.58 0.60",
            "Ks 0.08 0.08 0.08",
            "Ns 12",
            "d 1.0",
            "",
        ]
    )
    manifest = {
        "obj": "shanghai_city_twin_buildings.obj",
        "mtl": "shanghai_city_twin_buildings.mtl",
        "unit": "centimeters",
        "origin_lon": origin[0],
        "origin_lat": origin[1],
        "exported_buildings": exported,
        "skipped_missing_height": skipped_missing_height,
        "skipped_invalid_geometry": skipped_invalid_geometry,
        "vertex_count": len(vertices),
        "triangle_count": len(faces),
        "max_height_cm": round(max_height_cm, 3),
    }
    return "\n".join(obj_lines) + "\n", mtl, manifest


def write_unreal_scene_package(
    layers: dict[str, dict[str, Any]],
    bbox: BBox,
    output_dir: Path,
) -> dict[str, Any]:
    source_dir = output_dir / "Content" / "CityTwin" / "Source"
    scripts_dir = output_dir / "Scripts"
    config_dir = output_dir / "Config"
    source_dir.mkdir(parents=True, exist_ok=True)
    scripts_dir.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)

    obj, mtl, obj_manifest = build_unreal_obj(layers.get("buildings", {"features": []}), bbox)
    (source_dir / "shanghai_city_twin_buildings.obj").write_text(obj, encoding="utf-8")
    (source_dir / "shanghai_city_twin_buildings.mtl").write_text(mtl, encoding="utf-8")
    for layer_name, layer in layers.items():
        (source_dir / f"{layer_name}.geojson").write_text(
            json.dumps(layer, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    uproject = _uproject()
    (output_dir / "ShanghaiCityTwinPOC.uproject").write_text(
        json.dumps(uproject, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (config_dir / "DefaultEngine.ini").write_text(_default_engine_ini(), encoding="utf-8")
    (scripts_dir / "import_city_twin_scene.py").write_text(_import_script(), encoding="utf-8")
    (output_dir / "README_UNREAL.md").write_text(_readme(), encoding="utf-8")

    manifest = {
        "artifacts": {
            "unreal_project": "ShanghaiCityTwinPOC.uproject",
            "unreal_import_script": "Scripts/import_city_twin_scene.py",
            "unreal_obj": "Content/CityTwin/Source/shanghai_city_twin_buildings.obj",
            "unreal_mtl": "Content/CityTwin/Source/shanghai_city_twin_buildings.mtl",
            "unreal_readme": "README_UNREAL.md",
        },
        "buildings_obj": obj_manifest,
        "bbox": {
            "south": bbox.south,
            "west": bbox.west,
            "north": bbox.north,
            "east": bbox.east,
        },
    }
    (output_dir / "scene_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def sync_unreal_package_assets(source_package: Path, output_package: Path) -> None:
    if output_package.exists():
        shutil.rmtree(output_package)
    shutil.copytree(source_package, output_package)


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


def _uproject() -> dict[str, Any]:
    return {
        "FileVersion": 3,
        "EngineAssociation": "5.4",
        "Category": "DigitalTwin",
        "Description": "Shanghai City Digital Twin real-data POC import package.",
        "Modules": [],
        "Plugins": [
            {"Name": "PythonScriptPlugin", "Enabled": True},
            {"Name": "EditorScriptingUtilities", "Enabled": True},
        ],
    }


def _default_engine_ini() -> str:
    return """[/Script/EngineSettings.GameMapsSettings]
EditorStartupMap=/Game/CityTwin/Maps/ShanghaiCityTwinPOC
GameDefaultMap=/Game/CityTwin/Maps/ShanghaiCityTwinPOC
"""


def _import_script() -> str:
    return r'''import os
import unreal

PROJECT_DIR = unreal.Paths.project_dir()
SOURCE_DIR = os.path.join(PROJECT_DIR, "Content", "CityTwin", "Source")
OBJ_FILE = os.path.join(SOURCE_DIR, "shanghai_city_twin_buildings.obj")
DEST_PATH = "/Game/CityTwin/Imported"
MAP_PATH = "/Game/CityTwin/Maps/ShanghaiCityTwinPOC"


def log(message):
    unreal.log("[ShanghaiCityTwinPOC] " + message)


def ensure_dir(path):
    unreal.EditorAssetLibrary.make_directory(path)


def import_obj():
    if not os.path.exists(OBJ_FILE):
        raise RuntimeError("Missing OBJ source: " + OBJ_FILE)
    ensure_dir(DEST_PATH)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", OBJ_FILE)
    task.set_editor_property("destination_path", DEST_PATH)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported = list(task.get_editor_property("imported_object_paths") or [])
    if not imported:
        raise RuntimeError("OBJ import produced no assets. Confirm the OBJ importer is available in this Unreal build.")
    log("Imported assets: " + ", ".join(imported))
    return imported[0]


def new_level(path):
    ensure_dir("/Game/CityTwin/Maps")
    if hasattr(unreal, "LevelEditorSubsystem"):
        subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        if hasattr(subsystem, "new_level"):
            subsystem.new_level(path)
            return
    unreal.EditorLevelLibrary.new_level(path)


def spawn_actor(asset_path):
    mesh = unreal.EditorAssetLibrary.load_asset(asset_path)
    if mesh is None:
        raise RuntimeError("Unable to load imported mesh: " + asset_path)
    location = unreal.Vector(0.0, 0.0, 0.0)
    actor = None
    if hasattr(unreal, "EditorActorSubsystem"):
        actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
        if hasattr(actor_subsystem, "spawn_actor_from_object"):
            actor = actor_subsystem.spawn_actor_from_object(mesh, location)
    if actor is None:
        actor = unreal.EditorLevelLibrary.spawn_actor_from_object(mesh, location)
    actor.set_actor_label("Shanghai_OSM_Buildings_LOD1")
    return actor


def add_lighting_and_camera():
    if hasattr(unreal, "DirectionalLight"):
        light = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(-50000, -50000, 90000))
        light.set_actor_label("Sun_Key_Light")
        light.set_actor_rotation(unreal.Rotator(-45.0, 45.0, 0.0), False)
    if hasattr(unreal, "CameraActor"):
        camera = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(-180000, -180000, 140000))
        camera.set_actor_label("POC_Overview_Camera")
        camera.set_actor_rotation(unreal.Rotator(-35.0, 45.0, 0.0), False)


def save_all():
    unreal.EditorAssetLibrary.save_directory("/Game/CityTwin", only_if_is_dirty=False, recursive=True)
    if hasattr(unreal, "EditorLoadingAndSavingUtils"):
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)


asset = import_obj()
new_level(MAP_PATH)
spawn_actor(asset)
add_lighting_and_camera()
save_all()
log("Scene ready: " + MAP_PATH)
'''


def _readme() -> str:
    return """# Unreal 导入包

这个目录是由真实 OSM/Overpass POC 数据生成的 Unreal Engine 导入包。

## 内容

- `ShanghaiCityTwinPOC.uproject`：最小 UE 项目文件。
- `Content/CityTwin/Source/shanghai_city_twin_buildings.obj`：厘米单位建筑体块 OBJ。
- `Content/CityTwin/Source/*.geojson`：原始标准化图层，供后续蓝图/编辑器工具使用。
- `Scripts/import_city_twin_scene.py`：导入 OBJ、创建关卡、生成建筑 Actor、添加光照和相机。
- `scene_manifest.json`：导入包统计。

## 导入命令

```bash
/path/to/UnrealEditor data/poc-shanghai-core/unreal/ShanghaiCityTwinPOC.uproject \\
  -ExecutePythonScript=data/poc-shanghai-core/unreal/Scripts/import_city_twin_scene.py
```

macOS 示例：

```bash
/Applications/UE_5.4/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor \\
  data/poc-shanghai-core/unreal/ShanghaiCityTwinPOC.uproject \\
  -ExecutePythonScript=data/poc-shanghai-core/unreal/Scripts/import_city_twin_scene.py
```

本机当前未检测到 Unreal Editor，因此本仓库只验证到“可导入包生成完成”。有 UE 的机器执行上面的命令后，会在 `/Game/CityTwin/Maps/ShanghaiCityTwinPOC` 生成关卡。
"""
