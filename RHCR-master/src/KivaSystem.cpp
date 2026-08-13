#include "KivaSystem.h"
#include "WHCAStar.h"
#include "ECBS.h"
#include "LRAStar.h"
#include "PBS.h"
#include <iomanip>
 
#include "SIPP.h"
#include "ReservationTable.h"

#include <unordered_map>
#include <unordered_set>
#include <algorithm>
#include <random>
#include <iostream>
#include <fstream>
#include <list>
#include <queue>
#include <deque>
#include <sstream>
#include <tuple>
#include <climits>

using std::cout;
using std::endl;

 

 
static bool  dss_debug_print           = false;

 
static const int REPLAN_COOLDOWN_TICKS = 3;

 
static const int SII_REBUILD_PERIOD    = 1;

 static const int  HOT_CHOKE_THRESH     = 4;    
static const int  CHOKE_PENALTY_W      = 6;    
static const int  CHOKE_LOOKAHEAD_CAP  = 2;   

// per-agent cool-down vector
static std::vector<int> g_replan_cooldown;

 

 
static inline int effective_planning_window(int base_window, int agents)
{
    if (agents >= 256) return std::max(10, base_window * 2 / 3);
    if (agents >= 128) return std::max(14, base_window * 4 / 5);
    return base_window;
}

 
static inline int adaptive_depth_cap(int stitch_depth, int agents)
{
    if (agents >= 256) return std::min(stitch_depth, 2);
    if (agents >= 128) return std::min(stitch_depth, 2);
    return stitch_depth;
}

// for very big fleets: only rank top-2 goals; else all
static inline int prefilter_goal_topk(int bundle_size, int agents)
{
    if (agents >= 256) return std::min(bundle_size, 2);
    if (agents >= 128) return std::min(bundle_size, 3);
    return bundle_size;
}

// ============================================================================
// Small utilities
// ============================================================================
static inline int grid_vertex_count(const KivaGrid& G)
{
    const int R = G.get_rows();
    const int C = G.get_cols();
    if (R <= 0 || C <= 0) return 0;
    return R * C;
}

static inline int clamp_vertex(const KivaGrid& G, int v)
{
    const int N = grid_vertex_count(G);
    if (N <= 0) return 0;
    if (v < 0) return 0;
    if (v >= N) return N - 1;
    return v;
}

static inline int pick_random_endpoint_except(const KivaGrid& G, int avoid);
static int find_exterior_travel_cell_for_endpoint(const BasicGraph& G, int raw_ep);

static inline int pick_random_endpoint_except(const KivaGrid& G, int avoid)
{
    if (G.endpoints.empty())
        return clamp_vertex(G, avoid);

    int goal = G.endpoints[std::max(0, rand() % (int)G.endpoints.size())];
    int guard = 16;
    while (guard-- > 0 && goal == avoid && !G.endpoints.empty())
        goal = G.endpoints[rand() % (int)G.endpoints.size()];

    if (goal == avoid) {
        for (int e : G.endpoints) { if (e != avoid) { goal = e; break; } }
        if (goal == avoid) goal = G.endpoints.front();
    }
    return clamp_vertex(G, goal);
}

static inline int get_zone_for_location(const BasicGraph& G, int loc)
{
    if (loc < 0 || loc >= G.size()) return 0;
    int r = loc / G.cols;
    int c = loc % G.cols;
    int mid_r = G.rows / 2;
    int mid_c = G.cols / 2;
    if (r < mid_r && c < mid_c) return 0; // Zone 0: Top-Left
    if (r < mid_r && c >= mid_c) return 1; // Zone 1: Top-Right
    if (r >= mid_r && c < mid_c) return 2; // Zone 2: Bottom-Left
    return 3;                              // Zone 3: Bottom-Right
}

static inline int pick_random_endpoint_in_zone(const KivaGrid& G, int agent_id, int avoid)
{
    int target_zone = (agent_id >= 0) ? (agent_id % 4) : 0;
    int ep = pick_random_endpoint_except(G, avoid);
    int tries = 100;
    while (get_zone_for_location(G, ep) != target_zone && tries-- > 0)
    {
        ep = pick_random_endpoint_except(G, avoid);
    }
    return ep;
}

static inline const State& safe_path_at(std::vector<std::vector<State>>& paths,
                                        const KivaGrid& G,
                                        int k, int t,
                                        bool consider_rotation)
{
    if (k < 0) k = 0;
    if (k >= (int)paths.size()) paths.resize(k + 1);

    if (paths[k].empty()) {
        int home = (!G.agent_home_locations.empty() && k < (int)G.agent_home_locations.size())
                 ? clamp_vertex(G, G.agent_home_locations[k])
                 : (G.endpoints.empty() ? 0 : clamp_vertex(G, G.endpoints[k % (int)G.endpoints.size()]));
        int ori  = consider_rotation ? 0 : -1;
        paths[k].push_back(State(home, 0, ori));
    }
    while ((int)paths[k].size() <= t) {
        const State& last = paths[k].back();
        const int loc = clamp_vertex(G, last.location);
        paths[k].push_back(State(loc, last.timestep + 1, last.orientation));
    }
    return paths[k][t];
}

static inline bool is_endpoint_safe(const KivaGrid& G, int v)
{
    if (v < 0) return false;
    for (int e : G.endpoints) if (e == v) return true;
    return false;
}

static inline void clean_goals(const KivaGrid& G, int start_v, std::vector<int>& goals)
{
    for (int& g : goals) g = clamp_vertex(G, g);
    const int sv = clamp_vertex(G, start_v);
    goals.erase(std::remove(goals.begin(), goals.end(), sv), goals.end());
    std::sort(goals.begin(), goals.end());
    goals.erase(std::unique(goals.begin(), goals.end()), goals.end());
}

static inline std::vector<std::pair<int,int>>
safe_step_path(const KivaGrid& G, int v0, int t0, int v_goal)
{
    std::vector<std::pair<int,int>> out;
    v0     = clamp_vertex(G, v0);
    v_goal = clamp_vertex(G, v_goal);

    out.emplace_back(v0, t0);
    if (v0 == v_goal) return out;

    int t = t0;
    int v = v0;

    auto step_towards = [&](int target){
        int best = -1;
        int best_d = G.get_Manhattan_distance(v, target);
        for (int nb : G.get_neighbors(v)) {
            nb = clamp_vertex(G, nb);
            int d = G.get_Manhattan_distance(nb, target);
            if (d < best_d) { best_d = d; best = nb; }
        }
        if (best == -1) return false;
        v = best;
        ++t;
        out.emplace_back(v, t);
        return true;
    };

    const int CAP = 20000;
    int guard = 0;
    while (v != v_goal && guard++ < CAP) {
        if (!step_towards(v_goal)) break;
    }
    return out;
}

static inline void build_rt_from_teammates_safe(
    const KivaGrid& G,
    const std::vector<Path>& paths,
    int current_agent,
    int horizon_t,
    bool crop_to_horizon,
    bool consider_rotation,
    ReservationTable& rt)
{
    std::vector<Path> others(paths.size());
    for (int i = 0; i < (int)paths.size(); ++i) {
        if (i == current_agent) continue;
        Path tmp;

        if (crop_to_horizon && horizon_t >= 0) {
            for (const auto& s : paths[i]) {
                if (s.timestep <= horizon_t) tmp.push_back(s);
                else break;
            }
            if (tmp.empty() && !paths[i].empty())
                tmp.push_back(paths[i].front());
        } else {
            tmp = paths[i];
        }

        if (tmp.empty()) {
            int home = (!G.agent_home_locations.empty())
                     ? clamp_vertex(G, G.agent_home_locations.front())
                     : 0;
            int ori = consider_rotation ? 0 : -1;
            tmp.push_back(State(home, 0, ori));
        } else {
            tmp[0].location = clamp_vertex(G, tmp[0].location);
            for (size_t t = 1; t < tmp.size(); ++t) {
                tmp[t].location = clamp_vertex(G, tmp[t].location);
                if (tmp[t].timestep <= tmp[t-1].timestep) tmp[t].timestep = tmp[t-1].timestep + 1;
            }
        }

        others[i] = std::move(tmp);
    }
    std::list<std::tuple<int,int,int>> empty_initial;
    rt.build(others, empty_initial, current_agent);
}

// ============================================================================
// DSS: Safe Interval Index (per vertex)
// ============================================================================
struct SIInterval { int t0, t1; }; // inclusive

