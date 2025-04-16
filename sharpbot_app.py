# sharpbot_app.py

import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import math

# --- Config ---
ODDS_THRESHOLD = 1.7  # Minimum decimal odds
EV_THRESHOLD = 3      # Min expected value in percent

# --- Helper Functions ---

def american_to_decimal(odds):
    if odds >= 100:
        return (odds / 100) + 1
    elif odds <= -100:
        return (100 / abs(odds)) + 1
    else:
        return None

def implied_prob_from_decimal(decimal_odds):
    return 1 / decimal_odds

def calculate_ev(win_prob, decimal_odds):
    return round((win_prob * decimal_odds - 1) * 100, 2)

def scrape_1h_avg_from_fbref(url):
    try:
        res = requests.get(url)
        soup = BeautifulSoup(res.content, "html.parser")
        table = soup.find("table", {"id": "stats_squads_standard_for"})

        if not table:
            return 0.0

        rows = table.find_all("tr")
        for row in rows:
            if "Average" in row.text:
                avg = row.find_all("td")[-1].text.strip()
                return float(avg) if avg else 0.0
    except:
        return 0.0

# --- GUI Start ---
st.set_page_config("SharpBot Evaluator", layout="wide")
tab1, tab2 = st.tabs(["📊 Pre-Game (1H)", "🔥 Live Game (1H)"])

# --- Pregame Evaluator ---
with tab1:
    st.title("Pre-Game Over 1.5 Goals Model")

    fbref_url = st.text_input("FBref Team Stats URL")
    match_name = st.text_input("Match Name (Optional Label)")
    odds_input = st.text_input("Odds (+180)", "180")
    decimal_odds = american_to_decimal(int(odds_input))

    if st.button("Scrape + Evaluate"):
        avg_1h_goals = scrape_1h_avg_from_fbref(fbref_url)
        win_prob = min(1, avg_1h_goals / 1.5)
        ev = calculate_ev(win_prob, decimal_odds)

        st.success(f"Scraped Avg 1H Goals: {avg_1h_goals:.2f}")
        st.success(f"Est. Win %: {win_prob * 100:.1f}% | EV: {ev:.2f}%")

        if ev > EV_THRESHOLD:
            st.success("✅ Bet Recommended")
        else:
            st.warning("❌ EV too low")

# --- Live Game Evaluator ---
with tab2:
    st.title("Live Game Over 1.5 Goals Evaluator")

    match_name = st.text_input("Match Name")
    minute = st.slider("1st Half Minute", 1, 45, 15)
    shots_on = st.number_input("Shots On Target", 0)
    shots_off = st.number_input("Shots Off Target", 0)
    corners = st.number_input("Corners", 0)
    cards = st.number_input("Total Cards", 0)
    odds_live = st.number_input("Live Odds (+180)", value=180)

    decimal_live_odds = american_to_decimal(int(odds_live))

    if st.button("Evaluate Live Bet"):
        activity_score = (shots_on * 1.5 + shots_off + corners * 0.75 + cards * 0.5)
        time_factor = (45 - minute) / 45
        est_win = min(1, (activity_score / 10) * time_factor)
        ev_live = calculate_ev(est_win, decimal_live_odds)

        st.success(f"Live Momentum Score: {activity_score:.1f}")
        st.success(f"Est. Win %: {est_win * 100:.1f}% | EV: {ev_live:.2f}%")

        if ev_live > EV_THRESHOLD:
            st.success("✅ Bet Live")
        else:
            st.warning("❌ EV too low")

# Future: Add Top 10 EV pregame bet module + export option
