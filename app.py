from flask import Flask, request
import requests, sqlite3, os, datetime

app = Flask(__name__)

TOKEN = os.environ.get("TG_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
WA_TOKEN = os.environ.get("WA_TOKEN", "YOUR_WHATSAPP_TOKEN")
PHONE_ID = os.environ.get("PHONE_ID", "YOUR_PHONE_ID")
VERIFY = "sr_team_07"
MY_ID = "8931533687"
NUM = "01887339991"

db = sqlite3.connect("sr.db", check_same_thread=False)
db.execute("CREATE TABLE IF NOT EXISTS users (wa TEXT PRIMARY KEY, name TEXT, bal INTEGER DEFAULT 0, joined TEXT)")
db.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, wa TEXT, item TEXT, price INTEGER, date TEXT)")
db.commit()

def get_user(wa):
    r = db.execute("SELECT * FROM users WHERE wa=?", (wa,)).fetchone()
    if not r:
        db.execute("INSERT INTO users(wa,name,bal,joined)VALUES(?,?,?,?)", (wa, wa, 0, datetime.date.today().isoformat()))
        db.commit()
        r = db.execute("SELECT * FROM users WHERE wa=?", (wa,)).fetchone()
    return r

def wa_send(to, txt):
    try:
        requests.post(
            f"https://graph.facebook.com/v20.0/{PHONE_ID}/messages",
            headers={"Authorization": f"Bearer {WA_TOKEN}"},
            json={
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": txt}
            }
        )
    except:
        pass

@app.route('/profile/<wa>')
@app.route('/pay/<wa>')
def profile(wa):
    user = get_user(wa)
    name, bal = user[1], user[2]
    orders = db.execute("SELECT * FROM orders WHERE wa=? ORDER BY id DESC LIMIT 20", (wa,)).fetchall()
    hist = "".join([f"<div style='padding:10px;border-bottom:1px solid #eee'>{o[2]} - {o[3]}৳ - {o[4]}</div>" for o in orders]) or "কোনো অর্ডার নেই"
    return f"<html><head><meta name='viewport' content='width=device-width,initial-scale=1'><style>body{{font-family:sans-serif;background:#f2f3f5;margin:0}}.top{{background:#111;color:#fff;padding:25px;text-align:center;border-radius:0 0 25px 25px}}.card{{background:#fff;margin:-20px 15px;padding:20px;border-radius:15px}}.btn{{width:92%;padding:14px;margin:6px;border-radius:10px;border:none}}</style></head><body><div class='top'><h2>{name}</h2><small>{wa}</small><h1>{bal}</h1><small>বর্তমান ব্যালেন্স</small></div><div class='card'><h3>রিচার্জ করুন</h3><p>Bkash/Nagad: {NUM}</p><button class='btn' onclick='s(120)'>120৳</button><button class='btn' onclick='s(200)'>200৳</button><button class='btn' onclick='s(300)'>300৳</button><button class='btn' onclick='s(500)'>500৳</button><div id='s2' style='display:none'><h3 id='ah'></h3><input id='tx' placeholder='TrxID দিন' style='width:85%;padding:12px'><br><br><button class='btn' style='background:#2d3436;color:#fff' onclick='sub()'>Submit</button><p id='msg'></p></div><hr><h3>অর্ডার হিস্টোরি</h3><div>{hist}</div></div><script>let A=0;function s(a){{A=a;document.getElementById('s2').style.display='block';document.getElementById('ah').innerText=a+' ৳ রিচার্জ';}}function sub(){{let t=document.getElementById('tx').value;if(!t)return alert('TrxID দিন');fetch('/api/pay',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{wa:'{wa}',amt:A,trx:t}})}}).then(r=>{{document.getElementById('msg').innerText='পাঠানো হয়েছে';}});}}</script></body></html>"

@app.route('/api/pay', methods=['POST'])
def api_pay():
    data = request.get_json()
    wa_send(MY_ID, f"New Pay: {data['wa']} - {data['amt']} - {data['trx']}")
    return "ok"

@app.route('/webhook', methods=['GET','POST'])
def webhook():
    if request.method == 'GET':
        if request.args.get('hub.verify_token') == VERIFY:
            return request.args.get('hub.challenge')
        return "verify failed"
    return "ok"

@app.route('/')
def home():
    return "Bot is Live"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
