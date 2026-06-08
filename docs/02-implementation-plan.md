# 实施方案

最后更新：2026-06-08

## 1. 结论

可靠方案不是“从 Google Maps 导出上海”，而是采用双轨架构：

- 在线视觉参考轨：Google Photorealistic 3D Tiles 或其他商业 3D 地图服务，用于快速获得真实城市外观和对照参考。
- 自有资产生产轨：用开放数据、采购授权数据和自采合规数据生成可编辑、可仿真、可离线部署的上海城市资产。

这两条轨道可以在引擎里叠加显示，但数据所有权和使用边界必须分开。

## 2. 总体架构

### 2.1 数据层

- GIS 数据仓库：PostGIS 或等价空间数据库。
- 原始数据区：保存开放数据、采购数据、自采数据的原始文件和许可证。
- 标准化数据区：统一坐标系统、字段、几何有效性、tile 编号。
- 质量检查区：保存抽样检查、拓扑检查、许可证检查和版本记录。

### 2.2 资产生成层

- 地形生成：DEM/DSM 转 terrain mesh 或 heightmap。
- 建筑生成：footprint + height/levels 转 LOD1/LOD2 体块。
- 道路生成：中心线/车道线转 spline mesh、OpenDRIVE 或 SUMO network。
- 水系绿地生成：polygon 转材质面和边界。
- 语义层生成：道路、建筑、水体、绿地、交通设施、POI 标签。
- 分块导出：按 geohash、quadkey、自定义网格或行政区导出 tile。

### 2.3 引擎运行层

- Unreal：World Partition、Cesium georeference、Nanite/HLOD、实例化建筑。
- Unity：Cesium for Unity、Addressables、GPU instancing、LODGroup。
- Web：CesiumJS、3D Tiles、轻量业务叠加。
- Omniverse：USD 资产组织、物理材质、传感器仿真。
- CARLA/SUMO：OpenDRIVE、路口、车道、信号灯、交通流。

## 3. 数据来源建议

### 3.1 建筑

优先级：

1. 商业授权建筑数据或城市三维模型。
2. Overture Maps Buildings。
3. OpenStreetMap building footprint。
4. 自采航测、LiDAR 或人工建模。

处理方式：

- 有高度时直接生成建筑体块。
- 有楼层数但无高度时按用途估算层高。
- 无高度时按区域统计、POI 类型、建筑面积和遥感高度模型估算。
- 地标建筑单独制作，不依赖自动拉伸。

### 3.2 道路

优先级：

1. 授权高精地图或车道级地图。
2. Overture transportation。
3. OpenStreetMap road network。
4. 人工修复复杂路口、高架、隧道和匝道。

处理方式：

- 游戏展示用 spline road mesh。
- 交通流仿真用 SUMO network。
- 自动驾驶仿真用 OpenDRIVE。
- 路口、车道方向、交通灯相位必须单独校验。

### 3.3 地形

可选来源：

- Copernicus DEM。
- NASA SRTM。
- 国内合规高程数据供应商。
- 项目自采 LiDAR 或航测。

处理方式：

- 全市底座使用中低分辨率 DEM。
- 核心区使用更高精度 DSM/点云。
- 桥梁、高架、隧道不要只依赖 DEM，需要道路层级数据单独表达。

### 3.4 影像和材质

可选来源：

- 授权卫星影像或航摄影像。
- 自采摄影测量。
- 程序化材质。
- 人工制作地标贴图。

禁止来源：

- 未授权缓存 Google 卫星图。
- 从 Google Street View 截图制作建筑立面。
- 从 Google 3D Tiles 烘焙贴图或导出模型。

### 3.5 POI

可选来源：

- OSM/Overture Places。
- 商业授权 POI。
- 项目自建业务 POI。
- Google Places 仅作为在线查询和实时展示，不作为批量离线 POI 库。

## 4. 推荐技术路线

### 4.1 POC 路线

目标：2 周内验证一块 2km x 2km 上海核心区能否完成真实数据拉取、标准化、质量检查和目标引擎加载。当前仓库已经实现第一步可执行流水线：通过 `config/poc-shanghai-core.json` 配置范围和图层，通过 `python3 -m city_twin_pipeline run-poc` 拉取真实 OpenStreetMap 数据并导出 GeoJSON、质量报告和数据台账。

步骤：

