import streamlit as st
import requests
from bs4 import BeautifulSoup

# --- FBref Scraper ---
def scrape_avg_1h_goals(team_url):
    try:
        res = requests.get(team_url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find('table')
        rows = table.find_all('tr')

        total_goals = 0
        match_count = 0

        for row in rows:
            cells = row.find_all('td')
            if len(cells) > 5:
                try:
                    first_half_score = int(cells[4].text.strip())
                    total_goals += first_half_score
                    match_count += 1
                except:
                    continue

        avg_1h = total_goals / match_count if match_count else 0
        return round(avg_1h, 2)
    except Exception as e:
        return 0

# --- EV Calculators ---
def calculate_pregame_ev(avg_1h_goals, odds_decimal):
    win_probability = min(avg_1h_goals / 1.8, 0.99)
    ev = (odds_decimal * win_probability) - 1
    return win_probability, ev

def calculate_live_ev(minute, shots, corners, cards, odds_decimal):
    shot_weight = 1.5
    corner_weight = 0.8
    card_bonus = 0.5 if cards >= 2 else 0
    time_factor = (45 - minute) / 30

    momentum_score = (shots * shot_weight) + (corners * corner_weight) + card_bonus
    win_probability = min((momentum_score * time_factor) / 10, 1.0)
    ev = (odds_decimal * win_probability) - 1
    return win_probability, ev

# --- Streamlit UI ---
st.set_page_config("SharpBot", layout="centered")
st.title("⚽ SharpBot - Over 1.5 Goals EV Evaluator")

tab1, tab2 = st.tabs(["📊 Pre-Game (1H)", "🔥 Live Game (1H)"])

with tab1:
    st.subheader("Pre-Game Over 1.5 Goals Model")

    team_url = st.text_input("FBref Team Stats URL")
    match = st.text_input("Match Name (Optional Label)")
    odds_input = st.text_input("Odds (+180)", value="180")

    if st.button("Scrape + Evaluate"):
        try:
            odds_decimal = 1 + (int(odds_input) / 100)
            avg_goals = scrape_avg_1h_goals(team_url)
            win_pct, ev = calculate_pregame_ev(avg_goals, odds_decimal)
            st.info(f"📈 Scraped Avg 1H Goals: {avg_goals}")
            st.success(f"✅ Est. Win %: {round(win_pct*100, 1)}%\nEV: {round(ev*100, 2)}%")
            if ev > 0:
                st.markdown("**🔥 +EV Detected — Bet May Be Worth Placing!**")
            else:
                st.warning("❌ EV too low")
        except Exception as e:
            st.error(f"Error: {e}")

with tab2:
    st.subheader("Live Game 1H Model")

    minute = st.number_input("1st Half Minute (e.g. 16)", step=1, value=16)
    shots = st.number_input("Shots (On + Off)", step=1)
    corners = st.number_input("Corners", step=1)
    cards = st.number_input("Cards (Total)", step=1)
    odds_input_live = st.text_input("Odds (+210)", value="210")

    if st.button("Evaluate Live EV"):
        try:
            odds_decimal = 1 + (int(odds_input_live) / 100)
            win_pct, ev = calculate_live_ev(minute, shots, corners, cards, odds_decimal)
            st.success(f"✅ Est. Win %: {round(win_pct*100, 1)}%\nEV: {round(ev*100, 2)}%")
            if ev > 0:
                st.markdown("**💥 Live Bet Worth Considering!**")
            else:
                st.warning("❌ Not enough momentum for +EV")
        except:
            st.error("Invalid entry, double check odds.")
