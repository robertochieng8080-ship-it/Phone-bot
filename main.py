import os
import requests
import math
from datetime import datetime

# Get from GitHub Secrets
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHANNEL_ID") # your personal ID now

# Average goals scored per game last season - for Over 1.5 math
AVG_GOALS = {
    # EPL
    "Manchester City": 2.18, "Arsenal": 2.11, "Liverpool": 2.05, "Chelsea": 1.76,
    "Manchester United": 1.52, "Newcastle United": 1.92, "Tottenham Hotspur": 1.89,
    "Brighton & Hove Albion": 1.65, "Aston Villa": 1.68, "West Ham United": 1.42,
    "Crystal Palace": 1.28, "Fulham": 1.35, "Wolves": 1.22, "Everton": 1.05,
    "Brentford": 1.44, "Nottingham Forest": 1.25, "Bournemouth": 1.38,
    # La Liga
    "Real Madrid": 2.05, "Barcelona": 1.95, "Atletico Madrid": 1.75, "Girona": 2.0,
    "Athletic Club": 1.55, "Real Sociedad": 1.35, "Real Betis": 1.42, "Villarreal": 1.68,
    "Valencia": 1.25, "Sevilla": 1.18,
    # Bundesliga
    "Bayern Munich": 2.45, "Bayer Leverkusen": 2.35, "Stuttgart": 2.0, "RB Leipzig": 1.95,
    "Borussia Dortmund": 1.88, "Eintracht Frankfurt": 1.62, "Hoffenheim": 1.75,
    "Werder Bremen": 1.42, "Freiburg": 1.38, "Borussia Monchengladbach": 1.55
}

def get_avg(team_name):
    # find team, if not found return 1.35
    for key, val in AVG_GOALS.items():
        if key.lower() in team_name.lower() or team_name.lower() in key.lower():
            return val
    return 1.35

def over_15_prob(avg1, avg2):
    lam = avg1 + avg2 # expected total goals
    # Poisson: P(over 1.5) = 1 - P(0) - P(1)
    prob = 1 - math.exp(-lam) * (1 + lam)
    percent = int(prob * 100)
    if percent > 88: percent = 88
    if percent < 58: percent = 58
    return percent, lam

def get_matches(league_code):
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_code}/scoreboard"
    try:
        r = requests.get(url, timeout=15)
        data = r.json()
        return data.get("events", [])[:6] # next 6 games
    except:
        return []

leagues = {
    "🏴󐁧󐁢󐁥󐁮󐁧󐁿 EPL": "eng.1",
    "🇪🇸 La Liga": "esp.1",
    "🇩🇪 Bundesliga": "ger.1"
}

message = f"⚽ <b>OVER 1.5 PREDICTIONS - {datetime.now().strftime('%d %b')}</b>\n\n"
has_games = False

for league_name, code in leagues.items():
    events = get_matches(code)
    if not events:
        continue
    message += f"<b>{league_name}</b>\n"
    for ev in events:
        try:
            comp = ev["competitions"][0]
            t1 = comp["competitors"][0]["team"]["displayName"]
            t2 = comp["competitors"][1]["team"]["displayName"]
            avg1 = get_avg(t1)
            avg2 = get_avg(t2)
            prob, lam = over_15_prob(avg1, avg2)
            if prob >= 68: # only show good ones
                message += f"{t1} vs {t2}\nOver 1.5 - {prob}% (xG {lam:.1f})\n\n"
                has_games = True
        except:
            continue

if not has_games:
    message += "No strong Over 1.5 today - checking tomorrow.\n\n"

message += "<i>Model: Poisson xG | Target: Over 1.5 Goals</i>"

# Send to Telegram
print(f"Trying to send to: {CHAT_ID}")
print(f"Token exists: {bool(BOT_TOKEN)}")

try:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    res = requests.post(url, json=payload, timeout=15)
    print(f"TELEGRAM RESPONSE: {res.text}")
    if res.status_code == 200:
        print("Message sent OK!")
    else:
        print(f"TELEGRAM ERROR: {res.text}")
except Exception as e:
    print(f"TELEGRAM ERROR: {e}")