class SafeIntervalIndex {
public:
    void init(int n_vertices, int horizon) {
        horizon_ = horizon;
        si_.assign(n_vertices, {});
    }
    void set_intervals_for_vertex(int v, std::vector<SIInterval>&& ivals) {
        if (v >= 0 && v < (int)si_.size()) si_[v] = std::move(ivals);
    }
    const std::vector<SIInterval>& at(int v) const {
        static const std::vector<SIInterval> kEmpty;
        if (v < 0 || v >= (int)si_.size()) return kEmpty;
        return si_[v];
    }
    int horizon() const { return horizon_; }
    int vertex_count() const { return (int)si_.size(); }
private:
    int horizon_ = 0;
    std::vector<std::vector<SIInterval>> si_;
};

// dbg print
static void debug_print_intervals(const KivaGrid& /*G*/,
                                  const SafeIntervalIndex& sii,
                                  const std::vector<int>& vertices,
                                  int max_show_per_vertex = 6)
{
    if (!dss_debug_print) return;
    std::cout << "[DSS/SII] horizon=" << sii.horizon()
              << " vertices=" << vertices.size() << "\n";
    for (int v : vertices) {
        std::cout << "  v=" << v
                  << " intervals=" << sii.at(v).size() << "  ";
        int show = 0;
        for (const auto& I : sii.at(v)) {
            if (show++ >= max_show_per_vertex) { std::cout << "..."; break; }
            std::cout << "[" << I.t0 << "," << I.t1 << "] ";
        }
        std::cout << "\n";
    }
}

// global SII
static SafeIntervalIndex g_sii_tick;
static int g_sii_horizonT = 0;
static int g_sii_built_at = -1000000;

// merge interval into occ
static inline void push_occ(std::vector<SIInterval>& occ, int a, int b)
{
    if (b < a) return;
    occ.push_back({a,b});
}

static inline void normalize_intervals(std::vector<SIInterval>& v)
{
    if (v.empty()) return;
    std::sort(v.begin(), v.end(), [](const SIInterval& A, const SIInterval& B){
        if (A.t0 != B.t0) return A.t0 < B.t0;
        return A.t1 < B.t1;
    });
    int w = 0;
    for (int i = 0; i < (int)v.size(); ++i) {
        if (w == 0) { v[w++] = v[i]; continue; }
        if (v[i].t0 <= v[w-1].t1 + 1) {
            v[w-1].t1 = std::max(v[w-1].t1, v[i].t1);
        } else {
            v[w++] = v[i];
        }
    }
    v.resize(w);
}

static inline std::vector<SIInterval> invert_to_free(const std::vector<SIInterval>& occ, int T)
{
    std::vector<SIInterval> freev;
    if (T < 0) return freev;
    if (occ.empty()) { freev.push_back({0,T}); return freev; }

    int cur = 0;
    for (const auto& I : occ) {
        if (cur <= I.t0 - 1) freev.push_back({cur, I.t0 - 1});
        cur = I.t1 + 1;
        if (cur > T) break;
    }
    if (cur <= T) freev.push_back({cur, T});
    return freev;
}

// build global vertex SII
static void build_global_vertex_sii_compressed(const KivaGrid& G,
                                               const std::vector<Path>& paths,
                                               int T,
                                               SafeIntervalIndex& out_sii)
{
    const int V = std::max(0, G.get_rows() * G.get_cols());
    T = std::max(0, T);
    out_sii.init(V, T);
    if (V == 0) return;

    std::unordered_map<int, std::vector<SIInterval>> occ; // v -> occupied intervals
    occ.reserve(V / 4 + 32);

    for (int a = 0; a < (int)paths.size(); ++a) {
        if (paths[a].empty()) continue;

        std::vector<State> p = paths[a];
        p[0].location = clamp_vertex(G, p[0].location);
        for (size_t i = 1; i < p.size(); ++i) {
            p[i].location = clamp_vertex(G, p[i].location);
            if (p[i].timestep <= p[i-1].timestep) p[i].timestep = p[i-1].timestep + 1;
        }

        for (size_t i = 0; i + 1 < p.size(); ++i) {
            int vi = p[i].location;
            int ti = std::max(0, p[i].timestep);
            int vj = p[i+1].location;
            int tj = std::max(0, p[i+1].timestep);

            if (ti <= T && tj-1 >= 0) {
                int a0 = std::max(0, ti);
                int b0 = std::min(T, tj - 1);
                if (a0 <= b0) push_occ(occ[vi], a0, b0);
            }
            if (tj <= T) push_occ(occ[vj], tj, tj);
        }

        int vlast = p.back().location;
        int tlast = std::max(0, p.back().timestep);
        if (tlast <= T) push_occ(occ[vlast], tlast, T);
    }

    const int Vtot = G.get_rows() * G.get_cols();
    for (int v = 0; v < Vtot; ++v) {
        auto it = occ.find(v);
        if (it == occ.end()) {
            std::vector<SIInterval> allfree = { {0, T} };
            out_sii.set_intervals_for_vertex(v, std::move(allfree));
        } else {
            normalize_intervals(it->second);
            auto freev = invert_to_free(it->second, T);
            out_sii.set_intervals_for_vertex(v, std::move(freev));
        }
    }
}

static inline bool sii_has_window_at(const SafeIntervalIndex& sii, int v, int q0, int q1)
{
    const auto& ivs = sii.at(v);
    if (ivs.empty() || q0 > q1) return false;
    for (const auto& I : ivs) {
        const int a0 = std::max(I.t0, q0);
        const int a1 = std::min(I.t1, q1);
        if (a0 <= a1) return true;
    }
    return false;
}

static inline int dss_interference_score(const KivaGrid& G,
                                         const SafeIntervalIndex& sii,
                                         int v,
                                         int start_v,
                                         int now_t,
                                         int horizon)
{
    const auto& ivs = sii.at(v);
    int best = INT_MAX;

    for (const auto& I : ivs) {
        if (I.t1 < now_t) continue;
        if (I.t0 > now_t + horizon) break;
        int wait = std::max(0, I.t0 - now_t);
        int len  = std::max(1, I.t1 - std::max(now_t, I.t0) + 1);
        int dist = G.get_Manhattan_distance(start_v, v);
        int score = wait * 8 + (256 / len) + dist;
        if (score < best) best = score;
    }

    if (best == INT_MAX) {
        int dist = G.get_Manhattan_distance(start_v, v);
        best = 100000 + dist;
    }
    return best;
}

// ============================================================================
// Edge-aware SII (directed edges)
// ============================================================================
struct EdgeKey {
    int u, v;
    bool operator==(const EdgeKey& o) const noexcept { return u==o.u && v==o.v; }
};
struct EdgeKeyHash {
    size_t operator()(const EdgeKey& k) const noexcept {
        return (size_t)k.u * 1315423911u ^ (size_t)k.v * 2654435761u;
    }
};

static std::unordered_map<EdgeKey, std::vector<SIInterval>, EdgeKeyHash> g_edge_free_sii;
static int g_edge_sii_horizonT = 0;
static int g_edge_sii_built_at = -1000000;

static void build_global_edge_sii_compressed(const KivaGrid& G,
                                             const std::vector<Path>& paths,
                                             int T)
{
    g_edge_free_sii.clear();
    T = std::max(0, T);

    std::unordered_map<EdgeKey, std::vector<SIInterval>, EdgeKeyHash> occ;

    for (int a = 0; a < (int)paths.size(); ++a) {
        if (paths[a].empty()) continue;

        std::vector<State> p = paths[a];
        p[0].location = clamp_vertex(G, p[0].location);
        for (size_t i = 1; i < p.size(); ++i) {
            p[i].location = clamp_vertex(G, p[i].location);
            if (p[i].timestep <= p[i-1].timestep) p[i].timestep = p[i-1].timestep + 1;
        }

        for (size_t i = 0; i + 1 < p.size(); ++i) {
            int u  = p[i].location;
            int v  = p[i+1].location;
            int tj = std::max(0, p[i+1].timestep);
            if (u == v) continue;
            if (tj <= T) {
                EdgeKey ek{u,v};
                push_occ(occ[ek], tj, tj);
            }
        }
    }

    for (auto &kv : occ) {
        auto &row = kv.second;
        normalize_intervals(row);
        g_edge_free_sii[kv.first] = invert_to_free(row, T);
    }
}

static inline bool edge_has_window_at(int u, int v, int q0, int q1)
{
    if (q0 > q1) return false;
    EdgeKey ek{u,v};
    auto it = g_edge_free_sii.find(ek);
    if (it == g_edge_free_sii.end()) return true; // unseen → free
    const auto& ivs = it->second;
    for (const auto& I : ivs) {
        const int a0 = std::max(I.t0, q0);
        const int a1 = std::min(I.t1, q1);
        if (a0 <= a1) return true;
    }
    return false;
}

