
import os
import re
import json
import argparse
import requests

from bs4 import BeautifulSoup
from pathlib import Path
from datetime import date, datetime, timedelta, timezone
from collections import defaultdict


# ==================================================
# CONFIGURATION
# ==================================================

USERNAME = os.getenv(
    "GITHUB_USERNAME",
    "YOUR_GITHUB_USERNAME"
)

OUTPUT_FILE = "data/contributions.json"

GITHUB_URL = "https://github.com/users/{username}/contributions"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; GitHubContributionFetcher/1.0)",
    "Accept": "text/html"
}

TIMEOUT = 30


# ==================================================
# 1. FETCH CONTRIBUTION HTML
# ==================================================

def fetch_html(username):

    url = GITHUB_URL.format(username=username)

    print(f"\nFetching contributions for: {username}")
    print(f"Source: {url}")

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=TIMEOUT
    )

    response.raise_for_status()

    if "text/html" not in response.headers.get(
        "Content-Type", ""
    ).lower():
        raise RuntimeError(
            "GitHub did not return an HTML response."
        )

    return response.text


# ==================================================
# 2. EXTRACT CONTRIBUTION COUNT
# ==================================================

def extract_count(text):

    """
    Extract exact contribution count from tooltip text.

    Examples:
        12 contributions on January 1st.
        No contributions on January 1st.
        1 contribution on January 1st.
    """

    if not text:
        return None

    text = " ".join(text.split())

    match = re.search(
        r"([\d,]+)\s+contributions?\b",
        text,
        re.IGNORECASE
    )

    if match:
        return int(match.group(1).replace(",", ""))

    if re.search(
        r"\bno contributions\b",
        text,
        re.IGNORECASE
    ):
        return 0

    return None


# ==================================================
# 3. PARSE CONTRIBUTION DAYS
# ==================================================

def parse_contributions(html):

    soup = BeautifulSoup(html, "html.parser")

    days = []

    # Map tooltip IDs to their text.
    tooltip_map = {}

    for tooltip in soup.find_all("tool-tip"):

        tooltip_id = tooltip.get("for")

        if tooltip_id:
            tooltip_map[tooltip_id] = tooltip.get_text(
                " ",
                strip=True
            )

    # GitHub contribution calendar cells.
    cells = soup.select(
        "td.ContributionCalendar-day[data-date], "
        "td[data-date][data-level], "
        "rect[data-date][data-level]"
    )

    # Avoid duplicate elements from overlapping selectors.
    seen_dates = set()

    for cell in cells:

        contribution_date = cell.get("data-date")
        level = cell.get("data-level")

        if not contribution_date or level is None:
            continue

        try:
            parsed_date = date.fromisoformat(
                contribution_date
            )

            level = int(level)

        except (ValueError, TypeError):
            continue

        if not 0 <= level <= 4:
            continue

        if contribution_date in seen_dates:
            continue

        seen_dates.add(contribution_date)

        # First try direct data-count.
        count = None

        direct_count = cell.get("data-count")

        if direct_count is not None:

            try:
                count = int(direct_count)
            except ValueError:
                pass

        # Try aria-label if data-count is unavailable.
        if count is None:
            count = extract_count(
                cell.get("aria-label", "")
            )

        # Try linked tooltip.
        if count is None:

            cell_id = cell.get("id")

            if cell_id:
                tooltip_text = tooltip_map.get(
                    cell_id,
                    ""
                )

                count = extract_count(tooltip_text)

        # A zero-level day is known to have zero contributions.
        if count is None and level == 0:
            count = 0

        # Do not silently treat an unknown count as zero.
        if count is None:
            raise RuntimeError(
                f"Could not extract exact contribution count "
                f"for {contribution_date}. "
                "GitHub may have changed its HTML markup."
            )

        if count < 0:
            raise RuntimeError(
                f"Invalid contribution count for {contribution_date}"
            )

        days.append({
            "date": parsed_date.isoformat(),
            "count": count,
            "level": level
        })

    if not days:
        raise RuntimeError(
            "No contribution days found. "
            "GitHub's HTML structure may have changed."
        )

    # Sort chronologically.
    days.sort(key=lambda item: item["date"])

    return days


# ==================================================
# 4. CALCULATE CURRENT STREAK
# ==================================================

