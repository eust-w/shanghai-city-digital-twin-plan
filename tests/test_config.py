import json
import tempfile
import unittest
from pathlib import Path

from city_twin_pipeline.config import ConfigError, load_config


class ConfigTests(unittest.TestCase):
    def write_config(self, payload: dict) -> Path:
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        path = Path(tmpdir.name) / "config.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def valid_payload(self) -> dict:
        return {
            "project": {
                "name": "Shanghai POC",
                "area_name": "Lujiazui",
                "standard_crs": "EPSG:4326",
            },
            "poc_area": {
                "south": 31.2307,
                "west": 121.4893,
                "north": 31.2488,
                "east": 121.5103,
            },
            "sources": {
                "osm": {
                    "endpoint": "https://overpass-api.de/api/interpreter",
                    "license": "ODbL-1.0",
                    "attribution": "© OpenStreetMap contributors",
                    "timeout_seconds": 180,
                }
            },
            "layers": {
                "buildings": [{"type": "way", "tags": {"building": "*"}}],
                "roads": [{"type": "way", "tags": {"highway": "*"}}],
                "water": [{"type": "way", "tags": {"natural": "water"}}],
                "pois": [{"type": "node", "tags": {"amenity": "*"}}],
            },
            "height": {"level_height_m": 3.2},
            "quality": {"minimum_counts": {"buildings": 1, "roads": 1}},
        }

    def test_load_config_accepts_complete_real_source_config(self):
        config = load_config(self.write_config(self.valid_payload()))

        self.assertEqual(config.project.name, "Shanghai POC")
        self.assertEqual(config.bbox.as_overpass_bbox(), "31.2307,121.4893,31.2488,121.5103")
        self.assertEqual(config.sources["osm"].license, "ODbL-1.0")

    def test_load_config_rejects_invalid_bbox_order(self):
        payload = self.valid_payload()
        payload["poc_area"]["south"] = payload["poc_area"]["north"]

        with self.assertRaisesRegex(ConfigError, "south.*north"):
            load_config(self.write_config(payload))

    def test_load_config_rejects_google_endpoint_as_asset_source(self):
        payload = self.valid_payload()
        payload["sources"]["osm"]["endpoint"] = "https://tile.googleapis.com/v1/3dtiles/root.json"

        with self.assertRaisesRegex(ConfigError, "Google.*online visual reference"):
            load_config(self.write_config(payload))


if __name__ == "__main__":
    unittest.main()
