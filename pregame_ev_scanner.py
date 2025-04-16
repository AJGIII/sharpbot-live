import requests
from bs4 import BeautifulSoup
import re

headers = {"User-Agent": "Mozilla/5.0"}

def implied_prob(odds): return 100 / (odds + 100)
def ev_value(prob, odds): return round((prob - implied_prob(odds)) * 100, 2)

def min_odds(est_win_pct, min_ev): return round((100 / (est_win_pct - min_ev / 100)) - 100, 2)

def fetch_1h_avg(team_name):
    try:
        search = requests.get(f"https://fbref.com/en/search/search.fcgi?search={team_name.replace(' ', '+')}", headers=headers)
        soup = BeautifulSoup(search.text, "html.parser")
        link = next(a for a in soup.find_all("a", href=True) if "/en/squads/" in a["href"])
        team = requests.get("https://fbref.com" + link["href"], headers=headers)
        table = BeautifulSoup(team.text, "html.parser").find("table", {"id": "matchlogs_for"})
        rows = table.find_all("tr", class_="full_table")
        goals = []
        for row in rows:
            g = row.find("td", {"data-stat": "goals"}).text.strip()
            if g.isdigit(): goals.append(int(g))
        return round(sum(goals)/len(goals), 2) if len(goals) >= 5 else None
    except:
        return None

def fetch_odds(team1, team2, goal_line="Over 1.5"):
    try:
        search_url = f"https://www.oddsportal.com/search/results/{team1.replace(' ', '%20')}%20vs%20{team2.replace(' ', '%20')}/"
        soup = BeautifulSoup(requests.get(search_url, headers=headers).text, "html.parser")
        link = next(a for a in soup.find_all("a", href=True) if "/soccer/" in a["href"])
        match_page = requests.get("https://www.oddsportal.com" + link["href"] + "over-under/", headers=headers)
        pattern = r"1st Half - " + re.escape(goal_line) + r".*?\+(\d+)"
        match = re.search(pattern, match_page.text, re.DOTALL)
        return int(match.group(1)) if match else None
    except:
        return None

def estimate_win(avg):  # crude model
    return (
        0.30 if avg < 1.2 else
        0.40 if avg < 1.5 else
        0.48 if avg < 1.8 else
        0.54 if avg < 2.1 else
        0.60
    )

def get_ev_bets(goal_line="Over 1.5", min_ev=5):
    matchups = [
        ("Real Madrid", "Arsenal"),
        ("Liverpool", "Brighton"),
        ("Man City", "West Ham"),
        ("Barcelona", "Valencia"),
        ("Inter Milan", "Napoli"),
        ("Atletico Madrid", "Betis"),
        ("Juventus", "Torino"),
        ("Bayern Munich", "Leipzig"),
        ("PSG", "Marseille"),
        ("Ajax", "Feyenoord"),
    ]

    good_bets = []

    for team1, team2 in matchups:
        avg1 = fetch_1h_avg(team1)
        avg2 = fetch_1h_avg(team2)
        if avg1 is None or avg2 is None:
            continue

        avg_total = avg1 + avg2
        est_win_pct = round(estimate_win(avg_total) * 100)
        odds = fetch_odds(team1, team2, goal_line)
        if odds is None:
            continue

        ev = ev_value(est_win_pct / 100, odds)
        if ev >= min_ev:
            good_bets.append({
                "match": f"{team1} vs {team2}",
                "avg1": avg1,
                "avg2": avg2,
                "avg_total": round(avg_total, 2),
                "est_win_pct": est_win_pct,
                "odds": odds,
                "ev": round(ev, 2)
            })

    return sorted(good_bets, key=lambda x: x['ev'], reverse=True)[:10]
