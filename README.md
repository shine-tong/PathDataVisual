<!-- markdownlint-disable MD033 MD041 -->
<div align="center">

# PathDataVisual

⚙️ 基于 `matplotlib` 的六轴机器人轨迹可视化工具。

[![Python][b1]][l1] [![Matplotlib][b2]][l2] [![Pillow][b3]][l3]<br>
[![PNG][b4]][l4] [![GIF][b5]][l5] [![Joint+TCP][b6]][l6]<br>
[![Player][b7]][l7] [![Batch][b8]][l8]

</div>
<!-- markdownlint-enable MD033 MD041 -->

支持以下能力：

- 静态曲线导出（PNG）
- 动态曲线导出（GIF）
- 单窗口交互播放（支持关节与 TCP 切换）
- 一条命令批量生成全部曲线

## 功能概览

- 关节数据（`message.json`）：
  `position / velocity / acceleration / effort`
- TCP 位姿数据（`message_tcp.json`）：
  `position`，支持 `XYZ(m/mm)` 与 `ABC(rad/deg)`
- 根据 `flags` 自动做阶段着色

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

缺失可选字段时，脚本会基于 `--dt` 差分推导。

## 脚本：plot_six_axis.py

导出静态图（PNG）。

```bash
python scripts/plot_six_axis.py \
  --input data/message.json \
  --signal all \
  --unit both
```

常用参数：

- `--signal`: `position|velocity|acceleration|effort|all`
- `--unit`: `rad|deg|both`
- `--linear-unit`: `m|mm|both`（TCP 的 XYZ）
- `--data-type`: `auto|joint|tcp`

## 脚本：animate_six_axis.py

导出动图（GIF）。

```bash
python scripts/animate_six_axis.py \
  --input data/message.json \
  --signal all \
  --unit both \
  --fps 20
```

## 脚本：player_six_axis.py

单窗口交互播放器。

单数据源模式：

```bash
python scripts/player_six_axis.py --input data/message.json
```

双数据源同窗口模式（推荐）：

```bash
python scripts/player_six_axis.py \
  --joint-input data/message.json \
  --tcp-input data/message_tcp.json
```

主要交互：

- `Data`: 切换 `joint/tcp`
- `Position/Velocity/Accel/Effort`: 信号切换
- `Unit`: 切换 `rad/deg`
- `XYZ`: 切换 `m/mm`
- `Play/Pause`、`Index` 滑块、鼠标拖拽

## 脚本：generate_all_curves.py

一键批量生成全部曲线（PNG + GIF）。

```bash
python scripts/generate_all_curves.py
```

可选示例：

```bash
python scripts/generate_all_curves.py \
  --joint-input data/message.json \
  --tcp-input data/message_tcp.json \
  --unit both \
  --linear-unit both \
  --fps 20
```

## 输出命名规则

输出目录：

- `outputs/PNG/<signal>/`
- `outputs/GIF/<signal>/`

后缀规则：

- 度制：`_deg`
- TCP 毫米：`_mm`
- 同时满足：`_mm_deg`

示例：

- `manipulator_positions.png`
- `manipulator_positions_deg.png`
- `tcp_pose_positions_mm.png`
- `tcp_pose_positions_mm_deg.png`

## 常见问题

### 只生成了位置曲线

请确认使用 `--signal all`。

### 切换角度单位后曲线形状不变

这是正常现象，单位转换是线性缩放。

### 交互窗口无法显示

`player_six_axis.py` 需要桌面图形环境。

[b1]: https://img.shields.io/badge/Python-3.8%2B-3776AB
[l1]: ./scripts/player_six_axis.py
[b2]: https://img.shields.io/badge/Matplotlib-Enabled-11557C
[l2]: ./requirements.txt
[b3]: https://img.shields.io/badge/Pillow-Enabled-8CAAE6
[l3]: ./requirements.txt
[b4]: https://img.shields.io/badge/Output-PNG-2ECC71
[l4]: ./scripts/plot_six_axis.py
[b5]: https://img.shields.io/badge/Output-GIF-F39C12
[l5]: ./scripts/animate_six_axis.py
[b6]: https://img.shields.io/badge/Data-Joint%2BTCP-9B59B6
[l6]: ./data
[b7]: https://img.shields.io/badge/Player-Single%20Window-34495E
[l7]: ./scripts/player_six_axis.py
[b8]: https://img.shields.io/badge/Batch-All%20Curves-1ABC9C
[l8]: ./scripts/generate_all_curves.py
