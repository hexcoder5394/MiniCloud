import requests
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# -------- ENV --------
TOKEN = "8765976104:AAE1S5dqUW702wIIs2Gi4TG8cKtP59qY-ZA"  # set this in env
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
        print(f"[WARN] Empty result for query:\n{query}\n")
        return None

    try:
        return float(result[0]["value"][1])
    except Exception as e:
        print(f"[ERROR] Parse error: {e}")
        return None

# -------- Get Stats --------
def get_server_stats(instance):
    # CPU (use 5m window for stability)
    cpu_query = f'''
    100 - (avg by(instance)(
        rate(node_cpu_seconds_total{{instance="{instance}", mode="idle"}}[5m])
    ) * 100)
    '''

    # RAM
    ram_query = f'''
    (node_memory_MemTotal_bytes{{instance="{instance}"}} -
     node_memory_MemAvailable_bytes{{instance="{instance}"}})
    / node_memory_MemTotal_bytes{{instance="{instance}"}} * 100
    '''

    # Disk (ignore tmpfs, all mounts)
    disk_query = f'''
    (node_filesystem_size_bytes{{instance="{instance}", fstype!="tmpfs"}} -
     node_filesystem_avail_bytes{{instance="{instance}", fstype!="tmpfs"}})
    / node_filesystem_size_bytes{{instance="{instance}", fstype!="tmpfs"}} * 100
    '''

    cpu = safe_query(cpu_query)
    ram = safe_query(ram_query)
    disk = safe_query(disk_query)

    return cpu, ram, disk

# -------- List Servers --------
def list_instances():
    result = query_prometheus("up")
    return [r["metric"]["instance"] for r in result]

# -------- Commands --------
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text(
            "Usage: /status <server_name or instance>\nUse /list to see servers."
        )
        return

    key = context.args[0].lower()
    instance = SERVERS.get(key, key)

    cpu, ram, disk = get_server_stats(instance)

    if cpu is None or ram is None or disk is None:
        await update.message.reply_text(
            f"❌ No data for '{instance}'\nUse /list to check valid servers."
        )
        return

    msg = (
        f"📊 {instance}\n"
        f"CPU: {cpu:.2f}%\n"
        f"RAM: {ram:.2f}%\n"
        f"Disk: {disk:.2f}%"
    )

    await update.message.reply_text(msg)

async def list_servers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    servers = list_instances()

    if not servers:
        await update.message.reply_text("❌ No servers found in Prometheus.")
        return

    msg = "🖥 Available servers:\n" + "\n".join(servers)
    await update.message.reply_text(msg)

# -------- Run Bot --------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("list", list_servers))

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()