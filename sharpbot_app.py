import streamlit as st
import requests
from bs4 import BeautifulSoup

# Core EV math
def implied_probability(decimal_odds):
    return round(1 / decimal_odds, 4)

def calculate_ev(prob, decimal_odds):
    return round((decimal_odds * prob - 1) * 100, 2)

def american_to_decimal(odds):
    try:
        odds = int(odds)
        return round((odds / 100) + 1, 2) if odds > 0 else round((100 / abs(odds)) + 1, 2)
    except:
        return 0.0

# FBref scraper for avg 1H goals
def extract_avg_1h_goals(fbref_url):
    try:
        response = requests.get(fbref_url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", {"id": "matchlogs_for"})
        rows = table.find_all("tr")[1:]

        first_half_goals = []
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 5:
                fhg = cells[4].text.strip()
                try:
                    if fhg:
                        first_half_goals.append(float(fhg))
                except:
                    pass

        avg_1h_goals = round(sum(first_half_goals) / len(first_half_goals), 2) if first_half_goals else 0.0
        return avg_1h_goals
    except:
        return 0.0

# Live game EV estimation based on momentum
def estimate_live_prob(shots, corners, cards, minutes_left, goal_line="1.5"):
    base = (shots * 1.5 + corners * 0.8)
    if cards >= 2:
        base += 1
    tempo_factor = minutes_left / 30
    raw_prob = min((base * tempo_factor) / 10, 1.0)

    if goal_line == "2.5":
        raw_prob = max(raw_prob - 0.15, 0.01)
    return raw_prob

# Streamlit App Layout
st.set_page_config(page_title="SharpBot Complete", layout="wide")
st.title("⚽ SharpBot - Full Soccer EV Suite")

tab1, tab2 = st.tabs(["📈 Pregame EV Evaluator", "🔥 Live Game EV Evaluator"])

# ---- Pregame Tab ----
with tab1:
    st.header("📊 Pregame Over 1.5 / 2.5 Goals Model")

    col1, col2 = st.columns(2)
    with col1:
        team1_url = st.text_input("FBref Match Logs URL - Team 1")
    with col2:
        team2_url = st.text_input("FBref Match Logs URL - Team 2")

    odds = st.text_input("Odds (e.g. +180)", value="180")
    goal_line = st.radio("Goal Line", ["1.5", "2.5"], horizontal=True)

    if st.button("Evaluate Pregame EV"):
        a1 = extract_avg_1h_goals(team1_url)
        a2 = extract_avg_1h_goals(team2_url)
        combined = a1 + a2
        line_factor = float(goal_line)
        prob = min(combined / line_factor, 0.99)
        decimal = american_to_decimal(odds)
        ev = calculate_ev(prob, decimal)

        st.success(f"✅ Combined Avg Goals: {combined} | Est. Win %: {int(prob*100)}% | EV: {ev}%")
        if ev > 5:
            st.markdown("### ✅ Recommended Bet (Pregame)")
        else:
            st.warning("⚠️ Below EV Threshold")

# ---- Live Game Tab ----
with tab2:
    st.header("🔥 Live Game Evaluator (Manual Input)")

    col1, col2 = st.columns(2)
    with col1:
        minute = st.number_input("Current 1H Minute", min_value=1, max_value=45, value=15)
        shots = st.number_input("Total Shots (On + Off)", min_value=0, value=5)
    with col2:
        corners = st.number_input("Corner Kicks", min_value=0, value=3)
        cards = st.number_input("Yellow/Red Cards (Total)", min_value=0, value=1)

    odds_live = st.text_input("Live Odds (e.g. +220)", value="220")
    goal_line_live = st.radio("Live Goal Line", ["1.5", "2.5"], horizontal=True)

    if st.button("Evaluate Live EV"):
        minutes_left = 45 - minute
        prob = estimate_live_prob(shots, corners, cards, minutes_left, goal_line_live)
        decimal = american_to_decimal(odds_live)
        ev = calculate_ev(prob, decimal)

        st.success(f"📈 Est. Win %: {int(prob * 100)}% | EV: {ev}%")
        if ev > 5:
            st.markdown("### ✅ Live Bet Recommended")
        else:
            st.warning("⚠️ No Edge at Current Pace")
