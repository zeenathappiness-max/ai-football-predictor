import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from predictor import predict_match, poisson_probabilities
from data_provider import load_demo_fixtures, load_api_football_fixtures

st.set_page_config(page_title="AI Football Predictor", page_icon="⚽", layout="wide")

st.title("⚽ AI Football Predictor")
st.caption("Worldwide fixtures • Goal markets • Match outcomes • WAT kickoff times")

with st.sidebar:
    st.header("Settings")
    data_mode = st.radio(
        "Fixture source",
        ["Demo data (works immediately)", "API-Football"],
        help="Demo data is illustrative only. Connect an API key to load live fixtures.",
    )
    api_key = ""
    if data_mode == "API-Football":
        api_key = st.text_input("API-Football API key", type="password")
    st.divider()
    st.info("Predictions are estimates, not guarantees. Demo matches and probabilities are fictional.")

if data_mode == "API-Football":
    if not api_key:
        st.warning("Enter your API-Football key in the sidebar to load live fixtures.")
        fixtures = pd.DataFrame()
    else:
        try:
            fixtures = load_api_football_fixtures(api_key)
        except Exception as exc:
            st.error(f"Could not load fixtures: {exc}")
            fixtures = pd.DataFrame()
else:
    fixtures = load_demo_fixtures()

if fixtures.empty:
    st.stop()

st.subheader("Today's fixtures")
league_options = ["All leagues"] + sorted(fixtures["league"].dropna().unique().tolist())
selected_league = st.selectbox("Filter by league", league_options)
if selected_league != "All leagues":
    fixtures = fixtures[fixtures["league"] == selected_league]

rows = []
for _, match in fixtures.iterrows():
    pred = predict_match(
        home_team=match["home_team"],
        away_team=match["away_team"],
        home_goals_for=float(match.get("home_avg_scored", 1.35)),
        home_goals_against=float(match.get("home_avg_conceded", 1.15)),
        away_goals_for=float(match.get("away_avg_scored", 1.15)),
        away_goals_against=float(match.get("away_avg_conceded", 1.35)),
    )
    rows.append({**match.to_dict(), **pred})

results = pd.DataFrame(rows)
if "kickoff_utc" in results.columns:
    def to_wat(value):
        try:
            dt = pd.to_datetime(value, utc=True)
            return dt.tz_convert(ZoneInfo("Africa/Lagos")).strftime("%Y-%m-%d %H:%M WAT")
        except Exception:
            return str(value)
    results["kickoff_wat"] = results["kickoff_utc"].apply(to_wat)
else:
    results["kickoff_wat"] = "Time unavailable"

tab1, tab2, tab3 = st.tabs(["Predictions", "Match details", "About & limitations"])

with tab1:
    market = st.selectbox(
        "Prediction market",
        ["Over 1.5 goals", "Over 2.5 goals", "Over 3.5 goals", "BTTS — Yes",
         "BTTS — No", "Home win", "Draw", "Away win", "Home team over 0.5",
         "Away team over 0.5", "Most likely score"]
    )
    market_map = {
        "Over 1.5 goals": "over_1_5",
        "Over 2.5 goals": "over_2_5",
        "Over 3.5 goals": "over_3_5",
        "BTTS — Yes": "btts_yes",
        "BTTS — No": "btts_no",
        "Home win": "home_win",
        "Draw": "draw",
        "Away win": "away_win",
        "Home team over 0.5": "home_over_0_5",
        "Away team over 0.5": "away_over_0_5",
        "Most likely score": "most_likely_score",
    }
    key = market_map[market]
    display = results[["kickoff_wat", "league", "home_team", "away_team", key]].copy()
    display = display.rename(columns={
        "kickoff_wat": "Kickoff (WAT)", "league": "League",
        "home_team": "Home", "away_team": "Away", key: "Prediction"
    })
    if key != "most_likely_score":
        display["Prediction"] = display["Prediction"].apply(lambda x: f"{x:.1%}")
        display = display.sort_values("Prediction", ascending=False, key=lambda s: s.str.rstrip("%").astype(float))
    st.dataframe(display, use_container_width=True, hide_index=True)
    st.download_button(
        "Download predictions as CSV",
        results.to_csv(index=False).encode("utf-8"),
        file_name="football_predictions.csv",
        mime="text/csv",
    )

with tab2:
    match_names = (results["home_team"] + " vs " + results["away_team"]).tolist()
    chosen = st.selectbox("Choose a match", match_names)
    match = results.iloc[match_names.index(chosen)]
    st.markdown(f"### {match['home_team']} vs {match['away_team']}")
    st.write(f"**League:** {match['league']}  |  **Kickoff:** {match['kickoff_wat']}")
    metrics = [
        ("Over 1.5", "over_1_5"), ("Over 2.5", "over_2_5"),
        ("Over 3.5", "over_3_5"), ("BTTS Yes", "btts_yes"),
        ("Home win", "home_win"), ("Draw", "draw"), ("Away win", "away_win")
    ]
    cols = st.columns(4)
    for i, (label, col) in enumerate(metrics):
        cols[i % 4].metric(label, f"{match[col]:.1%}")
    st.metric("Most likely score", match["most_likely_score"])

with tab3:
    st.markdown("""
    **What this starter version does**
    - Calculates illustrative probabilities using a simple independent Poisson-goals model.
    - Converts expected goals into goal-market, BTTS, match-outcome, and score probabilities.
    - Shows kickoff times in West Africa Time when UTC kickoff data is available.
    - Supports a live-fixture API connection.

    **Important limitations**
    - The built-in demo matches and team averages are fictional and must not be used for betting.
    - Live fixture access does not automatically provide reliable team-strength estimates. For real predictions, connect historical results/statistics and validate the model on future unseen matches.
    - The starter model is not a guarantee of accuracy or profit.
    """)