1. 选择 POC 范围，例如陆家嘴。
2. 获取建筑、道路、水系、地形开放数据。
3. 建立 PostGIS 数据仓库。
4. 统一坐标系统并修复几何错误。
5. 生成 LOD1 建筑体块。
6. 生成基础道路 mesh 和交通网络。
7. 导出 3D Tiles 或引擎原生资产。
8. 在 Unreal/Unity/CesiumJS 中加载。
9. 用 Google Photorealistic 3D Tiles 或商业底图做在线视觉对照。
10. 输出 POC 验收报告：精度、性能、合规、缺口。

验收标准：

- POC 区域可在目标引擎运行。
- 建筑、道路、水系、地形基本对齐。
- 至少 1000 栋建筑可自动生成。
- 路网可导入 SUMO 或等价系统进行基础交通流测试。
- 数据来源和许可记录完整。

当前可执行范围：

- 已实现：OSM/Overpass 真实数据获取、建筑/道路/水系/绿地/POI 图层导出、tile_id 分块、数据台账、基础质量检查、Google 离线资产来源拦截。
- 已实现：PostGIS SQL、LOD1 glTF、3D Tiles preview tileset、SUMO plain XML、OpenDRIVE baseline、本地 Web/Cesium 查看器、Unreal Engine 可导入项目包、Unreal Python 场景生成脚本和 MotrixSim 可导入场景包。
- 未硬编码：POC bbox、数据源 endpoint、图层选择、楼层高度换算和质量阈值都来自配置文件。
- 未 mock：运行时必须访问真实 Overpass API；缺失高度不会填假值。
- 待扩展：Overture GeoParquet、DEM、真实 PostGIS 实例执行验证、SUMO netconvert 执行验证、在安装 Unreal Editor 的机器上执行导入验证、Unity 工程模板、授权高精地图、地标人工资产和商业合规审查。

推荐命令：

```bash
python3 -m unittest discover -s tests
python3 -m city_twin_pipeline run-poc \
  --config config/poc-shanghai-core.json \
  --output data/poc-shanghai-core \
  --fail-on-quality
```

质量阈值应作为决策门禁，而不是造数据的理由。如果开放数据不足，应进入采购授权数据、自采数据或调整 POC 范围。

### 4.2 核心区路线

目标：1-2 个月完成 10-30 平方公里核心区。

步骤：

1. 扩大数据范围。
2. 补建筑高度和建筑类型。
3. 修复高架、桥梁、隧道、匝道和复杂路口。
4. 制作地标建筑资产。
5. 增加交通灯、公交站、地铁出入口、标志性 POI。
6. 建立 tile streaming 和 LOD 策略。
7. 接入基础仿真：交通流、车辆路径、行人热点。
8. 做性能预算和版本化发布。

验收标准：

- 核心区可连续浏览，无大面积空洞。
- 主要道路拓扑正确。
- 重点地标可识别。
- 交通仿真可运行 30 分钟以上无系统性卡死。
- 单个 tile 可独立更新。

### 4.3 全市底座路线

目标：2-4 个月完成全上海 LOD1 城市底座。

步骤：

1. 统一全市数据网格。
2. 批量生成建筑体块、道路、水系和地形。
3. 建立自动质量检查。
4. 建立版本发布流程。
5. 建立重点区域覆盖策略。
6. 输出 Unreal/Unity/Web/CARLA/SUMO 多目标格式。

验收标准：

- 全市主要建筑和道路有基本覆盖。
- 数据可按 tile 分块加载。
- 引擎中不会因坐标精度出现明显抖动。
- 资产生成流程可重复执行。
- 数据来源和许可证可追踪。

## 5. Google 相关使用方式

### 5.1 可以使用

- 在 CesiumJS、Unreal、Unity 或 Omniverse 中在线加载 Google Photorealistic 3D Tiles 作为视觉层。
- 用 Google Maps Platform 做在线地图展示、搜索、路线或地点查询。
- 在 POC 中把 Google 视觉结果作为人工对照，判断自有资产是否偏移或缺失。

### 5.2 不应使用

- 离线保存 Google 3D Tiles。
- 将 Google 3D 内容转换成 FBX、OBJ、glTF、USD 或其他可编辑模型。
- 从 Google 地图、卫星图、街景或 3D 数据中批量提取建筑、道路、POI 或贴图。
- 用 Google 数据生成自有城市资产库。

