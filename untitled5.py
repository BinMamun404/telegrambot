import requests
import time

BOT_TOKEN = "7523737381:AAFSjk6NQoyhfKWTgptjJWxoTZl882p3Xw0"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
CHANNEL_USERNAME = "zetzero"
BOT_LINK = "https://t.me/zetzero_customsms_bot"

users = {}  # user_id: {coins, referred_by, action, target, refers, referrals, join_msg_id}

def send_message(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        data["reply_markup"] = reply_markup
    r = requests.post(f"{BASE_URL}/sendMessage", json=data).json()
    return r.get("result", {}).get("message_id")

def edit_message(chat_id, message_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        data["reply_markup"] = reply_markup
    requests.post(f"{BASE_URL}/editMessageText", json=data)

def delete_message(chat_id, message_id):
    requests.post(f"{BASE_URL}/deleteMessage", json={"chat_id": chat_id, "message_id": message_id})

# ✅ Channel join check
def is_user_joined(user_id):
    url = f"{BASE_URL}/getChatMember?chat_id=@{CHANNEL_USERNAME}&user_id={user_id}"
    resp = requests.get(url).json()
    status = resp.get("result", {}).get("status", "")
    return status in ["member", "administrator", "creator"]

# ✅ Reply Keyboard buttons
def main_buttons():
    return {
        "keyboard": [
            ["📨 Send Custom SMS", "🔄 Update"],
            ["👤 Account", "🙌 Invite"],
            ["↩️ Back"]
        ],
        "resize_keyboard": True
    }

def joined_button():
    return {
        "keyboard": [
            ["☑️ JOINED"]
        ],
        "resize_keyboard": True
    }

def invite_buttons():
    return {
        "keyboard": [
            ["👥 View Referrals"],
            ["↩️ Back"]
        ],
        "resize_keyboard": True
    }

def handle_update(update):
    if "message" in update:
        message = update["message"]
        chat_id = message["chat"]["id"]
        user_id = message["from"]["id"]
        username = message["from"].get("first_name", "User")
        text = message.get("text", "")

        if user_id not in users:
            users[user_id] = {"coins": 5, "referred_by": None, "action": None, "target": None, "refers": 0, "referrals": [], "join_msg_id": None}

        if text.startswith("/start"):
            msg_id = send_message(
                chat_id,
                "⛔ <b>প্রথমে অবশ্যই চ্যানেলে জয়েন করুন</b>\n\n"
                f"➡️ <b>@{CHANNEL_USERNAME}</b>\n\n"
                "📌 জয়েন করার পর নিচে <b>JOINED</b> বাটনে চাপুন ✅",
                reply_markup=joined_button()
            )
            users[user_id]["join_msg_id"] = msg_id

            # referral handle
            if len(text.split()) > 1:
                ref_id = text.split()[1].replace("Bot", "")
                if ref_id.isdigit():
                    ref_id = int(ref_id)
                    if ref_id != user_id and users[user_id]["referred_by"] is None:
                        users[user_id]["referred_by"] = ref_id
                        users[ref_id]["coins"] += 2
                        users[ref_id]["refers"] += 1
                        users[ref_id]["referrals"].append(username)
            return

        # ✅ handle reply keyboard presses
        if text == "☑️ JOINED":
            if is_user_joined(user_id):
                # পুরানো join message delete করবে
                join_msg_id = users[user_id].get("join_msg_id")
                if join_msg_id:
                    delete_message(chat_id, join_msg_id)
                    users[user_id]["join_msg_id"] = None
                send_message(chat_id, "✅ You have successfully joined!", reply_markup=main_buttons())
            else:
                send_message(chat_id, "❌ Please join the channel first!", reply_markup=joined_button())

        elif text == "📨 Send Custom SMS":
            send_message(chat_id, "❯ 𝙴𝚗𝚝𝚎𝚛 𝚃𝚊𝚛𝚐𝚎𝚝 𝙽𝚞𝚖𝚋𝚎𝚛", reply_markup={"keyboard": [["↩️ Back"]], "resize_keyboard": True})
            users[user_id]["action"] = "await_number"

        elif text == "🔄 Update":
            send_message(chat_id, "🔄 Bot is updated", reply_markup=main_buttons())

        elif text == "👤 Account":
            coins = users[user_id]["coins"]
            refers = users[user_id]["refers"]
            send_message(chat_id, f"👤 <b>{username}</b>\n\n💰 Coins: {coins}\n🙌 Total Invites: {refers}", reply_markup=main_buttons())

        elif text == "🙌 Invite":
            link = f"{BOT_LINK}?start=Bot{user_id}"
            msg = (
                f"🙌🏻 Total Referrals = {users[user_id]['refers']} User(s)\n\n"
                f"🙌🏻 Your Referral Link = {link}\n\n"
                "🪢 প্রতি রেফারে 2 Coins পাবেন"
            )
            send_message(chat_id, msg, reply_markup=invite_buttons())

        elif text == "👥 View Referrals":
            refs = users[user_id]["referrals"]
            if not refs:
                ref_text = "❌ No users referred yet."
            else:
                ref_text = "👥 Your Referrals:\n" + "\n".join([f"• {r}" for r in refs])
            send_message(chat_id, ref_text, reply_markup=invite_buttons())

        elif text == "↩️ Back":
            users[user_id]["action"] = None
            users[user_id]["target"] = None
            send_message(chat_id, "Select Option:", reply_markup=main_buttons())

        else:
            # Action handle
            action = users[user_id].get("action")
            if action == "await_number":
                users[user_id]["target"] = text
                users[user_id]["action"] = "await_message"
                send_message(chat_id, "❯ 𝙴𝚗𝚝𝚎𝚛 𝚈𝚘𝚞𝚛 𝙼𝚎𝚜𝚜𝚊𝚐𝚎", reply_markup={"keyboard": [["↩️ Back"]], "resize_keyboard": True})

            elif action == "await_message":
                if users[user_id]["coins"] < 2:
                    send_message(chat_id, "⛔ You don't have enough coins to send SMS.", reply_markup=main_buttons())
                    users[user_id]["action"] = None
                    return
                target = users[user_id]["target"]
                msg = text
                try:
                    requests.get(f"https://helobuy.shop/csms.php?key=bft&number={target}&message={msg}")
                    users[user_id]["coins"] -= 2
                    send_message(chat_id, "📨𝙲𝚄𝚂𝚃𝙾𝙼 𝚂𝙼𝚂 𝚂𝙴𝙽𝙳 𝚂𝚄𝙲𝙲𝙴𝚂𝙵𝚄𝙻𝙻𝚈", reply_markup=main_buttons())
                except:
                    send_message(chat_id, "⚠️ Failed to send SMS.", reply_markup=main_buttons())
                users[user_id]["action"] = None

def run_bot():
    offset = None
    while True:
        try:
            params = {"timeout": 100, "offset": offset}
            resp = requests.get(f"{BASE_URL}/getUpdates", params=params).json()
            for update in resp.get("result", []):
                offset = update["update_id"] + 1
                handle_update(update)
        except Exception as e:
            print("Error:", e)
        time.sleep(1)

if __name__ == "__main__":
    run_bot()