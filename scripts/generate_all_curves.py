# -*- coding: utf-8 -*-
"""
一键生成全部曲线 (PNG + GIF)
- 关节: position/velocity/acceleration/effort
- TCP: position (XYZ m/mm + ABC rad/deg)

示例：
  python scripts/generate_all_curves.py
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd):
    print("run: {}".format(" ".join(cmd)))
    subprocess.run(cmd, check=True)


def ensure_file_exists(path_obj, name):
    if not path_obj.exists():
        raise FileNotFoundError("{} not found: {}".format(name, path_obj))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--joint-input", default="data/message.json", help="joint json path")
    parser.add_argument("--tcp-input", default="data/message_tcp.json", help="tcp json path")
    parser.add_argument("--unit", choices=["rad", "deg", "both"], default="both", help="angular unit")
    parser.add_argument("--linear-unit", choices=["m", "mm", "both"], default="both", help="linear unit for TCP XYZ")
    parser.add_argument("--dt", type=float, default=0.04, help="sampling interval for derivative fallback")
    parser.add_argument("--fps", type=int, default=20, help="GIF frame rate")
    args = parser.parse_args()

    joint_input = Path(args.joint_input)
    tcp_input = Path(args.tcp_input)
    ensure_file_exists(joint_input, "joint input")
    ensure_file_exists(tcp_input, "tcp input")

    py = sys.executable
    script_dir = Path(__file__).resolve().parent
    plot_script = script_dir / "plot_six_axis.py"
    animate_script = script_dir / "animate_six_axis.py"

    # 1) 关节全部信号 PNG/GIF
    run_cmd(
        [
            py,
            str(plot_script),
            "--input",
            str(joint_input),
            "--signal",
            "all",
            "--unit",
            args.unit,
            "--data-type",
            "joint",
            "--dt",
            str(args.dt),
            "--output",
            "outputs/PNG/position/manipulator_positions.png",
        ]
    )

    run_cmd(
        [
            py,
            str(animate_script),
            "--input",
            str(joint_input),
            "--signal",
            "all",
            "--unit",
            args.unit,
            "--data-type",
            "joint",
            "--dt",
            str(args.dt),
            "--fps",
            str(args.fps),
            "--output",
            "outputs/GIF/position/manipulator_animation.gif",
        ]
    )

    # 2) TCP 位置信号 PNG/GIF（位姿）
    run_cmd(
        [
            py,
            str(plot_script),
            "--input",
            str(tcp_input),
            "--signal",
            "position",
            "--unit",
            args.unit,
            "--linear-unit",
            args.linear_unit,
            "--data-type",
            "tcp",
            "--dt",
            str(args.dt),
            "--output",
            "outputs/PNG/position/tcp_pose_positions.png",
        ]
    )

    run_cmd(
        [
            py,
            str(animate_script),
            "--input",
            str(tcp_input),
            "--signal",
            "position",
            "--unit",
            args.unit,
            "--linear-unit",
            args.linear_unit,
            "--data-type",
            "tcp",
            "--dt",
            str(args.dt),
            "--fps",
            str(args.fps),
            "--output",
            "outputs/GIF/position/tcp_pose_animation.gif",
        ]
    )

    print("done: all curves generated (joint + tcp, PNG + GIF)")


if __name__ == "__main__":
    main()
