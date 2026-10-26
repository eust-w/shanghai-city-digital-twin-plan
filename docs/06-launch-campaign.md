# 介绍视频与多平台发布草案

状态：待 review 的开源预备版，未宣称项目已经公开。日期：2026-10-26。

## 主题与证据

主标题：**从开放地图，到 3D 城市场景**。

核心句：一条可以检查数据来源、保留缺口、生成多种资产格式的城市建模流水线。

视频使用实际导出的 OBJ，由 Blender 生成相机环绕画面。不是 MuJoCo、MotrixSim 或 Unreal 录屏，也不是生成式 AI 伪造的城市画面。平面为展示底板，不表示已接入 DEM。旁白为系统合成语音；没有背景音乐。

样例仅为上海核心区域；573 栋为带高度信息或按楼层估算的建筑体块；目前不能代表上海全市、高精地图或已经完成真实尺度物理验收。

## 分镜

| 顺序 | 画面 | 主要内容 |
| --- | --- | --- |
| 1 | 实际 OBJ 环绕，全景 | 开放地图到 3D 场景，说明开源预备状态 |
| 2 | 同一资产的不同视角 | 输入记录：2,227 建筑轮廓、1,414 道路记录 |
| 3 | 模型的真实空缺 | 导出 573，缺少高度跳过 1,654 |
| 4 | 建筑体块与来源说明 | 13 个 height 标签，560 个楼层估算 |
| 5 | 资产画面与格式标签 | glTF、OBJ、MJCF、URDF、Unreal 导入包；运行验收待逐项完成 |
| 6 | 全景收尾 | 原尺寸分块、碰撞验证、一键示例是后续工作 |

横版包含全部分镜，竖版选择 1、3、6。实际时长由合成旁白测量后决定，详见 `artifacts/launch/video/production-report.json`。视频包含中文烧录字幕，另附 SRT。各平台稿件按账号能力与实际上传界面复核后使用。

## 平台文案

### Bilibili

标题：从开放地图生成上海建筑体块：一个城市 3D 工具的开源准备

正文：从 OSM 数据获取、GeoJSON 图层到 3D 资产导出，我们做了一条可以重跑的城市建模流水线。视频展示真实导出的 OBJ，不是引擎运行录像。样本有 2,227 个建筑轮廓，本次生成 573 栋体块，其中 13 栋带高度标签、560 栋按楼层估算。缺少高度的数据保留并报告。下一步补齐原尺寸分块、碰撞验收和干净环境的一键示例。

适用素材：横版主片。源码链接待正式公开后添加。

### 小红书

标题：把地图变成 3D，难点不只是建模

正文：这个上海样例里有 2,227 个建筑轮廓，但当前只生成 573 栋体块。为什么？还有 1,654 栋缺少高度。做开源工具，需要把这些缺口告诉使用者。我们正在整理一条从 OSM 到三维网格和场景描述的流水线。视频是真实资产渲染，仍是早期 POC。

适用素材：竖版短片；封面用真实模型截图。话题建议：开源项目、三维建模、GIS。

### 抖音 / 视频号

标题：地图能变成三维场景吗？先看一个真实样例

正文：从开放地图到上海建筑体块，573 栋模型由现有数据生成，缺少高度的建筑明确跳过。开源预备版，后续继续补齐尺度、碰撞和复现体验。

适用素材：竖版短片。视频内持续显示 OSM 来源和合成旁白标识；发布时按平台要求填写相关标签。

### YouTube

标题：Open map data to a 3D city scene | Shanghai City Twin early preview

正文：An early, reproducible pipeline from OpenStreetMap data to GeoJSON, 3D assets and scene descriptions. This video renders the actual exported OBJ in Blender; it is not a simulator recording. The Shanghai sample exports 573 building blocks: 13 have OSM height tags and 560 use estimates from floor counts. 1,654 footprints are skipped for missing heights. Full-scale tiling, collision validation and engine acceptance remain on the roadmap. Chinese synthesized narration and subtitles. Source-code release is being prepared.

适用素材：横版；竖版可单独准备 Shorts 版本。英文字幕尚未制作，不声称已本地化。

### X

Preparing an open-source pipeline from OpenStreetMap to 3D city assets. Our Shanghai POC exports 573 building blocks and reports 1,654 missing heights. Actual OBJ render below. Full-scale tiling and collision validation are next.

适用素材：竖版短片或模型截图；不将 Stars、用户数或全引擎兼容作为现有成绩。

### LinkedIn

We are preparing an early release of a pipeline that converts OpenStreetMap data into city-scene assets. The most useful part of this prototype is making the evidence and gaps visible: the Shanghai sample has 2,227 building footprints, while 573 can currently be extruded from height tags or floor-count estimates. The attached video renders the exported OBJ. The next engineering milestones are full-scale tiling, collision checks and reproducible engine imports.

适用素材：横版片或短片，随正文说明工程阶段。

### 知乎

标题：从 OpenStreetMap 到三维城市场景，哪些环节仍需要验证？

正文：这个上海核心区样例展示了一条可重复运行的数据处理流程：原始 OSM、GeoJSON、质量报告和多格式资产导出。2,227 个建筑轮廓中，573 个有可用高度信息，其中 560 个是楼层估算值。视频展示实际 OBJ 的 Blender 渲染，并非仿真器运行画面。要进一步用于物理仿真，原尺寸分块、复杂多边形处理、碰撞体和原生引擎验收仍需逐项完成。项目正在准备开源，欢迎围绕数据和验证方法交流。

适用素材：横版主片，结合数据口径和工程限制说明。

### 快手

标题：开放地图生成 573 栋上海建筑体块

正文：这段画面来自实际导出的 3D 模型。缺少高度的 1,654 个建筑轮廓没有强行补值，生成结果和数据缺口一起保留。城市建模工具开源预备版，合成旁白，非仿真器录屏。

适用素材：竖版短片，保留 OSM 署名与合成旁白标识。

### 微信公众号

标题：从开放地图到三维场景：一个城市建模流水线的开源准备

正文：我们正在整理一个从 OpenStreetMap 数据到三维资产的早期工具。它获取并保留原始数据、生成 GeoJSON 和质量报告，再输出 glTF、OBJ、MJCF、URDF 与 Unreal 导入候选包。上海样例包含 2,227 个建筑轮廓，当前可生成 573 栋体块：13 栋带地图高度标签、560 栋按楼层数估算，剩余 1,654 栋缺少高度而跳过。本文视频是真实输出 OBJ 的渲染，不是高精度城市复刻，也不是目标引擎已验收的证明。下一步先补齐许可、复现样例与尺度和碰撞验证，再公开代码与验收记录。

适用素材：横版主片与模型截图；账号视频权限、正文排版和原创声明需在实际发布界面核对。

## 发布执行

用户要求覆盖全部账号。应先枚举实际连接的自媒体账号，按平台和账号逐一保存发布结果；仅有平台配置、账号名称或 dry-run 回执不表示拥有有效发布授权。

- 接口账号：验证当前权限、上传及发布结果，保留文章/视频 ID 和可访问 URL。
- 手动投递账号：准备对应 MP4、标题、正文、封面、字幕及署名，记录待投递状态。
- 尚未连接或已失效账号：标为待登录，不猜测账号、不记录成功。
- 正式“已开源”文案需等到许可确定、仓库公开、源码链接经未登录访问验证后替换。

本轮不承诺跨平台自动发布能力；以真实账号核对与平台回执为准。
