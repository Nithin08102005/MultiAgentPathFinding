#include "KivaGraph.h"
#include <fstream>
#include <boost/tokenizer.hpp>
#include "StateTimeAStar.h"
#include <sstream>
#include <random>
#include <chrono>

bool KivaGrid::load_map(std::string fname)
{
    std::size_t pos = fname.rfind('.');      // position of the file extension
    auto ext_name = fname.substr(pos, fname.size());     // get the name without extension
    if (ext_name == ".grid")
        return load_weighted_map(fname);
    else if (ext_name == ".map")
        return load_unweighted_map(fname);
		
    else
    {
        std::cout << "Map file name should end with either .grid or .map. " << std::endl;
        return false;
    }
}

bool KivaGrid::load_weighted_map(std::string fname)
{
	std::string line;
	std::ifstream myfile((fname).c_str());
	if (!myfile.is_open())
	{
		std::cout << "Map file " << fname << " does not exist. " << std::endl;
		return false;
	}

	std::cout << "*** Loading map ***" << std::endl;
	clock_t t = std::clock();
	std::size_t pos = fname.rfind('.');      // position of the file extension
	map_name = fname.substr(0, pos);     // get the name without extension
	getline(myfile, line); // skip the words "grid size"
	getline(myfile, line);
	boost::char_separator<char> sep(",");
	boost::tokenizer< boost::char_separator<char> > tok(line, sep);
	boost::tokenizer< boost::char_separator<char> >::iterator beg = tok.begin();
	this->rows = atoi((*beg).c_str()); // read number of cols
	beg++;
	this->cols = atoi((*beg).c_str()); // read number of rows
	move[0] = 1;
	move[1] = -cols;
	move[2] = -1;
	move[3] = cols;

	getline(myfile, line); // skip the headers

	//read tyeps and edge weights
	this->types.resize(rows * cols);
	this->weights.resize(rows * cols);
	for (int i = 0; i < rows * cols; i++)
	{
		getline(myfile, line);
		boost::tokenizer< boost::char_separator<char> > tok(line, sep);
		beg = tok.begin();
		beg++; // skip id
		this->types[i] = std::string(beg->c_str()); // read type
		beg++;
		if (types[i] == "Home")
			this->agent_home_locations.push_back(i);
		else if (types[i] == "Endpoint")
			this->endpoints.push_back(i);
		beg++; // skip x
		beg++; // skip y
		weights[i].resize(5);
		for (int j = 0; j < 5; j++) // read edge weights
		{
			if (std::string(beg->c_str()) == "inf")
				weights[i][j] = WEIGHT_MAX;
			else
				weights[i][j] = std::stod(beg->c_str());
			beg++;
		}
	}

	myfile.close();
	double runtime = (std::clock() - t) / CLOCKS_PER_SEC;
	std::cout << "Map size: " << rows << "x" << cols << " with ";
	cout << endpoints.size() << " endpoints and " <<
		agent_home_locations.size() << " home stations." << std::endl;
	std::cout << "Done! (" << runtime << " s)" << std::endl;
	return true;
}


