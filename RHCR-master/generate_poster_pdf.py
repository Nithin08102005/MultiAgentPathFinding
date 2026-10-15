import os
import pymupdf

def generate_poster(
    student_name="Nithin Rao",
    roll_number="2200020XX",
    supervisor_name="Dr. [Supervisor Name]",
    output_pdf="BTech_Project_Poster_MAPF.pdf",
    output_png="BTech_Project_Poster_MAPF.png"
):
    PAGE_W = 595.5
    PAGE_H = 842.25

    doc = pymupdf.open()
    page = doc.new_page(width=PAGE_W, height=PAGE_H)

    # 1. Background image
    bg_rect = pymupdf.Rect(-9.0, -34.5, 604.7, 877.1)
    page.insert_image(bg_rect, filename="poster_assets/bg.jpeg")

    # Standard colors
    c_blue = (24/255, 0, 173/255)  # #1800ad
    c_black = (0, 0, 0)
    c_white = (1, 1, 1)

    # 2. Header: Title
    page.insert_text(
        pymupdf.Point(PAGE_W / 2 - 250, 40.0),
        "Traffic-Aware Task Reordering and Bi-Level Architecture",
        fontname="hebo",
        fontsize=19.0,
        color=c_blue
    )
    page.insert_text(
        pymupdf.Point(PAGE_W / 2 - 165, 64.0),
        "for Lifelong Multi-Agent Path Finding",
        fontname="hebo",
        fontsize=19.0,
        color=c_blue
    )

    # 3. Author & Supervisor
    # Student on Left
    page.insert_text(pymupdf.Point(60.0, 114.0), student_name, fontname="hebo", fontsize=14.5, color=c_black)
    page.insert_text(pymupdf.Point(60.0, 134.0), roll_number, fontname="hebo", fontsize=14.5, color=c_black)

    # Supervisor on Right
    # Calculate text width to right-align properly
    sup_width = pymupdf.get_text_length(supervisor_name, fontname="hebo", fontsize=14.5)
    page.insert_text(pymupdf.Point(545.0 - sup_width, 114.0), supervisor_name, fontname="hebo", fontsize=14.5, color=c_black)

    # Divider bar
    shape = page.new_shape()
    shape.draw_line(pymupdf.Point(40.0, 144.0), pymupdf.Point(555.0, 144.0))
    shape.finish(color=c_black, width=2.0)
    shape.commit()

    # 4. Central Showcase Box
    frame_rect = pymupdf.Rect(39.3, 154.0, 556.2, 442.0)
    page.insert_image(frame_rect, filename="poster_assets/white_frame.png")

    fig_rect = pymupdf.Rect(43.5, 158.0, 552.0, 438.0)
    page.insert_image(fig_rect, filename="poster_assets/showcase_figure.png")

    # 5. Core Overview Paragraph (Centered below figure)
    summary_rect = pymupdf.Rect(20.0, 448.0, 575.0, 514.0)
    summary_text = (
        "A bi-level multi-agent path finding (MAPF) architecture integrating rolling-horizon "
        "collision resolution (RHCR) with traffic-aware task reordering is developed for automated "
        "warehouse logistics. By combining exact MTZ-MILP and microsecond Space-Time 2-Opt heuristics "
        "with Priority-Based Search, the framework eliminates corridor congestion and maximizes lifelong picking throughput."
    )
    page.insert_textbox(
        summary_rect,
        summary_text,
        fontname="hebo",
        fontsize=12.2,
        color=c_blue,
        align=pymupdf.TEXT_ALIGN_CENTER
    )

    # 6. Cards & Badges
    # --- Card 1 (Green) ---
    page.insert_image(pymupdf.Rect(30.9, 519.3, 272.5, 577.1), filename="poster_assets/pill_green_1.png")
    page.insert_image(pymupdf.Rect(27.1, 518.6, 84.9, 576.4), filename="poster_assets/badge_1.png")
    page.insert_text(pymupdf.Point(45.0, 560.0), "1", fontname="hebo", fontsize=37.0, color=c_white)
    page.insert_text(pymupdf.Point(86.0, 534.0), "Introduction/Motivation", fontname="hebo", fontsize=12.8, color=c_white)
    
    c1_body = (
        "Multi-agent warehouse robotics suffers severe throughput loss and corridor "
        "deadlocks under naive FIFO dispatching due to spatial conflicts in narrow picking aisles."
    )
    page.insert_textbox(pymupdf.Rect(85.0, 537.0, 268.0, 574.0), c1_body, fontname="hebo", fontsize=6.8, color=c_black)

    # --- Card 2 (Blue) ---
    page.insert_image(pymupdf.Rect(30.9, 589.2, 272.5, 647.0), filename="poster_assets/pill_blue_2.png")
    page.insert_image(pymupdf.Rect(27.1, 589.2, 84.9, 647.0), filename="poster_assets/badge_2.png")
    page.insert_text(pymupdf.Point(45.0, 630.0), "2", fontname="hebo", fontsize=37.0, color=c_white)
    page.insert_text(pymupdf.Point(82.0, 604.0), "Problem Statement & Objective", fontname="hebo", fontsize=11.2, color=c_white)

    c2_body = (
        "To design a scalable bi-level MAPF framework that dynamically sequences shelf-picking "
        "bundles, balances fleet traffic, and guarantees 100% collision-free lifelong navigation."
    )
    page.insert_textbox(pymupdf.Rect(85.0, 607.0, 268.0, 644.0), c2_body, fontname="hebo", fontsize=6.8, color=c_black)

    # --- Card 3 (Yellow) ---
    page.insert_image(pymupdf.Rect(30.9, 659.1, 272.5, 716.9), filename="poster_assets/pill_yellow_3.png")
    page.insert_image(pymupdf.Rect(27.1, 659.0, 84.9, 716.8), filename="poster_assets/badge_3.png")
    page.insert_text(pymupdf.Point(45.0, 700.0), "3", fontname="hebo", fontsize=37.0, color=c_white)
    page.insert_text(pymupdf.Point(86.0, 674.0), "Methodology/Approach", fontname="hebo", fontsize=12.8, color=c_white)

    c3_body = (
        "Combines RHCR rolling horizons with MTZ-MILP and Space-Time 2-Opt local search "
        "on reservation heatmaps, coordinated via Priority-Based Search (PBS) and SIPP."
    )
    page.insert_textbox(pymupdf.Rect(85.0, 677.0, 268.0, 714.0), c3_body, fontname="hebo", fontsize=6.8, color=c_black)

    # --- Vertical Divider ---
    page.insert_image(pymupdf.Rect(303.2, 518.6, 306.2, 722.7), filename="poster_assets/divider.png")

    # --- Card 4 (Orange) ---
    page.insert_image(pymupdf.Rect(327.1, 549.6, 568.7, 607.4), filename="poster_assets/pill_orange_4.png")
    page.insert_image(pymupdf.Rect(323.3, 549.2, 381.1, 606.9), filename="poster_assets/badge_4.png")
    page.insert_text(pymupdf.Point(340.0, 590.0), "4", fontname="hebo", fontsize=37.0, color=c_white)
    page.insert_text(pymupdf.Point(382.0, 564.0), "Results & Findings", fontname="hebo", fontsize=12.8, color=c_white)

    c4_body = (
        "Achieves 524 tasks (MILP upper bound) and 504 tasks (2-Opt) with an 87.9 us "
        "reordering speed (7,829x speedup), boosting fleet throughput by +63.4% with zero starvation."
    )
    page.insert_textbox(pymupdf.Rect(382.0, 567.0, 565.0, 604.0), c4_body, fontname="hebo", fontsize=6.8, color=c_black)

    # --- Card 5 (Purple) ---
    page.insert_image(pymupdf.Rect(327.1, 619.5, 568.7, 677.3), filename="poster_assets/pill_purple_5.png")
    page.insert_image(pymupdf.Rect(323.3, 619.7, 381.1, 677.5), filename="poster_assets/badge_5.png")
    page.insert_text(pymupdf.Point(340.0, 660.0), "5", fontname="hebo", fontsize=37.0, color=c_white)
    page.insert_text(pymupdf.Point(382.0, 634.0), "Conclusion & Impact", fontname="hebo", fontsize=12.8, color=c_white)

    c5_body = (
        "Demonstrates real-time industrial tractability and provable conflict elimination, "
        "enabling high-density autonomous fulfillment centers with zero deadlocks."
    )
    page.insert_textbox(pymupdf.Rect(382.0, 637.0, 565.0, 674.0), c5_body, fontname="hebo", fontsize=6.8, color=c_black)

    # 7. Keywords Bar
    page.insert_image(pymupdf.Rect(20.5, 744.1, 585.5, 801.2), filename="poster_assets/keywords_bar.png")
    page.insert_text(pymupdf.Point(44.0, 776.0), "Keywords:", fontname="hebo", fontsize=13.0, color=c_white)

    # Keywords chip list
    kw_list = [
        "Multi-Agent Path Finding",
        "Rolling Horizon (RHCR)",
        "Space-Time 2-Opt",
        "MTZ-MILP",
        "Warehouse Robotics"
    ]

    kw_shape = page.new_shape()
    start_x = 120.0
    for kw in kw_list:
        kw_w = pymupdf.get_text_length(kw, fontname="hebo", fontsize=8.0) + 12.0
        chip_rect = pymupdf.Rect(start_x, 763.0, start_x + kw_w, 779.0)
        kw_shape.draw_rect(chip_rect, radius=0.25)
        kw_shape.finish(fill=c_white, color=(0.7, 0.7, 0.7), width=0.5)
        start_x += kw_w + 5.0
    kw_shape.commit()

    # Draw text in chips
    start_x = 120.0
    for kw in kw_list:
        kw_w = pymupdf.get_text_length(kw, fontname="hebo", fontsize=8.0) + 12.0
        page.insert_text(
            pymupdf.Point(start_x + 6.0, 774.5),
            kw,
            fontname="hebo",
            fontsize=8.0,
            color=c_black
        )
        start_x += kw_w + 5.0

    # Save PDF and high-res PNG
    doc.save(output_pdf)
    print(f"Generated PDF: {output_pdf}")

    pix = page.get_pixmap(dpi=300)
    pix.save(output_png)
    print(f"Generated PNG: {output_png} ({pix.width}x{pix.height})")

if __name__ == "__main__":
    generate_poster()
