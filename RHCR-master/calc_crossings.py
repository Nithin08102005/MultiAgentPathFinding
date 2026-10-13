import os

map_file = "kiva_8x8_4zone.map"
with open(map_file, "r") as f:
    lines = [l.rstrip("\r\n") for l in f if l.strip()]
rows, cols = map(int, lines[0].split(","))
mid_r = rows // 2
mid_c = cols // 2

def get_zone(loc):
    r = loc // cols
    c = loc % cols
    if r < mid_r and c < mid_c: return 0
    if r < mid_r and c >= mid_c: return 1
    if r >= mid_r and c < mid_c: return 2
    return 3

for alpha_str in ["0_0", "0_3", "1_0"]:
    paths_file = f"exp/test_alpha_{alpha_str}/paths.txt"
    if not os.path.exists(paths_file):
        continue
    crossings = 0
    robot_crossings = {}
    with open(paths_file, "r") as f:
        lines = f.readlines()
    # Line 0 is agent count, subsequent lines are agent paths
    for agent_id, line in enumerate(lines[1:]):
        line = line.strip()
        if not line:
            continue
        steps = line.split(";")
        prev_z = None
        agent_cross = 0
        for step in steps:
            if not step or "," not in step:
                continue
            parts = step.split(",")
            loc = int(parts[0])
            z = get_zone(loc)
            if prev_z is not None and z != prev_z:
                crossings += 1
                agent_cross += 1
            prev_z = z
        if agent_cross > 0:
            robot_crossings[agent_id] = agent_cross
            
    print(f"Alpha {alpha_str.replace('_', '.')}:")
    print(f"  Total inter-zone boundary crossings: {crossings}")
    print(f"  Robots that crossed zones: {len(robot_crossings)} / 20")
    if robot_crossings:
        print(f"  Breakdown by agent: {robot_crossings}")
