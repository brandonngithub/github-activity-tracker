
import os
import requests

from datetime import datetime, timedelta, timezone

GITHUB_USERS = [
    "brandonngithub",
    "amarz45",
    "nbkurian11",
    "Harshk10-star",
    "loboa763",
]

# Leave an account out of this mapping to use its GitHub avatar automatically.
# Discord-specific image URLs can be added here later if desired.
DISCORD_AVATARS = {
    "brandonngithub":
        "https://raw.githubusercontent.com/brandonngithub/github-activity-tracker/main/avatars/brandon.png",
    "amarz45":
        "https://raw.githubusercontent.com/brandonngithub/github-activity-tracker/main/avatars/amar.png",
    "nbkurian11":
        "https://raw.githubusercontent.com/brandonngithub/github-activity-tracker/main/avatars/noel.png",
    "Harshk10-star":
        "https://raw.githubusercontent.com/brandonngithub/github-activity-tracker/main/avatars/harsh.png",
    "loboa763":
        "https://raw.githubusercontent.com/brandonngithub/github-activity-tracker/main/avatars/allister.png",
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


def get_monthly_total(username, month_start, target_date):
    if month_start > target_date:
        return 0

    return sum(
        day["contributionCount"]
        for day in get_contribution_days(username, month_start, target_date)
        if month_start.isoformat() <= day["date"] <= target_date.isoformat()
    )


def get_avatar_url(username):
    return DISCORD_AVATARS.get(
        username,
        f"https://github.com/{username}.png?size=128",
    )


def send_discord_report(embeds):

    response = requests.post(
        DISCORD_WEBHOOK,
        json={"embeds": embeds},
        timeout=30,
    )

    response.raise_for_status()


def main():

    # Yesterday according to GitHub's UTC calendar
    yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)
    month_start = yesterday.replace(day=1)

    committed = []
    inactive = []
    monthly_totals = []

    for username in GITHUB_USERS:

        print(f"Checking {username}...")

        count = get_contribution_count(username, yesterday)
        month_total = get_monthly_total(username, month_start, yesterday)

        print(f"{username}: {count} contributions")

        monthly_totals.append((username, month_total))

        if count > 0:
            committed.append((username, count))
        else:
            inactive.append(username)

    embeds = [{
        "title": "GitHub Daily Activity Report",
        "description": f"**Date:** {yesterday.isoformat()}",
        "color": 0x5865F2,
        "fields": [{
            "name": f"✅ Contributions ({len(committed)})",
            "value": (
                "\n".join(
                    f"**{username}** — {count} contribution(s)"
                    for username, count in committed
                )
                if committed else "Nobody had contributions yesterday."
            ),
            "inline": False,
        }, {
            "name": f"❌ No contributions ({len(inactive)})",
            "value": (
                "\n".join(f"**{username}**" for username in inactive)
                if inactive else "Everyone had contributions!"
            ),
            "inline": False,
        }],
    }]

    for username, count in committed:
        embeds.append({
            "author": {
                "name": username,
                "icon_url": get_avatar_url(username),
            },
            "description": f"{count} contribution(s) yesterday",
            "thumbnail": {"url": get_avatar_url(username)},
            "color": 0x57F287,
        })

    leaderboard = sorted(
        monthly_totals, key=lambda entry: entry[1], reverse=True
    )[:3]
    leaderboard_text = "\n".join(
        f"**{position}. {username}** — {count} contribution(s)"
        for position, (username, count) in enumerate(leaderboard, start=1)
    )
    embeds.append({
        "title": f"🏆 Monthly Leaderboard — {month_start.strftime('%B %Y')}",
        "description": leaderboard_text or "No contributions yet this month.",
        "footer": {"text": "Month-to-date totals"},
        "color": 0xFEE75C,
    })

    send_discord_report(embeds)

    print("Discord report sent successfully!")


if __name__ == "__main__":
    main()
