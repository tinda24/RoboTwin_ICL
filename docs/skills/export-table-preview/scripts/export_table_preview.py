"""Render one head-camera preview per shared-table layout.

Run from the RoboTwin_ICL repo root with the RoboTwin_ICL conda Python.
Set CUDA_VISIBLE_DEVICES before starting. Each layout rebuilds the scene, so
the full set takes about 25 minutes.
"""

import argparse
import importlib
import os

import numpy as np
import yaml
from PIL import Image, ImageDraw

from envs._GLOBAL_CONFIGS import CONFIGS_PATH
import envs.shared_place_cube as task_mod
from envs.shared_place_cube import shared_place_cube
from envs.shared_table import build_shared_table as original_build


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="docs/table_preview")
    parser.add_argument(
        "--layouts",
        nargs="*",
        help="Names such as shared_table or shared_table_variation_3. Default: all 11.",
    )
    return parser.parse_args()


def load_args():
    with open(os.path.join(CONFIGS_PATH, "shared_suite_debug.yml"), "r", encoding="utf-8") as file:
        args = yaml.load(file.read(), Loader=yaml.FullLoader)
    with open(os.path.join(CONFIGS_PATH, "_embodiment_config.yml"), "r", encoding="utf-8") as file:
        embodiment_types = yaml.load(file.read(), Loader=yaml.FullLoader)
    robot_file = embodiment_types["aloha-agilex"]["file_path"]
    with open(os.path.join(robot_file, "config.yml"), "r", encoding="utf-8") as file:
        robot_cfg = yaml.load(file.read(), Loader=yaml.FullLoader)
    args.update(
        task_name="shared_place_cube",
        left_robot_file=robot_file,
        right_robot_file=robot_file,
        dual_arm_embodied=True,
        left_embodiment_config=robot_cfg,
        right_embodiment_config=robot_cfg,
        embodiment_name="aloha-agilex",
        need_plan=True,
        render_freq=0,
        save_data=False,
        seed=0,
        now_ep_num=0,
    )
    args["camera"]["head_camera_type"] = "Large_D435"
    args["camera"]["collect_wrist_camera"] = False
    args["data_type"] = {"rgb": True}
    return args


def layouts_to_render(selected):
    available = [("shared_table", original_build)]
    for index in range(1, 11):
        module = importlib.import_module(f"envs.shared_table_variation_{index}")
        available.append((f"shared_table_variation_{index}", module.build_shared_table))
    if not selected:
        return available
    by_name = dict(available)
    missing = [name for name in selected if name not in by_name]
    if missing:
        raise SystemExit(f"unknown layout: {', '.join(missing)}")
    return [(name, by_name[name]) for name in selected]


def save_preview(rgb, path, title):
    image = Image.fromarray(np.asarray(rgb))
    canvas = Image.new("RGB", (image.width, image.height + 28), (255, 255, 255))
    canvas.paste(image, (0, 28))
    ImageDraw.Draw(canvas).text((8, 6), title, fill=(0, 0, 0))
    canvas.save(path)


def main():
    options = parse_args()
    os.makedirs(options.output, exist_ok=True)
    scene_args = load_args()
    for name, builder in layouts_to_render(options.layouts):
        print(f"RENDER {name}", flush=True)
        task_mod.build_shared_table = builder
        env = shared_place_cube()
        try:
            env.setup_demo(**scene_args)
            rgb = env.get_obs()["observation"]["head_camera"]["rgb"]
            path = os.path.join(options.output, f"{name}.png")
            save_preview(rgb, path, name)
            print(f"SAVED {path}", flush=True)
        finally:
            env.close_env()
    print("ALL_PREVIEWS", flush=True)


if __name__ == "__main__":
    main()
