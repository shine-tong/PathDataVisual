# -*- coding: utf-8 -*-
"""
六轴机械臂轨迹交互播放器
- Play/Pause 自动播放竖线
- 鼠标拖动竖线或使用滑块手动查看点位
- 按钮切换信号: Position / Velocity / Acceleration / Effort
- 按钮切换单位: rad / deg (角度) 与 m / mm (TCP 的 XYZ)
- 单窗口可切换数据源: Joint / TCP

示例：
  python scripts/player_six_axis.py --input data/message.json
  python scripts/player_six_axis.py --joint-input data/message.json --tcp-input data/message_tcp.json
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
TCP_COMPAT_SIGNALS = {"position", "velocity", "acceleration"}
JOINT_AXIS_LABELS = ["Axis 1", "Axis 2", "Axis 3", "Axis 4", "Axis 5", "Axis 6"]
TCP_AXIS_LABELS = ["X", "Y", "Z", "A", "B", "C"]


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


def detect_data_kind(input_path, user_choice):
    if user_choice != "auto":
        return user_choice
    return "tcp" if "tcp" in Path(input_path).stem.lower() else "joint"


def axis_labels(data_kind):
    return TCP_AXIS_LABELS if data_kind == "tcp" else JOINT_AXIS_LABELS


def prepare_signals(data, dt):
    positions = data["positions"]
    velocities = data.get("velocities") or derivative(positions, dt)
    accelerations = data.get("accelerations") or derivative(velocities, dt)
    effort = data.get("effort")
    if effort is None:
        effort = data.get("effot")
    if effort is None:
        effort = ensure_effort(positions, velocities, accelerations)

    return {
        "position": positions,
        "velocity": velocities,
        "acceleration": accelerations,
        "effort": effort,
    }


def signal_title(signal):
    if signal == "position":
        return "Position"
    if signal == "velocity":
        return "Velocity"
    if signal == "acceleration":
        return "Acceleration"
    return "Effort"


def convert_unit(matrix, signal, unit, data_kind, linear_unit):
    if signal not in ANGULAR_SIGNALS:
        return matrix
    if data_kind != "tcp":
        if unit == "rad":
            return matrix
        return [[math.degrees(v) for v in row] for row in matrix]

    converted = []
    for row in matrix:
        xyz = row[:3]
        abc = row[3:]
        if linear_unit == "mm":
            xyz = [v * 1000.0 for v in xyz]
        if unit == "deg":
            abc = [math.degrees(v) for v in abc]
        converted.append(xyz + abc)
    return converted


def signal_unit(signal, unit, data_kind="joint", linear_unit="m"):
    if data_kind == "tcp" and signal in TCP_COMPAT_SIGNALS:
        if signal == "position":
            return "XYZ {}, ABC {}".format(linear_unit, "deg" if unit == "deg" else "rad")
        if signal == "velocity":
            linear = "{}/s".format(linear_unit)
            angular = "deg/s" if unit == "deg" else "rad/s"
            return "XYZ {}, ABC {}".format(linear, angular)
        if signal == "acceleration":
            linear = "{}/s^2".format(linear_unit)
            angular = "deg/s^2" if unit == "deg" else "rad/s^2"
            return "XYZ {}, ABC {}".format(linear, angular)

    if signal == "position":
        return "deg" if unit == "deg" else "rad"
    if signal == "velocity":
        return "deg/s" if unit == "deg" else "rad/s"
    if signal == "acceleration":
        return "deg/s^2" if unit == "deg" else "rad/s^2"
    return "Nm"


def get_signal_series(raw_signal_data, signal, unit, data_kind, linear_unit):
    matrix = convert_unit(raw_signal_data[signal], signal, unit, data_kind, linear_unit)
    return list(zip(*matrix))


def build_data_source(data, data_kind, dt):
    return {
        "raw_signal_data": prepare_signals(data, dt),
        "flags": data["flags"],
        "sample_count": len(data["positions"]),
        "data_kind": data_kind,
    }


def build_interactive_player(data_sources, initial_source, unit, linear_unit, fps):
    source_names = list(data_sources.keys())
    if initial_source not in data_sources:
        initial_source = source_names[0]

    fig, axes = plt.subplots(2, 3, figsize=(16, 9), sharex=True)
    axes = axes.flatten()
    ax_list = list(axes)
    plt.subplots_adjust(bottom=0.18, right=0.88)

    lines = []
    vlines = []
    point_markers = []
    value_texts = []
    start_scatters = []
    end_scatters = []
    overlay_artists = [[] for _ in range(6)]

    initial_signal = "position"

    init_src = data_sources[initial_source]
    init_series_list = get_signal_series(init_src["raw_signal_data"], initial_signal, unit, init_src["data_kind"], linear_unit)

    for axis_idx in range(6):
        ax = axes[axis_idx]
        series = init_series_list[axis_idx]

        line, = ax.plot(range(len(series)), series, linewidth=1.6, color="#1f77b4")

        vline = ax.axvline(0, color="black", linestyle="--", linewidth=1.5, alpha=0.9, zorder=5)
        marker, = ax.plot([0], [series[0]], marker="o", color="black", markersize=4, zorder=6)
        unit_label = signal_unit(initial_signal, unit, data_kind=init_src["data_kind"], linear_unit=linear_unit)
        value_text = ax.text(
            0.02,
            0.05,
            "Axis {} = {:.4f} {}".format(axis_idx + 1, series[0], unit_label),
            transform=ax.transAxes,
            fontsize=9,
            bbox={"facecolor": "white", "alpha": 0.75, "edgecolor": "none"},
        )

        start_sc = ax.scatter([], [], color="green", s=32, zorder=4)
        end_sc = ax.scatter([], [], color="red", s=32, zorder=4)

        lines.append(line)
        start_scatters.append(start_sc)
        end_scatters.append(end_sc)
        vlines.append(vline)
        point_markers.append(marker)
        value_texts.append(value_text)

        ax.grid(True, alpha=0.3)

    axes[3].set_xlabel("Point Index")
    axes[4].set_xlabel("Point Index")
    axes[5].set_xlabel("Point Index")

    status_text = fig.text(0.02, 0.02, "", fontsize=10)

    slider_ax = fig.add_axes([0.15, 0.07, 0.52, 0.03])
    initial_count = init_src["sample_count"]
    slider = Slider(slider_ax, "Index", 0, max(initial_count - 1, 0), valinit=0, valstep=1)

    play_ax = fig.add_axes([0.73, 0.055, 0.10, 0.05])
    play_button = Button(play_ax, "Play")

    unit_ax = fig.add_axes([0.89, 0.055, 0.10, 0.05])
    unit_button = Button(unit_ax, "Unit: {}".format(unit))

    linear_ax = fig.add_axes([0.89, 0.115, 0.10, 0.05])
    linear_button = Button(linear_ax, "XYZ: {}".format(linear_unit))

    source_button = None
    if len(source_names) > 1:
        source_ax = fig.add_axes([0.89, 0.175, 0.10, 0.05])
        source_button = Button(source_ax, "Data: {}".format(initial_source))

    # Signal switch buttons
    btn_axes = {
        "position": fig.add_axes([0.89, 0.82, 0.10, 0.06]),
        "velocity": fig.add_axes([0.89, 0.74, 0.10, 0.06]),
        "acceleration": fig.add_axes([0.89, 0.66, 0.10, 0.06]),
        "effort": fig.add_axes([0.89, 0.58, 0.10, 0.06]),
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
        "linear_unit": linear_unit,
        "source": initial_source,
    }

    def current_source_data():
        return data_sources[state["source"]]

    def source_kind():
        return current_source_data()["data_kind"]

    def clear_overlay_for_axis(i):
        for art in overlay_artists[i]:
            try:
                art.remove()
            except ValueError:
                pass
        overlay_artists[i] = []

    def draw_source_overlays():
        src = current_source_data()
        flags = src["flags"]
        flag_ranges = get_flag_ranges(flags)

        color_map = {}
        cmap = plt.get_cmap("tab10")
        for idx, (flag, _, _) in enumerate(flag_ranges):
            if flag not in color_map:
                color_map[flag] = cmap(idx % 10)

        for i, ax in enumerate(axes):
            clear_overlay_for_axis(i)
            text_transform = mtransforms.blended_transform_factory(ax.transData, ax.transAxes)
            for flag, start, end in flag_ranges:
                span = ax.axvspan(start - 0.5, end + 0.5, color=color_map[flag], alpha=0.12, zorder=0)
                overlay_artists[i].append(span)
            for flag, start, end in flag_ranges:
                if flag not in ("start", "end"):
                    mid = (start + end) / 2.0
                    txt = ax.text(mid, 0.97, flag, transform=text_transform, ha="center", va="top", fontsize=8)
                    overlay_artists[i].append(txt)

    def clamp_idx(x):
        src = current_source_data()
        sample_count = src["sample_count"]
        if x is None:
            return 0
        idx = int(round(x))
        if idx < 0:
            return 0
        if idx >= sample_count:
            return sample_count - 1
        return idx

    def update_slider_range(sample_count):
        max_idx = max(sample_count - 1, 0)
        slider.valmin = 0
        slider.valmax = max_idx
        slider.ax.set_xlim(slider.valmin, slider.valmax)

    def set_frame(idx, from_slider=False):
        src = current_source_data()
        flags = src["flags"]
        series_list = get_signal_series(
            src["raw_signal_data"],
            state["signal"],
            state["unit"],
            src["data_kind"],
            state["linear_unit"],
        )
        idx = clamp_idx(idx)
        state["idx"] = idx

        u = signal_unit(state["signal"], state["unit"], data_kind=src["data_kind"], linear_unit=state["linear_unit"])

        for i, series in enumerate(series_list):
            y = series[idx]
            vlines[i].set_xdata([idx, idx])
            point_markers[i].set_data([idx], [y])
            value_texts[i].set_text("Axis {} = {:.4f} {}".format(i + 1, y, u))

        stage = flags[idx] if 0 <= idx < len(flags) else "N/A"
        status_text.set_text("Data: {} | Signal: {} | Index: {} | Stage: {}".format(state["source"], state["signal"], idx, stage))

        if not from_slider:
            state["updating_slider"] = True
            slider.set_val(idx)
            state["updating_slider"] = False

        fig.canvas.draw_idle()

    def apply_signal(signal):
        state["signal"] = signal
        src = current_source_data()
        flags = src["flags"]
        start_indices = [i for i, f in enumerate(flags) if f == "start"]
        end_indices = [i for i, f in enumerate(flags) if f == "end"]

        series_list = get_signal_series(
            src["raw_signal_data"],
            signal,
            state["unit"],
            src["data_kind"],
            state["linear_unit"],
        )

        labels = axis_labels(src["data_kind"])
        u = signal_unit(signal, state["unit"], data_kind=src["data_kind"], linear_unit=state["linear_unit"])
        y_label = "{} ({})".format(signal_title(signal), u)
        axes[0].set_ylabel(y_label)
        axes[3].set_ylabel(y_label)

        title_prefix = "TCP Pose" if src["data_kind"] == "tcp" else "Manipulator"
        fig.suptitle("{} Interactive Player: {} ({})".format(title_prefix, signal_title(signal), u))

        for i, series in enumerate(series_list):
            lines[i].set_data(range(len(series)), series)
            axes[i].set_title(labels[i])
            axes[i].set_xlim(-0.5, len(series) - 0.5)

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

            ymin = min(series)
            ymax = max(series)
            if ymax == ymin:
                pad = max(abs(ymax) * 0.05, 1e-6)
            else:
                pad = (ymax - ymin) * 0.08
            axes[i].set_ylim(ymin - pad, ymax + pad)

        update_slider_range(src["sample_count"])
        draw_source_overlays()
        set_frame(state["idx"], from_slider=False)

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

    def on_toggle_linear(_event):
        state["linear_unit"] = "mm" if state["linear_unit"] == "m" else "m"
        linear_button.label.set_text("XYZ: {}".format(state["linear_unit"]))
        apply_signal(state["signal"])

    def on_toggle_source(_event):
        if len(source_names) <= 1:
            return
        cur = state["source"]
        idx = source_names.index(cur)
        state["source"] = source_names[(idx + 1) % len(source_names)]
        if source_button is not None:
            source_button.label.set_text("Data: {}".format(state["source"]))
        apply_signal(state["signal"])

    def on_timer():
        if not state["playing"]:
            return
        src = current_source_data()
        sample_count = src["sample_count"]
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
    linear_button.on_clicked(on_toggle_linear)
    if source_button is not None:
        source_button.on_clicked(on_toggle_source)

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
    parser.add_argument("--input", default="data/message.json", help="single input JSON path (legacy mode)")
    parser.add_argument("--joint-input", default=None, help="joint JSON path for all-in-one mode")
    parser.add_argument("--tcp-input", default=None, help="tcp JSON path for all-in-one mode")
    parser.add_argument("--source", choices=["joint", "tcp"], default="joint", help="initial source in all-in-one mode")
    parser.add_argument("--data-type", choices=["auto", "joint", "tcp"], default="auto", help="single input semantics")
    parser.add_argument("--unit", choices=["rad", "deg"], default="rad", help="angular unit for position/velocity/acceleration")
    parser.add_argument("--linear-unit", choices=["m", "mm"], default="m", help="linear unit for TCP XYZ")
    parser.add_argument("--fps", type=int, default=20, help="playback frame rate")
    parser.add_argument("--dt", type=float, default=0.04, help="sampling interval for derivative fallback")
    args = parser.parse_args()

    data_sources = {}

    if args.joint_input or args.tcp_input:
        if not args.joint_input or not args.tcp_input:
            raise ValueError("all-in-one mode requires both --joint-input and --tcp-input")

        joint_path = Path(args.joint_input)
        tcp_path = Path(args.tcp_input)
        if not joint_path.exists():
            raise FileNotFoundError("file not found: {}".format(joint_path))
        if not tcp_path.exists():
            raise FileNotFoundError("file not found: {}".format(tcp_path))

        joint_data = load_trajectory(joint_path)
        tcp_data = load_trajectory(tcp_path)
        data_sources["joint"] = build_data_source(joint_data, "joint", args.dt)
        data_sources["tcp"] = build_data_source(tcp_data, "tcp", args.dt)
        initial_source = args.source
    else:
        input_path = Path(args.input)
        if not input_path.exists():
            raise FileNotFoundError("file not found: {}".format(input_path))

        data = load_trajectory(input_path)
        data_kind = detect_data_kind(input_path, args.data_type)
        src_name = "tcp" if data_kind == "tcp" else "joint"
        data_sources[src_name] = build_data_source(data, data_kind, args.dt)
        initial_source = src_name

    build_interactive_player(data_sources, initial_source, args.unit, args.linear_unit, args.fps)


if __name__ == "__main__":
    main()
