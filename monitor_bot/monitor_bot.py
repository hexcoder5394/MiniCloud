import psutil
import time
import asyncio
import socket

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8765976104:AAE1S5dqUW702wIIs2Gi4TG8cKtP59qY-ZA"
CHAT_ID = "8313606283"

CPU_THRESHOLD = 80
RAM_THRESHOLD = 80
DISK_THRESHOLD = 90

# -------- System Stats --------
def get_stats():
    hostname = socket.gethostname()
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    return float(cpu), float(ram), float(disk), str(hostname)

# -------- Commands --------
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cpu, ram, disk, hostname = get_stats()
    msg = f"""
📊 System Status:
Hostname: {hostname}
CPU: {cpu}%
RAM: {ram}%
Disk: {disk}%
"""
    await update.message.reply_text(msg)

async def uptime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time
    uptime_hours = uptime_seconds // 3600
    await update.message.reply_text(f"⏱ Uptime: {int(uptime_hours)} hours")

# -------- Alert Loop --------
async def monitor(app):
    while True:
        hostname, cpu, ram, disk = get_stats()

        if cpu > CPU_THRESHOLD:
            await app.bot.send_message(chat_id=CHAT_ID, text=f"⚠️ High CPU: {cpu}%")

        if ram > RAM_THRESHOLD:
            await app.bot.send_message(chat_id=CHAT_ID, text=f"⚠️ High RAM: {ram}%")

        if disk > DISK_THRESHOLD:
            await app.bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Disk Almost Full: {disk}%")

        await asyncio.sleep(30)

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("status", status))
app.add_handler(CommandHandler("uptime", uptime))

# start monitoring loop
async def post_init(app):
    asyncio.create_task(monitor(app))

app.post_init = post_init

app.run_polling()