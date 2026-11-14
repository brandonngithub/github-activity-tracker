
import os
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# GitHub accounts to monitor
GITHUB_USERS = [
    "brandonngithub",
    "nbkurian11",
    "Harshk10-star",
    "TarunK-EE",
    "amarz45",
    "loboa763",
    "vickenpogosyan"
]

# Discord webhook URL (stored securely in GitHub)
DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]

# GitHub API token
GITHUB_TOKEN = os.environ["GH_TOKEN"]

# Use Toronto local time
TIMEZONE = ZoneInfo("America/Toronto")

GITHUB_API = "https://api.github.com/search/commits"


def get_commits(username, date):
    """Find public commits authored by a GitHub account."""

    query = (
        f"author:{username} "
        f"committer-date:{date} "
        f"is:public"
    )

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    response = requests.get(
        GITHUB_API,
        headers=headers,
        params={
            "q": query,
            "per_page": 100,
            "page": 1,
        },
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()

    return data["total_count"]


def main():
    # Check the previous local calendar day
    today = datetime.now(TIMEZONE).date()
    yesterday = today - timedelta(days=1)
    report_date = yesterday.isoformat()

    committed = []
    not_committed = []

    for username in GITHUB_USERS:
        print(f"Checking {username}...")

        count = get_commits(username, report_date)

        if count > 0:
            committed.append((username, count))
        else:
            not_committed.append(username)

    # Build Discord message
    message = f"## GitHub Activity Report\n"
    message += f"**Date:** {report_date}\n\n"

    message += f"### ✅ Committed ({len(committed)})\n"

    if committed:
        for username, count in committed:
            message += f"- **@{username}** — {count} commit(s)\n"
    else:
        message += "- Nobody committed yesterday.\n"

    message += f"\n### ❌ No commits ({len(not_committed)})\n"

    if not_committed:
        for username in not_committed:
            message += f"- **@{username}**\n"
    else:
        message += "- Everyone committed yesterday!\n"

    # Send report to Discord
    response = requests.post(
        DISCORD_WEBHOOK,
        json={"content": message},
        timeout=30,
    )

    response.raise_for_status()

    print("Discord report sent successfully!")


if __name__ == "__main__":
    main()
