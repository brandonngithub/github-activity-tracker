# github-activity-tracker

## Discord avatars

Reports use each person's GitHub profile avatar automatically, so no Discord
usernames or image uploads are required. To use a Discord avatar instead, add
the person's direct image URL to `DISCORD_AVATARS` in `tracker.py`:

```python
DISCORD_AVATARS = {
    "brandonngithub": "https://cdn.discordapp.com/avatars/...",
}
```

The daily report also includes a month-to-date leaderboard showing the top
three contributors. It sends a single horizontal dashboard image so the
account avatars appear side by side.