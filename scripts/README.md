# scripts

## 说明

1. 这里保存项目的人工复核和辅助运行脚本。
2. 脚本应围绕真实导出产物做验证，不引入 mock 成功路径。

## 当前脚本

1. `review_motrix_mujoco.py`：加载 MotrixSim 导出的 MJCF `scene.xml`，可进行 headless MuJoCo 步进或启动交互式 viewer。
