import streamlit as st
from pregame_ev_scanner import get_ev_bets

st.set_page_config(page_title="SharpBot - Pregame EV Scanner", layout="wide")

st.title("⚽ SharpBot - Pregame +EV Over Goals Scanner")

# Toggle
goal_line = st.radio("Pick Goal Line", ["Over 1.5", "Over 2.5"])
min_ev = st.slider("Minimum EV Threshold %", min_value=0, max_value=20, value=5, step=1)
run_scan = st.button("🔍 Run Pregame EV Scan")

if run_scan:
    with st.spinner("Scanning..."):
        results = get_ev_bets(goal_line=goal_line, min_ev=min_ev)

    if results:
        st.success(f"✅ {len(results)} +EV Bets Found")
        for r in results:
            st.markdown(f"""
            ### {r['match']}
            - **Goal Line:** {goal_line}
            - **Est Win %:** {r['est_win_pct']}%
            - **Odds:** +{r['odds']}
            - **EV:** {r['ev']}%
            - **Avg 1H Goals:** {r['avg1']} + {r['avg2']} = {r['avg_total']}
            """)
    else:
        st.warning("No +EV games found based on current thresholds.")
