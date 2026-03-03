<!-- markdownlint-disable MD033 MD041 -->
<div align="center">

# PathDataVisual

⚙️ A `matplotlib`-based visualization toolkit for 6-axis robot trajectories.

[![Python][b1]][l1] [![Matplotlib][b2]][l2] [![Pillow][b3]][l3]
[![PNG][b4]][l4] [![GIF][b5]][l5] [![Joint+TCP][b6]][l6]
[![Player][b7]][l7] [![Batch][b8]][l8]

</div>
<!-- markdownlint-enable MD033 MD041 -->

It provides:

- Static curve export (PNG)
- Animated curve export (GIF)
- Single-window interactive player (Joint/TCP switch)
- One-command batch generation for all curves

## Features

- Joint data (`message.json`):
  `position / velocity / acceleration / effort`
- TCP pose data (`message_tcp.json`):
  `position`, with `XYZ(m/mm)` and `ABC(rad/deg)`
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
- `effort` (alias: `effot`)

If optional fields are missing,
scripts derive fallback values from `--dt`.

## Script: plot_six_axis.py

Exports static plots (PNG).

```bash
python scripts/plot_six_axis.py \
  --input data/message.json \
  --signal all \
  --unit both
```

Common arguments:

- `--signal`: `position|velocity|acceleration|effort|all`
- `--unit`: `rad|deg|both`
- `--linear-unit`: `m|mm|both` (TCP XYZ)
- `--data-type`: `auto|joint|tcp`

## Script: animate_six_axis.py

Exports animated plots (GIF).

```bash
python scripts/animate_six_axis.py \
  --input data/message.json \
  --signal all \
  --unit both \
  --fps 20
```

## Script: player_six_axis.py

Single-window interactive player.

Single source mode:

```bash
python scripts/player_six_axis.py --input data/message.json
```

Dual source mode in one window (recommended):

```bash
python scripts/player_six_axis.py \
  --joint-input data/message.json \
  --tcp-input data/message_tcp.json
```

Main controls:

- `Data`: switch `joint/tcp`
- `Position/Velocity/Accel/Effort`: switch signal
- `Unit`: switch `rad/deg`
- `XYZ`: switch `m/mm`
- `Play/Pause`, `Index` slider, mouse drag

## Script: generate_all_curves.py

Generates all curves in one command (PNG + GIF).

```bash
python scripts/generate_all_curves.py
```

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

Output directories:

- `outputs/PNG/<signal>/`
- `outputs/GIF/<signal>/`

Suffix rules:

- Degree output: `_deg`
- TCP mm output: `_mm`
- Both applied: `_mm_deg`

Examples:

- `manipulator_positions.png`
- `manipulator_positions_deg.png`
- `tcp_pose_positions_mm.png`
- `tcp_pose_positions_mm_deg.png`

## Common Issues

### Only position curves are generated

Use `--signal all`.

### Curve shape does not change when switching units

This is expected. Unit conversion is linear scaling.

### Interactive window does not open

`player_six_axis.py` requires a desktop GUI environment.

[b1]: https://img.shields.io/badge/Python-3.8%2B-3776AB
[l1]: ./scripts/player_six_axis.py
[b2]: https://img.shields.io/badge/Matplotlib-Enabled-11557C
[l2]: ./requirements.txt
[b3]: https://img.shields.io/badge/Pillow-Enabled-8CAAE6
[l3]: ./requirements.txt
[b4]: https://img.shields.io/badge/Output-PNG-2ECC71
[l4]: ./scripts/plot_six_axis.py
[b5]: https://img.shields.io/badge/Output-GIF-F39C12
[l5]: ./scripts/animate_six_axis.py
[b6]: https://img.shields.io/badge/Data-Joint%2BTCP-9B59B6
[l6]: ./data
[b7]: https://img.shields.io/badge/Player-Single%20Window-34495E
[l7]: ./scripts/player_six_axis.py
[b8]: https://img.shields.io/badge/Batch-All%20Curves-1ABC9C
[l8]: ./scripts/generate_all_curves.py

