"""Render an existing exported OBJ for launch footage with Blender.

Run with blender --background --python scripts/render_launch_scene.py -- ...
This is an asset visualization, not evidence of simulation-engine compatibility.
"""

import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--frames", default=360, type=int)
    parser.add_argument("--width", default=1280, type=int)
    parser.add_argument("--height", default=720, type=int)
    parser.add_argument("--sample-only", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    mesh_path = args.package.resolve() / "meshes/scene_visual.obj"
    if not mesh_path.is_file() or args.frames <= 0:
        parser.error("An exported visual OBJ and positive frame count are required")
    args.output.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.wm.obj_import(filepath=str(mesh_path), forward_axis="Y", up_axis="Z")
    meshes = [obj for obj in bpy.context.selected_objects if obj.type == "MESH"]
    points = [obj.matrix_world @ vertex.co for obj in meshes for vertex in obj.data.vertices]
    low = Vector(tuple(min(p[a] for p in points) for a in range(3)))
    high = Vector(tuple(max(p[a] for p in points) for a in range(3)))
    center = (low + high) / 2
    extent = max(high - low)
    for obj in meshes:
        obj.color = (0.11, 0.43, 0.48, 1)
    bpy.ops.mesh.primitive_plane_add(size=extent * 1.7, location=(center.x, center.y, low.z - extent * .001))
    bpy.context.object.color = (.82, .85, .85, 1)
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = extent * 1.55
    camera.data.clip_end = extent * 15
    camera.data.clip_start = extent * .0001
    scene = bpy.context.scene
    scene.camera = camera
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = args.width
    scene.render.resolution_y = args.height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.fps = 12
    scene.view_settings.view_transform = "Standard"
    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.color_type = "OBJECT"
    shading.show_shadows = True
    shading.show_cavity = True
    shading.cavity_type = "BOTH"
    shading.show_object_outline = True
    shading.background_type = "WORLD"
    scene.world.color = (.82, .85, .85)
    scene.display.render_aa = "8"
    frames = [0] if args.sample_only else range(args.frames)
    for index in frames:
        angle = -math.pi / 3 + 2 * math.pi * index / args.frames
        camera.location = center + Vector((math.cos(angle)*extent*1.5, math.sin(angle)*extent*1.5, extent*1.25))
        camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(args.output.resolve() / f"{index:04d}.png")
        bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output.resolve().parent / "launch-scene.blend"))


if __name__ == "__main__":
    main()