static inline int min_outgoing_edge_wait(const KivaGrid& G, int start_v, int t0, int horizon)
{
    int best = INT_MAX;
    for (int nb : G.get_neighbors(start_v)) {
        nb = clamp_vertex(G, nb);
        for (int w = 0; w <= horizon; ++w) {
            const int step_t = t0 + 1 + w;
            if (edge_has_window_at(start_v, nb, step_t, step_t)) {
                best = std::min(best, w);
                break;
            }
        }
    }
    return best;
}

static inline int min_incoming_edge_wait(const KivaGrid& G, int goal_v, int eta, int delta)
{
    int best = INT_MAX;
    for (int nb : G.get_neighbors(goal_v)) {
        nb = clamp_vertex(G, nb);
        for (int w = 0; w <= delta; ++w) {
            const int t = eta + w;
            if (edge_has_window_at(nb, goal_v, t, t)) {
                best = std::min(best, w);
                break;
            }
        }
    }
    return best;
}

// ============================================================================
// Chokepoints
// ============================================================================
static std::vector<char> g_is_choke;
static std::unordered_map<int,int> g_choke_heat;
static int g_choke_built_at = -1000000;
static int g_choke_horizonT = 0;

static inline void build_chokepoints_once(const KivaGrid& G)
{
    const int V = grid_vertex_count(G);
    g_is_choke.assign(V, 0);
    for (int v = 0; v < V; ++v) {
        const auto& nbs = G.get_neighbors(v);
        if ((int)nbs.size() == 2) {
            g_is_choke[v] = 1;
        }
    }
}

static inline void build_choke_heat(const KivaGrid& G,
                                    const std::vector<Path>& paths,
                                    int now_t,
                                    int horizonT)
{
    g_choke_heat.clear();
    for (int a = 0; a < (int)paths.size(); ++a) {
        if (paths[a].empty()) continue;
        const auto& p = paths[a];
        for (size_t i = 0; i < p.size(); ++i) {
            int t = p[i].timestep;
            if (t < now_t || t > horizonT) continue;
            int v = clamp_vertex(G, p[i].location);
            if (v >= 0 && g_is_choke[v]) {
                g_choke_heat[v] += 1;
            }
        }
    }
}

static inline int greedy_choke_penalty(const KivaGrid& G,
                                       int start_v, int start_t,
                                       int goal_v, int horizonT)
{
    auto seq = safe_step_path(G, start_v, start_t, goal_v);
    int seen = 0;
    int penalty = 0;
    for (size_t i = 0; i < seq.size(); ++i) {
        int v = seq[i].first;
        int t = seq[i].second;
        if (t > horizonT) break;
        if (v >= 0 && g_is_choke[v]) {
            auto it = g_choke_heat.find(v);
            if (it != g_choke_heat.end() && it->second > 0) {
                penalty += CHOKE_PENALTY_W * it->second;
                if (++seen >= CHOKE_LOOKAHEAD_CAP) break;
            }
        }
    }
    return penalty;
}

static inline bool starts_into_hot_choke(const KivaGrid& G,
                                         int start_v, int start_t, int goal_v)
{
    auto seq = safe_step_path(G, start_v, start_t, goal_v);
    if (seq.size() < 2) return false;
    int next_v = seq[1].first;
    if (next_v >= 0 && g_is_choke[next_v]) {
        auto it = g_choke_heat.find(next_v);
        if (it != g_choke_heat.end() && it->second >= HOT_CHOKE_THRESH)
            return true;
    }
    return false;
}

KivaSystem::KivaSystem(const KivaGrid& G_, MAPFSolver& solver)
  : BasicSystem(G_, solver), G(G_) {}

KivaSystem::~KivaSystem() {}

void KivaSystem::initialize()
{
    initialize_solvers();
    // In capacity_mode with task_delay > 0, robots hold at goal cells for task_delay
    // steps and then leave. We must NOT use hold_endpoints=true (that checks
    // earliest_holding_time from the RT, which returns a huge value because the
    // initial_rt permanently extends each robot's old path — causing robots to generate
    // path_size=274 trying to avoid their own old goal cell, getting completely stuck).
    //
    // Instead, keep solver.hold_endpoints=false (SIPP paths end at arrival+task_delay)
    // BUT flip initial_rt.hold_endpoints=false so the initial RT does NOT permanently
    // extend paths. Without permanent extension the soft-constraint at a goal cell ends
    // when the robot's path ends (arrival+task_delay), so other robots' SIPP sees a
    // FINITE block there — no more 80K-node exhaustion from permanent RT occupation.
    if (capacity_mode && task_delay > 0) {
        solver.initial_rt.hold_endpoints = false;
    }

    starts.resize(num_of_drives);
    goal_locations.resize(num_of_drives);
    paths.resize(num_of_drives);
    finished_tasks.resize(num_of_drives);

    g_replan_cooldown.assign(num_of_drives, 0);

    bundle.assign(num_of_drives, {});
    rest.assign(num_of_drives, {});
    bundle_dirty.assign(num_of_drives, true);

    bool succ = load_records();
    if (!succ)
    {
        timestep = 0;
        succ = load_locations();
        if (!succ)
        {
            cout << "Randomly generating initial locations" << endl;
            initialize_start_locations();
            initialize_goal_locations();
        }
    }

    build_chokepoints_once(G);

    bundle_configure(num_of_drives, default_agent_capacity, randomize_sequences, rng_seed);
    if (!given_goals.empty())
        bundle_initialize_from_given(given_goals);
    else if (capacity_mode && succ) {
        // load_records() filled goal_locations from paths.txt/tasks.txt but left bundle/rest
        // empty. bundle_mirror_to_engine() would then wipe goal_locations to one random goal.
        for (int k = 0; k < num_of_drives; ++k) {
            if (goal_locations[k].empty()) continue;
            if (!bundle[k].empty() || !rest[k].empty()) continue;
            const int cap = cap_of(k);
            for (const auto& g : goal_locations[k]) {
                std::pair<int, int> gg = { clamp_vertex(G, g.first), g.second };
                if ((int)bundle[k].size() < cap) bundle[k].push_back(gg);
                else rest[k].push_back(gg);
            }
            bundle_dirty[k] = true;
        }
        bundle_mirror_to_engine();
    }
}

void KivaSystem::initialize_start_locations()
{
    for (int k = 0; k < num_of_drives; k++)
    {
        int home = (!G.agent_home_locations.empty() && k < (int)G.agent_home_locations.size())
                 ? clamp_vertex(G, G.agent_home_locations[k]) : 0;
        int orientation = consider_rotation ? 0 : -1;
        if (consider_rotation)
        {
            for (int ori = 0; ori < 4; ori++)
            {
                if (G.valid_3cell_state(home, ori))
                {
                    orientation = ori;
                    break;
                }
            }
            if (!G.valid_3cell_state(home, orientation))
            {
                for (int loc = 0; loc < G.size(); loc++)
                {
                    for (int ori = 0; ori < 4; ori++)
                    {
                        if (G.valid_3cell_state(loc, ori))
                        {
                            home = loc;
                            orientation = ori;
                            break;
                        }
                    }
                    if (G.valid_3cell_state(home, orientation)) break;
                }
            }
        }

        starts[k] = State(home, 0, orientation);
        paths[k].clear();
        paths[k].emplace_back(starts[k]);
        finished_tasks[k].clear();
        finished_tasks[k].emplace_back(home, 0);
    }
}

void KivaSystem::initialize_goal_locations()
{
    if (hold_endpoints || useDummyPaths) return;

    for (int k = 0; k < num_of_drives; k++)
    {
        int curr = safe_path_at(paths, G, k, 0, consider_rotation).location;
        int raw_g = pick_random_endpoint_in_zone(G, k, curr);
        int goal = find_exterior_travel_cell_for_endpoint(G, raw_g);
        goal_locations[k].emplace_back(goal, 0);
    }
}

// -------------------------------- helpers -----------------------------------
void KivaSystem::ensure_goal_exists(int k, int curr)
{
    if (k < 0 || k >= (int)goal_locations.size()) return;
    if (!goal_locations[k].empty()) return;
    int raw_g = pick_random_endpoint_in_zone(G, k, curr);
    int g = find_exterior_travel_cell_for_endpoint(G, raw_g);
    goal_locations[k].emplace_back(g, 0);
}

int KivaSystem::cap_of(int k) const
{
    if (!per_agent_capacity.empty() && k >= 0 && k < (int)per_agent_capacity.size()) {
        int c = per_agent_capacity[k];
        return c > 0 ? c : 1;
    }
    return default_agent_capacity > 0 ? default_agent_capacity : 1;
}

void KivaSystem::bundle_configure(int, int capacity, bool randomize, unsigned seed)
{
    default_agent_capacity = (capacity > 0 ? capacity : 1);
    randomize_sequences = randomize;
    rng_seed            = seed;
}

