from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import PipelineConfig
from .osm import build_overpass_query


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def write_data_ledger(
    path: Path,
    config: PipelineConfig,
    fetched_at: str,
    raw_count: int,
    layer_counts: dict[str, int],
    quality_status: str,
) -> None:
    source = config.sources["osm"]
    lines = [
        "# POC 数据台账",
        "",
        f"- 项目：{config.project.name}",
        f"- 区域：{config.project.area_name}",
        f"- 标准坐标：{config.project.standard_crs}",
        f"- 范围 bbox：`{config.bbox.as_overpass_bbox()}`",
        f"- 获取时间：{fetched_at}",
        f"- 数据源：OpenStreetMap via Overpass API",
        f"- API Endpoint：{source.endpoint}",
        f"- 许可证：{source.license}",
        f"- Attribution：{source.attribution}",
        "- Google 数据：未作为离线资产来源使用",
        f"- Overpass 原始元素数：{raw_count}",
        f"- 质量状态：{quality_status}",
        "",
        "## 图层统计",
        "",
    ]
    for layer_name, count in sorted(layer_counts.items()):
        lines.append(f"- {layer_name}: {count}")
    lines.extend(
        [
            "",
            "## Overpass Query",
            "",
            "```overpass",
            build_overpass_query(config).strip(),
            "```",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
