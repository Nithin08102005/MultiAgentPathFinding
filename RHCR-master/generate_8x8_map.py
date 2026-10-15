import matplotlib.pyplot as plt
import numpy as np

def generate():
    W = 101
    H = 37

    # Templates
    row_empty = "." * W
    row_endpoints = "........" + ("eeeeeeee..." * 3) + "eeeeeeee" + "..." + ("eeeeeeee..." * 3) + "eeeeeeee" + "........"
    row_racks = ".rrr...." + ("@@@@@@@@..." * 3) + "@@@@@@@@" + "..." + ("@@@@@@@@..." * 3) + "@@@@@@@@" + "....rrr."
    row_corridor = ".rrr...." + ("." * 85) + "....rrr."

    # Top/Bottom bays row
    z0_bays = "....rrr....rrr....rrr.....rrr....rrr....rrr......" # 49 chars (cols 0..48)
    mid_sep = "..."                                            # 3 chars (cols 49..51)
    z1_bays = "......rrr....rrr....rrr.....rrr....rrr....rrr...." # 49 chars (cols 52..100)
    row_bays = z0_bays + mid_sep + z1_bays
    assert len(row_bays) == W, f"row_bays len {len(row_bays)} != {W}"
    assert len(row_endpoints) == W, f"row_endpoints len {len(row_endpoints)} != {W}"
    assert len(row_racks) == W, f"row_racks len {len(row_racks)} != {W}"
    assert len(row_corridor) == W, f"row_corridor len {len(row_corridor)} != {W}"

    lines = []
    # Row 0: Top wall border
    lines.append(row_empty)
    # Row 1: Top parking bays
    lines.append(row_bays)
    # Row 2: Top open perimeter highway
    lines.append(row_empty)

    # Top Half: 4 rack tiers (Rows 3..17)
    # Tier 1
    lines.append(row_endpoints) # Row 3
    lines.append(row_racks)     # Row 4 (side bays)
    lines.append(row_endpoints) # Row 5
    # Corridor 1
    lines.append(row_corridor)  # Row 6 (side bays)
    # Tier 2
    lines.append(row_endpoints) # Row 7
    lines.append(row_racks)     # Row 8 (side bays)
    lines.append(row_endpoints) # Row 9
    # Corridor 2
    lines.append(row_corridor)  # Row 10 (side bays)
    # Tier 3
    lines.append(row_endpoints) # Row 11
    lines.append(row_racks)     # Row 12 (side bays)
    lines.append(row_endpoints) # Row 13
    # Corridor 3
    lines.append(row_corridor)  # Row 14 (side bays)
    # Tier 4
    lines.append(row_endpoints) # Row 15
    lines.append(row_racks)     # Row 16 (side bays)
    lines.append(row_endpoints) # Row 17

    # Central Cross-Quadrant Highway
    lines.append(row_empty)     # Row 18

    # Bottom Half: 4 rack tiers (Rows 19..33)
    # Tier 5
    lines.append(row_endpoints) # Row 19
    lines.append(row_racks)     # Row 20 (side bays)
    lines.append(row_endpoints) # Row 21
    # Corridor 4
    lines.append(row_corridor)  # Row 22 (side bays)
    # Tier 6
    lines.append(row_endpoints) # Row 23
    lines.append(row_racks)     # Row 24 (side bays)
    lines.append(row_endpoints) # Row 25
    # Corridor 5
    lines.append(row_corridor)  # Row 26 (side bays)
    # Tier 7
    lines.append(row_endpoints) # Row 27
    lines.append(row_racks)     # Row 28 (side bays)
    lines.append(row_endpoints) # Row 29
    # Corridor 6
    lines.append(row_corridor)  # Row 30 (side bays)
    # Tier 8
    lines.append(row_endpoints) # Row 31
    lines.append(row_racks)     # Row 32 (side bays)
    lines.append(row_endpoints) # Row 33

    # Row 34: Bottom open perimeter highway
    lines.append(row_empty)
    # Row 35: Bottom parking bays
    lines.append(row_bays)
    # Row 36: Bottom wall border
    lines.append(row_empty)

    assert len(lines) == H, f"Total rows {len(lines)} != {H}"

    # Count statistics
    endpoints = sum(row.count('e') for row in lines)
    r_cells = sum(row.count('r') for row in lines)
    bays = r_cells // 3
    shelves = sum(row.count('@') for row in lines)

    print(f"Generated map: {H} rows x {W} cols")
    print(f"  Endpoints: {endpoints}")
    print(f"  Shelves: {shelves} (64 pods of 8 cells)")
    print(f"  Rest cells: {r_cells} ({bays} bays = {bays // 4} per zone)")

    # Write map file
    map_path = "kiva_8x8_4zone.map"
    with open(map_path, "w") as f:
        f.write(f"{H},{W}\n")
        f.write(f"{endpoints}\n")
        f.write(f"{r_cells}\n")
        f.write("5000\n")
        for line in lines:
            f.write(line + "\n")
    print(f"Saved map to {map_path}")

    # Render Preview PNG
    bg = np.ones((H, W, 3))
    for y in range(H):
        for x in range(W):
            c = lines[y][x]
            if c == '@': bg[y, x] = [0.6, 0.4, 0.2]  # Brown
            elif c == 'e': bg[y, x] = [1.0, 0.6, 0.0]  # Orange
            elif c == 'r': bg[y, x] = [0.15, 0.55, 1.0] # Blue
            elif c == '.': bg[y, x] = [0.96, 0.96, 0.96]

    fig, ax = plt.subplots(figsize=(18, 9))
    ax.imshow(bg, aspect='equal')
    ax.set_title(f"Symmetrical 8x8 Kiva Warehouse (37 rows x 101 cols) - 4x4 Racks per Zone | 52 Bays | 1024 Endpoints", 
                 fontsize=14, fontweight='bold')
    
    mid_y = H // 2
    mid_x = W // 2
    ax.axhline(mid_y, color='red', linestyle='--', alpha=0.6, linewidth=1.5)
    ax.axvline(mid_x, color='red', linestyle='--', alpha=0.6, linewidth=1.5)

    ax.text(mid_x * 0.5, mid_y * 0.5, "ZONE 0 (Top-Left)\n4x4 Racks (16 pods)\n13 Bays | 256 Endpoints", 
            fontsize=11, fontweight='bold', color='darkblue', ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.88, edgecolor='blue'))
    ax.text(mid_x * 1.5, mid_y * 0.5, "ZONE 1 (Top-Right)\n4x4 Racks (16 pods)\n13 Bays | 256 Endpoints", 
            fontsize=11, fontweight='bold', color='darkgreen', ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.88, edgecolor='green'))
    ax.text(mid_x * 0.5, mid_y * 1.5, "ZONE 2 (Bottom-Left)\n4x4 Racks (16 pods)\n13 Bays | 256 Endpoints", 
            fontsize=11, fontweight='bold', color='darkorange', ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.88, edgecolor='orange'))
    ax.text(mid_x * 1.5, mid_y * 1.5, "ZONE 3 (Bottom-Right)\n4x4 Racks (16 pods)\n13 Bays | 256 Endpoints", 
            fontsize=11, fontweight='bold', color='purple', ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.88, edgecolor='purple'))

    ax.set_xticks([])
    ax.set_yticks([])
    plt.tight_layout()
    preview_path = "kiva_8x8_4zone_preview.png"
    plt.savefig(preview_path, dpi=200, bbox_inches='tight')
    print(f"Saved preview to {preview_path}")

if __name__ == '__main__':
    generate()
