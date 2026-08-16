#include "ReservationTable.h"

// update SIT at the given location
void ReservationTable::updateSIT(size_t location)
{
	if (sit.find(location) == sit.end())
	{
		const auto& it = ct.find(location);
		if (it != ct.end())
		{
			for (auto time_range : it->second)
				insertConstraint2SIT(location, time_range.first, time_range.second);
			// Do not erase ct[location] so isConstrained can still query ct
		}

		if (location < map_size) // vertex
		{
			for (int t = 0; t < (int)cat.size(); t++)
			{
				if (location < cat[t].size() && cat[t][location])
				{
					insertSoftConstraint2SIT(location, t, t + 1);
				}
			}
		}
		else // edge
		{
			auto edge = getEdge(location);
			for (int t = 1; t < (int)cat.size(); t++)
			{
				if (edge.first >= 0 && (size_t)edge.first < cat[t].size() && edge.second >= 0 && (size_t)edge.second < cat[t-1].size() &&
                    cat[t][edge.first] && cat[t - 1][edge.second])
				{
					insertSoftConstraint2SIT(location, t, t + 1);
				}
			}
		}
	}
}


//merge successive safe intervals with the same number of conflicts.
void ReservationTable::mergeIntervals(list<Interval >& intervals) const
{
	if (intervals.empty())
		return;
	auto prev = intervals.begin();
	auto curr = prev;
	++curr;
	while (curr != intervals.end())
	{
		if (std::get<1>(*prev) == std::get<0>(*curr) && std::get<2>(*prev) == std::get<2>(*curr))
		{
			*prev = make_tuple(std::get<0>(*prev), std::get<1>(*curr), std::get<2>(*prev));
			curr = intervals.erase(curr);
		}
		else
		{
			prev = curr;
			++curr;
		}
	}
}



int ReservationTable::getHoldingTimeFromSIT(int location)
{
	updateSIT(location);
	if (sit.find(location) == sit.end())
		return 0;
	int t = std::get<1>(sit[location].back());
	if (t < INTERVAL_MAX)
		return INTERVAL_MAX;
	for (auto p = sit[location].rbegin(); p != sit[location].rend(); ++p)
	{
		if (t == std::get<1>(*p))
			t = std::get<0>(*p);
		else
			break;
	}
	return t;
}

int ReservationTable::getHoldingTimeFromCT(int location) const
{
	const auto& it = ct.find(location);
	if (it == ct.end())
		return 0;

	int t = 0;
	for (auto time_range : it->second)
	{
		if (time_range.second >= 100000)
		{
			if (time_range.first > t)
				t = time_range.first;
		}
		else if (time_range.second > t)
		{
			t = time_range.second;
		}
	}
	return t;
}

set<int> ReservationTable::getConstrainedTimesteps(int location) const
{
    set<int> rst;
    const auto& it = ct.find(location);
    if (it == ct.end())
        return rst;

    for (auto time_range : it->second)
    {
        if (time_range.second == INTERVAL_MAX) // skip goal constraint
            continue;
        for (auto t = time_range.first; t < time_range.second; t++)
            rst.insert(t);
    }
    return rst;
}

void ReservationTable::insertConstraint2SIT(int location, int t_min, int t_max)
{
    if (sit.find(location) == sit.end())
    {
        if (t_min > 0)
        {
			sit[location].emplace_back(0, t_min, 0);
        }
		sit[location].emplace_back(t_max, INTERVAL_MAX, 0);
        return;
    }
    for (auto it = sit[location].begin(); it != sit[location].end();)
    {
        if (t_min >= std::get<1>(*it))
			++it; 
        else if (t_max <= std::get<0>(*it))
            break;
       else  if (std::get<0>(*it) < t_min && std::get<1>(*it) <= t_max)
        {
            (*it) = make_tuple(std::get<0>(*it), t_min, 0);
			++it;
        }
        else if (t_min <= std::get<0>(*it) && t_max < std::get<1>(*it))
        {
            (*it) = make_tuple(t_max, std::get<1>(*it), 0);
            break;
        }
        else if (std::get<0>(*it) < t_min && t_max < std::get<1>(*it))
        {
			sit[location].insert(it, make_tuple(std::get<0>(*it), t_min, 0));
            (*it) = make_tuple(t_max, std::get<1>(*it), 0);
            break;
        }
        else // constraint_min <= get<0>(*it) && get<1> <= constraint_max
        {
            it = sit[location].erase(it);
        }
    }
}

