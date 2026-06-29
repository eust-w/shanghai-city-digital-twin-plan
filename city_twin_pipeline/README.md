# city_twin_pipeline

## 说明

1. 这里保存上海城市数字孪生 POC 的 Python pipeline 代码。
2. 代码入口是 `cli.py` 和 `__main__.py`，用于拉取或读取真实 OpenStreetMap 数据并导出运行资产。
3. 运行输出默认写入项目根目录下的 `data/`，不在这里保存生成后的大体量数据。

## 主要模块

1. `config.py`：读取和校验 POC 配置。
2. `osm.py`、`geometry.py`、`tiling.py`：Overpass 数据获取、几何转换和分块。
3. `exporters.py`、`outputs.py`、`quality.py`：统一导出、数据台账和质量报告。
4. `gltf.py`、`tiles3d.py`、`viewer.py`：Web 和 3D Tiles 查看资产。
5. `postgis.py`、`sumo.py`、`opendrive.py`、`unreal_export.py`、`motrix_export.py`：仿真、GIS 和引擎运行资产导出。
