import streamlit as st

def evaluate_live_ev(minute, shots, corners, cards, odds):
    try:
        minute = int(minute)
        shots = int(shots)
        corners = int(corners)
        cards = int(cards)
        odds = int(odds)

        # Simplified momentum + time-weighted EV scoring
        shot_weight = 1.5
        corner_weight = 0.8
        card_bonus = 0.5 if cards >= 2 else 0
        time_factor = (45 - minute) / 30  # weight urgency

        momentum_score = (shots * shot_weight) + (corners * corner_weight) + card_bonus
        expected_win_pct = min((momentum_score * time_factor) / 10, 1.0)
        implied_odds = round((1 / expected_win_pct) - 1, 2)
        ev_percent = (odds / 100) - implied_odds

        result = f"🧮 Estimated Win %: {round(expected_win_pct*100, 1)}%\n"
        result += f"🎯 Minimum Odds Needed: +{int(implied_odds * 100)}\n"
        result += f"{'✅ Bet has positive EV' if ev_percent > 0 else '❌ EV too low'}"
        return result
    except Exception as e:
        return f"Error: {str(e)}"

# Streamlit GUI
st.set_page_config(page_title="SharpBot Live Bet Evaluator", layout="centered")
st.title("⚡ SharpBot - Live Bet Evaluator (1H Over 1.5)")

match = st.text_input("Match Name")
minute = st.text_input("1st Half Minute (e.g. 16)")
shots = st.text_input("Shots (On + Off)")
corners = st.text_input("Corners")
cards = st.text_input("Cards (Total)")
odds = st.text_input("Odds (+210)")

if st.button("Evaluate Bet"):
    output = evaluate_live_ev(minute, shots, corners, cards, odds)
    st
