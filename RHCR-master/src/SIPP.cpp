#include "SIPP.h"
#include <fstream>

extern std::ofstream* g_crash_log;


Path SIPP::updatePath(const BasicGraph& G, const SIPPNode* goal)
{
    Path path(goal->state.timestep + 1);
    path_cost = goal->getFVal();
    num_of_conf = goal->conflicts;

    const SIPPNode* curr = goal;
    while (true)
    {
        if (curr->parent == nullptr) // root node
        {
            for (int t = curr->state.timestep; t >= 0; t--)
            {
                path[t] = State(curr->state.location, t, curr->state.orientation);
            }
            break;
        }
        else
        {
            const SIPPNode* prev = curr->parent;
            int degree = G.get_rotate_degree(prev->state.orientation, curr->state.orientation);
            int t = prev->state.timestep + 1;
            if (degree == 1) // turn right or turn left
            {
                path[t] = State(prev->state.location, t, curr->state.orientation);
                t++;
            }
            else if (degree == 2) // turn back
            {
                path[t] = State(prev->state.location, t, (prev->state.orientation + 1) % 4); // turn right
                t++;
                path[t] = State(prev->state.location, t, curr->state.orientation); // turn right
                t++;
            }
            while ( t < curr->state.timestep)
            {
                path[t] = State(prev->state.location, t, curr->state.orientation); // wait at prev location
                t++;
            }
            path[curr->state.timestep] = State(curr->state.location, curr->state.timestep, curr->state.orientation); // move to current location
            curr = prev;
        }
    }
    return path;
}


