from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import PipelineConfig
from .gltf import build_buildings_gltf
from .motrix_export import build_motrix_package
from .opendrive import build_opendrive_xml
from .outputs import write_json
from .postgis import build_postgis_sql
from .sumo import build_sumo_plain_xml
from .tiles3d import build_tileset_json
from .tiling import tile_metadata
from .unreal_export import write_unreal_scene_package
from .viewer import write_static_viewer


def export_runtime_artifacts(
    layers: dict[str, dict[str, Any]],
    config: PipelineConfig,
    output_dir: Path,
) -> dict[str, Any]:
    manifest: dict[str, Any] = {"artifacts": {}}
    write_json(output_dir / "tiles" / "tile_grid.json", tile_metadata(config.bbox, rows=2, cols=2))
    manifest["artifacts"]["tile_grid"] = "tiles/tile_grid.json"

    gltf_manifest = build_buildings_gltf(layers.get("buildings", {"features": []}), config.bbox, output_dir / "gltf")
    manifest["artifacts"]["buildings_gltf"] = "gltf/buildings.gltf"
    manifest["buildings_gltf"] = gltf_manifest

    tileset = build_tileset_json(
        config.bbox,
        content_uri="../../gltf/buildings.gltf",
        min_height=0,
        max_height=max(1.0, float(gltf_manifest.get("max_height_m", 0) or 0)),
    )
    write_json(output_dir / "3dtiles" / "buildings" / "tileset.json", tileset)
    manifest["artifacts"]["buildings_3dtiles"] = "3dtiles/buildings/tileset.json"

    sumo_files = build_sumo_plain_xml(layers.get("roads", {"features": []}), config.bbox)
    (output_dir / "sim" / "sumo").mkdir(parents=True, exist_ok=True)
    (output_dir / "sim" / "sumo" / "shanghai_poc.nod.xml").write_text(sumo_files["nodes"], encoding="utf-8")
    (output_dir / "sim" / "sumo" / "shanghai_poc.edg.xml").write_text(sumo_files["edges"], encoding="utf-8")
    manifest["artifacts"]["sumo_nodes"] = "sim/sumo/shanghai_poc.nod.xml"
    manifest["artifacts"]["sumo_edges"] = "sim/sumo/shanghai_poc.edg.xml"

    (output_dir / "sim" / "opendrive").mkdir(parents=True, exist_ok=True)
    (output_dir / "sim" / "opendrive" / "shanghai_poc.xodr").write_text(
        build_opendrive_xml(layers.get("roads", {"features": []}), config.bbox),
        encoding="utf-8",
    )
    manifest["artifacts"]["opendrive"] = "sim/opendrive/shanghai_poc.xodr"

    (output_dir / "db").mkdir(parents=True, exist_ok=True)
    (output_dir / "db" / "postgis_load.sql").write_text(build_postgis_sql(layers), encoding="utf-8")
    manifest["artifacts"]["postgis_load_sql"] = "db/postgis_load.sql"

    write_static_viewer(output_dir / "viewer", list(layers.keys()))
    manifest["artifacts"]["cesium_viewer"] = "viewer/index.html"

    unreal_manifest = write_unreal_scene_package(layers, config.bbox, output_dir / "unreal")
    manifest["artifacts"]["unreal_project"] = "unreal/ShanghaiCityTwinPOC.uproject"
    manifest["artifacts"]["unreal_import_script"] = "unreal/Scripts/import_city_twin_scene.py"
    manifest["unreal"] = unreal_manifest

    motrix_result = build_motrix_package(layers, config.bbox, output_dir)
    manifest["artifacts"]["motrix_scene"] = "motrix_scene"
    manifest["artifacts"]["motrix_scene_zip"] = "motrix_scene.zip"
    manifest["motrix"] = motrix_result

    write_json(output_dir / "reports" / "export_manifest.json", manifest)
    return manifest
