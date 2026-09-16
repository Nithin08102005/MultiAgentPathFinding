"""
Real Mathematical MTZ-MILP Solver CLI
Invoked by C++ lifelong.exe when --reorder_mode 3 is selected.
Solves the exact integer linear programming Traveling Salesperson Problem using COIN-OR CBC.
"""
import sys
import pulp

def main():
    if len(sys.argv) < 2:
        return
    try:
        dim = int(sys.argv[1])
        if len(sys.argv) >= 3 + dim * dim:
            allow_full = int(sys.argv[2])
            values = [float(x) for x in sys.argv[3:3 + dim * dim]]
        else:
            allow_full = 1
            values = [float(x) for x in sys.argv[2:2 + dim * dim]]
        if len(values) != dim * dim:
            sys.stderr.write(f"Expected {dim*dim} values, got {len(values)}\n")
            return
    except Exception as e:
        sys.stderr.write(f"Error parsing args: {e}\n")
        return
        
    cost_matrix = []
    idx = 0
    for i in range(dim):
        row = []
        for j in range(dim):
            row.append(values[idx])
            idx += 1
        cost_matrix.append(row)
        
    N = dim - 1
    if N <= 1:
        print(" ".join(str(i) for i in range(N)))
        sys.stdout.flush()
        return
        
    prob = pulp.LpProblem("Exact_TRP_CLI", pulp.LpMinimize)
    x = pulp.LpVariable.dicts("x", ((i, j) for i in range(N + 1) for j in range(N + 1) if i != j), cat=pulp.LpBinary)
    
    # Big-M upper bound on maximum possible tour duration
    M = sum(max(row) for row in cost_matrix) + 1000.0
    
    # Continuous arrival time variables T[j] for each goal j in 1..N
    T = pulp.LpVariable.dicts("T", range(1, N + 1), lowBound=0, upBound=M, cat=pulp.LpContinuous)
    
    # 1. Objective: Standard Canonical TRP (Minimize Cumulative Arrival Times)
    prob += pulp.lpSum(T[j] for j in range(1, N + 1))
    
    # 2. Constraints
    # (a) Start location departs exactly once
    prob += pulp.lpSum(x[(0, j)] for j in range(1, N + 1)) == 1

    # If active goal is locked, node 0 must go directly to Goal 0 (node 1)
    if allow_full == 0 and N >= 1:
        prob += x[(0, 1)] == 1
    
    # (b) Each goal is entered exactly once
    for j in range(1, N + 1):
        prob += pulp.lpSum(x[(i, j)] for i in range(N + 1) if i != j) == 1
        
    # (c) Each goal is departed at most once (open-loop tour)
    for i in range(1, N + 1):
        prob += pulp.lpSum(x[(i, j)] for j in range(1, N + 1) if i != j) <= 1
        
    # (d) Arrival Time Propagation Constraints (Linearized Big-M):
    # From start node (0) to goal j:
    for j in range(1, N + 1):
        prob += T[j] >= cost_matrix[0][j] - M * (1 - x[(0, j)])
        
    # Between goals i and j (strictly enforces sequence progression and eliminates subtours):
    for i in range(1, N + 1):
        for j in range(1, N + 1):
            if i != j:
                prob += T[j] >= T[i] + cost_matrix[i][j] - M * (1 - x[(i, j)])
                
    # 3. Solve with CBC Branch-and-Cut Integer Linear Programming Solver
    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    
    # 4. Extract optimal sequence
    curr = 0
    seq = []
    while len(seq) < N:
        for j in range(1, N + 1):
            if (curr, j) in x and pulp.value(x[(curr, j)]) is not None and pulp.value(x[(curr, j)]) > 0.5:
                seq.append(j - 1)
                curr = j
                break
        else:
            break
            
    # Fallback to sorting by arrival time T[j] if extraction incomplete
    if len(seq) < N:
        remaining = [i for i in range(N) if i not in seq]
        remaining.sort(key=lambda idx: pulp.value(T[idx + 1]) if (idx + 1) in T and pulp.value(T[idx + 1]) is not None else 999999)
        seq.extend(remaining)
        
    print(" ".join(str(i) for i in seq))
    sys.stdout.flush()

if __name__ == '__main__':
    main()
