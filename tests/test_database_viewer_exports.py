import tempfile
import unittest
from pathlib import Path

from city_twin_pipeline.postgis import build_postgis_sql
from city_twin_pipeline.viewer import write_static_viewer


def layers():
    return {
        "pois": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [121.0, 31.0]},
                    "properties": {"osm_id": "node/1", "tile_id": "r0_c0"},
                }
            ],
        }
    }


class DatabaseViewerExportTests(unittest.TestCase):
    def test_postgis_sql_creates_real_spatial_tables_and_inserts_geojson_geometry(self):
        sql = build_postgis_sql(layers())

        self.assertIn("CREATE EXTENSION IF NOT EXISTS postgis;", sql)
        self.assertIn("CREATE TABLE IF NOT EXISTS city_twin_pois", sql)
        self.assertIn("ST_GeomFromGeoJSON", sql)
        self.assertIn('"node/1"', sql)

    def test_static_viewer_references_generated_layers_and_quality_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            write_static_viewer(output, ["buildings", "roads", "pois"])

            html = (output / "index.html").read_text(encoding="utf-8")
            self.assertIn("Cesium", html)
            self.assertIn("../layers/buildings.geojson", html)
            self.assertIn("../reports/quality_report.json", html)
            self.assertIn("renderFallbackMap", html)
            self.assertNotIn('<script src="https://cdnjs.cloudflare.com/ajax/libs/cesium', html)


if __name__ == "__main__":
    unittest.main()
