import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import os, random, time, psutil, threading, traceback

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-100xxxxxxxxxx"))

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

reply_mode = {}
live_monitor = False

taglines = [
    "⚡ Lightning Fast Support",
    "🚀 Powered by Intelligence",
    "💀 Elite Response System",
    "🔥 Premium Support Activated",
    "🧠 Smart AI Routing Enabled"
]

# ===== ERROR ALERT =====
def send_error(e):
    try:
        bot.send_message(ADMIN_ID, f"⚠️ ERROR:\n<code>{e}</code>")
    except:
        pass

# ===== AUTO ALERT =====
def auto_alert():
    while True:
        try:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent

            if cpu > 80 or ram > 80:
                bot.send_message(ADMIN_ID, f"""
🚨 SYSTEM ALERT 🚨

⚡ CPU: {cpu}%
🧠 RAM: {ram}%

🔥 HIGH USAGE DETECTED
""")
            time.sleep(10)
        except:
            send_error(traceback.format_exc())

threading.Thread(target=auto_alert, daemon=True).start()

# ===== ADMIN KEYBOARD =====
def admin_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📊 SPEED"), KeyboardButton("⛔ STOP"))
    return kb

# ===== START =====
@bot.message_handler(commands=['start'])
def start(m):
    try:
        msg = bot.send_message(m.chat.id, "⚡ Initializing system...")
        time.sleep(0.5)
        bot.edit_message_text("🚀 Loading modules...", m.chat.id, msg.message_id)
        time.sleep(0.5)
        bot.edit_message_text("🧠 Connecting to admin core...", m.chat.id, msg.message_id)
        time.sleep(0.5)

        bot.edit_message_text(f"""
<b>╔═══〔 🚀 ULTRA SUPPORT CORE 🚀 〕═══╗</b>

👋 <b>Welcome, {m.from_user.first_name}</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ <b>{random.choice(taglines)}</b>

💬 📡 Direct Admin Connection  
🔒 🛡️ End-to-End Secure  
🚀 ⚡ Instant Delivery  

━━━━━━━━━━━━━━━━━━━━━━━━━━━

📢🔥 <b>🚀 SEND YOUR MESSAGE TO ADMIN 🚀</b> 🔥📢

━━━━━━━━━━━━━━━━━━━━━━━━━━━

💀 <b>ELITE MODE ACTIVATED</b> ⚡

<b>╚════════════════════════════╝</b>
""", m.chat.id, msg.message_id)

        if m.chat.id == ADMIN_ID:
            bot.send_message(ADMIN_ID, "⚙️ Admin Panel Ready", reply_markup=admin_keyboard())

    except:
        send_error(traceback.format_exc())

# ===== USER → ADMIN =====
@bot.message_handler(func=lambda m: m.chat.id != ADMIN_ID,
content_types=['text','photo','video','document','audio','voice','sticker'])
def forward(m):
    try:
        uid = m.from_user.id
        uname = m.from_user.username or "NoUsername"

        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("💬 REPLY", callback_data=f"reply_{uid}"))

        if m.content_type == "text":
            bot.send_message(ADMIN_ID, f"""
<b>╔═══〔 📡💬 LIVE MESSAGE STREAM 💬📡 〕═══╗</b>

👤 <b>Username:</b> @{uname}
🆔 <b>ID:</b> <code>{uid}</code>

💬 <code>{m.text}</code>

<b>╚════════════════════════════╝</b>
""", reply_markup=kb)
        else:
            bot.copy_message(ADMIN_ID, m.chat.id, m.message_id)

        # ===== CHANNEL LOG WITH USER INFO =====
        try:
            if m.content_type == "text":
                bot.send_message(CHANNEL_ID, f"""
💀📡 ╔═══〔 📡💬 CHANNEL LOG 💬📡 〕═══╗ 📡💀

👤🔥 Username: @{uname}
🆔💀 ID: <code>{uid}</code>

💬⚡ <code>{m.text}</code>

💀📡 ╚════════════════════════════╝ 📡💀
""")
            else:
                bot.copy_message(CHANNEL_ID, m.chat.id, m.message_id)
                bot.send_message(CHANNEL_ID, f"""
👤 Username: @{uname}
🆔 ID: <code>{uid}</code>
📎 Media received
""")
        except:
            pass

        # ===== ULTRA LOADING =====
        sent = bot.send_message(m.chat.id, "⚡ Initiating Secure Transmission...")

        steps = [
            "🧠 Connecting to Neural Core...",
            "📡 Establishing Quantum Link...",
            "🔐 Encrypting Data Stream...",
            "🚀 Boosting Signal Power...",
            "⚡ Injecting Speed Protocol...",
            "💀 Bypassing Firewalls...",
            "🔥 Ultra Mode Activated...",
            "📤 Transmitting Packet...",
            "⚡ Almost Delivered..."
        ]

        for step in steps:
            time.sleep(0.3)
            try:
                bot.edit_message_text(step, m.chat.id, sent.message_id)
            except:
                pass

        bot.edit_message_text("""
<b>╔═══〔 💀⚡ TRANSMISSION COMPLETE ⚡💀 〕═══╗</b>

📡 Delivered Successfully  
🚀 Ultra Speed  
🧠 System Active  

<b>╚════════════════════════════╝</b>
""", m.chat.id, sent.message_id)

    except:
        send_error(traceback.format_exc())

# ===== REPLY BUTTON =====
@bot.callback_query_handler(func=lambda c: c.data.startswith("reply_"))
def reply_btn(c):
    uid = int(c.data.split("_")[1])
    reply_mode[ADMIN_ID] = uid
    bot.send_message(ADMIN_ID, f"🎯 Reply to: {uid}", reply_markup=admin_keyboard())

# ===== ADMIN REPLY =====
@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and m.text not in ["📊 SPEED", "⛔ STOP"])
def admin_reply(m):
    try:
        if ADMIN_ID not in reply_mode:
            return

        uid = reply_mode[ADMIN_ID]
        bot.copy_message(uid, m.chat.id, m.message_id)

        try:
            bot.copy_message(CHANNEL_ID, m.chat.id, m.message_id)
        except:
            pass

        del reply_mode[ADMIN_ID]

    except:
        send_error(traceback.format_exc())

# ===== LIVE SYSTEM =====
def live_system(chat_id, msg_id):
    global live_monitor
    while live_monitor:
        try:
            start_time = time.time()

            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent

            ping = round((time.time() - start_time) * 1000, 2)

            bot.edit_message_text(f"""
💀 LIVE SYSTEM 💀

⚡ CPU: {cpu}%
🧠 RAM: {ram}%
🚀 SPEED: {ping} ms

🔥 Running...
""", chat_id, msg_id)

            time.sleep(2)
        except:
            break

# ===== SPEED BUTTON =====
@bot.message_handler(func=lambda m: m.text == "📊 SPEED" and m.chat.id == ADMIN_ID)
def start_live(m):
    global live_monitor
    live_monitor = True

    msg = bot.send_message(ADMIN_ID, "🚀 Starting Live Monitor...")
    threading.Thread(target=live_system, args=(ADMIN_ID, msg.message_id), daemon=True).start()

# ===== STOP BUTTON =====
@bot.message_handler(func=lambda m: m.text == "⛔ STOP" and m.chat.id == ADMIN_ID)
def stop_live(m):
    global live_monitor
    live_monitor = False
    bot.send_message(ADMIN_ID, "⛔ Monitoring Stopped")

print("💀🔥 ULTRA BOT RUNNING 🔥💀")
bot.infinity_polling(skip_pending=True)