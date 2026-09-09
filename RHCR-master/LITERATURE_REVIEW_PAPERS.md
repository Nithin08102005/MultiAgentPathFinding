# Literature Review: Multi-Goal & Capacitated MAPF / MAPD

A detailed summary and technical breakdown of the 4 benchmark journal and conference papers provided as references for our warehouse research.

---

## Quick Reference Summary Table

| # | Paper Title | Authors & Venue | Core Contribution | Key Algorithm | Relevance to Our Project |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **1** | **Integrated Task Assignment & Path Planning for Capacitated MAPD** | Chen et al. (*IEEE RA-L 2021*) | Coupled task assignment with real delivery costs for multi-capacity robots. | Marginal-Cost Assignment (MCA) + LNS | Highlights why static distance estimates fail in multi-capacity warehouse routing. |
| **2** | **Multi-Goal MAPF via Decoupled & Integrated Goal Vertex Ordering** | Pavel Surynek (*AAAI 2021*) | Formulated Multi-Goal MAPF (MG-MAPF) as a Hamiltonian Path / TSP search. | Hamiltonian-CBS (HCBS) & SMT-HCBS | Establishes the decoupled bi-level hierarchy (TSP goal sequencing + MAPF path planning). |
| **3** | **Dynamic Path Finding for Multi-Load Agent Pickup & Delivery** | Li et al. (*Theor. Comput. Sci. 2025*) | Proved NP-hardness of Multi-Load MAPD (MLAPD); formulated Min-Cost Max-Flow. | Cost-Based Task Assignment (CBTA) + Dynamic A* | Formal proof that exact single-stage MILP cannot scale in real-time online warehouses. |
| **4** | **Task Assignment Strategies for Capacitated Agents in Lifelong MAPD** | Çilden & Polat (*Knowl.-Based Syst. 2025*) | Waypoint sequencing heuristics for multi-capacity agents in lifelong operations. | Token Passing with Multiple Capacity (TPMC) | Demonstrates how intelligent multi-waypoint insertion improves lifelong throughput. |

---

# Paper 1: Integrated Task Assignment and Path Planning for Capacitated Multi-Agent Pickup and Delivery

* **Authors:** Zhe Chen, Javier Alonso-Mora, Xiaoshan Bai, Daniel D. Harabor, Peter J. Stuckey
* **Published in:** *IEEE Robotics and Automation Letters (RA-L)*, Vol. 6, No. 3, July 2021
* **Institutions:** Monash University (Australia), TU Delft (Netherlands), Shenzhen University (China)

### 1. Core Problem Addressed
Traditional Multi-Agent Pickup and Delivery (MAPD) solvers operate sequentially in two disjoint stages:
1. First, assign tasks using lower-bound estimates (e.g., Manhattan distance).
2. Second, compute collision-free paths using Multi-Agent Path Finding (MAPF).

**The Fatal Flaw:** The initial task assignment ignores multi-robot traffic congestion. A task that appeared "close" on paper causes massive traffic jams, making the true coordination cost far higher than estimated.

### 2. Key Contributions & Methodology
* **Coupled Assignment & Planning:** Proposed the **Marginal-Cost Assignment (MCA)** heuristic, where task assignment decisions are evaluated using the *actual coordinated delivery cost* computed by a prioritized planner.
* **Large Neighborhood Search (LNS):** An anytime meta-heuristic that iteratively destroys and repairs subsets of assignments to escape local optima.
* **Multi-Task Capacity Extension ($C > 1$):** Generalized MAPD from single-item robots ($C=1$) to multi-capacity robots that hold multiple items simultaneously.

### 3. Mathematical Formulation Snippet
* **Objective:** Minimize Total Travel Delay (TTD):
  $$\min \text{TTD} = \sum_{i \in \mathcal{P}} \left( a(g_i) - r_i - t(s_i, g_i) \right)$$
  where $a(g_i)$ is arrival time at delivery point $g_i$, $r_i$ is task release time, and $t(s_i, g_i)$ is shortest unobstructed transit time.
* **Key Constraints:** Multi-capacity limit $n_k(t) \le C$, precedence constraints ($s_i$ visited before $g_i$), and spatial non-collision between robots.

