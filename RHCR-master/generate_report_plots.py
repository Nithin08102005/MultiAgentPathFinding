import matplotlib.pyplot as plt
import numpy as np

# Set global publication styles
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 1.0

# ==============================================================================
# PLOT 1: Planning Window Horizon Sweep (w) - Throughput & Runtime Trade-off
# ==============================================================================
def make_plot1():
    w_vals = [5, 10, 20, 50, 100]
    tasks = [0, 790, 817, 810, 789]
    runtimes = [None, 30.9, 27.6, 63.5, 163.4]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.8, 7.2), sharex=True, gridspec_kw={'height_ratios': [1.2, 1]})

    # --- Top Panel: Tasks Completed ---
    valid_w = [10, 20, 50, 100]
    valid_tasks = [790, 817, 810, 789]

    ax1.plot(valid_w, valid_tasks, color='#1f77b4', lw=2.5, marker='o', markersize=8, label='Dynamic ST 2-Opt')
    # Mark w=5 failure
    ax1.scatter([5], [0], color='#d62728', marker='X', s=160, zorder=5, label='w=5: Deadlock (Myopia Failure)')
    # Star on w=20 peak
    ax1.scatter([20], [817], color='#2ca02c', marker='*', s=250, zorder=5, label='w=20: Global Optimum (817 Tasks)')

    # Value annotations
    ax1.annotate('Deadlock\n(t=130)', (5, 30), textcoords="offset points", xytext=(0, 10),
                 ha='center', fontsize=9, color='#d62728', weight='bold')
    ax1.annotate('790', (10, 790), textcoords="offset points", xytext=(0, 8), ha='center', fontsize=9, weight='bold')
    ax1.annotate('817 (Peak)', (20, 817), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=10, weight='bold', color='#2ca02c')
    ax1.annotate('810', (50, 810), textcoords="offset points", xytext=(0, 8), ha='center', fontsize=9, weight='bold')
    ax1.annotate('789', (100, 789), textcoords="offset points", xytext=(0, 8), ha='center', fontsize=9, weight='bold')

    ax1.set_ylabel('Tasks Completed (1k timesteps)', fontsize=11, weight='bold')
    ax1.set_title('Plot 1: Planning Window Horizon Sweep (w) — Throughput & Computation Trade-off', fontsize=11.5, weight='bold', pad=12)
    ax1.set_ylim(-50, 920)
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.legend(loc='lower right', framealpha=0.9, fontsize=9)

    # --- Bottom Panel: Wall-Clock Runtime ---
    valid_runtimes = [30.9, 27.6, 63.5, 163.4]
    ax2.plot(valid_w, valid_runtimes, color='#ff7f0e', lw=2.5, marker='s', markersize=7, label='Wall-Clock Runtime')
    
    ax2.annotate('30.9 s', (10, 30.9), textcoords="offset points", xytext=(0, 8), ha='center', fontsize=9, weight='bold')
    ax2.annotate('27.6 s (Fastest)', (20, 27.6), textcoords="offset points", xytext=(0, -16), ha='center', fontsize=9, weight='bold', color='#2ca02c')
    ax2.annotate('63.5 s (2.3x)', (50, 63.5), textcoords="offset points", xytext=(0, 8), ha='center', fontsize=9, weight='bold')
    ax2.annotate('163.4 s (5.9x)', (100, 163.4), textcoords="offset points", xytext=(-25, -5), ha='center', fontsize=9, weight='bold', color='#d62728')

    ax2.set_xscale('log')
    ax2.set_xticks([5, 10, 20, 50, 100])
    ax2.get_xaxis().set_major_formatter(plt.ScalarFormatter())
    ax2.set_xlabel('Planning Horizon Window (w)', fontsize=11, weight='bold')
    ax2.set_ylabel('Runtime (Seconds)', fontsize=11, weight='bold')
    ax2.set_ylim(0, 190)
    ax2.grid(True, linestyle='--', alpha=0.5)
    ax2.legend(loc='upper left', framealpha=0.9, fontsize=9)

    plt.tight_layout()
    plt.savefig('plot1_planning_window.png', dpi=300)
    plt.savefig('plot1_planning_window.pdf')
    plt.close()
    print('[+] Saved plot1_planning_window.png & .pdf')


