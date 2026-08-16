import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from matplotlib.patches import Rectangle, Circle
from matplotlib.collections import LineCollection
import matplotlib.colors as mcolors
import os
import math

# Resolve data files relative to this script so `python mapf_visualizer.py` works from any cwd.
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _resolve_data_path(path):
    if not path or os.path.isabs(path):
        return path
    return os.path.normpath(os.path.join(_SCRIPT_DIR, path))


class GeneralizedKivaVisualizer:
    def __init__(self, map_file='kiva_4zone_shaved.map', results_file='exp/test_4zone/paths.txt'):
        map_file = _resolve_data_path(map_file)
        results_file = _resolve_data_path(results_file)
        print("Loading Generalized Kiva Warehouse MAPF data...")
        print(f"  map: {map_file}")
        print(f"  paths: {results_file}")
        
        # Load data
        self.map_data = self.load_kiva_map(map_file)
        self.grid_height,self.grid_width = self.map_data.shape
        self.raw_data = self.load_raw_data(results_file)
        self.solution = self.convert_to_solution()
        tasks_file = results_file.replace('paths.txt', 'tasks.txt')
        self.tasks = self.load_tasks(tasks_file)
        
        # **ADAPTIVE SETUP: Configure based on robot count**
        self.num_agents = len(self.solution['agents'])
        self.setup_adaptive_parameters()
        
        # Setup endpoint registry with Zone and Local IDs
        self.build_endpoint_registry()
        
        # Pre-cache warehouse statistics
        self.warehouse_stats = {
            'shelves': np.sum(self.map_data == '@'),
            'endpoints': np.sum(self.map_data == 'e'),
            'robot_zones': np.sum(self.map_data == 'r'),
            'free_space': np.sum(self.map_data == '.')
        }
        
        # Setup visualization
        self.setup_adaptive_layout()
        self.current_timestep = 0
        self.substeps = 1
        self.max_timestep = max(len(path) for path in self.solution['agents'].values()) if self.solution['agents'] else 1
        
        # Pre-render static elements
        self.setup_static_warehouse()
        self.agent_artists = []
        self.trail_artists = []
        
        print(f"SUCCESS: Generalized visualizer ready for {self.num_agents} robots")
        print(f"Mode: {self.viz_mode} | Grid: {self.grid_width}x{self.grid_height} | Endpoints: {len(self.endpoint_info_by_loc)} mapped across 4 zones")

    def setup_adaptive_parameters(self):
        """Configure visualization parameters based on robot count"""
        
        if self.num_agents <= 10:
            self.viz_mode = "DETAILED"
            self.robot_size = 0.4
            self.font_size = 10
            self.trail_length = 12
            self.trail_alpha = 0.7
            self.show_individual_status = True
            self.show_robot_ids = True
            self.grid_detail = "high"
            
        elif self.num_agents <= 30:
            self.viz_mode = "MEDIUM"
            self.robot_size = 0.3
            self.font_size = 8
            self.trail_length = 8
            self.trail_alpha = 0.5
            self.show_individual_status = True
            self.show_robot_ids = True
            self.grid_detail = "medium"
            
        elif self.num_agents <= 100:
            self.viz_mode = "COMPACT"
            self.robot_size = 0.25
            self.font_size = 6
            self.trail_length = 5
            self.trail_alpha = 0.4
            self.show_individual_status = False
            self.show_robot_ids = True
            self.grid_detail = "low"
            
        elif self.num_agents <= 500:
            self.viz_mode = "DENSE"
            self.robot_size = 0.15
            self.font_size = 4
            self.trail_length = 3
            self.trail_alpha = 0.3
            self.show_individual_status = False
            self.show_robot_ids = False
            self.grid_detail = "minimal"
            
        else:  # 500+ robots
            self.viz_mode = "HEATMAP"
            self.robot_size = 0.1
            self.font_size = 0
            self.trail_length = 2
            self.trail_alpha = 0.2
            self.show_individual_status = False
            self.show_robot_ids = False
            self.grid_detail = "none"
        
        # **ADAPTIVE COLOR SCHEME**
        self.setup_adaptive_colors()
        
        # **ADAPTIVE ANIMATION SPEED**
        if self.num_agents <= 10:
            self.animation_interval = 1
        elif self.num_agents <= 50:
            self.animation_interval = 75
        elif self.num_agents <= 200:
            self.animation_interval = 100
        else:
            self.animation_interval = 150

    def setup_adaptive_colors(self):
        """Generate colors that work for any number of robots"""
        if self.num_agents <= 12:
            # Use distinct colors for small groups
            self.colors = plt.cm.Set3(np.linspace(0, 1, max(self.num_agents, 1)))
        elif self.num_agents <= 50:
            # Combine multiple colormaps
            colors = []
            maps = ['Set3', 'Dark2', 'Paired', 'Accent']
            per_map = math.ceil(self.num_agents / len(maps))
            
            for i, cmap_name in enumerate(maps):
                start_idx = i * per_map
                end_idx = min((i + 1) * per_map, self.num_agents)
                if start_idx < self.num_agents:
                    cmap = plt.cm.get_cmap(cmap_name)
                    colors.extend([cmap(j / per_map) for j in range(end_idx - start_idx)])
            
            self.colors = np.array(colors[:self.num_agents])
        else:
            # Use continuous color space for large numbers
            self.colors = plt.cm.rainbow(np.linspace(0, 1, self.num_agents))

    def build_endpoint_registry(self):
        """Map every endpoint in the map to a Zone (Z0-Z3) and local ID (1..128)"""
        self.endpoint_info_by_loc = {}
        self.service_to_endpoint = {}
        
        mid_x = (self.grid_width - 1) / 2.0
        mid_y = (self.grid_height - 1) / 2.0
        
        zone_endpoints = {0: [], 1: [], 2: [], 3: []}
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.map_data[y, x] == 'e':
                    loc = y * self.grid_width + x
                    if x < mid_x:
                        zid = 0 if y < mid_y else 2
                    else:
                        zid = 1 if y < mid_y else 3
                    zone_endpoints[zid].append((y, x, loc))
        
        for zid in range(4):
            zone_endpoints[zid].sort(key=lambda item: (item[0], item[1]))
            for idx, (ey, ex, eloc) in enumerate(zone_endpoints[zid], start=1):
                info = {
                    'zone': zid,
                    'id': idx,
                    'x': ex,
                    'y': ey,
                    'loc': eloc,
                    'label': f"Z{zid}:{idx}"
                }
                self.endpoint_info_by_loc[eloc] = info
                
                # Map adjacent travel dots (exterior service cells) to this endpoint
                for dy in [-1, 1]:
                    sy = ey + dy
                    if 0 <= sy < self.grid_height:
                        sloc = sy * self.grid_width + ex
                        if sloc not in self.service_to_endpoint:
                            self.service_to_endpoint[sloc] = info

    def get_current_target_info(self, agent_id, t):
        """Get the current target endpoint info (Zone and local ID) for an agent at time t"""
        if agent_id not in self.tasks or not self.tasks[agent_id]:
            return None
        
        # tasks[agent_id] is a list of (loc, finish_time)
        # Find the active task where finish_time > t
        for loc, finish_time in self.tasks[agent_id][1:]:
            if finish_time > t or finish_time < 0:
                if loc in self.endpoint_info_by_loc:
                    return self.endpoint_info_by_loc[loc]
                elif loc in self.service_to_endpoint:
                    return self.service_to_endpoint[loc]
                else:
                    tx, ty = self.location_to_xy(loc)
                    return {'label': f"({tx},{ty})", 'x': tx, 'y': ty, 'zone': agent_id % 4, 'id': 0}
        
        # If all tasks are completed, show the last target
        last_loc = self.tasks[agent_id][-1][0]
        if last_loc in self.endpoint_info_by_loc:
            return self.endpoint_info_by_loc[last_loc]
        elif last_loc in self.service_to_endpoint:
            return self.service_to_endpoint[last_loc]
        tx, ty = self.location_to_xy(last_loc)
        return {'label': f"({tx},{ty})", 'x': tx, 'y': ty, 'zone': agent_id % 4, 'id': 0}

    def setup_adaptive_layout(self):
        """Setup figure layout based on visualization mode with Dark Theme"""
        plt.style.use('dark_background')
        if self.viz_mode in ["DETAILED", "MEDIUM"]:
            self.fig, (self.ax_main, self.ax_info) = plt.subplots(1, 2, figsize=(22, 12), gridspec_kw={'width_ratios': [3.5, 1]})
            self.use_info_panel = True
        elif self.viz_mode in ["COMPACT", "DENSE"]:
            self.fig, self.ax_main = plt.subplots(1, 1, figsize=(16, 12))
            self.use_info_panel = False
        else:
            self.fig, self.ax_main = plt.subplots(1, 1, figsize=(18, 14))
            self.use_info_panel = False
            
        self.fig.patch.set_facecolor('#101016')
        self.ax_main.set_facecolor('#161620')
        if self.use_info_panel:
            self.ax_info.set_facecolor('#101016')

    def render_zones(self):
        """Overlay 4 quadrant zones with vibrant dark-mode shading and watermark labels"""
        mid_x = (self.grid_width - 1) / 2.0
        mid_y = (self.grid_height - 1) / 2.0
        
        zones = [
            (0, -0.5, mid_x, -0.5, mid_y, '#00b0ff', 'ZONE 0 (Top-Left)', mid_x / 2.0, mid_y / 2.0),
            (1, mid_x, self.grid_width - 0.5, -0.5, mid_y, '#00e676', 'ZONE 1 (Top-Right)', (mid_x + self.grid_width) / 2.0, mid_y / 2.0),
            (2, -0.5, mid_x, mid_y, self.grid_height - 0.5, '#ff9100', 'ZONE 2 (Bottom-Left)', mid_x / 2.0, (mid_y + self.grid_height) / 2.0),
            (3, mid_x, self.grid_width - 0.5, mid_y, self.grid_height - 0.5, '#e040fb', 'ZONE 3 (Bottom-Right)', (mid_x + self.grid_width) / 2.0, (mid_y + self.grid_height) / 2.0),
        ]
        
        for zid, x0, x1, y0, y1, color_hex, title, lx, ly in zones:
            rect = Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor=color_hex, alpha=0.14, edgecolor=color_hex, linestyle='--', linewidth=1.5, zorder=1)
            self.ax_main.add_patch(rect)
            
            self.ax_main.text(lx, ly, title, ha='center', va='center', fontsize=13, fontweight='bold',
                              color=color_hex, alpha=0.9, zorder=2,
                              bbox=dict(boxstyle="round,pad=0.4", facecolor="#101016", edgecolor=color_hex, alpha=0.85, linewidth=1.5))
            
        self.ax_main.axvline(mid_x, color='#78909c', linestyle='--', linewidth=2.0, alpha=0.7, zorder=3)
        self.ax_main.axhline(mid_y, color='#78909c', linestyle='--', linewidth=2.0, alpha=0.7, zorder=3)

    def setup_static_warehouse(self):
        """Pre-render static warehouse elements"""
        self.ax_main.set_xlim(-0.5, self.grid_width - 0.5)
        self.ax_main.set_ylim(self.grid_height - 0.5, -0.5)
        self.ax_main.set_aspect('equal')
        
        # Render Zone Layout Background & Overlay
        self.render_zones()
        
        # **ADAPTIVE WAREHOUSE RENDERING**
        if self.grid_detail == "high":
            # Full detail for small robot counts
            self.render_detailed_warehouse()
        elif self.grid_detail == "medium":
            # Simplified rendering
            self.render_medium_warehouse()
        elif self.grid_detail == "low":
            # Basic shapes only
            self.render_basic_warehouse()
        elif self.grid_detail == "minimal":
            # Just obstacles
            self.render_minimal_warehouse()
        else:  # "none"
            # Background color coding only
            self.render_background_only()
        
        # **ADAPTIVE GRID LINES**
        if self.grid_detail in ["high", "medium"]:
            spacing = 5 if self.grid_detail == "high" else 10
            for x in range(0, self.grid_width, spacing):
                self.ax_main.axvline(x - 0.5, color='lightgray', linewidth=0.2, alpha=0.5)
            for y in range(0, self.grid_height, spacing):
                self.ax_main.axhline(y - 0.5, color='lightgray', linewidth=0.2, alpha=0.5)

    def render_detailed_warehouse(self):
        """Full warehouse detail with Zone-coded endpoint IDs (Dark Theme)"""
        zone_colors = {
            0: ('#0a2a4a', '#00b0ff'),
            1: ('#0a3820', '#00e676'),
            2: ('#422000', '#ff9100'),
            3: ('#38004a', '#e040fb')
        }
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                cell = self.map_data[y, x]
                loc = y * self.grid_width + x
                
                if cell == '@':
                    rect = Rectangle((x-0.5, y-0.5), 1, 1, facecolor='#2a2b38', edgecolor='#3d3f54', alpha=0.9, zorder=2)
                    self.ax_main.add_patch(rect)
                elif cell == 'e':
                    info = self.endpoint_info_by_loc.get(loc, None)
                    if info:
                        zid = info['zone']
                        num_str = str(info['id'])
                        bg_col, edge_col = zone_colors.get(zid, ('#2a2b38', '#ffd600'))
                        rect = Rectangle((x-0.5, y-0.5), 1, 1, facecolor=bg_col, edgecolor=edge_col, alpha=0.92, linewidth=0.8, zorder=2)
                        self.ax_main.add_patch(rect)
                        self.ax_main.text(x, y, num_str, ha='center', va='center', fontweight='bold', fontsize=5.0, color='#ffffff', zorder=10)
                    else:
                        rect = Rectangle((x-0.5, y-0.5), 1, 1, facecolor='#ffab00', edgecolor='#ffd600', alpha=0.85, zorder=2)
                        self.ax_main.add_patch(rect)
                        self.ax_main.text(x, y, 'E', ha='center', va='center', fontweight='bold', fontsize=6, color='#101016', zorder=10)
                elif cell == 'r':
                    rect = Rectangle((x-0.5, y-0.5), 1, 1, facecolor='#00b0ff', edgecolor='#80d8ff', alpha=0.4, zorder=2)
                    self.ax_main.add_patch(rect)
                    self.ax_main.text(x, y, 'R', ha='center', va='center', fontweight='bold', fontsize=6, color='#ffffff', zorder=10)

    def render_medium_warehouse(self):
        """Simplified warehouse with Zone-coded endpoint IDs for 10-30 robots"""
        zone_colors = {
            0: ('#0a2a4a', '#00b0ff'),
            1: ('#0a3820', '#00e676'),
            2: ('#422000', '#ff9100'),
            3: ('#38004a', '#e040fb')
        }
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                cell = self.map_data[y, x]
                loc = y * self.grid_width + x
                
                if cell == '@':
                    rect = Rectangle((x-0.5, y-0.5), 1, 1, facecolor='#2a2b38', alpha=0.8)
                    self.ax_main.add_patch(rect)
                elif cell == 'e':
                    info = self.endpoint_info_by_loc.get(loc, None)
                    if info:
                        zid = info['zone']
                        num_str = str(info['id'])
                        bg_col, edge_col = zone_colors.get(zid, ('#2a2b38', '#ffd600'))
                        rect = Rectangle((x-0.5, y-0.5), 1, 1, facecolor=bg_col, edgecolor=edge_col, alpha=0.85, linewidth=0.7, zorder=2)
                        self.ax_main.add_patch(rect)
                        self.ax_main.text(x, y, num_str, ha='center', va='center', fontweight='bold', fontsize=4.5, color='#ffffff', zorder=10)
                    else:
                        rect = Rectangle((x-0.5, y-0.5), 1, 1, facecolor='orange', alpha=0.7)
                        self.ax_main.add_patch(rect)
                elif cell == 'r':
                    rect = Rectangle((x-0.5, y-0.5), 1, 1, facecolor='lightblue', alpha=0.5)
                    self.ax_main.add_patch(rect)

    def render_basic_warehouse(self):
        """Basic warehouse for 30-100 robots"""
        # Batch render for performance
        shelf_coords = np.where(self.map_data == '@')
        endpoint_coords = np.where(self.map_data == 'e')
        robot_coords = np.where(self.map_data == 'r')
        
        for y, x in zip(shelf_coords[0], shelf_coords[1]):
            rect = Rectangle((x-0.5, y-0.5), 1, 1, facecolor='brown', alpha=0.6)
            self.ax_main.add_patch(rect)
            
        for y, x in zip(endpoint_coords[0], endpoint_coords[1]):
            rect = Rectangle((x-0.5, y-0.5), 1, 1, facecolor='orange', alpha=0.5)
            self.ax_main.add_patch(rect)

    def render_minimal_warehouse(self):
        """Minimal warehouse for 100-500 robots"""
        # Only show obstacles as scatter plot for performance
        shelf_coords = np.where(self.map_data == '@')
        if len(shelf_coords[0]) > 0:
            self.ax_main.scatter(shelf_coords[1], shelf_coords[0], c='brown', s=4, alpha=0.5, marker='s')
        
        endpoint_coords = np.where(self.map_data == 'e')
        if len(endpoint_coords[0]) > 0:
            self.ax_main.scatter(endpoint_coords[1], endpoint_coords[0], c='orange', s=4, alpha=0.5, marker='s')

    def render_background_only(self):
        """Background color coding for 500+ robots"""
        # Create background image for maximum performance
        background = np.ones((self.grid_height, self.grid_width, 3))
        
        shelf_mask = self.map_data == '@'
        endpoint_mask = self.map_data == 'e'
        robot_mask = self.map_data == 'r'
        
        background[shelf_mask] = [0.6, 0.4, 0.2]  # Brown
        background[endpoint_mask] = [1.0, 0.6, 0.0]  # Orange
        background[robot_mask] = [0.7, 0.8, 1.0]  # Light blue
        
        self.ax_main.imshow(background, extent=[-0.5, self.grid_width-0.5, self.grid_height-0.5, -0.5], alpha=0.5)

    def update_dynamic_elements(self, timestep):
        """Adaptive robot rendering based on count"""
        # Clear previous elements
        for artist in self.agent_artists + self.trail_artists:
            artist.remove()
        self.agent_artists.clear()
        self.trail_artists.clear()
        
        if self.viz_mode == "HEATMAP":
            return self.render_heatmap_mode(timestep)
        else:
            return self.render_individual_robots(timestep)

    def render_individual_robots(self, timestep):
        """Render robots individually with interpolation"""
        robot_status = []
        active_count = 0
        picking_count = 0
        completed_count = 0
        
        t_int = int(timestep)
        t_frac = timestep - t_int
        
        for agent_id, path in self.solution['agents'].items():
            if t_int < len(path):
                # Current state
                tup_curr = path[t_int]
                if len(tup_curr) == 3:
                    x_curr, y_curr, orient_curr = tup_curr
                else:
                    x_curr, y_curr = tup_curr[:2]
                    orient_curr = -1
                
                # Next state
                if t_int + 1 < len(path):
                    tup_next = path[t_int + 1]
                    if len(tup_next) == 3:
                        x_next, y_next, orient_next = tup_next
                    else:
                        x_next, y_next = tup_next[:2]
                        orient_next = -1
                else:
                    x_next, y_next, orient_next = x_curr, y_curr, orient_curr
                
                # Interpolate position
                x = x_curr + (x_next - x_curr) * t_frac
                y = y_curr + (y_next - y_curr) * t_frac
                
                # Interpolate orientation/angle
                if orient_curr != -1:
                    angle_curr = orient_curr * 90
                    angle_next = orient_next * 90 if orient_next != -1 else angle_curr
                    angle_diff = (angle_next - angle_curr + 180) % 360 - 180
                    angle = angle_curr + angle_diff * t_frac
                else:
                    angle = 0
                
                color = self.colors[agent_id % len(self.colors)]
                
                # Draw rotating 3x1 footprint
                if orient_curr != -1:
                    rect = Rectangle((-1.5, -0.5), 3, 1, facecolor=color, edgecolor='black', linewidth=1.5, alpha=0.9, zorder=5)
                    import matplotlib.transforms as mtransforms
                    trans = mtransforms.Affine2D().rotate_deg(-angle).translate(x, y) + self.ax_main.transData
                    rect.set_transform(trans)
                else:
                    rect = Rectangle((x - 0.5, y - 0.5), 1, 1, facecolor=color, edgecolor='black', linewidth=1, alpha=0.8, zorder=5)
                
                self.ax_main.add_patch(rect)
                self.agent_artists.append(rect)
                
                # Target endpoint lookup and status
                target_info = self.get_current_target_info(agent_id, timestep)
                target_label = target_info['label'] if target_info else "IDLE"
                
                cell_x, cell_y = int(round(x)), int(round(y))
                cell_type = self.map_data[cell_y, cell_x] if 0 <= cell_y < self.grid_height and 0 <= cell_x < self.grid_width else '?'
                zone_id = agent_id % 4
                completed_tasks = self.get_completed_tasks_count(agent_id, timestep)
                
                # Detect picking/dwelling (at target endpoint or adjacent service cell)
                is_picking = (cell_type == 'e') or (target_info and target_info['x'] == cell_x and abs(target_info['y'] - cell_y) <= 1 and (orient_curr == 0 or orient_curr == 2))

                # Robot ID centered inside robot body, target badge floating offset above robot
                if self.show_robot_ids and self.font_size > 0:
                    # 1. Clean Robot ID inside robot body
                    text_id = self.ax_main.text(x, y, f"R{agent_id}", ha='center', va='center',
                                               fontweight='bold', fontsize=self.font_size, color='#ffffff', zorder=7)
                    self.agent_artists.append(text_id)
                    
                    # 2. Dynamic Target & Task floating tag offset above robot
                    tag_y = y - 0.85
                    if is_picking:
                        tag_label = f"R{agent_id} [PICK {target_label}]"
                        badge_edge = "#ffd600"
                    else:
                        tag_label = f"R{agent_id} → {target_label} [{completed_tasks}]"
                        badge_edge = color
                        
                    text_tag = self.ax_main.text(x, tag_y, tag_label, ha='center', va='center',
                                               fontweight='bold', fontsize=max(5.5, self.font_size - 2.5), color='#ffffff', zorder=8,
                                               bbox=dict(boxstyle="round,pad=0.2", facecolor="#0a0a14", edgecolor=badge_edge, alpha=0.9, linewidth=1.2))
                    self.agent_artists.append(text_tag)
                
                # Trail
                if t_int > 0 and self.trail_length > 0:
                    trail_len = min(self.trail_length, t_int)
                    if trail_len > 1:
                        trail_points = [path[t] for t in range(t_int-trail_len, t_int)]
                        trail_x = [pt[0] for pt in trail_points]
                        trail_y = [pt[1] for pt in trail_points]
                        trail_x.append(x)
                        trail_y.append(y)
                        line, = self.ax_main.plot(trail_x, trail_y, color=color, alpha=self.trail_alpha, linewidth=1)
                        self.trail_artists.append(line)
                
                if is_picking:
                    picking_count += 1
                    if self.show_individual_status:
                        robot_status.append(f"R{agent_id} (Z{zone_id}): -> {target_label} [PICKING] ({completed_tasks} done)")
                    star = self.ax_main.plot(cell_x, cell_y, '*', color='yellow', markersize=max(6, 12-self.num_agents//10), markeredgecolor='black')[0]
                    self.agent_artists.append(star)
                else:
                    active_count += 1
                    if self.show_individual_status:
                        robot_status.append(f"R{agent_id} (Z{zone_id}): -> {target_label} [NAVIGATING] ({completed_tasks} done)")
            else:
                completed_count += 1
                if self.show_individual_status:
                    completed_tasks = self.get_completed_tasks_count(agent_id, timestep)
                    robot_status.append(f"R{agent_id}: [COMPLETED] ({completed_tasks} done)")
        
        # Update title
        total_tasks_completed = sum(self.get_completed_tasks_count(agent_id, timestep) for agent_id in self.solution['agents'].keys())
        summary = f"Active: {active_count} | Picking: {picking_count} | Tasks: {total_tasks_completed} | "
        self.ax_main.set_title(f'Kiva Warehouse ({self.num_agents} robots) - {summary} - Step: {timestep:.1f}', 
                              fontsize=12, fontweight='bold')
        
        return robot_status, {'active': active_count, 'picking': picking_count, 'completed': completed_count}

    def render_heatmap_mode(self, timestep):
        """Heatmap visualization for 500+ robots"""
        # Create density heatmap
        density_map = np.zeros((self.grid_height, self.grid_width))
        
        for agent_id, path in self.solution['agents'].items():
            if timestep < len(path):
                x, y = path[timestep]
                if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                    density_map[y, x] += 1
        
        # Clear previous heatmap
        for artist in self.agent_artists:
            artist.remove()
        self.agent_artists.clear()
        
        # Draw heatmap
        if np.max(density_map) > 0:
            im = self.ax_main.imshow(density_map, cmap='hot', alpha=0.7, 
                                   extent=[-0.5, self.grid_width-0.5, self.grid_height-0.5, -0.5])
            self.agent_artists.append(im)
        
        active_robots = np.sum(density_map)
        self.ax_main.set_title(f'Kiva Warehouse Heatmap - {int(active_robots)} Active Robots - Step: {timestep}', 
                              fontsize=12, fontweight='bold')
        
        return [], {'active': int(active_robots), 'picking': 0, 'completed': self.num_agents - int(active_robots)}

    def update_info_panel(self, timestep, robot_status, summary_stats):
        """Adaptive info panel"""
        if not self.use_info_panel:
            return
            
        self.ax_info.clear()
        self.ax_info.set_xlim(0, 10)
        self.ax_info.set_ylim(0, 10)
        self.ax_info.axis('off')
        
        if self.viz_mode == "DETAILED":
            # Full detail mode
            info_text = f"""KIVA WAREHOUSE - DETAILED VIEW
================================
Grid: {self.grid_width}x{self.grid_height}
Robots: {self.num_agents} (Mode: {self.viz_mode})

Warehouse:
• Shelves: {self.warehouse_stats['shelves']}
• Endpoints: {self.warehouse_stats['endpoints']}
• Robot Zones: {self.warehouse_stats['robot_zones']}

Status Summary:
• Active: {summary_stats['active']}
• Picking: {summary_stats['picking']}
• Completed: {summary_stats['completed']}

Timestep: {timestep}/{self.max_timestep-1}

Individual Robots:
{chr(10).join(robot_status[:15])}
{f"... and {len(robot_status) - 15} more" if len(robot_status) > 15 else ""}"""

        else:  # MEDIUM mode
            # Summary mode
            info_text = f"""KIVA WAREHOUSE - SUMMARY VIEW
=============================
{self.num_agents} Robots (Mode: {self.viz_mode})
Grid: {self.grid_width}x{self.grid_height}

ROBOT STATUS:
Active: {summary_stats['active']}
Picking: {summary_stats['picking']}
Completed: {summary_stats['completed']}

PROGRESS:
Timestep: {timestep}/{self.max_timestep-1}
Progress: {timestep/self.max_timestep*100:.1f}%

WAREHOUSE:
Shelves: {self.warehouse_stats['shelves']}
Endpoints: {self.warehouse_stats['endpoints']}

Top 8 Robots:
{chr(10).join(robot_status[:8])}"""
        
        font_size = 9 if self.viz_mode == "DETAILED" else 8
        self.ax_info.text(0.1, 9.8, info_text, fontsize=font_size, ha='left', va='top',
                         fontfamily='monospace', color='#e0e6ed',
                         bbox=dict(boxstyle="round,pad=0.4", facecolor="#161622", edgecolor="#00b0ff", alpha=0.95, linewidth=1.5))

    def animate(self, frame):
        """Generalized animation function with interpolation"""
        t = frame / self.substeps
        self.current_timestep = t
        robot_status, summary_stats = self.update_dynamic_elements(t)
        
        if self.use_info_panel:
            self.update_info_panel(t, robot_status, summary_stats)
        
        return self.agent_artists + self.trail_artists

    # Include all the previous data loading methods (load_kiva_map, load_raw_data, etc.)
    # [Previous methods remain the same - keeping the response concise]

    def generate_demo_data(self):
        """Generate demo data for any number of robots"""
        demo_data = {}
        
        # Find positions
        robot_positions = np.where(self.map_data == 'r')
        endpoint_positions = np.where(self.map_data == 'e')
        
        robot_locs = [(y * self.grid_width + x, x, y) for y, x in zip(robot_positions[0], robot_positions[1])]
        endpoint_locs = [(y * self.grid_width + x, x, y) for y, x in zip(endpoint_positions[0], endpoint_positions[1])]
        
        # **ADAPTIVE: Generate appropriate number of demo robots**
        num_agents = getattr(self, 'num_agents', 0)
        if not robot_locs:  # If no robot positions in map, create distributed starts
            num_demo_robots = min(num_agents, 50) if num_agents > 0 else 5
        else:
            num_demo_robots = min(num_agents, len(robot_locs) * 3) if num_agents > 0 else 5
        
        for agent_id in range(num_demo_robots):
            # Distribute starting positions
            if robot_locs:
                start_loc, start_x, start_y = robot_locs[agent_id % len(robot_locs)]
            else:
                # Create grid distribution for many robots
                start_x = 1 + (agent_id % int(math.sqrt(self.grid_width - 2)))
                start_y = 1 + (agent_id // int(math.sqrt(self.grid_width - 2)))
                start_x = min(start_x, self.grid_width - 2)
                start_y = min(start_y, self.grid_height - 2)
            
            # Distribute goal positions
            if endpoint_locs:
                goal_loc, goal_x, goal_y = endpoint_locs[(agent_id * 7) % len(endpoint_locs)]
            else:
                goal_x = self.grid_width - 2 - (agent_id % 5)
                goal_y = self.grid_height - 2 - (agent_id // 5)
            
            # Variable path lengths for realistic movement
            base_length = 30
            variation = agent_id % 20
            path_length = base_length + variation
            
            path = []
            for t in range(path_length):
                progress = min(1.0, t / (path_length * 0.8))
                x = int(start_x + (goal_x - start_x) * progress)
                y = int(start_y + (goal_y - start_y) * progress)
                
                # Add movement variation
                if t % 3 == 0 and t > 5:
                    x += (agent_id % 3) - 1
                    y += ((agent_id + t) % 3) - 1
                    x = max(0, min(x, self.grid_width - 1))
                    y = max(0, min(y, self.grid_height - 1))
                
                location_id = y * self.grid_width + x
                path.append((location_id, t))
            
            demo_data[agent_id] = path
        
        print(f"Generated demo data for {num_demo_robots} robots")
        return demo_data

    # [Include all other methods from previous versions]
    def load_kiva_map(self, map_file):
        """Load Kiva warehouse map"""
        if not os.path.exists(map_file):
            print(f"ERROR: Map file {map_file} not found!")
            return np.array([['.' for _ in range(46)] for _ in range(33)])
        
        with open(map_file, 'r') as f:
            lines = f.readlines()
        
        try:
            header = lines[0].strip().split(',')
            map_height, map_width = int(header[0]), int(header[1])
            
            map_grid = []
            for i in range(4, 4 + map_height):
                if i < len(lines):
                    row = lines[i].strip()[:map_width].ljust(map_width, '.')
                    map_grid.append(list(row))
                else:
                    map_grid.append(['.'] * map_width)
            
            return np.array(map_grid)
            
        except Exception as e:
            print(f"Error parsing map: {e}")
            return np.array([['.' if (x+y) % 3 != 0 else '@' for x in range(46)] for y in range(33)])

    def load_raw_data(self, results_file):
        """Load RHCR results"""
        if not os.path.exists(results_file):
            return self.generate_demo_data()
        
        try:
            with open(results_file, 'r') as f:
                lines = f.readlines()
            
            num_agents = int(lines[0].strip())
            raw_data = {}
            
            for agent_id in range(num_agents):
                if agent_id + 1 < len(lines):
                    line = lines[agent_id + 1].strip()
                    positions = line.split(';')
                    
                    agent_data = []
                    for pos in positions:
                        if pos.strip():
                            try:
                                parts = pos.split(',')
                                location_id = int(parts[0])
                                orientation = int(parts[1]) if len(parts) > 1 else -1
                                timestep = int(parts[2]) if len(parts) > 2 else -1
                                agent_data.append((location_id, orientation, timestep))
                            except:
                                continue
                    
                    raw_data[agent_id] = sorted(agent_data, key=lambda x: x[2])
            
            return raw_data
            
        except Exception as e:
            print(f"Error loading results: {e}")
            return self.generate_demo_data()

    def load_tasks(self, tasks_file):
        tasks = {}
        if not os.path.exists(tasks_file):
            return tasks
        try:
            with open(tasks_file, 'r') as f:
                lines = f.readlines()
            if not lines:
                return tasks
            num_agents = int(lines[0].strip())
            for idx in range(num_agents):
                if idx + 1 < len(lines):
                    line = lines[idx + 1].strip()
                    if not line:
                        continue
                    parts = line.split(' ')
                    agent_id = int(parts[0])
                    task_tokens = parts[1].split(';')
                    agent_tasks = []
                    for tok in task_tokens:
                        if not tok.strip():
                            continue
                        subparts = tok.split(',')
                        if len(subparts) >= 2:
                            loc = int(subparts[0])
                            finish_time = int(subparts[1])
                            agent_tasks.append((loc, finish_time))
                    tasks[agent_id] = agent_tasks
        except Exception as e:
            print(f"Error loading tasks: {e}")
        return tasks

    def get_completed_tasks_count(self, agent_id, t):
        if agent_id not in self.tasks:
            return 0
        count = 0
        for loc, finish_time in self.tasks[agent_id][1:]:
            if finish_time >= 0 and finish_time <= t:
                count += 1
        return count

    def location_to_xy(self, location_id):
        """Convert location ID to x,y coordinates"""
        return location_id % self.grid_width, location_id // self.grid_width

    def convert_to_solution(self):
        """Convert to solution format"""
        solution = {'agents': {}}
        
        for agent_id, agent_data in self.raw_data.items():
            agent_path = []
            for item in agent_data:
                if len(item) == 3:
                    location_id, orientation, timestep = item
                else:
                    location_id, timestep = item
                    orientation = -1
                x, y = self.location_to_xy(location_id)
                x = max(0, min(x, self.grid_width - 1))
                y = max(0, min(y, self.grid_height - 1))
                agent_path.append((x, y, orientation))
            
            solution['agents'][agent_id] = agent_path
        
        return solution

    def run(self):
        """Start generalized visualization"""
        print(f"\nStarting Generalized Kiva Warehouse Visualization")
        print(f"Robots: {self.num_agents} | Mode: {self.viz_mode}")
        print(f"Animation: {self.animation_interval}ms intervals")
        
        mode_descriptions = {
            "DETAILED": "Full detail with individual robot tracking",
            "MEDIUM": "Simplified view with robot IDs", 
            "COMPACT": "Compact view for moderate robot counts",
            "DENSE": "Minimal detail for large robot counts",
            "HEATMAP": "Density heatmap for massive robot swarms"
        }
        
        print(f"Description: {mode_descriptions.get(self.viz_mode, 'Unknown mode')}")
        print("Close window to exit")
        
        anim = animation.FuncAnimation(
            self.fig, self.animate, frames=(self.max_timestep - 1) * self.substeps,
            interval=int(self.animation_interval / self.substeps),
            blit=False,
            repeat=True,
            cache_frame_data=False
        )
        
        plt.tight_layout()
        plt.show()
        return anim

def main():
    print("=" * 70)
    print("    GENERALIZED KIVA WAREHOUSE VISUALIZER")
    print("    Automatically adapts to any number of robots")
    print("=" * 70)
    
    try:
        visualizer = GeneralizedKivaVisualizer()
        visualizer.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
     main()