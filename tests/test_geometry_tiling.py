import unittest

from city_twin_pipeline.config import BBox
from city_twin_pipeline.geometry import bbox_center, lonlat_to_local_m
from city_twin_pipeline.tiling import assign_tile_ids


class GeometryTilingTests(unittest.TestCase):
    def test_lonlat_to_local_m_uses_bbox_center_as_stable_origin(self):
        bbox = BBox(south=31.0, west=121.0, north=31.02, east=121.02)
        origin = bbox_center(bbox)

        x, y = lonlat_to_local_m(121.02, 31.02, origin)

        self.assertGreater(x, 900)
        self.assertLess(x, 1000)
        self.assertGreater(y, 1100)
        self.assertLess(y, 1125)

    def test_assign_tile_ids_from_feature_centroids_without_changing_geometry(self):
        bbox = BBox(south=31.0, west=121.0, north=31.02, east=121.02)
        layers = {
            "pois": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [121.015, 31.015]},
                        "properties": {},
                    }
                ],
            }
        }

        result = assign_tile_ids(layers, bbox, rows=2, cols=2)

        feature = result["pois"]["features"][0]
        self.assertEqual(feature["properties"]["tile_id"], "r1_c1")
        self.assertEqual(feature["geometry"]["coordinates"], [121.015, 31.015])


if __name__ == "__main__":
    unittest.main()
