"""
MAPF Web App - Flask backend
Runs lifelong.exe with 3-cell physical rotation, PBS+SIPP, and space-time reordering.
"""
import os, json, time, subprocess
from flask import Flask, request, jsonify, send_from_directory

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # RHCR-master/
EXE  = os.path.join(BASE, "build", "lifelong.exe")

app = Flask(__name__, static_folder="static")

ALGO_NAMES = {0: "FIFO", 1: "Nearest-Neighbour", 2: "Space-Time 2-Opt", 3: "Held-Karp"}
MAP_FILES  = ["kiva_4zone_shaved.map", "kiva_shaved.map", "kiva.map"]


# ── helpers ──────────────────────────────────────────────────────────────

def parse_paths(paths_file, grid_width):
    """Parse paths.txt → {num_agents, agents: {str(a): [{x, y, o}, ...]}}"""
    with open(paths_file) as f:
        lines = f.read().splitlines()
    num_agents = int(lines[0])
    agents = {}
    for a in range(num_agents):
        raw = lines[a + 1]
        steps = []
        for token in raw.split(";"):
            token = token.strip()
            if not token:
                continue
            parts = token.split(",")
            loc_id = int(parts[0])
            orient = int(parts[1]) if len(parts) > 1 else -1
            x = loc_id % grid_width
            y = loc_id // grid_width
            steps.append({"x": x, "y": y, "o": orient})
        agents[str(a)] = steps
    return {"num_agents": num_agents, "agents": agents}


def parse_tasks(tasks_file, grid_width):
    """Parse tasks.txt → {str(a): [{loc, x, y, finish_time}, ...]}"""
    tasks = {}
    if not os.path.exists(tasks_file):
        return tasks
    try:
        with open(tasks_file) as f:
            lines = f.read().splitlines()
        if not lines:
            return tasks
        num_agents = int(lines[0].strip())
        for idx in range(num_agents):
            if idx + 1 < len(lines):
                line = lines[idx + 1].strip()
                if not line:
                    continue
                parts = line.split(" ")
                agent_id = str(parts[0])
                task_tokens = parts[1].split(";")
                agent_tasks = []
                for tok in task_tokens:
                    if not tok.strip():
                        continue
                    subparts = tok.split(",")
                    if len(subparts) >= 2:
                        loc = int(subparts[0])
                        finish_time = int(subparts[1])
                        agent_tasks.append({
                            "loc": loc,
                            "x": loc % grid_width,
                            "y": loc // grid_width,
                            "finish_time": finish_time
                        })
                tasks[agent_id] = agent_tasks
    except Exception as e:
        print(f"Error parsing tasks: {e}")
    return tasks


def parse_map(map_file):
    """Parse a .map file → {H, W, grid: [[int]]}"""
    with open(map_file) as f:
        lines = f.read().splitlines()
    rows, cols = int(lines[0].split(",")[0]), int(lines[0].split(",")[1])
    MAP_START = 4
    grid = []
    for r in range(rows):
        row_str = lines[MAP_START + r]
        row = []
        for ch in row_str:
            if ch == ".":
                row.append(0)   # aisle
            elif ch == "@":
                row.append(1)   # shelf / obstacle
            elif ch == "e":
                row.append(2)   # endpoint / station
            else:
                row.append(0)
        while len(row) < cols:
            row.append(0)
        grid.append(row[:cols])
    return {"H": rows, "W": cols, "grid": grid}


def count_tasks(tasks_file):
    """Count total tasks from tasks.txt"""
    try:
        with open(tasks_file) as f:
            lines = f.read().splitlines()
        total = 0
        for line in lines[1:]:
            parts = line.strip().split(" ", 1)
            if len(parts) < 2:
                continue
            tasks = [t for t in parts[1].split(";") if t.strip()]
            total += len(tasks)
        return total
    except Exception:
        return 0


# ── routes ───────────────────────────────────────────────────────────────

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    return send_from_directory(os.path.dirname(__file__), "index.html")


@app.route("/run", methods=["POST"])
def run_sim():
    data       = request.json or {}
    map_name   = data.get("map", "kiva_4zone_shaved.map")
    agents     = int(data.get("agents", 8))
    algo       = int(data.get("algorithm", 2))
    sim_time   = int(data.get("sim_time", 300))
    rotation   = int(data.get("rotation", 1))
    capacity   = int(data.get("capacity", 7))

    # Safety clamps
    agents   = max(1, min(agents, 50))
    sim_time = max(50, min(sim_time, 2000))
    if map_name not in MAP_FILES:
        return jsonify({"error": "Invalid map name"}), 400

    run_id  = str(int(time.time() * 1000))
    out_dir = os.path.join(BASE, "exp", f"web_{run_id}")
    os.makedirs(out_dir, exist_ok=True)

    map_path = os.path.join(BASE, map_name)

    cmd = [
        EXE,
        "--scenario",         "KIVA",
        "--map",              map_path,
        "--agentNum",         str(agents),
        "-o",                 out_dir,
        "--simulation_time",  str(sim_time),
        "--cutoffTime",       "120",
        "--reorder_mode",     str(algo),
        "--rotation",         str(rotation),
        "--prioritize_start", "1",
        "--capacity",         str(capacity),
        "--task_delay",       "7",
        "--safety_mode",      "1",
        "--capacity_mode",    "1",
        "--solver",           "PBS",
        "--single_agent_solver", "SIPP",
        "--planning_window",  "20",
        "--simulation_window","5",
        "-s",                 "1",
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=BASE,
            capture_output=True,
            text=True,
            timeout=240,
        )
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Simulation timed out (>240s). Try fewer agents or timesteps."}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if result.returncode != 0 and "Total tasks completed" not in result.stdout:
        return jsonify({
            "error": "lifelong.exe failed",
            "stderr": result.stderr[-800:],
            "stdout": result.stdout[-800:],
        }), 500

    paths_file = os.path.join(out_dir, "paths.txt")
    tasks_file = os.path.join(out_dir, "tasks.txt")
    map_file   = os.path.join(BASE, map_name)

    if not os.path.exists(paths_file):
        return jsonify({"error": "paths.txt not found after run", "stdout": result.stdout[-500:]}), 500

    map_data   = parse_map(map_file)
    paths_data = parse_paths(paths_file, map_data["W"])
    tasks_data = parse_tasks(tasks_file, map_data["W"])
    tasks_done = count_tasks(tasks_file)

    throughput = None
    for line in result.stdout.splitlines():
        if "Average throughput" in line:
            try:
                throughput = float(line.split(":")[1].strip().split()[0])
            except Exception:
                pass

    return jsonify({
        "paths":     paths_data,
        "tasks":     tasks_data,
        "map":       map_data,
        "stats": {
            "tasks_completed": tasks_done,
            "throughput":      throughput,
            "agents":          agents,
            "sim_time":        sim_time,
            "algorithm":       ALGO_NAMES.get(algo, "Custom"),
            "map":             map_name,
            "rotation":        bool(rotation),
            "capacity":        capacity,
        },
    })


if __name__ == "__main__":
    print("=" * 55)
    print("  MAPF Web Visualizer (Rotation + Space-Time 2-Opt)")
    print("  Open: http://localhost:5000")
    print("=" * 55)
    app.run(debug=False, port=5000)
