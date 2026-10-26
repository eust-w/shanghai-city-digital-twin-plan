# POC 运行手册

最后更新：2026-10-26

本手册把第一阶段 POC 从“方案”落到可执行流程。默认 POC 使用真实 OpenStreetMap 数据，通过 Overpass API 拉取，不使用 Google 离线瓦片、影像、街景、3D Tiles 或手工 mock 数据。

## 1. 默认范围

- 区域：人民广场-南京东路-外滩 2km 级核心区
- 配置文件：`config/poc-shanghai-core.json`
- 坐标：EPSG:4326
- bbox：`31.224,121.47,31.244,121.4925`
- 目标验证：建筑、道路、水系、绿地、POI 的真实开放数据拉取、转换、台账和质量检查。

## 2. 运行命令

```bash
python3 -m city_twin_pipeline run-poc \
  --config config/poc-shanghai-core.json \
  --output data/poc-shanghai-core \
  --fail-on-quality
```

当 Overpass 网络不稳定时，可以使用已真实拉取的原始数据继续导出：

```bash
python3 -m city_twin_pipeline run-poc \
  --config config/poc-shanghai-core.json \
  --raw-input data/poc-shanghai-core/raw/osm_overpass.json \
  --output data/poc-shanghai-core \
  --fail-on-quality
```

## 3. 输出物

- `data/poc-shanghai-core/raw/osm_overpass.json`：Overpass API 原始返回。
- `data/poc-shanghai-core/layers/buildings.geojson`：建筑 footprint、OSM 高度标签和楼层估算字段。
- `data/poc-shanghai-core/layers/roads.geojson`：道路中心线和 OSM 道路属性。
- `data/poc-shanghai-core/layers/water.geojson`：水系多边形。
- `data/poc-shanghai-core/layers/green.geojson`：公园、草地、树林等绿地。
- `data/poc-shanghai-core/layers/pois.geojson`：POI 点。
- `data/poc-shanghai-core/reports/quality_report.json`：数量、几何、bbox、建筑高度覆盖检查。
- `data/poc-shanghai-core/reports/data_ledger.md`：数据来源、许可证、获取时间、图层统计和 Overpass 查询。
- `data/poc-shanghai-core/reports/export_manifest.json`：运行资产清单。
- `data/poc-shanghai-core/db/postgis_load.sql`：PostGIS 装载脚本。
- `data/poc-shanghai-core/gltf/buildings.gltf`：有高度标签或楼层估算值的 LOD1 glTF。
- `data/poc-shanghai-core/3dtiles/buildings/tileset.json`：3D Tiles preview。
- `data/poc-shanghai-core/sim/sumo/*.xml`：SUMO plain node/edge 输入。
- `data/poc-shanghai-core/sim/opendrive/shanghai_poc.xodr`：OpenDRIVE baseline。
- `data/poc-shanghai-core/viewer/index.html`：本地 Web/Cesium 查看器，带 SVG fallback。
- `data/poc-shanghai-core/unreal/ShanghaiCityTwinPOC.uproject`：Unreal Engine 可导入项目。
- `data/poc-shanghai-core/unreal/Scripts/import_city_twin_scene.py`：Unreal Python 导入和关卡生成脚本。
- `data/poc-shanghai-core/motrix_scene/scene.xml`：MotrixSim MJCF 场景入口。
- `data/poc-shanghai-core/motrix_scene/scene.urdf`：MotrixSim URDF 场景入口。
- `data/poc-shanghai-core/motrix_scene/scene.json`：MotrixSim 场景索引。
- `data/poc-shanghai-core/motrix_scene/meshes/*.obj`：视觉和碰撞 OBJ 网格。
- `data/poc-shanghai-core/motrix_scene.zip`：面向 MotrixSim 的候选压缩包，尚待原生引擎验收。

## 4. 不做的事

- 不保存、导出或转换 Google 3D Tiles。
- 不缓存 Google 地图瓦片、卫星图或街景。
- 不从 Google 内容描摹建筑、道路、POI 或贴图。
- 不为缺失建筑高度填假值；仅在 OSM 提供 `height` 或 `building:levels` 时生成 `height_m`。楼层数乘配置层高是估算，不是实测。
- 不把视觉 GeoJSON 直接当作交通仿真真值；后续 SUMO/OpenDRIVE 仍需独立拓扑检查。
- 不把 OSM 中心线导出的 SUMO/OpenDRIVE baseline 误称为车道级高精地图。

## 5. 验收口径

默认阈值在配置文件中定义：

- 建筑：不少于 1000 个 footprint。
- 道路：不少于 200 条 way。
- 水系：不少于 1 个面。
- POI：不少于 50 个点。

如果真实开放数据达不到阈值，不应通过 mock 或硬编码补齐，而应在质量报告中记录缺口，并进入数据采购、人工测绘或范围调整决策。

2026-10-26 使用 2026-06-08 的真实存档输入重跑结果（不是本次联网抓取）：

- Quality：`pass`
- Buildings：`2227`
- Roads：`1414`
- Water：`13`
- Green：`73`
- POI：`818`
- glTF 导出建筑：`573`
- Unreal OBJ 导出建筑：`573`
- MotrixSim 视觉网格 faces：`13732`
- MotrixSim 碰撞网格 faces：`6876`
- MotrixSim bbox：`898.37m x 929.56m x 89.74m`
- MotrixSim 缩放比例：`0.40424188`
- 本项目 Motrix 包结构与网格校验：`pass`，不代表 MotrixSim 原生验收。
- 因缺少高度或楼层数跳过建筑：`1654`

573 栋体块中，13 栋有 OSM 高度标签、560 栋由楼层数估算。缩放与碰撞等限制见[开源发布评估](05-open-source-release.md)。

## 6. 官方参考

- OpenStreetMap Copyright and License: https://www.openstreetmap.org/copyright
- Overpass API / Overpass QL: https://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_QL
- Overture Maps data access: https://docs.overturemaps.org/getting-data/
- Google Map Tiles API Policies: https://developers.google.com/maps/documentation/tile/policies
