# PathDataVisual

A 6-axis robot trajectory visualization toolkit built with `matplotlib`.

It provides:

- Static curve export (PNG)
- Animated curve export (GIF)
- Single-window interactive player

## 1. Project Structure

```text
PathDataVisual/
├─ data/
│  ├─ message.json
│  └─ message_ros_sample.json
├─ scripts/
│  ├─ plot_six_axis.py
│  ├─ animate_six_axis.py
│  └─ player_six_axis.py
├─ outputs/
│  ├─ PNG/
│  │  ├─ position/
│  │  ├─ velocity/
│  │  ├─ acceleration/
│  │  └─ effort/
│  └─ GIF/
│     ├─ position/
│     ├─ velocity/
│     ├─ acceleration/
│     └─ effort/
└─ README.md
```

## 2. Input Data Format

Required fields in input JSON:

- `positions`: `N x 6` joint position data
- `flags`: stage labels with length `N` (aligned with `positions`)

Optional fields (used directly if present):

- `velocities`
- `accelerations`
- `effort` (or compatible alias `effot`)

If optional fields are missing,
scripts derive fallback data from `positions` with `--dt`.

## 3. Requirements

- Python 3.8+
- Dependencies: `matplotlib`, `pillow`

Install:

```bash
pip install -r requirements.txt
```

## 4. Static Plot Script (PNG)

```bash
python scripts/plot_six_axis.py \
  --input data/message_ros_sample.json \
  --signal all \
  --unit both
```

Arguments:

- `--input`: input JSON path
- `--output`: base output path
  default: `outputs/PNG/position/manipulator_positions.png`
- `--signal`: `position|velocity|acceleration|effort|all`
- `--unit`: `rad|deg|both`
  `effort` always stays in `Nm`
- `--dt`: sampling interval for fallback derivatives (`0.04`)
- `--show`: display figure window

Output rules:

- Files are written to `outputs/PNG/<signal>/`
- Degree versions append `_deg`

## 5. Animation Script (GIF)

```bash
python scripts/animate_six_axis.py \
  --input data/message_ros_sample.json \
  --signal all \
  --unit both \
  --fps 20
```

Arguments:

- `--input`: input JSON path
- `--output`: base output path
  default: `outputs/GIF/position/manipulator_animation.gif`
- `--signal`: `position|velocity|acceleration|effort|all`
- `--unit`: `rad|deg|both`
  `effort` always stays in `Nm`
- `--fps`: frame rate (default `20`)
- `--dt`: sampling interval for fallback derivatives (`0.04`)

Output rules:

- Files are written to `outputs/GIF/<signal>/`
- Degree versions append `_deg`

## 6. Interactive Player (Single Window)

```bash
python scripts/player_six_axis.py \
  --input data/message_ros_sample.json \
  --unit rad \
  --fps 20
```

Arguments:

- `--input`: input JSON path
- `--unit`: initial angular unit `rad|deg`
- `--fps`: playback speed
- `--dt`: sampling interval for fallback derivatives

Interactive features:

- `Play/Pause` for auto-play
- Drag the vertical cursor for manual inspection
- `Index` slider for precise navigation
- Signal switch: `Position / Velocity / Accel / Effort`
- Unit switch: `Unit: rad/deg`
  `effort` remains in `Nm`

## 7. FAQ

### 7.1 Only position output is generated

Use `--signal all` to generate all signal types.

### 7.2 Why does the curve shape stay the same in rad/deg?

This is expected. Unit switching is linear scaling (`* 180/pi`).
The curve shape stays the same while y-values change.

### 7.3 Interactive window does not open

`player_six_axis.py` requires a desktop GUI environment.
It will not display in headless-only environments.
