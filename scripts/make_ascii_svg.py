
import argparse
import html
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

RAMP = " .`:-=+*cs#%@"
# Bright (sparse) -> Dark (dense)

GRID_WIDTH = 100
GRID_HEIGHT = 53

FONT_SIZE = 10
CHAR_WIDTH = 6
LINE_HEIGHT = 11

TEXT_COLOR = "#777777"
BACKGROUND_COLOR = "#ffffff"

ROW_DURATION = 2.5
ROW_STAGGER = 0.045

OUTPUT_FILE = "avi-ascii.svg"
DEFAULT_INPUT = "data/prepared_photo.png"


# --------------------------------------------------
# 1. LOAD AND PREPARE IMAGE
# --------------------------------------------------

def load_image(image_path):
    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Prepared image not found: {path}"
        )

    image = Image.open(path).convert("RGB")

    return image


# --------------------------------------------------
# 2. RESIZE IMAGE TO CHARACTER GRID
# --------------------------------------------------

def resize_to_grid(image, width, height):
    """
    Preserve aspect ratio and fit the image
    into a fixed character grid.

    White padding ensures the background maps
    to empty ASCII characters.
    """

    gray = ImageOps.grayscale(image)

    resized = ImageOps.contain(
        gray,
        (width, height),
        method=Image.Resampling.LANCZOS
    )

    canvas = Image.new(
        "L",
        (width, height),
        255
    )

    x_offset = (width - resized.width) // 2
    y_offset = (height - resized.height) // 2

    canvas.paste(resized, (x_offset, y_offset))

    return np.asarray(canvas, dtype=np.uint8)


# --------------------------------------------------
# 3. PIXEL BRIGHTNESS TO ASCII
# --------------------------------------------------

def brightness_to_ascii(brightness):
    """
    Convert brightness into a character.

    255 = white = space
    0   = black = dense character
    """

    ramp_index = int(
        (255 - brightness) / 255 * (len(RAMP) - 1)
    )

    ramp_index = max(
        0,
        min(ramp_index, len(RAMP) - 1)
    )

    return RAMP[ramp_index]


def generate_ascii_grid(pixel_array):
    """
    Generate ASCII characters for every pixel.
    """

    rows = []

    for row in pixel_array:

        ascii_row = "".join(
            brightness_to_ascii(int(pixel))
            for pixel in row
        )

        rows.append(ascii_row)

    return rows


# --------------------------------------------------
# 4. SVG DOCUMENT HEADER
# --------------------------------------------------

def create_svg_header(width, height):
    return f"""<?xml version="1.0" encoding="UTF-8"?>

<svg
    xmlns="http://www.w3.org/2000/svg"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    width="{width}"
    height="{height}"
    viewBox="0 0 {width} {height}"
    role="img"
    aria-label="Animated ASCII portrait"
>

    <title>Self-typing ASCII Portrait</title>

    <rect
        width="100%"
        height="100%"
        fill="{BACKGROUND_COLOR}"
    />

    <defs>
"""


# --------------------------------------------------
# 5. GENERATE ROW CLIPS
# --------------------------------------------------

def create_clip_definitions(rows, total_width):
    """
    Each row gets an independent clipping rectangle.

    The clip expands from left to right.
    """

    definitions = []

    for index, _ in enumerate(rows):

        y = index * LINE_HEIGHT
        delay = index * ROW_STAGGER

        definitions.append(f"""
        <clipPath id="clip-{index}">
            <rect
                x="0"
                y="0"
                width="0"
                height="{LINE_HEIGHT}"
            >
                <animate
                    attributeName="width"
                    from="0"
                    to="{total_width}"
                    begin="{delay:.3f}s"
                    dur="{ROW_DURATION}s"
                    fill="freeze"
                />
            </rect>
        </clipPath>
        """)

    return "\n".join(definitions)


# --------------------------------------------------
# 6. GENERATE ANIMATED ASCII ROWS
# --------------------------------------------------

def create_animated_rows(rows, total_width):
    """
    Render every ASCII row with:

    - Monochrome text
    - Independent horizontal clipping
    - A moving cursor
    - Staggered animation timing
    """

    elements = []

    for index, row in enumerate(rows):

        y = index * LINE_HEIGHT
        baseline = y + FONT_SIZE
        delay = index * ROW_STAGGER

        safe_row = html.escape(row, quote=False)

        elements.append(f"""
        <g transform="translate(0, {y})">

            <!-- ASCII characters -->
            <text
                x="0"
                y="{FONT_SIZE}"
                font-family="monospace"
                font-size="{FONT_SIZE}px"
                fill="{TEXT_COLOR}"
                xml:space="preserve"
                clip-path="url(#clip-{index})"
            >{safe_row}</text>

            <!-- Moving typing cursor -->
            <rect
                x="0"
                y="0"
                width="5"
                height="{FONT_SIZE}"
                fill="#555555"
                opacity="0.85"
            >
                <animate
                    attributeName="x"
                    from="0"
                    to="{total_width}"
                    begin="{delay:.3f}s"
                    dur="{ROW_DURATION}s"
                    fill="freeze"
                />

                <animate
                    attributeName="opacity"
                    values="0.85;0.85;0"
                    keyTimes="0;0.98;1"
                    begin="{delay:.3f}s"
                    dur="{ROW_DURATION}s"
                    fill="freeze"
                />
            </rect>

        </g>
        """)

    return "\n".join(elements)


# --------------------------------------------------
# 7. BUILD COMPLETE SVG
# --------------------------------------------------

def generate_svg(rows, output_path):
    """
    Combine the SVG header, clipping definitions,
    animated rows and closing SVG tag.
    """

    width = GRID_WIDTH * CHAR_WIDTH
    height = GRID_HEIGHT * LINE_HEIGHT

    svg_parts = [
        create_svg_header(width, height),

        create_clip_definitions(
            rows,
            width
        ),

        """
    </defs>

    <g>
""",

        create_animated_rows(
            rows,
            width
        ),

        """
    </g>

</svg>
"""
    ]

    svg_content = "\n".join(svg_parts)

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path.write_text(
        svg_content,
        encoding="utf-8"
    )

    return output_path


# --------------------------------------------------
# 8. MAIN PIPELINE
# --------------------------------------------------

def make_ascii_svg(input_path, output_path):

    print("\n[1/4] Loading prepared portrait...")

    image = load_image(input_path)

    print("[2/4] Resizing to ASCII character grid...")

    pixels = resize_to_grid(
        image,
        GRID_WIDTH,
        GRID_HEIGHT
    )

    print("[3/4] Converting brightness to ASCII...")

    ascii_rows = generate_ascii_grid(pixels)

    print("[4/4] Generating animated SVG...")

    output = generate_svg(
        ascii_rows,
        output_path
    )

    total_duration = (
        ROW_DURATION
        + (GRID_HEIGHT - 1) * ROW_STAGGER
    )

    print("\nASCII SVG generated successfully!")
    print(f"Output: {output.resolve()}")
    print(f"Grid: {GRID_WIDTH} x {GRID_HEIGHT}")
    print(f"Characters: {GRID_WIDTH * GRID_HEIGHT}")
    print(f"Animation duration: {total_duration:.2f}s")


# --------------------------------------------------
# ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Generate a self-typing ASCII SVG portrait."
    )

    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT,
        help="Prepared portrait image"
    )

    parser.add_argument(
        "--output",
        default=OUTPUT_FILE,
        help="Output SVG filename"
    )

    args = parser.parse_args()

    make_ascii_svg(
        args.input,
        args.output
    )
