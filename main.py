import os, requests, math, time
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHANNEL_ID")
EAT = timezone(timedelta(hours=3)) # Nairobi

STATS = {
    "Arsenal": (2.39, 0.76), "Man City": (2.53, 0.89), "Manchester City": (2.53, 0.89),
    "Liverpool": (2.26, 1.08), "Chelsea": (2.03, 1.63), "Newcastle": (2.0, 1.53),
    "Tottenham": (1.95, 1.61), "Aston Villa": (1.97, 1.29), "Brighton": (1.71, 1.61),
    "Real Madrid": (2.11, 0.68), "Barcelona": (2.08, 1.16), "Girona": (2.24, 1.21),
    "Atletico Madrid": (1.84, 1.13), "Athletic Bilbao": (1.61, 1.0),
    "Bayern Munich": (2.76, 1.32), "Bayern": (2.76, 1.32), "Leverkusen": (2.35, 0.71),
    "Bayer Leverkusen": (2.35, 0.71), "Dortmund": (1.91, 1.29), "RB Leipzig": (2.26, 1.15),
    "Inter Milan": (2.32, 0.58), "Inter": (2.32, 0.58), "AC Milan": (1.97, 1.26),
    "Juventus": (1.42, 0.76), "Napoli": (1.5, 1.26), "AS Roma": (1.71, 1.24),
    "Roma": (1.71, 1.24), "Atalanta": (1.92, 1.11), "Paris Saint-Germain": (2.26, 0.85),
    "PSG": (2.26, 0.85), "Monaco": (1.85, 1.32), "Lille": (1.44, 0.85),
    "PSV": (2.91, 0.88), "Ajax": (2.18, 1.76), "Benfica": (2.41, 0.76),
    "Sporting CP": (2.82, 0.88), "Porto": (1.91, 0.79)
}

def get_stats(name):
    name=name.lower()
    for k,v in STATS.items():
        if k.lower() in name or name in k.lower():
            return v
    return (1.35, 1.35)

def probs(eg1, eg2):
    lam = eg1 + eg2
    p15 = 1 - math.exp(-lam)*(1+lam)
    p25 = 1 - math.exp(-lam)*(1+lam+ (lam**2)/2)
    btts = (1-math.exp(-eg1)) * (1-math.exp(-eg2))
    return int(p15*100), int(p25*100), int(btts*100), lam

def get_matches(code):
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard"
        r = requests.get(url, timeout=15)
        return r.json().get("events", [])[:6]
    except:
        return []

def get_time_eat(date_str):
    try:
        # ESPN: 2024-08-25T19:00:00Z
        dt_utc = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        dt_eat = dt_utc.astimezone(EAT)
        return dt_eat.strftime("%H:%M EAT")
    except:
        return ""

LEAGUES = {
    "🏴󐁧󐁢󐁥󐁮󐁧󐁿 EPL": "eng.1", "🇪🇸 La Liga": "esp.1", "🇩🇪 Bundesliga": "ger.1",
    "🇮🇹 Serie A": "ita.1", "🇫🇷 Ligue 1": "fra.1", "🇳🇱 Eredivisie": "ned.1",
    "🇵🇹 Portugal": "por.1", "🇪🇺 UCL": "uefa.champions"
}

MIN = 80
msg = f"⚽ <b>80%+ TIPS + TIME - {datetime.now(EAT).strftime('%d %b %H:%M')}</b>\n\n"

tips=[]
for lname,lcode in LEAGUES.items():
    time.sleep(1.2)
    for ev in get_matches(lcode):
        try:
            comp=ev["competitions"][0]
            t1=comp["competitors"][0]["team"]["displayName"]
            t2=comp["competitors"][1]["team"]["displayName"]
            kickoff = get_time_eat(ev.get("date",""))
            s1,c1=get_stats(t1); s2,c2=get_stats(t2)
            eg1=(s1+c2)/2; eg2=(s2+c1)/2
            p15,p25,btts,xg=probs(eg1,eg2)
            best=max(p15,p25,btts)
            if best>=MIN:
                line=f"<b>{lname} | {kickoff}</b>\n{t1} vs {t2}\n"
                if p15>=MIN: line+=f"Over 1.5 {p15}% ✅\n"
                if p25>=MIN: line+=f"Over 2.5 {p25}% ✅\n"
                if btts>=MIN: line+=f"BTTS {btts}% ✅\n"
                line+=f"xG {xg:.2f}\n\n"
                tips.append((best,line))
        except: continue

tips.sort(reverse=True, key=lambda x: x[0])
if tips:
    for _,l in tips[:15]:
        msg+=l
else:
    msg+="No 80%+ tips today.\n"

msg+="\n<i>Time in Nairobi EAT | 8 leagues | 18+</i>"

try:
    url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id":CHAT_ID,"text":msg,"parse_mode":"HTML"}, timeout=15)
    print("Sent with time!")
except Exception as e:
    print(f"ERROR {e}")
