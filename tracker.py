
import os
import json
import tempfile
import requests

from datetime import datetime, timedelta, timezone
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont, ImageOps

GITHUB_USERS = [
    "brandonngithub",
    "nbkurian11",
    "Harshk10-star",
    "TarunK-EE",
    "amarz45",
    "loboa763",
    "vickenpogosyan",
    "harito-git"
]

DISCORD_NAMES = {
    "brandonngithub": "7brv",
    "nbkurian11": "youngneezy",
    "Harshk10-star": "_harsh_0052",
    "TarunK-EE": "freeddawg",
    "amarz45": "amaral455",
    "loboa763": "rllymyself",
    "vickenpogosyan": "vic2slick_",
    "harito-git": ".curryyt"
}

DISCORD_AVATARS = {
    "brandonngithub":
        "https://raw.githubusercontent.com/brandonngithub/github-activity-tracker/main/avatars/brandon.png",
    "nbkurian11":
        "https://raw.githubusercontent.com/brandonngithub/github-activity-tracker/main/avatars/noel.png",
    "Harshk10-star":
        "https://raw.githubusercontent.com/brandonngithub/github-activity-tracker/main/avatars/harsh.png",
    "TarunK-EE":
        "https://raw.githubusercontent.com/brandonngithub/github-activity-tracker/main/avatars/tarun.png",
    "amarz45":
        "https://raw.githubusercontent.com/brandonngithub/github-activity-tracker/main/avatars/amar.png",
    "loboa763":
        "https://raw.githubusercontent.com/brandonngithub/github-activity-tracker/main/avatars/allister.png",
    "vickenpogosyan":
        "https://raw.githubusercontent.com/brandonngithub/github-activity-tracker/main/avatars/vicken.png",
    "harito-git":
        "https://raw.githubusercontent.com/brandonngithub/github-activity-tracker/main/avatars/harit.png"
}

GITHUB_TOKEN = os.environ["GH_TOKEN"]
DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]

GITHUB_API = "https://api.github.com/graphql"

QUERY = """
query($username: String!, $from: DateTime!, $to: DateTime!) {
    user(login: $username) {
        contributionsCollection(from: $from, to: $to) {
            contributionCalendar {
                weeks {
                    contributionDays {
                        date
                        contributionCount
                    }
                }
            }
        }
    }
}
"""


def get_contribution_days(username, start_date, end_date):
    start = datetime(
        start_date.year, start_date.month, start_date.day, tzinfo=timezone.utc
    )
    end = datetime(
        end_date.year, end_date.month, end_date.day, 23, 59, 59,
        tzinfo=timezone.utc,
    )
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    variables = {
        "username": username,
        "from": start.isoformat(),
        "to": end.isoformat(),
    }

    response = requests.post(
        GITHUB_API,
        headers=headers,
        json={
            "query": QUERY,
            "variables": variables,
        },
        timeout=30,
    )

    response.raise_for_status()

    result = response.json()

    if "errors" in result:
        raise RuntimeError(result["errors"])

    user = result["data"]["user"]

    if user is None:
        raise ValueError(f"User not found: {username}")

    return [
        day
        for week in user["contributionsCollection"]["contributionCalendar"]["weeks"]
        for day in week["contributionDays"]
    ]


def get_contribution_count(username, target_date):
    days = get_contribution_days(username, target_date, target_date)

    for day in days:
        if day["date"] == target_date.isoformat():
            return day["contributionCount"]

    raise RuntimeError(f"Date {target_date} missing from {username}'s calendar")


def get_monthly_active_days(username, month_start, target_date):
    if month_start > target_date:
        return 0

    return sum(
        day["contributionCount"] > 0
        for day in get_contribution_days(username, month_start, target_date)
        if month_start.isoformat() <= day["date"] <= target_date.isoformat()
    )


def get_streak(username, target_date):
    start_date = target_date - timedelta(days=365)
    days = {
        day["date"]: day["contributionCount"]
        for day in get_contribution_days(username, start_date, target_date)
    }
    streak = 0
    current_date = target_date

    while days.get(current_date.isoformat(), 0) > 0:
        streak += 1
        current_date -= timedelta(days=1)

    return streak


def get_avatar_url(username):
    return DISCORD_AVATARS.get(
        username,
        f"https://github.com/{username}.png?size=128",
    )


def get_display_name(username):
    return DISCORD_NAMES.get(username, username)


def format_report_date(report_date):
    day = report_date.day
    if 10 < day % 100 < 14:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

    return f"{report_date.strftime('%A %B')} {day}{suffix}"


def format_active_days(active_days):
    if active_days == 1:
        return "1 day active"
    return f"{active_days} days active"


def load_avatar(username):
    response = requests.get(get_avatar_url(username), timeout=30)
    response.raise_for_status()

    try:
        return Image.open(BytesIO(response.content)).convert("RGB")
    except Exception as error:
        raise RuntimeError(f"Unable to decode avatar for {username}") from error


