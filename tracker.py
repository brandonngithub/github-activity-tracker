
import os
import requests

from datetime import datetime, timedelta, timezone

GITHUB_USERS = [
    "brandonngithub",
    "amarz45",
    "nbkurian11",
    "Harshk10-star",
    "TarunK-EE",
    "loboa763",
    "vickenpogosyan",
]

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


def get_contribution_count(username, target_date):

    # GitHub contribution calendar uses UTC dates
    start = datetime(
        target_date.year,
        target_date.month,
        target_date.day,
        tzinfo=timezone.utc
    )

    end = start + timedelta(days=1) - timedelta(seconds=1)

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

    weeks = (
        user["contributionsCollection"]
        ["contributionCalendar"]["weeks"]
    )

    # Find the exact date in the contribution calendar
    for week in weeks:
        for day in week["contributionDays"]:
            if day["date"] == target_date.isoformat():
                return day["contributionCount"]

    # Don't silently treat missing data as zero
    raise RuntimeError(
        f"Date {target_date} missing from {username}'s calendar"
    )


def send_discord_report(message):

    response = requests.post(
        DISCORD_WEBHOOK,
        json={"content": message},
        timeout=30,
    )

    response.raise_for_status()


def main():

    # Yesterday according to GitHub's UTC calendar
    yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)

    committed = []
    inactive = []

    for username in GITHUB_USERS:

        print(f"Checking {username}...")

        count = get_contribution_count(username, yesterday)

        print(f"{username}: {count} contributions")

        if count > 0:
            committed.append((username, count))
        else:
            inactive.append(username)

    message = (
        f"## GitHub Daily Activity Report\n"
        f"**Date:** {yesterday.isoformat()}\n\n"
    )

    message += f"### ✅ Contributions ({len(committed)})\n"

    if committed:
        for username, count in committed:
            message += f"- **{username}** — {count} contribution(s)\n"
    else:
        message += "- Nobody had contributions yesterday.\n"

    message += f"\n### ❌ No contributions ({len(inactive)})\n"

    if inactive:
        for username in inactive:
            message += f"- **{username}**\n"
    else:
        message += "- Everyone had contributions!\n"

    send_discord_report(message)

    print("Discord report sent successfully!")


if __name__ == "__main__":
    main()
