import streamlit as st
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(page_title="SharpBot Live Evaluator", layout="centered")

# ===== Core Calculations =====

def implied_probability(odds):
    return 100 / (odds + 100) if odds > 0 else abs(odds) / (abs(odds) + 100)

def min_odds_for_ev(est_win_prob, min_ev=5):
    implied_prob = est_win_prob - (min_ev / 100)
    if implied_prob <= 0:
        return None
    return round((100 / implied_prob) - 100, 2)

def estimate_live_win_prob(shots, corners, cards, time_left, line="1.5"):
    base = 0.15 + (shots * 0.03) + (corners * 0.02)
    time_factor = time_left / 45
    base *= (1 + time_factor * 0.4)
    if cards >= 2:
        base += 0.05
    if line == "0.5":
        return min(base + 0.25, 0.9)
    elif line == "2.5":
        return max(base - 0.1, 0.05)
    return min(base, 0.75)

# ===== Sheets Sync =====

def sync_to_sheet(match, time_left, est_prob, odds, ev):
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("SharpBot_Logs").sheet1
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [
            now, match,
            f"{time_left} min",
            f"{round(est_prob * 100)}%",
            f"+{odds}", f"{round(ev, 2)}%"
        ]
        sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"❌ Google Sheets error: {e}")
        return False

# ===== SofaScore Live Stats =====

def get_sofascore_live_stats(slug):
    try:
        url = f"https://www.sofascore.com/api/v1/event/{slug}/statistics"
        match_url = f"https://www.sofascore.com/api/v1/event/{slug}"
        headers = {"User-Agent": "Mozilla/5.0"}
        stats_resp = requests.get(url, headers=headers)
        match_resp = requests.get(match_url, headers=headers)

        data = stats_resp.json()
        match_data = match_resp.json()

        home_stats = data["statistics"][0]["groups"][0]["statisticsItems"]
        away_stats = data["statistics"][1]["groups"][0]["statisticsItems"]

        def find(stat_name):
            total = 0
            for stat in home_stats + away_stats:
                if stat["name"].lower() == stat_name.lower():
                    total += int(stat["value"])
            return total

        shots_total = find("shots on target") + find("shots off target")
        corners = find("corner kicks")
        cards = find("yellow cards") + find("red cards")
        minute = match_data["event"]["time"]["current"]

        return {
            "shots": shots_total,
            "corners": corners,
            "cards": cards,
            "minute": minute
        }
    except Exception as e:
        st.error(f"⚠️ SofaScore Error: {e}")
        return None

# ===== UI Layout =====

st.title("⚽ SharpBot Live Evaluator")
st.caption("Real-time EV Scanner for 1st Half Goal Lines")

with st.form("sharp_form"):
    match = st.text_input("Match Name")
    line = st.selectbox("1H Over Line", ["0.5", "1.5", "2.5"])
    slug = st.text_input("SofaScore Slug (ID from URL, e.g. 12437031)")
    fetch = st.form_submit_button("📡 Auto-Fill From SofaScore")

    if fetch and slug:
        data = get_sofascore_live_stats(slug)
        if data:
            st.session_state["shots"] = data["shots"]
            st.session_state["corners"] = data["corners"]
            st.session_state["cards"] = data["cards"]
            st.session_state["minute"] = data["minute"]
        else:
            st.warning("Could not fetch live data")

    shots = st.number_input("Shots (On + Off)", min_value=0, value=st.session_state.get("shots", 0))
    corners = st.number_input("Corners", min_value=0, value=st.session_state.get("corners", 0))
    cards = st.number_input("Cards", min_value=0, value=st.session_state.get("cards", 0))
    minute = st.number_input("Current Minute", min_value=0, max_value=45, value=st.session_state.get("minute", 0))
    odds = st.number_input("Odds (+210 → enter 210)", value=0)

    submitted = st.form_submit_button("Evaluate Bet")

if submitted:
    time_left = 45 - minute
    est_prob = estimate_live_win_prob(shots, corners, cards, time_left, line)
    ev = (est_prob - implied_probability(odds)) * 100
    min_needed = min_odds_for_ev(est_prob)

    st.subheader("📊 Result")
    st.markdown(f"""
- Match: `{match}`
- Line: `1H o{line}`
- Time Left: `{time_left} min`
- Estimated Win %: `{round(est_prob * 100)}%`
- Min Odds Needed: `+{int(min_needed)}`
- EV: `{round(ev, 2)}%`
""")

    if ev >= 5:
        st.success("✅ +EV Detected — Bet Approved")
        if sync_to_sheet(match, time_left, est_prob, odds, ev):
            st.success("📤 Logged to Google Sheets")
    else:
        st.error("❌ EV too low — do not bet")

