from flask import Flask, request
import requests, os, json, re
from datetime import datetime

app = Flask(__name__)
BOT_TOKEN = "9299183989:AAEamZClB7qwjicyjndGe_Gft8B5mBBgL0A"
BKASH_NUMBER = "01887339991"
USER_FILE = "users.json"
ORDER_FILE = "orders.json"
ADMIN_FILE = "admin_id.txt"

def load_json(f):
    try: return json.load(open(f)) if os.path.exists(f) else {}
    except: return {}
def save_json(f,d): json.dump(d, open(f,'w'), ensure_ascii=False, indent=2)

def send_msg(chat_id, text, kb=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if kb: data["reply_markup"] = kb
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json=data, timeout=20)

def main_menu():
    return {"keyboard": [["📄 V1 - 12৳"], ["🏛️ V3 - 30৳", "📄 V3 - 27৳"], ["🏛️ V4 - 40৳", "📄 V4 - 31৳"], ["📄 NID PDF - 350৳", "✍️ Sign Copy - 400৳"], ["💰 Balance", "⚡ Auto Recharge"], ["👤 Profile"]], "resize_keyboard": True}

def copy_menu():
    return {"inline_keyboard": [
        [{"text": "📄 V1 (12৳)", "callback_data": "V1_12"}],
        [{"text": "🏛️ V3 Official (30৳)", "callback_data": "V3O_30"}, {"text": "📄 V3 Unofficial (27৳)", "callback_data": "V3U_27"}],
        [{"text": "🏛️ V4 Official (40৳)", "callback_data": "V4O_40"}, {"text": "📄 V4 Unofficial (31৳)", "callback_data": "V4U_31"}],
        [{"text": "📄 NID PDF (350৳)", "callback_data": "PDF_350"}, {"text": "✍️ Sign Copy (400৳)", "callback_data": "SIGN_400"}]
    ]}

def admin_order_kb(cid):
    return {"inline_keyboard": [[{"text": "✅ Delivery Done", "callback_data": f"done_{cid}"}], [{"text": "🚫 তথ্য পাওয়া যায়নি", "callback_data": f"notfound_{cid}"}, {"text": "❌ Cancel", "callback_data": f"cancel_{cid}"}], [{"text": "⏳ Server Pending", "callback_data": f"pending_{cid}"}]]}

def admin_recharge_kb(cid, amount, trx):
    return {"inline_keyboard": [[{"text": f"✅ {amount}৳ Approve", "callback_data": f"approve_{cid}_{amount}_{trx}"}], [{"text": "❌ Reject", "callback_data": f"reject_{cid}_{trx}"}]]}

PRICE = {"V1_12":12, "V3O_30":30, "V3U_27":27, "V4O_40":40, "V4U_31":31, "PDF_350":350, "SIGN_400":400}
NAME = {"V1_12":"V1 Unofficial", "V3O_30":"V3 Official", "V3U_27":"V3 Unofficial", "V4O_40":"V4 Official", "V4U_31":"V4 Unofficial", "PDF_350":"NID PDF", "SIGN_400":"Sign Copy"}

