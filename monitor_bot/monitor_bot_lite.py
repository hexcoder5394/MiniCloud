import requests
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)

# -------- ENV --------
TOKEN = "8765976104:AAE1S5dqUW702wIIs2Gi4TG8cKtP59qY-ZA"
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://192.168.8.152:9090")

# -------- Server Aliases --------
SERVERS = {
    "container-host": "192.168.8.150:9100",
    "db": "192.168.8.151:9100",
}

# -------- Prometheus Query --------
def query_prometheus(query):
    try:
        url = f"{PROMETHEUS_URL}/api/v1/query"
        response = requests.get(url, params={"query": query}, timeout=5)
        data = response.json()

        if data.get("status") != "success":
            return []

        return data["data"]["result"]

    except Exception as e:
        print(f"Prometheus error: {e}")
        return []

# -------- Safe Query --------
def safe_query(query):
    result = query_prometheus(query)

    if not result:
        return None

    try:
        return float(result[0]["value"][1])
    except:
        return None

# -------- Get Stats --------
def get_server_stats(instance):
    cpu_query = f'100 - (avg by(instance)(rate(node_cpu_seconds_total{{instance="{instance}",mode="idle"}}[5m])) * 100)'
    ram_query = f'(node_memory_MemTotal_bytes{{instance="{instance}"}} - node_memory_MemAvailable_bytes{{instance="{instance}"}}) / node_memory_MemTotal_bytes{{instance="{instance}"}} * 100'
    disk_query = f'(node_filesystem_size_bytes{{instance="{instance}",fstype!="tmpfs"}} - node_filesystem_avail_bytes{{instance="{instance}",fstype!="tmpfs"}}) / node_filesystem_size_bytes{{instance="{instance}",fstype!="tmpfs"}} * 100'

    cpu = safe_query(cpu_query)
    ram = safe_query(ram_query)
    disk = safe_query(disk_query)

    return cpu, ram, disk

# -------- Commands --------

# 🔹 Single server status
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await show_buttons(update)
        return

    key = context.args[0].lower()
    instance = SERVERS.get(key, key)

    cpu, ram, disk = get_server_stats(instance)

    if cpu is None:
        await update.message.reply_text(f"❌ No data for {instance}")
        return

    msg = (
        f"📊 {instance}\n"
        f"CPU: {cpu:.2f}%\n"
        f"RAM: {ram:.2f}%\n"
        f"Disk: {disk:.2f}%"
    )

    await update.message.reply_text(msg)

# 🔹 Status all servers
async def status_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "📊 All Servers:\n\n"

    for name, instance in SERVERS.items():
        cpu, ram, disk = get_server_stats(instance)

        if cpu is None:
            msg += f"{name}: ❌ no data\n\n"
            continue

        msg += (
            f"{name} ({instance})\n"
            f"CPU: {cpu:.1f}% | RAM: {ram:.1f}% | Disk: {disk:.1f}%\n\n"
        )

    await update.message.reply_text(msg)

# 🔹 Top CPU server
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    highest = None
    highest_cpu = -1

    for name, instance in SERVERS.items():
        cpu, ram, disk = get_server_stats(instance)

        if cpu is None:
            continue

        if cpu > highest_cpu:
            highest_cpu = cpu
            highest = (name, instance, ram, disk)

    if not highest:
        await update.message.reply_text("❌ No data available")
        return

    name, instance, ram, disk = highest

    msg = (
        f"🔥 Highest CPU Usage\n\n"
        f"{name} ({instance})\n"
        f"CPU: {highest_cpu:.2f}%\n"
        f"RAM: {ram:.2f}%\n"
        f"Disk: {disk:.2f}%"
    )

    await update.message.reply_text(msg)

# 🔹 Inline buttons
async def show_buttons(update: Update):
    keyboard = [
        [InlineKeyboardButton(name, callback_data=instance)]
        for name, instance in SERVERS.items()
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Select a server:",
        reply_markup=reply_markup
    )

# 🔹 Button handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    instance = query.data
    cpu, ram, disk = get_server_stats(instance)

    if cpu is None:
        await query.edit_message_text(f"❌ No data for {instance}")
        return

    msg = (
        f"📊 {instance}\n"
        f"CPU: {cpu:.2f}%\n"
        f"RAM: {ram:.2f}%\n"
        f"Disk: {disk:.2f}%"
    )

    await query.edit_message_text(msg)

# -------- Run Bot --------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("status_all", status_all))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("✅ Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()