# ==============================================================================
# PLOT 2: Time Allocation & Congestion Breakdown (Stacked Bar Chart)
# ==============================================================================
def make_plot2():
    methods = [
        'FIFO Baseline',
        'Naive TSP\n(Locked)',
        'Space-Time 2-Opt\n(Locked)',
        'Naive TSP\n(Dynamic)',
        'Proposed ST 2-Opt\n(Dynamic)'
    ]
    tasks = [500, 769, 804, 823, 832]
    moving = [68.8, 52.6, 52.1, 50.8, 51.3]
    dwell = [24.1, 37.3, 38.7, 39.8, 40.0]
    wait = [7.2, 10.1, 9.2, 9.5, 8.7]

    x = np.arange(len(methods))
    width = 0.55

    fig, ax = plt.subplots(figsize=(9.2, 6.2))

    b_dwell = ax.bar(x, dwell, width, label='Productive Pick Dwell (task_delay=7s)', color='#2ca02c', alpha=0.9, edgecolor='black', lw=0.8)
    b_move = ax.bar(x, moving, width, bottom=dwell, label='Active Transit / Moving', color='#1f77b4', alpha=0.85, edgecolor='black', lw=0.8)
    b_wait = ax.bar(x, wait, width, bottom=np.array(dwell) + np.array(moving), label='Traffic Wait / Congestion', color='#d62728', alpha=0.85, edgecolor='black', lw=0.8)

    # Annotate percentages inside segments
    for i in range(len(methods)):
        ax.text(x[i], dwell[i] / 2, f'{dwell[i]:.1f}%', ha='center', va='center', color='white', weight='bold', fontsize=9.5)
        ax.text(x[i], dwell[i] + moving[i] / 2, f'{moving[i]:.1f}%', ha='center', va='center', color='white', weight='bold', fontsize=9.5)
        ax.text(x[i], dwell[i] + moving[i] + wait[i] / 2, f'{wait[i]:.1f}%', ha='center', va='center', color='white', weight='bold', fontsize=8.5)
        ax.text(x[i], 102.5, f'{tasks[i]} Tasks', ha='center', va='bottom', color='#111111', weight='bold', fontsize=10)

    ax.set_ylabel('Fleet Time Allocation (%)', fontsize=11, weight='bold')
    ax.set_title('Plot 2: Fleet Time Allocation Breakdown — Driving vs. Picking Dwell vs. Traffic Wait', fontsize=12, weight='bold', pad=34)
    ax.set_xticks(x)
    ax.set_xticklabels(methods, fontsize=10, weight='semibold')
    ax.set_ylim(0, 116)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, 1.01), ncol=3, framealpha=0.95, fontsize=9.2)

    plt.tight_layout()
    plt.savefig('plot2_time_allocation.png', dpi=300)
    plt.savefig('plot2_time_allocation.pdf')
    plt.close()
    print('[+] Saved plot2_time_allocation.png & .pdf')


# ==============================================================================
# PLOT 3: Task Capacity Sensitivity (C)
# ==============================================================================
def make_plot3():
    capacities = [1, 3, 5, 7, 9]
    tasks = [494, 659, 763, 817, 873]
    runtimes = [50.0, 30.0, 25.0, 26.0, 24.0]

    fig, ax1 = plt.subplots(figsize=(8, 5.5))

    color_tasks = '#1f77b4'
    color_time = '#d62728'

    # Left axis: Tasks
    ax1.set_xlabel('Robot Carrying Capacity (C)', fontsize=11, weight='bold')
    ax1.set_ylabel('Completed Tasks (1k timesteps)', color=color_tasks, fontsize=11, weight='bold')
    line1 = ax1.plot(capacities, tasks, color=color_tasks, lw=2.5, marker='o', markersize=8, label='Completed Tasks')
    ax1.tick_params(axis='y', labelcolor=color_tasks)
    ax1.set_ylim(400, 950)
    ax1.set_xticks(capacities)

    for c, t in zip(capacities, tasks):
        ax1.annotate(f'{t}', (c, t), textcoords="offset points", xytext=(0, 8), ha='center', fontsize=9.5, weight='bold', color=color_tasks)

    # Right axis: Runtime
    ax2 = ax1.twinx()
    ax2.set_ylabel('Wall-Clock Simulation Runtime (s)', color=color_time, fontsize=11, weight='bold')
    line2 = ax2.plot(capacities, runtimes, color=color_time, lw=2.2, linestyle='--', marker='s', markersize=7, label='Runtime (s)')
    ax2.tick_params(axis='y', labelcolor=color_time)
    ax2.set_ylim(15, 60)

    for c, rt in zip(capacities, runtimes):
        ax2.annotate(f'{rt:.0f}s', (c, rt), textcoords="offset points", xytext=(0, -15), ha='center', fontsize=9, weight='bold', color=color_time)

    plt.title('Plot 3: Robot Task Capacity Sensitivity (C) — Throughput Saturation & Runtime', fontsize=12, weight='bold', pad=14)
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='center right', framealpha=0.9, fontsize=9.5)
    ax1.grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.savefig('plot3_capacity_sensitivity.png', dpi=300)
    plt.savefig('plot3_capacity_sensitivity.pdf')
    plt.close()
    print('[+] Saved plot3_capacity_sensitivity.png & .pdf')


