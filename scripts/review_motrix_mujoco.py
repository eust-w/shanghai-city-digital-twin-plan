from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Load a MotrixSim MJCF scene with MuJoCo.")
    parser.add_argument("scene_xml", type=Path, help="Path to motrix_scene/scene.xml")
    parser.add_argument("--viewer", action="store_true", help="Launch the interactive MuJoCo viewer.")
    parser.add_argument("--steps", type=int, default=10, help="Headless simulation steps.")
    parser.add_argument("--lock-lookat", action="store_true", help="Keep the viewer orbit center fixed while running.")
    args = parser.parse_args()

    import mujoco

    scene_xml = args.scene_xml.expanduser().resolve()
    model = mujoco.MjModel.from_xml_path(str(scene_xml))
    data = mujoco.MjData(model)
    for _ in range(max(0, args.steps)):
        mujoco.mj_step(model, data)

    manifest_path = scene_xml.parent / "metadata" / "asset_manifest.json"
    manifest = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    summary = {
        "scene_xml": str(scene_xml),
        "mjcf_loaded": True,
        "nbody": int(model.nbody),
        "ngeom": int(model.ngeom),
        "nmesh": int(model.nmesh),
        "nmeshvert": int(model.nmeshvert),
        "nmeshface": int(model.nmeshface),
        "source_to_motrix_scale": manifest.get("source_to_motrix_scale"),
        "exported_buildings": manifest.get("mesh_generation", {}).get("exported_buildings"),
        "headless_steps": max(0, args.steps),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if args.viewer:
        _launch_viewer(model, data, mujoco, lock_lookat=args.lock_lookat)
    return 0


def _launch_viewer(model, data, mujoco, lock_lookat: bool = False) -> None:
    import mujoco.viewer

    center = [float(v) for v in model.stat.center]
    extent = max(float(model.stat.extent), 10.0)
    with mujoco.viewer.launch_passive(model, data) as viewer:
        with viewer.lock():
            viewer.cam.type = mujoco.mjtCamera.mjCAMERA_FREE
            viewer.cam.lookat[:] = center
            viewer.cam.distance = extent * 1.15
            viewer.cam.azimuth = 135
            viewer.cam.elevation = -42
            viewer.opt.flags[mujoco.mjtVisFlag.mjVIS_TRANSPARENT] = 0
        while viewer.is_running():
            mujoco.mj_step(model, data)
            if lock_lookat:
                with viewer.lock():
                    viewer.cam.lookat[:] = center
            viewer.sync()
            time.sleep(0.02)


if __name__ == "__main__":
    raise SystemExit(main())