### 5.3 决策建议

- 如果目标是展示效果：Google 3D Tiles + Cesium 是最快路线。
- 如果目标是仿真、编辑、发布、商业化：必须建设自有资产生产轨。
- 如果目标是中国境内正式上线：优先评估国内合规地图和三维城市数据供应商。

## 6. 坐标和空间精度

### 6.1 坐标系统

项目至少需要记录并处理：

- WGS84：全球开放数据常用。
- GCJ-02：中国互联网地图常见偏移坐标。
- CGCS2000：国内测绘常用。
- 引擎局部坐标：Unreal/Unity/Omniverse 运行时坐标。

### 6.2 推荐做法

- 数据仓库保留原始坐标和标准化坐标。
- 引擎中使用局部原点或 georeference 系统。
- 大范围场景使用浮点原点漂移或分块局部坐标。
- 不同来源数据必须做抽样对齐检查。

## 7. 资产格式

### 7.1 中间格式

- GeoPackage：交换矢量 GIS 数据。
- GeoJSON：小范围调试和可视化。
- Shapefile：兼容老工具，但字段和编码限制多。
- PostGIS：主数据仓库。
- LAS/LAZ：点云。
- CityGML：三维城市模型交换。

### 7.2 运行格式

- 3D Tiles：大范围城市流式可视化。
- glTF/glb：建筑、地标和通用 3D 资产。
- USD：Omniverse/Isaac 和资产协作。
- FBX：DCC 和传统引擎工作流。
- OpenDRIVE：自动驾驶道路网络。
- SUMO network：交通流仿真。
- MotrixSim scene package：包含 `scene.xml`、`scene.urdf`、`scene.json`、视觉网格、碰撞网格和元数据，可作为机器人/物理仿真场景包。

## 8. 引擎落地方案

### 8.1 Unreal Engine

适合：高质量游戏画面、大范围交互、影视级展示、车辆仿真前端。

建议：

- 用 Cesium for Unreal 处理地理坐标和 3D Tiles。
- 自有建筑和道路按 tile 导入 World Partition。
- 建筑使用 HLOD/Nanite/实例化减少 draw call。
- 道路视觉 mesh、车辆可行驶面、碰撞体分离。
- 不把高密度摄影测量网格直接用作碰撞。

### 8.2 Unity

适合：跨平台交互、桌面和移动端、轻量数字孪生。

建议：

- 用 Cesium for Unity 或自研 georeference。
- 用 Addressables 管理城市 tile。
- 建筑和道路做 GPU instancing。
- 移动端使用更低 LOD 和更短可视距离。

### 8.3 CesiumJS

适合：Web 数字孪生、业务数据叠加、快速演示。

建议：

- 3D Tiles 作为主资产格式。
- 业务数据用矢量图层和 entity 叠加。
- 不承担复杂物理仿真。

### 8.4 CARLA / SUMO

适合：交通、车辆、传感器和自动驾驶验证。

建议：

- SUMO 负责交通流。
- CARLA 负责车辆动力学、传感器和 3D 场景。
- OpenDRIVE 需要人工检查复杂路口和高架。
- 不要只用 OSM 自动转换结果作为高可信仿真地图。

### 8.5 MotrixSim

适合：机器人、物理仿真和本地 Web Viewer 场景验证。

当前 POC 已生成 MotrixSim 包：

- `data/poc-shanghai-core/motrix_scene/scene.xml`：MJCF 入口。
- `data/poc-shanghai-core/motrix_scene/scene.urdf`：URDF 入口。
- `data/poc-shanghai-core/motrix_scene/scene.json`：场景索引。
- `data/poc-shanghai-core/motrix_scene/meshes/scene_visual.obj`：真实高度建筑视觉网格。
- `data/poc-shanghai-core/motrix_scene/meshes/scene_collision.obj`：简化碰撞网格。
- `data/poc-shanghai-core/motrix_scene.zip`：可拖入 MotrixSim Web Viewer 的压缩包。

当前包使用 OSM 中真实 `height` 或 `building:levels` 派生高度生成建筑体块。缺少真实高度的建筑不会被填假高度。为了符合 MotrixSim/Real2Motrix 的 1000m 场景范围校验，2km 级 POC 会记录并应用 `source_to_motrix_scale`，比例写入 `metadata/asset_manifest.json`。

