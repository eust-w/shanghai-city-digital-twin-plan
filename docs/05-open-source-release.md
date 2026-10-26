# 开源发布评估与验收计划

审查日期：2026-10-26。审查基线：`1b77f15`。本文是发布方案，不表示已开源、已发布或已完成引擎验收。

审查后的首发改进：权利人已确认 Apache-2.0，已加入 LICENSE 与独立数据许可说明；README 已纠正高度和引擎验收表述，加入中英版本、真实模型图、真实存档样例和 SHA256 校验的离线入口；新增贡献指南与三版本 Python CI。下表保留审查基线的问题，实际发布与 CI 结果以 Release 和 Actions 回执为准。

## 定位

建议定位为 **从开放地图到可追溯 3D 场景的开发者流水线**。上海是第一个样例，而不是项目能力的地理上限。目标用户是需要快速搭建城市基础场景的独立开发者、GIS 工具开发者和仿真研究者。

当前适合以 early preview / POC 发布。成为有影响力的开源项目，需要证明别人能够复现、能用于具体工作，并愿意持续贡献；无法从已有功能数量推断 Stars 或传播量。

竞争参照：[Blosm](https://github.com/vvoovv/blosm) 已有 OSM 建筑、地形等导入能力。因此，不将“拉伸地图建筑”本身描述成独有技术。建议围绕来源记录、缺失数据处理、统一坐标与多格式导入验收形成差异；其中统一坐标和跨引擎验收仍需补强。

## 本次核验

- GitHub 仓库仍为 private，尚未更改可见性。
- 本地提交基线包含两个 Git 提交；Gitleaks 扫描未发现规则命中的密钥。另检查了已知内部地址、私钥标记和本地部署路径，未发现命中。这不是完整知识产权审核。
- 本次运行 `python3 -m unittest discover -s tests`：23 个测试通过。未计算覆盖率，不声称达到 80%。
- 用真实存档 Overpass JSON 重新导出：quality 为 pass。不是本次重新抓取地图。
- 输入数据时间为 `2026-06-08T04:18:00Z`，包含 2,227 个建筑轮廓、1,414 条道路、13 个水系面、73 个绿地图形和 818 个 POI。
- 导出 573 栋建筑体块；13 栋带 OSM `height` 标签，560 栋按 `building:levels * 3.2m` 估算；1,654 栋缺少高度而跳过。OSM 高度标签也不等于经过项目实测。
- 当前 Motrix 包缩放比例为 `0.40424188`。不能称为可直接用于真实尺度机器人验证的地图。
- 可运行的 Python 入口为 `python3 -m city_twin_pipeline run-poc`；浏览器预览和格式输出已经存在。
- 历史对话有 MuJoCo 加载和离屏图像证据；本轮不将历史证据当成新一轮 MuJoCo、MotrixSim 或 Unreal 原生验收。

## 发布前需要处理的事实

| 项目 | 当前问题 | 验收方式 |
| --- | --- | --- |
| 代码许可 | 根目录无 LICENSE | 权利人选定许可，保留必要第三方声明 |
| 高度说明 | 旧文档将估算高度笼统称为真实高度 | README、元数据、视频统一区分 height 标签、楼层估算和缺失 |
| 尺度 | 大场景为通过本项目/Real2Motrix 范围检查而缩小 | 默认保留米单位，采用局部坐标分块；不可把本地校验器的 1km 阈值说成 MotrixSim 官方限制 |
| 碰撞体 | 多栋建筑合并为一个碰撞 mesh | 在目标引擎验证多建筑间道路可通行；MuJoCo 凸包行为需重点检查 |
| 几何 | 顶底使用 fan triangulation；只取 Polygon 外环 | 凹多边形、孔洞、多部件和环方向都有几何回归样例 |
| 引擎声明 | 文件可解析不等于目标引擎完整兼容 | 记录每个引擎的版本、导入命令、运行截图和失败情况 |
| 首次体验 | 存档样例在 gitignore 中，没有稳定公开样例包 | 提供附许可证、来源时间、SHA256 的小样例与 Release 附件 |
| CI | 仓库尚无自动化工作流 | 在干净环境运行测试和离线样例导出 |
| 预览交互 | 曾出现黑屏和相机缩放被重置 | 实际验证打开、旋转、平移、缩放，并保留图片/操作录像 |

首发时可以明确列出限制；若要宣传“仿真可用”，尺寸、碰撞和对应引擎验收必须先通过。当前片子只展示真实输出的资产渲染。

## 许可证与数据

权利人于本轮明确确认拥有开源授权，并选择 Apache-2.0 作为项目自有代码的许可。完整文本见根目录 LICENSE。第三方代码、数据及软件不因本项目许可而被重新授权。

公开仓库并不自动等于开源；GitHub 官方说明要求提供许可，明确使用、修改、分发权限：[Licensing a repository](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)。

代码许可与地图数据许可分别记录。OSM 数据采用 ODbL，需要署名并标明数据许可；修改数据库、发布派生数据库与发布图像的义务需要按实际分发形式判断，不能用代码的 Apache-2.0 统一覆盖。视频保留 `© OpenStreetMap contributors` 和版权链接。

参考：[Apache-2.0 正文](https://www.apache.org/licenses/LICENSE-2.0)、[OSM Copyright](https://www.openstreetmap.org/copyright)、[OSMF Attribution Guidelines](https://osmfoundation.org/wiki/Licence/Attribution_Guidelines)。

## 建议发布顺序

1. 完成上述许可与首发能力声明，准备中英 README、实际效果图、快速启动、限制表和贡献指南。
2. 修复影响真实尺度、碰撞与导入稳定性的核心问题；先验收一个主要运行目标，再扩展兼容矩阵。
3. 制作带来源记录的小型 Release 样例，并从干净 checkout 复现。初期优先做好一个城市小范围。
4. 发布 early preview，附真实演示、错误反馈入口和明确路线图。仅在仓库公开后发布可访问的源码链接。
5. 按平台发布介绍；收集首次导出成功率、问题复现率、实际复用者和贡献反馈，不使用虚构用户数或保证 Stars 的文案。

建议第一个阶段的成功标准：3 位非作者在干净环境复现样例，并能理解尺度、缺失高度与目标引擎边界。该数字是建议目标，不是已发生的事实。

## 本轮产物

`artifacts/launch/` 包含本次存档数据重跑输出、真实 OBJ 渲染帧、横竖版 MP4、字幕和生产记录。该目录按现有 gitignore 保持本地，不自动上传或创建公共 Release。

可复现的素材生成命令：

```bash
python3 -m city_twin_pipeline run-poc \
  --config config/poc-shanghai-core.json \
  --raw-input data/poc-shanghai-core/raw/osm_overpass.json \
  --output artifacts/launch/rebuild --fail-on-quality
blender --background --python scripts/render_launch_scene.py -- \
  --package artifacts/launch/rebuild/motrix_scene \
  --output artifacts/launch/frames
uv run --no-project --python 3.12 --with-requirements requirements-media.txt \
  python scripts/build_launch_video.py \
  --data artifacts/launch/rebuild --frames artifacts/launch/frames \
  --output artifacts/launch/video
```

视频工具另需 Blender、ffmpeg/ffprobe、Pillow 与 macOS Tingting 语音。媒体工具使用独立 Python 3.12 环境和 `requirements-media.txt`；不应使用系统旧版 Pillow。它们用于制作媒体，不是核心流水线的运行依赖。制作脚本不负责发布。
