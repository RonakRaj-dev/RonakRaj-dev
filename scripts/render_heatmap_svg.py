
import json
import html
import argparse

from pathlib import Path
from datetime import date, timedelta
from collections import defaultdict


# ==================================================
# CONFIGURATION
# ==================================================

INPUT_FILE = "data/contributions.json"
OUTPUT_FILE = "contrib-heatmap.svg"

WIDTH = 900
HEIGHT = 190

CELL_SIZE = 11
CELL_GAP = 4

GRID_X = 45
GRID_Y = 38

CELL_RADIUS = 3

PALETTE = [
    "#161b22",  # Level 0 - No contributions
    "#0e4429",  # Level 1
    "#006d32",  # Level 2
    "#26a641",  # Level 3
    "#39d353",  # Level 4
    "#69f0a0"   # Level 5 - Neon top end
]

BACKGROUND = "#0d1117"
TEXT_COLOR = "#c9d1d9"
MUTED_COLOR = "#8b949e"

# Animation
ANIMATION_DURATION = 0.45
ANIMATION_STAGGER = 0.025

STATIC = False


# ==================================================
# 1. LOAD CONTRIBUTION JSON
# ==================================================

def load_contributions(input_file):

    path = Path(input_file)

    if not path.exists():
        raise FileNotFoundError(
            f"Contribution data not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if "days" not in data:
        raise ValueError(
            "Invalid contributions JSON: missing days."
        )

    return data


# ==================================================
# 2. PREPARE CALENDAR DATA
# ==================================================

def prepare_calendar(days):

    """
    Convert daily contribution records into
    a 53-week x 7-day calendar.

    Monday = 0
    Sunday = 6
    """

    contribution_map = {}

    for item in days:

        current_date = date.fromisoformat(
            item["date"]
        )

        count = int(item["count"])
        level = int(item["level"])

        if count < 0:
            raise ValueError("Contribution count cannot be negative.")

        if not 0 <= level <= 5:
            raise ValueError(
                f"Invalid contribution level: {level}"
            )

        contribution_map[current_date] = {
            "count": count,
            "level": level
        }

    if not contribution_map:
        raise ValueError("No contribution records found.")

    first_date = min(contribution_map)
    last_date = max(contribution_map)

    # Align first date to Monday.
    calendar_start = (
        first_date
        - timedelta(days=first_date.weekday())
    )

    # Align last date to Sunday.
    calendar_end = (
        last_date
        + timedelta(days=6 - last_date.weekday())
    )

    # Fixed 53-week layout.
    total_weeks = 53

    calendar = []

    for week in range(total_weeks):

        week_data = []

        for weekday in range(7):

            current_date = (
                calendar_start
                + timedelta(
                    days=week * 7 + weekday
                )
            )

            record = contribution_map.get(
                current_date
            )

            if record is None:
                # Dates outside the fetched range
                # remain visually empty.
                record = {
                    "count": 0,
                    "level": 0
                }

            week_data.append({
                "date": current_date.isoformat(),
                "count": record["count"],
                "level": record["level"],
                "weekday": weekday,
                "week": week
            })

        calendar.append(week_data)

    return calendar, calendar_start, first_date, last_date


# ==================================================
# 3. SVG HEADER
# ==================================================

def create_svg_header():

    return f"""<?xml version="1.0" encoding="UTF-8"?>

<svg
    xmlns="http://www.w3.org/2000/svg"
    width="{WIDTH}"
    height="{HEIGHT}"
    viewBox="0 0 {WIDTH} {HEIGHT}"
    role="img"
    aria-label="GitHub contribution heatmap"
>

<title>GitHub Contribution Activity</title>

<rect
    width="100%"
    height="100%"
    rx="8"
    fill="{BACKGROUND}"
/>

"""


# ==================================================
# 4. MONTH LABELS
# ==================================================

def create_month_labels(calendar_start, first_date, last_date):

    labels = []

    current_date = calendar_start

    for week in range(53):

        week_date = (
            calendar_start
            + timedelta(days=week * 7)
        )

        # Label the first visible week of each month.
        if week_date.day <= 7:

            if first_date <= week_date <= last_date:

                x = (
                    GRID_X
                    + week * (CELL_SIZE + CELL_GAP)
                )

                month_name = week_date.strftime("%b")

                labels.append(f"""
                <text
                    x="{x}"
                    y="20"
                    font-size="11"
                    font-family="Arial, sans-serif"
                    fill="{MUTED_COLOR}"
                >{month_name}</text>
                """)

    return "\n".join(labels)


# ==================================================
# 5. WEEKDAY LABELS
# ==================================================

def create_weekday_labels():

    labels = []

    weekday_names = {
        0: "Mon",
        2: "Wed",
        4: "Fri"
    }

    for weekday, name in weekday_names.items():

        y = (
            GRID_Y
            + weekday * (CELL_SIZE + CELL_GAP)
            + CELL_SIZE - 1
        )

        labels.append(f"""
        <text
            x="8"
            y="{y}"
            font-size="10"
            font-family="Arial, sans-serif"
            fill="{MUTED_COLOR}"
        >{name}</text>
        """)

    return "\n".join(labels)


# ==================================================
# 6. CONTRIBUTION CELLS
# ==================================================

def create_cells(calendar):

    elements = []

    for week_index, week in enumerate(calendar):

        for day in week:

            weekday = day["weekday"]
            level = day["level"]

            x = (
                GRID_X
                + week_index * (CELL_SIZE + CELL_GAP)
            )

            y = (
                GRID_Y
                + weekday * (CELL_SIZE + CELL_GAP)
            )

            fill = PALETTE[level]

            tooltip = (
                f"{day['count']} contributions on "
                f"{day['date']}"
            )

            elements.append(f"""
            <rect
                x="{x}"
                y="{y}"
                width="{CELL_SIZE}"
                height="{CELL_SIZE}"
                rx="{CELL_RADIUS}"
                fill="{fill}"
                stroke="{BACKGROUND}"
                stroke-width="0.5"
            >
                <title>{html.escape(tooltip)}</title>
            </rect>
            """)

    return "\n".join(elements)


# ==================================================
# 7. ANIMATION
# ==================================================

def create_animated_grid(calendar):

    elements = []

    for week_index, week in enumerate(calendar):

        delay = week_index * ANIMATION_STAGGER

        if STATIC:

            animation = ""

            opacity = "1"

            transform = "translate(0, 0)"

        else:

            animation = f"""
            <animate
                attributeName="opacity"
                from="0"
                to="1"
                begin="{delay:.3f}s"
                dur="{ANIMATION_DURATION}s"
                fill="freeze"
            />

            <animateTransform
                attributeName="transform"
                type="translate"
                from="0 -8"
                to="0 0"
                begin="{delay:.3f}s"
                dur="{ANIMATION_DURATION}s"
                fill="freeze"
            />
            """

            opacity = "0"

            transform = "translate(0, -8)"

        week_elements = []

        for day in week:

            weekday = day["weekday"]
            level = day["level"]

            x = (
                GRID_X
                + week_index * (CELL_SIZE + CELL_GAP)
            )

            y = (
                GRID_Y
                + weekday * (CELL_SIZE + CELL_GAP)
            )

            fill = PALETTE[level]

            tooltip = (
                f"{day['count']} contributions on "
                f"{day['date']}"
            )

            week_elements.append(f"""
            <rect
                x="{x}"
                y="{y}"
                width="{CELL_SIZE}"
                height="{CELL_SIZE}"
                rx="{CELL_RADIUS}"
                fill="{fill}"
                stroke="{BACKGROUND}"
                stroke-width="0.5"
            >
                <title>{html.escape(tooltip)}</title>
            </rect>
            """)

        elements.append(f"""
        <g
            opacity="{opacity}"
            transform="{transform}"
        >

            {animation}

            {''.join(week_elements)}

        </g>
        """)

    return "\n".join(elements)


# ==================================================
# 8. LESS -> MORE LEGEND
# ==================================================

def create_legend():

    elements = []

    legend_x = 700
    legend_y = 145

    elements.append(f"""
    <text
        x="{legend_x}"
        y="{legend_y + 10}"
        font-size="10"
        font-family="Arial, sans-serif"
        fill="{MUTED_COLOR}"
    >Less</text>
    """)

    for index, color in enumerate(PALETTE):

        x = legend_x + 34 + index * 17

        elements.append(f"""
        <rect
            x="{x}"
            y="{legend_y}"
            width="12"
            height="12"
            rx="3"
            fill="{color}"
        />
        """)

    elements.append(f"""
    <text
        x="{legend_x + 34 + len(PALETTE) * 17}"
        y="{legend_y + 10}"
        font-size="10"
        font-family="Arial, sans-serif"
        fill="{MUTED_COLOR}"
    >More</text>
    """)

    return "\n".join(elements)


# ==================================================
# 9. STATISTICS FOOTER
# ==================================================

def create_stats_footer(data):

    stats = data["stats"]

    total = int(
        stats.get("total_contributions", 0)
    )

    username = html.escape(
        data.get("username", "GitHub User")
    )

    footer_text = (
        f"{total:,} contributions in the last year"
    )

    return f"""
    <text
        x="{GRID_X}"
        y="160"
        font-size="12"
        font-family="Arial, sans-serif"
        fill="{TEXT_COLOR}"
    >{html.escape(footer_text)}</text>

    <text
        x="{GRID_X}"
        y="178"
        font-size="9"
        font-family="Arial, sans-serif"
        fill="{MUTED_COLOR}"
    >@{username}</text>
    """


# ==================================================
# 10. BUILD FINAL SVG
# ==================================================

def render_heatmap(input_file, output_file):

    print("\n[1/5] Loading contribution data...")

    data = load_contributions(input_file)

    print("[2/5] Preparing 53-week calendar...")

    calendar, calendar_start, first_date, last_date = (
        prepare_calendar(data["days"])
    )

    print("[3/5] Rendering contribution cells...")

    svg_parts = [
        create_svg_header(),

        create_month_labels(
            calendar_start,
            first_date,
            last_date
        ),

        create_weekday_labels(),

        create_animated_grid(calendar),

        create_legend(),

        create_stats_footer(data),

        "</svg>"
    ]

    print("[4/5] Combining SVG elements...")

    svg_content = "\n".join(svg_parts)

    print("[5/5] Saving contribution heatmap...")

    output_path = Path(output_file)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path.write_text(
        svg_content,
        encoding="utf-8"
    )

    print("\n========== HEATMAP GENERATED ==========")

    print(f"Output: {output_path.resolve()}")

    print(f"Grid: 53 weeks x 7 days")

    print(f"Date range: {first_date} to {last_date}")

    print(
        f"Total contributions: "
        f"{data['stats']['total_contributions']:,}"
    )

    print(f"Mode: {'STATIC' if STATIC else 'ANIMATED'}")

    print("=======================================")


# ==================================================
# ENTRY POINT
# ==================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Render GitHub contribution heatmap."
    )

    parser.add_argument(
        "--input",
        default=INPUT_FILE
    )

    parser.add_argument(
        "--output",
        default=OUTPUT_FILE
    )

    parser.add_argument(
        "--static",
        action="store_true",
        help="Generate a static SVG without animations."
    )

    args = parser.parse_args()

    STATIC = (
        args.static
        or __import__("os").getenv("STATIC", "0") == "1"
    )

    render_heatmap(
        args.input,
        args.output
    )
