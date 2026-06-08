import unittest

from city_twin_pipeline.config import BBox
from city_twin_pipeline.opendrive import build_opendrive_xml
from city_twin_pipeline.sumo import build_sumo_plain_xml


def road_layer():
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": [[121.0, 31.0], [121.001, 31.0]]},
                "properties": {"osm_id": "way/10", "highway": "primary", "oneway": "yes", "maxspeed": "50"},
            },
            {
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": [[121.0, 31.001], [121.001, 31.001]]},
                "properties": {"osm_id": "way/11", "highway": "residential"},
            },
        ],
    }


class SimulationExportTests(unittest.TestCase):
    def test_sumo_plain_xml_exports_nodes_and_directed_edges_from_real_roads(self):
        files = build_sumo_plain_xml(road_layer(), BBox(south=31.0, west=121.0, north=31.01, east=121.01))

        self.assertIn("<nodes>", files["nodes"])
        self.assertIn('id="way_10"', files["edges"])
        self.assertNotIn('id="way_10_rev"', files["edges"])
        self.assertIn('id="way_11_rev"', files["edges"])
        self.assertIn('speed="13.89"', files["edges"])

    def test_opendrive_exports_roads_with_plan_view_geometry(self):
        xml = build_opendrive_xml(road_layer(), BBox(south=31.0, west=121.0, north=31.01, east=121.01))

        self.assertIn("<OpenDRIVE>", xml)
        self.assertIn('name="way/10"', xml)
        self.assertIn("<planView>", xml)
        self.assertIn("<laneSection", xml)


if __name__ == "__main__":
    unittest.main()
