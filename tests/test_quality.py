import unittest

from city_twin_pipeline.config import BBox
from city_twin_pipeline.quality import build_quality_report


class QualityReportTests(unittest.TestCase):
    def test_quality_report_counts_layers_and_flags_missing_required_counts(self):
        bbox = BBox(south=31.0, west=121.0, north=32.0, east=122.0)
        layers = {
            "buildings": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Polygon", "coordinates": [[[121.1, 31.1], [121.2, 31.1], [121.2, 31.2], [121.1, 31.1]]]},
                        "properties": {"height_m": None},
                    }
                ],
            },
            "roads": {"type": "FeatureCollection", "features": []},
        }

        report = build_quality_report(layers, bbox, {"buildings": 1, "roads": 1})

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["counts"]["buildings"], 1)
        self.assertEqual(report["counts"]["roads"], 0)
        self.assertEqual(report["buildings"]["missing_height_count"], 1)
        self.assertIn("roads has 0 features, below required minimum 1", report["issues"])

    def test_quality_report_warns_for_boundary_crossing_features_without_failing(self):
        bbox = BBox(south=31.0, west=121.0, north=32.0, east=122.0)
        layers = {
            "roads": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "LineString", "coordinates": [[121.5, 31.5], [122.2, 31.6]]},
                        "properties": {},
                    }
                ],
            }
        }

        report = build_quality_report(layers, bbox, {"roads": 1})

        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["boundary_crossing"]["roads"], 1)
        self.assertIn("roads has 1 boundary-crossing features requiring clip/tile handling", report["warnings"])


if __name__ == "__main__":
    unittest.main()
