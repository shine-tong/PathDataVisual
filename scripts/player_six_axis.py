# -*- coding: utf-8 -*-
"""
六轴轨迹交互播放器：
- 点击 Play/Pause 自动播放
- 鼠标在子图内拖动竖线，手动查看点位信息
- 底部 Slider 也可手动拖动

用法:
  python scripts/player_six_axis.py
  python scripts/player_six_axis.py --unit deg --fps 24
"""

import argparse
import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import transforms as mtransforms
from matplotlib.widgets import Button, Slider


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


def convert_positions(positions, unit):
    if unit == "deg":
        return [[math.degrees(v) for v in row] for row in positions]
    return positions


def build_interactive_player(positions, flags, unit, fps):
    positions = convert_positions(positions, unit)
    sample_count = len(positions)
    axis_series = list(zip(*positions))
    flag_ranges = get_flag_ranges(flags)
    start_indices = [i for i, f in enumerate(flags) if f == "start"]
    end_indices = [i for i, f in enumerate(flags) if f == "end"]

    fig, axes = plt.subplots(2, 3, figsize=(16, 8), sharex=True)
    axes = axes.flatten()
    plt.subplots_adjust(bottom=0.16)

    # 与 plot_six_axis.py 保持一致：按阶段出现顺序分配 tab10 颜色
    color_map = {}
    cmap = plt.get_cmap("tab10")
    for idx, (flag, _, _) in enumerate(flag_ranges):
        if flag not in color_map:
            color_map[flag] = cmap(idx % 10)

    vlines = []
    markers = []
    value_texts = []

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

        vline = ax.axvline(0, color="black", linestyle="--", linewidth=1.5, alpha=0.9, zorder=5)
        marker, = ax.plot([0], [series[0]], marker="o", color="black", markersize=4, zorder=6)
        value_text = ax.text(
            0.02,
            0.05,
            "Axis {} = {:.4f} {}".format(axis_idx, series[0], unit),
            transform=ax.transAxes,
            fontsize=9,
            bbox={"facecolor": "white", "alpha": 0.75, "edgecolor": "none"},
        )

        vlines.append(vline)
        markers.append(marker)
        value_texts.append(value_text)

        ax.set_title("Axis {}".format(axis_idx))
        ax.grid(True, alpha=0.3)

    axes[3].set_xlabel("Point Index")
    axes[4].set_xlabel("Point Index")
    axes[5].set_xlabel("Point Index")
    axes[0].set_ylabel("Position ({})".format(unit))
    axes[3].set_ylabel("Position ({})".format(unit))

    status_text = fig.text(0.02, 0.02, "", fontsize=10)
    fig.suptitle("Manipulator Interactive Player ({})".format(unit))

    slider_ax = fig.add_axes([0.15, 0.07, 0.60, 0.03])
    slider = Slider(slider_ax, "Index", 0, sample_count - 1, valinit=0, valstep=1)

    button_ax = fig.add_axes([0.79, 0.055, 0.13, 0.055])
    button = Button(button_ax, "Play")

    state = {
        "idx": 0,
        "playing": False,
        "dragging": False,
        "updating_slider": False,
    }

    def clamp_idx(x):
        if x is None:
            return None
        idx = int(round(x))
        if idx < 0:
            return 0
        if idx >= sample_count:
            return sample_count - 1
        return idx

    def set_frame(idx, from_slider=False):
        idx = clamp_idx(idx)
        if idx is None:
            return
        state["idx"] = idx

        for i, series in enumerate(axis_series):
            y = series[idx]
            vlines[i].set_xdata([idx, idx])
            markers[i].set_data([idx], [y])
            value_texts[i].set_text("Axis {} = {:.4f} {}".format(i + 1, y, unit))

        status_text.set_text("Index: {} | Stage: {}".format(idx, flags[idx]))

        if not from_slider:
            state["updating_slider"] = True
            slider.set_val(idx)
            state["updating_slider"] = False

        fig.canvas.draw_idle()

    def on_slider_change(val):
        if state["updating_slider"]:
            return
        set_frame(int(val), from_slider=True)

    def on_toggle_play(_event):
        state["playing"] = not state["playing"]
        button.label.set_text("Pause" if state["playing"] else "Play")
        fig.canvas.draw_idle()

    def on_timer():
        if not state["playing"]:
            return
        next_idx = (state["idx"] + 1) % sample_count
        set_frame(next_idx)

    def on_press(event):
        if event.button != 1:
            return
        if event.inaxes in axes:
            state["dragging"] = True
            if state["playing"]:
                state["playing"] = False
                button.label.set_text("Play")
            set_frame(event.xdata)

    def on_motion(event):
        if not state["dragging"]:
            return
        if event.inaxes in axes:
            set_frame(event.xdata)

    def on_release(_event):
        state["dragging"] = False

    slider.on_changed(on_slider_change)
    button.on_clicked(on_toggle_play)
    fig.canvas.mpl_connect("button_press_event", on_press)
    fig.canvas.mpl_connect("motion_notify_event", on_motion)
    fig.canvas.mpl_connect("button_release_event", on_release)

    timer = fig.canvas.new_timer(interval=max(int(1000 / max(fps, 1)), 1))
    timer.add_callback(on_timer)
    timer.start()

    set_frame(0)
    plt.show()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/message.json", help="输入JSON文件路径")
    parser.add_argument("--unit", choices=["rad", "deg"], default="rad", help="位置单位：rad 或 deg")
    parser.add_argument("--fps", type=int, default=20, help="播放帧率")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError("文件不存在: {}".format(input_path))

    positions, flags = load_trajectory(input_path)
    build_interactive_player(positions, flags, args.unit, args.fps)


if __name__ == "__main__":
    main()
