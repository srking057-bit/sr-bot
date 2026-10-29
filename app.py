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
    r=db.execute("SELECT * FROM users WHERE wa=?",(wa,)).fetchone()
    if not r:
        db.execute("INSERT INTO users(wa,name,bal,joined)VALUES(?,?,0,?)",(wa, wa, datetime.date.today().isoformat())); db.commit()
        r=db.execute("SELECT * FROM users WHERE wa=?",(wa,)).fetchone()
    return r

def get_bal(wa): return get_user(wa)[2]
def add_bal(wa,a): get_user(wa); db.execute("UPDATE users SET bal=bal+? WHERE wa=?",(a,wa)); db.commit()
def add_order(wa,item,price): db.execute("INSERT INTO orders(wa,item,price,date)VALUES(?,?,?,?)",(wa,item,price,datetime.datetime.now().strftime("%d-%m %I:%M %p"))); db.commit()

def wa_send(to, txt):
    try: requests.post(f"https://graph.facebook.com/v20.0/{PHONE_ID}/messages", headers={"Authorization": f"Bearer {WA_TOKEN}"}, json={"messaging_product":"whatsapp","to":to,"type":"text","text":{"body":txt}}})
    except: pass

# === নিজস্ব প্রোফাইল পেজ ===
@app.route('/profile/<wa>')
@app.route('/pay/<wa>')
def profile(wa):
    user = get_user(wa)
    name, bal = user[1], user[2]
    orders = db.execute("SELECT * FROM orders WHERE wa=? ORDER BY id DESC LIMIT 20",(wa,)).fetchall()
    hist_html = "".join([f"<div style='display:flex;justify-content:space-between;padding:10px;border-bottom:1px solid #eee'><span>{o[2]}</span><span>-{o[3]}৳</span><small>{o[4]}</small></div>" for o in orders]) or "<p>কোনো অর্ডার নেই</p>"
    
    return f"""
    <html><head><meta name='viewport' content='width=device-width,initial-scale=1'>
    <style>body{{font-family:sans-serif;background:#f2f3f5;margin:0}} .top{{background:#111;color:#fff;padding:25px;border-radius:0 0 25px 25px;text-align:center}} .card{{background:#fff;margin:-30px 15px 15px 15px;padding:20px;border-radius:15px;box-shadow:0 5px 15px #ddd}} .btn{{width:92%;padding:14px;margin:6px;border-radius:10px;border:none;font-size:16px}} .amt{{border:2px solid #e84393;background:#fff}} .bk{{background:#e2136e;color:#fff}}</style></head>
    <body>
    <div class='top'><h2 style='margin:0'>{name}</h2><small>ID: {wa}</small><h1 style='margin:10px 0'>৳ {bal}</h1><small>বর্তমান ব্যালেন্স</small></div>
    <div class='card'>
        <h3>💳 রিচার্জ করুন</h3>
        <p>Bkash/Nagad: <b>{NUM}</b></p>
        <div id='s1'><button class='btn amt' onclick='s(120)'>120৳</button><button class='btn amt' onclick='s(200)'>200৳</button><button class='btn amt' onclick='s(300)'>300৳</button><button class='btn amt' onclick='s(500)'>500৳</button></div>
        <div id='s2' style='display:none'><h3 id='ah'></h3><input id='tx' placeholder='TrxID দিন' style='padding:12px;width:85%;border-radius:8px;border:1px solid #ccc'><br><br><button class='btn bk' onclick='sub()'>Submit ✅</button><p id='msg'></p></div>
        <hr style='margin:20px 0'>
        <h3>📜 অর্ডার হিস্ট্রি</h3>
        <div>{hist_html}</div>
    </div>
    <script>let A=0;function s(a){{A=a;document.getElementById('s1').style.display='none';document.getElementById('s2').style.display='block';document.getElementById('ah').innerText=a+'৳ সিলেক্ট'}};function sub(){{let t=document.getElementById('tx').value;if(!t)return alert('TrxID দিন');fetch('/api/pay',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{wa:'{wa}',amt:A,trx:t}})}}).then(()=>{{document.getElementById('msg').innerText='✅ পাঠানো হয়েছে, Approve হলে ব্যালেন্স যোগ হবে।'}})}}</script>
    </body></html>
    """

@app.route('/api/pay', methods=['POST'])
def api_pay():
    d=request.json; wa=d['wa']; amt=d['amt']; trx=d['trx']
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={{"chat_id":MY_ID,"text":f"🔝 NEW RECHARGE\nProfile: {request.host_url}profile/{wa}\nWA: {wa}\nAmt: {amt}৳\nTrxID: {trx}","reply_markup":{{"inline_keyboard":[[{{"text":f"✅ Approve {amt}৳","callback_data":f"ap_{wa}_{amt}"}}]]}}}})
    return {{"ok":True}}

@app.route('/webhook', methods=['GET','POST'])
def wh():
    if request.method=='GET':
        if request.args.get('hub.verify_token')==VERIFY: return request.args.get('hub.challenge')
        return "no"
    try:
        val=request.json['entry'][0]['changes'][0]['value']
        msg=val['messages'][0]; wa=msg['from']; txt=msg.get('text',{{}}).get('body','')
        # WhatsApp নামটা অটো সেভ
        wa_name = val.get('contacts',[{{}}])[0].get('profile',{{}}).get('name', wa)
        get_user(wa); db.execute("UPDATE users SET name=? WHERE wa=?",(wa_name,wa)); db.commit()

        if 'recharge' in txt.lower() or 'profile' in txt.lower() or 'balance' in txt.lower():
            wa_send(wa, f"👤 {wa_name} আপনার প্রোফাইল:\n\n🆔 ID: {wa}\n💰 Balance: {get_bal(wa)}৳\n\n🔗 লিংক: {request.host_url}profile/{wa}\n\nএই লিংকে গেলে ব্যালেন্স, অর্ডার হিস্ট্রি সব দেখতে পারবেন।")
            return "ok"
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={{"chat_id":MY_ID,"text":f"💬 {wa_name} ({wa})\nBal: {get_bal(wa)}৳\nMsg: {txt}\nProfile: {request.host_url}profile/{wa}"}})
    except: pass
    return "ok"

@app.route(f'/{TOKEN}', methods=['POST'])
def tg():
    d=request.json
    if "callback_query" in d:
        q=d["callback_query"]; data=q["data"]
        if data.startswith("ap_"):
            _,wa,amt=data.split("_"); add_bal(wa,int(amt)); wa_send(wa,f"✅ {amt}৳ Added! Profile: {request.host_url}profile/{wa}")
            requests.post(f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery", json={{"callback_query_id":q["id"],"text":"Approved"}})
    return "ok"

@app.route('/')
def home(): return "SR Team Profile System Running"
if __name__=='__main__': app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