void KivaSystem::bundle_initialize_from_given(const std::vector<std::vector<int>>& gg)
{
    std::mt19937 rng(rng_seed);
    int n = std::min<int>((int)gg.size(), num_of_drives);
    for (int k = 0; k < n; ++k)
    {
        std::vector<int> seq = gg[k];
        if (randomize_sequences) std::shuffle(seq.begin(), seq.end(), rng);

        const int cap = cap_of(k);
        for (size_t i = 0; i < seq.size(); ++i) {
            int v = clamp_vertex(G, seq[i]);
            std::pair<int,int> g = { v, 0 };
            if ((int)bundle[k].size() < cap) bundle[k].push_back(g);
            else                              rest[k].push_back(g);
        }
        bundle_dirty[k] = true;
    }
}

bool KivaSystem::bundle_on_goal_reached(int k)
{
    if (k < 0 || k >= (int)bundle.size()) return false;
    if (bundle[k].empty()) return false;

    auto& front = bundle[k].front();
    const int raw_target = clamp_vertex(G, front.first);
    const int target = find_exterior_travel_cell_for_endpoint(G, raw_target);

    // Scan the recent window to find the FIRST timestep robot arrived at target.
    // We only use this to initialize the dwell timer (front.second).
    // The pop decision always compares global timestep against front.second,
    // NOT the individual scan timestep - this avoids the bug where the scan
    // finds an old timestep (e.g. t=30) that is still before front.second (35)
    // and returns false even though the current tick IS past front.second.
    const int t1 = timestep;
    const int t0 = std::max(0, timestep - simulation_window);
    bool robot_at_target = false;
    for (int t = t0; t <= t1 && k < (int)paths.size(); ++t) {
        if (t >= (int)paths[k].size()) break;
        int loc = clamp_vertex(G, paths[k][t].location);
        if (loc == target || loc == raw_target) {
            // Initialize dwell timer on first arrival (only once, when front.second==0)
            if (task_delay > 0 && front.second == 0) {
                front.second = paths[k][t].timestep + task_delay;
            }
            robot_at_target = true;
            break;  // found the earliest arrival; timer is set
        }
    }

    if (!robot_at_target) return false;  // robot not at target in this window

    // Compare GLOBAL timestep (current simulation time) against the dwell deadline.
    // Do NOT use the individual path-state timestep from the scan - that can be
    // an old slice from the window start that is still before front.second.
    if (task_delay > 0 && timestep < front.second) {
        return false;  // still within dwell period
    }

    // Dwell complete (or no task_delay): pop the completed task
    bundle[k].pop_front();
    bundle_dirty[k] = true;
    m_restitches_total++;
    num_of_tasks++;
    if (k < (int)finished_tasks.size()) {
        finished_tasks[k].emplace_back(target, t1);
    }
    return true;
}

std::unordered_set<int> KivaSystem::collect_claimed_active_endpoints(int except_agent) const
{
    std::unordered_set<int> claimed;
    if (!capacity_mode) return claimed;
    for (int i = 0; i < (int)bundle.size(); ++i) {
        if (i == except_agent) continue;
        for (const auto& g : bundle[i]) claimed.insert(clamp_vertex(G, g.first));
    }
    return claimed;
}

bool KivaSystem::bundle_maybe_top_up(int k)
{
    if (k < 0 || k >= (int)bundle.size()) return false;
    bool changed = false;

    std::unordered_set<int> claimed = avoid_dup_goals ? collect_claimed_active_endpoints(k)
                                                      : std::unordered_set<int>{};

    const int cap = cap_of(k);
    int curr = safe_path_at(paths, G, k, timestep, consider_rotation).location;
    while ((int)bundle[k].size() < cap && !rest[k].empty()) {
        auto g = rest[k].front(); rest[k].pop_front();
        g.first = clamp_vertex(G, g.first);

        if (avoid_dup_goals && claimed.count(g.first)) {
            int fresh_v = generate_endpoint_for(k, curr);
            int tries = 50;
            while (claimed.count(fresh_v) && tries-- > 0) {
                fresh_v = generate_endpoint_for(k, curr);
            }
            g.first = clamp_vertex(G, fresh_v);
        }

        bundle[k].push_back(g);
        claimed.insert(g.first);
        changed = true;
    }
    if (changed) { bundle_dirty[k] = true; m_restitches_total++; }
    return changed;
}

void KivaSystem::bundle_assert_capacity_ok(int k)
{
    if (k < 0 || k >= (int)bundle.size()) return;
    int cap = cap_of(k);
    while ((int)bundle[k].size() > cap) {
        bundle[k].pop_back();
    }
}

void KivaSystem::bundle_mirror_to_engine()
{
    for (int k = 0; k < num_of_drives; ++k) {
        int existing_release = (!goal_locations[k].empty()) ? goal_locations[k].front().second : 0;
        goal_locations[k].clear();
        if (!bundle[k].empty()) {
            int raw_v = clamp_vertex(G, bundle[k].front().first);
            int v = find_exterior_travel_cell_for_endpoint(G, raw_v);
            int release_t = std::max(bundle[k].front().second, existing_release);

            // If robot is already sitting at this goal cell and dwell timer hasn't been
            // set yet (release_t==0), initialize the dwell timer right now so that
            // BasicSystem::move() never sees release_t=0 while robot is already there
            // (which would cause move() to instantly pop the goal before the 7-step dwell).
            if (task_delay > 0 && release_t == 0) {
                int curr_loc = clamp_vertex(G, safe_path_at(paths, G, k, timestep, consider_rotation).location);
                int gsz = G.size(); if (gsz <= 0) gsz = 1;
                if ((curr_loc % gsz) == (raw_v % gsz) || (curr_loc % gsz) == (v % gsz)) {
                    release_t = timestep + task_delay;
                }
            }

            bundle[k].front().second = release_t;
            goal_locations[k].push_back({v, release_t});
        }
        if (goal_locations[k].empty()) {
            int curr = safe_path_at(paths, G, k, timestep, consider_rotation).location;
            ensure_goal_exists(k, curr);
        }
        bundle_assert_capacity_ok(k);
    }
}

static inline int get_dist_h(const KivaGrid& G, int u, int v) {
    int target = find_exterior_travel_cell_for_endpoint(G, v);
    auto it = G.heuristics.find(target);
    if (it != G.heuristics.end() && u >= 0 && u < (int)it->second.size() && it->second[u] < INT_MAX)
        return (int)it->second[u];
    return G.get_Manhattan_distance(u, target);
}

static int get_aisle_traffic_penalty(const KivaGrid& G, std::vector<Path>& paths, int current_agent, int target_raw_v, int current_t) {
    if (paths.empty()) return 0;

    int target = find_exterior_travel_cell_for_endpoint(G, target_raw_v);
    int traffic_count = 0;

    for (int i = 0; i < (int)paths.size(); ++i) {
        if (i == current_agent || paths[i].empty()) continue;
        const State& st = safe_path_at(paths, G, i, current_t, true);
        int teammate_loc = clamp_vertex(G, st.location);
        if (G.get_Manhattan_distance(teammate_loc, target) <= 3) {
            traffic_count++;
        }
    }

    return traffic_count * 5; // 5-timestep penalty per nearby teammate
}

// -------------------------- reorder by DVS (Dynamic Traffic-Aware Distance) --------------------------
void KivaSystem::reorder_bundle_by_dvs(int k)
{
    if (!safety_mode) return;
    if (k < 0 || k >= (int)bundle.size()) return;
    if (bundle[k].size() <= 1) return;

    const int start_v = safe_path_at(paths, G, k, timestep, consider_rotation).location;

    std::vector<std::pair<int,int>> items(bundle[k].begin(), bundle[k].end());
    const int N = (int)items.size();

    std::vector<int> perm(N);
    for (int i = 0; i < N; ++i) perm[i] = i;

    std::vector<int> best_perm = perm;
    int best_cost = INT_MAX;

    do {
        int cost = 0;
        int prev_v = start_v;

        for (int i = 0; i < N; ++i) {
            int goal_raw = items[perm[i]].first;
            int dist = get_dist_h(G, prev_v, goal_raw);
            int penalty = (timestep > 0) ? get_aisle_traffic_penalty(G, paths, k, goal_raw, timestep) : 0;
            cost += dist + penalty;
            prev_v = find_exterior_travel_cell_for_endpoint(G, goal_raw);
        }

        if (cost < best_cost) {
            best_cost = cost;
            best_perm = perm;
        }
    } while (std::next_permutation(perm.begin(), perm.end()));

    std::deque<std::pair<int,int>> reordered;
    for (int idx : best_perm) {
        reordered.push_back(items[idx]);
    }

    bundle[k] = std::move(reordered);
    bundle_dirty[k] = true;
    m_restitches_total++;
}

