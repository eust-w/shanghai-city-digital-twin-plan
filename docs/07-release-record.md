# v0.1.0-alpha.1 发布与验证记录

日期：2026-10-26。定位：可复现的真实开放数据早期预览，不是已经完成原生引擎和物理验收的成品。

## 发布入口

- [公开源码](https://github.com/eust-w/shanghai-city-digital-twin-plan)，自有代码 Apache-2.0，地图数据独立遵循 ODbL。
- [预发布版及下载](https://github.com/eust-w/shanghai-city-digital-twin-plan/releases/tag/v0.1.0-alpha.1)，对应代码 `074593092d4838809901e32551dac872a8125ddc`。后续文档提交可能领先此标签。
- [Bilibili 主片](https://www.bilibili.com/video/BV1CinZ6xEJN/)、[知乎介绍](https://www.zhihu.com/pin/2098141574253241817)、[抖音短片](https://www.douyin.com/video/7700918059808181504)和 [X 发布帖](https://x.com/eustancewu/status/2114660223210430712)已打开正式作品页核实。其他平台不因存在账号或草稿而计为发布成功。

## 附件

Release 包含 7 个手工上传附件；GitHub 另自动提供源码 ZIP 和 tar.gz。

| 文件 | 内容 |
| --- | --- |
| `shanghai-core-example-v0.1.0-alpha.1.zip` | 从真实存档重新生成的 51 项样例资产及许可说明 |
| `shanghai-city-twin-landscape.mp4` | 1280 x 720，约 82.77 秒 |
| `shanghai-city-twin-vertical.mp4` | 720 x 1280，约 43.81 秒 |
| `shanghai-city-twin-landscape.srt` | 横版中文字幕 |
| `shanghai-city-twin-vertical.srt` | 竖版中文字幕 |
| `production-report.json` | 制作参数、来源及验证边界 |
| `SHA256SUMS.txt` | 其余六个附件的 SHA256 |

所有上传附件的 GitHub 返回摘要均与本地 SHA256 一致。压缩包通过 CRC 和路径检查；视频通过完整解码检查。视频是实际导出 OBJ 的 Blender 渲染，包含系统合成旁白，没有背景音乐，不是 Unreal/MotrixSim 录屏。展示底板不代表 DEM。

下载附件后可在同目录使用 `shasum -a 256 -c SHA256SUMS.txt` 核对完整性。

## 验证

- 本地 23 项单元测试通过；真实存档重新导出通过质量门禁。
- [GitHub Actions 40303294200](https://github.com/eust-w/shanghai-city-digital-twin-plan/actions/runs/40303294200) 在 Python 3.9、3.12、3.14 上全部通过测试与真实存档导出。
- 自有核心流水线仅依赖 Python 标准库。可选视频依赖固定为 Pillow 13.0.0；在隔离的 Python 3.12 环境进行依赖审计，发布时未发现已知漏洞。
- 公开前对 Git 历史及待发布目录进行密钥扫描，并检查私有基础设施路径；扫描无发现不等于绝对不存在风险。
- GitHub 仓库及 Release 经匿名访问核实；不是仅确认登录后的页面可见。

## 尚未完成

样例数据来自 2026-06-08，不能当作当前实时地图。2,227 个轮廓仅导出 573 栋：13 栋采用地图高度标签，560 栋根据楼层数估算，1,654 栋缺少高度而跳过。

Motrix 候选包缩放为原尺寸的 `0.40424188`，原尺寸分块、复杂多边形处理、独立碰撞体验证，以及明确版本的 Unreal/MotrixSim 原生导入验收仍待完成。历史 MuJoCo 加载记录不能替代上述验收。详细工程路线见[开源发布评估](05-open-source-release.md)。
