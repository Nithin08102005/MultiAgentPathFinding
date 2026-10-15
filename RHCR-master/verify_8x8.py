map_path = "c:/Users/raoni/OneDrive/Desktop/GitHub - Copy/MAPF-with-multi-level-architecture/RHCR-master/kiva_8x8_4zone.map"
with open(map_path) as f:
    lines = f.read().splitlines()

dims = lines[0].split(',')
H, W = int(dims[0]), int(dims[1])
eps = int(lines[1])
r_cells = int(lines[2])
maxtime = int(lines[3])
grid = lines[4:]

print(f"H={H}, W={W}, eps={eps}, r_cells={r_cells}")
print(f"Actual grid lines: {len(grid)}")

assert len(grid) == H, f"len(grid) {len(grid)} != {H}"
for i, line in enumerate(grid):
    assert len(line) == W, f"Row {i} len {len(line)} != {W} (line: {line})"

actual_eps = sum(l.count('e') for l in grid)
actual_r = sum(l.count('r') for l in grid)
actual_shelves = sum(l.count('@') for l in grid)

print(f"Actual endpoints: {actual_eps} (expected {eps})")
print(f"Actual rest cells: {actual_r} (expected {r_cells})")
print(f"Actual shelf cells: {actual_shelves} (64 pods x 8 = 512)")
assert actual_eps == eps, f"eps mismatch: {actual_eps} != {eps}"
assert actual_r == r_cells, f"r mismatch: {actual_r} != {r_cells}"

# Check center detection
home_locs = []
for i in range(H):
    for j in range(W):
        c = grid[i][j]
        if c == 'r':
            if (j > 0 and j + 1 < W and grid[i][j-1] == 'r' and grid[i][j+1] == 'r' and (j < 2 or grid[i][j-2] != 'r')):
                home_locs.append((i, j, i * W + j))

print(f"Detected 3-cell bay centers: {len(home_locs)} (expected 52)")
assert len(home_locs) == 52, f"Expected 52 centers, got {len(home_locs)}"

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

print(f"Zone distribution: Zone 0={z_counts[0]}, Zone 1={z_counts[1]}, Zone 2={z_counts[2]}, Zone 3={z_counts[3]}")
assert z_counts == [13, 13, 13, 13], f"Zone mismatch: {z_counts}"
print("ALL ASSERTIONS PASSED! Map is 100% mathematically valid!")
