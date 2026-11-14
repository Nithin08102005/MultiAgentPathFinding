# MAPF Kiva Warehouse Web Simulator

Live interactive visualizer for Large Footprint Capacitated MAPF in Kiva Automated Warehouses.
Features Bi-Level PBS+SIPP, physical 3-cell rotations with 90° in-place turning, and Space-Time Fast 2-Opt task reordering (IIT Indore BTP).

---

## 🚀 Quick Start (Windows)

### 1. Requirements
- Python 3.8+
- Install Flask:
  ```bash
  pip install flask
  ```

### 2. Launch
Simply double-click:
```
start_server.bat
```
*(Or from the terminal in the RHCR-master folder: `python web_app\app.py`)*

### 3. Open in Browser
Visit:
```
http://localhost:5000
```

---

## 🎮 Features
- **Map Selection**: Kiva 4-Zone Shaved (35×57), Kiva Shaved, Kiva Full Benchmark.
- **Robot Fleets**: 4, 8, 12, 16, 20, 24 robots.
- **Algorithms**: Space-Time Fast 2-Opt (Novel), FIFO Baseline, Nearest-Neighbour, Held-Karp.
- **Physical 3×1 Rotation**: Live 90° in-place turns with 3-cell physical safety.
- **Live Collision Monitor**: Mathematically verifies 0 footprint overlaps at all timesteps.
- **Timeline Scrubber**: Drag slider to any timestep or step frame-by-frame with Spacebar to Play/Pause.
