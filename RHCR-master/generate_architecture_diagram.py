import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Set up figure with extended bottom margin for caption
plt.rcParams['font.family'] = 'DejaVu Sans'
fig, ax = plt.subplots(figsize=(16, 11), dpi=300)
ax.set_xlim(0, 155)
ax.set_ylim(-10, 104)
ax.axis('off')

def draw_card(ax, x, y, w, h, title, items, bg='#ffffff', border='#1e293b', 
              title_color='#0f172a', title_size=10.0, item_size=8.1, 
              highlight_last=False):
    rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.2",
                                  linewidth=1.3, edgecolor=border, facecolor=bg)
    ax.add_patch(rect)
    
    # Title
    ax.text(x + w/2, y + h - 2.8, title, ha='center', va='top', 
            fontsize=title_size, fontweight='bold', color=title_color)
    
    # Divider line
    ax.plot([x + 2.5, x + w - 2.5], [y + h - 5.2, y + h - 5.2], color='#cbd5e1', lw=0.9)
    
    # Items with generous padding
    curr_y = y + h - 7.6
    spacing = 2.6
    for i, item in enumerate(items):
        is_last = (i == len(items) - 1) and highlight_last
        color = '#15803d' if is_last else '#334155'
        weight = 'bold' if is_last else 'normal'
        ax.text(x + 3.0, curr_y, item, ha='left', va='top', 
                fontsize=item_size, color=color, fontweight=weight)
        curr_y -= spacing

# =========================================================================
# 1. TOP BOX: TRAFFIC-AWARE CALIBRATION
# =========================================================================
draw_card(ax, 52, 73, 46, 26,
          title="Traffic-Aware Calibration",
          items=[
              "• NN Forward Timeline Simulation:",
              "   t̂₀ = t_cur",
              "   t̂_{n+1} = t̂_n + d(π_n, π_{n+1}) + w(π_n, π_{n+1}, t̂_n) + δ",
              "• Dynamic Traffic Delay: w(i, j, t̂_i)",
              "• Time-Calibrated Edge Cost: c_ij = d(i, j) + w(i, j, t̂_i) + δ"
          ],
          bg='#f8fafc', border='#334155', title_color='#0f172a', item_size=8.2)

# =========================================================================
# 2. LEFT COLUMN: WAREHOUSE PARAMETERS & ROBOT STATES
# =========================================================================
draw_card(ax, 4, 53, 40, 26,
          title="Warehouse & Fleet Parameters",
          items=[
              "• 4-Zone Topological Map G = (V, E)",
              "• Carrying Capacity: C = 5 tasks / robot",
              "• Planning Window: w = 20, Step Δt",
              "• Task Dwell Service Delay: δ = 4 s",
              "• Kinematic Footprint: 5-cell chassis",
              "• In-Place Rotations: 9-cell swept envelope"
          ],
          bg='#ffffff', border='#1e293b', item_size=8.1)

draw_card(ax, 4, 20, 40, 25,
          title="Robot States (i = 1, ..., M)",
          items=[
              "• Current Pose: s_i(t) = ⟨p_i(t), θ_i(t)⟩",
              "• Active Goal Bundle: G_i = {g₁, ..., g_N}",
              "• Goal Commitment Lock: lock_active_goal",
              "• Space-Time Reservation Table",
              "• Dynamic Refill Queue Status"
          ],
          bg='#ffffff', border='#1e293b', item_size=8.1)

# =========================================================================
# 3. CENTER: UPPER-LEVEL TASK SEQUENCING CORE
# =========================================================================
opt_container = patches.FancyBboxPatch((49, 18), 51, 49, boxstyle="round,pad=0.6,rounding_size=1.8",
                                      linewidth=1.2, edgecolor='#94a3b8', facecolor='#f8fafc', linestyle='--')
ax.add_patch(opt_container)
ax.text(74.5, 64.0, "UPPER-LEVEL TASK SEQUENCING", ha='center', va='top', 
        fontsize=10.0, fontweight='bold', color='#475569')

