from __future__ import annotations

import json
from typing import Any


def build_postgis_sql(layers: dict[str, dict[str, Any]]) -> str:
    lines = [
        "-- Generated from real project GeoJSON layers.",
        "CREATE EXTENSION IF NOT EXISTS postgis;",
        "",
    ]
    for layer_name in sorted(layers):
        table = f"city_twin_{_safe_identifier(layer_name)}"
        lines.extend(
            [
                f"DROP TABLE IF EXISTS {table};",
                f"CREATE TABLE IF NOT EXISTS {table} (",
                "  id bigserial PRIMARY KEY,",
                "  osm_id text,",
                "  tile_id text,",
                "  height_m double precision,",
                "  properties jsonb NOT NULL,",
                "  geom geometry(Geometry, 4326) NOT NULL",
                ");",
                f"CREATE INDEX IF NOT EXISTS {table}_geom_idx ON {table} USING gist (geom);",
            ]
        )
        for feature in layers[layer_name].get("features", []):
            props = feature.get("properties", {})
            geometry = feature.get("geometry", {})
            if not geometry:
                continue
            osm_id = _sql(str(props.get("osm_id", "")))
            tile_id = _sql(str(props.get("tile_id", "")))
            height_m = props.get("height_m")
            height_sql = str(float(height_m)) if isinstance(height_m, (int, float)) else "NULL"
            props_json = _sql(json.dumps(props, ensure_ascii=False, sort_keys=True))
            geom_json = _sql(json.dumps(geometry, ensure_ascii=False, sort_keys=True))
            lines.append(
                f"INSERT INTO {table} (osm_id, tile_id, height_m, properties, geom) VALUES "
                f"('{osm_id}', '{tile_id}', {height_sql}, '{props_json}'::jsonb, "
                f"ST_SetSRID(ST_GeomFromGeoJSON('{geom_json}'), 4326));"
            )
        lines.append("")
    return "\n".join(lines)


def _safe_identifier(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in value)
    return cleaned.strip("_") or "layer"


def _sql(value: str) -> str:
    return value.replace("'", "''")
