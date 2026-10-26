# Shanghai City Twin

A reproducible pipeline from OpenStreetMap to traceable city-scene assets.
Shanghai is the first example, not a claim of full-city coverage.

[中文](README.md) | [Apache-2.0](LICENSE) | [Data license](DATA_LICENSE.md) | [Contributing](CONTRIBUTING.md)

![Blender render of the actual exported OBJ](docs/images/shanghai-preview.jpg)

Actual exported geometry rendered in Blender, not an engine integration demo.
Map data: Copyright OpenStreetMap contributors, ODbL. The display plane is not
surveyed terrain. Most heights in this example are estimated from floor counts.

## Downloads and Demo

- [v0.1.0-alpha.1 pre-release](https://github.com/eust-w/shanghai-city-digital-twin-plan/releases/tag/v0.1.0-alpha.1): real example assets, introduction videos, subtitles, production metadata and SHA256 checksums.
- [44-second video](https://www.douyin.com/video/7700918059808181504) | [X launch post](https://x.com/eustancewu/status/2114660223210430712). The 83-second landscape video is available in the release. Both use Chinese synthesized narration and Chinese subtitles.
- [Release verification record](docs/07-release-record.md): 23 unit tests and real archived exports in CI on Python 3.9, 3.12 and 3.14.

## Run the Real Archived Example

Python 3.9 or newer; no API key or third-party Python dependency for the core:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/run_archived_example.py --output artifacts/example
```

This verifies and replays the bundled 2026-06-08 Overpass response offline.
To fetch a current sample instead:

```bash
python3 -m city_twin_pipeline run-poc \
  --config config/poc-shanghai-core.json \
  --output data/poc-shanghai-core --fail-on-quality
```

## What It Produces

- Raw source archive, GeoJSON layers, quality reports and provenance ledger.
- PostGIS loading SQL, LOD1 glTF, preview 3D Tiles and a local viewer.
- SUMO/OpenDRIVE baseline geometry, not lane-level ground truth.
- Unreal project/import script and OBJ; MJCF/URDF/OBJ candidate scene packages.

## Honest Boundaries

This is an early preview, not a physics-validated digital twin. The archived
sample contains 2,227 building footprints and 1,414 road records. It exports
573 building blocks: 13 use OSM height tags and 560 estimate heights from floor
counts. Another 1,654 footprints are skipped because both fields are missing.
OSM height tags are not measurements verified by this project.

The Motrix candidate package is currently scaled by 0.40424188; full-scale
tiling is unfinished. The merged collision mesh and polygon triangulation need
further validation. Package validation and historical MuJoCo loading do not
establish native MotrixSim or Unreal compatibility.

The next milestones are full-scale tiles, robust polygon geometry, collision
tests and versioned native-engine acceptance. See the [release assessment](docs/05-open-source-release.md).

Code is Apache-2.0. OpenStreetMap data remains under ODbL; see
[data attribution and redistribution requirements](DATA_LICENSE.md).
