import unittest

from city_twin_pipeline.config import BBox, HeightConfig, LayerSelector, PipelineConfig, ProjectConfig, SourceConfig
from city_twin_pipeline.osm import OverpassTransformer, build_overpass_query


def make_config() -> PipelineConfig:
    return PipelineConfig(
        project=ProjectConfig(name="Shanghai POC", area_name="Lujiazui", standard_crs="EPSG:4326"),
        bbox=BBox(south=31.2307, west=121.4893, north=31.2488, east=121.5103),
        sources={
            "osm": SourceConfig(
                endpoint="https://overpass-api.de/api/interpreter",
                license="ODbL-1.0",
                attribution="© OpenStreetMap contributors",
                timeout_seconds=180,
            )
        },
        layers={
            "buildings": [LayerSelector(type="way", tags={"building": "*"})],
            "roads": [LayerSelector(type="way", tags={"highway": "*"})],
            "water": [LayerSelector(type="way", tags={"natural": "water"})],
            "pois": [LayerSelector(type="node", tags={"amenity": "*"})],
        },
        height=HeightConfig(level_height_m=3.2),
        minimum_counts={"buildings": 1, "roads": 1},
    )


class OSMTransformTests(unittest.TestCase):
    def test_build_overpass_query_uses_configured_bbox_and_layer_selectors(self):
        query = build_overpass_query(make_config())

        self.assertIn("31.2307,121.4893,31.2488,121.5103", query)
        self.assertIn('way["building"]', query)
        self.assertIn('way["highway"]', query)
        self.assertIn('way["natural"="water"]', query)
        self.assertNotIn("google", query.lower())

    def test_transform_converts_real_overpass_shapes_into_separate_geojson_layers(self):
        raw = {
            "elements": [
                {"type": "node", "id": 1, "lat": 31.231, "lon": 121.49},
                {"type": "node", "id": 2, "lat": 31.231, "lon": 121.491},
                {"type": "node", "id": 3, "lat": 31.232, "lon": 121.491},
                {"type": "node", "id": 4, "lat": 31.232, "lon": 121.49},
                {"type": "node", "id": 10, "lat": 31.233, "lon": 121.492},
                {"type": "node", "id": 11, "lat": 31.234, "lon": 121.493},
                {"type": "node", "id": 20, "lat": 31.235, "lon": 121.494, "tags": {"amenity": "ferry_terminal", "name": "Dock"}},
                {"type": "node", "id": 30, "lat": 31.236, "lon": 121.495},
                {"type": "node", "id": 31, "lat": 31.236, "lon": 121.496},
                {"type": "node", "id": 32, "lat": 31.237, "lon": 121.496},
                {"type": "node", "id": 33, "lat": 31.237, "lon": 121.495},
                {"type": "way", "id": 100, "nodes": [1, 2, 3, 4, 1], "tags": {"building": "office", "building:levels": "12"}},
                {"type": "way", "id": 200, "nodes": [10, 11], "tags": {"highway": "primary", "name": "Century Avenue"}},
                {"type": "way", "id": 300, "nodes": [30, 31, 32, 33, 30], "tags": {"natural": "water", "name": "Pond"}},
            ]
        }

        layers = OverpassTransformer(make_config()).transform(raw, fetched_at="2026-06-08T00:00:00Z")

        self.assertEqual(layers["buildings"]["features"][0]["geometry"]["type"], "Polygon")
        self.assertEqual(layers["buildings"]["features"][0]["properties"]["height_m"], 38.4)
        self.assertEqual(layers["buildings"]["features"][0]["properties"]["height_source"], "building:levels")
        self.assertEqual(layers["roads"]["features"][0]["geometry"]["type"], "LineString")
        self.assertEqual(layers["water"]["features"][0]["geometry"]["type"], "Polygon")
        self.assertEqual(layers["pois"]["features"][0]["geometry"]["type"], "Point")
        self.assertEqual(layers["pois"]["features"][0]["properties"]["osm_id"], "node/20")

    def test_transform_keeps_closed_roads_as_linestrings(self):
        raw = {
            "elements": [
                {"type": "node", "id": 1, "lat": 31.231, "lon": 121.49},
                {"type": "node", "id": 2, "lat": 31.231, "lon": 121.491},
                {"type": "node", "id": 3, "lat": 31.232, "lon": 121.491},
                {"type": "way", "id": 400, "nodes": [1, 2, 3, 1], "tags": {"highway": "secondary"}},
            ]
        }

        layers = OverpassTransformer(make_config()).transform(raw, fetched_at="2026-06-08T00:00:00Z")

        self.assertEqual(layers["roads"]["features"][0]["geometry"]["type"], "LineString")


if __name__ == "__main__":
    unittest.main()
