import os, requests, math
from datetime import datetime

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHANNEL_ID")

# (Scored per game, Conceded per game) 23/24 season - for real xG
STATS = {
    # EPL
    "Arsenal": (2.39, 0.76), "Manchester City": (2.53, 0.89), "Man City": (2.53, 0.89),
    "Liverpool": (2.26, 1.08), "Aston Villa": (1.97, 1.29), "Tottenham": (1.95, 1.61),
    "Tottenham Hotspur": (1.95, 1.61), "Newcastle": (2.0, 1.53), "Newcastle United": (2.0, 1.53),
    "Chelsea": (2.03, 1.63), "Manchester United": (1.5, 1.53), "Man United": (1.5, 1.53),
    "West Ham": (1.58, 1.95), "West Ham United": (1.58, 1.95), "Brighton": (1.71, 1.61),
    "Brighton & Hove Albion": (1.71, 1.61), "Wolves": (1.32, 1.71), "Wolverhampton": (1.32, 1.71),
    "Fulham": (1.47, 1.61), "Bournemouth": (1.42, 1.87), "Crystal Palace": (1.5, 1.5),
    "Brentford": (1.47, 1.63), "Everton": (1.05, 1.34), "Nottingham Forest": (1.29, 1.76),
    "Luton Town": (1.37, 1.89), "Luton": (1.37, 1.89), "Burnley": (1.08, 2.05),
    "Sheffield United": (0.74, 2.74), "Leicester City": (1.3, 1.4), "Ipswich Town": (1.2, 1.5),
    # LA LIGA
    "Real Madrid": (2.11, 0.68), "Barcelona": (2.08, 1.16), "Girona": (2.24, 1.21),
    "Atletico Madrid": (1.84, 1.13), "Atletico": (1.84, 1.13), "Athletic Club": (1.61, 1.0),
    "Athletic Bilbao": (1.61, 1.0), "Real Sociedad": (1.34, 1.03), "Real Betis": (1.26, 1.18),
    "Betis": (1.26, 1.18), "Villarreal": (1.63, 1.71), "Valencia": (1.05, 1.16),
    "Alaves": (0.92, 1.18), "Osasuna": (1.18, 1.5), "Getafe": (1.13, 1.34),
    "Celta Vigo": (1.08, 1.5), "Celta": (1.08, 1.5), "Sevilla": (1.29, 1.42),
    "Mallorca": (0.87, 1.13), "Las Palmas": (0.87, 1.21), "Rayo Vallecano": (0.76, 1.29),
    "Rayo": (0.76, 1.29),
    # BUNDESLIGA
    "Bayern Munich": (2.76, 1.32), "Bayern": (2.76, 1.32), "Bayer Leverkusen": (2.35, 0.71),
    "Leverkusen": (2.35, 0.71), "Stuttgart": (2.06, 1.15), "VfB Stuttgart": (2.06, 1.15),
    "RB Leipzig": (2.26, 1.15), "Leipzig": (2.26, 1.15), "Borussia Dortmund": (1.91, 1.29),
    "Dortmund": (1.91, 1.29), "Eintracht Frankfurt": (1.5, 1.47), "Frankfurt": (1.5, 1.47),
    "Hoffenheim": (1.74, 1.79), "Heidenheim": (1.5, 1.62), "Werder Bremen": (1.24, 1.62),
    "Bremen": (1.24, 1.62), "Freiburg": (1.32, 1.71), "Augsburg": (1.47, 1.5),
    "Wolfsburg": (1.21, 1.56), "Mainz": (0.85, 1.5), "Borussia Monchengladbach": (1.65, 1.79),
    "Monchengladbach": (1.65, 1.79), "Union Berlin": (0.85, 1.56), "Bochum": (1.24, 2.18),
    "Koln": (0.82, 1.79), "FC Koln": (0.82, 1.79)
}

def get_stats(name):
    name = name.lower()
    for k, v in STATS.items():
        if k.lower() in name or name in k.lower():
            return v
    return (1.35, 1.35)

def over_prob(exp_g1, exp_g2):
    lam = exp_g1 + exp_g2
    # Poisson P(over 1.5)
    p = 1 - math.exp(-lam) * (1 + lam)
    percent = int(p*100)
    return max(55, min(91, percent)), lam

def get_matches(code):
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard"
        r = requests.get(url, timeout=15)
        return r.json().get("events", [])[:8]
    except:
        return []

leagues = {"🏴󐁧󐁢󐁥󐁮󐁧󐁿 EPL": "eng.1", "🇪🇸 La Liga": "esp.1", "🇩🇪 Bundesliga": "ger.1"}

msg = f"⚽ <b>OVER 1.5 TIPS - {datetime.now().strftime('%d %b %Y')}</b>\n"
msg += "<i>Model: Attack vs Defence xG (Poisson)</i>\n\n"

all_tips = []
for lname, lcode in leagues.items():
    for ev in get_matches(lcode):
        try:
            comp = ev["competitions"][0]
            t1 = comp["competitors"][0]["team"]["displayName"]
            t2 = comp["competitors"][1]["team"]["displayName"]
            s1, c1 = get_stats(t1)
            s2, c2 = get_stats(t2)
            # expected goals = (attack + opponent defence)/2
            eg1 = (s1 + c2)/2
            eg2 = (s2 + c1)/2
            prob, xg = over_prob(eg1, eg2)
            if prob >= 70:
                conf = "🔥 HIGH" if prob>=82 else "✅ MED" if prob>=75 else "⚠️ LOW"
                all_tips.append((prob, f"{lname}\n{t1} vs {t2}\nOver 1.5 - {prob}% | xG {xg:.2f} - {conf}\n"))
        except:
            continue

# Sort by best probability
all_tips.sort(reverse=True, key=lambda x: x[0])

if all_tips:
    for _, line in all_tips[:10]: # top 10 best
        msg += line + "\n"
else:
    msg += "No strong Over 1.5 today. Check back tomorrow 9am.\n"

msg += "\n<i>18+ Bet responsibly | Form table: EPL + La Liga + Bundesliga</i>"

# Send
try:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=15)
    print(r.text)
    print("Message sent OK!" if r.status_code==200 else f"ERROR {r.text}")
except Exception as e:
    print(f"TELEGRAM ERROR: {e}")