### 4. Limitations & Gaps
* Used simple prioritized planning (fixed priority order), which can suffer from priority deadlocks in high-density corridors.
* Evaluates task insertions sequentially, which becomes computationally heavy for large capacity queues ($C \ge 7$).

### 5. How Our Project Connects & Improves
* **Our Project** uses a **2-Opt Local Search Optimizer** combined with **Exact Footprint Clearance Time Calculations** and **Priority-Based Search (PBS)**, allowing $C=7$ capacity queues to be optimized in $< 0.2$ ms without priority deadlocks.

---

# Paper 2: Multi-Goal Multi-Agent Path Finding via Decoupled and Integrated Goal Vertex Ordering

* **Author:** Pavel Surynek
* **Published in:** *AAAI Conference on Artificial Intelligence (AAAI-21)*, Vol. 35, No. 14, 2021
* **Institution:** Czech Technical University in Prague

### 1. Core Problem Addressed
Standard MAPF assigns each agent a single destination vertex. However, in real-world automated logistics and maintenance, an agent is assigned a **set of multiple goals** and must visit all of them in the most efficient sequence.

### 2. Key Contributions & Methodology
* **Defined MG-MAPF (Multi-Goal MAPF):** Formally unified Multi-Agent Path Finding with the Traveling Salesperson Problem (TSP) / Hamiltonian Path.
* **Hamiltonian-CBS (HCBS):** A 3-level search algorithm:
  1. *High Level:* CBS conflict tree resolving collisions between agents.
  2. *Mid Level:* Permutation search finding the optimal ordering of goal vertices per agent using an A* search guided by a **Minimum Spanning Tree (MST)** heuristic.
  3. *Low Level:* Standard A* finding shortest paths between consecutive goal vertices.
* **SMT-HCBS:** A compilation-based solver using Satisfiability Modulo Theories (SMT) and Multi-Valued Decision Diagrams (MDD) to solve goal ordering and path planning simultaneously.

### 3. Mathematical Formulation Snippet
* **Objective:** Minimize Sum-of-Costs (SoC) across all agents visiting their goal subsets $g(a_i)$:
  $$\min \text{SoC} = \sum_{i=1}^k \text{Cost}(a_i)$$
  $$\text{Cost}(a_i) = \min \{ t_c \mid \forall v_g \in g(a_i), \; \exists t \le t_c : s_t(a_i) = v_g \}$$

### 4. Limitations & Gaps
* **High Theoretical Complexity:** Because each node in the CBS high-level search triggers an exponential Hamiltonian path search, HCBS struggles to scale beyond small maps and small agent counts (fails for $> 16$ agents or $> 8$ goals per agent).
* Offline formulation that is not easily adapted to continuous, lifelong rolling-horizon execution.

### 5. How Our Project Connects & Improves
* We adopt Surynek's decoupled goal-ordering insight, but replace the expensive exact search with **Fast 2-Opt Local Search ($O(N^2)$)** operating inside a **Rolling-Horizon (RHCR)** window, enabling real-time execution on 16 agents with 512 endpoints.

---

# Paper 3: Dynamic Path Finding for Multi-Load Agent Pickup and Delivery Problem

* **Authors:** Yifei Li, Ruixi Huang, Hao Ye, Hejiao Huang, Hongwei Du
* **Published in:** *Theoretical Computer Science (TCS)*, Vol. 1023, 2025 (Elsevier)
* **Institution:** Harbin Institute of Technology (Shenzhen), China

### 1. Core Problem Addressed
Commercial warehouse operators (Amazon, Cainiao, JD) increasingly deploy **multi-load agents** (robots carrying multiple bins). Existing single-load MAPD algorithms cannot handle multi-load scheduling, while existing multi-load algorithms plan paths sequentially with greedy A*, causing severe congestion.

### 2. Key Contributions & Methodology
* **NP-Hardness & Competitive Hardness Proofs:** Proved that Multi-Load MAPD (MLAPD) is strongly NP-hard via reduction from the Capacitated Vehicle Routing Problem (CVRP).
* **Cost-Based Task Assignment (CBTA):** Formulated online task assignment as a **Min-Cost Max-Flow (MCMF)** network optimization problem.
* **Dynamic Path Finding:** Deployed real-time conflict-avoidance strategies to dynamically update multi-load schedules as new online tasks arrive.