void ReservationTable::insertSoftConstraint2SIT(int location, int t_min, int t_max)
{
    if (sit.find(location) == sit.end())
    {
        if (t_min > 0)
        {
			sit[location].emplace_back(0, t_min, false);
        }
		sit[location].emplace_back(t_min, t_max, true);
		sit[location].emplace_back(t_max, INTERVAL_MAX, false);
        return;
    }
    for (auto it = sit[location].begin(); it != sit[location].end(); it++)
    {
        if (t_min >= std::get<1>(*it))
            continue;
        else if (t_max <= std::get<0>(*it))
            break;
		else if (std::get<2>(*it)) // the interval already has conflicts. No need to update
			continue;

        if (std::get<0>(*it) < t_min && std::get<1>(*it) <= t_max)
        {
			sit[location].insert(it, make_tuple(std::get<0>(*it), t_min, false));
			(*it) = make_tuple(t_min, std::get<1>(*it), true);
        }
        else if (t_min <= std::get<0>(*it) && t_max < std::get<1>(*it))
        {
			sit[location].insert(it, make_tuple(std::get<0>(*it), t_max, true));
            (*it) = make_tuple(t_max, std::get<1>(*it), false);
        }
        else if (std::get<0>(*it) < t_min && t_max < std::get<1>(*it))
        {
			sit[location].insert(it, make_tuple(std::get<0>(*it), t_min, false));
			sit[location].insert(it, make_tuple(t_min, t_max,  true));
            (*it) = make_tuple(t_max, std::get<1>(*it), false);
        }
        else // constraint_min <= get<0>(*it) && get<1> <= constraint_max
        {
            (*it) = make_tuple(std::get<0>(*it), std::get<1>(*it), true);
        }
    }
}


void ReservationTable::insertPath2CT(const Path& path)
{
	if (path.empty())
		return;
	for (size_t i = 0; i < path.size(); i++)
	{
		int t = path[i].timestep;
		if (t - k_robust <= window)
		{
			int cells5[5];
			G.get_5cell_occupied_cells(path[i].location, path[i].orientation, cells5);
			for (int c = 0; c < 5; c++)
			{
				if (cells5[c] >= 0 && cells5[c] < (int)G.types.size() && G.types[cells5[c]] != "Magic" && G.types[cells5[c]] != "Obstacle" && G.types[cells5[c]] != "Endpoint")
				{
					ct[cells5[c]].emplace_back(max(0, t - k_robust), t + 1 + k_robust);
				}
			}

			if (k_robust == 0 && i > 0 && (path[i-1].location != path[i].location || path[i-1].orientation != path[i].orientation))
			{
				int prev_cells[5];
				G.get_5cell_occupied_cells(path[i-1].location, path[i-1].orientation, prev_cells);
				int curr_cells[5];
				G.get_5cell_occupied_cells(path[i].location, path[i].orientation, curr_cells);
				for (int c = 0; c < 5; c++)
				{
					for (int p = 0; p < 5; p++)
					{
						if (curr_cells[c] >= 0 && curr_cells[c] < (int)G.types.size() && prev_cells[p] >= 0 && prev_cells[p] < (int)G.types.size() &&
                            curr_cells[c] != prev_cells[p] && G.types[curr_cells[c]] != "Magic" && G.types[prev_cells[p]] != "Magic")
						{
							ct[getEdgeIndex(curr_cells[c], prev_cells[p])].emplace_back(t, t + 1);
							ct[getEdgeIndex(prev_cells[p], curr_cells[c])].emplace_back(t, t + 1);
						}
					}
				}
			}
		}
	}
	if (path.back().location >= 0 && path.back().location < (int)G.types.size() && G.types[path.back().location] != "Magic")
	{
		int cells5[5];
		G.get_5cell_occupied_cells(path.back().location, path.back().orientation, cells5);
		int end_t = max((int)path.back().timestep + task_delay + 2, window + 1);
		for (int c = 0; c < 5; c++)
		{
			if (cells5[c] >= 0 && cells5[c] < (int)G.types.size() && G.types[cells5[c]] != "Magic" && G.types[cells5[c]] != "Obstacle" && G.types[cells5[c]] != "Endpoint")
				ct[cells5[c]].emplace_back(path.back().timestep, end_t);
		}
	}
}

