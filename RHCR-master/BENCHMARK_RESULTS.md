# Multi-Agent Pathfinding (MAPF) Warehouse Benchmark Results

**Experiment Date:** August 27, 2026  
**Simulation Duration:** 1,000 Timesteps  
**Fleet Size:** 16 Robots  
**Map:** `kiva_4zone_shaved.map` (35x57 Grid, 512 Shelf Endpoints, 4 Zones)  
**Robot Capacity:** 7 Tasks  
**Shelf Pick Dwell Time:** 7 Seconds (`task_delay 7`)  
**Low-Level Solver:** PBS + SIPP (20-step planning window, 5-step execution window)  

---

## 1. Master Evaluation Table

| Config # | Scheduling Algorithm | Goal 1 Policy | Tasks Completed | Throughput (tasks/sec) | Improvement vs FIFO |
| :---: | :--- | :---: | :---: | :---: | :---: |
| **1** | **FIFO Baseline** (Uncoordinated Arrival Order) | None (Raw Order) | **524** | 0.523 | *Baseline (0.0%)* |
| **2** | **Naive Distance TSP** (Static Map Distance) | **Locked $G_1$** | **769** | 0.768 | **+46.8%** |
| **3** | **Space-Time 2-Opt** (Exact Clearance Wait Times) | **Locked $G_1$** | **804** | 0.803 | **+53.4%** |
| **4** | **Naive Distance TSP** (Static Map Distance) | **Dynamic $G_1$** | **823** | 0.822 | **+57.1%** |
| **5** | **Proposed Dynamic Space-Time 2-Opt** (Our Method) | **Dynamic $G_1$** | **832** | **0.831** | **+58.8% (PEAK)** |

---

## 2. Key Findings & Technical Rationale

### 1. Multi-Task Capacity + TSP Re-ordering is Vital (+46.8% Boost)
* **FIFO Baseline:** 524 tasks. Robots follow whatever random sequence the backlog provides, zig-zagging across the warehouse.
* **Naive Distance TSP:** 769 tasks. Organizing the 7-task queue using Nearest-Neighbor + 2-Opt local search groups tasks geographically, eliminating wasted travel distance.

### 2. Space-Time Wait-Time Projection Adds Real Collision Avoidance (+35 Tasks)
* Comparing locked configurations:
  * **Naive Distance (Locked):** 769 tasks
  * **Space-Time 2-Opt (Locked):** 804 tasks (+35 tasks, +4.6% improvement over Naive)
* **Why:** By projecting moving 5-cell robot footprints step-by-step into the 20-step window and computing exact teammate clearance wait times, the system identifies aisle congestion in advance and schedules routes around traffic jams.

### 3. Dynamic Opportunistic Switching Delivers Peak Throughput (832 Tasks, +58.8%)
* **Our Proposed Dynamic ST-TSP:** 832 tasks (Throughput: 0.831 tasks/timestep).
* **Why:** When a robot encounters a teammate actively performing a 7-second pick at its target shelf, the exact clearance wait-time calculation detects the 7-second stall. Rather than standing idle in the hallway waiting for the teammate, the robot dynamically pivots to an adjacent open shelf, completes it, and returns when the original shelf is clear.

---

## 3. Reproduction Commands (PowerShell)

### Config 1: FIFO Baseline (Capacity = 7, Mode 0)
```powershell
Remove-Item -Recurse -Force .\exp\bench_fifo -ErrorAction SilentlyContinue; .\build\Release\lifelong.exe --scenario KIVA --map kiva_4zone_shaved.map --agentNum 16 --solver PBS --simulation_time 1000 --output .\exp\bench_fifo --rotation 1 --cutoffTime 100 --planning_window 20 --task_delay 7 --capacity_mode 1 --capacity 7 --safety_mode 1 --reorder_mode 0 --seed 0
```

### Config 2: Naive Distance TSP Locked (Capacity = 7, Mode 1, Lock 1)
```powershell
Remove-Item -Recurse -Force .\exp\bench_naive_locked -ErrorAction SilentlyContinue; .\build\Release\lifelong.exe --scenario KIVA --map kiva_4zone_shaved.map --agentNum 16 --solver PBS --simulation_time 1000 --output .\exp\bench_naive_locked --rotation 1 --cutoffTime 100 --planning_window 20 --task_delay 7 --capacity_mode 1 --capacity 7 --safety_mode 1 --reorder_mode 1 --lock_active_goal 1 --seed 0
```

### Config 3: Space-Time 2-Opt Locked (Capacity = 7, Mode 2, Lock 1)
```powershell
Remove-Item -Recurse -Force .\exp\bench_st_locked -ErrorAction SilentlyContinue; .\build\Release\lifelong.exe --scenario KIVA --map kiva_4zone_shaved.map --agentNum 16 --solver PBS --simulation_time 1000 --output .\exp\bench_st_locked --rotation 1 --cutoffTime 100 --planning_window 20 --task_delay 7 --capacity_mode 1 --capacity 7 --safety_mode 1 --reorder_mode 2 --lock_active_goal 1 --seed 0
```

### Config 4: Naive Distance TSP Dynamic (Capacity = 7, Mode 1, Lock 0)
```powershell
Remove-Item -Recurse -Force .\exp\bench_naive_dynamic -ErrorAction SilentlyContinue; .\build\Release\lifelong.exe --scenario KIVA --map kiva_4zone_shaved.map --agentNum 16 --solver PBS --simulation_time 1000 --output .\exp\bench_naive_dynamic --rotation 1 --cutoffTime 100 --planning_window 20 --task_delay 7 --capacity_mode 1 --capacity 7 --safety_mode 1 --reorder_mode 1 --lock_active_goal 0 --seed 0
```

### Config 5: Proposed Dynamic Space-Time 2-Opt (Capacity = 7, Mode 2, Lock 0)
```powershell
Remove-Item -Recurse -Force .\exp\bench_st_dynamic -ErrorAction SilentlyContinue; .\build\Release\lifelong.exe --scenario KIVA --map kiva_4zone_shaved.map --agentNum 16 --solver PBS --simulation_time 1000 --output .\exp\bench_st_dynamic --rotation 1 --cutoffTime 100 --planning_window 20 --task_delay 7 --capacity_mode 1 --capacity 7 --safety_mode 1 --reorder_mode 2 --lock_active_goal 0 --seed 0
```

---

## 4. Visualizer Commands

* **To visualize the Peak Winner (Config 5 - 832 tasks):**
  ```powershell
  python mapf_visualizer.py
  ```
* **To visualize FIFO Baseline (Config 1 - 524 tasks):**
  ```powershell
  python mapf_visualizer.py exp/bench_fifo
  ```
* **To visualize Naive Distance Locked (Config 2 - 769 tasks):**
  ```powershell
  python mapf_visualizer.py exp/bench_naive_locked
  ```
* **To visualize Space-Time Locked (Config 3 - 804 tasks):**
  ```powershell
  python mapf_visualizer.py exp/bench_st_locked
  ```
* **To visualize Naive Distance Dynamic (Config 4 - 823 tasks):**
  ```powershell
  python mapf_visualizer.py exp/bench_naive_dynamic
  ```
