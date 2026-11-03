# RoboTwin ICL 共享桌面

同一张桌子上固定摆放 16 个物体。物体位姿只由 seed 决定，和任务无关。

不同任务共用 `build_shared_table(task, seed)`，同一个 seed 会重建出同一张桌子。

相关文件：

| 文件 | 作用 |
| --- | --- |
| `envs/shared_table.py` | 16 个物体的槽位。`build_shared_table` 用独立的 `RandomState(seed)` 做小范围抖动，不占用全局随机数 |
| `env_cfg/task_config/shared_scene.yml` | 放置任务的采集配置。`episode_num: 2`，`embodiment: [aloha-agilex]`，关闭杂物桌和域随机 |
| `env_cfg/task_config/shared_grasp.yml` | 抓取检查的采集配置。`episode_num: 1`，其余与 `shared_scene.yml` 相同 |

## 任务  `shared_place_cube`

当前采集的任务是 `shared_place_cube`：aloha-agilex 的左臂把红色方块放到蓝色垫上。罐子留在桌上，不作为这次专家动作的目标。

**成功条件**：红方块中心与蓝色垫中心的水平距离小于 3 cm，方块高度接近原来放在桌面上的高度，两只夹爪张开。

#### 文件新增：

| 文件 | 作用 |
| --- | --- |
| `envs/shared_place_cube.py` | 任务类。`load_actors` 调用共享桌面，`play_once` 只操作红方块和蓝色垫 |
| `description/task_instruction/shared_place_cube.json` | 该任务的 seen / unseen 指令。`{A}` 是红方块，`{a}` 是手臂 |

修改：

| 文件 | 改动 |
| --- | --- |
| `envs/shared_grasp.py` | 按 `SHARED_GRASP_OBJECT` 抓一个物体。腕部不绕夹持轴转动 |
| `description/task_instruction/shared_grasp.json` | 抓取指令。`{A}` 是物体名，`{a}` 是手臂 |
| `env_cfg/task_config/_eval_step_limit.yml` | `shared_place_cube: 400`，`shared_grasp: 400` |
| `envs/utils/images_to_video.py` | 写视频时优先 `libx264`。当前环境的 ffmpeg 没有这个编码器，自动改用 `libopenh264`，再不行用 `mpeg4` |

桌子上的 16 个物体，槽位在 `envs/shared_table.py` 的 `TABLE_OBJECTS`。按钮是从 RMBench 拷来的 `005_button`，帽可以按下。旋钮是 `119_knob`，绕竖直轴转动。唯一的容器是中间的盘子。三块垫和 `move_pillbottle_pad` 一样，半尺寸 `(0.04, 0.04, 0.0005)`。方块半尺寸 `(0.02, 0.02, 0.02)`。

| 名字 | 模型 | 大约位置 (x, y) | 抓取 |
| --- | --- | --- | --- |
| bell | `050_bell` / 0 | (0.22, -0.32) | 右臂闭合夹爪按顶部。静态 |
| button | `005_button` / 0 | (-0.40, -0.10) | 左臂闭合夹爪下按。底座固定，帽行程 6 mm |
| knob | `119_knob` / 0 | (0.28, -0.08) | 资产没有夹取点，不抓 |
| hammer | `020_hammer` / 0 | (0.34, 0.00) | 右臂，接触点 0，夹锤柄短边 |
| scanner | `024_scanner` / 0 | (-0.30, -0.03) | 左臂，接触点 0，夹短边 |
| plate | `003_plate` / 0 | (0.12, 0.00) | 资产没有夹取点，不抓。静态，在中间 |
| cup | `021_cup` / 0 | (0.34, -0.18) | 右臂，接触点 0，手指向右 |
| blue_pad | 程序生成方块 | (-0.16, -0.04) | 左臂，接触点 0，手指沿左右。放置目标 |
| yellow_pad | 程序生成方块 | (0.00, -0.18) | 左臂，接触点 0 |
| purple_pad | 程序生成方块 | (0.10, -0.19) | 右臂，接触点 0 |
| red_cube | 程序生成方块 | (-0.16, -0.19) | 左臂，接触点 0。和蓝垫前后相距约 14.5 cm |
| green_cube | 程序生成方块 | (-0.30, -0.19) | 左臂，接触点 0 |
| blue_cube | 程序生成方块 | (-0.04, 0.00) | 左臂，接触点 1，手指沿前后 |
| cards | `081_playingcards` / 0 | (0.20, -0.19) | 右臂，接触点 0，手指沿左右 |
| roller | `102_roller` / 0 | (-0.33, -0.25) | 左臂，接触点 0，夹滚筒左端，手指沿前后 |
| can | `071_can` / 0 | (-0.06, -0.07) | 左臂，接触点 2，手指沿前后 |

头部相机只在 `build_shared_table` 里改，不改 `aloha-agilex` 的默认相机。位置 `(0, -0.42, 1.70)`，朝向桌面中心 `(0, 0.02, 0.74)`，这样 37° 垂直视场能罩住整张桌子。

锤子在右手边，扫描仪在左手边，盘子在中间。红方块和蓝垫都在左手侧，前后相距约 14.5 cm。张开的夹爪沿夹持方向大约伸出 ±8.4 cm，垂直方向大约 ±3.6 cm。每个能抓的物体只留出这一条空道，`play_once` 把左右腕的 `rotate_lim` 设成 `[0, 0]`，并传入上表里的接触点，避免手腕再转开去碰到旁边。罐子和紫垫旁边的空道仍然偏紧。铃铛、杯子和锤子的中心在常用抓取框附近，外轮廓会到大约 x = 0.40、y = 0.24。每个物体还会在槽位上做约 ±0.3 cm 平移和约 ±0.03 rad 偏航。铃铛、盘子、三块垫、锤子、扫描仪是静态物体。按钮和旋钮的底座固定。