## 9. 团队和角色

最小团队：

- GIS 工程师：数据清洗、坐标、PostGIS、拓扑。
- 技术美术/工具工程师：资产生成、LOD、材质、导出。
- 引擎工程师：Unreal/Unity/Web 加载、性能、交互。
- 仿真工程师：SUMO/CARLA/OpenDRIVE、交通灯、车辆行为。
- 合规/采购负责人：数据许可、供应商、地图审图、合同边界。

## 10. 里程碑

### M0：启动准备

周期：3-5 天。

交付：

- POC 范围确定。
- 数据源候选清单。
- 许可证初审。
- 目标引擎确定。
- 验收指标确定。

### M1：2km x 2km POC

周期：2 周。

交付：

- GIS 数据仓库。
- 建筑体块、道路、水系、地形。
- 引擎可运行场景。
- POC 验收报告。
- 数据缺口和成本评估。

### M2：核心区

周期：1-2 个月。

交付：

- 10-30 平方公里核心区域。
- 地标建筑。
- 修复后的主干路网。
- 基础交通仿真。
- tile streaming 和 LOD 策略。

### M3：全市底座

周期：2-4 个月。

交付：

- 全上海 LOD1 城市底座。
- 自动生成流水线。
- 数据台账。
- 多引擎导出格式。
- 重点区域升级计划。

### M4：高精仿真区

周期：6-12 个月。

交付：

- 指定走廊或园区高精建模。
- 车道级道路和交通灯。
- 语义标签和传感器仿真。
- 与真实数据的对比校验。

## 11. 成本判断

### 低成本验证

- 使用 OSM、Overture、公开 DEM 和程序化材质。
- 适合验证引擎和流水线。
- 视觉可信但精度有限。

### 中等成本产品原型

- 采购建筑高度、POI、影像或部分三维数据。
- 人工制作地标和复杂道路。
- 适合展示、园区、核心区数字孪生。

### 高成本仿真系统

- 采购或自采高精地图、LiDAR、航测、车道级数据。
- 人工校验路口、交通灯、语义标签。
- 适合自动驾驶、机器人和高可信城市运营仿真。

## 12. 风险控制

### 12.1 许可风险

控制措施：

- 建立数据台账。
- 每个数据源先做许可证审查。
- Google 数据只作为在线服务使用。
- 商业发布前做法律和地图合规复核。

### 12.2 精度风险

控制措施：

- POC 阶段就做抽样测量。
- 高架、隧道、桥梁人工复核。
- 不同来源数据分层保存，避免覆盖原始数据。

### 12.3 性能风险

控制措施：

- 从第一天按 tile 设计。
- 每个 tile 有三角面数、材质数、纹理大小预算。
- 远景使用简化体块，近景按需加载。

### 12.4 工期风险

控制措施：

- 全市只做低精度底座。
- 高精度只做重点区域。
- 先完成自动流水线，再扩大范围。

## 13. 推荐下一步

1. 确定第一个 POC 区域。
2. 确定目标引擎：Unreal、Unity、Web/CesiumJS、CARLA 或 SUMO。
3. 列出可接受的数据许可证和商业化目标。
4. 拉取 OSM/Overture/DEM 的 POC 样本数据。
5. 做一次 2km x 2km 的坐标、建筑、道路、引擎加载验证。

## 14. 参考资料

- Google Maps Platform Terms: https://cloud.google.com/maps-platform/terms
- Google Map Tiles API 3D Tiles overview: https://developers.google.com/maps/documentation/tile/3d-tiles-overview
- Google Maps Platform EEA changes: https://developers.google.com/maps/comms/eea/map-tiles
- Google Places API policies: https://developers.google.com/maps/documentation/places/web-service/policies
- Cesium for Unreal with Google Photorealistic 3D Tiles: https://cesium.com/learn/unreal/unreal-photorealistic-3d-tiles/
- Overture Maps Buildings guide: https://docs.overturemaps.org/guides/buildings/
- Overture Maps data access: https://docs.overturemaps.org/getting-data/
- Copernicus DEM: https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM
- SUMO OpenStreetMap import: https://sumo.dlr.de/docs/Networks/Import/OpenStreetMap.html
- CARLA OpenDRIVE standalone mode: https://carla.readthedocs.io/en/latest/adv_opendrive/
