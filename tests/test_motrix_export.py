import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from city_twin_pipeline.config import BBox
from city_twin_pipeline.motrix_export import build_motrix_package, validate_motrix_package


def building_layer():
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [121.0, 31.0],
                            [121.001, 31.0],
                            [121.001, 31.001],
                            [121.0, 31.001],
                            [121.0, 31.0],
                        ]
                    ],
                },
                "properties": {"osm_id": "way/1", "height_m": 12.5},
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [121.002, 31.0],
                            [121.003, 31.0],
                            [121.003, 31.001],
                            [121.002, 31.001],
                            [121.002, 31.0],
                        ]
                    ],
                },
                "properties": {"osm_id": "way/2", "height_m": None},
            },
        ],
    }


class MotrixExportTests(unittest.TestCase):
    def test_build_motrix_package_writes_valid_scene_package_and_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = build_motrix_package(
                {"buildings": building_layer()},
                BBox(south=31.0, west=121.0, north=31.005, east=121.005),
                root,
            )
            package_dir = root / "motrix_scene"

            self.assertTrue((package_dir / "scene.xml").exists())
            self.assertTrue((package_dir / "scene.urdf").exists())
            self.assertTrue((package_dir / "scene.json").exists())
            self.assertTrue((package_dir / "review.html").exists())
            self.assertTrue((package_dir / "meshes" / "scene_visual.obj").exists())
            self.assertTrue((package_dir / "meshes" / "scene_collision.obj").exists())
            self.assertTrue((root / "motrix_scene.zip").exists())
            self.assertTrue(result["validation"]["valid"])

            scene_xml = (package_dir / "scene.xml").read_text(encoding="utf-8")
            self.assertIn('<camera name="overview"', scene_xml)
            self.assertIn('<light name="city_key_light"', scene_xml)
            self.assertIn("<statistic", scene_xml)

            manifest = json.loads((package_dir / "metadata" / "asset_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["scene"]["visual_mesh"], "meshes/scene_visual.obj")
            self.assertEqual(manifest["generated_from"], "shanghai_city_digital_twin_plan")
            self.assertEqual(manifest["source_to_motrix_scale"], 1.0)
            self.assertIn("local_bbox", manifest["scene"])

            with zipfile.ZipFile(root / "motrix_scene.zip") as archive:
                names = set(archive.namelist())
            self.assertIn("motrix_scene/scene.xml", names)
            self.assertIn("motrix_scene/review.html", names)
            self.assertIn("motrix_scene/meshes/scene_visual.obj", names)

    def test_validate_motrix_package_flags_collision_more_complex_than_visual(self):
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / "motrix_scene"
            (package / "meshes").mkdir(parents=True)
            (package / "metadata").mkdir()
            (package / "scene.xml").write_text(
                '<mujoco model="x"><compiler meshdir="meshes"/><asset><mesh name="scene_visual" file="scene_visual.obj"/><mesh name="scene_collision" file="scene_collision.obj"/></asset></mujoco>',
                encoding="utf-8",
            )
            (package / "scene.urdf").write_text(
                '<robot name="x"><link name="static_scene"><visual><geometry><mesh filename="meshes/scene_visual.obj"/></geometry></visual><collision><geometry><mesh filename="meshes/scene_collision.obj"/></geometry></collision></link></robot>',
                encoding="utf-8",
            )
            (package / "scene.json").write_text(
                json.dumps(
                    {
                        "entry": "scene.xml",
                        "metadata": "metadata/asset_manifest.json",
                        "assets": {
                            "visual_mesh": "meshes/scene_visual.obj",
                            "collision_mesh": "meshes/scene_collision.obj",
                        },
                    }
                ),
                encoding="utf-8",
            )
            (package / "metadata" / "asset_manifest.json").write_text(
                json.dumps(
                    {
                        "scene": {
                            "visual_mesh": "meshes/scene_visual.obj",
                            "collision_mesh": "meshes/scene_collision.obj",
                        },
                        "objects": [],
                    }
                ),
                encoding="utf-8",
            )
            (package / "meshes" / "scene_visual.obj").write_text(
                "v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n",
                encoding="utf-8",
            )
            (package / "meshes" / "scene_collision.obj").write_text(
                "v 0 0 0\nv 1 0 0\nv 0 1 0\nv 1 1 0\nf 1 2 3\nf 2 4 3\n",
                encoding="utf-8",
            )

            report = validate_motrix_package(package)

            self.assertFalse(report["valid"])
            self.assertIn("collision mesh must not have more faces than visual mesh", [issue["message"] for issue in report["issues"]])


if __name__ == "__main__":
    unittest.main()