# Box A: Exact MILP
draw_card(ax, 52, 43.5, 45, 17.5,
          title="Exact MILP-Based TRP (Mode 3)",
          items=[
              "• Objective: Min Cumulative Latency min Σ T_j",
              "• Big-M Subtour Elimination & Time Propagation",
              "• Globally Optimal Delivery Ordering π*"
          ],
          bg='#ffffff', border='#2563eb', title_color='#1d4ed8', item_size=8.2)

# "Or" Divider
ax.text(74.5, 41.5, "— Or —", ha='center', va='center', fontsize=10.0, fontweight='bold', color='#64748b')

# Box B: Space-Time 2-Opt
draw_card(ax, 52, 21.0, 45, 17.5,
          title="Space-Time 2-Opt TSP (Mode 2)",
          items=[
              "• Heuristic Local Search Baseline",
              "• Greedy Nearest-Neighbor (NN) Seeding",
              "• Space-Time Conflict Edge Swaps"
          ],
          bg='#ffffff', border='#475569', title_color='#334155', item_size=8.2)

# =========================================================================
# 4. TASK DISPATCHER (Shifted up to align cleanly with Lower-Level MAPF)
# =========================================================================
disp_rect = patches.FancyBboxPatch((104, 43), 15, 16, boxstyle="round,pad=0.3,rounding_size=1.2",
                                   linewidth=1.3, edgecolor='#1e293b', facecolor='#ffffff')
ax.add_patch(disp_rect)
ax.text(111.5, 54.5, "Task\nDispatcher", ha='center', va='top', fontsize=9.8, fontweight='bold', color='#0f172a')
ax.plot([106, 117], [48.5, 48.5], color='#cbd5e1', lw=0.9)
ax.text(111.5, 46.5, "Sequence π*", ha='center', va='top', fontsize=8.0, color='#64748b')

# =========================================================================
# 5. LOWER-LEVEL MAPF ENGINE
# =========================================================================
draw_card(ax, 124, 43, 27, 28,
          title="LOWER-LEVEL MAPF",
          items=[
              "Rolling-Horizon (RHCR)",
              "• Priority-Based Search (PBS)",
              "• Safe Interval Path Planning",
              "• Swept Rotational Kinematics",
              "• Dynamic Window Restitching",
              "• 100% Conflict-Free Paths"
          ],
          bg='#eff6ff', border='#1d4ed8', title_color='#1e3a8a', title_size=9.5, item_size=8.0)

# =========================================================================
# 6. LAYERED ROBOT EXECUTION FLEET
# =========================================================================
card_m = patches.FancyBboxPatch((128, 16), 24, 21, boxstyle="round,pad=0.3,rounding_size=1.2",
                               linewidth=1.0, edgecolor='#cbd5e1', facecolor='#f8fafc')
ax.add_patch(card_m)
ax.text(140, 35.0, "Robot M", ha='center', va='top', fontsize=8.2, fontweight='bold', color='#94a3b8')

card_2 = patches.FancyBboxPatch((126, 13.5), 24, 21, boxstyle="round,pad=0.3,rounding_size=1.2",
                               linewidth=1.1, edgecolor='#94a3b8', facecolor='#f1f5f9')
ax.add_patch(card_2)
ax.text(138, 32.5, "Robot 2", ha='center', va='top', fontsize=8.2, fontweight='bold', color='#64748b')

draw_card(ax, 124, 11, 24, 21,
          title="Robot 1 (AGV Fleet)",
          items=[
              "• Execute Safe Interval Paths",
              "• Pose Update: ⟨p_i(t), θ_i(t)⟩",
              "• Shelf Picking Dwell (δ)",
              "• Queue Refill on Delivery",
              "★ 524 Tasks (+4.0%)"
          ],
          bg='#ffffff', border='#1e293b', title_color='#0f172a', 
          title_size=9.0, item_size=7.9, highlight_last=True)

# =========================================================================
# ARROWS & CONNECTORS
# =========================================================================
arrow_style = dict(arrowstyle="-|>", color='#111827', lw=1.3, mutation_scale=10)
dashed_arrow = dict(arrowstyle="-|>", color='#2563eb', lw=1.3, linestyle='--', mutation_scale=10)

