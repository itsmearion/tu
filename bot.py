import asyncio
from telethon import TelegramClient
from telethon.tl.functions.channels import GetParticipantsRequest, EditBannedRequest
from telethon.tl.types import ChatBannedRights, ChannelParticipantsSearch

# === KONFIGURASI ===
api_id = 123456                         # Ganti dengan API ID dari my.telegram.org
api_hash = 'your_api_hash'             # Ganti dengan API HASH
session_name = 'userbot_session'       # Nama file session userbot Telethon
channel_username = 'yourchannel'       # Nama channel tanpa '@'
admin_user_id = 123456789              # Ganti dengan user ID kamu (dapat dari @userinfobot)

# === HAK BAN PERMANEN ===
ban_rights = ChatBannedRights(
    until_date=None,
    view_messages=True                 # Ban user dari melihat channel
)

# === INISIALISASI TELETHON ===
client = TelegramClient(session_name, api_id, api_hash)
known_users = set()                    # Untuk menyimpan list member sebelumnya

# === FUNGSI: Ambil Semua Anggota Channel ===
async def fetch_all_members(channel):
    users = set()
    offset = 0
    limit = 100
    while True:
        result = await client(GetParticipantsRequest(
            channel=channel,
            filter=ChannelParticipantsSearch(''),
            offset=offset,
            limit=limit,
            hash=0
        ))
        if not result.users:
            break
        for user in result.users:
            users.add(user.id)
        offset += len(result.users)
    return users

# === FUNGSI: Kirim Pesan ke Admin ===
async def send_admin_message(text):
    try:
        await client.send_message(admin_user_id, text)
    except Exception as e:
        print(f"[ERROR] Gagal kirim notifikasi admin: {e}")

# === FUNGSI UTAMA: Monitor & Ban User yang Keluar ===
async def auto_ban_left_users():
    global known_users
    await client.start()
    channel = await client.get_entity(channel_username)

    print(f"Monitoring channel: {channel.title}")
    known_users = await fetch_all_members(channel)
    print(f"Total member awal: {len(known_users)}")

    while True:
        await asyncio.sleep(5)  # Interval polling
        try:
            current_users = await fetch_all_members(channel)
            left_users = known_users - current_users

            for user_id in left_users:
                # Notifikasi: User keluar
                await send_admin_message(f"User {user_id} telah keluar dari channel.")

                try:
                    # Eksekusi BAN
                    await client(EditBannedRequest(
                        channel=channel,
                        participant=user_id,
                        banned_rights=ban_rights
                    ))
                    print(f"[BANNED] User {user_id} keluar dan diban.")
                    await send_admin_message(f"User {user_id} telah DIBAN karena keluar dari channel.")
                except Exception as e:
                    print(f"[ERROR] Gagal ban {user_id}: {e}")
                    await send_admin_message(f"Gagal ban user {user_id}: {e}")

            known_users = current_users
        except Exception as e:
            print(f"[ERROR] Saat polling: {e}")
            await asyncio.sleep(10)

# === JALANKAN ===
with client:
    client.loop.run_until_complete(auto_ban_left_users())
