import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, UserProfilePhotos
import os
import random
import time
import psutil
import threading
import traceback
import requests
from datetime import datetime
from collections import deque
import queue

# ========== CONFIG ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ========== GLOBAL VARIABLES ==========
reply_mode = {}
live_monitor = False
message_queue = queue.Queue()
queue_thread_running = True
seen_users = set()  # Track users who already started

# ========== QUEUE PROCESSOR (HAR MESSAGE KO DELAY KE SAATH BHEJEGA) ==========
def process_queue():
    """Background thread jo queue se message nikalta hai aur bhejta hai"""
    while queue_thread_running:
        try:
            task = message_queue.get(timeout=1)
            if task is None:
                break
            
            msg_type = task['type']
            
            if msg_type == 'forward_to_admin':
                if task['content_type'] == 'text':
                    bot.send_message(
                        ADMIN_ID, 
                        task['text'], 
                        reply_markup=task.get('reply_markup'),
                        parse_mode='HTML'
                    )
                else:
                    bot.copy_message(ADMIN_ID, task['chat_id'], task['message_id'])
                    if task.get('caption'):
                        bot.send_message(ADMIN_ID, task['caption'], reply_markup=task.get('reply_markup'))
            
            elif msg_type == 'log_to_channel':
                if task['content_type'] == 'text':
                    bot.send_message(CHANNEL_ID, task['text'], parse_mode='HTML')
                else:
                    bot.copy_message(CHANNEL_ID, task['chat_id'], task['message_id'])
                    if task.get('caption'):
                        bot.send_message(CHANNEL_ID, task['caption'])
            
            elif msg_type == 'ack_to_user':
                try:
                    bot.edit_message_text(
                        task['text'], 
                        task['chat_id'], 
                        task['message_id'],
                        parse_mode='HTML'
                    )
                except:
                    pass
            
            elif msg_type == 'admin_reply':
                bot.send_message(task['user_id'], task['text'], parse_mode='HTML')
                if task.get('channel_log'):
                    bot.send_message(CHANNEL_ID, task['channel_log'], parse_mode='HTML')
            
            elif msg_type == 'confirm_to_admin':
                bot.send_message(ADMIN_ID, task['text'], parse_mode='HTML')
            
            elif msg_type == 'new_user_alert':
                # Send photo if available
                if task.get('photo'):
                    try:
                        bot.send_photo(
                            ADMIN_ID, 
                            task['photo'], 
                            caption=task['text'],
                            parse_mode='HTML'
                        )
                    except:
                        bot.send_message(ADMIN_ID, task['text'], parse_mode='HTML')
                else:
                    bot.send_message(ADMIN_ID, task['text'], parse_mode='HTML')
                
                # Also log to channel
                if task.get('channel_log'):
                    if task.get('photo'):
                        try:
                            bot.send_photo(
                                CHANNEL_ID,
                                task['photo'],
                                caption=task['channel_log'],
                                parse_mode='HTML'
                            )
                        except:
                            bot.send_message(CHANNEL_ID, task['channel_log'], parse_mode='HTML')
                    else:
                        bot.send_message(CHANNEL_ID, task['channel_log'], parse_mode='HTML')
            
            time.sleep(0.3)
            
        except queue.Empty:
            continue
        except Exception as e:
            send_error(f"Queue Error: {traceback.format_exc()}")

# Start queue processor thread
threading.Thread(target=process_queue, daemon=True).start()

# ========== ERROR HANDLER ==========
def send_error(e):
    try:
        bot.send_message(ADMIN_ID, f"⚠️ ERROR:\n<code>{str(e)[:500]}</code>")
    except:
        pass

# ========== AUTO ALERT SYSTEM ==========
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

# ========== GET USER PROFILE PHOTO ==========
def get_user_profile_photo(user_id):
    """Get user's profile photo file_id"""
    try:
        photos = bot.get_user_profile_photos(user_id, limit=1)
        if photos.total_count > 0:
            return photos.photos[0][-1].file_id
        return None
    except:
        return None

# ========== GET USER DETAILS ==========
def get_user_full_details(user):
    """Get complete user details"""
    details = {
        'first_name': user.first_name or "N/A",
        'last_name': user.last_name or "N/A",
        'username': f"@{user.username}" if user.username else "No username",
        'user_id': user.id,
        'language': user.language_code or "N/A",
        'is_premium': getattr(user, 'is_premium', False),
        'is_bot': user.is_bot if hasattr(user, 'is_bot') else False
    }
    return details

