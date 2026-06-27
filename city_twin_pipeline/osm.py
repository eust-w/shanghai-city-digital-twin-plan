from __future__ import annotations

import json
import re
import time
from http.client import RemoteDisconnected
from typing import Any
from urllib.error import URLError
from urllib import parse, request

from .config import LayerSelector, PipelineConfig


def build_overpass_query(config: PipelineConfig) -> str:
    bbox = config.bbox.as_overpass_bbox()
    statements: list[str] = []
    seen: set[str] = set()
    for selectors in config.layers.values():
        for selector in selectors:
            statement = f"{selector.type}{_tag_filter(selector)}({bbox});"
            if statement not in seen:
                statements.append(statement)
                seen.add(statement)
    body = "\n  ".join(statements)
    timeout = config.sources["osm"].timeout_seconds
    return f"""[out:json][timeout:{timeout}];
(
  {body}
);
out body;
>;
out skel qt;
"""


def fetch_overpass(config: PipelineConfig) -> dict[str, Any]:
    source = config.sources["osm"]
    query = build_overpass_query(config)
    return post_overpass_query(
        endpoint=source.endpoint,
        query=query,
        timeout_seconds=source.timeout_seconds,
        opener=request.urlopen,
        retries=2,
        retry_delay_seconds=0.75,
    )