@app.route('/pay')
def pay():
    amount = request.args.get('amount','120')
    return f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1">
    <style>body{{font-family:sans-serif;background:#0f172a;color:#fff;display:flex;justify-content:center;align-items:center;min-height:100vh}}.card{{background:#1e293b;padding:25px;border-radius:20px;text-align:center;max-width:350px}}.amt{{font-size:40px;color:#22c55e;font-weight:bold}}.btn{{display:block;background:#e2136e;color:#fff;padding:15px;border-radius:12px;text-decoration:none;margin:10px 0}}</style></head>
    <body><div class="card"><h3>⚡ Auto Recharge {amount}৳</h3><div class="amt">{amount}৳</div><p>Number: {BKASH_NUMBER}</p><a class="btn" href="https://bKash.app">💳 bKash App এ {amount}৳ Send Money করুন</a><p style="font-size:12px;color:#94a3b8">Send করার পর Bot এ TrxID পাঠান, যেমন: 9AB3CD12EF</p></div></body></html>
    """

@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data: return "ok"

    if "callback_query" in data:
        cq = data["callback_query"]
        chat_id = str(cq["message"]["chat"]["id"])
        cdata = cq["data"]
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery", json={"callback_query_id": cq["id"]})
        users = load_json(USER_FILE); orders = load_json(ORDER_FILE)
        admin_id = open(ADMIN_FILE).read().strip() if os.path.exists(ADMIN_FILE) else None

        if cdata.startswith("approve_"):
            _, cid, amount, trx = cdata.split("_",3)
            amount=int(amount)
            if cid not in users: users[cid]={"balance":0}
            users[cid]["balance"]+=amount
            save_json(USER_FILE, users)
            send_msg(chat_id, f"✅ Approved {amount}৳ to {cid}")
            send_msg(cid, f"✅ {amount}৳ Balance Add হয়েছে!\nTrxID: {trx}\nNew Bal: {users[cid]['balance']}৳")
            return "ok"
        if cdata.startswith("reject_"):
            _, cid, trx = cdata.split("_",2)
            send_msg(chat_id, f"❌ Rejected {trx}")
            send_msg(cid, f"❌ Recharge Reject: {trx}")
            return "ok"
        if admin_id and chat_id==admin_id:
            cid=None; action=None
            if cdata.startswith("done_"): action="done"; cid=cdata.replace("done_","")
            if cdata.startswith("cancel_"): action="cancel"; cid=cdata.replace("cancel_","")
            if cdata.startswith("notfound_"): action="notfound"; cid=cdata.replace("notfound_","")
            if cdata.startswith("pending_"): action="pending"; cid=cdata.replace("pending_","")
            if cid and cid in orders:
                o=orders[cid]; price=o["price"]
                if action=="cancel": send_msg(cid, f"❌ Cancelled NID: {o['nid']}"); o["status"]="cancelled"
                elif action=="notfound": send_msg(cid, f"🚫 তথ্য পাওয়া যায়নি NID: {o['nid']}"); o["status"]="not_found"
                elif action=="pending": send_msg(cid, f"⏳ Server Pending NID: {o['nid']}"); o["status"]="server_pending"
                elif action=="done": 
                    if cid in users: users[cid]["balance"]-=price
                    send_msg(cid, f"✅ {o['vname']} Ready! {price}৳ কাটা হয়েছে")
                    o["status"]="done"
                save_json(ORDER_FILE, orders); save_json(USER_FILE, users)
                return "ok"

        if cdata.startswith("RECHARGE_"):
            amount=cdata.split("_")[1]
            link=f"https://sr-bot-zowq.onrender.com/pay?amount={amount}&uid={chat_id}"
            send_msg(chat_id, f"⚡ {amount}৳ Recharge\nNumber: {BKASH_NUMBER}\n\nনিচে ক্লিক করে Send Money করুন, তারপর TrxID পাঠান", {"inline_keyboard": [[{"text": f"💳 {amount}৳ Pay", "url": link}]]})
            return "ok"
        if cdata in PRICE:
            if chat_id not in users: users[chat_id]={"balance":0}
            price=PRICE[cdata]
            if users[chat_id].get("balance",0) < price:
                send_msg(chat_id, f"❌ ব্যালেন্স নেই! Bal: {users[chat_id]['balance']}৳ Need: {price}৳\n\nNID PDF / Sign Copy এর জন্য 350৳+ লাগবে", {"inline_keyboard": [[{"text": "⚡ 120৳ Recharge", "callback_data": "RECHARGE_120"}]]})
                return "ok"
            nid=users[chat_id].get("nid","-"); dob=users[chat_id].get("dob","-")
            orders[chat_id]={"nid":nid, "dob":dob, "version":cdata, "vname":NAME[cdata], "price":price, "status":"pending", "time":str(datetime.now())}
            save_json(ORDER_FILE, orders)
            if admin_id: send_msg(admin_id, f"🔥 নতুন অর্ডার!\nID: {chat_id}\n👤 {users[chat_id].get('name','-')}\n🆔 NID: <code>{nid}</code>\n🎂 DOB: {dob}\n📄 {NAME[cdata]} - {price}৳\n💰 Bal: {users[chat_id]['balance']}৳", admin_order_kb(chat_id))
            send_msg(chat_id, f"✅ অর্ডার নেওয়া হয়েছে\n{NAME[cdata]} - {price}৳\n⏳ 2-5 মিনিট")
            return "ok"

    if "message" not in data: return "ok"
    msg=data["message"]; chat_id=str(msg["chat"]["id"]); text=msg.get("text","").strip()
    users=load_json(USER_FILE)
    if chat_id not in users: users[chat_id]={"balance":0, "nid":None, "dob":None, "name": msg["from"].get("first_name","User")}
    admin_id = open(ADMIN_FILE).read().strip() if os.path.exists(ADMIN_FILE) else None

    if "reply_to_message" in msg and admin_id and chat_id==admin_id:
        m=re.search(r"ID:\s*(\d+)", msg["reply_to_message"].get("text",""))
        if m:
            cid=m.group(1)
            orders=load_json(ORDER_FILE)
            if cid in orders and orders[cid]["status"]=="pending":
                price=orders[cid]["price"]
                if cid in users: users[cid]["balance"]-=price
                if "document" in msg:
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument", json={"chat_id": cid, "document": msg["document"]["file_id"], "caption": f"✅ {orders[cid]['vname']} Ready!"}, timeout=20)
                save_json(USER_FILE, users); orders[cid]["status"]="done"; save_json(ORDER_FILE, orders)
                send_msg(admin_id, f"✅ Delivered to {cid} + {price}৳ কাটা")
            return "ok"

    if text.startswith("/start"):
        open(ADMIN_FILE,'w').write(chat_id)
        send_msg(chat_id, f"🇧🇩 SR Team 07 - FINAL\n\n💰 Bal: {users[chat_id]['balance']}৳\nService: V1 12৳, V3 30/27৳, V4 40/31৳\nNID PDF 350৳, Sign 400৳\n\n⚠️ Server Copy এর জন্য NID + DOB বাধ্যতামূলক\nযেমন: 4635346762 01/06/1995", main_menu())
        save_json(USER_FILE, users); return "ok"

    if "Balance" in text or "Profile" in text:
        send_msg(chat_id, f"👤 ID: {chat_id}\n💰 Bal: {users[chat_id]['balance']}৳\nNID: {users[chat_id].get('nid','-')}\nDOB: {users[chat_id].get('dob','-')}")
    elif "Recharge" in text:
        send_msg(chat_id, f"⚡ Auto Recharge\nNumber: {BKASH_NUMBER}\nMin 120৳", {"inline_keyboard": [[{"text": "💰 120৳", "callback_data": "RECHARGE_120"}, {"text": "💰 200৳", "callback_data": "RECHARGE_200"}], [{"text": "💰 350৳ (PDF)", "callback_data": "RECHARGE_350"}, {"text": "💰 400৳ (Sign)", "callback_data": "RECHARGE_400"}]]})
    else:
        m=re.search(r"(\d{10,17})\s+(\d{2}[/-]\d{2}[/-]\d{4})", text)
        if m:
            nid=m.group(1); dob=m.group(2)
            users[chat_id]["nid"]=nid; users[chat_id]["dob"]=dob; save_json(USER_FILE, users)
            bal=users[chat_id]['balance']
            if bal<12: send_msg(chat_id, f"✅ NID: {nid} Save হয়েছে\nBal: {bal}৳ - Recharge করুন", {"inline_keyboard": [[{"text": "⚡ 120৳ Recharge", "callback_data": "RECHARGE_120"}]]})
            else: send_msg(chat_id, f"✅ NID: {nid}\nBal: {bal}৳\nService সিলেক্ট করুন:", copy_menu())
        else:
            if re.search(r"^[A-Z0-9]{8,12}$", text.upper()):
                if admin_id: send_msg(admin_id, f"💰 Recharge Request!\nID: {chat_id}\nTrxID: {text}\nBal: {users[chat_id]['balance']}৳", admin_recharge_kb(chat_id, "120", text))
                send_msg(chat_id, "✅ TrxID পেয়েছি, Admin Approve করলে Balance Add হবে")
            elif re.search(r"^\d{10,17}$", text):
                send_msg(chat_id, "❌ শুধু NID দিলে হবে না ভাই!\nServer Copy এর জন্য অবশ্যই NID + DOB লাগবে\n\nযেমন: 4635346762 01/06/1995")

    save_json(USER_FILE, users); return "ok"

@app.route('/')
def home(): return "FINAL Running"
@app.route('/set-webhook')
def set_wh():
    r=requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url=https://sr-bot-zowq.onrender.com/webhook/{BOT_TOKEN}")
    return r.text
if __name__=='__main__': app.run(host='0.0.0.0', port=10000)