// load map
bool KivaGrid::load_unweighted_map(std::string fname)
{
    std::string line;
    std::ifstream myfile ((fname).c_str());
	if (!myfile.is_open())
    {
	    std::cout << "Map file " << fname << " does not exist. " << std::endl;
        return false;
    }
	
    std::cout << "*** Loading map ***" << std::endl;
    clock_t t = std::clock();
	std::size_t pos = fname.rfind('.');      // position of the file extension
    map_name = fname.substr(0, pos);     // get the name without extension
    getline (myfile, line); 
	
	
	boost::char_separator<char> sep(",");
	boost::tokenizer< boost::char_separator<char> > tok(line, sep);
	boost::tokenizer< boost::char_separator<char> >::iterator beg = tok.begin();
	rows = atoi((*beg).c_str()); // read number of rows
	beg++;
	cols = atoi((*beg).c_str()); // read number of cols
	move[0] = 1;
	move[1] = -cols;
	move[2] = -1;
	move[3] = cols;

	std::stringstream ss;
	getline(myfile, line);
	ss << line;
	int num_endpoints;
	ss >> num_endpoints;

	int agent_num;
	ss.clear();
	getline(myfile, line);
	ss << line;
	ss >> agent_num;

	ss.clear();
	getline(myfile, line);
	ss << line;
	int maxtime;
	ss >> maxtime;

	//this->agents.resize(agent_num);
	//endpoints.resize(num_endpoints + agent_num);
	types.resize(rows * cols);
	weights.resize(rows*cols);
	//DeliverGoal.resize(row*col, false);
	// read map
	//int ep = 0, ag = 0;
	for (int i = 0; i < rows; i++)
	{
		getline(myfile, line);
		for (int j = 0; j < cols; j++)
		{
			int id = cols * i + j;
			weights[id].resize(5, WEIGHT_MAX);
			if (line[j] == '@') // obstacle
			{
				types[id] = "Obstacle";
			}
			else if (line[j] == 'e') //endpoint
			{
				types[id] = "Endpoint";
				weights[id][4] = 1;
				endpoints.push_back(id);
			}
			else if (line[j] == 'r') //robot rest
			{
				types[id] = "Home";
				weights[id][4] = 1;
			}
			else
			{
				types[id] = "Travel";
				weights[id][4] = 1;
			}
		}
	}

	// Automatically detect robot home bay centers (3-cell rigid bays) for any map layout
	std::vector<bool> in_bay(rows * cols, false);

	// 1. Detect horizontal 3-cell bays: 'r r r'
	for (int i = 0; i < rows; i++)
	{
		for (int j = 1; j < cols - 1; j++)
		{
			int left = i * cols + (j - 1);
			int center = i * cols + j;
			int right = i * cols + (j + 1);
			if (types[left] == "Home" && types[center] == "Home" && types[right] == "Home" &&
			    !in_bay[left] && !in_bay[center] && !in_bay[right])
			{
				agent_home_locations.push_back(center);
				in_bay[left] = in_bay[center] = in_bay[right] = true;
			}
		}
	}

	// 2. Detect vertical 3-cell bays: 'r' above, 'r' center, 'r' below
	for (int j = 0; j < cols; j++)
	{
		for (int i = 1; i < rows - 1; i++)
		{
			int top = (i - 1) * cols + j;
			int center = i * cols + j;
			int bottom = (i + 1) * cols + j;
			if (types[top] == "Home" && types[center] == "Home" && types[bottom] == "Home" &&
			    !in_bay[top] && !in_bay[center] && !in_bay[bottom])
			{
				agent_home_locations.push_back(center);
				in_bay[top] = in_bay[center] = in_bay[bottom] = true;
			}
		}
	}

	// 3. Fallback for standard 1-cell MAPF benchmark maps (where each 'r' is a 1-cell station):
	if (agent_home_locations.empty())
	{
		for (int id = 0; id < rows * cols; id++)
		{
			if (types[id] == "Home")
			{
				agent_home_locations.push_back(id);
			}
		}
	}

	shuffle(agent_home_locations.begin(), agent_home_locations.end(), std::default_random_engine());
	for (int i = 0; i < cols * rows; i++)
	{
		if (types[i] == "Obstacle" || types[i] == "Endpoint")
		{
			continue;
		}
		for (int dir = 0; dir < 4; dir++)
		{
			int next_loc = i + move[dir];
			if (0 <= next_loc && next_loc < cols * rows && get_Manhattan_distance(i, next_loc) <= 1 &&
				types[next_loc] != "Obstacle" && types[next_loc] != "Endpoint")
			{
				if (types[i] != "Home" && types[next_loc] == "Home")
				{
					// ONE-WAY EXIT: Disallow entering Home from Travel lanes during tasks!
					weights[i][dir] = WEIGHT_MAX;
				}
				else
				{
					weights[i][dir] = 1;
				}
			}
			else
			{
				weights[i][dir] = WEIGHT_MAX;
			}
		}
	}
	

	myfile.close();
    double runtime = (std::clock() - t) / CLOCKS_PER_SEC;
    std::cout << "Map size: " << rows << "x" << cols << " with ";
	cout << endpoints.size() << " endpoints and " <<
	agent_home_locations.size() << " home stations." << std::endl;		
    std::cout << "Done! (" << runtime << " s)" << std::endl;
    return true;
}

void KivaGrid::preprocessing(bool consider_rotation)
{
	std::cout << "*** PreProcessing map ***" << std::endl;
	clock_t t = std::clock();
	this->consider_rotation = consider_rotation;
	std::string fname;
	if (consider_rotation)
		fname = map_name + "_rotation_heuristics_table.txt";
	else
		fname = map_name + "_heuristics_table.txt";
	std::ifstream myfile(fname.c_str());
	bool succ = false;
	if (myfile.is_open())
	{
		succ = load_heuristics_table(myfile);
		myfile.close();
	}
	bool missing = false;
	for (auto endpoint : endpoints)
	{
		if (heuristics.find(endpoint) == heuristics.end())
		{
			auto h_tbl = compute_heuristics(endpoint);
			heuristics[endpoint] = h_tbl;
			for (int dir = 0; dir < 4; dir++)
			{
				int nb = endpoint + move[dir];
				if (nb >= 0 && nb < rows * cols && get_Manhattan_distance(endpoint, nb) == 1)
				{
					if (is_cell_valid_for_robot(nb) && is_robot_maneuverable(nb))
					{
						heuristics[nb] = h_tbl;
						break;
					}
				}
			}
			missing = true;
		}
	}
	for (auto home : agent_home_locations)
	{
		if (heuristics.find(home) == heuristics.end())
		{
			heuristics[home] = compute_heuristics(home);
			missing = true;
		}
	}
	if (!succ || missing)
	{
		save_heuristics_table(fname);
	}

	double runtime = (std::clock() - t) / CLOCKS_PER_SEC;
	std::cout << "Done! (" << runtime << " s)" << std::endl;
}
