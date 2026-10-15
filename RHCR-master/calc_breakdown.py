import sys

def analyze(folder, task_delay=7):
    task_times = {}
    total_tasks = 0
    with open(f'{folder}/tasks.txt') as f:
        lines = [l.strip() for l in f if l.strip()][1:]
    for line in lines:
        parts = line.split(' ', 1)
        if len(parts) < 2: continue
        ag = int(parts[0])
        entries = parts[1].strip(';').split(';')[1:]
        for e in entries:
            toks = e.split(',')
            if len(toks) >= 2 and toks[1] != '-1':
                t_fin = int(toks[1])
                total_tasks += 1
                for dt in range(t_fin - task_delay, t_fin + 1):
                    task_times[(ag, dt)] = True

    moving = 0
    dwell = 0
    wait = 0
    total_steps = 0

    with open(f'{folder}/paths.txt') as f:
        plines = [l.strip() for l in f if l.strip()][1:]
    for ag, line in enumerate(plines):
        steps = [s.split(',') for s in line.strip(';').split(';') if s]
        for i in range(1, len(steps)):
            loc_prev, ori_prev, t_prev = int(steps[i-1][0]), int(steps[i-1][1]), int(steps[i-1][2])
            loc_curr, ori_curr, t_curr = int(steps[i][0]), int(steps[i][1]), int(steps[i][2])
            total_steps += 1
            if loc_curr != loc_prev or ori_curr != ori_prev:
                moving += 1
            else:
                if (ag, t_curr) in task_times:
                    dwell += 1
                else:
                    wait += 1
    return total_tasks, moving, dwell, wait, total_steps

configs = [
    ('1. FIFO Baseline', 'exp/bench_fifo'),
    ('2. Naive TSP (Locked)', 'exp/bench_naive_locked'),
    ('3. Space-Time 2-Opt (Locked)', 'exp/bench_st_locked'),
    ('4. Naive TSP (Dynamic)', 'exp/bench_naive_dynamic'),
    ('5. Proposed ST 2-Opt (Dynamic)', 'exp/bench_st_dynamic')
]

print('| Method                      | Tasks | Moving % | Dwell %  | Traffic Wait % |')
print('|-----------------------------|-------|----------|----------|----------------|')
for name, path in configs:
    t, m, d, w, tot = analyze(path)
    print(f'| {name:27s} | {t:5d} | {m/tot*100:6.1f}%  | {d/tot*100:6.1f}%  | {w/tot*100:10.1f}%    |')
