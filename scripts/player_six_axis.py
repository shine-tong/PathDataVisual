# -*- coding: utf-8 -*-
"""
六轴机械臂轨迹交互播放器
- Play/Pause 自动播放竖线
- 鼠标拖动竖线或使用滑块手动查看点位
- 按钮切换信号: Position / Velocity / Acceleration / Effort
- 按钮切换单位: rad / deg(effort 固定 Nm)

示例：
  python scripts/player_six_axis.py --input data/message_ros_sample.json
  python scripts/player_six_axis.py --input data/message.json --unit deg
"""

import argparse
import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import transforms as mtransforms
from matplotlib.widgets import Button, Slider

ANGULAR_SIGNALS = {"position", "velocity", "acceleration"}
SIGNALS = ["position", "velocity", "acceleration", "effort"]


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

    return data


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


def derivative(values, dt):
    n = len(values)
    jn = len(values[0]) if n else 0
    out = [[0.0] * jn for _ in range(n)]

    for i in range(n):
        for j in range(jn):
            if n == 1:
                out[i][j] = 0.0
            elif i == 0:
                out[i][j] = (values[i + 1][j] - values[i][j]) / dt
            elif i == n - 1:
                out[i][j] = (values[i][j] - values[i - 1][j]) / dt
            else:
                out[i][j] = (values[i + 1][j] - values[i - 1][j]) / (2.0 * dt)
    return out


def ensure_effort(positions, velocities, accelerations):
    n = len(positions)
    jn = len(positions[0]) if n else 0
    effort = [[0.0] * jn for _ in range(n)]
    for i in range(n):
        for j in range(jn):
            effort[i][j] = 0.35 * abs(positions[i][j]) + 0.12 * abs(velocities[i][j]) + 0.03 * abs(accelerations[i][j])
    return effort


def prepare_signals(data, dt):
    positions = data["positions"]
    velocities = data.get("velocities") or derivative(positions, dt)
    accelerations = data.get("accelerations") or derivative(velocities, dt)
    effort = data.get("effort")
    if effort is None:
        effort = data.get("effot")
    if effort is None:
        effort = ensure_effort(positions, velocities, accelerations)

    signal_data_rad = {
        "position": positions,
        "velocity": velocities,
        "acceleration": accelerations,
        "effort": effort,
    }

    signal_data_deg = {
        "position": [[math.degrees(v) for v in row] for row in positions],
        "velocity": [[math.degrees(v) for v in row] for row in velocities],
        "acceleration": [[math.degrees(v) for v in row] for row in accelerations],
        "effort": effort,
    }

    return {"rad": signal_data_rad, "deg": signal_data_deg}


def signal_title(signal):
    if signal == "position":
        return "Position"
    if signal == "velocity":
        return "Velocity"
    if signal == "acceleration":
        return "Acceleration"
    return "Effort"


def signal_unit(signal, unit):
    if signal == "position":
        return "deg" if unit == "deg" else "rad"
    if signal == "velocity":
        return "deg/s" if unit == "deg" else "rad/s"
    if signal == "acceleration":
        return "deg/s^2" if unit == "deg" else "rad/s^2"
    return "Nm"


