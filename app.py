from flask import Flask, request
import requests, os, json, re
from datetime import datetime

app = Flask(__name__)
BOT_TOKEN = "9299183989:AAEamZClB7qwjicyjndGe_Gft8B5mBBgL0A"
USER_FILE = "users.json"
ORDER_FILE = "orders.json"
ADMIN_FILE = "admin_id.txt"

def get_admin(): return open(ADMIN_FILE).read().strip() if os.path.exists(ADMIN_FILE) else None
def load_json(f):
    if os.path.exists(f):
        try: return json.load(open(f))
        except: return {}
    return {}
def save_json(f,d): json.dump(d, open(f,'w'), ensure_ascii=False, indent=2)

def send_msg(chat_id, text, keyboard=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if keyboard: data["reply_markup"] = keyboard
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json=data, timeout=15)

def main_menu():
    return {"keyboard": [["📄 V1 (Unofficial) - 12৳"], ["🏛️ V3 Official - 30৳", "📄 V3 Unofficial - 27৳"], ["🏛️ V4 Official - 40৳", "📄 V4 Unofficial - 31৳"], ["💰 Balance", "⚡ অটো রিচার্জ (bKash)"], ["📋 Services", "💵 Price"], ["👤 Profile", "📜 History"], ["❓ Help"]], "resize_keyboard": True}

def copy_menu():
    return {"inline_keyboard": [[{"text": "📄 V1 Unofficial (12৳)", "callback_data": "V1_12"}], [{"text": "🏛️ V3 Official (30৳)", "callback_data": "V3O_30"}, {"text": "📄 V3 Unofficial (27৳)", "callback_data": "V3U_27"}], [{"text": "🏛️ V4 Official (40৳)", "callback_data": "V4O_40"}, {"text": "📄 V4 Unofficial (31৳)", "callback_data": "V4U_31"}]]}

PRICE = {"V1_12":12, "V3O_30":30, "V3U_27":27, "V4O_40":40, "V4U_31":31}
NAME = {"V1_12":"V1 Unofficial", "V3O_30":"V3 Official", "V3U_27":"V3 Unofficial", "V4O_40":"V4 Official", "V4U_31":"V4 Unofficial"}