# ========== HELPERS ==========
def get_user_info(user_id):
    try:
        chat = bot.get_chat(user_id)
        return {
            "username": chat.username or "NoUsername",
            "first_name": chat.first_name or "User"
        }
    except:
        return {"username": "Unknown", "first_name": "User"}

def admin_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📊 SPEED"), KeyboardButton("⛔ STOP"))
    kb.add(KeyboardButton("📊 STATS"))
    return kb

# ========== START COMMAND (WITH NEW USER DETECTION) ==========
@bot.message_handler(commands=['start'])
def start(m):
    try:
        user = m.from_user
        user_id = user.id
        
        # Check if new user
        is_new_user = user_id not in seen_users
        
        # Loading animation
        msg = bot.send_message(m.chat.id, "⚡ Initializing system...")
        time.sleep(0.5)
        bot.edit_message_text("🚀 Loading modules...", m.chat.id, msg.message_id)
        time.sleep(0.5)
        bot.edit_message_text("🧠 Connecting to admin core...", m.chat.id, msg.message_id)
        time.sleep(0.5)
        
        taglines = [
            "⚡ Lightning Fast Support",
            "🚀 Powered by Intelligence",
            "💀 Elite Response System",
            "🔥 Premium Support Activated",
            "🧠 Smart AI Routing Enabled"
        ]
        
        # Welcome message for user
        bot.edit_message_text(f"""
<b>╔═══〔 🚀 ULTRA SUPPORT CORE 🚀 〕═══╗</b>

👋 <b>Welcome, {user.first_name}</b>

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
        
        # ===== NEW USER ALERT TO ADMIN (WITH DP) =====
        if is_new_user:
            seen_users.add(user_id)
            
            # Get user details
            details = get_user_full_details(user)
            profile_photo = get_user_profile_photo(user_id)
            
            # Premium badge
            premium_badge = "✅ Yes" if details['is_premium'] else "❌ No"
            
            # User link
            user_link = f"tg://user?id={user_id}"
            
            # Format date (account creation approx)
            current_year = datetime.now().year
            
            # Admin alert message
            admin_alert = f"""
╔═══〔 🆕 NEW USER DETECTED 🆕 〕═══╗

━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 <b>USER DETAILS</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 <b>First Name:</b> {details['first_name']}
📛 <b>Last Name:</b> {details['last_name']}
🔖 <b>Username:</b> {details['username']}
🆔 <b>User ID:</b> <code>{details['user_id']}</code>
🌐 <b>Language:</b> {details['language']}
⭐ <b>Telegram Premium:</b> {premium_badge}
🤖 <b>Is Bot:</b> {details['is_bot']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔗 <b>User Link:</b> <a href='{user_link}'>Click to message</a>
⏰ <b>First Seen:</b> Just now

━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 <b>Total Users:</b> {len(seen_users)}
╚════════════════════════════╝
"""
            
            # Channel log
            channel_log = f"""
💀📡 ╔═══〔 🆕 NEW USER JOINED 🆕 〕═══╗ 📡💀

👤 <b>Name:</b> {details['first_name']} {details['last_name']}
🔖 <b>Username:</b> {details['username']}
🆔 <b>ID:</b> <code>{details['user_id']}</code>
🌐 <b>Language:</b> {details['language']}
⭐ <b>Premium:</b> {premium_badge}

⏰ <b>Joined:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📊 <b>Total Users:</b> {len(seen_users)}

💀📡 ╚════════════════════════════╝ 📡💀
"""
            
            # Queue new user alert with photo
            message_queue.put({
                'type': 'new_user_alert',
                'photo': profile_photo,
                'text': admin_alert,
                'channel_log': channel_log
            })
        
        # Admin panel if admin
        if m.chat.id == ADMIN_ID:
            bot.send_message(ADMIN_ID, "⚙️ Admin Panel Ready", reply_markup=admin_keyboard())
            
    except Exception as e:
        send_error(traceback.format_exc())

# ========== STATS COMMAND ==========
@bot.message_handler(func=lambda m: m.text == "📊 STATS" and m.chat.id == ADMIN_ID)
def show_stats(m):
    try:
        stats_msg = f"""
╔═══〔 📊 BOT STATISTICS 📊 〕═══╗

👥 <b>Total Users:</b> {len(seen_users)}
📦 <b>Queue Size:</b> {message_queue.qsize()}
⚡ <b>Status:</b> 🟢 Active

━━━━━━━━━━━━━━━━━━━━━━━━━━━
💀 <b>ULTRA ACK BOT</b> 🔥
╚════════════════════════════╝
"""
        bot.send_message(ADMIN_ID, stats_msg, parse_mode="HTML")
    except:
        send_error(traceback.format_exc())

# ========== USER MESSAGE HANDLER (FAST FORWARD - NO LIMIT) ==========
@bot.message_handler(func=lambda m: m.chat.id != ADMIN_ID,
content_types=['text','photo','video','document','audio','voice','sticker'])
def forward(m):
    try:
        uid = m.from_user.id
        uname = m.from_user.username or "NoUsername"
        
        # Add to seen users if not already
        if uid not in seen_users:
            seen_users.add(uid)
        
        # Reply button for admin
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("💬 REPLY", callback_data=f"reply_{uid}"))
        
        # Format user info
        user_info = f"👤 Username: @{uname}\n🆔 ID: <code>{uid}</code>"
        
        # ===== QUEUE: FORWARD TO ADMIN =====
        if m.content_type == "text":
            admin_text = f"""
<b>╔═══〔 📡💬 LIVE MESSAGE STREAM 💬📡 〕═══╗</b>

{user_info}

💬 <code>{m.text}</code>

<b>╚════════════════════════════╝</b>
"""
            message_queue.put({
                'type': 'forward_to_admin',
                'content_type': 'text',
                'text': admin_text,
                'reply_markup': kb,
                'chat_id': m.chat.id,
                'message_id': m.message_id
            })
        else:
            message_queue.put({
                'type': 'forward_to_admin',
                'content_type': 'media',
                'chat_id': m.chat.id,
                'message_id': m.message_id,
                'caption': user_info,
                'reply_markup': kb
            })
        
        # ===== QUEUE: LOG TO CHANNEL =====
        if m.content_type == "text":
            channel_text = f"""
💀📡 ╔═══〔 📡💬 CHANNEL LOG 💬📡 〕═══╗ 📡💀

👤🔥 Username: @{uname}
🆔💀 ID: <code>{uid}</code>

💬⚡ <code>{m.text}</code>

💀📡 ╚════════════════════════════╝ 📡💀
"""
            message_queue.put({
                'type': 'log_to_channel',
                'content_type': 'text',
                'text': channel_text
            })
        else:
            message_queue.put({
                'type': 'log_to_channel',
                'content_type': 'media',
                'chat_id': m.chat.id,
                'message_id': m.message_id,
                'caption': f"👤 @{uname}\n🆔 {uid}\n📎 Media received"
            })
        
        # ===== QUEUE: ACKNOWLEDGEMENT TO USER (LOADING ANIMATION) =====
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
            time.sleep(0.25)
            try:
                bot.edit_message_text(step, m.chat.id, sent.message_id)
            except:
                pass
        
        # Final acknowledgement
        final_msg = """
<b>╔═══〔 💀⚡ TRANSMISSION COMPLETE ⚡💀 〕═══╗</b>

📡 Delivered Successfully  
🚀 Ultra Speed  
🧠 System Active  

<b>╚════════════════════════════╝</b>
"""
        message_queue.put({
            'type': 'ack_to_user',
            'text': final_msg,
            'chat_id': m.chat.id,
            'message_id': sent.message_id
        })
        
    except Exception as e:
        send_error(traceback.format_exc())

# ========== REPLY BUTTON HANDLER ==========
@bot.callback_query_handler(func=lambda c: c.data.startswith("reply_"))
def reply_btn(c):
    uid = int(c.data.split("_")[1])
    user_info = get_user_info(uid)
    
    reply_mode[ADMIN_ID] = {
        "target_id": uid,
        "target_username": user_info["username"],
        "locked": True
    }
    
    bot.send_message(ADMIN_ID, f"""
╔═══〔 🔒 REPLY LOCK ACTIVATED 🔒 〕═══╗

👤 <b>Target User:</b> @{user_info['username']}
🆔 <b>Target ID:</b> <code>{uid}</code>

━━━━━━━━━━━━━━━━━━━━━━━━━━━
✏️ <b>Ab apna message likhein:</b>

💡 Jo likhoge wahi user tak jayega
🔒 Lock active: Sirf is user ko reply hoga

━━━━━━━━━━━━━━━━━━━━━━━━━━━
⛔ Cancel: <code>/cancel</code>
╚════════════════════════════╝
""", parse_mode="HTML")

# ========== ADMIN REPLY HANDLER ==========
@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and m.text not in ["📊 SPEED", "⛔ STOP", "/cancel", "📊 STATS"])
def admin_reply(m):
    try:
        if ADMIN_ID not in reply_mode:
            bot.send_message(ADMIN_ID, "❌ Pehle '💬 REPLY' button dabayein!")
            return
        
        if not reply_mode[ADMIN_ID]["locked"]:
            bot.send_message(ADMIN_ID, "❌ Lock expired, please click REPLY again")
            return
        
        uid = reply_mode[ADMIN_ID]["target_id"]
        uname = reply_mode[ADMIN_ID]["target_username"]
        
        # Show processing
        processing = bot.send_message(ADMIN_ID, "⚡ Processing your reply...\n🔄 Encrypting...")
        time.sleep(0.5)
        bot.edit_message_text("📡 Sending to user...", ADMIN_ID, processing.message_id)
        time.sleep(0.5)
        
        # Message to user
        user_msg = f"""
╔═══〔 📩 SUPPORT TEAM REPLY 📩 〕═══╗

{m.text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
💬 Aap is message ke neeche reply bhej sakte ho
⚡ Support active hai

╚════════════════════════════╝
"""
        
        # Channel log
        channel_log = f"""
💀📡 ╔═══〔 📡💬 ADMIN REPLY LOG 💬📡 〕═══╗ 📡💀

👑 <b>Admin → 👤 User:</b> @{uname} (<code>{uid}</code>)

📤 <b>Reply Message:</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━
"{m.text}"
━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏱️ <b>Sent at:</b> Just now
✅ <b>Status:</b> Delivered

💀📡 ╚════════════════════════════╝ 📡💀
"""
        
        # Queue admin reply
        message_queue.put({
            'type': 'admin_reply',
            'user_id': uid,
            'text': user_msg,
            'channel_log': channel_log
        })
        
        # Queue confirmation to admin
        confirmation = f"""
╔═══〔 ✅ MESSAGE SENT SUCCESSFULLY ✅ 〕═══╗

📤 <b>Your message:</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━
"{m.text}"
━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 <b>Delivered to:</b> @{uname} (<code>{uid}</code>)
⏱️ <b>Time:</b> Just now

🔓 <b>Reply lock removed</b>
💡 New reply ke liye fir se button dabayein

╚════════════════════════════╝
"""
        message_queue.put({
            'type': 'confirm_to_admin',
            'text': confirmation
        })
        
        # Remove lock
        del reply_mode[ADMIN_ID]
        
        # Update processing message
        bot.edit_message_text("✅ Message queued successfully!", ADMIN_ID, processing.message_id)
        
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Failed: {str(e)}")
        send_error(traceback.format_exc())

# ========== CANCEL COMMAND ==========
@bot.message_handler(func=lambda m: m.text == "/cancel" and m.chat.id == ADMIN_ID)
def cancel_reply(m):
    if ADMIN_ID in reply_mode:
        del reply_mode[ADMIN_ID]
        bot.send_message(ADMIN_ID, "🔓 Reply lock cancelled. Button dabake naya reply kar sakte ho.")
    else:
        bot.send_message(ADMIN_ID, "❌ Koi active reply lock nahi hai.")

# ========== LIVE MONITOR SYSTEM ==========
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
📊 Queue size: {message_queue.qsize()}
👥 Total Users: {len(seen_users)}

🔥 Running...
""", chat_id, msg_id)
            time.sleep(2)
        except:
            break

@bot.message_handler(func=lambda m: m.text == "📊 SPEED" and m.chat.id == ADMIN_ID)
def start_live(m):
    global live_monitor
    live_monitor = True
    msg = bot.send_message(ADMIN_ID, "🚀 Starting Live Monitor...")
    threading.Thread(target=live_system, args=(ADMIN_ID, msg.message_id), daemon=True).start()

@bot.message_handler(func=lambda m: m.text == "⛔ STOP" and m.chat.id == ADMIN_ID)
def stop_live(m):
    global live_monitor
    live_monitor = False
    bot.send_message(ADMIN_ID, "⛔ Monitoring Stopped")

# ========== MAIN ==========
print("💀🔥 ULTRA ACK BOT WITH QUEUE + NEW USER DETECTION RUNNING 🔥💀")
print(f"📊 Queue processor active - No message limit!")
print(f"👥 Tracking users...")
bot.infinity_polling(skip_pending=True)