def build_interactive_player(data, unit, fps, dt):
    flags = data["flags"]
    signal_data_by_unit = prepare_signals(data, dt)
    sample_count = len(data["positions"])

    # per signal -> list of 6 series
    signal_series_by_unit = {
        "rad": {k: list(zip(*v)) for k, v in signal_data_by_unit["rad"].items()},
        "deg": {k: list(zip(*v)) for k, v in signal_data_by_unit["deg"].items()},
    }

    flag_ranges = get_flag_ranges(flags)
    start_indices = [i for i, f in enumerate(flags) if f == "start"]
    end_indices = [i for i, f in enumerate(flags) if f == "end"]

    fig, axes = plt.subplots(2, 3, figsize=(16, 9), sharex=True)
    axes = axes.flatten()
    ax_list = list(axes)
    plt.subplots_adjust(bottom=0.18, right=0.88)

    color_map = {}
    cmap = plt.get_cmap("tab10")
    for idx, (flag, _, _) in enumerate(flag_ranges):
        if flag not in color_map:
            color_map[flag] = cmap(idx % 10)

    lines = []
    vlines = []
    point_markers = []
    value_texts = []
    start_scatters = []
    end_scatters = []

    initial_signal = "position"

    for axis_idx in range(6):
        ax = axes[axis_idx]
        series = signal_series_by_unit[unit][initial_signal][axis_idx]

        line, = ax.plot(range(sample_count), series, linewidth=1.6, color="#1f77b4")

        for flag, start, end in flag_ranges:
            ax.axvspan(start - 0.5, end + 0.5, color=color_map[flag], alpha=0.12)

        text_transform = mtransforms.blended_transform_factory(ax.transData, ax.transAxes)
        for flag, start, end in flag_ranges:
            if flag not in ("start", "end"):
                mid = (start + end) / 2.0
                ax.text(mid, 0.97, flag, transform=text_transform, ha="center", va="top", fontsize=8)

        if start_indices:
            y_start = [series[i] for i in start_indices]
            start_sc = ax.scatter(start_indices, y_start, color="green", s=32, zorder=4)
        else:
            start_sc = ax.scatter([], [], color="green", s=32, zorder=4)

        if end_indices:
            y_end = [series[i] for i in end_indices]
            end_sc = ax.scatter(end_indices, y_end, color="red", s=32, zorder=4)
        else:
            end_sc = ax.scatter([], [], color="red", s=32, zorder=4)

        vline = ax.axvline(0, color="black", linestyle="--", linewidth=1.5, alpha=0.9, zorder=5)
        marker, = ax.plot([0], [series[0]], marker="o", color="black", markersize=4, zorder=6)
        unit_label = signal_unit(initial_signal, unit)
        value_text = ax.text(
            0.02,
            0.05,
            "Axis {} = {:.4f} {}".format(axis_idx + 1, series[0], unit_label),
            transform=ax.transAxes,
            fontsize=9,
            bbox={"facecolor": "white", "alpha": 0.75, "edgecolor": "none"},
        )

        lines.append(line)
        start_scatters.append(start_sc)
        end_scatters.append(end_sc)
        vlines.append(vline)
        point_markers.append(marker)
        value_texts.append(value_text)

        ax.set_title("Axis {}".format(axis_idx + 1))
        ax.grid(True, alpha=0.3)

    axes[3].set_xlabel("Point Index")
    axes[4].set_xlabel("Point Index")
    axes[5].set_xlabel("Point Index")

    status_text = fig.text(0.02, 0.02, "", fontsize=10)

    slider_ax = fig.add_axes([0.15, 0.07, 0.52, 0.03])
    slider = Slider(slider_ax, "Index", 0, sample_count - 1, valinit=0, valstep=1)

    play_ax = fig.add_axes([0.69, 0.055, 0.10, 0.05])
    play_button = Button(play_ax, "Play")
    unit_ax = fig.add_axes([0.80, 0.055, 0.10, 0.05])
    unit_button = Button(unit_ax, "Unit: {}".format(unit))

    # Signal switch buttons (single window)
    btn_axes = {
        "position": fig.add_axes([0.89, 0.76, 0.10, 0.06]),
        "velocity": fig.add_axes([0.89, 0.68, 0.10, 0.06]),
        "acceleration": fig.add_axes([0.89, 0.60, 0.10, 0.06]),
        "effort": fig.add_axes([0.89, 0.52, 0.10, 0.06]),
    }
    signal_buttons = {
        "position": Button(btn_axes["position"], "Position"),
        "velocity": Button(btn_axes["velocity"], "Velocity"),
        "acceleration": Button(btn_axes["acceleration"], "Accel"),
        "effort": Button(btn_axes["effort"], "Effort"),
    }

    state = {
        "idx": 0,
        "playing": False,
        "dragging": False,
        "updating_slider": False,
        "signal": initial_signal,
        "unit": unit,
    }

    def apply_signal(signal):
        state["signal"] = signal
        current_unit = state["unit"]
        series_list = signal_series_by_unit[current_unit][signal]
        u = signal_unit(signal, current_unit)
        y_label = "{} ({})".format(signal_title(signal), u)
        axes[0].set_ylabel(y_label)
        axes[3].set_ylabel(y_label)
        fig.suptitle("Manipulator Interactive Player: {} ({})".format(signal_title(signal), u))

        for i, series in enumerate(series_list):
            lines[i].set_data(range(sample_count), series)

            if start_indices:
                start_offsets = np.column_stack((start_indices, [series[idx] for idx in start_indices]))
                start_scatters[i].set_offsets(start_offsets)
            else:
                start_scatters[i].set_offsets(np.empty((0, 2)))

            if end_indices:
                end_offsets = np.column_stack((end_indices, [series[idx] for idx in end_indices]))
                end_scatters[i].set_offsets(end_offsets)
            else:
                end_scatters[i].set_offsets(np.empty((0, 2)))

            ax = axes[i]
            # Explicitly reset y-limits from current signal/unit data to avoid
            # stale autoscale state when toggling between deg and rad.
            ymin = min(series)
            ymax = max(series)
            if ymax == ymin:
                pad = max(abs(ymax) * 0.05, 1e-6)
            else:
                pad = (ymax - ymin) * 0.08
            ax.set_ylim(ymin - pad, ymax + pad)

        set_frame(state["idx"], from_slider=False)

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
        signal = state["signal"]
        current_unit = state["unit"]
        series_list = signal_series_by_unit[current_unit][signal]
        u = signal_unit(signal, current_unit)

        for i, series in enumerate(series_list):
            y = series[idx]
            vlines[i].set_xdata([idx, idx])
            point_markers[i].set_data([idx], [y])
            value_texts[i].set_text("Axis {} = {:.4f} {}".format(i + 1, y, u))

        status_text.set_text("Signal: {} | Index: {} | Stage: {}".format(signal, idx, flags[idx]))

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
        play_button.label.set_text("Pause" if state["playing"] else "Play")
        fig.canvas.draw_idle()

    def on_toggle_unit(_event):
        state["unit"] = "deg" if state["unit"] == "rad" else "rad"
        unit_button.label.set_text("Unit: {}".format(state["unit"]))
        apply_signal(state["signal"])

    def on_timer():
        if not state["playing"]:
            return
        set_frame((state["idx"] + 1) % sample_count)

    def on_press(event):
        if event.button != 1:
            return
        if event.inaxes in ax_list:
            state["dragging"] = True
            if state["playing"]:
                state["playing"] = False
                play_button.label.set_text("Play")
            set_frame(event.xdata)

    def on_motion(event):
        if not state["dragging"]:
            return
        if event.inaxes in ax_list:
            set_frame(event.xdata)

    def on_release(_event):
        state["dragging"] = False

    slider.on_changed(on_slider_change)
    play_button.on_clicked(on_toggle_play)
    unit_button.on_clicked(on_toggle_unit)
    signal_buttons["position"].on_clicked(lambda _e: apply_signal("position"))
    signal_buttons["velocity"].on_clicked(lambda _e: apply_signal("velocity"))
    signal_buttons["acceleration"].on_clicked(lambda _e: apply_signal("acceleration"))
    signal_buttons["effort"].on_clicked(lambda _e: apply_signal("effort"))

    fig.canvas.mpl_connect("button_press_event", on_press)
    fig.canvas.mpl_connect("motion_notify_event", on_motion)
    fig.canvas.mpl_connect("button_release_event", on_release)

    timer = fig.canvas.new_timer(interval=max(int(1000 / max(fps, 1)), 1))
    timer.add_callback(on_timer)
    timer.start()

    apply_signal(initial_signal)
    plt.show()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/message.json", help="input JSON path")
    parser.add_argument("--unit", choices=["rad", "deg"], default="rad", help="angular unit for position/velocity/acceleration")
    parser.add_argument("--fps", type=int, default=20, help="playback frame rate")
    parser.add_argument("--dt", type=float, default=0.04, help="sampling interval for derivative fallback")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError("file not found: {}".format(input_path))

    data = load_trajectory(input_path)
    build_interactive_player(data, args.unit, args.fps, args.dt)


if __name__ == "__main__":
    main()