# ==============================================================================
# PLOT 4: Fleet Scalability (N Robots)
# ==============================================================================
def make_plot4():
    robots = [4, 6, 8, 10, 12, 14, 16]
    tasks = [239, 341, 439, 551, 657, 746, 817]
    runtimes = [3.0, 5.0, 6.2, 9.155, 12.35, 26.0, 27.0]

    fig, ax1 = plt.subplots(figsize=(8.5, 5.5))

    color_tasks = '#2ca02c'
    color_time = '#9467bd'

    # Left axis: Throughput
    ax1.set_xlabel('Fleet Size / Number of Robots (N)', fontsize=11, weight='bold')
    ax1.set_ylabel('Completed Tasks (1k timesteps)', color=color_tasks, fontsize=11, weight='bold')
    line1 = ax1.plot(robots, tasks, color=color_tasks, lw=2.5, marker='o', markersize=8, label='Completed Tasks')
    ax1.tick_params(axis='y', labelcolor=color_tasks)
    ax1.set_xticks(robots)
    ax1.set_ylim(150, 920)

    for r, t in zip(robots, tasks):
        ax1.annotate(f'{t}', (r, t), textcoords="offset points", xytext=(0, 8), ha='center', fontsize=9, weight='bold', color=color_tasks)

    # Right axis: Runtime
    ax2 = ax1.twinx()
    ax2.set_ylabel('Wall-Clock Runtime (Seconds)', color=color_time, fontsize=11, weight='bold')
    line2 = ax2.plot(robots, runtimes, color=color_time, lw=2.2, linestyle='--', marker='^', markersize=7.5, label='Runtime (s)')
    ax2.tick_params(axis='y', labelcolor=color_time)
    ax2.set_ylim(0, 35)

    for r, rt in zip(robots, runtimes):
        ax2.annotate(f'{rt:.1f}s', (r, rt), textcoords="offset points", xytext=(0, -14), ha='center', fontsize=8.5, weight='bold', color=color_time)

    plt.title('Plot 4: Fleet Scalability (N = 4 to 16 Robots) — Throughput & Low-Level Solver Runtime', fontsize=12, weight='bold', pad=14)
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='lower right', framealpha=0.9, fontsize=9.5)
    ax1.grid(True, linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.savefig('plot4_fleet_scalability.png', dpi=300)
    plt.savefig('plot4_fleet_scalability.pdf')
    plt.close()
    print('[+] Saved plot4_fleet_scalability.png & .pdf')


# ==============================================================================
# PLOT 5: Fleet Fairness & Workload Balance (Per-Agent Distribution)
# ==============================================================================
def make_plot5():
    robot_ids = [f'R{i}' for i in range(16)]
    fifo_tasks = [33, 33, 32, 29, 34, 33, 32, 31, 31, 30, 32, 33, 32, 27, 29, 29]
    opt_tasks  = [51, 51, 47, 53, 53, 49, 54, 49, 50, 50, 55, 49, 52, 47, 57, 50]

    x = np.arange(len(robot_ids))
    width = 0.38

    fig, ax = plt.subplots(figsize=(11, 5.8))

    b1 = ax.bar(x - width/2, fifo_tasks, width, label='FIFO Baseline (Total: 500, Avg: 31.3)', color='#7f7f7f', alpha=0.85, edgecolor='black', lw=0.7)
    b2 = ax.bar(x + width/2, opt_tasks, width, label='Proposed Dynamic ST 2-Opt (Total: 817, Avg: 51.1)', color='#1f77b4', alpha=0.9, edgecolor='black', lw=0.7)

    # Annotate bars inside for high contrast and zero reference line collision
    for i in range(len(robot_ids)):
        ax.text(x[i] - width/2, fifo_tasks[i] - 2.8, f'{fifo_tasks[i]}', ha='center', va='center', fontsize=8.5, weight='bold', color='white', zorder=6)
        ax.text(x[i] + width/2, opt_tasks[i] - 3.2, f'{opt_tasks[i]}', ha='center', va='center', fontsize=9, weight='bold', color='white', zorder=6)

    # Average benchmark lines
    ax.axhline(np.mean(fifo_tasks), color='#d62728', linestyle=':', lw=1.5, alpha=0.7, label='FIFO Fleet Mean (31.3 tasks/robot)')
    ax.axhline(np.mean(opt_tasks), color='#2ca02c', linestyle='--', lw=1.8, alpha=0.85, label='Proposed Fleet Mean (51.1 tasks/robot)')

    ax.set_xlabel('Robot Identifier (16 Concurrent AGVs Across 4 Warehouse Zones)', fontsize=11, weight='bold')
    ax.set_ylabel('Tasks Completed per Robot', fontsize=11, weight='bold')
    ax.set_title('Plot 5: Fleet Workload Balance & Fairness — Per-Agent Productivity Comparison', fontsize=12, weight='bold', pad=14)
    ax.set_xticks(x)
    ax.set_xticklabels(robot_ids, fontsize=10, weight='semibold')
    ax.set_ylim(0, 76)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.legend(loc='upper right', bbox_to_anchor=(0.99, 0.98), framealpha=0.95, fontsize=9.2)

    plt.tight_layout()
    plt.savefig('plot5_fleet_fairness.png', dpi=300)
    plt.savefig('plot5_fleet_fairness.pdf')
    plt.close()
    print('[+] Saved plot5_fleet_fairness.png & .pdf')


if __name__ == '__main__':
    print('Generating all 5 publication-quality report plots...')
    make_plot1()
    make_plot2()
    make_plot3()
    make_plot4()
    make_plot5()
    print('\n[SUCCESS] All 5 figures successfully generated in PNG (300 DPI) and PDF!')
