# 运行资产说明

最后更新：2026-06-08

端到端 POC 会从真实 OpenStreetMap / Overpass 数据生成以下资产。所有输出默认位于 `data/poc-shanghai-core/`，不纳入 git 版本控制。

## 1. 数据和台账

- `raw/osm_overpass.json`：Overpass API 原始 JSON。
- `layers/*.geojson`：标准化图层，包含 `tile_id`、来源、许可证、抓取时间和 OSM 标签。
- `reports/data_ledger.md`：数据台账和实际 Overpass 查询。
- `reports/quality_report.json`：数量、几何、bbox、建筑高度覆盖率和边界跨越检查。
- `reports/export_manifest.json`：运行资产清单。

## 2. 数据库

- `db/postgis_load.sql`：真实 GeoJSON 派生的 PostGIS 装载脚本。

示例：

```bash
createdb shanghai_city_twin_poc
psql shanghai_city_twin_poc -c 'CREATE EXTENSION IF NOT EXISTS postgis;'
psql shanghai_city_twin_poc -f data/poc-shanghai-core/db/postgis_load.sql
```

脚本会创建 `city_twin_buildings`、`city_twin_roads`、`city_twin_water`、`city_twin_green`、`city_twin_pois` 等表，并保留 `properties jsonb` 与 `geom geometry(Geometry, 4326)`。

## 3. 三维和 3D Tiles

- `gltf/buildings.gltf` / `gltf/buildings.bin`：LOD1 建筑体块 glTF。
- `gltf/manifest.json`：导出统计、坐标原点、最高高度、跳过原因。
- `3dtiles/buildings/tileset.json`：3D Tiles 1.1 preview tileset，指向 glTF 内容。

建筑 extrusion 只使用 OSM `height` 或 `building:levels` 派生出的真实字段。缺失高度的建筑不会被填假高度；它们仍保留在 GeoJSON 和 PostGIS 中。

## 4. 仿真输入

- `sim/sumo/shanghai_poc.nod.xml`：SUMO plain nodes。
- `sim/sumo/shanghai_poc.edg.xml`：SUMO plain edges。
- `sim/opendrive/shanghai_poc.xodr`：OpenDRIVE baseline 几何。
- `motrix_scene/`：MotrixSim scene package。
- `motrix_scene.zip`：MotrixSim 可导入压缩包。

示例：

```bash
netconvert \
  --node-files data/poc-shanghai-core/sim/sumo/shanghai_poc.nod.xml \
  --edge-files data/poc-shanghai-core/sim/sumo/shanghai_poc.edg.xml \
  --output-file data/poc-shanghai-core/sim/sumo/shanghai_poc.net.xml
```

当前导出是 OSM 中心线级 baseline，不代表车道级高精地图；复杂路口、高架、交通灯相位仍需要授权高精数据或人工复核。

### MotrixSim

- `motrix_scene/scene.xml`：MJCF 入口，引用 `meshes/scene_visual.obj` 和 `meshes/scene_collision.obj`。
- `motrix_scene/scene.urdf`：URDF 入口，引用同一视觉/碰撞网格。
- `motrix_scene/scene.json`：场景索引。
- `motrix_scene/metadata/asset_manifest.json`：来源、缩放比例、mesh 统计和 bbox。
- `motrix_scene/metadata/validation_report.json`：包结构和网格校验结果。
- `motrix_scene.zip`：打包后的可导入 ZIP。

导入方式：

```text
在 MotrixSim Web Viewer 中拖入 data/poc-shanghai-core/motrix_scene/
或解压 data/poc-shanghai-core/motrix_scene.zip 后加载 scene.xml、scene.urdf 或 scene.json。
```

当前包为了满足 1000m 场景范围校验，将真实 POC 范围按 `source_to_motrix_scale=0.40424188` 缩放到 MotrixSim 局部坐标。该比例记录在 `metadata/asset_manifest.json`，没有用假高度或补齐建筑。

## 5. Web 查看器

- `viewer/index.html`：本地静态查看器。

启动：

```bash
cd data/poc-shanghai-core
python3 -m http.server 8765
```

访问：

```text
http://localhost:8765/viewer/index.html
```

查看器先加载本地 GeoJSON 并渲染 SVG fallback；如果 Cesium CDN 可用，会自动切换到 Cesium 视图。

## 6. Unreal Engine 导入包

- `unreal/ShanghaiCityTwinPOC.uproject`：最小 Unreal 项目文件。
- `unreal/Content/CityTwin/Source/shanghai_city_twin_buildings.obj`：厘米单位建筑 OBJ。
- `unreal/Content/CityTwin/Source/shanghai_city_twin_buildings.mtl`：OBJ 材质。
- `unreal/Content/CityTwin/Source/*.geojson`：随包保留的真实图层数据。
- `unreal/Scripts/import_city_twin_scene.py`：Unreal Python 导入脚本。
- `unreal/README_UNREAL.md`：导入说明。
- `unreal/scene_manifest.json`：Unreal 包统计。
- `ShanghaiCityTwinPOC_UnrealImportPackage.zip`：可复制到有 Unreal Editor 机器上的导入包。

导入命令：

```bash
/path/to/UnrealEditor data/poc-shanghai-core/unreal/ShanghaiCityTwinPOC.uproject \
  -ExecutePythonScript=data/poc-shanghai-core/unreal/Scripts/import_city_twin_scene.py
```

脚本会在 Unreal 内执行：

- 导入 `shanghai_city_twin_buildings.obj` 为 Static Mesh。
- 创建 `/Game/CityTwin/Maps/ShanghaiCityTwinPOC` 关卡。
- 将建筑 Static Mesh 放入关卡。
- 添加基础方向光和概览相机。
- 保存 `/Game/CityTwin` 目录。

本机当前没有检测到 Unreal Editor，因此验证止于可导入包生成、JSON/OBJ/脚本结构校验。执行 UE 内导入需要在安装 Unreal Editor 的机器上运行上面的命令。

## 7. 当前真实验证结果

最近一次端到端运行：

- Quality：`pass`
- Buildings：`2227`
- Roads：`1414`
- Water：`13`
- Green：`73`
- POI：`818`
- glTF 导出建筑：`573`
- Unreal OBJ 导出建筑：`573`
- MotrixSim 导出建筑：`573`
- MotrixSim visual faces：`13732`
- MotrixSim collision faces：`6876`
- MotrixSim bbox：`898.37m x 929.56m x 89.74m`
- MotrixSim validation：`pass`
- 因缺少真实高度跳过建筑：`1654`
- PostGIS SQL：`3.2M`
- OpenDRIVE：`1.3M`