////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// return true if a path found (and updates vector<int> path) or false if no path exists
// after max_timestep, switch from time-space A* search to normal A* search
Path SIPP::run(const BasicGraph& G, const State& start,
               const vector<pair<int, int> >& goal_location,
               ReservationTable& rt)
{
    if (g_crash_log) { (*g_crash_log) << "        [SIPP::run] enter start=" << start.location << " goals=" << goal_location.size() << std::endl; g_crash_log->flush(); }
    num_expanded = 0;
    num_generated = 0;
    runtime = 0;
    clock_t t = std::clock();
    double h_val = compute_h_value(G, start.location, 0, goal_location);
    if (g_crash_log) { (*g_crash_log) << "        [SIPP::run] h_val=" << h_val << std::endl; g_crash_log->flush(); }
	if (h_val > INT_MAX)
	{
		std::cout << "[DEBUG SIPP FAIL] compute_h_value returned > INT_MAX for start=" << start.location << std::endl;
		return Path();
	}
    if (g_crash_log) { (*g_crash_log) << "        [SIPP::run] calling getFirstSafeInterval" << std::endl; g_crash_log->flush(); }
    Interval interval = rt.getFirstSafeInterval(start.location);
    if (g_crash_log) { (*g_crash_log) << "        [SIPP::run] getFirstSafeInterval done" << std::endl; g_crash_log->flush(); }
	
    {
        Interval init_interval = (std::get<0>(interval) == 0) ? interval : std::make_tuple(0, INTERVAL_MAX, false);
        auto node = new SIPPNode(start, 0, h_val, init_interval, nullptr, 0);
        num_generated++;
        node->open_handle = open_list.push(node);
        node->in_openlist = true;
        allNodes_table.insert(node);
        min_f_val = node->getFVal();
        focal_bound = std::max(min_f_val * suboptimal_bound, min_f_val + 5);
        node->focal_handle = focal_list.push(node);
        node->in_focallist = true;
    }
	int earliest_holding_time = 0;
	if (hold_endpoints && !goal_location.empty())
		earliest_holding_time = rt.getHoldingTimeFromSIT(goal_location.back().first);
    if (g_crash_log) { (*g_crash_log) << "        [SIPP::run] entering search loop" << std::endl; g_crash_log->flush(); }
    while (!focal_list.empty() && num_expanded < 3000)
    {
        SIPPNode* curr = focal_list.top(); focal_list.pop();
        curr->in_focallist = false;
        open_list.erase(curr->open_handle);
        curr->in_openlist = false;
        num_expanded++;
        if (g_crash_log) { (*g_crash_log) << "        [SIPP::loop] exp=" << num_expanded << " loc=" << curr->state.location << " t=" << curr->state.timestep << " ori=" << curr->state.orientation << " goal_id=" << curr->goal_id << std::endl; g_crash_log->flush(); }

         // update goal id
        int req_release = std::max(goal_location[curr->goal_id].second, curr->arrival_t + task_delay);
        if (curr->state.location == goal_location[curr->goal_id].first)
        {
            if (curr->state.timestep < req_release && req_release <= std::get<1>(curr->interval))
            {
                curr->state.timestep = req_release;
            }
            if (curr->state.timestep >= req_release)
            {
                curr->goal_id++;
                if (curr->goal_id == (int)goal_location.size() &&
                    earliest_holding_time > curr->state.timestep)
                    curr->goal_id--;
            }
        }
		// check if the popped node is a goal
		if (curr->goal_id == (int)goal_location.size())
		{
			Path path = updatePath(G, curr);
			releaseClosedListNodes();
			open_list.clear();
			focal_list.clear();
			runtime = (std::clock() - t) * 1.0 / CLOCKS_PER_SEC;
            if (g_crash_log) { (*g_crash_log) << "        [SIPP::loop] goal reached, path_size=" << path.size() << std::endl; g_crash_log->flush(); }
			return path;
		}

        if (g_crash_log) { (*g_crash_log) << "        [SIPP::loop] expanding 4 moves..." << std::endl; g_crash_log->flush(); }
        // expand the nodes
        for (int orientation = 0; orientation < 4; orientation++) // move
        {
            if (!G.valid_move(curr->state.location, orientation)) // the edge is blocked
                continue;
            int degree;
            if (curr->state.orientation < 0)
                degree = 0;
            else
                degree = G.get_rotate_degree(curr->state.orientation, orientation);
            if (degree > std::get<1>(curr->interval) - curr->state.timestep) // don't have enough time to turn
                continue;
            int location = curr->state.location + G.move[orientation];
            if (curr->state.orientation >= 0)
            {
                // Check move destination and intermediate rotation if turning 180 degrees
                if (!G.valid_3cell_state(location, orientation))
                    continue;
                if (degree == 2 && !G.valid_3cell_rotation(curr->state.location, curr->state.orientation, (curr->state.orientation + 1) % 4))
                    continue;
                if (degree > 0 && !G.valid_3cell_rotation(curr->state.location, curr->state.orientation, orientation))
                    continue;
            }
            double h_val = compute_h_value(G, location, curr->goal_id, goal_location);
            if (h_val > INT_MAX)   // This vertex cannot reach the goal vertex
                continue;
            int min_timestep = curr->state.timestep + degree + 1;
            for (auto interval : rt.getSafeIntervals(curr->state.location, location, orientation, min_timestep, std::get<1>(curr->interval) + 1))
            {
                if (curr->state.orientation < 0)
                {
                    generate_node(interval, curr, G, rt, location, min_timestep, -1, h_val);
                }
                else
                {
                    generate_node(interval, curr, G, rt, location, min_timestep, orientation, h_val);
                }
            }
        }  // end for loop that generates successors

        // Backward movement: robot slides one cell in reverse (opposite direction)
        // without changing orientation. No rotation needed — like a vehicle reversing.
        if (curr->state.orientation >= 0)
        {
            int back_dir = (curr->state.orientation + 2) % 4; // opposite direction
            int back_location = curr->state.location + G.move[back_dir];
            // 3-cell check and valid edge check at new position with SAME orientation
            if (G.valid_move(curr->state.location, back_dir) && G.valid_3cell_state(back_location, curr->state.orientation))
            {
                double h_val = compute_h_value(G, back_location, curr->goal_id, goal_location);
                if (h_val <= INT_MAX)
                {
                    int min_timestep = curr->state.timestep + 1;
                    for (auto interval : rt.getSafeIntervals(curr->state.location, back_location, curr->state.orientation, min_timestep, std::get<1>(curr->interval) + 1))
                    {
                        generate_node(interval, curr, G, rt, back_location, min_timestep, curr->state.orientation, h_val);
                    }
                }
            }
        }

        // wait to the successive interval (always allowed in SIPP)
        {
            int location = curr->state.location;
            int min_timestep = std::get<1>(curr->interval);
            int orientation = curr->state.orientation;
            Interval interval;
            bool found = rt.findSafeInterval(interval, location, min_timestep);
            if (found)
            {
				if (curr->state.orientation < 0)
				{
					generate_node(interval, curr, G, rt, location, min_timestep, -1, curr->h_val);
				}
				else
				{
					generate_node(interval, curr, G, rt, location, min_timestep, orientation, curr->h_val);
					if (G.valid_3cell_rotation(location, orientation, (orientation + 1) % 4))
						generate_node(interval, curr, G, rt, location, min_timestep, (orientation + 1) % 4, curr->h_val);
					if (G.valid_3cell_rotation(location, orientation, (orientation + 3) % 4))
						generate_node(interval, curr, G, rt, location, min_timestep, (orientation + 3) % 4, curr->h_val);
					if (std::get<1>(curr->interval) - curr->state.timestep > 1 && G.valid_3cell_rotation(location, orientation, (orientation + 2) % 4))
						generate_node(interval, curr, G, rt, location, min_timestep, (orientation + 2) % 4, curr->h_val);
				}
            }
        }

        // update FOCAL if min f-val increased or focal_list is empty
        if (focal_list.empty())
        {
            if (open_list.empty())
            {
                if (prioritize_start)
                {
                    Interval interval = rt.getFirstSafeInterval(start.location);
                    Interval interval2 = make_tuple(std::get<1>(interval), INTERVAL_MAX, 0);
                    double h_val = compute_h_value(G, start.location, 0, goal_location);
                    auto node2 = new SIPPNode(start, 0, h_val, interval2, nullptr, 0);
                    num_generated++;
                    node2->open_handle = open_list.push(node2);
                    node2->in_openlist = true;
                    allNodes_table.insert(node2);
                    min_f_val = node2->getFVal();
                    focal_bound = min_f_val;
                    node2->focal_handle = focal_list.push(node2);
                    node2->in_focallist = true;
                }
                else
                {
                    break;
                }
            }
            else
            {
                SIPPNode* open_head = open_list.top();
                double new_min_f_val = open_head->getFVal();
                double new_focal_bound = std::max(new_min_f_val * suboptimal_bound, new_min_f_val + 5);
                for (SIPPNode* n : open_list)
                {
                    if (n->getFVal() <= new_focal_bound && !n->in_focallist)
                    {
                        n->focal_handle = focal_list.push(n);
                        n->in_focallist = true;
                    }
                }
                min_f_val = new_min_f_val;
                focal_bound = new_focal_bound;
            }
        }
        else
        {
            SIPPNode* open_head = open_list.top();
            if (open_head->getFVal() > min_f_val)
            {
                double new_min_f_val = open_head->getFVal();
                double new_focal_bound = std::max(new_min_f_val * suboptimal_bound, new_min_f_val + 5);
                for (SIPPNode* n : open_list)
                {
                    if (n->getFVal() > focal_bound && n->getFVal() <= new_focal_bound && !n->in_focallist)
                    {
                        n->focal_handle = focal_list.push(n);
                        n->in_focallist = true;
                    }
                }
                min_f_val = new_min_f_val;
                focal_bound = new_focal_bound;
            }
        }

    }  // end while loop

    // no path found
    releaseClosedListNodes();
    open_list.clear();
    focal_list.clear();
    return Path();
}


