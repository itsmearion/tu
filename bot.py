import asyncio
from telethon import TelegramClient, events
from telethon.tl.functions.channels import GetParticipantsRequest, EditBannedRequest
from telethon.tl.types import ChatBannedRights, ChannelParticipantsSearch
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# === KONFIGURASI ===
api_id = 123456                         # Ganti dengan API ID dari my.telegram.org
api_hash = 'your_api_hash'              # Ganti dengan API HASH
session_name = 'userbot_session'        # Nama file session userbot Telethon
channel_username = 'yourchannel'        # Nama channel tanpa '@'
admin_group_id = -1001234567890         # ID Grup Admin untuk notifikasi log (tanpa @)

# === HAK BAN PERMANEN ===
ban_rights = ChatBannedRights(
    until_date=None,
    view_messages=True                 # Ban user dari melihat channel
)

# === INISIALISASI TELETHON ===
client = TelegramClient(session_name, api_id, api_hash)
known_users = set()                    # Untuk menyimpan list member sebelumnya

# === LOGGING ===
logging.basicConfig(filename="userbot_activity.log", level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

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

# === FUNGSI: Kirim Pesan ke Grup Admin ===
async def send_group_message(text):
    try:
        await client.send_message(admin_group_id, text)
    except Exception as e:
        print(f"[ERROR] Gagal kirim notifikasi ke grup admin: {e}")

# === FUNGSI: Log Aktivitas ke Grup Admin ===
def log_activity(message):
    logging.info(message)
    asyncio.create_task(send_group_message(message))

# === FUNGSI UTAMA: Monitor & Ban User yang Keluar ===
async def auto_ban_left_users():
    global known_users
    await client.start()
    channel = await client.get_entity(channel_username)

    log_activity(f"Monitoring channel: {channel.title}")
    known_users = await fetch_all_members(channel)
    log_activity(f"Total member awal: {len(known_users)}")

    while True:
        await asyncio.sleep(5)  # Interval polling
        try:
            current_users = await fetch_all_members(channel)
            left_users = known_users - current_users

            for user_id in left_users:
                # Kirim Notifikasi: User keluar
                log_activity(f"User {user_id} keluar dari channel.")
                await send_group_message(f"User {user_id} keluar dari channel.")
                
                try:
                    # Eksekusi BAN
                    await client(EditBannedRequest(
                        channel=channel,
                        participant=user_id,
                        banned_rights=ban_rights
                    ))
                    log_activity(f"[BANNED] User {user_id} keluar dan diban.")
                    await send_group_message(f"User {user_id} telah DIBAN karena keluar dari channel.")
                except Exception as e:
                    log_activity(f"[ERROR] Gagal ban {user_id}: {e}")
                    await send_group_message(f"Gagal ban user {user_id}: {e}")

            known_users = current_users
        except Exception as e:
            log_activity(f"[ERROR] Saat polling: {e}")
            await send_group_message(f"[ERROR] Saat polling: {e}")
            await asyncio.sleep(10)

# === FUNGSI: Deteksi User Bergabung Kembali ===
@client.on(events.NewUser)
async def user_joined(event):
    user = event.user
    if user.id not in known_users:
        log_activity(f"User {user.id} baru bergabung kembali.")
        await send_group_message(f"User {user.id} baru bergabung kembali.")

# === FUNGSI: Laporan Statistik Pengguna ===
ban_stats = {
    "total_bans": 0,
    "total_left": 0
}

def update_stats(ban=False, left=False):
    if ban:
        ban_stats["total_bans"] += 1
    if left:
        ban_stats["total_left"] += 1

async def send_statistic_report():
    report = f"Total bans: {ban_stats['total_bans']}\nTotal left: {ban_stats['total_left']}"
    await send_group_message(report)

# === PENJADWALAN: Kirim Laporan Statistik Setiap Hari ===
scheduler = AsyncIOScheduler()
scheduler.add_job(send_statistic_report, 'interval', hours=24)
scheduler.start()

# === JALANKAN ===
with client:
    client.loop.run_until_complete(auto_ban_left_users())
