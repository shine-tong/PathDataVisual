# -*- coding: utf-8 -*-
"""
六轴机械臂轨迹静态绘图
支持信号类型: position、velocity、acceleration、effort

示例：
  python scripts/plot_six_axis.py --input data/message.json
  python scripts/plot_six_axis.py --input data/message_ros_sample.json --signal all --unit both
"""

import argparse
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import transforms as mtransforms


ANGULAR_SIGNALS = {"position", "velocity", "acceleration"}


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


def resolve_signal_matrix(data, signal, dt):
    positions = data["positions"]
    velocities = data.get("velocities")
    accelerations = data.get("accelerations")
    effort = data.get("effort")
    if effort is None:
        effort = data.get("effot")

    if velocities is None:
        velocities = derivative(positions, dt)
    if accelerations is None:
        accelerations = derivative(velocities, dt)
    if effort is None:
        effort = ensure_effort(positions, velocities, accelerations)

    if signal == "position":
        return positions
    if signal == "velocity":
        return velocities
    if signal == "acceleration":
        return accelerations
    if signal == "effort":
        return effort
    raise ValueError("unsupported signal: {}".format(signal))


def convert_unit(matrix, signal, unit):
    if signal not in ANGULAR_SIGNALS or unit == "rad":
        return matrix
    return [[math.degrees(v) for v in row] for row in matrix]


def signal_unit_label(signal, unit):
    if signal == "position":
        return "deg" if unit == "deg" else "rad"
    if signal == "velocity":
        return "deg/s" if unit == "deg" else "rad/s"
    if signal == "acceleration":
        return "deg/s^2" if unit == "deg" else "rad/s^2"
    return "Nm"


def signal_title(signal):
    if signal == "position":
        return "Position"
    if signal == "velocity":
        return "Velocity"
    if signal == "acceleration":
        return "Acceleration"
    return "Effort"


def build_output_path(base_path, signal, unit, multi_signal, multi_unit):
    base = Path(base_path)
    parent = base.parent
    if parent.name.lower() in {"position", "velocity", "acceleration", "effort"}:
        root_dir = parent.parent
    else:
        root_dir = parent
    signal_dir = root_dir / signal

    stem = base.stem

    if signal != "position" and signal not in stem:
        stem = "{}_{}".format(stem, signal)
    if multi_unit and unit == "deg":
        stem = "{}_deg".format(stem)

    return signal_dir / (stem + base.suffix)


def plot_signal(matrix, flags, signal, unit, save_path=None, show=False):
    sample_count = len(matrix)
    axis_series = list(zip(*matrix))
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

        ax.set_title("Axis {}".format(axis_idx))
        ax.grid(True, alpha=0.3)

    axes[3].set_xlabel("Point Index")
    axes[4].set_xlabel("Point Index")
    axes[5].set_xlabel("Point Index")

    unit_label = signal_unit_label(signal, unit)
    y_label = "{} ({})".format(signal_title(signal), unit_label)
    axes[0].set_ylabel(y_label)
    axes[3].set_ylabel(y_label)

    fig.suptitle("Manipulator {} Curves ({})".format(signal_title(signal), unit_label))
    fig.tight_layout(rect=[0, 0, 1, 0.96])

    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(str(save_path), dpi=160)
        print("saved: {}".format(save_path))

    if show:
        plt.show()
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/message.json", help="input JSON path")
    parser.add_argument("--output", default="outputs/PNG/position/manipulator_positions.png", help="base output png path")
    parser.add_argument("--signal", choices=["position", "velocity", "acceleration", "effort", "all"], default="all")
    parser.add_argument("--unit", choices=["rad", "deg", "both"], default="both")
    parser.add_argument("--dt", type=float, default=0.04, help="sampling interval in seconds for derivative fallback")
    parser.add_argument("--show", action="store_true", help="show window")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError("file not found: {}".format(input_path))

    data = load_trajectory(input_path)
    flags = data["flags"]

    signals = ["position", "velocity", "acceleration", "effort"] if args.signal == "all" else [args.signal]
    multi_signal = len(signals) > 1

    for signal in signals:
        units = ["rad", "deg"] if (signal in ANGULAR_SIGNALS and args.unit == "both") else ["deg" if args.unit == "deg" else "rad"]
        if signal == "effort":
            units = ["rad"]

        matrix = resolve_signal_matrix(data, signal, args.dt)
        for unit in units:
            converted = convert_unit(matrix, signal, unit)
            multi_unit = len(units) > 1
            save_path = build_output_path(args.output, signal, unit, multi_signal, multi_unit)
            plot_signal(converted, flags, signal, unit, save_path, args.show)


if __name__ == "__main__":
    main()