void ReservationTable::addInitialConstraints(const list< tuple<int, int, int> >& initial_constraints, int current_agent)
{
	for (auto con : initial_constraints)
	{
		if (std::get<0>(con) != current_agent && 0 <= std::get<1>(con) && std::get<1>(con) < G.types.size() &&
			G.types[std::get<1>(con)] != "Magic")
			ct[std::get<1>(con)].emplace_back(0, min(window, std::get<2>(con)));
	}
}


//  insert the path to the conflict avoidance table
void ReservationTable::insertPath2CAT(const Path& path)
{
	if (path.empty())
		return;
	int max_timestep = min((int)path.size() - 1, k_robust + window);
	int timestep = 0;
	while (timestep <= max_timestep)
	{
		int cells5[5];
		G.get_5cell_occupied_cells(path[timestep].location, path[timestep].orientation, cells5);
		for (int c = 0; c < 5; c++)
		{
			if (cells5[c] >= 0 && cells5[c] < (int)G.types.size() && G.types[cells5[c]] != "Magic" && G.types[cells5[c]] != "Obstacle" && G.types[cells5[c]] != "Endpoint")
			{
				for (int t = max(0, timestep - k_robust); t <= min((int)cat.size() - 1, timestep + k_robust); t++)
				{
					if (cells5[c] < (int)cat[t].size())
						cat[t][cells5[c]] = true;
				}
			}
		}
		timestep++;
	}
	if (path.back().location >= 0 && path.back().location < (int)G.types.size() && G.types[path.back().location] != "Magic")
	{
		int cells5[5];
		G.get_5cell_occupied_cells(path.back().location, path.back().orientation, cells5);
		while (timestep < (int)cat.size()) // assume that the agent waits at its last location
		{
			for (int c = 0; c < 5; c++)
			{
				if (cells5[c] >= 0 && cells5[c] < (int)cat[timestep].size() && G.types[cells5[c]] != "Obstacle" && G.types[cells5[c]] != "Endpoint")
					cat[timestep][cells5[c]] = true;
			}
			timestep++;
		}
	}
}

// For PBS
void ReservationTable::build(const vector<Path*>& paths,
        const list< tuple<int, int, int> >& initial_constraints,
        const unordered_set<int>& high_priority_agents, int current_agent, int start_location)
{
    clock_t t = std::clock();

    // add hard constraints
    vector<bool> soft(num_of_agents, true);
    for (auto i : high_priority_agents)
    {
        if (paths[i] == nullptr)
            continue;
		insertPath2CT(*paths[i]);
		soft[i] = false;
    }

    if (prioritize_start) // prioritize waits at start locations
    {
        insertConstraints4starts(paths, current_agent, start_location);
    }

	addInitialConstraints(initial_constraints, current_agent); // add initial constraints
   
    runtime = (std::clock() - t) * 1.0  / CLOCKS_PER_SEC;
    if (!use_cat)
        return;

    // add soft constraints
    soft[current_agent] = false;
    for (int i = 0; i < num_of_agents; i++)
    {
        if(!soft[i] || paths[i] == nullptr)
            continue;
		insertPath2CAT(*paths[i]);
    }

    runtime = (std::clock() - t) * 1.0  / CLOCKS_PER_SEC;
}

