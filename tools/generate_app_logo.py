"""Generate the Black Titanium Fitness Control application mark."""

from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "icons" / "icon.png"
SCALE = 2
SIZE = 1024


def box(values):
    return tuple(value * SCALE for value in values)


def main():
    image = Image.new("RGB", (SIZE * SCALE, SIZE * SCALE), "#07090B")
    draw = ImageDraw.Draw(image)

    # Titanium chassis and recessed smoked-glass face.
    draw.rectangle(box((68, 68, 956, 956)), fill="#111519", outline="#66727A", width=6 * SCALE)
    draw.rectangle(box((82, 82, 942, 942)), outline="#252C31", width=8 * SCALE)
    draw.rectangle(box((112, 112, 912, 912)), fill="#080B0E", outline="#3A444C", width=4 * SCALE)
    draw.line(box((122, 122, 902, 122)), fill="#66727A", width=2 * SCALE)

    # Precision corner indexes keep the mark equipment-like at large sizes.
    tick = "#3A444C"
    for x, y, sx, sy in ((148, 148, 1, 1), (876, 148, -1, 1),
                         (148, 876, 1, -1), (876, 876, -1, -1)):
        draw.line(box((x, y, x + 64 * sx, y)), fill=tick, width=8 * SCALE)
        draw.line(box((x, y, x, y + 64 * sy)), fill=tick, width=8 * SCALE)

    # Dim underlay gives the VFD shapes depth without blur or neon bloom.
    cyan_dim = "#197781"
    orange_dim = "#9D5B18"
    draw.rectangle(box((244, 250, 326, 774)), fill=cyan_dim)
    draw.rectangle(box((244, 250, 774, 332)), fill=cyan_dim)
    draw.rectangle(box((244, 692, 774, 774)), fill=cyan_dim)
    draw.rectangle(box((692, 250, 774, 404)), fill=cyan_dim)
    draw.rectangle(box((692, 620, 774, 774)), fill=cyan_dim)

    draw.rectangle(box((420, 350, 502, 680)), fill=orange_dim)
    draw.rectangle(box((420, 350, 674, 432)), fill=orange_dim)
    draw.rectangle(box((420, 492, 626, 574)), fill=orange_dim)

    # Main FC monogram: cyan Control frame, orange Fitness core.
    cyan = "#3ED9E6"
    orange = "#FF9D2E"
    draw.rectangle(box((232, 238, 314, 762)), fill=cyan)
    draw.rectangle(box((232, 238, 762, 320)), fill=cyan)
    draw.rectangle(box((232, 680, 762, 762)), fill=cyan)
    draw.rectangle(box((680, 238, 762, 392)), fill=cyan)
    draw.rectangle(box((680, 608, 762, 762)), fill=cyan)

    draw.rectangle(box((408, 338, 490, 668)), fill=orange)
    draw.rectangle(box((408, 338, 662, 420)), fill=orange)
    draw.rectangle(box((408, 480, 614, 562)), fill=orange)

    # Equipment registration cuts and one restrained online indicator.
    draw.rectangle(box((232, 490, 276, 510)), fill="#080B0E")
    draw.rectangle(box((718, 490, 762, 510)), fill="#080B0E")
    draw.rectangle(box((812, 812, 866, 830)), fill="#2C7749")
    draw.rectangle(box((812, 800, 866, 818)), fill="#63D98B")

    image = image.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    image.save(OUTPUT, format="PNG", optimize=True)
    print(f"generated={OUTPUT} size={image.size}")


if __name__ == "__main__":
    main()
