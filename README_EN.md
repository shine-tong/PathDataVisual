# PathDataVisual

Visualization toolkit for 6-axis robot arm trajectory data using `matplotlib`.

Features:
- Static trajectory plots (PNG)
- Animated trajectory export (GIF)
- Interactive player (play/pause + draggable cursor)

## 1. Project Structure

```text
PathDataVisual/
├─ data/
│  └─ message.json
├─ scripts/
│  ├─ plot_six_axis.py       # static plots (generates rad/deg by default)
│  ├─ animate_six_axis.py    # GIF animation (generates rad/deg by default)
│  └─ player_six_axis.py     # interactive player
└─ outputs/                  # generated output files
```

## 2. Input Data Format

Required JSON fields:
- `positions`: `N x 6` list, six joint values per sample
- `flags`: stage label list with length `N` (aligned with `positions`)

Example:

```json
{
  "positions": [[...6 values...], [...]],
  "flags": ["during-p", "start", "during-l", "end", "go-home"],
  "weld_order": [1],
  "failed": []
}
```

## 3. Requirements

- Python 3.8+
- Packages:
  - `matplotlib`
  - `pillow` (required for GIF export)

Install:

```bash
pip install -r requirements.txt
```

## 4. Usage

### 4.1 Static PNG

```bash
python scripts/plot_six_axis.py
```

Default outputs:
- `outputs/manipulator_positions.png` (rad)
- `outputs/manipulator_positions_deg.png` (deg)

Options:

```bash
python scripts/plot_six_axis.py --input data/message.json --output outputs/manipulator_positions.png --unit rad|deg|both --show
```

### 4.2 Animated GIF

```bash
python scripts/animate_six_axis.py
```

Default outputs:
- `outputs/six_axis_animation.gif` (rad)
- `outputs/six_axis_animation_deg.gif` (deg)

Options:

```bash
python scripts/animate_six_axis.py --input data/message.json --output outputs/six_axis_animation.gif --unit rad|deg|both --fps 20
```

### 4.3 Interactive Player

```bash
python scripts/player_six_axis.py
```

Options:

```bash
python scripts/player_six_axis.py --input data/message.json --unit rad|deg --fps 20
```

Controls:
- `Play/Pause` button for auto-play
- Drag the vertical cursor in subplots to inspect points
- Use the bottom `Index` slider for precise positioning

## 5. Notes

- Stage background color mapping in GIF is aligned with PNG style.
- `start` is marked with green points, `end` with red points.

## 6. Troubleshooting

- No output file:
  - run commands in project root
  - verify `data/message.json` exists and is valid
- Slow GIF export:
  - reduce FPS, e.g. `--fps 10`
- Interactive window not showing:
  - run in a desktop GUI environment (not headless shell)