/*void SIPP::generate_node(SIPPNode* curr, const SortationGrid& G,
                         int location, int timestep, int orientation, double h_val)
{
    int wait_time = timestep - curr->state.timestep - 1; // inlcude rotate time
    double travel_time = 1;
    if (!travel_times.empty())
    {
        int dir = G.get_direction(curr->state.location, location);
        travel_time += travel_times[curr->state.location][dir];
    }
    double g_val = curr->g_val + travel_time * (wait_time * G.get_weight(curr->state.location, curr->state.location)
                   + G.get_weight(curr->state.location, location));

    int conflicts = curr->conflicts;

    // generate (maybe temporary) node
    auto next = new SIPPNode(State(location, timestep, orientation),
                             g_val, h_val, Interval(window + 1, INTERVAL_MAX, 0), curr, conflicts);

    // try to retrieve it from the hash table
    auto it = allNodes_table.find(next);
    if (it != allNodes_table.end() && (*it)->state.timestep != next->state.timestep)
    { // arrive at the same interval at different timestep
        int waiting_time = (*it)->state.timestep - next->state.timestep;
        double waiting_cost = abs(G.get_weight(next->state.location, next->state.location) * waiting_time);
        double next_f_val = next->getFVal() + waiting_cost;
        if (waiting_time > 0 && next_f_val <= (*it)->getFVal())
        { // next arrives earlier with a smaller cost
            // so delete it
            // let the following update it with next
        }
        else if (waiting_time < 0 && next_f_val >= (*it)->getFVal())
        { // it arrives earlier with a smaller cost
            delete next; // so delete next
            return;
        }
        else // the later node arrives with a smaller cost, so they cannot be regarded as the same state
            it = allNodes_table.end();
    }
    if (it == allNodes_table.end())
    {
        next->open_handle = open_list.push(next);
        next->in_openlist = true;
        num_generated++;
        if (next->getFVal() <= focal_bound)
            next->focal_handle = focal_list.push(next);
        allNodes_table.insert(next);
        return;
    }

    // update existing node if needed (only in the open_list)
    SIPPNode* existing_next = *it;
    double existing_f_val = existing_next->getFVal();

    if (existing_next->in_openlist)
    {  // if its in the open list
        if (existing_f_val > g_val + h_val ||
            (existing_f_val == g_val + h_val && existing_next->conflicts > conflicts))
        {
            // if f-val decreased through this new path (or it remains the same and there's less internal conflicts)
            bool add_to_focal = false;  // check if it was above the focal bound before and now below (thus need to be inserted)
            bool update_in_focal = false;  // check if it was inside the focal and needs to be updated (because f-val changed)
            bool update_open = false;
            if ((g_val + h_val) <= focal_bound)
            {  // if the new f-val qualify to be in FOCAL
                if (existing_f_val > focal_bound)
                    add_to_focal = true;  // and the previous f-val did not qualify to be in FOCAL then add
                else
                    update_in_focal = true;  // and the previous f-val did qualify to be in FOCAL then update
            }
            if (existing_f_val > g_val + h_val)
                update_open = true;
            // update existing node
            existing_next->state = next->state;
            existing_next->g_val = g_val;
            existing_next->h_val = h_val;
            existing_next->parent = curr;
            existing_next->depth = next->depth;
            existing_next->conflicts = conflicts;
            // existing_next->move = next->move;

            if (update_open)
                open_list.increase(existing_next->open_handle);  // increase because f-val improved
            if (add_to_focal)
                existing_next->focal_handle = focal_list.push(existing_next);
            if (update_in_focal)
                focal_list.update(existing_next->focal_handle);  // should we do update? yes, because number of conflicts may go up or down
        }
    }
    else
    {  // if its in the closed list (reopen)
        if (existing_f_val > g_val + h_val ||
            (existing_f_val == g_val + h_val && existing_next->conflicts > conflicts))
        {
            // if f-val decreased through this new path (or it remains the same and there's less internal conflicts)
            existing_next->state = next->state;
            existing_next->g_val = g_val;
            existing_next->h_val = h_val;
            existing_next->parent = curr;
            existing_next->depth = next->depth;
            existing_next->conflicts = conflicts;
            existing_next->open_handle = open_list.push(existing_next);
            existing_next->in_openlist = true;
            if (existing_f_val <= focal_bound)
                existing_next->focal_handle = focal_list.push(existing_next);
        }
    }  // end update a node in closed list

    delete(next);  // not needed anymore -- we already generated it before
}*/


