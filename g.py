from telethon.sync import TelegramClient
from telethon.sessions import StringSession

api_id = int(input("Masukkan API ID: "))
api_hash = input("Masukkan API Hash: ")

with TelegramClient(StringSession(), api_id, api_hash) as client:
    print("Login ke Telegram...")
    session_string = client.session.save()
    print("\n✅ String session kamu:\n")
    print(session_string)