int KivaSystem::generate_endpoint_for(int k, int avoid_v) const
{
    return pick_random_endpoint_in_zone(G, k, avoid_v);
}

void KivaSystem::maybe_autorefill_rest(int k)
{
    if (!auto_refill) return;
    if (k < 0 || k >= (int)rest.size()) return;

    if (rest[k].empty()) {
        int curr = safe_path_at(paths, G, k, timestep, consider_rotation).location;

        std::unordered_set<int> claimed = collect_claimed_active_endpoints(k);
        claimed.insert(clamp_vertex(G, curr));

        const int cap = cap_of(k);
        for (int i = 0; i < cap; ++i) {
            int v = generate_endpoint_for(k, curr);
            int tries = 16;
            while (avoid_dup_goals && claimed.count(v) && tries-- > 0) {
                v = generate_endpoint_for(k, curr);
            }
            v = clamp_vertex(G, v);
            rest[k].push_back({v, 0});
            claimed.insert(v);
        }
    }
}

// ------------------------------- Stitching ----------------------------------
void KivaSystem::suppress_replan_for(int k)
{
    for (auto it = new_agents.begin(); it != new_agents.end(); ) {
        if (*it == k) it = new_agents.erase(it);
        else ++it;
    }
}

void KivaSystem::plan_stitched_for_agent(int k)
{
    if (k < 0 || k >= num_of_drives) return;
    if (!capacity_mode) return;
    if (bundle[k].empty()) return;

    // cooldown
    if (!bundle_dirty[k] && g_replan_cooldown.size() == (size_t)num_of_drives && g_replan_cooldown[k] > 0) {
        metrics_after_stitch(false,false,false,true);
        return;
    }

    if (restitch_on_change && !bundle_dirty[k] && timestep > 0) {
        metrics_after_stitch(false, false, false, true);
        return;
    }

    const int start_v = safe_path_at(paths, G, k, timestep, consider_rotation).location;
    const int start_t = timestep;
    const int AGENTS  = num_of_drives;

    const int PLWIN   = effective_planning_window(planning_window, AGENTS);

    // collect goals
    std::vector<int> goals;
    goals.reserve(bundle[k].size());
    for (const auto& g : bundle[k]) goals.push_back(clamp_vertex(G, g.first));
    clean_goals(G, start_v, goals);

    if (goals.empty()) {
        bundle_dirty[k] = false;
        metrics_after_stitch(false, false, false, true);
        return;
    }

    // depth adapt
    const int depth_cap = adaptive_depth_cap(stitch_depth, AGENTS);
    if ((int)goals.size() > depth_cap) goals.resize(depth_cap);

    // prefilter for very large fleets
    const int keepK = prefilter_goal_topk((int)goals.size(), AGENTS);
    if ((int)goals.size() > keepK) goals.resize(keepK);

    // DSS ranking: vertex SII + incoming edge wait + choke penalty
    std::vector<std::pair<int,int>> ranked;
    ranked.reserve(goals.size());
    for (int g : goals) {
        int v = clamp_vertex(G, g);
        int dist = G.get_Manhattan_distance(start_v, v);
        int eta  = start_t + dist;

        int sc_v = dss_interference_score(G, g_sii_tick, v, start_v, start_t, PLWIN);
        int delta = std::max(2, PLWIN / 3);
        int wait_in = min_incoming_edge_wait(G, v, eta, delta);
        if (wait_in == INT_MAX) wait_in = 64;

        int choke_pen = greedy_choke_penalty(G, start_v, start_t, v, start_t + PLWIN);

        int score = sc_v + wait_in * 6 + choke_pen;
        ranked.emplace_back(score, v);
    }
    std::sort(ranked.begin(), ranked.end());
    goals.clear();
    for (auto &p : ranked) goals.push_back(p.second);

    // deferral: if the first has no vertex window in [t, t+PLWIN] → push to rest
    {
        const int q0 = start_t, q1 = start_t + PLWIN;
        if (!goals.empty()) {
            int g0 = goals.front();
            if (!sii_has_window_at(g_sii_tick, g0, q0, q1)) {
                if (k >= 0 && k < (int)rest.size()) rest[k].push_back({g0, 0});
                goals.erase(goals.begin());
                bundle_dirty[k] = true;
                m_restitches_total++;
                bundle_maybe_top_up(k);
            }
        }
        if (goals.empty()) {
            metrics_after_stitch(false, false, false, true);
            return;
        }
    }

    // avoid starting straight into a hot choke — skip those, but don't starve
    {
        std::vector<int> kept;
        kept.reserve(goals.size());
        for (int v : goals) {
            if (starts_into_hot_choke(G, start_v, start_t, v)) continue;
            kept.push_back(v);
        }
        if (!kept.empty()) goals.swap(kept);
    }

    // edge-feasibility gate near ETA
    {
        std::vector<int> kept;
        kept.reserve(goals.size());
        for (int v : goals) {
            int dist = G.get_Manhattan_distance(start_v, v);
            int eta  = start_t + dist;
            int win  = std::max(2, PLWIN / 3);
            int w_in = min_incoming_edge_wait(G, v, eta, win);
            if (w_in != INT_MAX) kept.push_back(v);
        }
        if (kept.empty()) {
            bundle_dirty[k] = false;
            metrics_after_stitch(false, false, false, true);
            if (g_replan_cooldown.size() == (size_t)num_of_drives)
                g_replan_cooldown[k] = REPLAN_COOLDOWN_TICKS;
            return;
        }
        goals.swap(kept);
    }

    std::vector<State> new_suffix;
    bool used_sipp = false, sipp_ok = false, fell_back = false;

    // Determine the agent's actual orientation at the current timestep so that
    // stitched states are consistent with rotation-aware path validation.
    int start_ori = -1;
    if (consider_rotation && k < (int)paths.size() && !paths[k].empty()) {
        int idx = std::min(timestep, (int)paths[k].size() - 1);
        start_ori = paths[k][idx].orientation;
        if (start_ori < 0) start_ori = 0; // default to East (0) if no orientation yet
    }

    if (stitch_use_sipp) {
        used_sipp = true;

        // small local SII around start+first
        auto build_sii_sparse_local = [&](int horizon_t,
                                          int around_v0,
                                          int around_g,
                                          SafeIntervalIndex& out_sii)
        {
            const int V = G.get_rows() * G.get_cols();
            const int T = std::max(0, horizon_t);
            out_sii.init(V, T);

            auto near_any = [&](int v)->bool{
                if (G.get_Manhattan_distance(v, around_v0) <= 8) return true;
                if (G.get_Manhattan_distance(v, around_g ) <= 8) return true;
                return false;
            };

            std::unordered_map<int, std::vector<SIInterval>> occ;
            for (int a = 0; a < (int)paths.size(); ++a) {
                if (paths[a].empty() || a == k) continue;
                std::vector<State> p = paths[a];
                p[0].location = clamp_vertex(G, p[0].location);
                for (size_t i = 1; i < p.size(); ++i) {
                    p[i].location = clamp_vertex(G, p[i].location);
                    if (p[i].timestep <= p[i-1].timestep) p[i].timestep = p[i-1].timestep + 1;
                }

                for (size_t i = 0; i + 1 < p.size(); ++i) {
                    int vi = p[i].location, ti = std::max(0, p[i].timestep);
                    int vj = p[i+1].location, tj = std::max(0, p[i+1].timestep);
                    if (near_any(vi)) { int a0=std::max(0,ti), b0=std::min(T,tj-1); if (a0<=b0) push_occ(occ[vi], a0,b0); }
                    if (near_any(vj) && tj <= T) push_occ(occ[vj], tj, tj);
                }
                int vlast=p.back().location, tlast=std::max(0,p.back().timestep);
                if (near_any(vlast) && tlast<=T) push_occ(occ[vlast], tlast, T);
            }

            for (auto &kv : occ) {
                normalize_intervals(kv.second);
                auto freev = invert_to_free(kv.second, T);
                out_sii.set_intervals_for_vertex(kv.first, std::move(freev));
            }
        };

        SafeIntervalIndex sii_local;
        int first_goal = goals.front();
        const int localH = start_t + PLWIN;
        build_sii_sparse_local(localH,
                               clamp_vertex(G, start_v),
                               clamp_vertex(G, first_goal),
                               sii_local);

        // vertex snap
        int best_w_vertex = 0;
        {
            const auto& ivs = sii_local.at(clamp_vertex(G, start_v));
            bool snapped = false;
            for (const auto& I : ivs) {
                if (I.t1 < start_t) continue;
                best_w_vertex = std::max(0, I.t0 - start_t);
                snapped = true;
                break;
            }
            if (!snapped) {
                bundle_dirty[k] = false;
                metrics_after_stitch(false, false, false, true);
                if (g_replan_cooldown.size() == (size_t)num_of_drives)
                    g_replan_cooldown[k] = REPLAN_COOLDOWN_TICKS;
                return;
            }
        }

        // outgoing edge snap
        int extra_w_edge = min_outgoing_edge_wait(G, clamp_vertex(G, start_v),
                                                  start_t + best_w_vertex, PLWIN);
        if (extra_w_edge == INT_MAX) {
            bundle_dirty[k] = false;
            metrics_after_stitch(false, false, false, true);
            if (g_replan_cooldown.size() == (size_t)num_of_drives)
                g_replan_cooldown[k] = REPLAN_COOLDOWN_TICKS;
            return;
        }
        int best_w = best_w_vertex + extra_w_edge;

        // RT
        ReservationTable rt(G);
        build_rt_from_teammates_safe(G, paths, k,
                                     start_t + PLWIN,
                                     /*crop=*/stitch_crop_horizon,
                                     consider_rotation,
                                     rt);

        // Determine the agent's actual orientation at the current timestep so that
        // stitched states are consistent with rotation-aware path validation.
        // (start_ori is now declared above, outside this block)

        State s0(clamp_vertex(G, start_v), start_t + best_w, start_ori);
        std::vector<std::pair<int,int>> gl; gl.reserve(goals.size());
        for (int g : goals) gl.emplace_back(g, 0);

        SIPP sipp;
        auto path = sipp.run(G, s0, gl, rt);
        if (!path.empty()) {
            if (best_w > 0) {
                new_suffix.reserve(best_w + path.size());
                // Use the actual orientation for wait-in-place states before SIPP path begins
                for (int i = 0; i < best_w; ++i) new_suffix.emplace_back(start_v, start_t + i, start_ori);
                new_suffix.insert(new_suffix.end(), path.begin(), path.end());
                for (size_t i = 1; i < new_suffix.size(); ++i)
                    if (new_suffix[i].timestep <= new_suffix[i-1].timestep)
                        new_suffix[i].timestep = new_suffix[i-1].timestep + 1;
            } else {
                new_suffix = std::move(path);
            }
            sipp_ok = true;
        }
    }

    if (!sipp_ok) {
        // deterministic fallback
        std::vector<std::pair<int,int>> seq;
        seq.emplace_back(start_v, start_t);
        int v = start_v, t = start_t;
        for (int g : goals) {
            auto seg = safe_step_path(G, v, t, g);
            if (seg.size() > 1) {
                seq.insert(seq.end(), seg.begin() + 1, seg.end());
                v = g; t = seq.back().second;
            }
        }
        new_suffix.clear();
        new_suffix.reserve(seq.size());
        // Propagate orientation per step: derive from movement direction when rotation is on
        {
            int cur_ori = start_ori;
            for (int fi = 0; fi < (int)seq.size(); ++fi) {
                if (consider_rotation && fi > 0) {
                    int d = G.get_direction(seq[fi-1].first, seq[fi].first);
                    if (d >= 0 && d < 4) cur_ori = d;
                    // if d==4 (wait) or d<0 (error), keep the previous orientation
                }
                new_suffix.emplace_back(seq[fi].first, seq[fi].second,
                                        consider_rotation ? cur_ori : -1);
            }
        }
        fell_back = true;
    }

    if (new_suffix.empty()) {
        bundle_dirty[k] = false;
        metrics_after_stitch(used_sipp, sipp_ok, fell_back, false);
        return;
    }

    // prefix + suffix
    std::vector<State> new_path;
    new_path.reserve(paths[k].size() + new_suffix.size());
    for (int i = 0; i < (int)paths[k].size() && paths[k][i].timestep < timestep; ++i)
        new_path.push_back(paths[k][i]);
    new_path.insert(new_path.end(), new_suffix.begin(), new_suffix.end());
    paths[k] = std::move(new_path);

    suppress_replan_for(k);
    bundle_dirty[k] = false;
    metrics_after_stitch(used_sipp, sipp_ok, fell_back, false);

    if (g_replan_cooldown.size() == (size_t)num_of_drives)
        g_replan_cooldown[k] = REPLAN_COOLDOWN_TICKS;
}