def get_font(size, bold=False):
    font_name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    font_paths = [
        f"/usr/share/fonts/truetype/dejavu/{font_name}",
        f"/Library/Fonts/{font_name}",
    ]

    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


def draw_fire_icon(draw, x, y, size=18):
    draw.polygon(
        [
            (x + size * 0.52, y),
            (x + size * 0.82, y + size * 0.42),
            (x + size * 0.72, y + size),
            (x + size * 0.25, y + size),
            (x + size * 0.08, y + size * 0.62),
            (x + size * 0.35, y + size * 0.46),
        ],
        fill="#ff6b35",
    )
    draw.polygon(
        [
            (x + size * 0.53, y + size * 0.38),
            (x + size * 0.68, y + size * 0.7),
            (x + size * 0.58, y + size),
            (x + size * 0.35, y + size * 0.88),
            (x + size * 0.4, y + size * 0.62),
        ],
        fill="#ffd166",
    )


def create_activity_dashboard(activity, output_path):
    card_width = 180
    card_height = 230
    gap = 14
    padding = 24
    image = Image.new(
        "RGB",
        (
            padding * 2 + len(activity) * card_width + (len(activity) - 1) * gap,
            padding * 2 + card_height,
        ),
        "#17181c",
    )
    draw = ImageDraw.Draw(image)

    for index, (username, streak) in enumerate(activity):
        x = padding + index * (card_width + gap)
        y = padding
        draw.rounded_rectangle(
            (x, y, x + card_width, y + card_height),
            radius=16,
            fill="#23252b",
            outline="#3d414b",
            width=2,
        )

        display_name = get_display_name(username)
        username_font = get_font(15, bold=True)
        username_width = draw.textbbox(
            (0, 0), display_name, font=username_font
        )[2]
        draw.text(
            (x + (card_width - username_width) // 2, y + 14),
            display_name,
            fill="#f2f3f5",
            font=username_font,
        )

        avatar = ImageOps.fit(
            load_avatar(username),
            (92, 92),
            method=Image.Resampling.LANCZOS,
        )
        mask = Image.new("L", avatar.size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0, *avatar.size), fill=255)
        image.paste(avatar, (x + (card_width - 92) // 2, y + 42), mask)

        draw.text(
            (x + 42, y + 158),
            f"{streak} day streak",
            fill="#57f287",
            font=get_font(15, bold=True),
        )
        draw_fire_icon(draw, x + 18, y + 158, size=18)

    image.save(output_path, format="PNG")


def send_discord_report(embeds, image_path):
    response = requests.post(
        DISCORD_WEBHOOK,
        json={"embeds": embeds},
        timeout=30,
    )
    response.raise_for_status()

    with open(image_path, "rb") as image_file:
        follow_up_response = requests.post(
            DISCORD_WEBHOOK,
            data={"payload_json": json.dumps({})},
            files={
                "file": ("daily-activity.png", image_file, "image/png"),
            },
            timeout=30,
        )
    follow_up_response.raise_for_status()


def main():
    yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)
    month_start = yesterday.replace(day=1)

    committed = []
    inactive = []
    daily_totals = []
    monthly_active_days = []

    for username in GITHUB_USERS:

        print(f"Checking {username}...")

        count = get_contribution_count(username, yesterday)
        month_active_days = get_monthly_active_days(
            username, month_start, yesterday
        )

        print(f"{username}: {count} contributions")

        monthly_active_days.append((username, month_active_days))

        if count > 0:
            streak = get_streak(username, yesterday)
            committed.append((username, streak))
            daily_totals.append((username, streak))
        else:
            inactive.append(username)

    leaderboard = sorted(
        monthly_active_days, key=lambda entry: entry[1], reverse=True
    )[:5]
    leaderboard_text = "\n".join(
        f"{position}. **{get_display_name(username)}** — "
        f"{format_active_days(active_days)}"
        for position, (username, active_days) in enumerate(leaderboard, start=1)
    )
    leaderboard_embed = {
        "title": (
            f"🏆 Monthly Leaderboard — {month_start.strftime('%B %Y')}"
        ),
        "description": leaderboard_text or "No contributions yet this month.",
        "color": 0xFEE75C,
    }

    daily_embed = {
        "title": format_report_date(yesterday),
        "color": 0x5865F2,
        "fields": [{
            "name": f"✅ Contributions ({len(committed)})",
            "value": (
                "\n".join(
                    get_display_name(username)
                    for username, _ in committed
                )
                if committed else "Nobody had contributions yesterday."
            ),
            "inline": False,
        }, {
            "name": f"❌ No contributions ({len(inactive)})",
            "value": (
                "\n".join(
                    get_display_name(username)
                    for username in inactive
                )
                if inactive else "Everyone had contributions!"
            ),
            "inline": False,
        }],
    }

    with tempfile.NamedTemporaryFile(suffix=".png") as image_file:
        create_activity_dashboard(
            daily_totals,
            image_file.name,
        )
        send_discord_report(
            [leaderboard_embed, daily_embed],
            image_file.name,
        )

    print("Discord report sent successfully!")


if __name__ == "__main__":
    main()