// For WHCA*
void ReservationTable::build(const vector<Path>& paths,
                            const list< tuple<int, int, int> >& initial_constraints,
                            int current_agent)
{
    clock_t t = std::clock();
    // add hard constraints
    for (int i = 0; i < (int)paths.size(); i++)
    {
		if (i == current_agent)
			continue;
		insertPath2CT(paths[i]);
    }

	addInitialConstraints(initial_constraints, current_agent); // add initial constraints
    runtime = (std::clock() - t) * 1.0  / CLOCKS_PER_SEC;
}

// For ECBS
void ReservationTable::build(const vector<Path*>& paths,
                            const list< tuple<int, int, int> >& initial_constraints,
                            const list< Constraint >& hard_constraints, int current_agent)
{
    clock_t t = std::clock();
    // add hard constraints
    for (auto con : hard_constraints)
    {
        if (std::get<0>(con) == current_agent && std::get<4>(con)) // positive constraint
        {
           // insert_positive_constraint(std::get<1>(con), std::get<3>(con));
		   // TODO: insert positive constraints
        }
		else if (std::get<2>(con) < 0 && G.types[std::get<1>(con)] != "Magic") // vertex constraint
        {
			ct[std::get<1>(con)].emplace_back(std::get<3>(con), std::get<3>(con) + 1);
        }
		else // edge constraint
		{
			ct[getEdgeIndex(std::get<1>(con), std::get<2>(con))].emplace_back(std::get<3>(con), std::get<3>(con) + 1);
		}
    }

	addInitialConstraints(initial_constraints, current_agent); // add initial constraints

    /* add soft constraints */
	// compute the max timestep that cat needs
	size_t cat_size = 0;
    for (int i = 0; i < num_of_agents; i++)
    {
        if(i == current_agent || paths[i] == nullptr)
            continue;

		if ((int)paths[i]->size() > window)
		{
			cat_size = window;
			break;
		}
		else if (cat_size < paths[i]->size())
			cat_size = paths[i]->size();
	}
	cat.resize(cat_size, vector<bool>(map_size));

	// build cat
	for (int i = 0; i < num_of_agents; i++)
	{
		if (i == current_agent || paths[i] == nullptr)
			continue;
		
       insertPath2CAT(*paths[i]);
    }
    runtime = (std::clock() - t) * 1.0  / CLOCKS_PER_SEC;
}


void ReservationTable::insertConstraints4starts(const vector<Path*>& paths, int current_agent, int start_location)
{
    for (int i = 0; i < num_of_agents; i++)
    {
        if (paths[i] == nullptr)
            continue;
        else if (i != current_agent)// prohibit the agent from conflicting with other agents at their start locations
        {
            int start = paths[i]->front().location;
            if (start < 0 || G.types[start] == "Magic")
                continue;
            for (auto state : (*paths[i]))
            {
                if (state.location != start) // The agent starts to move
                {
                    int cells[3];
                    G.get_occupied_cells(paths[i]->front().location, paths[i]->front().orientation, cells);
                    for (int c = 0; c < 3; c++)
                    {
                        if (G.types[cells[c]] != "Magic")
                        {
                            ct[cells[c]].emplace_back(0, state.timestep + k_robust);
                        }
                    }
                    break;
                }
            }
        }
    }
}

// [lower_bound, upper_bound)
list<Interval> ReservationTable::getSafeIntervals(int location, int lower_bound, int upper_bound)
{
    list<Interval> safe_intervals;
    if (lower_bound >= upper_bound)
        return safe_intervals;

	updateSIT(location);
	
	auto it = sit.find(location);
    if (it == sit.end()) 
    {
		safe_intervals.emplace_back(0, INTERVAL_MAX, 0);
		return safe_intervals;
    }

    for(auto interval : it->second)
    {
        if (lower_bound >= std::get<1>(interval))
            continue;
        else if (upper_bound <= std::get<0>(interval))
            break;
        else
        {
            safe_intervals.emplace_back(interval);
        }

    }
    return safe_intervals;
}

