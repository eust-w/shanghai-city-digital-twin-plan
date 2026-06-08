from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .config import ConfigError, load_config
from .exporters import export_runtime_artifacts
from .osm import OverpassTransformer, fetch_overpass
from .outputs import write_data_ledger, write_json
from .quality import build_quality_report
from .tiling import assign_tile_ids


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the real-data Shanghai digital twin POC pipeline.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run-poc", help="Fetch real OSM data and export POC GeoJSON layers.")
    run_parser.add_argument("--config", required=True, type=Path, help="Path to pipeline JSON config.")
    run_parser.add_argument("--output", required=True, type=Path, help="Output directory for raw data, layers, and reports.")
    run_parser.add_argument(
        "--raw-input",
        type=Path,
        help="Use an existing real Overpass JSON file instead of performing a network fetch.",
    )
    run_parser.add_argument(
        "--fail-on-quality",
        action="store_true",
        help="Exit non-zero if quality thresholds fail.",
    )

    args = parser.parse_args(argv)
    if args.command == "run-poc":
        try:
            status = run_poc(args.config, args.output, raw_input=args.raw_input)
        except ConfigError as exc:
            parser.error(str(exc))
        return 2 if args.fail_on_quality and status != "pass" else 0
    return 1


def run_poc(config_path: Path, output_dir: Path, raw_input: Path | None = None) -> str:
    config = load_config(config_path)
    processing_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    if raw_input is not None:
        raw = json.loads(raw_input.read_text(encoding="utf-8"))
        fetched_at = raw.get("osm3s", {}).get("timestamp_osm_base", processing_at)
    else:
        raw = fetch_overpass(config)
        fetched_at = processing_at
    transformer = OverpassTransformer(config)
    layers = transformer.transform(raw, fetched_at=fetched_at)
    layers = assign_tile_ids(layers, config.bbox, rows=2, cols=2)
    report = build_quality_report(layers, config.bbox, config.minimum_counts)

    write_json(output_dir / "raw" / "osm_overpass.json", raw)
    for layer_name, layer in layers.items():
        write_json(output_dir / "layers" / f"{layer_name}.geojson", layer)
    write_json(output_dir / "reports" / "quality_report.json", report)
    write_data_ledger(
        output_dir / "reports" / "data_ledger.md",
        config,
        fetched_at=fetched_at,
        raw_count=len(raw.get("elements", [])),
        layer_counts=report["counts"],
        quality_status=report["status"],
    )
    export_manifest = export_runtime_artifacts(layers, config, output_dir)

    print(f"POC output: {output_dir}")
    print(f"Quality: {report['status']}")
    for layer_name, count in sorted(report["counts"].items()):
        print(f"{layer_name}: {count}")
    print("Artifacts:")
    for name, path in sorted(export_manifest["artifacts"].items()):
        print(f"{name}: {path}")
    if report["issues"]:
        print("Issues:")
        for issue in report["issues"]:
            print(f"- {issue}")
    return str(report["status"])
