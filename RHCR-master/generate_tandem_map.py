# Generate kiva_tandem_4zone.map (35 rows x 73 cols)
# 4 rack zones, with 2 bays in series on left and right: .rrr.....rrr

rows = 35
cols = 73

header = [
    "35,73",
    "512",
    "84",
    "5000"
]

grid = []

# Helper components
DOTS_73 = "." * 73
DOTS_16 = "." * 16
LEFT_BAY = ".rrr.....rrr...."   # 1 + 3 + 5 + 3 + 4 = 16
RIGHT_BAY = "....rrr.....rrr."  # 4 + 3 + 5 + 3 + 1 = 16

RACK_CORE = "@@@@@@@@...@@@@@@@@...@@@@@@@@...@@@@@@@@"   # 8 + 3 + 8 + 3 + 8 + 3 + 8 = 41
EP_CORE   = "eeeeeeee...eeeeeeee...eeeeeeee...eeeeeeee"   # 41
DOTS_41   = "." * 41                                       # 41

for r in range(rows):
    if r in (0, 1, 17, 33, 34):
        # Cross highways
        grid.append(DOTS_73)
    elif r in (2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32):
        # Endpoint rows
        row_str = DOTS_16 + EP_CORE + DOTS_16
        assert len(row_str) == 73
        grid.append(row_str)
    elif r in (3, 7, 11, 15, 19, 23, 27, 31):
        # Rack rows with bays
        row_str = LEFT_BAY + RACK_CORE + RIGHT_BAY
        assert len(row_str) == 73
        grid.append(row_str)
    elif r in (5, 9, 13, 21, 25, 29):
        # Corridor rows with bays
        row_str = LEFT_BAY + DOTS_41 + RIGHT_BAY
        assert len(row_str) == 73
        grid.append(row_str)
    else:
        raise ValueError(f"Unhandled row {r}")

assert len(grid) == 35

map_content = "\n".join(header + grid) + "\n"

with open("kiva_tandem_4zone.map", "w", newline="\n") as f:
    f.write(map_content)

print(f"Generated kiva_tandem_4zone.map ({len(grid)}x{len(grid[0])})")
