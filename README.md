# Shanghai City Digital Twin Plan

本仓库用于沉淀“将上海级城市导入建模、游戏引擎或仿真系统”的需求、边界和实施方案。

核心原则：

- Google Maps / Google Earth 适合作为在线视觉参考或流式可视化底图，不作为可离线导出、可编辑、可再发布的城市资产来源。
- 可控、可仿真、可商业化的城市模型必须来自开放数据、采购授权数据或自采合规数据，并保留数据来源、许可证和更新时间。
- 城市重建应拆成视觉层、GIS 数据层、资产生成层、仿真语义层、引擎运行层，而不是把一张地图直接“导出成城市”。

## 文档

- [需求说明](docs/01-requirements.md)
- [实施方案](docs/02-implementation-plan.md)
- [POC 运行手册](docs/03-poc-runbook.md)
- [运行资产说明](docs/04-runtime-artifacts.md)

## 项目目标

构建一套真实可落地的上海城市重建方案，支持以下方向：

- 游戏引擎中的大范围城市场景。
- 城市数字孪生可视化。
- 交通、车辆、机器人或城市运营仿真。
- 分级精度建模：全市低精度覆盖 + 重点区域高精度还原。

## 当前状态

当前仓库包含：

- 需求和实施方案。
- 一个可执行的真实开放数据 POC 流水线。
- PostGIS SQL、glTF、3D Tiles preview、SUMO、OpenDRIVE 和 Web 查看器导出。
- Unreal Engine 可导入场景包：`.uproject`、OBJ 建筑体块、导入脚本和关卡生成脚本。
- MotrixSim 可导入场景包：`scene.xml`、`scene.urdf`、`scene.json`、视觉 OBJ、碰撞 OBJ 和 ZIP 包。
- 默认 POC 配置：`config/poc-shanghai-core.json`。

仓库不包含密钥、Google 离线地图数据、第三方商业素材或生成后的大体量数据。运行输出默认写入 `data/`，该目录不纳入版本控制。

## 快速运行

```bash
python3 -m unittest discover -s tests
python3 -m city_twin_pipeline run-poc \
  --config config/poc-shanghai-core.json \
  --output data/poc-shanghai-core \
  --fail-on-quality
```

该命令会从 Overpass API 拉取真实 OpenStreetMap 数据，并导出建筑、道路、水系、绿地、POI GeoJSON、质量报告、数据台账、PostGIS SQL、glTF、3D Tiles preview、SUMO、OpenDRIVE、本地 Web 查看器、Unreal Engine 可导入场景包和 MotrixSim 可导入场景包。不会使用 mock 数据，也不会把 Google Maps / Google Earth / Google 3D Tiles 作为离线资产来源。

当 Overpass 网络不稳定时，可以使用已真实拉取的原始数据继续导出：

```bash
python3 -m city_twin_pipeline run-poc \
  --config config/poc-shanghai-core.json \
  --raw-input data/poc-shanghai-core/raw/osm_overpass.json \
  --output data/poc-shanghai-core \
  --fail-on-quality
```

查看器：

```bash
cd data/poc-shanghai-core
python3 -m http.server 8765
```

打开 `http://localhost:8765/viewer/index.html`。

Unreal 导入包位于 `data/poc-shanghai-core/unreal/`，压缩包为 `data/poc-shanghai-core/ShanghaiCityTwinPOC_UnrealImportPackage.zip`。有 Unreal Editor 的机器可执行：

```bash
/path/to/UnrealEditor data/poc-shanghai-core/unreal/ShanghaiCityTwinPOC.uproject \
  -ExecutePythonScript=data/poc-shanghai-core/unreal/Scripts/import_city_twin_scene.py
```

MotrixSim 导入包位于 `data/poc-shanghai-core/motrix_scene/`，压缩包为 `data/poc-shanghai-core/motrix_scene.zip`。在 MotrixSim Web Viewer 中拖入该目录或解压后的目录，然后加载 `scene.xml`、`scene.urdf` 或 `scene.json`。
