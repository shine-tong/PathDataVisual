<div align="center">

# PathDataVisual

A 6-axis robot trajectory visualization toolkit built with `matplotlib`.

[![Python 3.8+][badge-python]][badge-python-link] [![Matplotlib][badge-mpl]][badge-mpl-link] [![Pillow][badge-pillow]][badge-pillow-link]
[![Output PNG][badge-png]][badge-png-link] [![Output GIF][badge-gif]][badge-gif-link] [![Data Joint+TCP][badge-data]][badge-data-link]
[![Single Window][badge-player]][badge-player-link] [![Batch All Curves][badge-batch]][badge-batch-link]

</div>

It provides:

- Static curve export (PNG)
- Animated curve export (GIF)
- Single-window interactive player
  (switch between Joint and TCP data sources)
- One-command batch generation for all curves

## Features

- Joint data (`message.json`):
  `position / velocity / acceleration / effort`
- TCP pose data (`message_tcp.json`):
  `position`, with `XYZ(m/mm)` and `ABC(rad/deg)` combinations
- Stage highlighting based on `flags`

## Project Layout

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

## Environment

- Python 3.8+
- Dependencies: `matplotlib`, `pillow`

Install:

```bash
pip install -r requirements.txt
```

## Input Data Format

Required fields:

- `positions`: `N x 6`
- `flags`: length `N`, aligned with `positions`

Optional fields:

- `velocities`
- `accelerations`
- `effort` (compatible alias: `effot`)

If optional fields are missing,
scripts derive fallback values using `--dt`.

## Script: plot_six_axis.py

Exports static plots (PNG).

```bash
python scripts/plot_six_axis.py \
  --input data/message.json \
  --signal all \
  --unit both
```

Common arguments:

- `--input`: input JSON path
- `--output`: base output path
- `--signal`: `position|velocity|acceleration|effort|all`
- `--unit`: `rad|deg|both` (angular unit)
- `--linear-unit`: `m|mm|both` (linear unit for TCP XYZ)
- `--data-type`: `auto|joint|tcp`
- `--dt`: sampling interval for derivatives (default `0.04`)
- `--show`: show figure window

Notes:

- Joint mode treats all 6 channels as angular values.
- TCP mode treats channels as `[X,Y,Z,A,B,C]`.
- In TCP position mode, all 4 unit combinations are supported:
  `m/rad`, `m/deg`, `mm/rad`, `mm/deg`.

## Script: animate_six_axis.py

Exports animated curves (GIF).

```bash
python scripts/animate_six_axis.py \
  --input data/message.json \
  --signal all \
  --unit both
```

Arguments are mostly the same as `plot_six_axis.py`, plus:

- `--fps`: GIF frame rate

## Script: player_six_axis.py

Single-window interactive player.

### Single source mode (legacy)

```bash
python scripts/player_six_axis.py --input data/message.json
```

### Dual source mode in one window (recommended)

```bash
python scripts/player_six_axis.py \
  --joint-input data/message.json \
  --tcp-input data/message_tcp.json
```

Interactive controls:

- `Data`: switch `joint/tcp`
- `Position/Velocity/Accel/Effort`: signal switch
- `Unit`: angular unit switch (`rad/deg`)
- `XYZ`: linear unit switch (`m/mm`, effective for TCP)
- `Play/Pause`: autoplay
- `Index` slider + mouse drag: manual inspection

Behavior:

- TCP source uses axis labels `X Y Z A B C`
- Joint source uses axis labels `Axis 1 ... Axis 6`
- Each source uses its own x-axis range

## Script: generate_all_curves.py

Generates all curves in one command (PNG + GIF).

```bash
python scripts/generate_all_curves.py
```

Default behavior:

- Joint: `position/velocity/acceleration/effort`
- TCP: `position`
  with `m/mm` and `rad/deg` combinations

Optional example:

```bash
python scripts/generate_all_curves.py \
  --joint-input data/message.json \
  --tcp-input data/message_tcp.json \
  --unit both \
  --linear-unit both \
  --fps 20
```

## Output Naming

Outputs are grouped by signal:

- `outputs/PNG/<signal>/`
- `outputs/GIF/<signal>/`

Suffix rules:

- Degree output: append `_deg`
- TCP mm output: append `_mm`
- Both applied: `_mm_deg`

Examples:

- `manipulator_positions.png`
- `manipulator_positions_deg.png`
- `tcp_pose_positions_mm.png`
- `tcp_pose_positions_mm_deg.png`

## Common Issues

### Only `position` is generated

Use `--signal all`.

### Curve shape does not change when switching `rad/deg`

This is expected.
Unit conversion is a linear scaling.

### Interactive window does not open

`player_six_axis.py` requires a desktop GUI environment.
Headless-only environments cannot display windows.

[badge-python]: https://img.shields.io/badge/Python-3.8%2B-3776AB
[badge-python-link]: ./scripts/player_six_axis.py
[badge-mpl]: https://img.shields.io/badge/Matplotlib-Enabled-11557C
[badge-mpl-link]: ./requirements.txt
[badge-pillow]: https://img.shields.io/badge/Pillow-Enabled-8CAAE6
[badge-pillow-link]: ./requirements.txt
[badge-png]: https://img.shields.io/badge/Output-PNG-2ECC71
[badge-png-link]: ./scripts/plot_six_axis.py
[badge-gif]: https://img.shields.io/badge/Output-GIF-F39C12
[badge-gif-link]: ./scripts/animate_six_axis.py
[badge-data]: https://img.shields.io/badge/Data-Joint%2BTCP-9B59B6
[badge-data-link]: ./data
[badge-player]: https://img.shields.io/badge/Player-Single%20Window-34495E
[badge-player-link]: ./scripts/player_six_axis.py
[badge-batch]: https://img.shields.io/badge/Batch-All%20Curves-1ABC9C
[badge-batch-link]: ./scripts/generate_all_curves.py
