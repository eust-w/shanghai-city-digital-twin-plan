import json
import tempfile
import unittest
from pathlib import Path

from city_twin_pipeline.config import BBox
from city_twin_pipeline.unreal_export import build_unreal_obj, write_unreal_scene_package


def building_layer():
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[121.0, 31.0], [121.001, 31.0], [121.001, 31.001], [121.0, 31.001], [121.0, 31.0]]],
                },
                "properties": {"osm_id": "way/1", "height_m": 12.5},
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[121.002, 31.0], [121.003, 31.0], [121.003, 31.001], [121.002, 31.001], [121.002, 31.0]]],
                },
                "properties": {"osm_id": "way/2", "height_m": None},
            },
        ],
    }


class UnrealExportTests(unittest.TestCase):
    def test_build_unreal_obj_exports_centimeter_obj_only_for_real_height_buildings(self):
        obj, mtl, manifest = build_unreal_obj(
            building_layer(),
            BBox(south=31.0, west=121.0, north=31.01, east=121.01),
        )

        self.assertIn("mtllib shanghai_city_twin_buildings.mtl", obj)
        self.assertIn("v ", obj)
        self.assertIn("1250.000", obj)
        self.assertIn("usemtl building_neutral", obj)
        self.assertIn("newmtl building_neutral", mtl)
        self.assertEqual(manifest["exported_buildings"], 1)
        self.assertEqual(manifest["skipped_missing_height"], 1)
        self.assertEqual(manifest["unit"], "centimeters")

    def test_write_unreal_scene_package_creates_project_import_script_and_source_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            manifest = write_unreal_scene_package(
                {"buildings": building_layer()},
                BBox(south=31.0, west=121.0, north=31.01, east=121.01),
                out,
            )

            uproject = json.loads((out / "ShanghaiCityTwinPOC.uproject").read_text(encoding="utf-8"))
            self.assertEqual(uproject["FileVersion"], 3)
            self.assertTrue((out / "Content" / "CityTwin" / "Source" / "shanghai_city_twin_buildings.obj").exists())
            self.assertTrue((out / "Scripts" / "import_city_twin_scene.py").exists())
            script = (out / "Scripts" / "import_city_twin_scene.py").read_text(encoding="utf-8")
            self.assertIn("AssetImportTask", script)
            self.assertIn("spawn_actor", script)
            self.assertEqual(manifest["artifacts"]["unreal_project"], "ShanghaiCityTwinPOC.uproject")


if __name__ == "__main__":
    unittest.main()
