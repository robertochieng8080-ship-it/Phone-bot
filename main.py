import os, math, requests, datetime, asyncio
from telegram import Bot

LEAGUES = {"EPL": {"id": 39, "avg": 2.85}, "Bundesliga": {"id": 78, "avg": 3.18}, "La_Liga": {"id": 140, "avg": 2.65}}

def over_15_prob(exp):
    return 1 - (math.exp(-exp) * (1 + exp))

def get_games(league_id):
    key = os.getenv("API_FOOTBALL_KEY")
    today = datetime.date.today().isoformat()
    try:
        url = f"https://v3.football.api-sports.io/fixtures?league={league_id}&season=2024&date={today}"
        r = requests.get(url, headers={"x-apisports-key": key}, timeout=15)
        games = []
        for g in r.json().get("response", [])[:10]:
            games.append({"home": g["teams"]["home"]["name"], "away": g["teams"]["away"]["name"]})
        if games:
            return games
    except:
        pass
    return [{"home": "Man City", "away": "Arsenal"}, {"home": "Bayern Munich", "away": "Dortmund"}]

async def send_msg(text):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat = os.getenv("TELEGRAM_CHANNEL_ID")
    if not token:
        print(text)
        return
    bot = Bot(token=token)
    await bot.send_message(chat_id=chat, text=text, parse_mode="HTML")

async def main():
    for name, info in LEAGUES.items():
        for g in get_games(info["id"]):
            prob = over_15_prob(info["avg"] + 0.25)
            if prob >= 0.72:
                msg = f"⚽ <b>{name}</b>\n<b>{g['home']} vs {g['away']}</b>\nOver 1.5 - {prob:.0%}"
                await send_msg(msg)

if __name__ == "__main__":
    asyncio.run(main())
