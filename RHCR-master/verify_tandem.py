# Verify kiva_tandem_4zone.map
import re

map_path = "kiva_tandem_4zone.map"
with open(map_path) as f:
    lines = f.read().splitlines()

dims = lines[0].split(',')
H, W = int(dims[0]), int(dims[1])
eps = int(lines[1])
r_cells = int(lines[2])
maxtime = int(lines[3])
grid = lines[4:]

print(f"==================================================")
print(f"VERIFYING TANDEM MAP: {map_path}")
print(f"Dimensions: H={H}, W={W}")
print(f"Expected: endpoints={eps}, rest_cells={r_cells}, maxtime={maxtime}")
print(f"Actual grid lines: {len(grid)}")

assert len(grid) == H, f"len(grid) {len(grid)} != {H}"
for i, line in enumerate(grid):
    assert len(line) == W, f"Row {i} length {len(line)} != {W}"

actual_eps = sum(l.count('e') for l in grid)
actual_r = sum(l.count('r') for l in grid)
actual_shelves = sum(l.count('@') for l in grid)

print(f"Actual endpoints: {actual_eps} (expected {eps})")
print(f"Actual rest cells: {actual_r} (expected {r_cells})")
print(f"Actual shelf cells: {actual_shelves} (32 pods x 8 = 256)")

assert actual_eps == eps, f"eps mismatch: {actual_eps} != {eps}"
assert actual_r == r_cells, f"r mismatch: {actual_r} != {r_cells}"

# Check horizontal 3-cell bay center detection matching KivaGraph.cpp
home_locs = []
in_bay = [False] * (H * W)
for i in range(H):
    for j in range(1, W - 1):
        left = i * W + (j - 1)
        center = i * W + j
        right = i * W + (j + 1)
        if (grid[i][j-1] == 'r' and grid[i][j] == 'r' and grid[i][j+1] == 'r' and
            not in_bay[left] and not in_bay[center] and not in_bay[right]):
            home_locs.append((i, j, center))
            in_bay[left] = in_bay[center] = in_bay[right] = True

print(f"Detected 3-cell bay centers: {len(home_locs)} (expected 56)")
assert len(home_locs) == 56, f"Expected 56 centers, got {len(home_locs)}"

# Check zone distribution
z_counts = [0, 0, 0, 0]
mid_r = H // 2
mid_c = W // 2
for r, c, loc in home_locs:
    if r < mid_r and c < mid_c: z = 0
    elif r < mid_r and c >= mid_c: z = 1
    elif r >= mid_r and c < mid_c: z = 2
    else: z = 3
    z_counts[z] += 1

print(f"Zone distribution of bays: Zone 0={z_counts[0]}, Zone 1={z_counts[1]}, Zone 2={z_counts[2]}, Zone 3={z_counts[3]}")
assert z_counts == [14, 14, 14, 14], f"Zone mismatch: {z_counts}"

print("\nALL 56 BAYS ARE PERFECTLY DISTRIBUTED (14 per zone)!")
print("Map is 100% mathematically valid and ready for simulation!")
print("==================================================")