std::vector<int> KivaSystem::compute_batch_order() const
{
    std::vector<int> pool;
    if (stitch_target == -1) {
        pool.reserve(num_of_drives);
        for (int k = 0; k < num_of_drives; ++k) pool.push_back(k);
    } else if (stitch_target >= 0 && stitch_target < num_of_drives) {
        pool.push_back(stitch_target);
    } else {
        return pool;
    }

    pool.erase(std::remove_if(pool.begin(), pool.end(), [&](int k){
        if (!capacity_mode) return true;
        if (k < 0 || k >= (int)bundle.size()) return true;
        if (bundle[k].empty()) return true;
        if (restitch_on_change && !bundle_dirty[k] && timestep > 0) return true;
        return false;
    }), pool.end());

    // keep ordering simple
    return pool;
}

void KivaSystem::plan_stitched_batch()
{
    auto to_go = compute_batch_order();

    // decay cooldown once per tick
    if (g_replan_cooldown.size() == (size_t)num_of_drives) {
        for (int i = 0; i < num_of_drives; ++i) if (g_replan_cooldown[i] > 0) --g_replan_cooldown[i];
    }

    const int AGENTS   = num_of_drives;
    const int PLWIN    = effective_planning_window(planning_window, AGENTS);
    const int horizonT = timestep + PLWIN;

    // rebuild global SII every tick (quality)
    if ((timestep - g_sii_built_at) >= SII_REBUILD_PERIOD) {
        g_sii_horizonT = horizonT;
        build_global_vertex_sii_compressed(G, paths, g_sii_horizonT, g_sii_tick);
        g_sii_built_at = timestep;
    }
    // rebuild global edge SII every tick
    if ((timestep - g_edge_sii_built_at) >= SII_REBUILD_PERIOD) {
        g_edge_sii_horizonT = horizonT;
        build_global_edge_sii_compressed(G, paths, g_edge_sii_horizonT);
        g_edge_sii_built_at = timestep;
    }
    // chokepoint heat
    if ((timestep - g_choke_built_at) >= 1) {
        g_choke_horizonT = horizonT;
        build_choke_heat(G, paths, timestep, g_choke_horizonT);
        g_choke_built_at = timestep;
    }

    // per-tick budget: scale with agents
    int BUDGET = std::max(4, AGENTS / 5);  // ~20%
    if ((int)to_go.size() > BUDGET) to_go.resize(BUDGET);

    for (int k : to_go) {
        plan_stitched_for_agent(k);
    }
}

// ------------------------------- Metrics ------------------------------------
void KivaSystem::metrics_begin_tick()
{
    m_tick_stitched_agents = 0;
    m_tick_sipp_success    = 0;
    m_tick_sipp_fallback   = 0;
    m_tick_skipped_clean   = 0;
}

void KivaSystem::metrics_after_stitch(bool used_sipp, bool sipp_ok, bool fell_back, bool skipped_clean)
{
    if (skipped_clean) { m_tick_skipped_clean++; m_skipped_clean_total++; return; }

    m_stitch_attempts_total++;
    m_tick_stitched_agents++;
    m_stitch_agents_ticks++;

    if (used_sipp) {
        if (sipp_ok) { m_tick_sipp_success++; m_sipp_success_total++; }
        else         { m_sipp_fail_total++; }
    }
    if (fell_back)  { m_tick_sipp_fallback++; m_sipp_fallback_total++; }
}

void KivaSystem::metrics_end_tick_and_maybe_log()
{
    if (metrics_verbose) {
        cout << "[t=" << timestep << "] stitched_agents=" << m_tick_stitched_agents
             << " sipp_ok=" << m_tick_sipp_success
             << " fallbacks=" << m_tick_sipp_fallback
             << " skipped_clean=" << m_tick_skipped_clean
             << endl;
    }
    if (metrics_csv_enabled && !metrics_csv_path.empty()) {
        std::ofstream f(metrics_csv_path, std::ios::app);
        if (f.tellp() == 0) {
            f << "t,stitched_agents,sipp_ok,fallbacks,skipped_clean\n";
        }
        f << timestep << ","
          << m_tick_stitched_agents << ","
          << m_tick_sipp_success << ","
          << m_tick_sipp_fallback << ","
          << m_tick_skipped_clean << "\n";
    }
}