## 抓取检查 `shared_grasp`

`envs/shared_grasp.py` 按环境变量 `SHARED_GRASP_OBJECT` 抓一个物体。能移动的物体再抬高 6 cm。成功条件是：使用的那只夹爪闭合，夹爪碰到目标，不碰到桌上其他物体，其他可动物体的水平位置移动不超过 1.5 cm。盘子和旋钮没有夹取点，不生成轨迹。

```bash
conda activate RoboTwin_ICL
cd /mnt/pre02/data/hqd/ICL_related/RoboTwin_ICL
SHARED_GRASP_OBJECT=red_cube SHARED_GRASP_MAX_FAIL=3 \
  bash collect_data.sh shared_grasp shared_grasp 0
```

`SHARED_GRASP_MAX_FAIL` 限制连续失败的 seed 次数，避免一个夹不到的物体一直重试。输出在 `data/shared_grasp/shared_grasp/<物体名>/aloha_agilex/`。

## 按按钮 `shared_press_button`

按钮原来在桌面后沿 `(-0.30, 0.19)`，离机器人基座大约 0.89 m，左臂规划不到。现在放在左前方 `(-0.40, -0.10)`。帽的滑动行程是 6 mm，关节有回位刚度，松手后会弹回。专家先把左夹爪闭合，再从正上方按下。

成功条件：左夹爪闭合，按钮关节比按下前至少低 3 mm，其他可动物体水平移动不超过 1.5 cm。

```bash
bash collect_data.sh shared_press_button shared_grasp 0
```

输出在 `data/shared_grasp/shared_press_button/aloha_agilex/`。seed `0` 一次成功，视频 68 帧。

## 采集

在仓库根目录 `RoboTwin_ICL/` 下执行。工作目录必须是仓库根目录，物体和机器人资产都用相对路径。

```bash
conda activate RoboTwin_ICL
cd /mnt/pre02/data/hqd/ICL_related/RoboTwin_ICL
bash collect_data.sh shared_place_cube shared_scene 0
```

第三个参数是 GPU 编号。脚本会设置 `CUDA_VISIBLE_DEVICES`，然后运行 `python scripts/collect_data.py shared_place_cube shared_scene`。

采集分两段：

1. 从 seed 0 递增，跑专家轨迹。规划成功、`check_success()` 为真、关节不超限才写入 `seed.txt`。凑满 `episode_num` 条后停止。
2. 按这些 seed 回放，写成 HDF5，并生成语言指令和视频。

已有 `seed.txt` 时会接着采，不会从头覆盖。已有 `data/episode_xxxxxxx.hdf5` 的条目会跳过。

改条数、机器人或相机时编辑 `env_cfg/task_config/shared_scene.yml`：

- `episode_num`：成功轨迹条数
- `embodiment`：一个名字表示左右臂同一台机器人，例如 `[aloha-agilex]`。三项表示左臂、右臂和间距，例如 `[franka-panda, ur5-wsg, 0.6]`
- 可选本体见 `env_cfg/task_config/_embodiment_config.yml`：`aloha-agilex`、`piper`、`franka-panda`、`ARX-X5`、`ur5-wsg`

换机器人时复制一份 yml，只改 `embodiment`。可达范围不同，需要重新搜 seed。

## 输出

```text
data/shared_scene/shared_place_cube/aloha_agilex/
  seed.txt
  scene_info.json
  _traj_data/episode0.pkl
  data/episode_0000000.hdf5
  video/episode_0000000.mp4
  instruction/episode_0000000.json
```

本体目录名由配置推导，`aloha-agilex` 对应 `aloha_agilex`。

这次采集 seed `0` 和 `1` 都一次成功，环境是 `RoboTwin_ICL`：

- `episode_0000000.hdf5`：135 帧
- `episode_0000001.hdf5`：136 帧

更早的举瓶试采集仍在 `data/shared_scene/shared_lift_bottle/aloha_agilex/`。

HDF5 里的图像要用 `decode_image_bit` 解码，不要再做 BGR/RGB 转换：

```python
from XPolicyLab.utils.process_data import decode_image_bit
rgb = decode_image_bit(image_bits)
```

## 在同一张桌子上加任务

1. 新建 `envs/<任务名>.py`，类名与文件名相同，继承 `Base_Task`。
2. `setup_demo` 里先保存 `self.scene_seed = kwags.get("seed", 0)`，再调用 `super()._init_task_env_(**kwags)`。
3. `load_actors` 里调用 `build_shared_table(self, self.scene_seed)`，只取出本任务要操作的物体。
4. 实现 `play_once` 和 `check_success`。`play_once` 返回的 `self.info["info"]` 占位符要和语言模板一致。
5. 新建 `description/task_instruction/<任务名>.json`。
6. 在 `env_cfg/task_config/_eval_step_limit.yml` 里写上该任务的步数上限。
7. 用同一个 `shared_scene.yml` 采集：

```bash
bash collect_data.sh <任务名> shared_scene 0
```

同一个 seed 会摆出同一张桌子。各任务单独采集时，失败的 seed 会被各自丢掉，episode 编号可能对不齐。要对齐时，把公共 seed 写进每个任务目录的 `seed.txt`，并把配置里的 `use_seed` 设为 `true`。