static list<Interval> intersect_two_intervals(const list<Interval>& safe1, const list<Interval>& safe2)
{
	list<Interval> safe_intervals;
	auto it1 = safe1.begin();
	auto it2 = safe2.begin();
	while (it1 != safe1.end() && it2 != safe2.end())
	{
		int t_min = max(std::get<0>(*it1), std::get<0>(*it2));
		int t_max = min(std::get<1>(*it1), std::get<1>(*it2));
		if (t_min < t_max)
			safe_intervals.emplace_back(t_min, t_max, std::get<2>(*it1) + std::get<2>(*it2));
		if (t_max == std::get<1>(*it1))
			++it1;
		if (t_max == std::get<1>(*it2))
			++it2;
	}
	return safe_intervals;
}

// [lower_bound, upper_bound)
list<Interval> ReservationTable::getSafeIntervals(int from, int to, int orientation, int lower_bound, int upper_bound)
{
	if (lower_bound >= upper_bound)
		return list<Interval>();
	
	int ori = (orientation >= 0 && orientation < 4) ? orientation : G.get_direction(from, to);
	list<Interval> safe_vertex_intervals;
	if (ori >= 0 && ori < 4)
	{
		int cells5[5];
		G.get_5cell_occupied_cells(to, ori, cells5);
		if (cells5[0] >= 0 && cells5[0] < (int)G.types.size())
			safe_vertex_intervals = getSafeIntervals(cells5[0], lower_bound, upper_bound);
		for (int c = 1; c < 5; c++)
		{
			if (cells5[c] >= 0 && cells5[c] < (int)G.types.size() && G.types[cells5[c]] != "Magic" && G.types[cells5[c]] != "Obstacle" && G.types[cells5[c]] != "Endpoint")
			{
				safe_vertex_intervals = intersect_two_intervals(safe_vertex_intervals, getSafeIntervals(cells5[c], lower_bound, upper_bound));
			}
		}
	}
	else
	{
		if (to >= 0 && to < (int)G.types.size())
			safe_vertex_intervals = getSafeIntervals(to, lower_bound, upper_bound);
	}

	if (from >= 0 && from < (int)map_size && to >= 0 && to < (int)map_size)
	{
		auto safe_edge_intervals1 = getSafeIntervals(getEdgeIndex(from, to), lower_bound, upper_bound);
		auto safe_edge_intervals2 = getSafeIntervals(getEdgeIndex(to, from), lower_bound, upper_bound);
		auto safe_edge_intervals = intersect_two_intervals(safe_edge_intervals1, safe_edge_intervals2);
		return intersect_two_intervals(safe_vertex_intervals, safe_edge_intervals);
	}

	return safe_vertex_intervals;
}

Interval ReservationTable::getFirstSafeInterval(int location)
{
	updateSIT(location);
    auto it = sit.find(location);
    if (it == sit.end())
    {
		return Interval(0, INTERVAL_MAX, 0);
    }
    return it->second.front();
}

// find a safe interval with t_min as given
bool ReservationTable::findSafeInterval(Interval& interval, int location, int t_min)
{
	updateSIT(location);

    auto it = sit.find(location);
    if (it == sit.end())
    {
		interval = make_tuple(0, INTERVAL_MAX, 0);
		return true;
    }
    for( auto i : it->second)
    {
        if (t_min >= std::get<0>(i) && t_min < std::get<1>(i))
        {
            interval = i;
            return true;
        }
    }
    return false;
}


