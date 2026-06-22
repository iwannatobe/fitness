"""Graphics utilities."""
def lighten(color, factor=0.28):
    return tuple(min(1.0, c + (1.0 - c) * factor) if i < 3 else c for i, c in enumerate(color))

def rgba_hex(color):
    r, g, b = int(color[0] * 255), int(color[1] * 255), int(color[2] * 255)
    return f"{r:02x}{g:02x}{b:02x}"