def calculate_current_streak(days):

    """
    Calculate consecutive active days ending today.

    If today's count is zero, allow today to be
    skipped because the day is not finished.
    """

    if not days:
        return 0

    counts = {
        date.fromisoformat(item["date"]): item["count"]
        for item in days
    }

    today = date.today()

    # If today's contribution count is zero,
    # start checking from yesterday.
    if counts.get(today) == 0:
        current_day = today - timedelta(days=1)
    else:
        current_day = today

    streak = 0

    while current_day in counts:

        if counts[current_day] <= 0:
            break

        streak += 1

        current_day -= timedelta(days=1)

    return streak


# ==================================================
# 5. CALCULATE LONGEST STREAK
# ==================================================

def calculate_longest_streak(days):

    longest = 0
    current = 0

    previous_date = None

    for item in days:

        current_date = date.fromisoformat(
            item["date"]
        )

        count = item["count"]

        if count > 0:

            if (
                previous_date is not None
                and current_date - previous_date == timedelta(days=1)
            ):
                current += 1

            else:
                current = 1

            longest = max(longest, current)

            previous_date = current_date

        else:

            current = 0
            previous_date = None

    return longest


# ==================================================
# 6. FIND BEST CONTRIBUTION DAY
# ==================================================

def calculate_best_day(days):

    if not days:
        return None

    best = max(
        days,
        key=lambda item: item["count"]
    )

    if best["count"] == 0:
        return None

    return best


# ==================================================
# 7. MONTHLY CONTRIBUTION TOTALS
# ==================================================

def calculate_monthly_totals(days):

    monthly = defaultdict(int)

    for item in days:

        month = item["date"][:7]

        monthly[month] += item["count"]

    return dict(sorted(monthly.items()))


# ==================================================
# 8. DERIVE STATISTICS
# ==================================================

def calculate_statistics(days):

    total = sum(
        item["count"]
        for item in days
    )

    active_days = sum(
        1 for item in days
        if item["count"] > 0
    )

    return {
        "total_contributions": total,

        "active_days": active_days,

        "current_streak": calculate_current_streak(
            days
        ),

        "longest_streak": calculate_longest_streak(
            days
        ),

        "best_day": calculate_best_day(
            days
        ),

        "monthly_totals": calculate_monthly_totals(
            days
        )
    }


# ==================================================
# 9. SAVE JSON
# ==================================================

def save_json(data, output_file):

    output_path = Path(output_file)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with output_path.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(f"\nJSON saved: {output_path.resolve()}")


# ==================================================
# 10. MAIN PIPELINE
# ==================================================

def fetch_contributions(username, output_file):

    if not username or username == "YOUR_GITHUB_USERNAME":
        raise ValueError(
            "Configure your actual GitHub username "
            "using GITHUB_USERNAME or --username."
        )

    print("\n[1/5] Fetching GitHub contribution HTML...")

    html = fetch_html(username)

    print("[2/5] Parsing contribution calendar...")

    days = parse_contributions(html)

    print(f"      Found {len(days)} contribution days.")

    print("[3/5] Calculating contribution statistics...")

    stats = calculate_statistics(days)

    print("[4/5] Building JSON dataset...")

    result = {
        "username": username,

        "source": GITHUB_URL.format(
            username=username
        ),

        "fetched_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "date_range": {
            "from": days[0]["date"],
            "to": days[-1]["date"]
        },

        "stats": stats,

        "days": days
    }

    print("[5/5] Saving contributions.json...")

    save_json(
        result,
        output_file
    )

    print("\n========== CONTRIBUTION SUMMARY ==========")

    print(f"Username: {username}")

    print(f"Total contributions: {stats['total_contributions']}")

    print(f"Active days: {stats['active_days']}")

    print(f"Current streak: {stats['current_streak']} days")

    print(f"Longest streak: {stats['longest_streak']} days")

    print(f"Best day: {stats['best_day']}")

    print("===========================================")

    return result


# ==================================================
# ENTRY POINT
# ==================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Fetch public GitHub contribution statistics."
    )

    parser.add_argument(
        "--username",
        default=USERNAME,
        help="GitHub username"
    )

    parser.add_argument(
        "--output",
        default=OUTPUT_FILE,
        help="Output JSON path"
    )

    args = parser.parse_args()

    fetch_contributions(
        args.username,
        args.output
    )
