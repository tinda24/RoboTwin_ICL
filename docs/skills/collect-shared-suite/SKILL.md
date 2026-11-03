---
name: collect-shared-suite
description: >-
  Collect RoboTwin shared-table demonstrations into data/shared_suite, 50
  episodes per verified task. Use when the user asks to collect, restart, or
  check shared_suite data, collect_data.sh, or the task_suite tasks.
---

# 采集共享桌面数据

在 `RoboTwin_ICL` 仓库根目录运行。Python 用 `/mnt/pre02/data/hqd/miniconda3/envs/RoboTwin_ICL/bin/python`。正式配置是 `env_cfg/task_config/shared_suite.yml`（`episode_num: 50`，`collect_data: true`）。

物体水平位置 ±10 mm、朝向 ±5°，写在 `envs/shared_table.py` 的 `_jittered_pose`。同一个 seed 摆放相同。当前任务用的是这张桌子，不是 `shared_table_variation_*.py`。

## 先验证，再采 50 条

专家动作没在 `shared_suite_debug` 上成功过，不要放进 50 条队列。调试配置 `episode_num: 1`、`collect_data: false`，只检查规划和 `check_success`，不写 hdf5。

```bash
cd /mnt/pre02/data/hqd/ICL_related/RoboTwin_ICL
export PATH=/mnt/pre02/data/hqd/miniconda3/envs/RoboTwin_ICL/bin:$PATH
export PYTHONUNBUFFERED=1
mkdir -p /tmp/suite_logs
SHARED_GRASP_MAX_FAIL=2 bash collect_data.sh <任务名> shared_suite_debug <空闲GPU> \
  > /tmp/suite_logs/<任务名>.log 2>&1
```

日志里要有 `success!`。`SHARED_GRASP_MAX_FAIL` 只用于调试；采 50 条时不要设它，失败的 seed 会跳过，直到成功 50 条。

## 采 50 条

先看 `nvidia-smi`。每条进程大约要 8GB 以上空闲显存。已经有 `collect_data.py` 在采 `shared_suite` 时，不要再启动一份。

```bash
bash docs/skills/collect-shared-suite/scripts/collect_shared_suite.sh <GPU> [GPU ...]
```

脚本把下面 23 个已验证任务轮流分到传入的 GPU 上，日志在 `/tmp/suite_logs/collect50_<任务名>.log` 和 `collect50_queue.log`。已有的 `seed.txt` 会接着采，不会删数据。

`shared_place_cube`、`shared_place_green_pad`、`shared_place_cup_pad`、`shared_place_cards_pad`、`shared_stack_green_red`、`shared_stack_red_green`、`shared_stack_blue_green`、`shared_place_red_yellow`、`shared_place_cards_plate`、`shared_place_cup_plate`、`shared_place_green_blue`、`shared_place_can_pad`、`shared_press_button`、`shared_turn_knob_cw`、`shared_turn_knob_ccw`、`shared_push_cards`、`shared_push_red_pad`、`shared_lift_green_cup`、`shared_lift_red_cards`、`shared_pinch_hammer`、`shared_pinch_scanner`、`shared_press_bell`、`shared_lift_roller`。

`shared_handover_cards` 和 `shared_handover_green` 还没验证通过，不在这张表里。左手把物体放进盘子也不可达，对应任务已改成放到垫上。

单任务：

```bash
bash collect_data.sh <任务名> shared_suite <GPU>
```

## 输出

`data/shared_suite/<任务名>/aloha_agilex/`

- `data/episode_*.hdf5`
- `video/`
- `instruction/`
- `seed.txt`
- `scene_info.json`

采集分两段：先找满 50 个成功 seed，再回放写成 hdf5 和视频。`seed.txt` 已经是 50，hdf5 仍可能少几条，那是在写盘。

一条任务大约 1.5 到 2 小时。队列自己往下走，日志出现 `ALL_COLLECT_DONE` 才是全部结束。

## 不要中途改动作

`shared_motion.py` 和已经在采的 `play_once` 不要改。回放吃的是保存下来的关节轨迹，动作步数变了会对不上。改完某条任务的动作后，先删掉该任务的 `data/shared_suite/<任务名>`，再用 debug 配置重跑，成功后才重新采 50 条。

用户明确要求重新开始时：先停掉队列进程和它的 `collect_data.py`，确认没有残留，再删掉指定的数据目录，然后重新跑脚本。不要只杀掉 python，父脚本还会接着拉起下一个任务。