@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data: return "ok"

    # ===== Admin থেকে File/Reply আসলে Customer কে Forward =====
    if "message" in data:
        msg = data["message"]
        chat_id = str(msg["chat"]["id"])
        admin_id = get_admin()

        # যদি Admin কোনো Document/Photo Reply করে পাঠায়
        if admin_id and chat_id == str(admin_id) and "reply_to_message" in msg:
            reply_text = msg["reply_to_message"].get("text","") + msg["reply_to_message"].get("caption","")
            # reply_text এর ভিতরে Customer ID আছে কিনা খুঁজবো: ID: 12345
            m = re.search(r"ID:\s*(\d+)", reply_text)
            if m:
                customer_id = m.group(1)
                # Admin যা পাঠিয়েছে (ফাইল/ছবি/লেখা) Customer কে পাঠাও
                if "document" in msg:
                    file_id = msg["document"]["file_id"]
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument", json={"chat_id": customer_id, "document": file_id, "caption": f"✅ আপনার {NAME.get('','')} ফাইল রেডি!\n\n🇧🇩 SR Team 07"}, timeout=15)
                    send_msg(admin_id, f"✅ Delivered to {customer_id}")
                elif "photo" in msg:
                    file_id = msg["photo"][-1]["file_id"]
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto", json={"chat_id": customer_id, "photo": file_id, "caption": msg.get("caption","✅ ফাইল রেডি")}, timeout=15)
                    send_msg(admin_id, f"✅ Photo Delivered to {customer_id}")
                else:
                    send_msg(customer_id, msg.get("text","✅ আপনার ফাইল রেডি"))
                    send_msg(admin_id, f"✅ Text Delivered to {customer_id}")

                # Order Complete
                orders = load_json(ORDER_FILE)
                if customer_id in orders:
                    orders[customer_id]["status"] = "done"
                    save_json(ORDER_FILE, orders)
                return "ok"

    # ===== Customer Button Click =====
    if "callback_query" in data:
        cq = data["callback_query"]
        chat_id = str(cq["message"]["chat"]["id"])
        cdata = cq["data"]
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery", json={"callback_query_id": cq["id"], "text": "অর্ডার নেওয়া হচ্ছে..."})

        users = load_json(USER_FILE)
        orders = load_json(ORDER_FILE)
        if chat_id not in users: users[chat_id] = {"balance":84}

        price = PRICE.get(cdata, 12)
        bal = users[chat_id].get("balance",0)
        if bal < price:
            send_msg(chat_id, f"❌ ব্যালেন্স কম! প্রয়োজন {price}৳, আছে {bal}৳\n⚡ অটো রিচার্জ করুন")
            return "ok"

        # Balance কাটা
        users[chat_id]["balance"] = bal - price
        save_json(USER_FILE, users)

        nid = users[chat_id].get("nid","N/A")
        dob = users[chat_id].get("dob","N/A")

        # Customer কে Loading দেখাও - এইটাই তুমি চেয়েছিলে
        send_msg(chat_id, f"✅ <b>তথ্য সংরক্ষিত হচ্ছে...</b>\n\n🆔 NID: {nid}\n🎂 DOB: {dob}\n📄 কপি: {NAME[cdata]} ({price}৳)\n\n⏳ <b>২-৫ মিনিট সময় লাগবে</b>\nঅনুগ্রহ করে অপেক্ষা করুন, Admin আপনার ফাইল প্রস্তুত করছে...")

        # Admin কে অর্ডার পাঠাও
        admin_id = get_admin()
        if admin_id:
            order_text = f"🔥 <b>নতুন অর্ডার!</b>\n\n👤 Customer ID: <code>{chat_id}</code>\nID: {chat_id}\n🆔 NID: <code>{nid}</code>\n🎂 DOB: {dob}\n📄 Version: {NAME[cdata]} - {price}৳\n💰 Balance: {users[chat_id]['balance']}৳\n\n👇 <b>এই মেসেজে Reply দিয়ে ফাইল/ছবি পাঠান, Customer পেয়ে যাবে</b>"
            send_msg(admin_id, order_text)

        # Save Order
        orders[chat_id] = {"nid":nid, "dob":dob, "version":NAME[cdata], "price":price, "status":"pending", "time": str(datetime.now())}
        save_json(ORDER_FILE, orders)
        return "ok"

    # ===== NID + DOB Text =====
    if "message" not in data: return "ok"
    msg = data["message"]
    chat_id = str(msg["chat"]["id"])
    text = msg.get("text","").strip()
    users = load_json(USER_FILE)
    if chat_id not in users:
        users[chat_id] = {"balance":84, "nid":None, "name": msg["from"].get("first_name","User")}

    if text.startswith("/start"):
        open(ADMIN_FILE,'w').write(chat_id)  # Admin Save
        send_msg(chat_id, "🇧🇩 <b>SR Team 07 Bot Active!</b>\n\nNID + জন্ম তারিখ পাঠান\nযেমন: <code>4635346762 01/06/1995</code>", main_menu())
        save_json(USER_FILE, users)
        return "ok"

    if text == "/pending":
        admin_id = get_admin()
        if str(admin_id) == chat_id:
            orders = load_json(ORDER_FILE)
            pending = [f"ID: {k} - {v['nid']} - {v['version']} - {v['status']}" for k,v in orders.items() if v['status']=='pending']
            if not pending: send_msg(chat_id, "কোন Pending অর্ডার নেই")
            else: send_msg(chat_id, "📋 Pending:\n" + "\n".join(pending))
        return "ok"

    m = re.search(r"(\d{10,17})\s+(\d{2}[/-]\d{2}[/-]\d{4})", text)
    if m:
        nid = m.group(1)
        dob_raw = m.group(2)
        try:
            dob_fmt = datetime.strptime(dob_raw.replace("-","/"), "%d/%m/%Y").strftime("%Y-%m-%d")
        except: dob_fmt = dob_raw
        users[chat_id]["nid"] = nid
        users[chat_id]["dob"] = dob_fmt
        save_json(USER_FILE, users)
        txt = f"✅ <b>NID সংরক্ষিত!</b>\n➖➖➖➖➖➖➖➖➖➖\n🆔 NID: {nid}\n🎂 জন্ম তারিখ: {dob_fmt}\n💰 ব্যালেন্স: {users[chat_id]['balance']}৳\n➖➖➖➖➖➖➖➖➖➖\n\n📄 <b>কোন কপি নিতে চান?</b>\n🏛️ Official = BEC ডিজাইন\n📄 Unofficial = NIDW ডিজাইন"
        send_msg(chat_id, txt, copy_menu())
        return "ok"

    if "Balance" in text:
        send_msg(chat_id, f"💰 ব্যালেন্স: {users[chat_id]['balance']}৳")
    else:
        send_msg(chat_id, "👇 NID + জন্ম তারিখ পাঠান\nযেমন: 4635346762 01/06/1995", main_menu())
    save_json(USER_FILE, users)
    return "ok"

@app.route('/set-webhook')
def set_wh():
    r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url=https://sr-bot-zowq.onrender.com/webhook/{BOT_TOKEN}")
    return r.text
@app.route('/')
def home(): return "Manual Delivery Bot Running"
if __name__ == '__main__': app.run(host='0.0.0.0', port=10000)
