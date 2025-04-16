import streamlit as st
import requests
from bs4 import BeautifulSoup
import re

# --- Scraper for SofaScore Match Stats ---
def get_sofascore_match_stats(sofa_url):
    try:
        response = requests.get(sofa_url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()

        stats = {
            "shots_on_target": sum(map(int, re.findall(r"Shots on target\s+(\d+)", text))),
            "shots_off_target": sum(map(int, re.findall(r"Shots off target\s+(\d+)", text))),
            "corners": sum(map(int, re.findall(r"Corner kicks\s+(\d+)", text))),
            "cards": sum(map(int, re.findall(r"(?:Yellow|Red) cards\s+(\d+)", text)))
        }
        return stats
    except:
        return None

# --- Estimate Probability and EV ---
def estimate_goal_probability(stats):
    total_shots = stats["shots_on_target"] + stats["shots_off_target"]
    attack_pressure = total_shots + stats["corners"] + (0.5 * stats["cards"])
    est_goals = attack_pressure / 6
    return min(est_goals / 1.5, 1.0)

def calculate_ev(prob, odds_decimal):
    return round((odds_decimal * prob - 1) * 100, 2)

# --- Streamlit GUI ---
st.set_page_config("SharpBot Manual EV", layout="centered")
st.title("🔍 SharpBot - Manual EV Checker (Over 1.5)")

sofa_url = st.text_input("Paste Sofascore Match URL:")
odds_input = st.text_input("Enter American Odds for Over 1.5 (e.g. +180):", "+180")

if st.button("Evaluate"):
    try:
        odds = int(odds_input)
        odds_decimal = (odds / 100 + 1) if odds > 0 else (100 / abs(odds) + 1)

        stats = get_sofascore_match_stats(sofa_url)

        if stats:
            st.subheader("📊 Match Stats")
            st.write(stats)

            win_prob = estimate_goal_probability(stats)
            ev = calculate_ev(win_prob, odds_decimal)

            st.subheader("📈 Analysis")
            st.write(f"Estimated Win Probability: **{win_prob * 100:.1f}%**")
            st.write(f"Expected Value (EV): **{ev:.2f}%**")

            if ev > 0:
                st.success("✅ +EV Opportunity Detected")
            else:
                st.warning("❌ EV Too Low")
        else:
            st.error("⚠️ Could not extract stats from the Sofascore page.")
    except Exception as e:
        st.error(f"❌ Error: {e}")
