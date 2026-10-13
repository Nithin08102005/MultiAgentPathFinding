import subprocess
import os
import re
import sys

def run_simulation(map_file, agents, flexibility, output_dir, sim_time=100):
    cmd = [
        r".\build\Release\lifelong.exe",
        "--scenario", "KIVA",
        "-m", map_file,
        "-k", str(agents),
        "--simulation_time", str(sim_time),
        "--simulation_window", "5",
        "--planning_window", "5",
        "--solver", "PBS",
        "--capacity_mode", "1",
        "--capacity", "4",
        "--safety_mode", "1",
        "--reorder_mode", "2",
        "--zone_flexibility", str(flexibility),
        "-o", output_dir,
        "-s", "1"
    ]
    
    print(f"\n=======================================================")
    print(f"Running: alpha = {flexibility} ({'Strict' if flexibility == 0.0 else 'Hybrid' if flexibility < 1.0 else 'Full Flexible'})")
    print(f"Command: {' '.join(cmd)}")
    print(f"=======================================================")
    
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    out_lines = []
    for line in p.stdout:
        print(line, end="")
        out_lines.append(line)
    p.wait()
    
    output_text = "".join(out_lines)
    
    # Extract tasks finished
    tasks = None
    m = re.search(r"finished tasks:\s*(\d+)", output_text, re.IGNORECASE)
    if m:
        tasks = int(m.group(1))
    else:
        m2 = re.search(r"(\d+)\s+tasks", output_text, re.IGNORECASE)
        if m2:
            tasks = int(m2.group(1))
            
    # Extract runtime
    runtime = None
    m_rt = re.search(r"Wall-Clock Runtime.*?:\s*([\d\.]+)\s*seconds", output_text)
    if m_rt:
        runtime = float(m_rt.group(1))
        
    return tasks, runtime

def analyze_cross_zone_movements(paths_file, map_file):
    if not os.path.exists(paths_file):
        return 0, 0
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
        
    # Read paths
    zone_crossings = 0
    with open(paths_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or ":" not in line:
                continue
            parts = line.split(":", 1)[1].strip()
            # tokens: (loc, orient)
            matches = re.findall(r"\((\d+),\s*(-?\d+)\)", parts)
            if not matches:
                continue
            prev_z = None
            for loc_str, _ in matches:
                loc = int(loc_str)
                z = get_zone(loc)
                if prev_z is not None and z != prev_z:
                    zone_crossings += 1
                prev_z = z
                
    return zone_crossings

if __name__ == "__main__":
    map_name = "kiva_8x8_4zone.map"
    agents = 20
    sim_time = 100
    
    results = []
    for alpha in [0.0, 0.3, 1.0]:
        out_dir = f"exp/test_alpha_{str(alpha).replace('.', '_')}"
        tasks, rt = run_simulation(map_name, agents, alpha, out_dir, sim_time)
        crossings = analyze_cross_zone_movements(f"{out_dir}/paths.txt", map_name)
        results.append({
            "alpha": alpha,
            "tasks": tasks,
            "runtime": rt,
            "crossings": crossings
        })
        
    print("\n\n" + "=" * 65)
    print("           ZONE FLEXIBILITY COMPARISON RESULTS           ")
    print("=" * 65)
    print(f"{'Alpha':<8} | {'Mode':<18} | {'Tasks':<8} | {'Throughput':<12} | {'Inter-Zone Crossings'}")
    print("-" * 65)
    for r in results:
        mode_str = "Strict (0.0)" if r["alpha"] == 0.0 else "Hybrid (0.3)" if r["alpha"] == 0.3 else "Full (1.0)"
        th = f"{r['tasks']/sim_time:.3f} t/step" if r['tasks'] else "N/A"
        print(f"{r['alpha']:<8.1f} | {mode_str:<18} | {str(r['tasks']):<8} | {th:<12} | {r['crossings']}")
    print("=" * 65)
