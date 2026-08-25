import os, requests, math, time
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHANNEL_ID")
EAT = timezone(timedelta(hours=3))
TODAY = datetime.now(EAT)
TOMORROW = TODAY + timedelta(days=1)

STATS = {
    "Arsenal": (2.39, 0.76), "Man City": (2.53, 0.89), "Manchester City": (2.53, 0.89),
    "Liverpool": (2.26, 1.08), "Chelsea": (2.03, 1.63), "Newcastle": (2.0, 1.53),
    "Tottenham": (1.95, 1.61), "Aston Villa": (1.97, 1.29), "Brighton": (1.71, 1.61),
    "Real Madrid": (2.11, 0.68), "Barcelona": (2.08, 1.16), "Girona": (2.24, 1.21),
    "Atletico Madrid": (1.84, 1.13), "Bayern Munich": (2.76, 1.32), "Bayern": (2.76, 1.32),
    "Leverkusen": (2.35, 0.71), "Dortmund": (1.91, 1.29), "Inter": (2.32, 0.58),
    "AC Milan": (1.97, 1.26), "Juventus": (1.42, 0.76), "PSG": (2.26, 0.85),
    "PSV": (2.91, 0.88), "Benfica": (2.41, 0.76), "Sporting CP": (2.82, 0.88)
}

def get_stats(name):
    name=name.lower()
    for k,v in STATS.items():
        if k.lower() in name or name in k.lower(): return v
    return (1.35, 1.35)

def probs(eg1, eg2):
    lam = eg1 + eg2
    p15 = 1 - math.exp(-lam)*(1+lam)
    p25 = 1 - math.exp(-lam)*(1+lam+ (lam**2)/2)
    btts = (1-math.exp(-eg1)) * (1-math.exp(-eg2))
    return int(p15*100), int(p25*100), int(btts*100), lam

def get_matches_for_date(code, date_obj):
    datestr = date_obj.strftime("%Y%m%d")
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard?dates={datestr}"
        return requests.get(url, timeout=15).json().get("events", [])[:6]
    except: return []

def get_time_eat(date_str):
    try:
        dt_utc = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt_utc.astimezone(EAT).strftime("%d %b %H:%M")
    except: return ""

# REAL bookie average odds for these markets (when 80%+)
def estimate_odds(market):
    if market == "Over 1.5": return 1.32
    if market == "Over 2.5": return 1.85
    if market == "BTTS": return 1.90
    return 1.50

LEAGUES = {
    "EPL": "eng.1", "La Liga": "esp.1", "Bundes": "ger.1",
    "Serie A": "ita.1", "Ligue 1": "fra.1", "Eredivisie": "ned.1",
    "Portugal": "por.1", "UCL": "uefa.champions"
}

MIN = 80
all_bets = [] # for accumulator

msg = f"⚽ <b>80%+ TIPS + 3-5 ODDS ACCA</b>\n<i>{TODAY.strftime('%d %b')} - {TOMORROW.strftime('%d %b')} | EAT</i>\n\n"

# Collect all 80%+ bets
for day_label, day_obj in [("TODAY", TODAY), ("TOMORROW", TOMORROW)]:
    for lname,lcode in LEAGUES.items():
        time.sleep(0.8)
        for ev in get_matches_for_date(lcode, day_obj):
            try:
                comp=ev["competitions"][0]
                t1=comp["competitors"][0]["team"]["displayName"]
                t2=comp["competitors"][1]["team"]["displayName"]
                kickoff = get_time_eat(ev.get("date",""))
                s1,c1=get_stats(t1); s2,c2=get_stats(t2)
                eg1=(s1+c2)/2; eg2=(s2+c1)/2
                p15,p25,btts,xg=probs(eg1,eg2)

                # Pick best market for accumulator (prefer high odds)
                best_market = None
                best_prob = 0
                if p25>=MIN and p25>=best_prob: best_market=("Over 2.5", p25)
                if btts>=MIN and btts>=best_prob: best_market=("BTTS", btts)
                if p15>=MIN and best_market is None: best_market=("Over 1.5", p15) # only if no high odds

                if best_market:
                    market, prob = best_market
                    odds = estimate_odds(market)
                    all_bets.append({
                        "day": day_label, "league": lname, "match": f"{t1} vs {t2}",
                        "time": kickoff, "market": market, "prob": prob, "odds": odds, "xg": xg
                    })
            except: continue

# Sort by highest prob
all_bets.sort(key=lambda x: x["prob"], reverse=True)

# Show individual tips
if all_bets:
    for b in all_bets[:10]:
        msg+=f"<b>{b['day']} {b['league']} | {b['time']}</b>\n{b['match']}\n{b['market']} {b['prob']}% @ {b['odds']} ✅\n\n"
else:
    msg+="No 80%+ tips today/tomorrow\n\n"

# BUILD 3-5 ODDS ACCUMULATOR
if len(all_bets) >= 2:
    # Try to hit 3-5 odds
    acca = []
    total_odds = 1.0
    for b in all_bets:
        if total_odds < 3.0: # need more legs
            acca.append(b)
            total_odds *= b["odds"]
        elif total_odds < 5.0: # perfect zone
            break
        else: # over 5, stop
            break

    # If still under 3 odds, add one more
    if total_odds < 3.0 and len(all_bets) > len(acca):
        acca.append(all_bets[len(acca)])
        total_odds *= all_bets[len(acca)-1]["odds"]

    if 3.0 <= total_odds <= 5.5 and len(acca)>=2:
        msg+=f"🔥 <b>ACCUMULATOR {total_odds:.2f} ODDS (3-5 Target)</b>\n"
        msg+=f"<i>{
