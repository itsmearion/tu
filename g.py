from telethon.sync import TelegramClient
from telethon.sessions import StringSession

print("=== Generate String Session ===")
api_id = int(input("API ID: "))
api_hash = input("API Hash: ")

with TelegramClient(
    StringSession(),
    api_id,
    api_hash,
    device_model="TermuxAndroid",
    system_version="13",
    app_version="10.0",
    lang_code="en",
    system_lang_code="en"
) as client:
    print("Login ke Telegram...")
    session_string = client.session.save()
    print("\n✅ String session kamu:\n")
    print(session_string)
