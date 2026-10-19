#  Capacitated Multi-Goal Multi-Agent Pathfinding (C-MG-MAPF) with Bi-Level Optimization & Large Physical Footprints

[![C++17](https://img.shields.io/badge/C%2B%2B-17-blue.svg?style=flat&logo=c%2B%2B)](https://en.cppreference.com/w/cpp/17)
[![Boost](https://img.shields.io/badge/Boost-1.74%2B-orange.svg?style=flat&logo=boost)](https://www.boost.org/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green.svg?style=flat&logo=python)](https://www.python.org/)
[![MILP](https://img.shields.io/badge/Solver-COIN--OR%20CBC-red.svg?style=flat)](https://github.com/coin-or/Cbc)

An enterprise-grade, high-throughput autonomous mobile robot (AGV) fleet routing engine designed for industrial fulfillment centers (e.g., Amazon Kiva, Ocado, Alibaba). 

This system resolves the fundamental gap between academic **Multi-Agent Path Finding (MAPF)** and physical industrial robotics by jointly optimizing **capacitated multi-goal sequencing (Travelling Repairman Problem)**, **finite task dwell times**, and **continuous large physical chassis footprints (5-cell safety buffers & swept turning kinematics)** under strict real-time deadlines.

---

## Visual Demonstration

<div align="center">
  <img src="kiva_simulation_demo_30s.gif" width="100%" alt="28-Robot Kiva Fleet Simulation Demo" />
  <p><em>Real-time visualization of 28 Autonomous Guided Vehicles (AGVs) navigating a 4-zone partitioned warehouse (57×39 grid, 512 storage endpoints) executing multi-bin order picks with continuous 5-cell collision buffers and zero deadlocks.</em></p>
</div>

---

## System Architecture

The framework employs a decoupled **Bi-Level Optimization Hierarchy** running inside a **Rolling-Horizon Collision Resolution (RHCR)** engine. It resolves dynamic order streams by decomposing the NP-hard joint problem into sequencing and spatial-temporal routing:

```
                            Dynamic Order Inflow & Outbound Bin Requests
                                                 │
                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ LEVEL 1: CAPACITATED GOAL SEQUENCING (Travelling Repairman Problem)                             │
│                                                                                                 │
│  • High-Level Goal Bundling: Up to C = 7 bins per AGV sortie                                    │
│  • Real-Time Heuristic: Space-Time 2-Opt with Dynamic Route Wait Projection (<0.20 ms)          │
│  • Exact Mathematical Benchmark: MTZ-MILP Formulation solved via COIN-OR CBC (PuLP)             │
│  • Performance: 95.44% Optimality Ratio with a >220x Algorithmic Speedup                       │
└───────────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                                │ Optimal Goal Trajectory Sequences
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ LEVEL 2: MULTI-AGENT SPACE-TIME FLEET ROUTING (Conflict-Free Navigation)                       │
│                                                                                                 │
│  • Rolling-Horizon Collision Resolution (RHCR): Windowed lookahead (w = 10–20, h = 5)           │
│  • High-Level MAPF Solver: Priority-Based Search (PBS) over Directed Acyclic Graphs (DAGs)      │
│  • Priority Cycle Prevention: Boost Graph DFS reachability checks eliminate deadlocks instantly  │
│  • Low-Level Single-Agent Planner: Focal Safe-Interval Path Planning (Focal-SIPP)               │
│  • Data Structures: Dual Boost Fibonacci Min-Heaps (OPEN / FOCAL) with O(1) decrease-key        │
└───────────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                                │ Collision-Free Path Segments
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ PHYSICAL HARDWARE & KINEMATICS SAFETY LAYER                                                     │
│                                                                                                 │
│  • Chassis Geometry: Real 3×1 chassis envelope verified via swept-area rotation checks          │
│  • Dynamic Reservation Table: Space-Time Constraint Table (CT), Safe Interval Table (SIT), and  │
│    Conflict Avoidance Table (CAT) maintaining continuous 5-cell safety buffers                  │
│  • Dwell Management: Enforces task_delay (e.g., 7 timesteps) for physical shelf pod lifting     │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

<div align="center">
  <img src="system_architecture_diagram.png" width="95%" alt="Bi-Level Optimization Architecture" />
</div>

---

## Key Technical Innovations

### 1. Space-Time 2-Opt vs. Exact MTZ-MILP (Level 1)
In capacitated fulfillment centers, each robot carries a bundle of bins ($C \le 7$). Minimizing the arrival latency at each station requires solving the **Travelling Repairman Problem (TRP / Cumulative TSP)**:
$$\min \sum_{j=1}^{C} T_j$$

* **Exact MTZ-MILP Benchmark:** Modeled using Miller-Tucker-Zemlin subtour elimination constraints and Big-$M$ linearization. Formulated in Python PuLP and solved to global optimality with **COIN-OR CBC**.
* **Space-Time 2-Opt Heuristic:** Runs in $\mathcal{O}(N^2)$ inside the C++ runtime. Evaluates sequence reversals $[i \dots j]$ using a forward cost projection function (`get_projected_route_wait_time`). If an upstream robot is performing a shelf dwell, 2-Opt dynamically pivots the active goal to an unblocked aisle.
* **Empirical Validation:** Proved an average **95.44% optimality match** against exact MILP while reducing solver latency from **44.65 ms to <0.20 ms (>220x speedup)**, fitting comfortably within hard 1-second real-time planning windows.

### 2. Priority-Based Search (PBS) with DAG Cycle Detection (Level 2)
Instead of maintaining an exponential Conflict-Based Search (CBS) constraint tree, the system dynamically assigns priorities between conflicting robots ($A_1 \prec A_2$ vs $A_2 \prec A_1$):
* **Topological Cycle Prevention:** A dedicated `PriorityGraph` backed by **Boost Graph Library (BGL)** enforces acyclicity. Before evaluating a branch, DFS reachability checks verify whether $A_2 \rightsquigarrow A_1$ already exists. Invalid cycles are pruned in $\mathcal{O}(V + E)$ without invoking path planning.
* **Minimal Replanning:** Lower-priority agents replan using `find_consistent_paths` only when affected by high-priority trajectories.

### 3. Focal Safe-Interval Path Planning (Focal-SIPP)
Unlike standard Time-Space A* which ticks discrete seconds $t = 1, 2, 3 \dots$ and explodes exponentially during long wait times, **SIPP groups contiguous collision-free timesteps into Safe Intervals** $[t_{\min}, t_{\max})$:
* **State Representation:** State is defined as $(u, \theta, [t_{\min}, t_{\max}), goal\_id)$, collapsing seconds of waiting into single interval transitions.
* **Dual Boost Fibonacci Heaps:**
  * `OPEN list`: Min-heap keyed on $f = g + h$ to track theoretical lower bounds.
  * `FOCAL list`: Contains all nodes within $f \le \min(f) \times 1.2$ (or $\min(f) + 5$). Sorted purely by **minimal soft conflicts** tracked in the Conflict Avoidance Table (CAT). SIPP proactively takes 1-step detours to prevent fleet-wide replanning cascades.

### 4. Continuous 5-Cell Safety Buffer & Chassis Kinematics
Single-cell point-robot models cause catastrophic physical collisions in real warehouses:
* **Physical Buffer:** During motion and stationary dwells, the `ReservationTable` reserves the central cell plus all 4 orthogonal surrounding cells (`get_5cell_occupied_cells`), guaranteeing clearance against rack overhangs and chassis corners.
* **Swept Area Rotations:** Explicitly verifies intermediate 90° and 180° rotations (`valid_3cell_rotation`) to ensure pivoting chassis do not collide with adjacent shelving racks.

---

## Benchmark Results

Extensive benchmarks across dense 4-zone Kiva warehouse layouts (57×39 grid, 28 robots, 512 endpoints, 5000 simulation timesteps):

| Metric | Baseline RHCR (Single-Goal) | Capacitated Multi-Goal (Our Bi-Level Architecture) | Performance Delta |
| :--- | :---: | :---: | :---: |
| **Outbound Order Throughput** | 142 tasks / k-ticks | **418 tasks / k-ticks** | **+194.3% Throughput** |
| **Order Sequencing Latency** | N/A (FIFO Queue) | **< 0.20 ms (Space-Time 2-Opt)** | Real-time bound satisfied |
| **2-Opt vs. Exact MILP Optimality** | N/A | **95.44% of Global Optimum** | Near-optimal tour efficiency |
| **Algorithmic Speedup vs. MILP** | N/A | **> 220x Faster** | 0.20 ms vs 44.65 ms |
| **Collision / Deadlock Rate** | 0 (Point Model) | **0 (Physical 5-Cell Chassis Enforced)** | 100% Kinematic Safety |
| **PBS High-Level Search Time** | 12.4 ms / window | **3.8 ms / window** | 3.2x faster convergence via FOCAL |

---

## Repository Structure

```
.
├── RHCR-master/                      # Core C++17 Fleet Routing Engine
│   ├── src/
│   │   ├── PBS.cpp                   # Priority-Based Search high-level solver & DAG logic
│   │   ├── SIPP.cpp                  # Focal Safe-Interval Path Planning low-level solver
│   │   ├── ReservationTable.cpp      # Constraint Table (CT), SIT & 5-cell buffer manager
│   │   ├── KivaSystem.cpp            # Kiva warehouse lifelong simulation engine & metrics
│   │   ├── BasicSystem.cpp           # Windowed execution, move(), and task dwell handler
│   │   └── MultiGoalSIPPAdapter.cpp  # Adapter bridging multi-goal sequences to SIPP
│   ├── inc/                          # C++ Header declarations
│   │   ├── SIPP.h                    # SIPPNode definition, Hasher, and Fibonacci heaps
│   │   ├── PBS.h                     # High-level search tree & priority graph structures
│   │   └── ReservationTable.h        # Continuous space-time reservation tables
│   ├── exp/                          # Benchmark trajectory outputs & experimental runs
│   ├── maps/                         # Warehouse floor plans (.map format)
│   │   └── kiva_4zone_shaved.map     # 57x39 4-zone partitioned industrial layout
│   ├── mapf_visualizer.py            # High-performance Pygame/Matplotlib simulation visualizer
│   ├── solve_exact_milp.py           # Mathematical MTZ-MILP solver using PuLP + COIN-OR CBC
│   └── CMakeLists.txt                # CMake build configuration
├── system_architecture_diagram.png   # High-resolution architectural diagram
├── kiva_simulation_demo_30s.gif      # 30-second studio demonstration animation
├── CAPACITATED_MAPF_MASTER_MANUAL.pdf# 14-page comprehensive reference & interview manual
└── README.md                         # Project documentation
```

---

## Quickstart & Reproduction Guide

### Prerequisites
* **C++ Compiler:** GCC 9+ / Clang 10+ / MSVC 2019+ supporting C++17.
* **Build System:** CMake (v3.16+)
* **Libraries:** [Boost C++ Libraries](https://www.boost.org/) (v1.71+)
* **Python Environment:** Python 3.8+ with `matplotlib`, `numpy`, and `Pillow`.

### 1. Build the C++ Simulation Engine
```bash
cd RHCR-master
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release
```

### 2. Run Lifelong Simulation Benchmark
Execute the 28-robot capacitated multi-goal outbound benchmark on the 4-zone warehouse map:
```bash
.\build\Release\lifelong.exe --scenario KIVA `
  --map kiva_4zone_shaved.map `
  --agentNum 28 `
  --solver PBS `
  --simulation_time 750 `
  --simulation_window 5 `
  --planning_window 20 `
  --rotation 1 `
  --cutoffTime 60 `
  --task_delay 7 `
  --capacity_mode 1 `
  --capacity 7 `
  --safety_mode 1 `
  --reorder_mode 2 `
  --seed 0 `
  --output .\exp\bench_outbound_39row.2
```

### 3. Launch the Fleet Visualizer
To inspect robot trajectories, zone handoffs, shelf dwells, and collision envelopes:
```bash
python mapf_visualizer.py exp/bench_outbound_39row.2/paths.txt kiva_4zone_shaved.map
```

---

## Citation & Academic Lineage

This implementation builds upon and significantly extends the foundational research on lifelong Multi-Agent Path Finding:

* **RHCR Foundation:** Li et al., *"Lifelong Multi-Agent Path Finding in Large-Scale Warehouses"*, **AAAI 2021** / **AAMAS 2020**.
* **PBS Foundation:** Ma et al., *"Priority-Based Search for Multi-Agent Path Finding"*, **AIJ 2019**.
* **SIPP Foundation:** Phillips & Likhachev, *"SIPP: Safe Interval Path Planning for Dynamic Environments"*, **ICRA 2011**.

---

