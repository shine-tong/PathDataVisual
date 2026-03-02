# PathDataVisual

六轴机械臂轨迹可视化项目，基于 `matplotlib`，提供：

- 静态曲线图导出（PNG）
- 动态曲线图导出（GIF）
- 单窗口交互播放与曲线切换

## 1. 项目结构

```text
PathDataVisual/
├─ data/
│  ├─ message.json
│  └─ message_ros_sample.json
├─ scripts/
│  ├─ plot_six_axis.py
│  ├─ animate_six_axis.py
│  └─ player_six_axis.py
├─ outputs/
│  ├─ PNG/
│  │  ├─ position/
│  │  ├─ velocity/
│  │  ├─ acceleration/
│  │  └─ effort/
│  └─ GIF/
│     ├─ position/
│     ├─ velocity/
│     ├─ acceleration/
│     └─ effort/
└─ README.md
```

## 2. 数据格式

输入 JSON 至少包含：

- `positions`: `N x 6` 位置数据
- `flags`: 长度 `N` 的阶段标签（与 `positions` 对齐）

可选字段（如有则直接使用）：

- `velocities`
- `accelerations`
- `effort`（或兼容 `effot`）

如果可选字段缺失，脚本会按 `--dt` 差分推导示例值。

## 3. 环境与依赖

- Python 3.8+
- 依赖：`matplotlib`、`pillow`

安装：

```bash
pip install -r requirements.txt
```

## 4. 静态图脚本（PNG）

```bash
python scripts/plot_six_axis.py \
  --input data/message_ros_sample.json \
  --signal all \
  --unit both
```

参数：

- `--input`: 输入 JSON 路径
- `--output`: 基础输出路径
  默认：`outputs/PNG/position/manipulator_positions.png`
- `--signal`: `position|velocity|acceleration|effort|all`
- `--unit`: `rad|deg|both`
  `effort` 固定为 `Nm`
- `--dt`: 差分采样间隔（默认 `0.04`）
- `--show`: 显示窗口

输出规则：

- 按信号类型写入：`outputs/PNG/<signal>/`
- 角度制文件自动追加 `_deg`

## 5. 动图脚本（GIF）

```bash
python scripts/animate_six_axis.py \
  --input data/message_ros_sample.json \
  --signal all \
  --unit both \
  --fps 20
```

参数：

- `--input`: 输入 JSON 路径
- `--output`: 基础输出路径
  默认：`outputs/GIF/position/manipulator_animation.gif`
- `--signal`: `position|velocity|acceleration|effort|all`
- `--unit`: `rad|deg|both`
  `effort` 固定为 `Nm`
- `--fps`: 帧率（默认 `20`）
- `--dt`: 差分采样间隔（默认 `0.04`）

输出规则：

- 按信号类型写入：`outputs/GIF/<signal>/`
- 角度制文件自动追加 `_deg`

## 6. 交互播放器（单窗口）

```bash
python scripts/player_six_axis.py \
  --input data/message_ros_sample.json \
  --unit rad \
  --fps 20
```

参数：

- `--input`: 输入 JSON 路径
- `--unit`: 初始角度单位 `rad|deg`
- `--fps`: 播放速度
- `--dt`: 差分采样间隔

交互功能：

- `Play/Pause`：自动播放
- 鼠标拖动竖线：手动定位点位
- `Index` 滑块：精确定位
- 信号切换：`Position / Velocity / Accel / Effort`
- 单位切换：`Unit: rad/deg`
  `effort` 读数保持 `Nm`

## 7. 常见问题

### 7.1 只看到 position 输出？

确认命令包含 `--signal all`，否则只会生成指定信号。

### 7.2 切换 deg/rad 后曲线形状为什么一样？

这是正常现象。单位切换是线性比例缩放（`* 180/pi`）。
曲线形状不变，仅纵轴数值变化。

### 7.3 交互窗口打不开

`player_six_axis.py` 需要桌面图形环境，
纯无头环境不会显示窗口。
