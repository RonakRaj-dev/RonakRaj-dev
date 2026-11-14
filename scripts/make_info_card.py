
import os
import html
from pathlib import Path


# ==================================================
# CONFIGURATION
# ==================================================

OUTPUT_FILE = "info-card.svg"

STATIC = os.getenv("STATIC", "0") == "1"

WIDTH = 520
HEIGHT = 300

BACKGROUND = "#161b22"
BORDER = "#30363d"

TITLE_COLOR = "#61afef"
LABEL_COLOR = "#e5c07b"
VALUE_COLOR = "#c9d1d9"
ACCENT_COLOR = "#98c379"
MUTED_COLOR = "#8b949e"

FONT = "monospace"

# Animation settings
ANIMATION_DURATION = 0.45
ANIMATION_STAGGER = 0.16

# ==================================================
# PROFILE INFORMATION
# EDIT THESE VALUES
# ==================================================

PROFILE = {
    "name": "Ronak Raj",
    "subtitle": "AI / ML ENGINEER",
    "now": "Building AI Agents",
    "prev": "ML Engineering",
    "stack": "Python, PyTorch, RAG, MCP",
    "highlights": "Multi-Agent Systems, CV, Research"
}

# ==================================================
# SVG HELPERS
# ==================================================

def escape(value):
    """Escape text for safe SVG/XML output."""
    return html.escape(str(value), quote=True)


def svg_header():
    return f"""<?xml version="1.0" encoding="UTF-8"?>

<svg
    xmlns="http://www.w3.org/2000/svg"
    width="{WIDTH}"
    height="{HEIGHT}"
    viewBox="0 0 {WIDTH} {HEIGHT}"
    role="img"
    aria-label="Developer information card"
>

<title>{escape(PROFILE['name'])} - Developer Profile</title>

<rect
    width="100%"
    height="100%"
    rx="12"
    fill="{BACKGROUND}"
    stroke="{BORDER}"
    stroke-width="1"
/>
"""


# ==================================================
# WINDOW TITLE BAR
# ==================================================

def create_title_bar():

    return f"""
    <!-- Terminal title bar -->

    <rect
        x="1"
        y="1"
        width="{WIDTH - 2}"
        height="38"
        rx="11"
        fill="#21262d"
    />

    <rect
        x="1"
        y="27"
        width="{WIDTH - 2}"
        height="12"
        fill="#21262d"
    />

    <circle cx="20" cy="20" r="5" fill="#ff5f56"/>
    <circle cx="38" cy="20" r="5" fill="#ffbd2e"/>
    <circle cx="56" cy="20" r="5" fill="#27c93f"/>

    <text
        x="{WIDTH / 2}"
        y="24"
        text-anchor="middle"
        font-family="{FONT}"
        font-size="11"
        fill="{MUTED_COLOR}"
    >developer@profile ~ </text>
    """


# ==================================================
# PROFILE HEADER
# ==================================================

def create_profile_header():

    name = escape(PROFILE["name"])
    subtitle = escape(PROFILE["subtitle"])

    return f"""
    <g transform="translate(24, 65)">

        <!-- Profile name -->

        <text
            x="0"
            y="0"
            font-family="{FONT}"
            font-size="21"
            font-weight="bold"
            fill="{TITLE_COLOR}"
        >{name}</text>

        <!-- Subtitle -->

        <text
            x="0"
            y="23"
            font-family="{FONT}"
            font-size="10"
            letter-spacing="2"
            fill="{ACCENT_COLOR}"
        >{subtitle}</text>

        <!-- Separator -->

        <line
            x1="0"
            y1="38"
            x2="470"
            y2="38"
            stroke="{BORDER}"
            stroke-width="1"
        />

    </g>
    """


# ==================================================
# KEY / VALUE ROWS
# ==================================================

def create_info_rows():

    rows = [
        ("Now", PROFILE["now"]),
        ("Prev", PROFILE["prev"]),
        ("Stack", PROFILE["stack"]),
        ("Highlights", PROFILE["highlights"])
    ]

    elements = []

    start_y = 137
    row_spacing = 35

    for index, (label, value) in enumerate(rows):

        y = start_y + index * row_spacing

        safe_label = escape(label)
        safe_value = escape(value)

        if STATIC:

            # Frozen final state
            animation = ""

            opacity = "1"

            transform = "translate(0, 0)"

        else:

            # Animated entrance
            delay = index * ANIMATION_STAGGER

            animation = f"""
            <animate
                attributeName="opacity"
                from="0"
                to="1"
                begin="{delay:.2f}s"
                dur="{ANIMATION_DURATION}s"
                fill="freeze"
            />

            <animateTransform
                attributeName="transform"
                type="translate"
                from="0 10"
                to="0 0"
                begin="{delay:.2f}s"
                dur="{ANIMATION_DURATION}s"
                fill="freeze"
            />
            """

            opacity = "0"
            transform = "translate(0, 10)"

        elements.append(f"""

        <g
            opacity="{opacity}"
            transform="{transform}"
        >

            {animation}

            <!-- Label -->

            <text
                x="24"
                y="{y}"
                font-family="{FONT}"
                font-size="12"
                font-weight="bold"
                fill="{LABEL_COLOR}"
            >{safe_label}</text>

            <!-- Separator -->

            <text
                x="125"
                y="{y}"
                font-family="{FONT}"
                font-size="12"
                fill="{MUTED_COLOR}"
            >:</text>

            <!-- Value -->

            <text
                x="145"
                y="{y}"
                font-family="{FONT}"
                font-size="12"
                fill="{VALUE_COLOR}"
            >{safe_value}</text>

        </g>

        """)

    return "\n".join(elements)


# ==================================================
# FOOTER
# ==================================================

def create_footer():

    return f"""

    <line
        x1="24"
        y1="272"
        x2="496"
        y2="272"
        stroke="{BORDER}"
    />

    <text
        x="24"
        y="290"
        font-family="{FONT}"
        font-size="10"
        fill="{ACCENT_COLOR}"
    >● SYSTEM ONLINE</text>

    <text
        x="496"
        y="290"
        text-anchor="end"
        font-family="{FONT}"
        font-size="10"
        fill="{MUTED_COLOR}"
    >PROFILE.SVG</text>

    """


# ==================================================
# BUILD SVG
# ==================================================

def make_info_card(output_path=OUTPUT_FILE):

    print("\n[1/3] Building terminal interface...")

    parts = [
        svg_header(),
        create_title_bar(),
        create_profile_header()
    ]

    print("[2/3] Generating information rows...")

    parts.append(create_info_rows())

    parts.append(create_footer())

    parts.append("</svg>")

    print("[3/3] Writing SVG file...")

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path.write_text(
        "\n".join(parts),
        encoding="utf-8"
    )

    print("\nInformation card generated!")
    print(f"Output: {output_path.resolve()}")
    print(f"Mode: {'STATIC' if STATIC else 'ANIMATED'}")


# ==================================================
# ENTRY POINT
# ==================================================

if __name__ == "__main__":
    make_info_card()
