import os
import sys

def evaluate_run():
    log_file = "tandem_50_test.log"
    csv_file = "tandem_50_test.csv"

    if not os.path.exists(log_file):
        print(f"Log file '{log_file}' not found. Please run the simulation first:")
        print(r".\build\Release\lifelong.exe --config config_tandem.txt")
        return

    print("==================================================")
    print("        TANDEM MAP SIMULATION EVALUATION          ")
    print("==================================================")

    with open(log_file, "r") as f:
        log_lines = f.readlines()

    tasks_completed = None
    runtime = None
    deadlocks = 0

    for line in log_lines:
        line_s = line.strip()
        if "finished tasks" in line_s or "tasks completed" in line_s:
            tasks_completed = line_s
        if "Runtime" in line_s or "CPU time" in line_s:
            runtime = line_s
        if "failed" in line_s.lower() or "deadlock" in line_s.lower():
            deadlocks += 1

    print(f"Log summary:")
    print(f"  Total log lines: {len(log_lines)}")
    if tasks_completed:
        print(f"  Tasks: {tasks_completed}")
    if runtime:
        print(f"  Runtime: {runtime}")
    print(f"  Failures/Deadlocks detected: {deadlocks}")

    if os.path.exists(csv_file):
        with open(csv_file, "r") as f:
            csv_lines = f.readlines()
        print(f"\nCSV Results ({csv_file}):")
        for line in csv_lines[:10]:
            print(f"  {line.strip()}")
    
    print("==================================================")

if __name__ == "__main__":
    evaluate_run()
