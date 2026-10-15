import os
import sys

def analyze_tandem_map():
    map_file = "kiva_tandem_4zone.map"
    if not os.path.exists(map_file):
        print(f"Error: {map_file} not found.")
        return

    with open(map_file, "r") as f:
        lines = [l.rstrip("\r\n") for l in f if l.strip()]

    header = lines[0]
    rows, cols = map(int, header.split(","))
    grid = lines[4:]
    print(f"==================================================")
    print(f"Map: {map_file}")
    print(f"Dimensions: {rows} rows x {cols} cols (Expected: 35 x 73)")
    print(f"Grid lines read: {len(grid)}")

    for idx, r in enumerate(grid):
        if len(r) != cols:
            print(f"Error on line {idx+5}: length is {len(r)}, expected {cols}")
            return
    print(f"[OK] All {rows} rows have exactly {cols} columns.")

    # Emulate KivaGraph.cpp bay detection exactly
    in_bay = [False] * (rows * cols)
    bays = []

    for i in range(rows):
        for j in range(1, cols - 1):
            left = i * cols + (j - 1)
            center = i * cols + j
            right = i * cols + (j + 1)
            if (grid[i][j-1] == 'r' and grid[i][j] == 'r' and grid[i][j+1] == 'r' and
                not in_bay[left] and not in_bay[center] and not in_bay[right]):
                bays.append((i, j, center))
                in_bay[left] = in_bay[center] = in_bay[right] = True

    print(f"[OK] Total 3-cell bays detected by KivaGraph: {len(bays)} bays")
    print(f"     (Sufficient for 50 robots? {'YES' if len(bays) >= 50 else 'NO'})")

    # Group by row
    row_bays = {}
    for r, c, idx in bays:
        row_bays.setdefault(r, []).append(c)

    print(f"\nRow-by-row Bay Center Columns:")
    for r, cols_list in sorted(row_bays.items()):
        print(f"  Row {r:2d}: cols {cols_list} ({len(cols_list)} bays in this row)")

    # Prepare config file
    config_content = f"""map={map_file}
agents=50
team_size=50
simulation_time=100
planning_window=5
potential_function=NONE
potential_threshold=0
capacity_mode=1
default_agent_capacity=4
task_delay=0
randomize_sequences=1
seed=0
output=tandem_50_test.csv
log=tandem_50_test.log
"""
    with open("config_tandem.txt", "w", newline="\n") as f:
        f.write(config_content)
    print(f"\n[OK] Created config_tandem.txt ready for simulation.")
    print(f"==================================================")

if __name__ == "__main__":
    analyze_tandem_map()