void KivaSystem::metrics_print_summary() const
{
    cout << "\n=== Stitching/Capacity Summary ===\n";
    cout << "stitch_attempts_total:   " << m_stitch_attempts_total   << "\n";
    cout << "stitched_agents_ticks:   " << m_stitch_agents_ticks     << "\n";
    cout << "sipp_success_total:      " << m_sipp_success_total      << "\n";
    cout << "sipp_fallback_total:     " << m_sipp_fallback_total     << "\n";
    cout << "sipp_fail_total:         " << m_sipp_fail_total         << "\n";
    cout << "skipped_clean_total:     " << m_skipped_clean_total     << "\n";
    cout << "restitches_total:        " << m_restitches_total        << "\n";
    cout << "=================================\n";
}

// ------------------------------- Debug print --------------------------------
void KivaSystem::debug_print_capacity_state() const
{
    if (!capacity_mode) return;

    std::ostringstream oss;
    oss << "[t=" << timestep << "] CAPACITY STATE\n";
    for (int k = 0; k < num_of_drives; ++k) {
        oss << "  agent " << k
            << " cap=" << cap_of(k)
            << " bundle=[";
        if (k >= 0 && k < (int)bundle.size()) {
            for (size_t i = 0; i < bundle[k].size(); ++i) {
                oss << clamp_vertex(G, bundle[k][i].first);
                if (i + 1 < bundle[k].size()) oss << ",";
            }
        }
        oss << "] rest=("
            << ((k >= 0 && k < (int)rest.size()) ? rest[k].size() : 0)
            << ")";

        if (k >= 0 && k < (int)bundle_dirty.size())
            oss << " dirty=" << (bundle_dirty[k] ? "Y" : "N");

        oss << "\n";
    }

    oss << "  replans: [";
    bool first = true;
    for (int a : new_agents) {
        if (!first) oss << ",";
        first = false;
        oss << a;
    }
    oss << "]\n";

    std::cout << oss.str();
}

static int find_exterior_travel_cell_for_endpoint(const BasicGraph& G, int raw_ep)
{
    if (raw_ep >= 0 && raw_ep < (int)G.types.size() && G.types[raw_ep] == "Endpoint")
    {
        // Check NORTH (1) and SOUTH (3) neighbors.
        // The service cell must be in a true travel aisle where a 3-cell robot
        // can validly occupy the position horizontally (valid_3cell_state(nb, 0)).
        for (int dir : {1, 3})
        {
            int nb = raw_ep + G.move[dir];
            if (nb >= 0 && nb < G.rows * G.cols && G.get_Manhattan_distance(raw_ep, nb) == 1)
                if (G.is_cell_valid_for_robot(nb) && G.valid_3cell_state(nb, 0))
                {
                    return nb;
                }
        }
    }

    // Fallback: Clamp to valid 3-cell interior row (1..rows-2)
    if (raw_ep >= 0 && raw_ep < G.size())
    {
        int r = raw_ep / G.cols;
        int c = raw_ep % G.cols;
        int clamped_r = std::max(1, std::min(G.rows - 2, r));
        int target = clamped_r * G.cols + c;
        if (G.is_cell_valid_for_robot(target) && G.valid_3cell_state(target, 0))
            return target;
    }
    return raw_ep;
}

static bool is_goal_service_cell_conflicting(const KivaGrid& G, int target_cell, int requesting_agent, int num_of_drives,
                                            std::vector<std::vector<State>>& paths,
                                            std::vector<std::vector<std::pair<int, int>>>& goal_locations,
                                            int timestep, bool consider_rotation)
{
    int target_footprint[5];
    G.get_5cell_occupied_cells(target_cell, 0, target_footprint);

    for (int other = 0; other < num_of_drives; other++)
    {
        if (other == requesting_agent) continue;

        // 1. Check against other agent's current 5-cell position at this timestep
        State other_st = safe_path_at(paths, G, other, timestep, consider_rotation);
        int other_pos_cells[5];
        G.get_5cell_occupied_cells(other_st.location, other_st.orientation, other_pos_cells);

        for (int tc = 0; tc < 5; tc++)
        {
            for (int oc = 0; oc < 5; oc++)
            {
                if (target_footprint[tc] >= 0 && target_footprint[tc] < (int)G.types.size() &&
                    target_footprint[tc] == other_pos_cells[oc] && G.types[target_footprint[tc]] != "Magic" &&
                    G.types[target_footprint[tc]] != "Obstacle" && G.types[target_footprint[tc]] != "Endpoint")
                    return true;
            }
        }

        // 2. Check against other agent's queued goal locations
        for (const auto& g : goal_locations[other])
        {
            int other_goal_cells[5];
            G.get_5cell_occupied_cells(g.first, 0, other_goal_cells);
            for (int tc = 0; tc < 5; tc++)
            {
                for (int ogc = 0; ogc < 5; ogc++)
                {
                    if (target_footprint[tc] >= 0 && target_footprint[tc] < (int)G.types.size() &&
                        target_footprint[tc] == other_goal_cells[ogc] && G.types[target_footprint[tc]] != "Magic" &&
                        G.types[target_footprint[tc]] != "Obstacle" && G.types[target_footprint[tc]] != "Endpoint")
                        return true;
                }
            }
        }
    }
    return false;
}

static int pick_random_unblocked_endpoint(const KivaGrid& G, int curr_loc, int requesting_agent, int num_of_drives,
                                           std::vector<std::vector<State>>& paths,
                                           std::vector<std::vector<std::pair<int, int>>>& goal_locations,
                                           int timestep, bool consider_rotation)
{
    int raw_next = pick_random_endpoint_in_zone(G, requesting_agent, curr_loc);
    int target_cell = find_exterior_travel_cell_for_endpoint(G, raw_next);

    int retry_count = 64;
    while (retry_count-- > 0)
    {
        if (!is_goal_service_cell_conflicting(G, target_cell, requesting_agent, num_of_drives, paths, goal_locations, timestep, consider_rotation))
        {
            return target_cell;
        }
        raw_next = pick_random_endpoint_in_zone(G, requesting_agent, raw_next);
        target_cell = find_exterior_travel_cell_for_endpoint(G, raw_next);
    }
    return target_cell;
}

