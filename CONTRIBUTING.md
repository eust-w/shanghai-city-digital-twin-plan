# Contributing

This is an early preview. Contributions should improve reproducibility and
correctness before adding more export-format claims.

## Run Locally

Use Python 3.9 or newer from a clean checkout:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/run_archived_example.py --output artifacts/example
```

The example uses the real OSM archive in this repository without a network
request. See `DATA_LICENSE.md` before redistributing map-derived outputs.

## Useful Contributions

- Preserve meter units through tiled exports instead of shrinking large scenes.
- Test concave polygons, holes, multipolygons and ring orientation.
- Validate independently collidable buildings and traversable roads.
- Record exact engine versions and commands for real import/render evidence.
- Improve missing-height reporting without inventing ground truth.

Include focused regression tests, the command you ran, and a concise explanation
of behavior changes. Engine integration claims require engine-specific evidence;
schema validation or MuJoCo loading does not establish MotrixSim compatibility.
Do not commit credentials, internal deployment details, or unlicensed assets.

Submit contributions under the project's Apache-2.0 code license. Include a
separate source/license declaration when contributing data or third-party assets.
