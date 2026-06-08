import json
import tempfile
import unittest
from pathlib import Path

from city_twin_pipeline.config import BBox
from city_twin_pipeline.gltf import build_buildings_gltf
from city_twin_pipeline.tiles3d import build_tileset_json


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


class AssetExportTests(unittest.TestCase):
    def test_buildings_gltf_exports_only_buildings_with_real_height(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = build_buildings_gltf(
                building_layer(),
                BBox(south=31.0, west=121.0, north=31.01, east=121.01),
                Path(tmp),
            )

            gltf = json.loads((Path(tmp) / "buildings.gltf").read_text(encoding="utf-8"))
            self.assertEqual(gltf["asset"]["version"], "2.0")
            self.assertEqual(manifest["exported_buildings"], 1)
            self.assertEqual(manifest["skipped_missing_height"], 1)
            self.assertTrue((Path(tmp) / "buildings.bin").exists())

    def test_tileset_json_uses_region_in_radians_and_points_to_gltf_content(self):
        tileset = build_tileset_json(
            BBox(south=31.0, west=121.0, north=31.01, east=121.01),
            content_uri="../gltf/buildings.gltf",
            min_height=0,
            max_height=120,
        )

        self.assertEqual(tileset["asset"]["version"], "1.1")
        self.assertEqual(tileset["root"]["content"]["uri"], "../gltf/buildings.gltf")
        self.assertAlmostEqual(tileset["root"]["boundingVolume"]["region"][0], 2.111848, places=5)


if __name__ == "__main__":
    unittest.main()
