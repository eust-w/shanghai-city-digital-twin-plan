"""Verify and run the bundled real OSM archive without downloading data."""

import argparse
import gzip
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("artifacts/example"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    source = root / "examples/shanghai-core"
    manifest = json.loads((source / "SOURCE.json").read_text(encoding="utf-8"))
    raw = gzip.decompress((source / "osm_overpass.json.gz").read_bytes())
    if hashlib.sha256(raw).hexdigest() != manifest["uncompressed_sha256"]:
        parser.error("Archived OSM input failed its SHA256 integrity check")
    output = args.output.resolve()
    with tempfile.TemporaryDirectory(prefix="city-twin-example-") as directory:
        input_path = Path(directory) / "osm_overpass.json"
        input_path.write_bytes(raw)
        subprocess.run([
            sys.executable, "-m", "city_twin_pipeline", "run-poc",
            "--config", str(root / "config/poc-shanghai-core.json"),
            "--raw-input", str(input_path), "--output", str(output),
            "--fail-on-quality",
        ], cwd=root, check=True)


if __name__ == "__main__":
    main()