def post_overpass_query(
    endpoint: str,
    query: str,
    timeout_seconds: int,
    opener=request.urlopen,
    retries: int = 2,
    retry_delay_seconds: float = 0.0,
) -> dict[str, Any]:
    body = parse.urlencode({"data": query}).encode("utf-8")
    req = request.Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            "User-Agent": "shanghai-city-digital-twin-plan/0.1",
        },
        method="POST",
    )
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with opener(req, timeout=timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except (URLError, RemoteDisconnected, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt >= retries:
                break
            if retry_delay_seconds > 0:
                time.sleep(retry_delay_seconds)
    if last_error is not None:
        raise last_error
    raise RuntimeError("Overpass request failed without an error")


class OverpassTransformer:
    def __init__(self, config: PipelineConfig):
        self.config = config

    def transform(self, raw: dict[str, Any], fetched_at: str) -> dict[str, dict[str, Any]]:
        node_index = _node_index(raw)
        layers = {
            layer_name: {
                "type": "FeatureCollection",
                "metadata": self._metadata(fetched_at),
                "features": [],
            }
            for layer_name in self.config.layers
        }

        for element in raw.get("elements", []):
            tags = element.get("tags")
            if not isinstance(tags, dict):
                continue
            for layer_name, selectors in self.config.layers.items():
                if not any(_matches_selector(element, selector) for selector in selectors):
                    continue
                feature = self._feature_for_element(layer_name, element, node_index, fetched_at)
                if feature is not None:
                    layers[layer_name]["features"].append(feature)

        return layers

    def _feature_for_element(
        self,
        layer_name: str,
        element: dict[str, Any],
        node_index: dict[int, tuple[float, float]],
        fetched_at: str,
    ) -> dict[str, Any] | None:
        element_type = element.get("type")
        tags = element.get("tags", {})
        geometry: dict[str, Any] | None = None

        if element_type == "node":
            lon = element.get("lon")
            lat = element.get("lat")
            if isinstance(lon, (int, float)) and isinstance(lat, (int, float)):
                geometry = {"type": "Point", "coordinates": [float(lon), float(lat)]}
        elif element_type == "way":
            coords = _way_coordinates(element, node_index)
            if not coords:
                return None
            if layer_name in {"buildings", "water", "green"}:
                if len(coords) < 4:
                    return None
                if coords[0] != coords[-1]:
                    coords.append(coords[0])
                geometry = {"type": "Polygon", "coordinates": [coords]}
            else:
                if len(coords) < 2:
                    return None
                geometry = {"type": "LineString", "coordinates": coords}

        if geometry is None:
            return None

        return {
            "type": "Feature",
            "geometry": geometry,
            "properties": self._properties(layer_name, element, tags, fetched_at),
        }

    def _properties(
        self,
        layer_name: str,
        element: dict[str, Any],
        tags: dict[str, str],
        fetched_at: str,
    ) -> dict[str, Any]:
        properties: dict[str, Any] = {
            "osm_id": f"{element.get('type')}/{element.get('id')}",
            "osm_type": element.get("type"),
            "data_source": "osm_overpass",
            "license": self.config.sources["osm"].license,
            "attribution": self.config.sources["osm"].attribution,
            "fetched_at": fetched_at,
            "tags": tags,
        }
        for key in ("name", "highway", "amenity", "natural", "waterway", "landuse", "bridge", "tunnel", "layer", "oneway", "maxspeed"):
            if key in tags:
                properties[key] = tags[key]
        if layer_name == "buildings":
            height_m, height_source = _height_from_tags(tags, self.config.height.level_height_m)
            properties["height_m"] = height_m
            properties["height_source"] = height_source
            if "building" in tags:
                properties["building"] = tags["building"]
        return properties

    def _metadata(self, fetched_at: str) -> dict[str, Any]:
        source = self.config.sources["osm"]
        return {
            "project": self.config.project.name,
            "area_name": self.config.project.area_name,
            "standard_crs": self.config.project.standard_crs,
            "source": "OpenStreetMap via Overpass API",
            "license": source.license,
            "attribution": source.attribution,
            "fetched_at": fetched_at,
            "bbox": self.config.bbox.as_overpass_bbox(),
        }


def _tag_filter(selector: LayerSelector) -> str:
    parts = []
    for key, value in selector.tags.items():
        if value == "*":
            parts.append(f'["{key}"]')
        else:
            parts.append(f'["{key}"="{value}"]')
    return "".join(parts)


def _matches_selector(element: dict[str, Any], selector: LayerSelector) -> bool:
    if element.get("type") != selector.type:
        return False
    tags = element.get("tags", {})
    if not isinstance(tags, dict):
        return False
    for key, expected in selector.tags.items():
        if key not in tags:
            return False
        if expected != "*" and tags[key] != expected:
            return False
    return True


def _node_index(raw: dict[str, Any]) -> dict[int, tuple[float, float]]:
    nodes: dict[int, tuple[float, float]] = {}
    for element in raw.get("elements", []):
        if element.get("type") != "node":
            continue
        node_id = element.get("id")
        lat = element.get("lat")
        lon = element.get("lon")
        if isinstance(node_id, int) and isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
            nodes[node_id] = (float(lon), float(lat))
    return nodes


def _way_coordinates(element: dict[str, Any], node_index: dict[int, tuple[float, float]]) -> list[list[float]]:
    coords: list[list[float]] = []
    for node_id in element.get("nodes", []):
        coord = node_index.get(node_id)
        if coord is None:
            return []
        coords.append([coord[0], coord[1]])
    return coords


def _height_from_tags(tags: dict[str, str], level_height_m: float) -> tuple[float | None, str | None]:
    height = _parse_height(tags.get("height"))
    if height is not None:
        return height, "height"
    levels = _parse_number(tags.get("building:levels"))
    if levels is not None:
        return round(levels * level_height_m, 2), "building:levels"
    return None, None


def _parse_height(value: str | None) -> float | None:
    if not value:
        return None
    normalized = value.strip().lower()
    match = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*(m|meter|meters)?$", normalized)
    if match:
        return round(float(match.group(1)), 2)
    feet_match = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*(ft|feet|')$", normalized)
    if feet_match:
        return round(float(feet_match.group(1)) * 0.3048, 2)
    return None


def _parse_number(value: str | None) -> float | None:
    if not value:
        return None
    match = re.match(r"^([0-9]+(?:\.[0-9]+)?)$", value.strip())
    if not match:
        return None
    return float(match.group(1))
