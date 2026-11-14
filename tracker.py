import os
import requests

from datetime import datetime, timedelta, time
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

GITHUB_TOKEN = os.environ["GH_TOKEN"]
DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]

TIMEZONE = ZoneInfo("America/Toronto")

GITHUB_GRAPHQL = "https://api.github.com/graphql"

QUERY = """
query($username: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $username) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
    }
  }
}
"""


def get_commit_count(username, start, end):
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json",
    }

    variables = {
        "username": username,
        "from": start.isoformat(),
        "to": end.isoformat(),
    }

    response = requests.post(
        GITHUB_GRAPHQL,
        headers=headers,
        json={
            "query": QUERY,
            "variables": variables,
        },
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if "errors" in data:
        raise RuntimeError(data["errors"])

    user = data["data"]["user"]

    if user is None:
        raise ValueError(f"GitHub user not found: {username}")

    return user["contributionsCollection"]["totalCommitContributions"]


def send_discord_report(message):
    response = requests.post(
        DISCORD_WEBHOOK,
        json={"content": message},
        timeout=30,
    )

    response.raise_for_status()


def main():
    # Yesterday in Toronto
    today = datetime.now(TIMEZONE).date()
    yesterday = today - timedelta(days=1)

    # Local midnight boundaries, converted to UTC
    start = datetime.combine(
        yesterday, time.min, tzinfo=TIMEZONE
    ).astimezone(ZoneInfo("UTC"))

    end = datetime.combine(
        today, time.min, tzinfo=TIMEZONE
    ).astimezone(ZoneInfo("UTC"))

    committed = []
    inactive = []

    for username in GITHUB_USERS:
        print(f"Checking {username}...")

        count = get_commit_count(username, start, end)

        if count > 0:
            committed.append((username, count))
        else:
            inactive.append(username)

    message = (
        f"## GitHub Daily Activity Report\n"
        f"**Date:** {yesterday.isoformat()}\n\n"
    )

    message += f"### ✅ Commits ({len(committed)})\n"

    if committed:
        for username, count in committed:
            message += f"- **{username}** — {count} commit(s)\n"
    else:
        message += "- No commits yesterday.\n"

    message += f"\n### ❌ No commits ({len(inactive)})\n"

    if inactive:
        for username in inactive:
            message += f"- **{username}**\n"
    else:
        message += "- Everyone committed!\n"

    send_discord_report(message)

    print("Daily report sent successfully!")


if __name__ == "__main__":
    main()
