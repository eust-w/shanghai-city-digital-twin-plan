# Map Data and Attribution

The Apache-2.0 license in `LICENSE` covers the project's own code and documentation,
not OpenStreetMap data or third-party software.

## OpenStreetMap

Copyright OpenStreetMap contributors. OpenStreetMap data is available under the
Open Data Commons Open Database License (ODbL) 1.0:

- https://www.openstreetmap.org/copyright
- https://opendatacommons.org/licenses/odbl/1-0/

`examples/shanghai-core/osm_overpass.json.gz` is a losslessly compressed, real
Overpass response captured on 2026-06-08. It is not synthetic test data. Its
metadata and SHA256 are in the adjacent `SOURCE.json`. The original OSM IDs,
tags and source timestamp are retained. This data is licensed separately under
ODbL, not Apache-2.0. No permission from a commercial imagery provider is implied.

Derived databases must comply with the applicable ODbL provisions, including
attribution, license notices and share-alike obligations. When publishing a
produced work such as a model render, retain appropriate attribution and make
the underlying derivative database available as required by ODbL. This repository
supplies the archived source and reproducible transformation code.

Display `Copyright OpenStreetMap contributors` and link to the copyright page.
The launch videos use the equivalent copyright-symbol attribution throughout.

## Optional Software

The core pipeline uses the Python standard library. Optional render/review tools
invoke separately installed Blender, FFmpeg, Pillow, MuJoCo and platform speech
services. Their software and assets are not relicensed by this repository.
Unreal Engine and MotrixSim are separate products and are not bundled here.