// -------------------------------- update ------------------------------------
void KivaSystem::update_goal_locations()
{
    if (!LRA_called)
        new_agents.clear();

    // Open a SEPARATE trace file for UGL (avoid double-handle on crash_trace.txt)
    std::ofstream gl_trace(outfile + "/ugl_trace.txt", std::ios::app);
    gl_trace << "  [UGL] enter t=" << timestep << std::endl; gl_trace.flush();

    // Sanitize initial start orientations and goal locations for 3-cell footprint
    for (int k = 0; k < num_of_drives; k++)
    {
        gl_trace << "  [UGL] sanitize k=" << k << std::endl; gl_trace.flush();
        if (timestep == 0 && !G.valid_3cell_state(starts[k].location, starts[k].orientation))
        {
            for (int dir = 0; dir < 4; dir++)
            {
                if (G.valid_3cell_state(starts[k].location, dir))
                {
                    starts[k].orientation = dir;
                    if (!paths[k].empty())
                        paths[k][0].orientation = dir;
                    break;
                }
            }
        }
        for (auto& g : goal_locations[k])
        {
            gl_trace << "  [UGL] k=" << k << " find_exterior g.first=" << g.first << std::endl; gl_trace.flush();
            g.first = find_exterior_travel_cell_for_endpoint(G, g.first);
            gl_trace << "  [UGL] k=" << k << " is_goal_service_cell_conflicting g.first=" << g.first << std::endl; gl_trace.flush();
            if (is_goal_service_cell_conflicting(G, g.first, k, num_of_drives, paths, goal_locations, timestep, consider_rotation))
            {
                gl_trace << "  [UGL] k=" << k << " pick_random_unblocked g.first=" << g.first << std::endl; gl_trace.flush();
                g.first = pick_random_unblocked_endpoint(G, g.first, k, num_of_drives, paths, goal_locations, timestep, consider_rotation);
            }
        }
    }
    gl_trace << "  [UGL] sanitize loop done" << std::endl; gl_trace.flush();

    if (capacity_mode)
    {
        for (int k = 0; k < num_of_drives; ++k) {
            bool popped = bundle_on_goal_reached(k);
            size_t size_before = bundle[k].size();
            maybe_autorefill_rest(k);
            bool topped = bundle_maybe_top_up(k);
            bool changed = popped || topped;

            if (safety_mode) { reorder_bundle_by_dvs(k); changed = true; }

            if (changed) bundle_dirty[k] = true;

            if (timestep == 0 || changed || bundle[k].size() != size_before) {
                new_agents.emplace_back(k);
            }
        }
        bundle_mirror_to_engine();
        if (capacity_debug) debug_print_capacity_state();
        gl_trace << "  [UGL] capacity_mode done" << std::endl; gl_trace.flush();
        return;
    }

    // legacy update for non-capacity
    if (hold_endpoints)
    {
        gl_trace << "  [UGL] hold_endpoints branch" << std::endl; gl_trace.flush();
        unordered_map<int, int> held_locations;
        for (int k = 0; k < num_of_drives; k++)
        {
            gl_trace << "  [UGL] hold_ep k=" << k << std::endl; gl_trace.flush();
            int curr = safe_path_at(paths, G, k, timestep, consider_rotation).location;
            if (goal_locations[k].empty())
            {
                int raw_next = pick_random_endpoint_except(G, curr);
                int next = find_exterior_travel_cell_for_endpoint(G, raw_next);
                int attempts = 0;
                while ((raw_next == curr || held_endpoints.find(raw_next) != held_endpoints.end() || held_endpoints.find(next) != held_endpoints.end()) && attempts++ < 100)
                {
                    raw_next = pick_random_endpoint_except(G, curr);
                    next = find_exterior_travel_cell_for_endpoint(G, raw_next);
                }
                goal_locations[k].clear();
                goal_locations[k].emplace_back(next, 0);
                held_endpoints.insert(raw_next);
                held_endpoints.insert(next);
            }
            if (paths[k].back().location == clamp_vertex(G, goal_locations[k].back().first) &&
                paths[k].back().timestep >= goal_locations[k].back().second)
            {
                // Goal reached: generate a new goal for agent k
                goal_locations[k].clear();
                int raw_next = pick_random_endpoint_except(G, curr);
                int next = find_exterior_travel_cell_for_endpoint(G, raw_next);
                int attempts = 0;
                while ((raw_next == curr || held_endpoints.find(raw_next) != held_endpoints.end() || held_endpoints.find(next) != held_endpoints.end()) && attempts++ < 100)
                {
                    raw_next = pick_random_endpoint_except(G, curr);
                    next = find_exterior_travel_cell_for_endpoint(G, raw_next);
                }
                goal_locations[k].emplace_back(next, 0);
                held_endpoints.insert(raw_next);
                held_endpoints.insert(next);
                new_agents.emplace_back(k);

                int agent = k;
                int loc = clamp_vertex(G, goal_locations[k].back().first);
                auto it = held_locations.find(loc);
                while (it != held_locations.end())
                {
                    int removed_agent = it->second;
                    new_agents.remove(removed_agent);
                    cout << "Agent " << removed_agent << " has to wait for agent " << agent
                         << " because of location " << loc << endl;
                    held_locations[loc] = agent;
                    agent = removed_agent;
                    loc = safe_path_at(paths, G, agent, timestep, consider_rotation).location;
                    it = held_locations.find(loc);
                }
                held_locations[loc] = agent;
            }
            else
            {
                if (held_locations.find(clamp_vertex(G, goal_locations[k].back().first)) == held_locations.end())
                {
                    held_locations[clamp_vertex(G, goal_locations[k].back().first)] = k;
                    new_agents.emplace_back(k);
                    continue;
                }
                int agent = k;
                int loc = curr;
                cout << "Agent " << agent
                     << " has to wait for agent "
                     << held_locations[clamp_vertex(G, goal_locations[k].back().first)]
                     << " because of location "
                     << clamp_vertex(G, goal_locations[k].back().first)
                     << endl;

                auto it = held_locations.find(loc);
                while (it != held_locations.end())
                {
                    int removed_agent = it->second;
                    new_agents.remove(removed_agent);
                    cout << "Agent " << removed_agent << " has to wait for agent "
                         << agent << " because of location " << loc << endl;
                    held_locations[loc] = agent;
                    agent = removed_agent;
                    loc = safe_path_at(paths, G, agent, timestep, consider_rotation).location;
                    it = held_locations.find(loc);
                }
                held_locations[loc] = agent;
            }
        }
    }
    else
    {
        gl_trace << "  [UGL] non-hold branch" << std::endl; gl_trace.flush();
        for (int k = 0; k < num_of_drives; k++)
        {
            gl_trace << "  [UGL] else k=" << k << " safe_path_at..." << std::endl; gl_trace.flush();
            int curr = safe_path_at(paths, G, k, timestep, consider_rotation).location;
            gl_trace << "  [UGL] else k=" << k << " curr=" << curr << " goal_empty=" << goal_locations[k].empty() << std::endl; gl_trace.flush();
            if (useDummyPaths)
            {
                if (goal_locations[k].empty())
                {
                    int home = (!G.agent_home_locations.empty() && k < (int)G.agent_home_locations.size())
                             ? clamp_vertex(G, G.agent_home_locations[k]) : 0;
                    goal_locations[k].emplace_back(home, 0);
                }
                if (goal_locations[k].size() == 1)
                {
                    int raw_next = pick_random_endpoint_except(G, curr);
                    int target_cell = find_exterior_travel_cell_for_endpoint(G, raw_next);
                    goal_locations[k].emplace(goal_locations[k].begin(), target_cell, 0);
                    new_agents.emplace_back(k);
                }
            }
            else
            {
                // Ensure there is always at least 1 goal in the queue.
                if (goal_locations[k].empty())
                {
                    gl_trace << "  [UGL] else k=" << k << " calling pick_random_unblocked..." << std::endl; gl_trace.flush();
                    int target_cell = pick_random_unblocked_endpoint(G, curr, k, num_of_drives, paths, goal_locations, timestep, consider_rotation);
                    gl_trace << "  [UGL] else k=" << k << " got target_cell=" << target_cell << std::endl; gl_trace.flush();
                    goal_locations[k].emplace_back(target_cell, 0);
                    new_agents.emplace_back(k);
                }
            }
        }
    }
    gl_trace << "  [UGL] exit" << std::endl; gl_trace.flush();
}

// ------------------------------- simulate -----------------------------------
void KivaSystem::simulate(int simulation_time)
{
    std::cout << "*** Simulating " << seed << " ***" << std::endl;
    this->simulation_time = simulation_time;
    initialize();

    std::ofstream crash_log(outfile + "/crash_trace.txt", std::ios::out);
    crash_log << "=== CRASH TRACE START ===" << std::endl;
    crash_log.flush();
    // Make crash_log accessible to solve() via a global pointer
    extern std::ofstream* g_crash_log;
    g_crash_log = &crash_log;

    for (; timestep < simulation_time; timestep += simulation_window)
    {
        crash_log << "--- LOOP timestep=" << timestep << " ---" << std::endl; crash_log.flush();
        std::cout << "Timestep " << timestep << std::endl;

        metrics_begin_tick();
        crash_log << "  metrics_begin_tick OK" << std::endl; crash_log.flush();

        update_start_locations();
        crash_log << "  update_start_locations OK" << std::endl; crash_log.flush();

        update_goal_locations();
        crash_log << "  update_goal_locations OK" << std::endl; crash_log.flush();

        if (capacity_mode && stitch_mode) {
            plan_stitched_batch();
            crash_log << "  plan_stitched_batch OK" << std::endl; crash_log.flush();
        }

        solve();
        crash_log << "  solve() OK" << std::endl; crash_log.flush();

        auto new_finished_tasks = move();
        crash_log << "  move() OK. finished_tasks.size()=" << new_finished_tasks.size() << std::endl; crash_log.flush();

        for (auto task : new_finished_tasks)
        {
            int id, loc, t;
            std::tie(id, loc, t) = task;
            // In capacity_mode, bundle_on_goal_reached() is the sole authority
            // on task counting (it enforces the task_delay dwell). Counting here
            // would cause double-counting and instant-pop of Goals B and C.
            if (!capacity_mode) {
                finished_tasks[id].emplace_back(loc, t);
                num_of_tasks++;
            }
            if (hold_endpoints)
            {
                held_endpoints.erase(loc);
                for (int nb : G.get_neighbors(loc))
                    held_endpoints.erase(nb);
            }
        }

        // Lifelong MAPF: do not abort on temporary waiting ticks when PBS solver is succeeding
        /*
        {
            static int congested_ticks = 0;
            if (congested())
            {
                congested_ticks++;
                if (congested_ticks >= 10)
                {
                    cout << "***** Too many traffic jams (10 consecutive ticks) ***" << endl;
                    break;
                }
            }
            else
            {
                congested_ticks = 0;
            }
        }
        */

        metrics_end_tick_and_maybe_log();
    }

    update_start_locations();
    std::cout << std::endl << "Done!" << std::endl;
    metrics_print_summary();

       std::cout << "======================================" << std::endl;
    std::cout << " Total tasks completed: " << num_of_tasks << std::endl;
    std::cout << "======================================" << std::endl;
    std::cout << "Average throughput: "
          << std::fixed << std::setprecision(3)
          << (double)num_of_tasks / (double)(timestep + 1)
          << " tasks per timestep" << std::endl;


    save_results();
}
