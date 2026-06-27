from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class ConfigError(ValueError):
    """Raised when the pipeline configuration is incomplete or unsafe."""


@dataclass(frozen=True)
class ProjectConfig:
    name: str
    area_name: str
    standard_crs: str


@dataclass(frozen=True)
class BBox:
    south: float
    west: float
    north: float
    east: float

    def validate(self) -> None:
        if not -90 <= self.south <= 90 or not -90 <= self.north <= 90:
            raise ConfigError("bbox latitude must be within -90..90")
        if not -180 <= self.west <= 180 or not -180 <= self.east <= 180:
            raise ConfigError("bbox longitude must be within -180..180")
        if self.south >= self.north:
            raise ConfigError("bbox south must be less than north")
        if self.west >= self.east:
            raise ConfigError("bbox west must be less than east")

    def as_overpass_bbox(self) -> str:
        return f"{self.south},{self.west},{self.north},{self.east}"

    def contains(self, lon: float, lat: float) -> bool:
        return self.west <= lon <= self.east and self.south <= lat <= self.north


@dataclass(frozen=True)
class SourceConfig:
    endpoint: str
    license: str
    attribution: str
    timeout_seconds: int = 180


@dataclass(frozen=True)
class LayerSelector:
    type: str
    tags: dict[str, str]


@dataclass(frozen=True)
class HeightConfig:
    level_height_m: float


@dataclass(frozen=True)
class PipelineConfig:
    project: ProjectConfig
    bbox: BBox
    sources: dict[str, SourceConfig]
    layers: dict[str, list[LayerSelector]]
    height: HeightConfig
    minimum_counts: dict[str, int]


def load_config(path: str | Path) -> PipelineConfig:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return parse_config(payload)


def parse_config(payload: dict[str, Any]) -> PipelineConfig:
    project_payload = _require_mapping(payload, "project")
    bbox_payload = _require_mapping(payload, "poc_area")
    sources_payload = _require_mapping(payload, "sources")
    layers_payload = _require_mapping(payload, "layers")
    height_payload = _require_mapping(payload, "height")
    quality_payload = _require_mapping(payload, "quality")

    project = ProjectConfig(
        name=_require_string(project_payload, "name"),
        area_name=_require_string(project_payload, "area_name"),
        standard_crs=_require_string(project_payload, "standard_crs"),
    )
    bbox = BBox(
        south=_require_number(bbox_payload, "south"),
        west=_require_number(bbox_payload, "west"),
        north=_require_number(bbox_payload, "north"),
        east=_require_number(bbox_payload, "east"),
    )
    bbox.validate()

    sources = {
        name: _parse_source(name, source_payload)
        for name, source_payload in sources_payload.items()
    }
    if "osm" not in sources:
        raise ConfigError("sources.osm is required for the current executable POC")

    layers = {
        layer_name: [_parse_selector(item) for item in selectors]
        for layer_name, selectors in layers_payload.items()
    }
    if not layers:
        raise ConfigError("layers must contain at least one configured layer")

    level_height_m = _require_number(height_payload, "level_height_m")
    if level_height_m <= 0:
        raise ConfigError("height.level_height_m must be positive")

    minimum_counts_payload = _require_mapping(quality_payload, "minimum_counts")
    minimum_counts = {
        layer_name: _require_int(minimum_counts_payload, layer_name)
        for layer_name in minimum_counts_payload
    }

    return PipelineConfig(
        project=project,
        bbox=bbox,
        sources=sources,
        layers=layers,
        height=HeightConfig(level_height_m=level_height_m),
        minimum_counts=minimum_counts,
    )


def _parse_source(name: str, payload: Any) -> SourceConfig:
    if not isinstance(payload, dict):
        raise ConfigError(f"sources.{name} must be an object")
    endpoint = _require_string(payload, "endpoint")
    _reject_google_asset_endpoint(endpoint)
    timeout = int(payload.get("timeout_seconds", 180))
    if timeout <= 0:
        raise ConfigError(f"sources.{name}.timeout_seconds must be positive")
    return SourceConfig(
        endpoint=endpoint,
        license=_require_string(payload, "license"),
        attribution=_require_string(payload, "attribution"),
        timeout_seconds=timeout,
    )


def _parse_selector(payload: Any) -> LayerSelector:
    if not isinstance(payload, dict):
        raise ConfigError("layer selector must be an object")
    selector_type = _require_string(payload, "type")
    if selector_type not in {"node", "way", "relation"}:
        raise ConfigError("layer selector type must be node, way, or relation")
    tags = _require_mapping(payload, "tags")
    parsed_tags = {str(key): str(value) for key, value in tags.items()}
    if not parsed_tags:
        raise ConfigError("layer selector tags cannot be empty")
    return LayerSelector(type=selector_type, tags=parsed_tags)


def _reject_google_asset_endpoint(endpoint: str) -> None:
    host = urlparse(endpoint).hostname or ""
    google_hosts = ("googleapis.com", "google.com", "gstatic.com")
    if any(host == item or host.endswith(f".{item}") for item in google_hosts):
        raise ConfigError(
            "Google endpoints are only allowed as an online visual reference, not as an asset data source"
        )


def _require_mapping(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ConfigError(f"{key} must be an object")
    return value


def _require_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{key} must be a non-empty string")
    return value.strip()


def _require_number(payload: dict[str, Any], key: str) -> float:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"{key} must be a number")
    return float(value)


def _require_int(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"{key} must be an integer")
    if value < 0:
        raise ConfigError(f"{key} must be non-negative")
    return value
