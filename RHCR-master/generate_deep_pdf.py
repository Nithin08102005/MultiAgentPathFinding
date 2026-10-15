"""
DEEP TECHNICAL MANUAL GENERATOR (BOOK-QUALITY SDE REFERENCE)
Generates CAPACITATED_MAPF_FLEET_ROUTING_SDE_MASTER_MANUAL.pdf

Comprehensive, exhaustive engineering manual covering:
- In-depth PBS (Priority-Based Search) mechanics, DAGs, cycle detection, replanning cascades
- In-depth SIPP (Safe Interval Path Planning) state intervals, successor generation, node expansion
- In-depth Reservation Table architecture (CT, SIT, CAT), edge hashing, 5-cell/3-cell footprint insertion
- In-depth 2-Opt Local Search algorithm, array slice reversal, space-time forward cost, dynamic G1 pivoting
- Exact MTZ-MILP mathematical formulation with Big-M linearization and CBC branch-and-cut IPC
- Modern C++14 / Boost internals (Fibonacci heap handles, zero-copy queues, stack buffers)
- 4 production debugging case studies and 15 SDE technical interview questions with senior answers.
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, Image, HRFlowable
)
from reportlab.pdfgen import canvas

# ==========================================
# 1. Custom Canvas with Professional Running Headers & Footers
# ==========================================
class DeepNumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, page_count):
        if self._pageNumber == 1:
            # Suppress running header/footer on cover
            return

        self.saveState()
        
        # Running Header
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(colors.HexColor("#0F294A")) # Dark Navy
        self.drawString(42, 754, "AUTONOMOUS WAREHOUSE FLEET ROUTING ENGINE (C-MG-MAPF)")
        
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#64748B")) # Slate Gray
        self.drawRightString(570, 754, "DEEP SYSTEMS & ALGORITHMIC TECHNICAL MANUAL")
        
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(42, 747, 570, 747)
        
        # Running Footer
        self.line(42, 40, 570, 40)
        
        self.setFont("Helvetica-Bold", 7.2)
        self.setFillColor(colors.HexColor("#334155"))
        self.drawString(42, 28, "CONFIDENTIAL & PROPRIETARY")
        
        self.setFont("Helvetica", 7.2)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(178, 28, "|  C++14 / Boost / PBS / SIPP / Space-Time 2-Opt / MILP")
        
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.setFont("Helvetica-Bold", 7.8)
        self.setFillColor(colors.HexColor("#1E3A8A"))
        self.drawRightString(570, 28, page_str)
        
        self.restoreState()


# ==========================================
# 2. Typography & Styles
# ==========================================
def build_styles():
    styles = getSampleStyleSheet()

    c_navy = colors.HexColor("#0A192F")
    c_blue = colors.HexColor("#1E3A8A")
    c_dark = colors.HexColor("#1E293B")
    
    styles.add(ParagraphStyle(
        'CoverSuper',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#2563EB"),
        spaceAfter=6
    ))

    styles.add(ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=23,
        leading=28,
        textColor=c_navy,
        spaceAfter=10
    ))

    styles.add(ParagraphStyle(
        'CoverSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#475569"),
        spaceAfter=16
    ))

    styles.add(ParagraphStyle(
        'ChapTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=c_navy,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        'SecTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=c_blue,
        spaceBefore=9,
        spaceAfter=4,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        'SubSecTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=c_dark,
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        'DeepBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=c_dark,
        spaceAfter=5
    ))

    styles.add(ParagraphStyle(
        'DeepBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.8,
        textColor=c_dark,
        leftIndent=12,
        firstLineIndent=-9,
        spaceAfter=3.5
    ))

    styles.add(ParagraphStyle(
        'DeepCode',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.4,
        leading=9.6,
        textColor=colors.HexColor("#0F172A")
    ))

    styles.add(ParagraphStyle(
        'TblText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.8,
        leading=10.2,
        textColor=c_dark
    ))

    styles.add(ParagraphStyle(
        'TblHdr',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.8,
        leading=10.2,
        textColor=colors.white
    ))

    styles.add(ParagraphStyle(
        'QAQ',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12.5,
        textColor=c_navy,
        spaceBefore=7,
        spaceAfter=2,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        'QAA',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.3,
        leading=11.8,
        textColor=c_dark,
        leftIndent=6,
        spaceAfter=5
    ))

    return styles


# ==========================================
# 3. Helper Component Generators
# ==========================================
def code_box(code_text, styles, font_size=7.2, leading=9.2):
    p_style = ParagraphStyle('CBStyle', parent=styles['DeepCode'], fontSize=font_size, leading=leading)
    lines = [Paragraph(line.replace(" ", "&nbsp;"), p_style) for line in code_text.strip().split("\n")]
    t = Table([[line] for line in lines], colWidths=[528])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    return t

def callout_box(title, text, styles, border_color="#2563EB", bg_color="#EFF6FF"):
    p_title = Paragraph(f"<b>{title}</b>", styles['SecTitle'])
    p_body = Paragraph(text, styles['DeepBody'])
    t = Table([[p_title], [p_body]], colWidths=[528])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(bg_color)),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#BFDBFE")),
        ('LINEBEFORE', (0,0), (0,-1), 3.5, colors.HexColor(border_color)),
    ]))
    return t

def divider():
    return HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#CBD5E1"), spaceBefore=5, spaceAfter=5)


# ==========================================
# 4. Main Document Construction
# ==========================================
def build_pdf():
    pdf_filename = "CAPACITATED_MAPF_FLEET_ROUTING_SDE_MASTER_MANUAL.pdf"
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        leftMargin=42,
        rightMargin=42,
        topMargin=46,
        bottomMargin=46
    )

    styles = build_styles()
    story = []

    # ====================================================
    # COVER PAGE
    # ====================================================
    story.append(Paragraph("TECHNICAL SYSTEMS MANUAL & COMPLETE SDE INTERVIEW COMPENDIUM", styles['CoverSuper']))
    story.append(Paragraph("Capacitated Multi-Agent Fleet Routing & Coordination Engine", styles['CoverTitle']))
    story.append(Paragraph(
        "A deep architectural, algorithmic, and mathematical reference for large-scale autonomous warehouse fleets. "
        "Provides line-by-line engineering breakdowns of Priority-Based Search (PBS), Safe Interval Path Planning (SIPP), "
        "the Space-Time Reservation Table, 2-Opt Local Search with Dynamic Congestion Caching, and exact MTZ-MILP optimization.",
        styles['CoverSub']
    ))
    story.append(divider())
    story.append(Spacer(1, 6))

    # Metric Badges Table
    badges = [
        [
            Paragraph("<b>+58.8% Throughput</b><br/><font size=6.8 color='#64748B'>832 completed tasks vs 524 FIFO baseline on 16 AGVs / 512 shelves</font>", styles['TblText']),
            Paragraph("<b>95.44% Optimality</b><br/><font size=6.8 color='#64748B'>Proven against exact mathematical MILP (COIN-OR CBC branch-and-cut)</font>", styles['TblText']),
            Paragraph("<b>> 220x Speedup</b><br/><font size=6.8 color='#64748B'>&lt;0.20 ms dispatch latency per decision vs 44.65 ms exact solver</font>", styles['TblText']),
            Paragraph("<b>Modern C++14 & Boost</b><br/><font size=6.8 color='#64748B'>Fibonacci heap O(1) decrease-key, DAG cycle detection, zero-copy</font>", styles['TblText']),
        ]
    ]
    t_badges = Table(badges, colWidths=[130, 134, 134, 130])
    t_badges.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
    ]))
    story.append(t_badges)
    story.append(Spacer(1, 10))

    # Table of Contents
    toc_data = [
        [Paragraph("<b>TABLE OF CONTENTS & CHAPTER DIRECTORY</b>", styles['TblHdr'])],
        [Paragraph(
            "<b>Chapter 1:</b> Problem Formulation & Real-World Fleet Kinematics (5-Cell Moving / 3-Cell Parked Buffer, 7s Dwell, Turns)<br/>"
            "<b>Chapter 2:</b> Upper-Level Engine: Space-Time 2-Opt Task Sequencer & Exact MTZ-MILP Formulation (TRP, Big-M, CBC)<br/>"
            "<b>Chapter 3:</b> Lower-Level Multi-Agent Coordination: Priority-Based Search (PBS Deep Dive, Priority DAG, Cycle Detection)<br/>"
            "<b>Chapter 4:</b> Single-Agent Pathfinding: Safe Interval Path Planning (SIPP Deep Dive, State Intervals, Successors, Fibonacci Heap)<br/>"
            "<b>Chapter 5:</b> Spatial Collision Detection Core: The Reservation Table (Constraint Table, Safe Interval Table, Edge Hashing)<br/>"
            "<b>Chapter 6:</b> Modern C++14 & Boost Systems Architecture (Handles, Move Semantics, Stack Buffers, Cache Locality)<br/>"
            "<b>Chapter 7:</b> Empirical Benchmarks & Mathematical Optimality Validation (Master 1,000s Table, 5,000s MILP Match)<br/>"
            "<b>Chapter 8:</b> Production Engineering & Debugging War Stories (4 Real Bugs: Iterator invalidation, copy drift, freezes)<br/>"
            "<b>Chapter 9:</b> Comprehensive SDE Technical Interview Q&A & System Design Defense (15 In-Depth Senior Answers)<br/>"
            "<b>Chapter 10:</b> Repository Architecture, Code Map & PowerShell Build/Execution Scripts",
            styles['TblText']
        )]
    ]
    t_toc = Table(toc_data, colWidths=[528])
    t_toc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F294A")),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#94A3B8")),
    ]))
    story.append(t_toc)
    story.append(Spacer(1, 10))

    if os.path.exists("shelf_robot_paths_spaced.png"):
        img = Image("shelf_robot_paths_spaced.png", width=528, height=99)
        story.append(img)
        story.append(Spacer(1, 4))
        story.append(Paragraph("<font size=6.8 color='#64748B'>Figure 1: AGV moving footprint with 5-cell dynamic safety buffers and 3-cell parked relaxation in warehouse storage bays.</font>", styles['Normal']))

    story.append(PageBreak())

    # ====================================================
    # CHAPTER 1: PROBLEM FORMULATION & FLEET KINEMATICS
    # ====================================================
    story.append(Paragraph("Chapter 1: Problem Formulation & Real-World Fleet Kinematics", styles['ChapTitle']))
    story.append(divider())

    story.append(Paragraph("1.1 The Real-World Domain & Why Academic \"Toy\" MAPF Fails", styles['SecTitle']))
    story.append(Paragraph(
        "Standard academic Multi-Agent Path Finding (MAPF) makes four naive assumptions that fail catastrophically in commercial warehouse fleets (e.g. Amazon Kiva, Geek+, Quicktron): "
        "(1) robots are 1x1 dimensionless point particles, (2) moving robots have zero safety buffers between them, (3) pick operations are instantaneous (0 seconds), and (4) robots process single tasks (capacity C=1) in raw arrival order. "
        "Deploying toy MAPF causes severe physical collisions, corridor deadlocks, and massive throughput collapse.",
        styles['DeepBody']
    ))

    story.append(Paragraph("1.2 Physical Kinematics: 5-Cell Moving Buffer vs. 3-Cell Parked Relaxation", styles['SecTitle']))
    story.append(Paragraph(
        "In our system, each robot has a physical chassis length and a discrete heading orientation Theta in {0: East, 1: North, 2: West, 3: South}. "
        "To guarantee collision-free operation under hardware latency or deceleration margins while simultaneously preventing corridor traffic deadlocks, we engineer a <b>dynamic state-dependent spatial footprint</b>:",
        styles['DeepBody']
    ))

    footprint_snippet = (
        "// 1. While Driving (t < t_goal): Robot occupies 5 contiguous grid cells\n"
        "// [Safety Back (-2)] [Physical Rear (-1)] [CENTER (0)] [Physical Front (+1)] [Safety Front (+2)]\n"
        "// Implemented via BasicGraph::get_5cell_occupied_cells(loc, orientation, out_cells5)\n"
        "out_cells5[0] = loc;\n"
        "out_cells5[1] = loc + move[orientation];      // Physical front\n"
        "out_cells5[2] = loc - move[orientation];      // Physical back\n"
        "out_cells5[3] = loc + 2 * move[orientation];  // Dynamic front safety buffer\n"
        "out_cells5[4] = loc - 2 * move[orientation];  // Dynamic rear safety buffer\n\n"
        "// 2. While Parked at Goal (t >= t_goal): Dynamically relaxed to 3 physical body cells\n"
        "// [Physical Rear (-1)] [CENTER (0)] [Physical Front (+1)]\n"
        "// The front/rear 1-cell safety margins are released so corridor traffic can flow past uninterrupted!"
    )
    story.append(code_box(footprint_snippet, styles))
    story.append(Spacer(1, 5))

    story.append(Paragraph(
        "<b>Why Endpoint Relaxation is Crucial:</b> In automated warehouses, storage racks line narrow aisles. If a robot parked at a shelf bay maintained its 5-cell moving safety buffer, its front bumper buffer would stick out into the adjacent two-way highway travel corridor. "
        "Any passing robot would detect a collision and freeze, causing a domino-effect gridlock across the entire warehouse quadrant. Dynamically relaxing to the 3-cell physical chassis footprint upon arrival keeps the highway travel lane 100% clear.",
        styles['DeepBody']
    ))

    story.append(Paragraph("1.3 Swept Area Rotation Clearance & 7-Second Shelf Dwell Time", styles['SecTitle']))
    story.append(Paragraph(
        "• <b>In-Place 90° Turning Latency:</b> Turning ±90° takes 1 discrete timestep. When a 3-cell chassis turns in place, its front and back swing through space, sweeping a complete <b>3x3 grid area</b>. "
        "The graph validator <code>BasicGraph::valid_3cell_rotation(loc, from_ori, to_ori)</code> verifies that all 9 adjacent cells are traversable travel cells before allowing a turn, preventing chassis corners from clipping shelves.<br/>"
        "• <b>Service Dwell Time (Delta = 7s):</b> When an AGV arrives at a target shelf, it must dock and service the pick for Delta = 7 seconds. During this entire 7-second dwell, the robot is stationary at the endpoint while its 3-cell physical footprint remains reserved in the space-time reservation table.",
        styles['DeepBody']
    ))

    story.append(PageBreak())

    # ====================================================
    # CHAPTER 2: UPPER-LEVEL ENGINE (2-OPT & MILP)
    # ====================================================
    story.append(Paragraph("Chapter 2: Upper-Level Task Scheduling: 2-Opt & Exact MTZ-MILP", styles['ChapTitle']))
    story.append(divider())

    story.append(Paragraph("2.1 Traveling Repairman Problem (TRP) vs. Standard TSP", styles['SecTitle']))
    story.append(Paragraph(
        "Standard Traveling Salesperson Problem (TSP) minimizes round-trip tour makespan (sum of edge distances). In warehouse order fulfillment, makespan is the wrong objective! "
        "Minimizing makespan treats arriving at Goal 1 at t=5s or t=50s identically as long as the last goal completes at the same time. "
        "Customer order turnaround depends on the <b>Cumulative Arrival Time</b> (Flowtime):",
        styles['DeepBody']
    ))

    story.append(code_box("TRP Objective: Minimize sum_{j=1}^N T_j  (where T_j is the arrival timestamp at task j)", styles))
    story.append(Spacer(1, 5))
    story.append(Paragraph("By optimizing the TRP metric, goals visited early in the sequence heavily reduce the cumulative sum, directly maximizing throughput and minimizing order latency.", styles['DeepBody']))

    story.append(Paragraph("2.2 Exact Mixed-Integer Linear Program (MILP) Formulation", styles['SecTitle']))
    story.append(Paragraph("In <code>solve_milp_cli.py</code>, we implement the provably optimal mathematical TRP using the Miller-Tucker-Zemlin (MTZ) subtour elimination formulation:", styles['DeepBody']))

    milp_code = (
        "Decision Variables:\n"
        "  x_{i, j} in {0, 1}   : 1 if robot travels directly from goal i to goal j; 0 otherwise (0 = start node).\n"
        "  T_j >= 0            : Continuous arrival time timestamp at goal j in {1..N}.\n\n"
        "Mathematical Model:\n"
        "  Minimize   sum_{j=1}^N T_j\n"
        "  Subject to:\n"
        "    sum_{j=1}^N x_{0, j} = 1                         // Depart origin exactly once\n"
        "    sum_{i=0, i!=j}^N x_{i, j} = 1   forall j in {1..N} // Each goal entered exactly once\n"
        "    sum_{j=1, j!=i}^N x_{i, j} <= 1  forall i in {1..N} // Open-loop tour departure\n"
        "    // Miller-Tucker-Zemlin (MTZ) Subtour Elimination with Big-M Linearization:\n"
        "    T_j >= c_{0, j} - M * (1 - x_{0, j})                forall j in {1..N}\n"
        "    T_j >= T_i + c_{i, j} - M * (1 - x_{i, j})          forall i, j in {1..N}, i != j"
    )
    story.append(code_box(milp_code, styles))
    story.append(Spacer(1, 5))

    story.append(Paragraph(
        "<b>How Big-M Linearization Works:</b> M is set to an upper bound on total tour duration (M = sum(max(row)) + 1000). "
        "If x_{i, j} = 1, the term (1 - x_{i, j}) becomes 0, activating the constraint: T_j >= T_i + c_{i, j}. "
        "If x_{i, j} = 0, the term -M relaxes the inequality completely. This eliminates disconnected subtours in O(N^2) constraints without needing exponential Dantzig-Fulkerson-Johnson sets.",
        styles['DeepBody']
    ))

    story.append(PageBreak())

    story.append(Paragraph("Chapter 2: Upper-Level Task Scheduling (Part 2: Space-Time 2-Opt)", styles['ChapTitle']))
    story.append(divider())

    story.append(Paragraph("2.3 The Space-Time 2-Opt Heuristic & Dynamic Goal 1 Pivoting", styles['SecTitle']))
    story.append(Paragraph(
        "Exact MILP takes ~45 ms for N=2, and explodes exponentially for N=7 across 16 robots ((7!)^16 approx 6.4 * 10^59 states). "
        "Our Space-Time 2-Opt algorithm in <code>KivaSystem.cpp</code> solves in <b>&lt;0.20 milliseconds</b>:",
        styles['DeepBody']
    ))

    two_opt_code = (
        "// 1. Nearest-Neighbor Greedy Construction (O(N^2))\n"
        "std::vector<int> perm = build_nearest_neighbor(items, start_v);\n"
        "int best_cost = evaluate_sequence_cost(G, paths, k, items, perm, start_v, start_ori, timestep, task_delay);\n\n"
        "// 2. 2-Opt Local Search Segment Reversal Loop (Max 10 passes)\n"
        "while (improved && max_passes-- > 0) {\n"
        "    improved = false;\n"
        "    for (int i = start_idx; i < N - 1; ++i) {\n"
        "        for (int j = i + 1; j < N; ++j) {\n"
        "            std::vector<int> candidate = best_perm;\n"
        "            std::reverse(candidate.begin() + i, candidate.begin() + j + 1); // Reverse array slice\n"
        "            int cost = evaluate_sequence_cost(G, paths, k, items, candidate, start_v, start_ori, timestep, task_delay);\n"
        "            if (cost < best_cost) { best_cost = cost; best_perm = candidate; improved = true; }\n"
        "        }\n"
        "    }\n"
        "}\n\n"
        "// 3. Dynamic Forward Cost Evaluator (evaluate_sequence_cost):\n"
        "// Leg Cost = Graph Dijkstra Distance + get_projected_route_wait_time(...) + task_delay (7s)\n"
        "// If Goal 1 is blocked by a teammate's 7s dwell, projected wait time spikes -> 2-Opt dynamically pivots to Goal 2!"
    )
    story.append(code_box(two_opt_code, styles))
    story.append(Spacer(1, 5))

    story.append(Paragraph("2.4 Why 2-Opt Untangles Crossed Paths & Dynamic Opportunistic Switching", styles['SecTitle']))
    story.append(Paragraph(
        "<b>Geometric Intuition (Triangle Inequality):</b> When a robot visits a queue of goals in random FIFO order, its path frequently crosses itself in an 'X' pattern. "
        "By reversing the sub-array slice <code>[i..j]</code>, 2-Opt deletes the two crossing edges and replaces them with two non-crossing parallel edges. "
        "By the triangle inequality in 2D graph space, the sum of lengths of opposite sides of a convex quadrangle is strictly shorter than the diagonals: <code>dist(A, C) + dist(B, D) < dist(A, D) + dist(B, C)</code>. "
        "This immediately eliminates millions of meters of wasted transit.<br/><br/>"
        "<b>Dynamic Goal 1 Opportunistic Switching (<code>--lock_active_goal 0</code>):</b><br/>"
        "In naive systems, once a robot starts driving toward Goal 1, it is strictly locked into that target. "
        "If another robot arrives at that shelf first and begins a 7-second dwell, the first robot is forced to come to a complete halt in the travel corridor, causing hallway congestion. "
        "In our system, setting <code>start_idx = 0</code> allows 2-Opt to re-evaluate Goal 1 itself. "
        "When the forward evaluator <code>get_projected_route_wait_time</code> detects that Goal 1 will suffer a 7-second stall upon arrival, 2-Opt dynamically swaps Goal 1 with an unblocked Goal 2. "
        "The robot pivots immediately to pick the open shelf, returning to Goal 1 later once the teammate has departed!",
        styles['DeepBody']
    ))

    story.append(PageBreak())

    # ====================================================
    # CHAPTER 3: LOWER-LEVEL PBS DEEP DIVE
    # ====================================================
    story.append(Paragraph("Chapter 3: Multi-Agent Coordination: Priority-Based Search (PBS)", styles['ChapTitle']))
    story.append(divider())

    story.append(Paragraph("3.1 What is PBS and Why Does Conflict-Based Search (CBS) Thrash?", styles['SecTitle']))
    story.append(Paragraph(
        "In dense warehouse environments with large 5-cell robot footprints, standard <b>Conflict-Based Search (CBS)</b> suffers from catastrophic thrashing. "
        "CBS branches on individual space-time constraints (e.g. Robot 1 cannot be at Cell X at time T). When two 5-cell robots meet in a narrow corridor, they generate dozens of overlapping footprint collisions. "
        "CBS creates thousands of symmetric tree nodes, repeatedly exploring identical deadlocks and timing out (>60 seconds).<br/><br/>"
        "<b>Priority-Based Search (PBS)</b>, invented by Ma et al., solves this by branching on <b>relative priority orderings</b> (e.g. A1 < A2 vs. A2 < A1) instead of discrete cell constraints. "
        "By enforcing that one robot strictly yields to the other, all corridor footprint conflicts between them vanish simultaneously in a single branch!",
        styles['DeepBody']
    ))

    story.append(Paragraph("3.2 PBS High-Level Tree Structure & Depth-First Search (DFS)", styles['SecTitle']))
    story.append(Paragraph("In <code>inc/PBSNode.h</code> and <code>src/PBS.cpp</code>, the high-level search explores a tree of <code>PBSNode</code> objects:", styles['DeepBody']))

    pbs_node_code = (
        "class PBSNode {\n"
        "    PriorityGraph priorities;       // Boost Graph DAG modeling all agent priority edges\n"
        "    list<pair<int, Path>> paths;    // Current collision-free path planned for each agent\n"
        "    list<Conflict> conflicts;       // List of all active space-time conflicts in paths\n"
        "    Conflict conflict;              // The specific chosen conflict to branch upon\n"
        "    pair<int, int> priority;        // The new priority constraint added (a1 < a2)\n"
        "    double g_val, h_val, f_val;     // Path costs for evaluation\n"
        "    PBSNode* parent;                // Pointer to parent node in DFS stack\n"
        "};"
    )
    story.append(code_box(pbs_node_code, styles))
    story.append(Spacer(1, 5))

    story.append(Paragraph("3.3 Step-by-Step PBS Algorithmic Walkthrough", styles['SecTitle']))
    story.append(Paragraph(
        "<b>Step 1: Root Node Initialization (<code>generate_root_node</code>):</b><br/>"
        "Each of the M agents plans its initial path independently using SIPP without any constraints. All paths are inserted into the root node. "
        "The function <code>find_conflicts</code> scans all pairs of paths over the planning window (W=20) to detect vertex and edge collisions.<br/><br/>"
        "<b>Step 2: Conflict Selection (<code>choose_conflict</code>):</b><br/>"
        "If the conflict list is empty, a mutually conflict-free solution is found! Otherwise, PBS selects the <b>earliest conflict in time</b> (minimum timestep t).<br/><br/>"
        "<b>Step 3: Branching on Priority:</b><br/>"
        "For a conflict between Agent A1 and Agent A2, PBS creates two child nodes:<br/>"
        "• <i>Branch 1:</i> Add priority A1 < A2 (A1 has priority over A2; A2 must yield to A1).<br/>"
        "• <i>Branch 2:</i> Add priority A2 < A1 (A2 has priority over A1; A1 must yield to A2).<br/><br/>"
        "<b>Step 4: Cycle Detection on Priority DAG (<code>PriorityGraph::connected</code>):</b><br/>"
        "Before adding an edge A1 -> A2, PBS checks <code>priorities.connected(A2, A1)</code> via depth-first reachability. "
        "If A2 is already higher priority than A1, adding A1 -> A2 creates a directed cycle (A1 < A2 < ... < A1). A cycle represents an impossible mutual wait deadlock! "
        "The child node is immediately pruned (returns <code>false</code>).<br/><br/>"
        "<b>Step 5: Cascade Replanning (<code>find_consistent_paths</code>):</b><br/>"
        "When A1 < A2 is added, A2's path is invalidated. A2 is added to a <code>replan</code> set. Any agent An that is lower priority than A2 in the priority DAG is also marked for replanning. "
        "PBS calls <code>find_path(node, An)</code>, where An plans via SIPP against a reservation table built containing <b>only agents with higher priority than An</b>! "
        "New conflicts are detected and added to the node. If an agent is replanned more than <code>max(5, num_agents)</code> times in one branch, the branch terminates to prevent infinite loops.",
        styles['DeepBody']
    ))

    story.append(PageBreak())

    # ====================================================
    # CHAPTER 4: SIPP ENGINE DEEP DIVE
    # ====================================================
    story.append(Paragraph("Chapter 4: Single-Agent Pathfinding: Safe Interval Path Planning (SIPP)", styles['ChapTitle']))
    story.append(divider())

    story.append(Paragraph("4.1 Why Space-Time A* is Slow vs. Why SIPP is 10x Faster", styles['SecTitle']))
    story.append(Paragraph(
        "Standard Space-Time A* models state as a 4D tuple: <code>(location, timestep, orientation, goal_id)</code>. "
        "At every single second, expanding a node generates 5 successors (4 moves + 1 wait). Across a 20-second window on a 1,995-cell grid, Space-Time A* explores tens of thousands of duplicate nodes. "
        "If a robot must wait for 7 seconds at a shelf, Space-Time A* generates 7 sequential wait states at the same cell!<br/><br/>"
        "<b>Safe Interval Path Planning (SIPP)</b>, invented by Phillips & Likhachev, groups contiguous collision-free timesteps into <b>Safe Intervals</b>: "
        "<code>Interval = [t_min, t_max)</code>. Instead of stepping second-by-second, SIPP transitions directly between safe intervals. "
        "A 7-second wait is compressed into a single interval jump, reducing node expansions by <b>over 90%</b>!",
        styles['DeepBody']
    ))

    story.append(Paragraph("4.2 SIPP Node Representation & Fibonacci Heap Handles", styles['SecTitle']))
    story.append(Paragraph("In <code>inc/SIPP.h</code>, each search node stores its current state and safe interval:", styles['DeepBody']))

    sipp_node_code = (
        "class SIPPNode : public StateTimeAStarNode {\n"
        "    Interval interval;          // [t_min, t_max) where this cell is 100% collision-free\n"
        "    SIPPNode* parent;           // Predecessor node in optimal path\n"
        "    int arrival_t;              // Exact timestep when robot first arrived at this cell\n"
        "    // Boost Fibonacci Heap persistent handles for O(1) amortized decrease-key:\n"
        "    fibonacci_heap<SIPPNode*, compare<compare_node>>::handle_type open_handle;\n"
        "    fibonacci_heap<SIPPNode*, compare<secondary_compare_node>>::handle_type focal_handle;\n"
        "};"
    )
    story.append(code_box(sipp_node_code, styles))
    story.append(Spacer(1, 5))

    story.append(Paragraph("4.3 Complete SIPP Node Expansion Algorithm (Line-by-Line)", styles['SecTitle']))
    story.append(Paragraph("In <code>src/SIPP.cpp</code> lines 93-216, when <code>curr</code> is popped from the FOCAL list, SIPP generates 4 classes of successors:", styles['DeepBody']))

    story.append(Paragraph(
        "<b>1. Forward Translations (4 Directions):</b><br/>"
        "For each orientation dir in {0..3}:<br/>"
        "• Calculates turning degree needed: <code>degree = G.get_rotate_degree(curr_ori, dir)</code> (0°, 90°, or 180°).<br/>"
        "• Validates that remaining time in current interval is sufficient to turn: <code>degree <= interval_max - curr_time</code>.<br/>"
        "• Checks destination physical clearance: <code>G.valid_3cell_state(target_loc, dir)</code> and swept area: <code>G.valid_3cell_rotation(curr_loc, curr_ori, dir)</code>.<br/>"
        "• Earliest possible arrival time at target cell is: <code>min_t = curr_time + degree + 1</code>.<br/>"
        "• Queries Reservation Table: <code>rt.getSafeIntervals(curr_loc, target_loc, dir, min_t, interval_max + 1)</code>.<br/>"
        "• For each safe interval returned, instantiates a child SIPPNode with arrival time <code>min_t</code>!<br/><br/>"
        "<b>2. Backward Reverse Slide (No Turning):</b><br/>"
        "Industrial AGVs can reverse without turning. SIPP evaluates <code>back_dir = (curr_ori + 2) % 4</code>. If the cell behind is clear, the robot slides backward in 1 timestep while keeping its original orientation (0° rotation cost).<br/><br/>"
        "<b>3. In-Place Wait Transitions (Successive Safe Intervals):</b><br/>"
        "If an obstacle passes through the robot's current cell, the cell becomes blocked and then safe again. SIPP calls <code>rt.findSafeInterval(interval, curr_loc, interval_max)</code> to find the <i>next</i> safe interval at the same cell, allowing the robot to wait out a passing teammate!<br/><br/>"
        "<b>4. Goal Shelf Dwell Enforcement (Delta = 7s):</b><br/>"
        "When arriving at a target shelf, SIPP enforces: <code>req_release = max(goal_time, curr->arrival_t + task_delay)</code>. If <code>curr_time < req_release</code> and the safe interval covers it, SIPP clamps <code>curr->state.timestep = req_release</code>, guaranteeing the full 7-second dwell!",
        styles['DeepBody']
    ))

    story.append(PageBreak())

    # ====================================================
    # CHAPTER 5: RESERVATION TABLE ARCHITECTURE
    # ====================================================
    story.append(Paragraph("Chapter 5: Spatial Collision Core: The Reservation Table", styles['ChapTitle']))
    story.append(divider())

    story.append(Paragraph("5.1 Internal Data Structures: CT, SIT, and CAT", styles['SecTitle']))
    story.append(Paragraph(
        "The <code>ReservationTable</code> in <code>inc/ReservationTable.h</code> is the in-memory spatial database that arbitrates multi-robot space-time reservations. "
        "It manages three core internal lookup tables:",
        styles['DeepBody']
    ))

    rt_struct_code = (
        "// 1. Constraint Table (CT): Location/Edge Hash -> List of Blocked Time Ranges [t_min, t_max)\n"
        "unordered_map<size_t, list<pair<int, int>>> ct;\n\n"
        "// 2. Safe Interval Table (SIT): Location/Edge Hash -> List of Collision-Free Intervals\n"
        "unordered_map<size_t, list<Interval>> sit;\n\n"
        "// 3. Conflict Avoidance Table (CAT): Soft constraints for secondary tie-breaking\n"
        "vector<vector<bool>> cat;"
    )
    story.append(code_box(rt_struct_code, styles))
    story.append(Spacer(1, 5))

    story.append(Paragraph("5.2 Vertex Constraints vs. Edge Hashing", styles['SecTitle']))
    story.append(Paragraph(
        "• <b>Vertex Constraints (Cell Collisions):</b> If an agent occupies grid cell <code>V</code> during time range <code>[t1, t2)</code>, it is inserted into the hash table as <code>ct[V].emplace_back(t1, t2)</code>.<br/>"
        "• <b>Edge Constraints (Head-On / Swap Collisions):</b> A swap collision occurs when Robot A moves U -> V while Robot B moves V -> U at timestep T. "
        "Standard vertex checking misses this because neither robot is on the same cell at the same time! "
        "We encode directed edges into unique 64-bit integer keys using the formula:<br/>"
        "<code>getEdgeIndex(from, to) = (from + 1) * map_size + to</code><br/>"
        "Both directed edges <code>getEdgeIndex(U, V)</code> and <code>getEdgeIndex(V, U)</code> are reserved in <code>ct</code> for time range <code>[T, T+1)</code>.",
        styles['DeepBody']
    ))

    story.append(Paragraph("5.3 Footprint Insertion: 5-Cell Moving Buffer & Parked Endpoints", styles['SecTitle']))
    story.append(Paragraph("In <code>ReservationTable::insertPath2CT(path)</code>, paths are mapped into space-time constraints:", styles['DeepBody']))

    insert_code = (
        "for (size_t i = 0; i < path.size(); i++) {\n"
        "    int t = path[i].timestep;\n"
        "    int cells5[5];\n"
        "    G.get_5cell_occupied_cells(path[i].location, path[i].orientation, cells5); // Extract 5 cells\n"
        "    for (int c = 0; c < 5; c++) {\n"
        "        ct[cells5[c]].emplace_back(max(0, t - k_robust), t + 1 + k_robust); // Block all 5 cells\n"
        "    }\n"
        "    // Edge constraints between consecutive 5-cell states:\n"
        "    if (i > 0) {\n"
        "        for (int c = 0; c < 5; c++) {\n"
        "            for (int p = 0; p < 5; p++) {\n"
        "                ct[getEdgeIndex(curr_cells[c], prev_cells[p])].emplace_back(t, t + 1);\n"
        "            }\n"
        "        }\n"
        "    }\n"
        "}\n"
        "// Parked endpoint holding: Keeps 3-cell footprint reserved up to window + Delta + 1:\n"
        "int end_t = max((int)path.back().timestep + task_delay + 2, window + 1);\n"
        "for (int c = 0; c < 5; c++) ct[cells5[c]].emplace_back(path.back().timestep, end_t);"
    )
    story.append(code_box(insert_code, styles))
    story.append(Spacer(1, 5))

    story.append(PageBreak())

    story.append(Paragraph("Chapter 5: Spatial Collision Core (Part 2: Safe Interval Generation)", styles['ChapTitle']))
    story.append(divider())

    story.append(Paragraph("5.4 Generating Safe Intervals: updateSIT & mergeIntervals Algorithm", styles['SecTitle']))
    story.append(Paragraph(
        "To allow SIPP to query collision-free time windows in O(1) time, <code>ReservationTable::updateSIT(loc)</code> reads all raw blocked ranges in <code>ct[loc]</code>, "
        "merges overlapping or touching ranges using <code>mergeIntervals</code>, and mathematically inverts the timeline:",
        styles['DeepBody']
    ))

    sit_code = (
        "void ReservationTable::updateSIT(size_t location) {\n"
        "    sit[location].clear();\n"
        "    if (ct.find(location) == ct.end()) {\n"
        "        sit[location].emplace_back(0, INTERVAL_MAX, false); // Completely free cell: [0, 10000)\n"
        "        return;\n"
        "    }\n"
        "    ct[location].sort(); // Sort blocked intervals by t_min\n"
        "    // 1. Merge overlapping blocked ranges: [3, 7) + [5, 9) -> [3, 9)\n"
        "    list<pair<int, int>> merged;\n"
        "    for (auto& range : ct[location]) {\n"
        "        if (merged.empty() || merged.back().second < range.first) merged.push_back(range);\n"
        "        else merged.back().second = max(merged.back().second, range.second);\n"
        "    }\n"
        "    // 2. Invert timeline to produce Safe Intervals:\n"
        "    int t_prev = 0;\n"
        "    for (auto& b : merged) {\n"
        "        if (t_prev < b.first) sit[location].emplace_back(t_prev, b.first, false); // Safe window\n"
        "        t_prev = b.second;\n"
        "    }\n"
        "    if (t_prev < INTERVAL_MAX) sit[location].emplace_back(t_prev, INTERVAL_MAX, false);\n"
        "}"
    )
    story.append(code_box(sit_code, styles))
    story.append(Spacer(1, 6))

    story.append(Paragraph("5.5 Concrete Numerical Walkthrough & Timeline Inversion", styles['SecTitle']))
    story.append(Paragraph(
        "Consider Grid Cell 42 during a 20-second planning window:<br/>"
        "• At t = 3, Robot 1 drives through Cell 42, reserving footprint interval <code>[3, 7)</code>.<br/>"
        "• At t = 10, Robot 2 arrives at adjacent bay and its safety buffer overlaps Cell 42 during <code>[10, 15)</code>.<br/>"
        "• The Constraint Table contains: <code>ct[42] = { [3, 7), [10, 15) }</code>.<br/>"
        "• <code>updateSIT(42)</code> inverts this into three discrete Safe Intervals:<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;<b>Interval 1:</b> <code>[0, 3)</code> &nbsp;&nbsp;&nbsp;(Duration: 3 seconds safe)<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;<b>Interval 2:</b> <code>[7, 10)</code> &nbsp;&nbsp;(Duration: 3 seconds safe)<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;<b>Interval 3:</b> <code>[15, 10000)</code> (Infinite tail safe)<br/><br/>"
        "<b>How SIPP Evaluates a Transition:</b><br/>"
        "Suppose Robot 3 is currently at Cell 41 at t = 2, with heading orientation requiring 1 rotation step (degree = 1). "
        "The earliest arrival time at Cell 42 is <code>min_t = curr_time (2) + turn (1) + move (1) = 4</code>.<br/>"
        "• SIPP checks Interval 1 <code>[0, 3)</code>: <code>min_t = 4 > 3</code> -> Target window has already closed (rejected).<br/>"
        "• SIPP checks Interval 2 <code>[7, 10)</code>: <code>min_t = 4 <= 10</code>. Arrival is valid! Robot 3 can either wait 3 seconds at Cell 41 until t = 5, begin moving at t = 6, and enter Cell 42 at exactly t = 7. "
        "SIPP generates a single successor node for Interval 2 with arrival timestamp 7 in <b>one single expansion</b>!",
        styles['DeepBody']
    ))

    story.append(PageBreak())

    # ====================================================
    # CHAPTER 6: MODERN C++ & BOOST SYSTEMS ARCHITECTURE
    # ====================================================
    story.append(Paragraph("Chapter 6: Modern C++14 & Boost Systems Architecture", styles['ChapTitle']))
    story.append(divider())

    story.append(Paragraph("6.1 Why Boost is Essential in Production Robotics Systems", styles['SecTitle']))
    story.append(Paragraph(
        "A common junior interview trap is thinking that standard C++ <code>std::</code> is always sufficient. In high-performance systems engineering, <code>std::</code> has critical architectural omissions. "
        "Here is why Boost libraries are strictly required in our engine:",
        styles['DeepBody']
    ))

    boost_deep = [
        ("boost::heap::fibonacci_heap", "std::priority_queue has NO decrease-key API. When A* or SIPP finds a shorter route to an existing open node, std:: forces you to push a duplicate node, bloating queue size and forcing stale node pops. Boost's Fibonacci heap provides persistent handle_type pointers stored directly inside the node. Calling open_list.update(node->open_handle) updates node priority in O(1) amortized time with zero heap reallocation!"),
        ("boost::graph::adjacency_list", "Provides industrial-grade Directed Acyclic Graph (DAG) structures. Used in PriorityGraph.h to represent agent priority constraints (A1 < A2), run reachability testing, and detect cycle deadlocks via topological traversal."),
        ("boost::program_options", "Declarative, type-safe CLI parsing for 20+ simulation flags. Automatically generates --help, enforces required arguments, and handles type conversion cleanly without manual strcmp parsing."),
        ("boost::tokenizer & filesystem", "boost::tokenizer uses zero-copy string slice parsing to read massive 57MB map heuristic tables without intermediate memory allocations. boost::filesystem guarantees cross-platform directory creation.")
    ]
    for lib, why in boost_deep:
        story.append(Paragraph(f"<b>• <code>{lib}</code>:</b> {why}", styles['DeepBullet']))
    story.append(Spacer(1, 6))

    story.append(Paragraph("6.2 Memory & Cache Optimization Patterns in the Codebase", styles['SecTitle']))
    story.append(Paragraph(
        "• <b>Zero-Copy Move Semantics (<code>std::move</code>):</b> In <code>KivaSystem.cpp</code> line 1425, when the 2-Opt optimizer completes reordering a robot's 7-task queue, the local buffer is transferred into the active robot state using <code>bundle[k] = std::move(reordered);</code>, transferring pointer ownership without deep-copying heap buffers.<br/>"
        "• <b>Stack-Allocated Fixed Arrays vs. Heap Churn:</b> Geometric footprint functions like <code>get_5cell_occupied_cells</code> pass pre-allocated stack arrays (<code>int out_cells[5]</code>) by reference instead of returning <code>std::vector<int></code>. This completely eliminates dynamic <code>malloc/free</code> allocations in the inner search loop, which runs over 100,000 times per second!<br/>"
        "• <b>Flat Heuristic Table Layout:</b> The 512-endpoint heuristic distance tables are stored in contiguous 2D vectors (<code>heuristics[endpoint][cell]</code>), maximizing L1/L2 CPU cache hit rates during heuristic lookups in SIPP.",
        styles['DeepBody']
    ))

    story.append(Paragraph("6.3 Subprocess IPC via OS Pipes (_popen)", styles['SecTitle']))
    story.append(Paragraph(
        "When exact mathematical MILP mode is selected (<code>--reorder_mode 3</code>), C++ streams the (N+1)x(N+1) cost matrix to <code>solve_milp_cli.py</code> over an OS pipe using <code>_popen</code> and parses the optimal integer sequence via <code>fscanf</code>. "
        "In production, pipe IPC can be upgraded to native C bindings (pybind11) or shared memory (POSIX <code>shm_open</code>) to eliminate process-spawning latency.",
        styles['DeepBody']
    ))

    story.append(PageBreak())

    # ====================================================
    # CHAPTER 7: EMPIRICAL BENCHMARKS & VALIDATION
    # ====================================================
    story.append(Paragraph("Chapter 7: Empirical Benchmarks & Mathematical Optimality Validation", styles['ChapTitle']))
    story.append(divider())

    story.append(Paragraph("7.1 Master Fleet Benchmark (16 AGVs, 512 Shelves, 1,000s Horizon)", styles['SecTitle']))
    story.append(Paragraph("Evaluated on <code>kiva_4zone_shaved.map</code> (35x57 grid) with capacity C=7, pick dwell Delta = 7s:", styles['DeepBody']))

    bench_data = [
        [Paragraph("Config", styles['TblHdr']), Paragraph("Scheduling Policy", styles['TblHdr']), Paragraph("Goal 1 Policy", styles['TblHdr']), Paragraph("Completed Tasks", styles['TblHdr']), Paragraph("Throughput (tasks/s)", styles['TblHdr']), Paragraph("Improvement vs. Baseline", styles['TblHdr'])],
        [Paragraph("1", styles['TblText']), Paragraph("FIFO Baseline (Raw Order)", styles['TblText']), Paragraph("Raw / Unordered", styles['TblText']), Paragraph("<b>524</b>", styles['TblText']), Paragraph("0.523", styles['TblText']), Paragraph("Baseline (0.0%)", styles['TblText'])],
        [Paragraph("2", styles['TblText']), Paragraph("Naive Distance TSP (Static)", styles['TblText']), Paragraph("Locked G1", styles['TblText']), Paragraph("<b>769</b>", styles['TblText']), Paragraph("0.768", styles['TblText']), Paragraph("+46.8%", styles['TblText'])],
        [Paragraph("3", styles['TblText']), Paragraph("Space-Time 2-Opt (Clearance Aware)", styles['TblText']), Paragraph("Locked G1", styles['TblText']), Paragraph("<b>804</b>", styles['TblText']), Paragraph("0.803", styles['TblText']), Paragraph("+53.4%", styles['TblText'])],
        [Paragraph("4", styles['TblText']), Paragraph("Naive Distance TSP (Static)", styles['TblText']), Paragraph("Dynamic G1", styles['TblText']), Paragraph("<b>823</b>", styles['TblText']), Paragraph("0.822", styles['TblText']), Paragraph("+57.1%", styles['TblText'])],
        [Paragraph("5", styles['TblText']), Paragraph("<b>Dynamic Space-Time 2-Opt (Ours)</b>", styles['TblText']), Paragraph("<b>Dynamic G1</b>", styles['TblText']), Paragraph("<b>832</b>", styles['TblText']), Paragraph("<b>0.831</b>", styles['TblText']), Paragraph("<b>+58.8% (PEAK)</b>", styles['TblText'])],
    ]
    t_bench = Table(bench_data, colWidths=[36, 148, 72, 75, 82, 115])
    t_bench.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F294A")),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#EFF6FF")),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#94A3B8")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    story.append(t_bench)
    story.append(Spacer(1, 8))

    # Benchmark Plots
    p1 = "plot1_planning_window.png"
    p4 = "plot4_fleet_scalability.png"
    if os.path.exists(p1) and os.path.exists(p4):
        img1 = Image(p1, width=258, height=211)
        img4 = Image(p4, width=258, height=167)
        t_plots = Table([[img1, img4]], colWidths=[264, 264])
        t_plots.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(t_plots)
        story.append(Paragraph("<font size=6.8 color='#64748B'>Figure 2: (Left) Planning Window W=20 balances foresight with replanning agility. (Right) Scalability up to 50 robots.</font>", styles['Normal']))

    story.append(Spacer(1, 8))
    story.append(Paragraph("7.2 Rigorous Mathematical Validation: Exact MILP vs. 2-Opt (5,000s Horizon)", styles['SecTitle']))
    story.append(Paragraph("Direct 1-to-1 evaluation across 904 real warehouse tasks and 900 continuous dispatch decisions:", styles['DeepBody']))

    val_data = [
        [Paragraph("Metric", styles['TblHdr']), Paragraph("Exact MILP (CBC Ground Truth)", styles['TblHdr']), Paragraph("Proposed C++ 2-Opt Engine", styles['TblHdr']), Paragraph("Scientific Assessment", styles['TblHdr'])],
        [Paragraph("Tasks Evaluated", styles['TblText']), Paragraph("904 tasks", styles['TblText']), Paragraph("904 tasks", styles['TblText']), Paragraph("100% Identical Real Workload", styles['TblText'])],
        [Paragraph("Exact Sequence Match", styles['TblText']), Paragraph("900 / 900 (100.0%)", styles['TblText']), Paragraph("706 / 900 (78.44%)", styles['TblText']), Paragraph("78.44% Exact Route Match", styles['TblText'])],
        [Paragraph("Cumulative Distance", styles['TblText']), Paragraph("18,828.0 steps", styles['TblText']), Paragraph("19,687.0 steps", styles['TblText']), Paragraph("Real turns & traffic included", styles['TblText'])],
        [Paragraph("Optimality Gap", styles['TblText']), Paragraph("<b>0.00% (Provable Optimum)</b>", styles['TblText']), Paragraph("<b>4.56%</b>", styles['TblText']), Paragraph("<b>95.44% Mathematical Optimality!</b>", styles['TblText'])],
        [Paragraph("CPU Solving Runtime", styles['TblText']), Paragraph("40.185 seconds total", styles['TblText']), Paragraph("~0.180 seconds total", styles['TblText']), Paragraph("<b>> 220x Faster Execution</b>", styles['TblText'])],
        [Paragraph("Avg. Latency / Decision", styles['TblText']), Paragraph("44.65 milliseconds", styles['TblText']), Paragraph("<b>&lt; 0.20 milliseconds</b>", styles['TblText']), Paragraph("Sub-millisecond Real-Time Ready", styles['TblText'])],
    ]
    t_val = Table(val_data, colWidths=[110, 134, 134, 150])
    t_val.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E3A8A")),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#94A3B8")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    story.append(t_val)

    story.append(PageBreak())

    # ====================================================
    # CHAPTER 8: DEBUGGING WAR STORIES
    # ====================================================
    story.append(Paragraph("Chapter 8: Production Engineering & Debugging War Stories", styles['ChapTitle']))
    story.append(divider())

    story.append(Paragraph("In senior technical and systems interviews, interviewers evaluate how you debug production failures. Here are the 4 real bugs diagnosed and resolved in this codebase:", styles['DeepBody']))

    bugs = [
        ("Story 1: The \"Silent Collision\" Iterator Invalidation Bug",
         "ReservationTable::updateSIT in ReservationTable.cpp",
         "Under dense robot traffic, robots occasionally drove through each other without throwing any solver collision exception.",
         "In ReservationTable::updateSIT, an obsolete cleanup statement called ct.erase(it) while updating constraints. This silently deleted active hard spatial constraints from the table, making subsequent collision checks completely blind to existing robot trajectories.",
         "Removed ct.erase(it), guaranteeing that hard constraints persist across all planning windows."),

        ("Story 2: The \"Ghost State\" Copy Constructor Bug",
         "ReservationTable::copy() in ReservationTable.h",
         "During PBS search branching, robots mysteriously stalled at timestep 35 and refused to explore paths.",
         "The copy routine ReservationTable::copy() omitted copying the boolean flag prioritize_start. When PBS branched and copied the reservation table for child nodes, prioritize_start defaulted to false, causing SIPP to skip start nodes and terminate early.",
         "Explicitly copied prioritize_start and task_delay across all table clone routines and PBS::setRT()."),

        ("Story 3: The 34-Second Search Freeze (Denial-of-Service)",
         "SIPP single-agent expansion loop in SIPP.cpp",
         "Whenever a target shelf was blocked by another robot servicing a pick, the simulation froze for 34+ seconds on a single tick.",
         "The single-agent SIPP expansion limit was configured to 50,000 nodes. When an endpoint was completely blocked, SIPP burned 34 seconds exploring 50,000 futile dead-end states before giving up.",
         "Profiled the search, reduced the node expansion limit to 3,000 nodes, and added early-exit Manhattan heuristic fallbacks, eliminating the 34-second freeze completely."),

        ("Story 4: The Flaky Non-Deterministic Tie-Breaker",
         "SIPPNode::compare_node in SIPP.h",
         "Identical simulation runs executed with the exact same random seed produced completely different path trajectories, breaking CI/CD regression tests.",
         "SIPPNode::compare_node was using rand() % 2 == 0 to break ties between equal-cost nodes, introducing non-reproducible randomness into the search tree.",
         "Replaced with deterministic multi-level keys: break ties by higher g-value (depth), then lower conflict counts, then deterministic agent ID ordering.")
    ]

    for title, loc, sym, root, fix in bugs:
        story.append(Paragraph(f"<b>{title}</b>", styles['SecTitle']))
        story.append(Paragraph(f"<b>Location:</b> <code>{loc}</code>", styles['DeepBody']))
        story.append(Paragraph(f"• <b>Symptom:</b> {sym}", styles['DeepBullet']))
        story.append(Paragraph(f"• <b>Root Cause:</b> {root}", styles['DeepBullet']))
        story.append(Paragraph(f"• <b>Engineering Fix:</b> {fix}", styles['DeepBullet']))
        story.append(Spacer(1, 3))

    story.append(PageBreak())

    # ====================================================
    # CHAPTER 9: COMPREHENSIVE SDE INTERVIEW DEFENSE
    # ====================================================
    story.append(Paragraph("Chapter 9: Comprehensive SDE Technical Interview Q&A", styles['ChapTitle']))
    story.append(divider())

    qas_p1 = [
        ("Q1: Walk me through your project from input to motor execution.",
         "1. Input: Loads a 2D warehouse map (walls, travel lanes, shelf bays) and incoming orders.<br/>"
         "2. Upper Level: Each AGV holds up to 7 tasks in a queue. Our 2-Opt scheduler groups and orders tasks by proximity and projected corridor congestion in <0.20ms.<br/>"
         "3. Lower Level: Rolling-horizon window (W = 20s). Robots plan paths using SIPP over a shared space-time reservation table.<br/>"
         "4. Conflict Resolution: If two robots want the same cell, Priority-Based Search builds a dependency DAG, resolves orderings, and prunes deadlocks.<br/>"
         "5. Execution: Robots drive the first 5 seconds, dwell 7 seconds to complete the pick, and replan."),

        ("Q2: Why use C++ instead of Python or Go?",
         "Multi-agent graph search expands tens of thousands of nodes per second. In Python, object overhead and GIL make tight search loops 50x–100x slower. Go has garbage collection pauses that introduce tail-latency spikes. C++ gives deterministic memory layouts, zero-cost abstractions, stack-allocated fixed arrays, and direct pointer handles into Fibonacci heaps, guaranteeing sub-millisecond execution (<0.20 ms)."),

        ("Q3: Why did you use Boost instead of sticking to standard std::?",
         "Because std::priority_queue does not support a decrease-key operation! In A* and SIPP, when a shorter path to an open node is discovered, you must update its priority. With std::, you must push a duplicate node, bloating heap size. boost::heap::fibonacci_heap provides persistent handle_type iterators that enable O(1) amortized decrease-key updates directly."),

        ("Q4: How does your system prevent corridor deadlocks when two robots face each other?",
         "1. Priority-Based Search (PBS) assigns priority (A_i yields to A_j). Before assigning, we run cycle detection on the priority DAG. If adding an edge creates a cycle (deadlock), that branch is pruned.<br/>"
         "2. Swept-area turning checks ensure turns only occur in 3-wide corridor junctions.<br/>"
         "3. Endpoint holding prevents robots from planning through stationary parked AGVs."),

        ("Q5: How would you scale this system from 16 robots to 10,000 robots?",
         "Centralized planning cannot scale to 10,000 robots. To scale to 10,000 AGVs:<br/>"
         "1. Spatial Decomposition: Partition the warehouse into discrete zones (like air traffic sectors) with regional planners.<br/>"
         "2. Highway Rules: Enforce one-way traffic directions on aisles to eliminate 85% of head-on conflicts by design.<br/>"
         "3. Microservice Handoffs: Use distributed locks or consensus at zone intersection boundaries."),

        ("Q6: What is the time complexity of the 2-Opt task scheduler?",
         "For N tasks in an agent's queue: Nearest-Neighbor seeding takes O(N^2). Each 2-Opt pass evaluates N*(N-1)/2 = O(N^2) candidate swaps. Capping passes at 10 yields strict O(N^2) complexity. Since capacity N <= 7, N^2 <= 49 operations, converging in under 0.20 ms."),

        ("Q7: How did you handle communication between C++ and Python for MILP?",
         "In reorder_mode 3, C++ constructs a cost matrix, launches solve_milp_cli.py via _popen, streams parameters over stdout, and parses the optimal integer sequence via fscanf. While convenient for benchmarking, in high-throughput production I would replace pipe IPC with native C API bindings (pybind11) or shared memory."),
    ]

    for q, a in qas_p1:
        story.append(Paragraph(q, styles['QAQ']))
        story.append(Paragraph(a, styles['QAA']))

    story.append(PageBreak())

    # Chapter 9 Part 2
    story.append(Paragraph("Chapter 9: Technical Interview Q&A (Continued)", styles['ChapTitle']))
    story.append(divider())

    qas_p2 = [
        ("Q8: What design patterns did you use across the codebase?",
         "1. Strategy Pattern: SingleAgentSolver base class with SIPP and StateTimeAStar implementations.<br/>"
         "2. Template Method: MAPFSolver base class extended by PBS, ECBS, and WHCAStar.<br/>"
         "3. RAII: Automatic resource and memory management in Boost data structures."),

        ("Q9: How do you handle unexpected delays or dynamic obstacles during path execution?",
         "In rolling-horizon execution, we only commit to h = 5 timesteps of the 20-step plan. If an unexpected delay occurs, SIPP invalidates the safe intervals for the affected cells. At the next planning tick, the robot's actual position is used as the new start state, and PBS reroutes affected agents. If a target shelf remains blocked by a delayed teammate, the upper-level 2-Opt scheduler dynamically pivots to an adjacent free shelf in the capacity queue."),

        ("Q10: How does the space-time reservation table differentiate between vertex conflicts and edge conflicts?",
         "Vertex conflicts occur when two robots occupy the same grid cell at timestep t; this is checked by looking up ct[cell] for interval [t, t+1]. Edge (swap) conflicts occur when robot A moves u->v while robot B moves v->u during [t, t+1]. We detect this by hashing a directed edge index getEdgeIndex(from, to) = (from + 1) * map_size + to and reserving both (u, v) and (v, u) during [t, t+1]."),

        ("Q11: Explain how you precomputed and stored the heuristic distance tables for 512 endpoints.",
         "We ran backward Dijkstra/BFS from each of the 512 shelf endpoints across the navigable map, generating a lookup table heuristics[endpoint][cell]. For 1,995 cells and 512 endpoints, this table consumes only ~8 MB in RAM. In SingleAgentSolver.cpp, we added lazy dynamic computation and Manhattan fallbacks so unindexed dynamic coordinates never crash with out-of-range exceptions."),

        ("Q12: What is the difference between Conflict-Based Search (CBS), ECBS, and PBS?",
         "CBS is an exact two-level solver that branches on individual vertex/edge constraints; it is optimal but scales exponentially in dense fleets. Enhanced CBS (ECBS) is bounded suboptimal: it maintains a FOCAL list containing nodes within w * min_cost and prioritizes nodes with the fewest conflicts. Priority-Based Search (PBS) branches on relative agent priorities (A_i < A_j) instead of spatial constraints, using depth-first search to find collision-free paths orders of magnitude faster without thrashing."),

        ("Q13: What memory profiling and performance analysis tools would you use on this C++ engine?",
         "For memory leaks and uninitialized reads, we compile with AddressSanitizer (-fsanitize=address) and run Valgrind Memcheck. For CPU profiling in hot loops, we use Linux perf or Intel VTune to analyze branch mispredictions and L1/L2 cache misses. In Windows/MSVC, we use Visual Studio Performance Profiler and Tracy Profiler macros to track per-tick millisecond latency breakdowns between the 2-Opt scheduler and SIPP expansions."),

        ("Q14: How does your system prevent starvation among lower-priority robots in PBS?",
         "Starvation is prevented by three mechanisms: (1) Rolling-Horizon Replanning (h=5), which periodically rebuilds priority relationships based on live conflict states; (2) Task Service Dwell (Delta = 7s), during which a high-priority robot docks at a shelf and relaxes its footprint to 3 cells, yielding travel corridors to lower-priority traffic; and (3) Dynamic FIFO task replenishment from the global backlog."),

        ("Q15: What was the single most difficult engineering trade-off you made in this project?",
         "The trade-off between monolithic theoretical optimality and real-time computational feasibility. An exact monolithic MILP formulation could theoretically guarantee 100% joint optimality across both task assignment and continuous trajectories, but it times out on more than 4 robots. By decoupling into a bi-level architecture (Space-Time 2-Opt + Rolling-Horizon PBS/SIPP), we accepted a negligible 4.56% optimality gap to achieve a >220x speedup (<0.20 ms per decision), making the system production-ready for real-time AGV deployments.")
    ]

    for q, a in qas_p2:
        story.append(Paragraph(q, styles['QAQ']))
        story.append(Paragraph(a, styles['QAA']))

    story.append(PageBreak())

    # ====================================================
    # CHAPTER 10: CODEBASE REPOSITORY MAP & SCRIPTS
    # ====================================================
    story.append(Paragraph("Chapter 10: Codebase Architecture, File Map & Build System", styles['ChapTitle']))
    story.append(divider())

    story.append(Paragraph("10.1 Complete Repository File Directory", styles['SecTitle']))
    
    file_map = (
        "MAPF-with-multi-level-architecture/RHCR-master/\n"
        "├── inc/\n"
        "│   ├── common.h             : Boost heap, unordered containers, interval typedefs\n"
        "│   ├── BasicGraph.h         : 5-cell moving & 3-cell parked footprints, 3x3 turn validation\n"
        "│   ├── BasicSystem.h        : Rolling-horizon simulation loop (W=20, h=5)\n"
        "│   ├── KivaSystem.h         : Task capacity queues, 2-Opt & MILP reorder modes\n"
        "│   ├── ReservationTable.h   : Space-time constraint table (CT) and Safe Interval Table (SIT)\n"
        "│   ├── SIPP.h / SIPPNode.h  : Safe Interval Path Planning single-agent solver\n"
        "│   ├── PBS.h / PBSNode.h    : Priority-Based Search multi-agent conflict coordinator\n"
        "│   └── PriorityGraph.h      : Boost Graph adjacency_list for priority DAG cycle detection\n"
        "├── src/\n"
        "│   ├── driver.cpp           : CLI entry point, Boost program_options, scenario launcher\n"
        "│   ├── KivaSystem.cpp       : 2-Opt ST-TSP reordering, MILP IPC pipe bridge, dwell logic\n"
        "│   ├── ReservationTable.cpp : 5-cell motion buffer insertion, 3-cell parked relaxation\n"
        "│   ├── SIPP.cpp             : SIPP interval expansion, arrival_t tracking, node limits\n"
        "│   └── PBS.cpp              : High-level conflict detection and priority tree branching\n"
        "├── solve_milp_cli.py        : Exact MTZ-MILP solver using Python PuLP + COIN-OR CBC\n"
        "├── compare_cpp_with_exact_milp.py : 1-to-1 ground truth validation script across 5000s\n"
        "├── kiva_4zone_shaved.map    : 35x57 grid, 512 shelf endpoints, 4 quadrant zones\n"
        "└── CMakeLists.txt           : C++14 build script linking Boost components"
    )
    story.append(code_box(file_map, styles, font_size=6.9, leading=8.4))
    story.append(Spacer(1, 4))

    story.append(Paragraph("10.2 Compilation & Execution Commands (PowerShell)", styles['SecTitle']))
    build_cmds = (
        "# 1. Install required Boost packages via vcpkg:\n"
        "./vcpkg install boost-program-options:x64-windows boost-system:x64-windows boost-filesystem:x64-windows boost-heap:x64-windows boost-graph:x64-windows\n\n"
        "# 2. Configure and Build High-Performance Release Binary:\n"
        "cmake -S . -B build -A x64 -DCMAKE_TOOLCHAIN_FILE=\"vcpkg/scripts/buildsystems/vcpkg.cmake\" -DVCPKG_TARGET_TRIPLET=x64-windows\n"
        "cmake --build build --config Release\n\n"
        "# 3. Run Winner Configuration (Dynamic Space-Time 2-Opt - 832 Tasks):\n"
        "./build/Release/lifelong.exe --scenario KIVA --map kiva_4zone_shaved.map --agentNum 16 --solver PBS --simulation_time 1000 --output ./exp/bench_st_dynamic --rotation 1 --cutoffTime 100 --planning_window 20 --task_delay 7 --capacity_mode 1 --capacity 7 --safety_mode 1 --reorder_mode 2 --lock_active_goal 0 --seed 0"
    )
    story.append(code_box(build_cmds, styles, font_size=6.7, leading=8.3))
    story.append(Spacer(1, 5))

    story.append(callout_box(
        "FINAL INTERVIEW ADVICE",
        "You now have complete, uncompromised, 360-degree technical command over this project. "
        "Whether asked about algorithmic complexity, C++ memory management, Boost internals, exact integer programming, "
        "or real-world debugging war stories, you have the exact numbers, diagrams, and code references to stand out as a top-tier systems engineer.",
        styles
    ))

    # Build the document
    doc.build(story, canvasmaker=DeepNumberedCanvas)
    print(f"Successfully generated {pdf_filename}!")

if __name__ == '__main__':
    build_pdf()
