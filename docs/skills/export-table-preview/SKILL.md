---
name: export-table-preview
description: >-
  Render head-camera preview PNGs of the RoboTwin shared table and
  shared_table_variation_1 through 10 into docs/table_preview. Use when the
  user asks to export, refresh, or visualize shared-table layouts, table
  previews, or docs/table_preview.
---

# 导出共享桌面预览

从 `RoboTwin_ICL` 仓库根目录运行。Python 用 `/mnt/pre02/data/hqd/miniconda3/envs/RoboTwin_ICL/bin/python`。

整套 11 张大约 25 分钟。第一张还要加载 SAPIEN 和运动规划库；之后每张约 2 分钟。时间花在 `setup_demo`：加载双臂和 16 个物体、物理空跑两千多步等落稳、再用光线追踪渲 640×480 的头部相机。不要为了加快而关掉落稳或降低采样，否则画面和采集场景不一致。

## 选 GPU

先看 `nvidia-smi` 和正在跑的 `collect_data.py`。用一张空闲、剩余显存大约 8GB 以上的卡。不要占用正在采 `data/shared_suite` 的卡，也不要停掉采集。

## 运行

```bash
cd /mnt/pre02/data/hqd/ICL_related/RoboTwin_ICL
export PATH=/mnt/pre02/data/hqd/miniconda3/envs/RoboTwin_ICL/bin:$PATH
export CUDA_VISIBLE_DEVICES=<空闲GPU>
export PYTHONUNBUFFERED=1
python docs/skills/export-table-preview/scripts/export_table_preview.py
```

只重渲其中几张时加上名字：

```bash
python docs/skills/export-table-preview/scripts/export_table_preview.py \
  --layouts shared_table shared_table_variation_3
```

脚本会改 `envs.shared_place_cube.build_shared_table` 指向当前布局，只在这个进程里生效。seed 固定为 0。腕部相机不采集。

## 输出

默认目录是 `docs/table_preview/`：

- `shared_table.png`
- `shared_table_variation_1.png` … `shared_table_variation_10.png`

图上方有布局名字。视角与采集视频相同，靠近机器人的物体会被夹爪挡住一部分。日志里出现 `ALL_PREVIEWS` 才算全部写完。
