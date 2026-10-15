from PIL import Image, ImageOps, ImageDraw, ImageFont

# Dimensions of the showcase frame
FRAME_W = 2150
FRAME_H = 1188

# Create white canvas
canvas = Image.new('RGB', (FRAME_W, FRAME_H), (255, 255, 255))
draw = ImageDraw.Draw(canvas)

# Load images
im_arch = Image.open('system_architecture_diagram.png')
im_plot = Image.open('plot2_time_allocation.png')

# Left panel: Architecture diagram
# Right panel: Plot 2 Time allocation (or Plot 4 fleet scalability)
# Target heights: 1040 (leaving room for labels)
left_w = 1240
right_w = FRAME_W - left_w - 40 # 870

# Resize architecture keeping aspect ratio
im_arch.thumbnail((left_w, 1020), Image.Resampling.LANCZOS)
arch_x = 20 + (left_w - im_arch.width) // 2
arch_y = 20 + (1040 - im_arch.height) // 2
canvas.paste(im_arch, (arch_x, arch_y))

# Resize plot keeping aspect ratio
im_plot.thumbnail((right_w, 1020), Image.Resampling.LANCZOS)
plot_x = left_w + 30 + (right_w - im_plot.width) // 2
plot_y = 20 + (1040 - im_plot.height) // 2
canvas.paste(im_plot, (plot_x, plot_y))

# Sub-captions
try:
    font = ImageFont.truetype('arial.ttf', 36)
except:
    font = ImageFont.load_default()

# Add labels
draw.text((left_w // 2 - 200, 1080), "(a) Proposed Bi-Level MAPF Architecture", fill=(20, 20, 80), font=font)
draw.text((left_w + 30 + right_w // 2 - 220, 1080), "(b) Fleet Time & Congestion Breakdown", fill=(20, 20, 80), font=font)

canvas.save('poster_assets/showcase_figure.png', quality=95)
print('Saved poster_assets/showcase_figure.png successfully!')
