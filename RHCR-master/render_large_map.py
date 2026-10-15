import matplotlib.pyplot as plt
import numpy as np

map_file = "c:/Users/raoni/OneDrive/Desktop/GitHub - Copy/MAPF-with-multi-level-architecture/RHCR-master/kiva_8x8_4zone.map"
output_file = "c:/Users/raoni/OneDrive/Desktop/GitHub - Copy/MAPF-with-multi-level-architecture/RHCR-master/kiva_8x8_4zone_preview.png"

with open(map_file, 'r') as f:
    lines = f.read().splitlines()

dims = lines[0].strip().split(',')
H, W = int(dims[0]), int(dims[1])
grid = lines[4:]

bg = np.ones((H, W, 3))
for y in range(H):
    for x in range(W):
        c = grid[y][x]
        if c == '@': bg[y, x] = [0.55, 0.35, 0.15] # Brown shelves
        elif c == 'e': bg[y, x] = [1.0, 0.6, 0.0]  # Orange endpoints
        elif c == 'r': bg[y, x] = [0.15, 0.55, 1.0] # Blue rest stations
        elif c == '.': bg[y, x] = [0.96, 0.96, 0.96] # Light gray aisles

fig, ax = plt.subplots(figsize=(18, 8))
ax.imshow(bg, aspect='equal')
ax.set_title(f"Symmetrical 8x8 Kiva Map (37 rows x 101 cols) - 4x4 Racks per Zone | 52 Bays | 1024 Endpoints", 
             fontsize=14, fontweight='bold')

mid_y = H // 2
mid_x = W // 2
ax.axhline(mid_y, color='red', linestyle='--', alpha=0.6, linewidth=1.5)
ax.axvline(mid_x, color='red', linestyle='--', alpha=0.6, linewidth=1.5)

ax.text(mid_x * 0.5, mid_y * 0.5, "ZONE 0 (Top-Left)\n4x4 Racks (16 pods)\n13 Bays (7 Side + 6 Top)", 
        fontsize=11, fontweight='bold', color='darkblue', ha='center', va='center',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, edgecolor='blue'))
ax.text(mid_x * 1.5, mid_y * 0.5, "ZONE 1 (Top-Right)\n4x4 Racks (16 pods)\n13 Bays (7 Side + 6 Top)", 
        fontsize=11, fontweight='bold', color='darkgreen', ha='center', va='center',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, edgecolor='green'))
ax.text(mid_x * 0.5, mid_y * 1.5, "ZONE 2 (Bottom-Left)\n4x4 Racks (16 pods)\n13 Bays (7 Side + 6 Bottom)", 
        fontsize=11, fontweight='bold', color='darkorange', ha='center', va='center',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, edgecolor='orange'))
ax.text(mid_x * 1.5, mid_y * 1.5, "ZONE 3 (Bottom-Right)\n4x4 Racks (16 pods)\n13 Bays (7 Side + 6 Bottom)", 
        fontsize=11, fontweight='bold', color='purple', ha='center', va='center',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, edgecolor='purple'))

ax.set_xticks([])
ax.set_yticks([])
plt.tight_layout()
plt.savefig(output_file, dpi=200, bbox_inches='tight')
print(f"Saved preview to {output_file}")
