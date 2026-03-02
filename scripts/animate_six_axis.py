# -*- coding: utf-8 -*-
"""
绘制六轴机械臂轨迹位置曲线动画
- 竖直虚线从起点移动到终点
- 每个轴实时显示当前数值文本

用法:
  python scripts/animate_six_axis.py
  python scripts/animate_six_axis.py --unit deg
  python scripts/animate_six_axis.py --unit both
"""

import argparse
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import transforms as mtransforms
from matplotlib.animation import FuncAnimation, PillowWriter

TAB10_HEX = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7f",
    "#bcbd22",
    "#17becf",
]


def load_trajectory(file_path):
    data = json.loads(Path(file_path).read_text(encoding="utf-8"))

    if "positions" not in data:
        raise KeyError("{} missing 'positions' field".format(file_path))
    if "flags" not in data:
        raise KeyError("{} missing 'flags' field".format(file_path))

    positions = data["positions"]
    flags = data["flags"]

    if not isinstance(positions, list) or len(positions) == 0:
        raise ValueError("'positions' must be a non-empty list")
    if not isinstance(flags, list):
        raise ValueError("'flags' must be a list")

    for i, row in enumerate(positions):
        if not isinstance(row, list) or len(row) != 6:
            raise ValueError("row {} is not 6-axis data: {}".format(i, row))

    if len(flags) != len(positions):
        raise ValueError("flags length {} != positions length {}".format(len(flags), len(positions)))

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


def convert_positions(positions, unit):
    if unit == "deg":
        return [[math.degrees(v) for v in row] for row in positions]
    return positions


def build_base_figure(positions, flags, unit):
    sample_count = len(positions)
    axis_series = list(zip(*positions))
    flag_ranges = get_flag_ranges(flags)
    start_indices = [i for i, f in enumerate(flags) if f == "start"]
    end_indices = [i for i, f in enumerate(flags) if f == "end"]

    fig, axes = plt.subplots(2, 3, figsize=(16, 8), sharex=True)
    axes = axes.flatten()

    # Keep the same stage-color assignment order as plot_six_axis.py:
    # first-seen stage -> tab10 color index
    color_map = {}
    for idx, (flag, _, _) in enumerate(flag_ranges):
        if flag not in color_map:
            color_map[flag] = TAB10_HEX[idx % 10]

    vlines = []
    value_texts = []
    point_markers = []

    for axis_idx, series in enumerate(axis_series, start=1):
        ax = axes[axis_idx - 1]
        ax.plot(range(sample_count), series, linewidth=1.6, color="#1f77b4")

        for flag, start, end in flag_ranges:
            ax.axvspan(start - 0.5, end + 0.5, color=color_map[flag], alpha=0.12)

        text_transform = mtransforms.blended_transform_factory(ax.transData, ax.transAxes)
        for flag, start, end in flag_ranges:
            if flag not in ("start", "end"):
                mid = (start + end) / 2.0
                ax.text(mid, 0.97, flag, transform=text_transform, ha="center", va="top", fontsize=8)

        if start_indices:
            y_start = [series[i] for i in start_indices]
            ax.scatter(start_indices, y_start, color="green", s=32, zorder=4)
        if end_indices:
            y_end = [series[i] for i in end_indices]
            ax.scatter(end_indices, y_end, color="red", s=32, zorder=4)

        vline = ax.axvline(0, color="black", linestyle="--", linewidth=1.5, alpha=0.9)
        marker, = ax.plot([0], [series[0]], marker="o", color="black", markersize=4, zorder=5)
        value_text = ax.text(
            0.02,
            0.05,
            "t=0, Axis {} = {:.4f} {}".format(axis_idx, series[0], unit),
            transform=ax.transAxes,
            fontsize=9,
            bbox={"facecolor": "white", "alpha": 0.75, "edgecolor": "none"},
        )

        vlines.append(vline)
        point_markers.append(marker)
        value_texts.append(value_text)

        ax.set_title("Axis {}".format(axis_idx))
        ax.grid(True, alpha=0.3)

    axes[3].set_xlabel("Point Index")
    axes[4].set_xlabel("Point Index")
    axes[5].set_xlabel("Point Index")
    axes[0].set_ylabel("Position ({})".format(unit))
    axes[3].set_ylabel("Position ({})".format(unit))
    fig.suptitle("Manipulator Position Animation ({})".format(unit))
    fig.tight_layout(rect=[0, 0, 1, 0.96])

    return fig, axis_series, vlines, point_markers, value_texts


def make_animation(positions, flags, output_path, unit="rad", fps=20):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    converted = convert_positions(positions, unit)
    fig, axis_series, vlines, point_markers, value_texts = build_base_figure(converted, flags, unit)
    sample_count = len(converted)

    def update(frame_idx):
        for i, series in enumerate(axis_series):
            x = frame_idx
            y = series[frame_idx]
            vlines[i].set_xdata([x, x])
            point_markers[i].set_data([x], [y])
            value_texts[i].set_text("t={}, Axis {} = {:.4f} {}".format(frame_idx, i + 1, y, unit))
        return vlines + point_markers + value_texts

    ani = FuncAnimation(
        fig,
        update,
        frames=sample_count,
        interval=int(1000 / max(fps, 1)),
        blit=False,
        repeat=True,
    )
    ani.save(str(output_path), writer=PillowWriter(fps=fps))
    plt.close(fig)
    print("GIF saved: {}".format(output_path))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/message.json", help="input JSON path")
    parser.add_argument("--output", default="outputs/manipulator_animation.gif", help="base output GIF path")
    parser.add_argument("--unit", choices=["rad", "deg", "both"], default="both", help="rad / deg / both")
    parser.add_argument("--fps", type=int, default=20, help="GIF frame rate")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError("file not found: {}".format(input_path))

    positions, flags = load_trajectory(input_path)

    output_rad = Path(args.output)
    output_deg = output_rad.with_name("{}_deg{}".format(output_rad.stem, output_rad.suffix))

    if args.unit == "both":
        make_animation(positions, flags, output_rad, "rad", args.fps)
        make_animation(positions, flags, output_deg, "deg", args.fps)
    elif args.unit == "rad":
        make_animation(positions, flags, output_rad, "rad", args.fps)
    else:
        make_animation(positions, flags, output_deg, "deg", args.fps)


if __name__ == "__main__":
    main()
