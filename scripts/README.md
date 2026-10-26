# scripts

## 说明

1. 这里保存项目的人工复核和辅助运行脚本。
2. 脚本应围绕真实导出产物做验证，不引入 mock 成功路径。

## 当前脚本

1. `review_motrix_mujoco.py`：加载本项目导出的 MJCF `scene.xml`，可进行 headless MuJoCo 步进或启动交互式 viewer；不代替 MotrixSim 验收。
2. `run_archived_example.py`：校验并离线运行仓库内的真实 OSM 存档样例。
3. `render_launch_scene.py`：用 Blender 渲染实际导出的 OBJ。
4. `build_launch_video.py`：将实际渲染帧与数据统计制作成横竖版视频，不负责平台发布。依赖见根目录 `requirements-media.txt`。
