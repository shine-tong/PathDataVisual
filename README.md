# PathDataVisual

六轴机械臂轨迹可视化项目，基于 `matplotlib` 对轨迹数据进行：
- 静态曲线绘图（PNG）
- 动态曲线动画导出（GIF）
- 交互式播放与拖动查看点位信息

## 1. 项目结构

```text
PathDataVisual/
├─ data/
│  └─ message.json
├─ scripts/
│  ├─ plot_six_axis.py       # 静态曲线图（默认同时生成rad/deg）
│  ├─ animate_six_axis.py    # 动画GIF（默认同时生成rad/deg）
│  └─ player_six_axis.py     # 交互播放器（Play/Pause + 拖动）
└─ outputs/                  # 输出目录（运行后生成）
```

## 2. 数据格式说明

输入数据为 JSON，核心字段：
- `positions`: `N x 6` 数组，表示 6 个轴在每个采样点的位置值（默认按弧度处理）
- `flags`: 长度为 `N` 的阶段标签列表（与 `positions` 一一对应）

示例结构：

```json
{
  "positions": [[...6 values...], [...]],
  "flags": ["during-p", "start", "during-l", "end", "go-home"],
  "weld_order": [1],
  "failed": []
}
```

## 3. 环境要求

- Python 3.8+
- 依赖：
  - `matplotlib`
  - `pillow`（GIF 导出需要）

安装依赖：

```bash
pip install matplotlib pillow
```

## 4. 快速开始

在项目根目录执行：

```bash
python scripts/plot_six_axis.py
```

默认会同时生成：
- `outputs/manipulator_positions.png`（rad）
- `outputs/manipulator_positions_deg.png`（deg）

## 5. 脚本说明

### 5.1 静态图脚本

```bash
python scripts/plot_six_axis.py [--input data/message.json] [--output outputs/manipulator_positions.png] [--unit rad|deg|both] [--show]
```

参数：
- `--input`: 输入 JSON 路径
- `--output`: 基础输出路径（rad 图使用该名称，deg 图自动追加 `_deg`）
- `--unit`: `rad` / `deg` / `both`，默认 `both`
- `--show`: 是否弹窗显示

图像特性：
- 2x3 布局（6轴）
- `start` 用绿色点标注，`end` 用红色点标注
- 阶段背景色按 `flags` 连续区间上色

### 5.2 动图脚本（GIF）

```bash
python scripts/animate_six_axis.py [--input data/message.json] [--output outputs/six_axis_animation.gif] [--unit rad|deg|both] [--fps 20]
```

参数：
- `--input`: 输入 JSON 路径
- `--output`: 基础 GIF 输出路径（deg 动图自动追加 `_deg`）
- `--unit`: `rad` / `deg` / `both`，默认 `both`
- `--fps`: 帧率，默认 `20`

动画特性：
- 竖直虚线从起点滑动到终点
- 实时显示每个轴当前点位数值
- 阶段背景颜色与静态 PNG 脚本保持一致

### 5.3 交互播放器脚本

```bash
python scripts/player_six_axis.py [--input data/message.json] [--unit rad|deg] [--fps 20]
```

交互能力：
- 点击 `Play/Pause` 自动播放
- 鼠标在图内拖动竖线手动定位点位
- 底部 `Index` 滑块可精确定位
- 实时显示当前采样点和阶段信息

## 6. 常见问题

### 6.1 没有生成文件

请检查：
- 是否在项目根目录执行命令
- `data/message.json` 是否存在且字段完整
- 是否有 `outputs/` 写权限

### 6.2 GIF 导出很慢

可降低帧率：

```bash
python scripts/animate_six_axis.py --fps 10
```

### 6.3 交互窗口打不开

`player_six_axis.py` 依赖图形界面环境。请在本地桌面环境（非纯终端/无头环境）运行。