# Top Calibration -> Optimization Core
ax.plot([75, 75], [73, 68.0], color='#334155', lw=1.2, linestyle=':')
ax.annotate('', xy=(75, 67.5), xytext=(75, 73), arrowprops=dict(arrowstyle="-|>", color='#334155', lw=1.2, linestyle=':', mutation_scale=10))
ax.text(76.5, 70.0, "Calibrated c_ij", fontsize=8.2, fontstyle='italic', color='#475569')

# Left Parameters & States -> Central Core
ax.plot([44, 46.5], [66, 66], color='#111827', lw=1.3)
ax.plot([44, 46.5], [32.5, 32.5], color='#111827', lw=1.3)
ax.plot([46.5, 46.5], [32.5, 66], color='#111827', lw=1.3)
ax.annotate('', xy=(49, 52), xytext=(46.5, 52), arrowprops=arrow_style)
ax.annotate('', xy=(49, 29.5), xytext=(46.5, 29.5), arrowprops=arrow_style)

# Core -> Task Dispatcher
ax.annotate('', xy=(104, 52), xytext=(97, 52), arrowprops=dashed_arrow)
ax.annotate('', xy=(104, 47), xytext=(97, 30), arrowprops=arrow_style)

# Task Dispatcher -> Lower-Level MAPF (Clean level horizontal arrow)
ax.annotate('', xy=(124, 51), xytext=(119, 51), arrowprops=arrow_style)
ax.text(121.5, 52.8, "Order π*", ha='center', va='bottom', fontsize=8.0, fontstyle='italic', color='#1e3a8a')

# Lower-Level MAPF -> Layered Robots
ax.annotate('', xy=(136, 32), xytext=(136, 43), arrowprops=arrow_style)
ax.text(137.5, 37.5, "Collision-Free\nTrajectory", ha='left', va='center', fontsize=8.0, fontweight='bold', color='#1d4ed8')

# =========================================================================
# RECEDING HORIZON FEEDBACK LOOP (PERFECTLY CONNECTED)
# =========================================================================
# Line from bottom of Robot 1 (x=136, y=11) down to y=5.5
ax.plot([136, 136], [11, 5.5], color='#111827', lw=1.3)
# Horizontal line left to feedback banner
ax.plot([136, 97], [5.5, 5.5], color='#111827', lw=1.3)

# Feedback banner
fdbk_patch = patches.FancyBboxPatch((32, 3.5), 65, 4.0, boxstyle="round,pad=0.2,rounding_size=0.8",
                                    linewidth=1.0, edgecolor='#64748b', facecolor='#ffffff')
ax.add_patch(fdbk_patch)
ax.text(64.5, 5.5, "Receding Horizon Loop: Update state & reoptimize at each planning window w",
        ha='center', va='center', fontsize=8.2, fontweight='bold', color='#0f172a')

# Line from left of banner to left column
ax.plot([32, 24], [5.5, 5.5], color='#111827', lw=1.3)
# Upward line into bottom of Robot States box
ax.plot([24, 24], [5.5, 20], color='#111827', lw=1.3)
ax.annotate('', xy=(24, 20), xytext=(24, 5.5), arrowprops=arrow_style)

# =========================================================================
# DEDICATED BOTTOM CAPTION (ZERO OVERLAP)
# =========================================================================
full_caption = (
    "Fig. 1. Proposed Bi-Level Lifelong MAPF Architecture: Real-time inputs (fleet states, goal bundles, map topology) feed into the upper-level\n"
    "task sequencing core (contrasting exact Traffic-Aware MILP against Space-Time 2-Opt). Pre-computed Nearest-Neighbor simulation provides\n"
    "time-dependent traffic calibration. The optimal sequence feeds the lower-level RHCR/PBS-SIPP kinematics engine, executing collision-free trajectories."
)
ax.text(4, -4.0, full_caption, fontsize=8.3, color='#1e293b', linespacing=1.35)

plt.tight_layout()
plt.savefig("system_architecture_diagram.png", dpi=300, bbox_inches='tight')
print("Successfully generated final flawless system_architecture_diagram.png")
