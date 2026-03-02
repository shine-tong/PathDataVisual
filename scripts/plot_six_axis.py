# -*- coding: utf-8 -*-
"""
绘制六轴机械臂轨迹位置曲线
用法:
  python scripts/plot_six_axis.py
  python scripts/plot_six_axis.py --input data/message.json --output outputs/six_axis_positions.png --show
"""

import argparse
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import transforms as mtransforms


def load_trajectory(file_path):
    data = json.loads(Path(file_path).read_text(encoding="utf-8"))

    if "positions" not in data:
        raise KeyError("{} 中未找到 'positions' 字段".format(file_path))
    if "flags" not in data:
        raise KeyError("{} 中未找到 'flags' 字段".format(file_path))

    positions = data["positions"]
    flags = data["flags"]

    if not isinstance(positions, list) or len(positions) == 0:
        raise ValueError("'positions' 不是有效的非空列表")
    if not isinstance(flags, list):
        raise ValueError("'flags' 不是有效列表")

    for i, row in enumerate(positions):
        if not isinstance(row, list) or len(row) != 6:
            raise ValueError("第 {} 行不是6轴数据: {}".format(i, row))

    if len(flags) != len(positions):
        raise ValueError("flags 长度({}) 与 positions 长度({}) 不一致".format(len(flags), len(positions)))

    return positions, flags


def get_flag_ranges(flags):
    ranges = []
    if not flags:
        return ranges

    start = 0
    current = flags[0]
    for i, flag in enumerate(flags[1:], start=1):
        if flag != current:
            ranges.append((current, start, i - 1))
            start = i
            current = flag
    ranges.append((current, start, len(flags) - 1))
    return ranges


def plot_positions(positions, flags, save_path=None, show=False, unit="rad"):
    sample_count = len(positions)
    if unit == "deg":
        positions = [[math.degrees(v) for v in row] for row in positions]
    axis_series = list(zip(*positions))
    flag_ranges = get_flag_ranges(flags)
    start_indices = [i for i, f in enumerate(flags) if f == "start"]
    end_indices = [i for i, f in enumerate(flags) if f == "end"]

    fig, axes = plt.subplots(2, 3, figsize=(16, 8), sharex=True)
    axes = axes.flatten()

    color_map = {}
    cmap = plt.get_cmap("tab10")
    for idx, (flag, _, _) in enumerate(flag_ranges):
        if flag not in color_map:
            color_map[flag] = cmap(idx % 10)

    for axis_idx, series in enumerate(axis_series, start=1):
        ax = axes[axis_idx - 1]
        ax.plot(range(sample_count), series, linewidth=1.6, color="#1f77b4")

        for flag, start, end in flag_ranges:
            color = color_map[flag]
            ax.axvspan(start - 0.5, end + 0.5, color=color, alpha=0.12)

        # 在每个子图顶部按采样索引标注阶段范围
        text_transform = mtransforms.blended_transform_factory(ax.transData, ax.transAxes)
        for flag, start, end in flag_ranges:
            mid = (start + end) / 2.0
            if flag not in ("start", "end"):
                ax.text(mid, 0.97, flag, transform=text_transform, ha="center", va="top", fontsize=8)

        if start_indices:
            y_start = [series[i] for i in start_indices]
            ax.scatter(start_indices, y_start, color="green", s=32, zorder=4)
        if end_indices:
            y_end = [series[i] for i in end_indices]
            ax.scatter(end_indices, y_end, color="red", s=32, zorder=4)

        ax.set_title("Axis {}".format(axis_idx))
        ax.grid(True, alpha=0.3)

    axes[3].set_xlabel("Point Index")
    axes[4].set_xlabel("Point Index")
    axes[5].set_xlabel("Point Index")
    axes[0].set_ylabel("Position ({})".format(unit))
    axes[3].set_ylabel("Position ({})".format(unit))

    fig.suptitle("Manipulator Position Curves ({})".format(unit))
    fig.tight_layout(rect=[0, 0, 1, 0.96])

    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(str(save_path), dpi=160)
        print("图像已保存: {}".format(save_path))

    if show:
        plt.show()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/message.json", help="输入JSON文件路径")
    parser.add_argument("--output", default="outputs/manipulator_positions.png", help="输出图片路径")
    parser.add_argument("--unit", choices=["rad", "deg", "both"], default="both", help="位置单位：rad、deg 或 both")
    parser.add_argument("--show", action="store_true", help="是否弹窗显示图像")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError("文件不存在: {}".format(input_path))

    positions, flags = load_trajectory(input_path)

    output_rad = Path(args.output)
    output_deg = output_rad.with_name("{}_deg{}".format(output_rad.stem, output_rad.suffix))

    if args.unit == "both":
        plot_positions(positions, flags, output_rad, args.show, "rad")
        plot_positions(positions, flags, output_deg, args.show, "deg")
    elif args.unit == "rad":
        plot_positions(positions, flags, output_rad, args.show, "rad")
    else:
        plot_positions(positions, flags, output_deg, args.show, "deg")


if __name__ == "__main__":
    main()
