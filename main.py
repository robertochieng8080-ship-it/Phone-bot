import os, requests, datetime, asyncio
from telegram import Bot

print("Bot starting...")

async def send_msg(text):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat = os.getenv("TELEGRAM_CHANNEL_ID")
    print(f"Trying to send to: {chat}")
    print(f"Token exists: {bool(token)}")
    if not token or not chat:
        print("Missing token or chat ID - check GitHub Secrets")
        print(text)
        return
    try:
        bot = Bot(token=token)
        await bot.send_message(chat_id=chat, text=text, parse_mode="HTML")
        print("Message sent OK!")
    except Exception as e:
        print(f"TELEGRAM ERROR: {e}")
        print(f"Chat ID you used: {chat}")
        print("FIX: Make bot admin in channel, or use @username with @, or use -100 number")
        print(f"Message was: {text}")

async def main():
    # test games
    msg = "⚽ <b>TEST</b>\nMan City vs Arsenal\nOver 1.5 - 78%\nBot is working!"
    await send_msg(msg)

if __name__ == "__main__":
    asyncio.run(main())
