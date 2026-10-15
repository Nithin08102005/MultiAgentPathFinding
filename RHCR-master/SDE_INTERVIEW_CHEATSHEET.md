# SDE Interview Cheat Sheet: C++ Fleet Routing & Coordination Engine

> **How to use this guide:**  
> When interviewing for Software Development Engineer (SDE / Backend / Systems / C++) roles, **never talk about abstract academic math or MILP theorems** unless explicitly asked.  
> SDE interviewers care about: **Data Structures, Big-O Complexity, C++ Memory/Performance, Concurrency/IPC, System Architecture, and Real Debugging Stories.**  
> Use this guide to explain your project in pure software engineering terms.

---

## 1. The 30-Second SDE Elevator Pitch

> *"I built a high-performance C++ routing and coordination engine for an autonomous warehouse fleet. Think of it like designing Google Maps or an Uber dispatch engine, but for dozens of autonomous robots operating simultaneously in tight warehouse corridors with zero collisions.*
>
> *Architecturally, it's a bi-level system: a high-level task scheduler that groups and reorders pickup jobs in under 0.2 milliseconds, and a low-level rolling-horizon path planner using custom graph algorithms. I wrote it in C++14 using Boost data structures like Fibonacci heaps and DAGs for cycle detection, cutting dispatch latency by 220x and boosting overall system throughput by 58%."*

---

## 2. Jargon Translator: Academic Terms ➔ SDE Terms

| What the Paper / Code calls it | What to say in an SDE Interview |
| :--- | :--- |
| **Capacitated Multi-Goal MAPF** | **Multi-Agent Fleet Routing & Task Dispatcher** |
| **Mixed-Integer Linear Programming (MILP)** | **Exact combinatorial optimizer (used as a benchmark)** |
| **Space-Time 2-Opt Heuristic** | **Greedy Local Search with Dynamic Caching** |
| **Safe Interval Path Planning (SIPP)** | **Interval-based A\* Graph Search** |
| **Priority-Based Search (PBS)** | **Topological DAG search with Cycle Detection** |
| **Reservation Table** | **Space-Time Hash Table / Collision Lookup Cache** |
| **5-cell / 3-cell footprint** | **Bounding-Box Collision Detection with Buffer Padding** |
| **Task Delay ($\Delta = 7$)** | **Service Dwell Time / Blocking Job Execution** |

---

## 3. Data Structures & Big-O Complexity (What Interviewers Test)

If an interviewer asks: *"What data structures did you use and why?"*, nail these 4:

### 1. Boost Fibonacci Heap (`boost::heap::fibonacci_heap`)
* **Where:** In the low-level A* / SIPP search queue ([inc/SIPP.h](file:///c:/Users/raoni/OneDrive/Desktop/GitHub%20-%20Copy/MAPF-with-multi-level-architecture/RHCR-master/inc/SIPP.h)).
* **SDE Explanation:**
  > *"Standard `std::priority_queue` does not support a `decrease-key` operation. When A* finds a shorter route to an existing node, with `std::priority_queue` you have to re-insert a duplicate node, which wastes memory and forces stale pop operations.  
  > Instead, I used `boost::heap::fibonacci_heap` with persistent **heap handles**. Each search node stores a pointer directly into the heap (`handle_type`). When a cheaper path is found, we call `heap.update(node->handle)` in **$\mathcal{O}(1)$ amortized time** without reallocating."*

### 2. Directed Acyclic Graph (DAG) for Deadlock Resolution
* **Where:** In `PriorityGraph` ([inc/PriorityGraph.h](file:///c:/Users/raoni/OneDrive/Desktop/GitHub%20-%20Copy/MAPF-with-multi-level-architecture/RHCR-master/inc/PriorityGraph.h)).
* **SDE Explanation:**
  > *"When two robots want the same corridor, we assign a priority: Robot A yields to Robot B ($A \prec B$). All priority rules form a directed graph.  
  > Before assigning a priority, we run a **Cycle Detection (DFS / Topological Traversal)**. If adding an edge creates a directed cycle (e.g., $A \prec B \prec C \prec A$), that would create a perpetual deadlock. We prune that branch immediately."*

### 3. Space-Time Reservation Hash Table
* **Where:** In `ReservationTable` ([inc/ReservationTable.h](file:///c:/Users/raoni/OneDrive/Desktop/GitHub%20-%20Copy/MAPF-with-multi-level-architecture/RHCR-master/inc/ReservationTable.h)).
* **SDE Explanation:**
  > *"To check if a cell is free at time $t$, checking all robots' full trajectories would be $\mathcal{O}(M \cdot T)$.  
  > Instead, I used an `unordered_map<int, list<pair<int,int>>>` mapping `Cell_ID -> List of [t_start, t_end]` reserved intervals. Collision checking becomes an $\mathcal{O}(1)$ average hash lookup followed by a quick interval overlap check."*

### 4. 2-Opt Local Search ($O(N^2)$ Array Reversal)
* **Where:** In `reorder_bundle_by_dvs` ([src/KivaSystem.cpp](file:///c:/Users/raoni/OneDrive/Desktop/GitHub%20-%20Copy/MAPF-with-multi-level-architecture/RHCR-master/src/KivaSystem.cpp)).
* **SDE Explanation:**
  > *"To sequence up to 7 pickup goals per robot, brute-force permutation is $7! = 5,040$ operations. Instead, we seed the order using a **Nearest-Neighbor greedy pass** ($\mathcal{O}(N^2)$) and refine it with **2-Opt local search** (reversing sub-segments in an array). It converges in under **0.2 milliseconds** while achieving 95.4% the quality of the exact solver."*

---

## 4. Modern C++ & Systems Concepts (Show You Write Good Code)

### 1. Zero-Copy & Move Semantics (`std::move`)
* In task dispatching ([src/KivaSystem.cpp](file:///c:/Users/raoni/OneDrive/Desktop/GitHub%20-%20Copy/MAPF-with-multi-level-architecture/RHCR-master/src/KivaSystem.cpp#L1425)), after reordering tasks in a local buffer, we transfer ownership back into the agent's queue using `bundle[k] = std::move(reordered);` to avoid deep-copying heap buffers.

### 2. Subprocess IPC via OS Pipes (`_popen`)
* Mode 3 invokes an external Python solver script.
* **How it works:** C++ formats the cost matrix into a command string, opens a read pipe with `FILE* pipe = _popen(cmd.c_str(), "r")`, reads back the space-separated output integers via `fscanf`, and closes the pipe with `_pclose(pipe)`.
* **SDE Talking Point:** *"While this provided a clean IPC prototype to benchmark against exact solvers, in production I would replace pipe IPC with a shared memory buffer or a C++ native binding (like pybind11 or direct C API) to eliminate process-spawning overhead."*

### 3. Memory & Allocation Optimization
* Hot path functions like `get_5cell_occupied_cells` avoid dynamic heap allocation (`new` or `std::vector`). Instead, they pass stack-allocated fixed-size arrays (`int out_cells[5]`) by reference. This avoids triggering `malloc` in the inner search loop millions of times per second.

---

## 5. The "Tough Bug I Debugged" Stories (Gold for SDE Behavioral / Tech Rounds)

Interviewers always ask: *"Tell me about the hardest bug you encountered in this project."*  
Pick any of these 4 real bugs that were identified and fixed:

### Story 1: The "Silent Collision" Iterator Invalidation Bug
* **The Symptom:** Under high robot density, robots were occasionally driving directly through each other without the solver throwing an error.
* **The Root Cause:** In `ReservationTable::updateSIT`, an old cleanup routine called `ct.erase(it)` while updating constraints. This silently deleted active hard collision constraints from the table, rendering subsequent collision lookups blind.
* **The Fix:** Removed the erroneous `ct.erase()`, ensuring hard constraints persist across the entire planning window.
* **SDE Takeaway:** Demonstrates deep understanding of state persistence, hash table lifecycle, and debugging silent data corruption.

### Story 2: The "Ghost State" Copy Constructor Bug
* **The Symptom:** In PBS search branches, robots were stalling at timestep 35 and refusing to move.
* **The Root Cause:** In `ReservationTable::copy()`, the developer omitted copying the boolean flag `prioritize_start`. It defaulted to `false` in child nodes, causing the SIPP search engine to skip valid start states.
* **The Fix:** Updated the copy routine to explicitly preserve all flags (`prioritize_start`, `task_delay`) across node forks.
* **SDE Takeaway:** Classic C++ copy semantics issue—shows vigilance with rule-of-three/five and deep-copy integrity.

### Story 3: The 34-Second Freeze (Search Space Explosion)
* **The Symptom:** Whenever a target shelf was blocked by another robot, the simulation froze for 34+ seconds on a single tick.
* **The Root Cause:** Single-agent SIPP expansion had a hard limit set to 50,000 nodes. When an endpoint was unreachable, the algorithm spent 50,000 futile expansions exploring dead-ends before failing.
* **The Fix:** Profiled the search, reduced the node expansion limit to 3,000 nodes, and added early exit logic with fallback Manhattan heuristic penalties.
* **SDE Takeaway:** Real-world performance profiling, tuning search budgets, preventing Denial-of-Service / CPU thrashing.

### Story 4: The Flaky Non-Deterministic Tie-Breaker
* **The Symptom:** Identical simulation runs with the same random seed were producing different paths, making automated regression tests flaky.
* **The Root Cause:** The search node comparator used `rand() % 2 == 0` to break ties between equal $f$-cost nodes!
* **The Fix:** Replaced random tie-breaking with strict, deterministic multi-level keys: break ties by higher $g$-value (depth), then lower conflicts, then agent ID.
* **SDE Takeaway:** Determinism, reproducibility, writing robust testable code.

---

## 6. Common SDE Interview Questions & Model Answers

### Q1: "Walk me through how your project works from input to output."
**Answer:**
> *"1. **Input:** We load a 2D warehouse grid (walls, travel corridors, shelf bays) and a stream of incoming customer pickup tasks.  
> 2. **High-Level Scheduling:** Each robot holds up to 7 active tasks in a queue. Every time a task completes, our 2-Opt scheduler groups and orders the remaining tasks by physical proximity and projected aisle congestion (<0.2ms).  
> 3. **Low-Level Pathfinding:** We use a rolling planning window of 20 seconds. Individual robots plan collision-free paths using SIPP (Safe Interval Path Planning) over a shared reservation table.  
> 4. **Conflict Resolution:** If two robots want the same cell at the same time, our Priority-Based Search engine builds a dependency DAG to determine who yields first, pruning any deadlocks via cycle detection.  
> 5. **Execution:** Robots execute the first 5 seconds of motion, dock for 7 seconds to complete the pick, and replan."*

### Q2: "Why use C++ instead of Python or Go?"
**Answer:**
> *"Pathfinding on a multi-agent grid requires expanding tens of thousands of graph nodes per second. In Python, object overhead and the Global Interpreter Lock (GIL) make tight graph traversals 50x–100x slower.  
> C++ allows deterministic memory layouts, zero-cost abstractions, stack allocation in tight loops, and direct pointer handles into Fibonacci heaps. This let us keep per-decision planning times under 0.20 milliseconds, which is critical for real-time robotics."*

### Q3: "How would you scale this system from 16 robots to 10,000 robots?"
**Answer:**
> *"Centralized planning doesn't scale to 10,000 robots because joint state spaces grow exponentially. To scale to 10,000 robots, I would:  
> 1. **Spatial Decomposition:** Partition the warehouse into distinct topological zones (like sectors in air-traffic control) with dedicated highway corridors.  
> 2. **Distributed Microservices:** Assign a regional planner service per zone; robots negotiate handoffs at zone boundary intersections via distributed locks or consensus.  
> 3. **One-Way Traffic Rules:** Impose directed edge constraints (one-way aisles) in the map graph to eliminate head-on collisions by design, reducing the conflict graph density by over 80%."*

### Q4: "What is the time complexity of your high-level scheduler?"
**Answer:**
> *"For $N$ tasks in a robot's bundle:  
> - Nearest-Neighbor initialization takes $\mathcal{O}(N^2)$.  
> - Each 2-Opt pass evaluates $\binom{N}{2} = \mathcal{O}(N^2)$ candidate edge swaps.  
> - With a capped limit of 10 passes, the overall complexity is strictly $\mathcal{O}(N^2)$.  
> Since capacity is bounded ($N \le 7$), $N^2 \le 49$ operations, which executes in under 200 microseconds—far faster than exact branch-and-bound solvers which scale as $\mathcal{O}(N!)$."*

---

## 7. SDE Resume Bullet Points (Copy & Paste Ready)

- **High-Performance Fleet Routing Engine (C++14 / Boost):** Engineered a real-time multi-agent routing system for 16 warehouse AGVs across a 512-node topological grid, achieving **+58.8% throughput** (832 tasks completed) over standard baselines.
- **Low-Latency Scheduling & Local Search:** Designed an $\mathcal{O}(N^2)$ 2-Opt local search task scheduler with dynamic congestion caching, cutting decision latency from 44.6ms to **<0.20ms (>220x speedup)** with a 95.4% optimality match against exact solvers.
- **Custom Graph Search & Deadlock Prevention:** Implemented Safe Interval Path Planning (SIPP) and Priority-Based Search (PBS) utilizing `boost::heap::fibonacci_heap` for **$\mathcal{O}(1)$ amortized decrease-key** updates and directed acyclic graphs (DAG) for cycle/deadlock detection.
- **Profiling & Systems Debugging:** Diagnosed and resolved memory corruption in space-time hash tables, eliminated 34-second search-space freezes by tuning expansion thresholds, and enforced deterministic multi-key tie-breaking across simulation runs.
