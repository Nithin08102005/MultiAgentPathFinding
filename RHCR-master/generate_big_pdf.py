"""
High-Performance PDF Generation Script
Generates CAPACITATED_MAPF_FLEET_ROUTING_SDE_MASTER_MANUAL.pdf
Comprehensive SDE Interview Manual & Systems Architecture Guide for C-MG-MAPF Project
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
# 1. Canvas with Running Header & Footer
# ==========================================
class NumberedCanvas(canvas.Canvas):
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
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            # Skip cover page
            return
        
        self.saveState()
        
        # Running Top Header
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#1A365D")) # Deep Navy
        self.drawString(45, 752, "CAPACITATED MULTI-AGENT FLEET ROUTING ENGINE (C-MG-MAPF)")
        
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#718096"))
        self.drawRightString(567, 752, "SDE TECHNICAL INTERVIEW MANUAL")
        
        self.setStrokeColor(colors.HexColor("#CBD5E0"))
        self.setLineWidth(0.6)
        self.line(45, 745, 567, 745)
        
        # Running Bottom Footer
        self.setStrokeColor(colors.HexColor("#CBD5E0"))
        self.setLineWidth(0.6)
        self.line(45, 42, 567, 42)
        
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(colors.HexColor("#4A5568"))
        self.drawString(45, 30, "CONFIDENTIAL & PROPRIETARY")
        
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#718096"))
        self.drawString(185, 30, "|  Autonomous Robotics, Systems & Fleet Dispatch Architecture")
        
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#2B6CB0"))
        self.drawRightString(567, 30, page_str)
        
        self.restoreState()


# ==========================================
# 2. Styles Definition
# ==========================================
def build_custom_styles():
    styles = getSampleStyleSheet()
    
    # Primary Colors
    c_navy = colors.HexColor("#0F294A")
    c_blue = colors.HexColor("#1E3A8A")
    c_accent = colors.HexColor("#2563EB")
    c_dark = colors.HexColor("#1F2937")
    c_code_bg = colors.HexColor("#F8FAFC")
    
    # Document Title (Cover)
    styles.add(ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=25,
        leading=30,
        textColor=c_navy,
        alignment=0, # Left-aligned
        spaceAfter=10
    ))
    
    styles.add(ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12.5,
        leading=17,
        textColor=colors.HexColor("#4B5563"),
        alignment=0,
        spaceAfter=20
    ))
    
    styles.add(ParagraphStyle(
        'ChapterHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=21,
        textColor=c_navy,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        'SectionHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=c_blue,
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        'SubSectionHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=c_dark,
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        'BodyCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.8,
        leading=12.4,
        textColor=c_dark,
        spaceAfter=6
    ))

    styles.add(ParagraphStyle(
        'BodyBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.8,
        leading=12.4,
        textColor=c_dark,
        spaceAfter=6
    ))

    styles.add(ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.8,
        leading=12.2,
        textColor=c_dark,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=4
    ))

    styles.add(ParagraphStyle(
        'CodeSnippet',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.8,
        leading=10.2,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=4,
        spaceAfter=4
    ))

    styles.add(ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1E3A8A"),
        spaceAfter=0
    ))

    styles.add(ParagraphStyle(
        'PitchText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.2,
        leading=13.5,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=0
    ))

    styles.add(ParagraphStyle(
        'TableText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=c_dark
    ))

    styles.add(ParagraphStyle(
        'TableHeaderText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        textColor=colors.white
    ))

    styles.add(ParagraphStyle(
        'QAQuestion',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=c_navy,
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    ))

    styles.add(ParagraphStyle(
        'QAAnswer',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.6,
        leading=12.2,
        textColor=c_dark,
        leftIndent=8,
        spaceAfter=6
    ))

    return styles


# ==========================================
# 3. Helper Factory Functions
# ==========================================
def make_callout(text, styles, title="KEY ARCHITECTURAL TAKEAWAY"):
    p_title = Paragraph(f"<b>{title}</b>", styles['SectionHeader'])
    p_body = Paragraph(text, styles['CalloutText'])
    t = Table([[p_title], [p_body]], colWidths=[522])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EFF6FF")),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#BFDBFE")),
        ('LINEBEFORE', (0,0), (0,-1), 3.5, colors.HexColor("#2563EB")),
    ]))
    return t

def make_code_box(code_str, styles):
    lines = [Paragraph(line.replace(" ", "&nbsp;"), styles['CodeSnippet']) for line in code_str.strip().split("\n")]
    t = Table([[line] for line in lines], colWidths=[522])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('BOX', (0,0), (-1,-1), 0.6, colors.HexColor("#CBD5E1")),
    ]))
    return t

def make_divider(color="#E2E8F0", thickness=0.8, space_before=6, space_after=6):
    return HRFlowable(width="100%", thickness=thickness, color=colors.HexColor(color), spaceBefore=space_before, spaceAfter=space_after)

# ==========================================
# 4. Main Document Builder
# ==========================================
def generate_master_manual():
    pdf_filename = "CAPACITATED_MAPF_FLEET_ROUTING_SDE_MASTER_MANUAL.pdf"
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        leftMargin=45,
        rightMargin=45,
        topMargin=50,
        bottomMargin=50
    )
    
    styles = build_custom_styles()
    story = []
    
    # ----------------------------------------------------
    # COVER PAGE
    # ----------------------------------------------------
    # Hero Banner
    banner_data = [
        [Paragraph("<font color='#93C5FD'><b>TECHNICAL SYSTEM MANUAL & INTERVIEW COMPENDIUM</b></font>", styles['Normal'])],
        [Paragraph("Capacitated Multi-Goal Multi-Agent Fleet Routing & Coordination Engine", styles['CoverTitle'])],
        [Paragraph("High-Performance C++14 / Boost Bi-Level Architecture for Autonomous Warehouse Fulfillment, Combining Space-Time 2-Opt Task Dispatching, Rolling-Horizon PBS & SIPP Path Planning, and Exact Mathematical MILP Benchmarking.", styles['CoverSubtitle'])],
    ]
    t_banner = Table(banner_data, colWidths=[522])
    t_banner.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('LEFTPADDING', (0,0), (-1,-1), 16),
        ('RIGHTPADDING', (0,0), (-1,-1), 16),
        ('TOPPADDING', (0,0), (-1,-1), 16),
        ('BOTTOMPADDING', (0,0), (-1,-1), 16),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('LINEBEFORE', (0,0), (0,-1), 4, colors.HexColor("#1E3A8A")),
    ]))
    story.append(t_banner)
    story.append(Spacer(1, 14))

    # Executive Key Performance Highlights (4 Badges Table)
    badges = [
        [
            Paragraph("<b>+58.8% Throughput</b><br/><font size=7 color='#4B5563'>832 completed tasks vs 524 FIFO on 16 AGVs / 512 shelves</font>", styles['TableText']),
            Paragraph("<b>95.44% Optimality</b><br/><font size=7 color='#4B5563'>Proven against exact mathematical MILP (COIN-OR CBC)</font>", styles['TableText']),
            Paragraph("<b>> 220x Speedup</b><br/><font size=7 color='#4B5563'>&lt;0.20 ms dispatch latency vs 44.65 ms MILP solver</font>", styles['TableText']),
            Paragraph("<b>Production C++14</b><br/><font size=7 color='#4B5563'>Boost Fibonacci heap, DAG cycle detection, zero-copy queues</font>", styles['TableText']),
        ]
    ]
    t_badges = Table(badges, colWidths=[126, 132, 132, 132])
    t_badges.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
    ]))
    story.append(t_badges)
    story.append(Spacer(1, 16))

    # Table of Contents Preview Box
    toc_data = [
        [Paragraph("<b>TABLE OF CONTENTS</b>", styles['TableHeaderText'])],
        [Paragraph("<b>Chapter 1:</b> Executive Summary & SDE Interview Positioning (Pitch, Resume, Metrics)<br/>"
                   "<b>Chapter 2:</b> Real-World Warehouse Robotics & Fleet Domain (Why Toy MAPF Fails)<br/>"
                   "<b>Chapter 3:</b> System Architecture & Bi-Level Optimization (Top-Down / Bottom-Up Coupling)<br/>"
                   "<b>Chapter 4:</b> Upper-Level Scheduling: Space-Time 2-Opt vs. Exact MTZ-MILP Formulation<br/>"
                   "<b>Chapter 5:</b> Lower-Level Coordination: Rolling-Horizon PBS & SIPP Engine<br/>"
                   "<b>Chapter 6:</b> C++14 & Boost Masterclass for Systems Software Engineers<br/>"
                   "<b>Chapter 7:</b> Empirical Benchmarks & Mathematical Optimality Validation<br/>"
                   "<b>Chapter 8:</b> Real Engineering Debugging War Stories (Iterator invalidation, ghost states, freezes)<br/>"
                   "<b>Chapter 9:</b> Comprehensive SDE Interview Defense & System Design Questions (15 In-Depth Q&As)<br/>"
                   "<b>Chapter 10:</b> Codebase Architecture, File Map & Build System (CMake / vcpkg)", styles['TableText'])]
    ]
    t_toc = Table(toc_data, colWidths=[522])
    t_toc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F294A")),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F8FAFC")),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#94A3B8")),
    ]))
    story.append(t_toc)
    story.append(Spacer(1, 14))

    # Shelf Robot Footprint graphic on Cover
    if os.path.exists("shelf_robot_paths_spaced.png"):
        img = Image("shelf_robot_paths_spaced.png", width=522, height=97.8)
        story.append(img)
        story.append(Spacer(1, 6))
        story.append(Paragraph("<font size=7 color='#64748B'>Figure 1: Autonomous Mobile Robot (AGV) moving footprint with 5-cell dynamic safety buffers and 3-cell parked relaxation in warehouse storage bays.</font>", styles['Normal']))

    story.append(PageBreak())

    # ----------------------------------------------------
    # CHAPTER 1: SDE POSITIONING, ELEVATOR PITCH & RESUME
    # ----------------------------------------------------
    story.append(Paragraph("Chapter 1: Executive Summary & SDE Interview Positioning", styles['ChapterHeader']))
    story.append(make_divider())

    story.append(Paragraph("1.1 The 30-Second SDE Elevator Pitch", styles['SectionHeader']))
    p_pitch = Paragraph(
        "\"I built a high-performance C++ fleet routing and dispatch engine for autonomous warehouse robots. "
        "Think of it like Google Maps or an Uber dispatch engine, but for dozens of autonomous vehicles operating simultaneously "
        "in tight warehouse corridors with zero collisions.<br/><br/>"
        "Architecturally, it’s a bi-level system: a high-level task scheduler that groups and reorders pickup jobs in under 0.2 milliseconds, "
        "and a low-level rolling-horizon path planner using custom graph algorithms. I wrote it in C++14 using Boost data structures like "
        "Fibonacci heaps and DAGs for cycle detection, cutting dispatch latency by 220x and boosting overall system throughput by 58%.\"",
        styles['PitchText']
    )
    t_pitch = Table([[p_pitch]], colWidths=[522])
    t_pitch.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0FDF4")),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('BOX', (0,0), (-1,-1), 0.6, colors.HexColor("#86EFAC")),
        ('LINEBEFORE', (0,0), (0,-1), 4, colors.HexColor("#16A34A")),
    ]))
    story.append(t_pitch)
    story.append(Spacer(1, 10))

    story.append(Paragraph("1.2 The Jargon Translator: How to Speak to SDE Interviewers", styles['SectionHeader']))
    story.append(Paragraph("Software Development Engineer (SDE) interviewers are looking for data structures, algorithms, concurrency, latency, and clean code. Always translate theoretical robotics terminology into standard backend/systems concepts:", styles['BodyCustom']))

    trans_data = [
        [Paragraph("Academic / Robotics Literature Jargon", styles['TableHeaderText']), Paragraph("How You Say It in an SDE Interview", styles['TableHeaderText']), Paragraph("Underlying CS Data Structure / Concept", styles['TableHeaderText'])],
        [Paragraph("Capacitated Multi-Goal MAPF (C-MG-MAPF)", styles['TableText']), Paragraph("Multi-Agent Fleet Routing & Task Dispatcher", styles['TableText']), Paragraph("Decoupled Distributed Scheduling Engine", styles['TableText'])],
        [Paragraph("Mixed-Integer Linear Program (MILP)", styles['TableText']), Paragraph("Exact Combinatorial Optimizer Baseline", styles['TableText']), Paragraph("Branch-and-Cut Integer Linear Programming", styles['TableText'])],
        [Paragraph("Space-Time 2-Opt Heuristic", styles['TableText']), Paragraph("Greedy Local Search with Dynamic Caching", styles['TableText']), Paragraph("O(N^2) Array Segment Reversal with Memoization", styles['TableText'])],
        [Paragraph("Safe Interval Path Planning (SIPP)", styles['TableText']), Paragraph("Interval-based A* Graph Search", styles['TableText']), Paragraph("Graph search over time ranges instead of discrete ticks", styles['TableText'])],
        [Paragraph("Priority-Based Search (PBS)", styles['TableText']), Paragraph("Topological DAG Search with Cycle Detection", styles['TableText']), Paragraph("Directed Acyclic Graph traversal for deadlock pruning", styles['TableText'])],
        [Paragraph("Reservation Table (CT & SIT)", styles['TableText']), Paragraph("Space-Time Hash Table / Collision Cache", styles['TableText']), Paragraph("unordered_map of location -> list of blocked time spans", styles['TableText'])],
        [Paragraph("5-Cell Moving / 3-Cell Parked Footprint", styles['TableText']), Paragraph("Dynamic Bounding-Box Buffer Padding", styles['TableText']), Paragraph("Geometric collision envelopes with state-dependent margins", styles['TableText'])],
        [Paragraph("Shelf Pick Dwell Time (Delta = 7s)", styles['TableText']), Paragraph("Stationary Job Execution / Service Dwell", styles['TableText']), Paragraph("Temporal resource holding in reservation table", styles['TableText'])],
    ]
    t_trans = Table(trans_data, colWidths=[170, 172, 180])
    t_trans.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E3A8A")),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#94A3B8")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
    ]))
    story.append(t_trans)
    story.append(Spacer(1, 10))

    story.append(Paragraph("1.3 Production-Grade Resume Bullet Points", styles['SectionHeader']))
    story.append(Paragraph("• <b>High-Performance Fleet Routing Engine (C++14 / Boost):</b> Engineered a real-time multi-agent routing system for 16 warehouse AGVs across a 512-node topological grid, achieving <b>+58.8% throughput</b> (832 tasks completed) over standard FIFO baselines.", styles['BulletCustom']))
    story.append(Paragraph("• <b>Low-Latency Scheduling & Local Search:</b> Designed an O(N^2) 2-Opt local search task scheduler with dynamic congestion caching, cutting decision latency from 44.6ms to <b>&lt;0.20ms (&gt;220x speedup)</b> while achieving a 95.4% optimality match against exact MILP branch-and-cut solvers.", styles['BulletCustom']))
    story.append(Paragraph("• <b>Custom Graph Search & Deadlock Prevention:</b> Implemented Safe Interval Path Planning (SIPP) and Priority-Based Search (PBS) utilizing <code>boost::heap::fibonacci_heap</code> for <b>O(1) amortized decrease-key</b> updates and directed acyclic graphs (DAG) for cycle/deadlock detection.", styles['BulletCustom']))
    story.append(Paragraph("• <b>Profiling & Systems Debugging:</b> Diagnosed and resolved memory corruption in space-time hash tables, eliminated 34-second search-space freezes by tuning expansion thresholds, and enforced deterministic multi-key tie-breaking across simulation runs.", styles['BulletCustom']))

    story.append(PageBreak())

    # ----------------------------------------------------
    # CHAPTER 2: REAL-WORLD WAREHOUSE ROBOTICS DOMAIN
    # ----------------------------------------------------
    story.append(Paragraph("Chapter 2: Real-World Warehouse Robotics & Fleet Domain", styles['ChapterHeader']))
    story.append(make_divider())

    story.append(Paragraph("2.1 The 4 Fatal Flaws of Academic \"Toy\" MAPF", styles['SectionHeader']))
    story.append(Paragraph("In university research papers, Multi-Agent Path Finding (MAPF) is almost universally simplified to dimensionless 1x1 point particles moving on a grid with instantaneous picking. In commercial production fleets (Amazon Robotics, Geek+, Quicktron), deploying these algorithms causes physical hardware damage, aisle blockages, and warehouse gridlock.", styles['BodyCustom']))

    flaws = [
        ("1. Point-Robot Assumption", "Academic models treat robots as zero-length points. In reality, an AGV transporting a pod occupies physical space. In our project, moving robots have an extended 5-cell dynamic footprint, requiring swept-area validation during turning."),
        ("2. Zero Safety Buffers", "Toy algorithms allow robots to drive bumper-to-bumper with 0 cells in between. If one robot experiences latency or decelerates, a catastrophic rear-end collision occurs. Our system enforces a dynamic 1-cell front and rear safety envelope."),
        ("3. Instantaneous Task Handshake", "Academic models assume that when a robot reaches a shelf cell, the item is picked in 0 timesteps. In reality, lifting, barcode scanning, or human picking requires stationary dwell time (we model Delta = 7 seconds)."),
        ("4. Unit-Capacity (C = 1) Ping-Ponging", "Academic robots take 1 task, visit 1 shelf, and return home. Real industrial AGVs carry bundles of up to C = 7 tasks. Visiting these in raw order causes wild, energy-wasting zig-zagging across the facility.")
    ]
    for title, desc in flaws:
        story.append(Paragraph(f"<b>{title}:</b> {desc}", styles['BulletCustom']))
    story.append(Spacer(1, 8))

    story.append(Paragraph("2.2 Robot Kinematics: 5-Cell Moving Buffer vs. 3-Cell Parked Footprint Relaxation", styles['SectionHeader']))
    story.append(Paragraph("A central innovation of this codebase is the dynamic state-dependent spatial footprint:", styles['BodyCustom']))
    
    footprint_code = (
        "// While driving (t < t_goal): Occupies 5 cells (Center + Front/Back Body + 1-cell Safety Margins)\n"
        "F_moving = [Safety_Back, Physical_Rear, CENTER, Physical_Front, Safety_Front]\n\n"
        "// While parked at shelf (t >= t_goal): Dynamically relaxed to 3 physical body cells\n"
        "F_parked = [Physical_Rear, CENTER, Physical_Front]"
    )
    story.append(make_code_box(footprint_code, styles))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Why Endpoint Relaxation is Crucial:</b> If an AGV parked in a storage bay maintained its 5-cell safety buffer while servicing a 7-second pick, its front safety margin would protrude into the main highway travel aisle, causing perpetual corridor deadlocks. Dynamically relaxing to 3 physical body cells when stationary allows corridor traffic to flow past uninterrupted.", styles['BodyCustom']))

    story.append(Paragraph("2.3 Rotational Kinematics & 3x3 Swept Area Check", styles['SectionHeader']))
    story.append(Paragraph("Robots maintain heading orientation Theta in {0: East, 1: North, 2: West, 3: South}. In-place 90-degree rotations take 1 discrete timestep. When a 3-cell chassis rotates, it sweeps a 3x3 area. The function <code>valid_3cell_rotation</code> in <code>BasicGraph.h</code> checks all 9 adjacent cells before permitting a turn, ensuring AGVs only rotate in sufficiently wide junction intersections.", styles['BodyCustom']))

    story.append(PageBreak())

    # ----------------------------------------------------
    # CHAPTER 3: SYSTEM ARCHITECTURE & BI-LEVEL COUPLING
    # ----------------------------------------------------
    story.append(Paragraph("Chapter 3: System Architecture & Bi-Level Optimization", styles['ChapterHeader']))
    story.append(make_divider())

    story.append(Paragraph("3.1 The Centralized Scalability Bottleneck", styles['SectionHeader']))
    story.append(Paragraph("Why can't we solve the entire problem using a single monolithic optimizer? Because Capacitated Multi-Goal MAPF is <b>strongly NP-hard</b>. It combines the permutation space of task sequencing with the exponential space-time configuration graph:", styles['BodyCustom']))

    math_box = (
        "Search Space Complexity = O( prod_{k=1}^M (N_k!) * |V|^M * T_max )\n\n"
        "For M = 16 robots each with capacity C = 7 tasks:\n"
        "(7!)^16 = (5,040)^16 approx 6.4 * 10^59 combinations at every single planning cycle!"
    )
    story.append(make_code_box(math_box, styles))
    story.append(Spacer(1, 8))

    story.append(Paragraph("3.2 The Decoupled Bi-Level Solution", styles['SectionHeader']))
    story.append(Paragraph("To achieve real-time responsiveness (<0.20 ms) on live warehouse AGV fleets, we decouple the problem into two specialized cooperating layers:", styles['BodyCustom']))

    # System Architecture Diagram
    if os.path.exists("system_architecture_diagram.png"):
        img = Image("system_architecture_diagram.png", width=510, height=349.7)
        story.append(img)
        story.append(Spacer(1, 6))
        story.append(Paragraph("<font size=7 color='#64748B'>Figure 2: Complete Bi-Level System Architecture. The Upper-Level Space-Time 2-Opt scheduler dispatches the active target G1, while the Lower-Level PBS/SIPP engine returns live clearance timestamps.</font>", styles['Normal']))

    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>Top-Down Dispatch:</b> The Upper Level dispatches the optimal active target G1 to the Lower Level.<br/>"
                           "<b>Bottom-Up Feedback Coupling:</b> The Lower Level planned paths provide live, exact clearance timestamps (t_clear) to the Upper Level. If an aisle is blocked by an ongoing 7-second pick, the upper level detects the stall and immediately pivots to an adjacent clear shelf.", styles['BodyCustom']))

    story.append(PageBreak())

    # ----------------------------------------------------
    # CHAPTER 4: UPPER-LEVEL SCHEDULING (MILP VS. 2-OPT)
    # ----------------------------------------------------
    story.append(Paragraph("Chapter 4: Upper-Level Task Scheduling: 2-Opt vs. Exact MILP", styles['ChapterHeader']))
    story.append(make_divider())

    story.append(Paragraph("4.1 Why the Traveling Repairman Problem (TRP) Instead of Standard TSP?", styles['SectionHeader']))
    story.append(Paragraph("In classic Traveling Salesperson Problem (TSP), the goal is to minimize total round-trip makespan (sum of edge distances). In automated fulfillment, that is the wrong metric! Customer order latency depends on the <b>Cumulative Arrival Time</b> (Flowtime) at which each individual item is retrieved:", styles['BodyCustom']))

    trp_math = "Objective: Minimize sum_{j=1}^N T_j  (where T_j is the arrival time at task j)"
    story.append(make_code_box(trp_math, styles))
    story.append(Spacer(1, 6))
    story.append(Paragraph("By optimizing the TRP objective, tasks visited early in the queue heavily reduce the sum, directly optimizing fleet responsiveness.", styles['BodyCustom']))

    story.append(Paragraph("4.2 The Exact Mixed-Integer Linear Programming (MILP) Formulation", styles['SectionHeader']))
    story.append(Paragraph("In <code>solve_milp_cli.py</code>, we implement the provably exact mathematical formulation using the Miller-Tucker-Zemlin (MTZ) subtour elimination model:", styles['BodyCustom']))

    milp_form = (
        "Decision Variables:\n"
        "  x_{i, j} in {0, 1}   : 1 if robot travels directly from node i to node j; 0 otherwise.\n"
        "  T_j >= 0            : Continuous arrival time timestamp at task j.\n\n"
        "Objective Function:\n"
        "  min sum_{j=1}^N T_j\n\n"
        "Constraints:\n"
        "  1. Start departure:   sum_{j=1}^N x_{0, j} = 1\n"
        "  2. Goal entry:        sum_{i=0, i!=j}^N x_{i, j} = 1       forall j in {1..N}\n"
        "  3. Goal departure:    sum_{j=1, j!=i}^N x_{i, j} <= 1      forall i in {1..N}\n"
        "  4. MTZ Subtour Elimination & Arrival Time Propagation (Linearized Big-M):\n"
        "     From origin:       T_j >= c_{0, j} - M * (1 - x_{0, j})  forall j in {1..N}\n"
        "     Between goals:     T_j >= T_i + c_{i, j} - M * (1 - x_{i, j})  forall i, j in {1..N}, i!=j"
    )
    story.append(make_code_box(milp_form, styles))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>How Big-M Linearization Works:</b> When x_{i,j} = 1, (1 - x_{i,j}) = 0, so the constraint activates: T_j >= T_i + c_{i,j}. When x_{i,j} = 0, the term -M relaxes the inequality completely. This eliminates sub-tours without needing exponential Dantzig-Fulkerson-Johnson constraints.", styles['BodyCustom']))

    story.append(Paragraph("4.3 The Space-Time 2-Opt Heuristic (<0.20 ms Latency)", styles['SectionHeader']))
    story.append(Paragraph("While exact MILP solves in ~45 ms for small queues, it fails at scale. In <code>KivaSystem.cpp</code>, we implement the Space-Time 2-Opt heuristic:", styles['BodyCustom']))
    story.append(Paragraph("1. <b>Nearest-Neighbor Seed:</b> Generates an initial greedy sequence in O(N^2).<br/>"
                           "2. <b>2-Opt Segment Reversal:</b> Systematically reverses sub-sequences (i to j) to untangle crossed routes.<br/>"
                           "3. <b>Dynamic Forward Cost Evaluator:</b> Queries the reservation table for actual projected teammate clearance wait times.", styles['BulletCustom']))

    story.append(PageBreak())

    # ----------------------------------------------------
    # CHAPTER 5: LOWER-LEVEL PBS & SIPP ENGINE
    # ----------------------------------------------------
    story.append(Paragraph("Chapter 5: Lower-Level Path Planning: Rolling-Horizon PBS & SIPP", styles['ChapterHeader']))
    story.append(make_divider())

    story.append(Paragraph("5.1 Rolling-Horizon Framework (RHCR)", styles['SectionHeader']))
    story.append(Paragraph("Planning over infinite time is impossible in real-time fleets. We use Rolling-Horizon Collision Resolution:", styles['BodyCustom']))
    story.append(Paragraph("• <b>Planning Window (W = 20 timesteps):</b> Computes collision-free trajectories for the next 20 seconds.<br/>"
                           "• <b>Execution Window (h = 5 timesteps):</b> Executes the first 5 seconds, updates world state, and replans.<br/>"
                           "• <b>Endpoint Holding:</b> Parked robots reserve their footprint up to W + Delta + 1 to prevent teammates from planning through stationary AGVs.", styles['BulletCustom']))
    story.append(Spacer(1, 8))

    story.append(Paragraph("5.2 Priority-Based Search (PBS) vs. Conflict-Based Search (CBS)", styles['SectionHeader']))
    story.append(Paragraph("A critical senior interview question is: <i>\"Why use PBS instead of CBS?\"</i>", styles['BodyCustom']))

    pbs_comp = [
        [Paragraph("Feature / Metric", styles['TableHeaderText']), Paragraph("Conflict-Based Search (CBS)", styles['TableHeaderText']), Paragraph("Priority-Based Search (PBS - Ours)", styles['TableHeaderText'])],
        [Paragraph("Branching Mechanism", styles['TableText']), Paragraph("Branches on individual vertex/edge constraints", styles['TableText']), Paragraph("Branches on relative agent priorities (A_i < A_j)", styles['TableText'])],
        [Paragraph("High-Level Tree Size", styles['TableText']), Paragraph("Explodes exponentially with dense footprints", styles['TableText']), Paragraph("Bounded by O(M!) depth; DFS search finds solutions rapidly", styles['TableText'])],
        [Paragraph("Corridor Thrashing", styles['TableText']), Paragraph("Severe thrashing due to symmetric footprint collisions", styles['TableText']), Paragraph("Prunes symmetry instantly by enforcing priority DAGs", styles['TableText'])],
        [Paragraph("Runtime in 16+ Fleets", styles['TableText']), Paragraph("Frequent timeouts (> 60 seconds)", styles['TableText']), Paragraph("Sub-second convergence (< 0.15 seconds)", styles['TableText'])],
    ]
    t_comp = Table(pbs_comp, colWidths=[120, 201, 201])
    t_comp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F294A")),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#94A3B8")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
    ]))
    story.append(t_comp)
    story.append(Spacer(1, 10))

    story.append(Paragraph("5.3 Safe Interval Path Planning (SIPP)", styles['SectionHeader']))
    story.append(Paragraph("Instead of expanding every discrete time tick (x, y, t) like standard Space-Time A*, SIPP partitions time into contiguous <b>safe intervals</b> [t_min, t_max) during which a cell has zero collisions. A single SIPP node expansion jumps across entire safe intervals, executing <b>10x faster</b> with 90% fewer node allocations.", styles['BodyCustom']))

    story.append(PageBreak())

    # ----------------------------------------------------
    # CHAPTER 6: C++ & BOOST MASTERCLASS FOR SYSTEMS SDE
    # ----------------------------------------------------
    story.append(Paragraph("Chapter 6: C++14 & Boost Masterclass for Systems Software Engineers", styles['ChapterHeader']))
    story.append(make_divider())

    story.append(Paragraph("6.1 Boost Libraries Architecture & Why std:: Was Not Enough", styles['SectionHeader']))
    story.append(Paragraph("In C++, developers use Boost when the standard <code>std::</code> library lacks specialized, production-grade data structures. Here is how our codebase uses Boost:", styles['BodyCustom']))

    boost_table = [
        [Paragraph("Boost Library Component", styles['TableHeaderText']), Paragraph("Where in Codebase", styles['TableHeaderText']), Paragraph("Why std:: Fails & Why Boost is Critical", styles['TableHeaderText'])],
        [Paragraph("boost::heap::fibonacci_heap", styles['TableText']), Paragraph("inc/SIPP.h, inc/common.h", styles['TableText']), Paragraph("std::priority_queue lacks decrease-key API. Boost provides persistent handle_type iterators for O(1) amortized key updates.", styles['TableText'])],
        [Paragraph("boost::graph::adjacency_list", styles['TableText']), Paragraph("inc/PriorityGraph.h", styles['TableText']), Paragraph("Models agent priority DAGs. Runs cycle detection and topological sorting to prune deadlocks.", styles['TableText'])],
        [Paragraph("boost::program_options", styles['TableText']), Paragraph("src/driver.cpp", styles['TableText']), Paragraph("Declarative, type-safe CLI parsing for 20+ simulation flags with automatic --help generation.", styles['TableText'])],
        [Paragraph("boost::filesystem", styles['TableText']), Paragraph("src/driver.cpp", styles['TableText']), Paragraph("Cross-platform path normalization and recursive folder creation (create_directories).", styles['TableText'])],
        [Paragraph("boost::tokenizer", styles['TableText']), Paragraph("src/KivaGraph.cpp", styles['TableText']), Paragraph("Zero-copy fast string splitting for parsing massive 57MB map distance files.", styles['TableText'])],
    ]
    t_boost = Table(boost_table, colWidths=[140, 110, 272])
    t_boost.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E3A8A")),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#94A3B8")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
    ]))
    story.append(t_boost)
    story.append(Spacer(1, 10))

    story.append(Paragraph("6.2 Deep Dive: Boost Fibonacci Heap with Persistent Handles", styles['SectionHeader']))
    story.append(Paragraph("In SIPPNode, we store a direct handle to the node inside the priority queue:", styles['BodyCustom']))

    fib_code = (
        "// In SIPP.h:\n"
        "boost::heap::fibonacci_heap<SIPPNode*, boost::heap::compare<compare_node>>::handle_type open_handle;\n\n"
        "// Pushing node into OPEN:\n"
        "node->open_handle = open_list.push(node);\n\n"
        "// When a cheaper path is discovered (Decrease-Key):\n"
        "node->g_val = new_cheaper_g;\n"
        "open_list.update(node->open_handle); // O(1) amortized update without reallocating!"
    )
    story.append(make_code_box(fib_code, styles))
    story.append(Spacer(1, 8))

    story.append(Paragraph("6.3 Modern C++ Performance & Memory Patterns in the Codebase", styles['SectionHeader']))
    story.append(Paragraph("• <b>Move Semantics (std::move):</b> In <code>KivaSystem.cpp</code> line 1425, reordered task deques are transferred using <code>bundle[k] = std::move(reordered);</code>, avoiding deep buffer copy allocations.<br/>"
                           "• <b>Stack Arrays vs. Heap Churn:</b> Geometric footprint functions pass fixed stack buffers <code>int out_cells[5]</code> by reference instead of returning <code>std::vector</code>, eliminating millions of malloc/free calls in the hot search loop.<br/>"
                           "• <b>Subprocess IPC via OS Pipes (_popen):</b> Mode 3 streams matrix costs to Python over stdout/stdin pipes via <code>_popen</code> and <code>_pclose</code>.", styles['BodyCustom']))

    story.append(PageBreak())

    # ----------------------------------------------------
    # CHAPTER 7: EMPIRICAL BENCHMARKS & VALIDATION
    # ----------------------------------------------------
    story.append(Paragraph("Chapter 7: Empirical Benchmarks & Mathematical Optimality Validation", styles['ChapterHeader']))
    story.append(make_divider())

    story.append(Paragraph("7.1 Master Fleet Benchmark (16 AGVs, 512 Shelves, 1,000s Horizon)", styles['SectionHeader']))
    
    bench_data = [
        [Paragraph("Config", styles['TableHeaderText']), Paragraph("Scheduling Policy", styles['TableHeaderText']), Paragraph("Active Goal G1", styles['TableHeaderText']), Paragraph("Completed Tasks", styles['TableHeaderText']), Paragraph("Throughput (tasks/s)", styles['TableHeaderText']), Paragraph("Improvement vs. Baseline", styles['TableHeaderText'])],
        [Paragraph("1", styles['TableText']), Paragraph("FIFO Baseline", styles['TableText']), Paragraph("Raw / Unordered", styles['TableText']), Paragraph("<b>524</b>", styles['TableText']), Paragraph("0.523", styles['TableText']), Paragraph("Baseline (0.0%)", styles['TableText'])],
        [Paragraph("2", styles['TableText']), Paragraph("Naive Distance TSP", styles['TableText']), Paragraph("Locked G1", styles['TableText']), Paragraph("<b>769</b>", styles['TableText']), Paragraph("0.768", styles['TableText']), Paragraph("+46.8%", styles['TableText'])],
        [Paragraph("3", styles['TableText']), Paragraph("Space-Time 2-Opt", styles['TableText']), Paragraph("Locked G1", styles['TableText']), Paragraph("<b>804</b>", styles['TableText']), Paragraph("0.803", styles['TableText']), Paragraph("+53.4%", styles['TableText'])],
        [Paragraph("4", styles['TableText']), Paragraph("Naive Distance TSP", styles['TableText']), Paragraph("Dynamic G1", styles['TableText']), Paragraph("<b>823</b>", styles['TableText']), Paragraph("0.822", styles['TableText']), Paragraph("+57.1%", styles['TableText'])],
        [Paragraph("5", styles['TableText']), Paragraph("<b>Dynamic Space-Time 2-Opt (Ours)</b>", styles['TableText']), Paragraph("<b>Dynamic G1</b>", styles['TableText']), Paragraph("<b>832</b>", styles['TableText']), Paragraph("<b>0.831</b>", styles['TableText']), Paragraph("<b>+58.8% (PEAK)</b>", styles['TableText'])],
    ]
    t_bench = Table(bench_data, colWidths=[40, 140, 75, 75, 82, 110])
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
    story.append(Spacer(1, 10))

    # Two benchmark plots side by side
    p1 = "plot1_planning_window.png"
    p4 = "plot4_fleet_scalability.png"
    if os.path.exists(p1) and os.path.exists(p4):
        img1 = Image(p1, width=255, height=208.6)
        img4 = Image(p4, width=255, height=165)
        t_plots = Table([[img1, img4]], colWidths=[261, 261])
        t_plots.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(t_plots)
        story.append(Spacer(1, 4))
        story.append(Paragraph("<font size=7 color='#64748B'>Figure 3: (Left) Planning Window Sensitivity (W=20 achieves peak throughput). (Right) Fleet Scalability vs. Throughput scaling linearly up to 50 robots.</font>", styles['Normal']))

    story.append(Spacer(1, 10))
    story.append(Paragraph("7.2 Rigorous 5,000s Mathematical Validation: Exact MILP vs. 2-Opt", styles['SectionHeader']))
    story.append(Paragraph("Evaluated across 904 actual warehouse tasks and 900 lifelong task re-ordering decisions:", styles['BodyCustom']))

    val_data = [
        [Paragraph("Validation Metric", styles['TableHeaderText']), Paragraph("Exact MILP (COIN-OR CBC Ground Truth)", styles['TableHeaderText']), Paragraph("Proposed C++ Space-Time 2-Opt Engine", styles['TableHeaderText']), Paragraph("Assessment / Significance", styles['TableHeaderText'])],
        [Paragraph("Tasks Evaluated", styles['TableText']), Paragraph("904 tasks", styles['TableText']), Paragraph("904 tasks", styles['TableText']), Paragraph("100% Identical Real Workload", styles['TableText'])],
        [Paragraph("Exact Sequence Match", styles['TableText']), Paragraph("900 / 900 (100.0%)", styles['TableText']), Paragraph("706 / 900 (78.44%)", styles['TableText']), Paragraph("78.44% Exact Route Match", styles['TableText'])],
        [Paragraph("Cumulative Distance", styles['TableText']), Paragraph("18,828.0 steps", styles['TableText']), Paragraph("19,687.0 steps", styles['TableText']), Paragraph("Accounts for physical turns & traffic", styles['TableText'])],
        [Paragraph("Optimality Gap", styles['TableText']), Paragraph("<b>0.00% (Provable Optimum)</b>", styles['TableText']), Paragraph("<b>4.56%</b>", styles['TableText']), Paragraph("<b>95.44% Mathematical Optimality!</b>", styles['TableText'])],
        [Paragraph("CPU Solving Runtime", styles['TableText']), Paragraph("40.185 seconds total", styles['TableText']), Paragraph("~0.180 seconds total", styles['TableText']), Paragraph("<b>> 220x Faster Execution</b>", styles['TableText'])],
        [Paragraph("Avg. Latency per Decision", styles['TableText']), Paragraph("44.65 milliseconds", styles['TableText']), Paragraph("<b>&lt; 0.20 milliseconds</b>", styles['TableText']), Paragraph("Sub-millisecond Real-Time Ready", styles['TableText'])],
    ]
    t_val = Table(val_data, colWidths=[120, 130, 132, 140])
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

    # ----------------------------------------------------
    # CHAPTER 8: ENGINEERING & DEBUGGING WAR STORIES
    # ----------------------------------------------------
    story.append(Paragraph("Chapter 8: Real Engineering & Debugging War Stories", styles['ChapterHeader']))
    story.append(make_divider())

    story.append(Paragraph("In senior SDE and systems interviews, interviewers evaluate how you debug production failures. Here are the 4 real bugs diagnosed and resolved in this codebase:", styles['BodyCustom']))

    bugs = [
        ("Story 1: The \"Silent Collision\" Iterator Invalidation Bug",
         "ReservationTable::updateSIT in ReservationTable.cpp",
         "Under dense robot traffic, robots were driving through each other without throwing any solver collision exception.",
         "In ReservationTable::updateSIT, an obsolete cleanup statement called ct.erase(it) while updating constraints. This silently deleted active hard spatial constraints from the table, making subsequent collision checks completely blind to existing robot trajectories.",
         "Removed ct.erase(it), guaranteeing that hard constraints persist across all planning windows."),

        ("Story 2: The \"Ghost State\" Copy Constructor Bug",
         "ReservationTable::copy() in ReservationTable.h",
         "During PBS search branching, robots were mysteriously stalling at timestep 35 and refusing to explore paths.",
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
        story.append(Paragraph(f"<b>{title}</b>", styles['SectionHeader']))
        story.append(Paragraph(f"<b>Location:</b> <code>{loc}</code>", styles['BodyCustom']))
        story.append(Paragraph(f"• <b>Symptom:</b> {sym}", styles['BulletCustom']))
        story.append(Paragraph(f"• <b>Root Cause:</b> {root}", styles['BulletCustom']))
        story.append(Paragraph(f"• <b>Engineering Fix:</b> {fix}", styles['BulletCustom']))
        story.append(Spacer(1, 4))

    story.append(PageBreak())

    # ----------------------------------------------------
    # CHAPTER 9: COMPREHENSIVE SDE TECHNICAL INTERVIEW Q&A
    # ----------------------------------------------------
    story.append(Paragraph("Chapter 9: Comprehensive SDE Technical Interview Q&A", styles['ChapterHeader']))
    story.append(make_divider())

    qas = [
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

    for q, a in qas:
        story.append(Paragraph(q, styles['QAQuestion']))
        story.append(Paragraph(a, styles['QAAnswer']))

    story.append(PageBreak())

    # ----------------------------------------------------
    # CHAPTER 10: CODEBASE DIRECTORY MAP & BUILD SYSTEM
    # ----------------------------------------------------
    story.append(Paragraph("Chapter 10: Codebase Architecture, File Map & Build System", styles['ChapterHeader']))
    story.append(make_divider())

    story.append(Paragraph("10.1 Complete Repository File Directory", styles['SectionHeader']))
    
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
    # Compact code box for file map
    lines_fm = [Paragraph(line.replace(" ", "&nbsp;"), ParagraphStyle('CodeCompact', parent=styles['CodeSnippet'], fontSize=7.0, leading=8.6)) for line in file_map.strip().split("\n")]
    t_fm = Table([[line] for line in lines_fm], colWidths=[522])
    t_fm.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    story.append(t_fm)
    story.append(Spacer(1, 4))

    story.append(Paragraph("10.2 Compilation & Execution Commands (PowerShell)", styles['SectionHeader']))
    build_cmds = (
        "# 1. Install required Boost packages via vcpkg:\n"
        "./vcpkg install boost-program-options:x64-windows boost-system:x64-windows boost-filesystem:x64-windows boost-heap:x64-windows boost-graph:x64-windows\n\n"
        "# 2. Configure and Build High-Performance Release Binary:\n"
        "cmake -S . -B build -A x64 -DCMAKE_TOOLCHAIN_FILE=\"vcpkg/scripts/buildsystems/vcpkg.cmake\" -DVCPKG_TARGET_TRIPLET=x64-windows\n"
        "cmake --build build --config Release\n\n"
        "# 3. Run Winner Configuration (Dynamic Space-Time 2-Opt - 832 Tasks):\n"
        "./build/Release/lifelong.exe --scenario KIVA --map kiva_4zone_shaved.map --agentNum 16 --solver PBS --simulation_time 1000 --output ./exp/bench_st_dynamic --rotation 1 --cutoffTime 100 --planning_window 20 --task_delay 7 --capacity_mode 1 --capacity 7 --safety_mode 1 --reorder_mode 2 --lock_active_goal 0 --seed 0"
    )
    lines_bc = [Paragraph(line.replace(" ", "&nbsp;"), ParagraphStyle('CodeCompact2', parent=styles['CodeSnippet'], fontSize=6.8, leading=8.4)) for line in build_cmds.strip().split("\n")]
    t_bc = Table([[line] for line in lines_bc], colWidths=[522])
    t_bc.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    story.append(t_bc)
    story.append(Spacer(1, 6))

    story.append(make_callout(
        "You now have complete, uncompromised, 360-degree technical command over this project. "
        "Whether asked about algorithmic complexity, C++ memory management, Boost internals, exact integer programming, "
        "or real-world debugging war stories, you have the exact numbers, diagrams, and code references to stand out as a top-tier systems engineer.",
        styles,
        title="FINAL INTERVIEW ADVICE"
    ))

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated {pdf_filename}!")

if __name__ == '__main__':
    generate_master_manual()
