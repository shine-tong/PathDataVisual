<div align="center">

# PathDataVisual

六轴机器人轨迹可视化工具，基于 `matplotlib`。

[![Python 3.8+][badge-python]][badge-python-link] [![Matplotlib][badge-mpl]][badge-mpl-link] [![Pillow][badge-pillow]][badge-pillow-link]
[![Output PNG][badge-png]][badge-png-link] [![Output GIF][badge-gif]][badge-gif-link] [![Data Joint+TCP][badge-data]][badge-data-link]
[![Single Window][badge-player]][badge-player-link] [![Batch All Curves][badge-batch]][badge-batch-link]

</div>

支持以下能力：

- 静态曲线导出（PNG）
- 动态曲线导出（GIF）
- 单窗口交互播放（支持关节与 TCP 数据源切换）
- 一条命令批量生成全部曲线

## 功能概览

- 关节数据（`message.json`）：
  `position / velocity / acceleration / effort`
- TCP 位姿数据（`message_tcp.json`）：
  `position`，并支持 `XYZ(m/mm)` 与 `ABC(rad/deg)` 组合
- 自动阶段着色：根据 `flags` 高亮不同阶段

## 项目结构

```text
PathDataVisual/
├─ data/
│  ├─ message.json
│  ├─ message_ros_sample.json
│  └─ message_tcp.json
├─ scripts/
│  ├─ plot_six_axis.py
│  ├─ animate_six_axis.py
│  ├─ player_six_axis.py
│  └─ generate_all_curves.py
├─ outputs/
│  ├─ PNG/
│  └─ GIF/
├─ README.md
└─ README_EN.md
```

## 环境要求

- Python 3.8+
- 依赖：`matplotlib`、`pillow`

安装：

```bash
pip install -r requirements.txt
```

## 数据格式

输入 JSON 必须包含：

- `positions`: `N x 6`
- `flags`: 长度为 `N`，与 `positions` 对齐

可选字段：

- `velocities`
- `accelerations`
- `effort`（兼容 `effot`）

若可选字段缺失，脚本会基于 `--dt` 进行差分推导。

## 脚本：plot_six_axis.py

导出静态图（PNG）。

```bash
python scripts/plot_six_axis.py \
  --input data/message.json \
  --signal all \
  --unit both
```

常用参数：

- `--input`: 输入 JSON 路径
- `--output`: 基础输出路径
- `--signal`: `position|velocity|acceleration|effort|all`
- `--unit`: `rad|deg|both`（角度单位）
- `--linear-unit`: `m|mm|both`（TCP 的 XYZ 线性单位）
- `--data-type`: `auto|joint|tcp`
- `--dt`: 差分采样周期（默认 `0.04`）
- `--show`: 显示窗口

说明：

- 关节数据默认语义：6 轴角度信号
- TCP 数据默认语义：`[X,Y,Z,A,B,C]`
- TCP 下位置可导出 4 组单位组合：
  `m/rad`、`m/deg`、`mm/rad`、`mm/deg`

## 脚本：animate_six_axis.py

导出动图（GIF）。

```bash
python scripts/animate_six_axis.py \
  --input data/message.json \
  --signal all \
  --unit both
```

常用参数与 `plot_six_axis.py` 基本一致，额外支持：

- `--fps`: GIF 帧率

## 脚本：player_six_axis.py

单窗口交互播放器。

### 单数据源模式（兼容旧用法）

```bash
python scripts/player_six_axis.py --input data/message.json
```

### 双数据源同窗口模式（推荐）

```bash
python scripts/player_six_axis.py \
  --joint-input data/message.json \
  --tcp-input data/message_tcp.json
```

交互按钮：

- `Data`: 在 `joint/tcp` 之间切换
- `Position/Velocity/Accel/Effort`: 信号切换
- `Unit`: `rad/deg` 角度切换
- `XYZ`: `m/mm` 线性单位切换（TCP 有效）
- `Play/Pause`: 自动播放
- `Index` 滑块 + 鼠标拖拽：手动定位

注意：

- 切到 `tcp` 时，坐标轴显示 `X Y Z A B C`
- 切到 `joint` 时，坐标轴显示 `Axis 1 ... Axis 6`
- 每个数据源使用自己的横坐标范围

## 脚本：generate_all_curves.py

一键批量生成全部曲线（PNG + GIF）。

```bash
python scripts/generate_all_curves.py
```

默认行为：

- 关节：生成 `position/velocity/acceleration/effort`
- TCP：生成 `position`（含 `m/mm` 与 `rad/deg` 组合）

可选参数：

```bash
python scripts/generate_all_curves.py \
  --joint-input data/message.json \
  --tcp-input data/message_tcp.json \
  --unit both \
  --linear-unit both \
  --fps 20
```

## 输出命名规则

输出目录按信号分类：

- `outputs/PNG/<signal>/`
- `outputs/GIF/<signal>/`

文件名后缀规则：

- 角度为度：追加 `_deg`
- TCP 线性单位为 mm：追加 `_mm`
- 同时满足：`_mm_deg`

示例：

- `manipulator_positions.png`
- `manipulator_positions_deg.png`
- `tcp_pose_positions_mm.png`
- `tcp_pose_positions_mm_deg.png`

## 常见问题

### 只生成了位置曲线

请确认 `--signal all`。

### 切换角度单位后曲线形状不变

这是正常现象，单位转换是线性缩放。

### 交互窗口无法显示

`player_six_axis.py` 需要桌面图形环境。
无头环境下无法弹窗。




[badge-python]: https://img.shields.io/badge/Python-3.8%2B-3776AB
[badge-python-link]: ./scripts/player_six_axis.py
[badge-mpl]: https://img.shields.io/badge/Matplotlib-Enabled-11557C
[badge-mpl-link]: ./requirements.txt
[badge-pillow]: https://img.shields.io/badge/Pillow-Enabled-8CAAE6
[badge-pillow-link]: ./requirements.txt
[badge-png]: https://img.shields.io/badge/Output-PNG-2ECC71
[badge-png-link]: ./scripts/plot_six_axis.py
[badge-gif]: https://img.shields.io/badge/Output-GIF-F39C12
[badge-gif-link]: ./scripts/animate_six_axis.py
[badge-data]: https://img.shields.io/badge/Data-Joint%2BTCP-9B59B6
[badge-data-link]: ./data
[badge-player]: https://img.shields.io/badge/Player-Single%20Window-34495E
[badge-player-link]: ./scripts/player_six_axis.py
[badge-batch]: https://img.shields.io/badge/Batch-All%20Curves-1ABC9C
[badge-batch-link]: ./scripts/generate_all_curves.py

