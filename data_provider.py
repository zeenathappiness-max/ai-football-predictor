import requests
import pandas as pd

def load_demo_fixtures():
    # Fictional examples for UI testing only; not real scheduled matches.
    return pd.DataFrame([
        {"league": "Demo League", "home_team": "Example FC", "away_team": "Sample United",
         "kickoff_utc": "2026-10-15T15:00:00Z", "home_avg_scored": 1.8,
         "home_avg_conceded": 0.9, "away_avg_scored": 1.2, "away_avg_conceded": 1.5},
        {"league": "Demo League", "home_team": "North Example", "away_team": "South Sample",
         "kickoff_utc": "2026-10-15T18:30:00Z", "home_avg_scored": 1.4,
         "home_avg_conceded": 1.2, "away_avg_scored": 1.3, "away_avg_conceded": 1.4},
        {"league": "Demo Cup", "home_team": "Demo Athletic", "away_team": "Demo Rovers",
         "kickoff_utc": "2026-10-15T20:00:00Z", "home_avg_scored": 2.0,
         "home_avg_conceded": 1.1, "away_avg_scored": 0.9, "away_avg_conceded": 1.6},
    ])

def load_api_football_fixtures(api_key, date=None):
    """Load fixtures from API-Football v3. Add historical-stat integration in a later version."""
    from datetime import date as date_cls
    match_date = date or date_cls.today().isoformat()
    response = requests.get(
        "https://v3.football.api-sports.io/fixtures",
        headers={"x-apisports-key": api_key},
        params={"date": match_date, "timezone": "UTC"},
        timeout=25,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("errors"):
        raise RuntimeError(str(payload["errors"]))
    rows = []
    for item in payload.get("response", []):
        rows.append({
            "league": item["league"]["name"],
            "home_team": item["teams"]["home"]["name"],
            "away_team": item["teams"]["away"]["name"],
            "kickoff_utc": item["fixture"]["date"],
            # Neutral defaults only: live fixtures alone don't provide model features.
            "home_avg_scored": 1.35,
            "home_avg_conceded": 1.15,
            "away_avg_scored": 1.15,
            "away_avg_conceded": 1.35,
        })
    return pd.DataFrame(rows)