void ReservationTable::print() const
{
    for (const auto& entry : sit)
    {
        cout << "loc=" << entry.first << ":";
        for (const auto& interval : entry.second)
        {
            cout << "[" << std::get<0>(interval) << "," << std::get<1>(interval) << "],";
        }
    }
    cout << endl;
}

void ReservationTable::printCT(size_t location) const
{
    cout << "loc=" << location << ":";
    const auto it = ct.find(location);
    if (it != ct.end())
    {
        for (const auto & interval : ct.at(location))
        cout << "[" << std::get<0>(interval) << "," << std::get<1>(interval) << "],";
    }
    cout << endl;
}


bool ReservationTable::isConstrained(const State& curr_s, const State& next_s) const
{
	int next_cells5[5];
	G.get_5cell_occupied_cells(next_s.location, next_s.orientation, next_cells5);
	for (int c = 0; c < 5; c++)
	{
		if (next_cells5[c] < 0 || next_cells5[c] >= (int)map_size)
		{
			if (c < 3) return true; // Physical 3-cell body out of bounds is constrained
			continue;
		}
		if (G.types[next_cells5[c]] == "Obstacle" || G.types[next_cells5[c]] == "Endpoint" || G.types[next_cells5[c]] == "Magic")
			continue;

		auto it = ct.find(next_cells5[c]);
		if (it != ct.end())
		{
			for (auto time_range : it->second)
			{
				if (next_s.timestep >= time_range.first && next_s.timestep < time_range.second)
					return true;
			}
		}
	}

	if (curr_s.location != next_s.location || (curr_s.orientation >= 0 && curr_s.orientation != next_s.orientation))
	{
		int curr_cells[3];
		G.get_occupied_cells(curr_s.location, curr_s.orientation, curr_cells);
		for (int c = 0; c < 3; c++)
		{
			if (curr_cells[c] >= 0 && curr_cells[c] < (int)map_size && next_cells5[c] >= 0 && next_cells5[c] < (int)map_size && curr_cells[c] != next_cells5[c])
			{
				auto it = ct.find(getEdgeIndex(curr_cells[c], next_cells5[c]));
				if (it != ct.end())
				{
					for (auto time_range : it->second)
					{
						if (next_s.timestep >= time_range.first && next_s.timestep < time_range.second)
							return true;
					}
				}
			}
		}
	}
	return false;
}

bool ReservationTable::isConstrained(int curr_id, int next_id, int next_timestep) const
{
	return isConstrained(State(curr_id, next_timestep - 1, -1), State(next_id, next_timestep, -1));
}

bool ReservationTable::isConflicting(const State& curr_s, const State& next_s) const
{
	if (next_s.timestep >= (int)cat.size())
		return false;

	int next_cells5[5];
	G.get_5cell_occupied_cells(next_s.location, next_s.orientation, next_cells5);
	for (int c = 0; c < 5; c++)
	{
		if (next_cells5[c] >= 0 && next_cells5[c] < (int)cat[next_s.timestep].size() && cat[next_s.timestep][next_cells5[c]])
			return true;
	}

	if ((curr_s.location != next_s.location || (curr_s.orientation >= 0 && curr_s.orientation != next_s.orientation)) && next_s.timestep > 0)
	{
		int curr_cells5[5];
		G.get_5cell_occupied_cells(curr_s.location, curr_s.orientation, curr_cells5);
		for (int c = 0; c < 5; c++)
		{
			if (curr_cells5[c] >= 0 && curr_cells5[c] < (int)cat[next_s.timestep].size() && next_cells5[c] >= 0 && next_cells5[c] < (int)cat[next_s.timestep - 1].size() &&
                cat[next_s.timestep][curr_cells5[c]] && cat[next_s.timestep - 1][next_cells5[c]])
				return true;
		}
	}
	return false;
}

bool ReservationTable::isConflicting(int curr_id, int next_id, int next_timestep) const
{
	return isConflicting(State(curr_id, next_timestep - 1, -1), State(next_id, next_timestep, -1));
}