void SIPP::generate_node(const Interval& interval, SIPPNode* curr, const BasicGraph& G,
        const ReservationTable& rt, int location, int min_timestep, int orientation, double h_val)
{
    if (g_crash_log) { (*g_crash_log) << "          [generate_node] loc=" << location << " ori=" << orientation << " min_t=" << min_timestep << std::endl; g_crash_log->flush(); }
    int timestep  = max(std::get<0>(interval), min_timestep);
    if (timestep >= std::get<1>(interval))
    {
        if (g_crash_log) { (*g_crash_log) << "          [generate_node] timestep >= interval max, returning" << std::endl; g_crash_log->flush(); }
        return;
    }

    int transition_conflicts = 0;
    State prev_s = curr->state;

    if (g_crash_log) { (*g_crash_log) << "          [generate_node] step 1 checking constraints... curr_ori=" << curr->state.orientation << " ori=" << orientation << " curr_t=" << curr->state.timestep << " target_t=" << timestep << std::endl; g_crash_log->flush(); }

    if (curr->state.orientation < 0 || orientation < 0)
    {
        for (int t = curr->state.timestep + 1; t <= timestep; ++t)
        {
            State next_s(location, t, -1);
            if (t < timestep) next_s.location = curr->state.location;
            if (rt.isConstrained(prev_s, next_s)) {
                if (g_crash_log) { (*g_crash_log) << "          [generate_node] constrained at t=" << t << std::endl; g_crash_log->flush(); }
                return;
            }
            if (rt.isConflicting(prev_s, next_s)) transition_conflicts++;
            prev_s = next_s;
        }
    }
    else
    {
        int degree = G.get_rotate_degree(curr->state.orientation, orientation);
        int t = curr->state.timestep + 1;
        
        // 1. Turn immediately
        if (degree == 1)
        {
            State next_s(curr->state.location, t, orientation);
            if (rt.isConstrained(prev_s, next_s)) {
                if (g_crash_log) { (*g_crash_log) << "          [generate_node] constrained at rotate deg=1 t=" << t << std::endl; g_crash_log->flush(); }
                return;
            }
            if (rt.isConflicting(prev_s, next_s)) transition_conflicts++;
            prev_s = next_s;
            t++;
        }
        else if (degree == 2)
        {
            State next_s1(curr->state.location, t, (curr->state.orientation + 1) % 4);
            if (rt.isConstrained(prev_s, next_s1)) {
                if (g_crash_log) { (*g_crash_log) << "          [generate_node] constrained at rotate deg=2 step 1 t=" << t << std::endl; g_crash_log->flush(); }
                return;
            }
            if (rt.isConflicting(prev_s, next_s1)) transition_conflicts++;
            prev_s = next_s1;
            t++;
            
            State next_s2(curr->state.location, t, orientation);
            if (rt.isConstrained(prev_s, next_s2)) {
                if (g_crash_log) { (*g_crash_log) << "          [generate_node] constrained at rotate deg=2 step 2 t=" << t << std::endl; g_crash_log->flush(); }
                return;
            }
            if (rt.isConflicting(prev_s, next_s2)) transition_conflicts++;
            prev_s = next_s2;
            t++;
        }
        
        // 2. Wait at prev->state.location with NEW orientation
        while (t < timestep)
        {
            State next_s(curr->state.location, t, orientation);
            if (rt.isConstrained(prev_s, next_s)) {
                if (g_crash_log) { (*g_crash_log) << "          [generate_node] constrained at wait t=" << t << std::endl; g_crash_log->flush(); }
                return;
            }
            if (rt.isConflicting(prev_s, next_s)) transition_conflicts++;
            prev_s = next_s;
            t++;
        }
        
        // 3. Move to target location
        if (t == timestep)
        {
            State next_s(location, timestep, orientation);
            if (rt.isConstrained(prev_s, next_s)) {
                if (g_crash_log) { (*g_crash_log) << "          [generate_node] constrained at move t=" << timestep << std::endl; g_crash_log->flush(); }
                return;
            }
            if (rt.isConflicting(prev_s, next_s)) transition_conflicts++;
        }
    }

    if (g_crash_log) { (*g_crash_log) << "          [generate_node] step 2 calculating weight..." << std::endl; g_crash_log->flush(); }
    int wait_time = timestep - curr->state.timestep - 1; // inlcude rotate time
    double g_val = curr->g_val + wait_time * G.get_weight(curr->state.location, curr->state.location)
                   + G.get_weight(curr->state.location, location);

    int conflicts = curr->conflicts + transition_conflicts;

    if (g_crash_log) { (*g_crash_log) << "          [generate_node] step 3 constructing SIPPNode..." << std::endl; g_crash_log->flush(); }
    // generate (maybe temporary) node
    auto next = new SIPPNode(State(location, timestep, orientation),
                             g_val, h_val, interval, curr, conflicts);

    if (g_crash_log) { (*g_crash_log) << "          [generate_node] step 4 allNodes_table lookup..." << std::endl; g_crash_log->flush(); }

    // try to retrieve it from the hash table
    auto it = allNodes_table.find(next);
    /*if (it != allNodes_table.end() && (*it)->state.timestep != next->state.timestep)
    { // arrive at the same interval at different timestep
        int waiting_time = (*it)->state.timestep - next->state.timestep;
        double waiting_cost = abs(G.get_weight(next->state.location, next->state.location) * waiting_time);
        if (waiting_time > 0 && next->getFVal() + waiting_cost <= (*it)->getFVal())
        { // next arrives later with a smaller cost
            // let the following update it with next
        }
        else if (waiting_time < 0 && next->getFVal() >= (*it)->getFVal() + waiting_cost)
        { // next arrives earlier with a larger cost
            delete next; // so delete next
            return;
        }
        else // next arrives with a smaller cost, so they cannot be regarded as the same state
            it = allNodes_table.end(); // TODO: fix this bug! When later inserting this node to allNodes_table, it will not override the previous node.
    }*/
    if (it == allNodes_table.end())
    {
        next->open_handle = open_list.push(next);
        next->in_openlist = true;
        num_generated++;
        if (next->getFVal() <= focal_bound)
        {
            next->focal_handle = focal_list.push(next);
            next->in_focallist = true;
        }
        allNodes_table.insert(next);
        return;
    }

    // update existing node if needed (only in the open_list)
    SIPPNode* existing_next = *it;
    double existing_f_val = existing_next->getFVal();

    if (existing_next->in_openlist)
    {  // if its in the open list
        if (existing_f_val > g_val + h_val ||
            (existing_f_val == g_val + h_val && existing_next->conflicts > conflicts))
        {
            bool update_open = (existing_f_val > g_val + h_val);
            // update existing node
            existing_next->state = next->state;
            existing_next->g_val = g_val;
            existing_next->h_val = h_val;
            existing_next->parent = curr;
            existing_next->depth = next->depth;
            existing_next->conflicts = conflicts;

            if (update_open)
                open_list.update(existing_next->open_handle);
            if ((g_val + h_val) <= focal_bound)
            {
                if (existing_next->in_focallist)
                    focal_list.update(existing_next->focal_handle);
                else
                {
                    existing_next->focal_handle = focal_list.push(existing_next);
                    existing_next->in_focallist = true;
                }
            }
        }
    }
    else
    {  // if its in the closed list (reopen)
        if (existing_f_val > g_val + h_val ||
            (existing_f_val == g_val + h_val && existing_next->conflicts > conflicts))
        {
            // if f-val decreased through this new path (or it remains the same and there's less internal conflicts)
            existing_next->state = next->state;
            existing_next->g_val = g_val;
            existing_next->h_val = h_val;
            existing_next->parent = curr;
            existing_next->depth = next->depth;
            existing_next->conflicts = conflicts;
            existing_next->open_handle = open_list.push(existing_next);
            existing_next->in_openlist = true;
            if ((g_val + h_val) <= focal_bound)
            {
                existing_next->focal_handle = focal_list.push(existing_next);
                existing_next->in_focallist = true;
            }
        }
    }  // end update a node in closed list

    delete(next);  // not needed anymore -- we already generated it before
}

inline void SIPP::releaseClosedListNodes()
{
    for (auto it = allNodes_table.begin(); it != allNodes_table.end(); it++)
        delete (*it);
    allNodes_table.clear();
}