### 3. Mathematical Formulation Snippet
* **Objective:** Minimize total cost combining travel distance and delivery deadline delay:
  $$\min C(V, \Gamma) = \sum_{v \in V} \sum_{\tau \in \Gamma} \left[ \alpha \cdot \max(t_v^\tau - t_\tau, 0) + \beta \cdot t(v, \tau) \right]$$
  where $\alpha + \beta = 1$, $t_\tau$ is deadline, and $t(v, \tau)$ is travel distance.

### 4. Limitations & Gaps
* Relies on Min-Cost Max-Flow for task matching, which assumes linear edge costs and cannot fully model multi-robot physical footprint chassis overlaps (5-cell bodies) or rotational delays.

### 5. How Our Project Connects & Improves
* We incorporate exact **5-cell physical footprint geometry** and **in-place $90^\circ$ rotational kinematics**, ensuring plans are physically executable on actual Kiva drive hardware without chassis clipping.

---

# Paper 4: Task Assignment Strategies for Capacitated Agents in Lifelong Pickup and Delivery Tasks

* **Authors:** Evren Çilden, Faruk Polat
* **Published in:** *Knowledge-Based Systems*, Vol. 329, August 2025 (Elsevier)
* **Institution:** Middle East Technical University (METU), Ankara, Turkey

### 1. Core Problem Addressed
Investigates how capacitated agents operating in lifelong warehouse environments should choose their next tasks from an available task pool and order their intermediate waypoints (pickup and drop-off locations).

### 2. Key Contributions & Methodology
* **Token Passing with Multiple Capacity (TPMC):** Extended the classical Token Passing (TP) algorithm to multi-capacity agents.
* **Comparative Evaluation of 3 Task Selection Heuristics:**
  1. *Closeness Centrality:* Evaluates proximity of tasks to the overall warehouse topology (found to perform poorly).
  2. *Average Hausdorff Distance:* Measures spatial distance between the robot's current waypoint set and a new candidate task's endpoints (effective for high capacity).
  3. *Cost-Based Estimation (CBE):* Calculates the marginal insertion cost of adding new waypoints into the agent's existing route (achieved the best performance).

### 3. Mathematical Formulation Snippet
* Evaluated makespan and average task service time across lifelong horizons up to thousands of timesteps.
* Enforced waypoint precedence: For any task $\tau$, its pickup waypoint $l_p^\tau$ must strictly precede its delivery waypoint $l_d^\tau$ in the agent's scheduled sequence.

### 4. Limitations & Gaps
* TPMC relies on token-passing reservation tables, which can cause long wait times when multiple agents compete for shared narrow corridors.
* Assumes point-mass robots without rotational delays or dwell times.

### 5. How Our Project Connects & Improves
* We integrate **7-second pick dwell times (`task_delay 7`)**, **5-cell spatial footprints**, and **Priority-Based Search (PBS)** with dynamic 2-Opt edge inversions, achieving **832 tasks / 1000s** throughput.

---

## Synthesis: How Our Project Builds the Ideal Architecture

By studying these 4 papers, we see that modern multi-agent warehousing requires solving three fundamental challenges:

1. **Multi-Task Capacity Optimization:** Addressed in Papers 1, 3, and 4 (proven NP-hard in Paper 3).
2. **Decoupled Goal Sequencing vs. Collision Avoidance:** Addressed in Paper 2.
3. **Coupled Feedback with Real Trajectory Costs:** Addressed in Paper 1 and Paper 4.

### Our Project's Unique Synthesis:
* **Upper Level:** Fast $O(N^2)$ **Space-Time 2-Opt** with exact clearance wait times (solves the TSP challenge from Paper 2 in $< 0.2$ ms).
* **Lower Level:** **Rolling-Horizon PBS + SIPP** on 5-cell physical chassis footprints (solves the multi-agent coordination challenge from Paper 1 & 3).
* **Feedback Coupling:** Real-time clearance timestamps dynamically guide goal re-ordering, preventing corridor traffic jams and achieving peak throughput (**832 tasks, +58.8% over FIFO**).
