import os
import sys
import matplotlib
matplotlib.use('Agg') # Headless rendering
import matplotlib.pyplot as plt
from PIL import Image

# Import the existing visualizer class
from mapf_visualizer import GeneralizedKivaVisualizer, _resolve_data_path

def create_30s_gif(map_file='kiva_4zone_shaved.map', 
                   paths_file='exp/bench_outbound_39row.2/paths.txt',
                   output_gif='kiva_fleet_simulation_30s.gif',
                   target_duration_sec=30.0,
                   fps=10):
    print("=" * 60)
    print("GENERATING 30-SECOND STUDIO-GRADE MAPF SIMULATION GIF")
    print(f"Map: {map_file}")
    print(f"Paths: {paths_file}")
    print(f"Output: {output_gif}")
    print(f"Target duration: {target_duration_sec}s at {fps} FPS")
    print("=" * 60)

    # Initialize visualizer in headless mode
    viz = GeneralizedKivaVisualizer(map_file, paths_file)
    
    # Configure high-quality aesthetic settings
    # We want a clean aspect ratio and resolution that fits nicely in GitHub README
    viz.fig.set_size_inches(16, 9.5)
    viz.fig.set_dpi(72) # Crisp resolution: ~1152 x 684
    
    # Calculate frames
    # 30 seconds at 10 fps = 300 frames
    total_frames = int(target_duration_sec * fps)
    frame_duration_ms = int(1000.0 / fps) # 100ms
    
    # Check max timesteps available
    max_t = viz.max_timestep
    print(f"Dataset has {max_t} total timesteps.")
    
    # Let's start from t=5 (when all robots have deployed from spawn)
    start_t = 5
    # If we advance by 0.5 timesteps per frame (smooth interpolation, substeps=2)
    # 300 frames * 0.5 = 150 timesteps covered over 30 seconds!
    step_increment = 0.5
    
    frames = []
    print(f"Rendering {total_frames} frames (time increment = {step_increment} per frame)...")
    
    for i in range(total_frames):
        current_t = start_t + i * step_increment
        if current_t >= max_t - 1:
            current_t = max_t - 1
            
        viz.animate(current_t)
        viz.fig.canvas.draw()
        
        # Extract RGB buffer directly from matplotlib canvas
        rgba_buffer = viz.fig.canvas.buffer_rgba()
        img = Image.frombuffer('RGBA', viz.fig.canvas.get_width_height(), rgba_buffer, 'raw', 'RGBA', 0, 1)
        
        # Convert to RGB and resize slightly if needed for ultra-sharp, compact GIF
        # Convert to P (palette mode) with adaptive palette to keep file size under 8MB
        rgb_img = img.convert('RGB')
        
        # Palettize with fast adaptive quantization
        pal_img = rgb_img.convert('P', palette=Image.ADAPTIVE, colors=128)
        frames.append(pal_img)
        
        if (i + 1) % 50 == 0 or i == total_frames - 1:
            print(f"  Rendered {i + 1}/{total_frames} frames ({(i + 1) / total_frames * 100:.1f}%)...")
            
    print(f"Saving {len(frames)} frames to {output_gif} with duration={frame_duration_ms}ms per frame...")
    frames[0].save(
        output_gif,
        save_all=True,
        append_images=frames[1:],
        duration=frame_duration_ms,
        loop=0,
        optimize=True
    )
    
    file_size_mb = os.path.getsize(output_gif) / (1024 * 1024)
    print(f"SUCCESS! Created {output_gif} ({file_size_mb:.2f} MB, {len(frames) * frame_duration_ms / 1000.0:.1f}s playback duration)")
    plt.close(viz.fig)
    return output_gif

if __name__ == '__main__':
    map_path = sys.argv[1] if len(sys.argv) > 1 else 'kiva_4zone_shaved.map'
    paths_path = sys.argv[2] if len(sys.argv) > 2 else 'exp/bench_outbound_39row.2/paths.txt'
    out_path = sys.argv[3] if len(sys.argv) > 3 else 'kiva_simulation_demo_30s.gif'
    
    create_30s_gif(map_path, paths_path, out_path, target_duration_sec=30.0, fps=10)
