# SharpBot: Auto Top 10 Pregame Over 1.5 EV Scanner (Streamlit App)

import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

# --- CONFIG ---
ODDS_THRESHOLD = 1.80  # Equivalent to +180 American odds
EV_THRESHOLD = 0.05     # +5% EV minimum

# --- FUNCTIONS ---

def fetch_fbref_1h_avg(team_url):
    try:
        res = requests.get(team_url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        table = soup.find("table", {"id": "stats_squads_standard_for"})
        rows = table.find_all("tr")

        for row in rows:
            if "1st Half" in row.text:
                cells = row.find_all("td")
                if len(cells) > 5:
                    goals_for = float(cells[5].text.strip())
                    return goals_for
    except:
        return 0.0
    return 0.0

def estimate_win_prob(avg_goals):
    # Simple conversion based on ~58% chance if avg = 1.4
    return min(max((avg_goals - 0.8) * 0.9, 0), 0.99)

def calculate_ev(prob, odds_decimal):
    payout = odds_decimal
    ev = (prob * payout) - 1
    return ev

def scrape_top_matches():
    # Simulated schedule for demo (replace with real scraper later)
    matches = [
        {"match": "Real Madrid vs Getafe", "home_url": "https://fbref.com/team1", "away_url": "https://fbref.com/team2"},
        {"match": "Man City vs Burnley", "home_url": "https://fbref.com/team3", "away_url": "https://fbref.com/team4"},
        {"match": "Liverpool vs Wolves", "home_url": "https://fbref.com/team5", "away_url": "https://fbref.com/team6"},
        {"match": "Bayern vs Augsburg", "home_url": "https://fbref.com/team7", "away_url": "https://fbref.com/team8"},
        {"match": "PSG vs Nice", "home_url": "https://fbref.com/team9", "away_url": "https://fbref.com/team10"},
    ]
    return matches

def run_ev_model():
    top_matches = scrape_top_matches()
    results = []

    for match in top_matches:
        avg1 = fetch_fbref_1h_avg(match["home_url"])
        avg2 = fetch_fbref_1h_avg(match["away_url"])
        combined_avg = avg1 + avg2
        win_prob = estimate_win_prob(combined_avg)
        ev = calculate_ev(win_prob, ODDS_THRESHOLD)

        results.append({
            "Match": match["match"],
            "Avg 1H Goals": round(combined_avg, 2),
            "Win %": round(win_prob * 100, 1),
            "EV": round(ev * 100, 2),
            "Odds": ODDS_THRESHOLD
        })

    df = pd.DataFrame(results)
    df = df[df["EV"] > EV_THRESHOLD * 100]
    df = df.sort_values("EV", ascending=False).head(10)
    return df

# --- STREAMLIT APP ---

st.set_page_config(page_title="SharpBot - Top 10 Pregame EV", layout="wide")
st.title("⚽ SharpBot - Top 10 Pregame Over 1.5 EV Bets")
st.markdown("Automatically shows the most +EV 1st Half Over 1.5 bets for today based on FBref stats.")

with st.spinner("Scanning upcoming matches..."):
    df_results = run_ev_model()

if not df_results.empty:
    st.success(f"✅ Found {len(df_results)} value bets:")
    st.dataframe(df_results, use_container_width=True)
else:
    st.warning("No +EV bets found right now. Try again later.")
