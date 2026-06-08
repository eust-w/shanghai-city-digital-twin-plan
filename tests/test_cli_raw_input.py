import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from city_twin_pipeline.cli import run_poc


class CLIRawInputTests(unittest.TestCase):
    def test_run_poc_can_process_existing_real_overpass_raw_without_fetching_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "config.json"
            raw = root / "raw.json"
            out = root / "out"
            config.write_text(json.dumps(_config()), encoding="utf-8")
            raw.write_text(json.dumps(_raw()), encoding="utf-8")

            with redirect_stdout(StringIO()):
                status = run_poc(config, out, raw_input=raw)

            self.assertEqual(status, "pass")
            self.assertTrue((out / "unreal" / "ShanghaiCityTwinPOC.uproject").exists())
            self.assertTrue((out / "unreal" / "Scripts" / "import_city_twin_scene.py").exists())
            self.assertTrue((out / "raw" / "osm_overpass.json").exists())


def _config():
    return {
        "project": {"name": "Test", "area_name": "Test", "standard_crs": "EPSG:4326"},
        "poc_area": {"south": 31.0, "west": 121.0, "north": 31.01, "east": 121.01},
        "sources": {
            "osm": {
                "endpoint": "http://overpass-api.de/api/interpreter",
                "license": "ODbL-1.0",
                "attribution": "© OpenStreetMap contributors",
                "timeout_seconds": 3,
            }
        },
        "layers": {
            "buildings": [{"type": "way", "tags": {"building": "*"}}],
            "roads": [{"type": "way", "tags": {"highway": "*"}}],
        },
        "height": {"level_height_m": 3.2},
        "quality": {"minimum_counts": {"buildings": 1, "roads": 1}},
    }


def _raw():
    return {
        "osm3s": {"timestamp_osm_base": "2026-06-08T00:00:00Z"},
        "elements": [
            {"type": "node", "id": 1, "lat": 31.001, "lon": 121.001},
            {"type": "node", "id": 2, "lat": 31.001, "lon": 121.002},
            {"type": "node", "id": 3, "lat": 31.002, "lon": 121.002},
            {"type": "node", "id": 4, "lat": 31.002, "lon": 121.001},
            {"type": "node", "id": 10, "lat": 31.003, "lon": 121.001},
            {"type": "node", "id": 11, "lat": 31.003, "lon": 121.002},
            {"type": "way", "id": 100, "nodes": [1, 2, 3, 4, 1], "tags": {"building": "yes", "height": "10"}},
            {"type": "way", "id": 200, "nodes": [10, 11], "tags": {"highway": "residential"}},
        ],
    }


if __name__ == "__main__":
    unittest.main()
