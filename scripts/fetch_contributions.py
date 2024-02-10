"""
fetch_contributions.py — Fetch GitHub contribution calendar via GraphQL API.
Requires GITHUB_TOKEN env var (set as a GitHub Actions secret or locally).
Saves contribution data and streak metrics to data/contributions.json.
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import requests

USERNAME = "wajahatabbsalvi"
GRAPHQL_URL = "https://api.github.com/graphql"


# ---------------------------------------------------------------------------
# GraphQL fetch (requires token)
# ---------------------------------------------------------------------------

QUERY = """
query($username: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $username) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
            contributionLevel
          }
        }
      }
    }
  }
}
"""

LEVEL_MAP = {
    "NONE": 0,
    "FIRST_QUARTILE": 1,
    "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3,
    "FOURTH_QUARTILE": 4,
}


def fetch_via_graphql(token: str) -> list[dict]:
    """Fetch full contribution data using GitHub GraphQL API."""
    # Fetch a rolling 12-month window (GitHub limit: must not exceed 1 year)
    now = datetime.utcnow()
    from_dt = (now - timedelta(days=364)).strftime("%Y-%m-%dT00:00:00Z")
    to_dt = now.strftime("%Y-%m-%dT23:59:59Z")

    headers = {
        "Authorization": f"bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "query": QUERY,
        "variables": {
            "username": USERNAME,
            "from": from_dt,
            "to": to_dt,
        },
    }

    print(f"🔗 Querying GitHub GraphQL API for @{USERNAME} …")
    resp = requests.post(GRAPHQL_URL, json=payload, headers=headers, timeout=20)
    resp.raise_for_status()

    body = resp.json()
    if "errors" in body:
        raise RuntimeError(f"GraphQL errors: {body['errors']}")

    weeks = (
        body["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    )

    days = []
    for week in weeks:
        for day in week["contributionDays"]:
            days.append(
                {
                    "date": day["date"],
                    "count": day["contributionCount"],
                    "level": LEVEL_MAP.get(day["contributionLevel"], 0),
                }
            )

    days.sort(key=lambda d: d["date"])
    return days


# ---------------------------------------------------------------------------
# HTML scrape fallback (level only, count always 0 — GitHub changed their HTML)
# ---------------------------------------------------------------------------

def fetch_via_html() -> list[dict]:
    """Scrape GitHub contribution calendar HTML (level only, no counts)."""
    from bs4 import BeautifulSoup

    url = f"https://github.com/users/{USERNAME}/contributions"
    print(f"⚠️  No GITHUB_TOKEN — falling back to HTML scrape: {url}")
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    days = []
    for td in soup.select("td.ContributionCalendar-day"):
        date = td.get("data-date")
        level = int(td.get("data-level", "0"))
        count = 0
        tip = td.find("tool-tip") or td.find("span", class_="sr-only")
        if tip:
            m = re.search(r"(\d+)\s+contribution", tip.get_text(strip=True))
            if m:
                count = int(m.group(1))
        if date:
            days.append({"date": date, "count": count, "level": level})

    days.sort(key=lambda d: d["date"])
    return days


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def calc_metrics(days: list[dict]) -> dict:
    """Calculate total contributions, current streak, longest streak, best day."""
    # Prefer count; fall back to treating any level > 0 as count=1 for streak calcs
    def had_contribution(day):
        return day["count"] > 0 or day["level"] > 0

    total = sum(d["count"] for d in days)

    best_day = max(days, key=lambda d: d["count"]) if days else {"date": "N/A", "count": 0}

    date_map = {d["date"]: d for d in days}

    # Current streak — walk back from today
    current_streak = 0
    d = datetime.utcnow()
    while True:
        ds = d.strftime("%Y-%m-%d")
        if ds in date_map and had_contribution(date_map[ds]):
            current_streak += 1
            d -= timedelta(days=1)
        else:
            # Allow a one-day grace (today might not be done yet)
            if current_streak == 0:
                d -= timedelta(days=1)
                ds2 = d.strftime("%Y-%m-%d")
                if ds2 in date_map and had_contribution(date_map[ds2]):
                    current_streak += 1
                    d -= timedelta(days=1)
                    continue
            break

    # Longest streak
    longest_streak = 0
    streak = 0
    for day in days:
        if had_contribution(day):
            streak += 1
            longest_streak = max(longest_streak, streak)
        else:
            streak = 0

    return {
        "total_contributions": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day["date"],
        "best_day_count": best_day["count"],
        "last_updated": datetime.utcnow().isoformat() + "Z",
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    root = Path(__file__).resolve().parent.parent
    data_dir = root / "data"
    data_dir.mkdir(exist_ok=True)

    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        days = fetch_via_graphql(token)
    else:
        days = fetch_via_html()

    print(f"📅 Found {len(days)} days of contribution data.")

    metrics = calc_metrics(days)
    print(
        f"🔥 Total: {metrics['total_contributions']} | "
        f"Current Streak: {metrics['current_streak']} | "
        f"Longest Streak: {metrics['longest_streak']} | "
        f"Best Day: {metrics['best_day']} ({metrics['best_day_count']})"
    )

    output = {"username": USERNAME, "metrics": metrics, "days": days}
    out_path = data_dir / "contributions.json"
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"✅ Saved {out_path}")


if __name__ == "__main__":
    main()
