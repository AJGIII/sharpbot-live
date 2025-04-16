# pregame_ev_gui.py

import streamlit as st
import requests
from bs4 import BeautifulSoup

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

def implied_prob(decimal_odds):
    return round(1 / decimal_odds, 4)

def calculate_ev(prob, decimal_odds):
    payout = decimal_odds - 1
    ev = round((prob * payout - (1 - prob)) * 100, 2)
    return ev

def american_to_decimal(odds):
    try:
        odds = int(odds)
        if odds > 0:
            return round((odds / 100) + 1, 2)
        else:
            return round((100 / abs(odds)) + 1, 2)
    except:
        return 0.0

# GUI
st.set_page_config(page_title="SharpBot Pregame EV", layout="centered")
st.title("📊 SharpBot: Pregame Over 1.5 Goals Evaluator")

st.subheader("FBref URLs for Each Team")
t1 = st.text_input("Team 1 FBref Match Logs URL")
t2 = st.text_input("Team 2 FBref Match Logs URL")

st.subheader("1st Half Over 1.5 Odds (e.g. +180)")
odds_input = st.text_input("Odds", value="+180")

if st.button("Scrape + Evaluate"):
    with st.spinner("Scraping data from FBref..."):
        g1 = extract_avg_1h_goals(t1)
        g2 = extract_avg_1h_goals(t2)
        total_avg = g1 + g2
        est_prob = min(round(total_avg / 1.5, 2), 0.99)
        dec_odds = american_to_decimal(odds_input)
        ev = calculate_ev(est_prob, dec_odds)

    st.success(f"Scraped Avg 1H Goals: {total_avg}")
    st.info(f"Est. Win %: {int(est_prob * 100)}%  EV: {ev}%")

    if ev > 5:
        st.success("✅ +EV Bet")
    else:
        st.warning("⚠️ EV too low")
