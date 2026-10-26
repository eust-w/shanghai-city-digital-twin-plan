"""Build review-only video drafts from actual export footage and source statistics.

Requires ffmpeg, ffprobe, Pillow and macOS say (Tingting). Does not publish.
The source geometry must already have been rendered by render_launch_scene.py.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def run(argv):
    subprocess.run([str(arg) for arg in argv], check=True)


def duration(path):
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ], text=True).strip())


def wrap(draw, text, font, width):
    lines, line = [], ""
    for char in text:
        if char == "\n" or draw.textlength(line + char, font=font) > width:
            lines.append(line)
            line = "" if char == "\n" else char
        else:
            line += char
    if line:
        lines.append(line)
    return lines


def title_overlay(path, size, scene, footer, font_path):
    width, height = size
    vertical = height > width
    image = Image.new("RGBA", size)
    draw = ImageDraw.Draw(image)
    font = lambda pt: ImageFont.truetype(str(font_path), pt)
    top_end = 300 if vertical else 145
    bottom_start = 850 if vertical else 560
    draw.rectangle((0, 0, width, top_end), fill=(247, 249, 248, 255))
    draw.rectangle((0, bottom_start, width, height), fill=(247, 249, 248, 255))
    draw.rectangle((36, 32, 42, 55), fill=(24, 115, 117, 255))
    draw.text((55, 33), "SHANGHAI CITY TWIN  /  EARLY PREVIEW", font=font(20), fill="#326266")
    y = 85 if vertical else 66
    heading_font = font(45 if vertical else 35)
    for line in wrap(draw, scene["title"], heading_font, width-72):
        draw.text((36, y), line, font=heading_font, fill="#162a2d")
        y += 60 if vertical else 44
    detail_font = font(26 if vertical else 23)
    y += 8
    for line in wrap(draw, scene["detail"], detail_font, width-72):
        draw.text((36, y), line, font=detail_font, fill="#53676a")
        y += 39
    y = bottom_start + 24
    caption_font = font(30 if vertical else 24)
    for line in wrap(draw, scene["voice"], caption_font, width-72):
        draw.text((36, y), line, font=caption_font, fill="#1c3437")
        y += 43 if vertical else 32
    label_font = font(18 if vertical else 17)
    footer_lines = wrap(draw, footer, label_font, width-72)
    y = height - 22 - 26*len(footer_lines)
    for line in footer_lines:
        draw.text((36, y), line, font=label_font, fill="#526267")
        y += 26
    image.save(path)


def srt_time(seconds):
    milliseconds = round(seconds*1000)
    return f"{milliseconds//3600000:02}:{milliseconds//60000%60:02}:{milliseconds//1000%60:02},{milliseconds%1000:03}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--frames", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--font", default="/System/Library/Fonts/STHeiti Medium.ttc", type=Path)
    args = parser.parse_args()
    if not args.font.is_file() or not (args.frames / "0000.png").exists():
        parser.error("Font and rendered source frames must exist")
    args.output.mkdir(parents=True, exist_ok=True)
    root = args.data.resolve()
    report = json.loads((root / "reports/quality_report.json").read_text())
    manifest = json.loads((root / "motrix_scene/metadata/asset_manifest.json").read_text())
    buildings = json.loads((root / "layers/buildings.geojson").read_text())
    sources = Counter(f["properties"].get("height_source") or "missing" for f in buildings["features"])
    counts = report["counts"]
    exported = manifest["mesh_generation"]["exported_buildings"]
    skipped = manifest["mesh_generation"]["skipped_missing_height"]
    scenes = [
        {"title": "从开放地图，到 3D 场景", "detail": "真实 OSM 数据派生的建筑体块 · 上海核心区 POC",
         "voice": "这是从开放地图数据生成的上海建筑体块。我们把这条流水线开源，让开发者能检查来源，复现同一份真实数据。"},
        {"title": "每份输入，都有来源", "detail": f"{counts['buildings']:,} 个建筑轮廓  /  {counts['roads']:,} 条道路记录",
         "voice": f"这份上海样本包含 {counts['buildings']} 个建筑轮廓和 {counts['roads']} 条道路记录。来源、数据时间和质量报告，随输出一起保留。"},
        {"title": "数据缺口，也要看得见", "detail": f"{exported:,} 栋建筑体块  /  {skipped:,} 栋待补高度",
         "voice": f"当前导出 {exported} 栋建筑体块，跳过 {skipped} 栋缺少高度的建筑。看到的空缺，就是开放数据还需要补齐的地方。"},
        {"title": "标注高度与估算高度", "detail": f"{sources['height']} 栋高度标签  /  {sources['building:levels']} 栋按楼层估算",
         "voice": f"其中 {sources['height']} 栋带地图高度标签，{sources['building:levels']} 栋根据楼层估算。这是早期场景底座，还不是高精度数字孪生。"},
        {"title": "一份数据，多种输出", "detail": "glTF · OBJ · MJCF · URDF · Unreal 导入包",
         "voice": "同一份数据可以导出三维网格、场景描述和虚幻引擎导入包。各引擎的运行验收，将逐项记录。"},
        {"title": "开源早期版，先把复现做好", "detail": "代码 Apache-2.0 · 数据 ODbL · 真实存档样例",
         "voice": "代码采用 Apache 二点零许可，并提供真实存档样例。下一步补齐原尺寸分块和碰撞验证。源码链接见视频简介，欢迎复现和反馈。"},
    ]
    source_date = json.loads((root / "raw/osm_overpass.json").read_text())["osm3s"]["timestamp_osm_base"][:10]
    footer = f"OBJ 实际产物 · Blender 渲染 · 合成旁白 · {source_date} 样本\n© OpenStreetMap contributors | ODbL | openstreetmap.org/copyright"
    scenes_path = args.output / "narration.json"
    scenes_path.write_text(json.dumps(scenes, ensure_ascii=False, indent=2), encoding="utf-8")
    for index, scene in enumerate(scenes):
        text_path = args.output / f"voice-{index}.txt"
        text_path.write_text(scene["voice"], encoding="utf-8")
        audio = args.output / f"voice-{index}.aiff"
        run(["say", "-v", "Tingting", "-r", "160", "-f", text_path, "-o", audio])
        scene["duration"] = math.ceil((duration(audio)+1.0)*24)/24
    base_video = args.output / "scene-orbit.mp4"
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-framerate", "12", "-i", args.frames / "%04d.png",
         "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", base_video])
    output_info = {}
    for name, size, selection in [("landscape", (1280,720), list(range(6))), ("vertical", (720,1280), [0,2,5])]:
        segments, captions, start = [], [], 0.0
        for index in selection:
            scene = scenes[index]
            overlay = args.output / f"overlay-{name}-{index}.png"
            title_overlay(overlay, size, scene, footer, args.font)
            segment = args.output / f"segment-{name}-{index}.mp4"
            if name == "landscape":
                video_filter = "[0:v]scale=736:414,pad=1280:720:272:146:color=0xe8eeed[v];[v][1:v]overlay=0:0,format=yuv420p[out]"
            else:
                video_filter = "[0:v]crop=1000:720,scale=720:518,pad=720:1280:0:320:color=0xe8eeed[v];[v][1:v]overlay=0:0,format=yuv420p[out]"
            run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-stream_loop", "-1", "-ss", str(index*4), "-i", base_video,
                 "-loop", "1", "-i", overlay, "-i", args.output/f"voice-{index}.aiff", "-filter_complex", video_filter,
                 "-map", "[out]", "-map", "2:a:0", "-af", "apad,loudnorm=I=-16:TP=-1.5:LRA=7", "-t", str(scene["duration"]),
                 "-r", "24", "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-c:a", "aac", "-ar", "48000", "-ac", "2", segment])
            segments.append(segment)
            captions.append(f"{len(captions)+1}\n{srt_time(start)} --> {srt_time(start+scene['duration'])}\n{scene['voice']}\n")
            start += scene["duration"]
        concat = args.output/f"concat-{name}.txt"
        concat.write_text("\n".join(f"file '{p.name}'" for p in segments)+"\n", encoding="utf-8")
        final = args.output/f"shanghai-city-twin-{name}-draft.mp4"
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", concat,
             "-c", "copy", "-movflags", "+faststart", final])
        (args.output/f"shanghai-city-twin-{name}.srt").write_text("\n".join(captions), encoding="utf-8")
        output_info[name] = {"file": final.name, "duration_seconds": duration(final), "resolution": size,
                             "sha256": hashlib.sha256(final.read_bytes()).hexdigest()}
    proof = {"status": "draft_not_published", "renderer": "Blender Workbench, actual exported OBJ",
             "narrator": "macOS Tingting synthesized voice", "music": None,
             "source_sha256": hashlib.sha256((root/"raw/osm_overpass.json").read_bytes()).hexdigest(),
             "source_timestamp": json.loads((root/"raw/osm_overpass.json").read_text())["osm3s"]["timestamp_osm_base"],
             "source_mesh_sha256": hashlib.sha256((root/"motrix_scene/meshes/scene_visual.obj").read_bytes()).hexdigest(),
             "source_to_motrix_scale": manifest["source_to_motrix_scale"],
             "height_sources": dict(sources), "outputs": output_info}
    (args.output/"production-report.json").write_text(json.dumps(proof,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(output_info,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
