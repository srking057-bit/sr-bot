from flask import Flask, request, render_template_string
import requests
import os

app = Flask(__name__)

# --- CONFIG ---
BOT_TOKEN = "9299183989:AAEamZClB7qwjicyjndGe_Gft8B5mBBgL0A"
BOT_USERNAME = "Sr_Team_07Bot"
ADMIN_FILE = "admin_id.txt" # তোমার টেলিগ্রাম আইডি এখানে সেভ হবে

WHATSAPP_NUMBER = "8801887339991"
WHATSAPP_LINK = f"https://wa.me/{WHATSAPP_NUMBER}?text=Hi%20SR%20Team%2C%20I%20need%20help"

def get_admin_id():
    if os.path.exists(ADMIN_FILE):
        with open(ADMIN_FILE, 'r') as f:
            return f.read().strip()
    return None

def save_admin_id(chat_id):
    with open(ADMIN_FILE, 'w') as f:
        f.write(str(chat_id))

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=data, timeout=10)
    except:
        pass

# --- HTML PAGE ---
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SR Team - WhatsApp Support</title>
<style>
body{font-family:system-ui;text-align:center;padding:40px;background:#f0f2f5}
.card{background:white;padding:30px;border-radius:20px;max-width:400px;margin:auto;box-shadow:0 10px 30px rgba(0,0,0,0.1)}
.btn{display:block;background:#25D366;color:white;padding:16px;border-radius:12px;text-decoration:none;font-weight:bold;font-size:18px;margin-top:20px}
.btn-tg{background:#0088cc;margin-top:12px}
small{color:#888}
</style>
</head>
<body>
<div class="card">
<h2>📞 SR Team Support</h2>
<p>WhatsApp এ মেসেজ দিন, সাথে সাথে Telegram এ নোটিফিকেশন যাবে</p>
<a class="btn" onclick="notify()" href="__WALINK__">💬 WhatsApp এ মেসেজ করুন<br><small>01887339991</small></a>
<a class="btn btn-tg" href="https://t.me/__BOTUSER__">🤖 Telegram Bot খুলুন</a>
<p id="status"></p>
</div>
<script>
function notify(){
  fetch('/wa-click', {method:'POST'});
  document.getElementById('status').innerText = 'Connecting to WhatsApp...';
}
</script>
</body>
</html>
""".replace("__WALINK__", WHATSAPP_LINK).replace("__BOTUSER__", BOT_USERNAME)

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/wa-click', methods=['POST'])
def wa_click():
    admin_id = get_admin_id()
    if admin_id:
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        send_telegram_message(admin_id, f"🔥 <b>নতুন কাস্টমার!</b>\n\nকেউ তোমার WhatsApp বাটনে ক্লিক করেছে!\nIP: {ip}\n\nএখনই WhatsApp চেক করো: 01887339991\nLink: {WHATSAPP_LINK}")
    return "ok"

# --- TELEGRAM WEBHOOK ---
@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data or 'message' not in data:
        return "ok"
    
    chat_id = data['message']['chat']['id']
    text = data['message'].get('text', '')
    
    # প্রথমবার /start দিলে তোমাকে Admin বানাবে
    if text == '/start':
        save_admin_id(chat_id)
        send_telegram_message(chat_id, f"✅ ভাই সেটআপ Done!\n\nতোমার ID {chat_id} Admin হিসেবে Save হলো।\n\nএখন থেকে কেউ {WHATSAPP_LINK} ওয়েবসাইটের বাটনে ক্লিক করলেই তোমাকে এখানে নোটিফিকেশন দিবো।\n\nতোমার সাইট: https://sr-bot-zowq.onrender.com\nWhatsApp: 01887339991")
    else:
        # তুমি এখানে যা লিখবে সেটা কাস্টমারকে পাঠানোর সিস্টেম পরে বানাবো
        send_telegram_message(chat_id, f"মেসেজ পেয়েছি: {text}\n\nAdmin ID: {chat_id}")

    return "ok"

@app.route('/set-webhook')
def set_webhook():
    # এই লিংকে একবার ঢুকলেই Webhook সেট হবে
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url=https://sr-bot-zowq.onrender.com/webhook/{BOT_TOKEN}"
    r = requests.get(url)
    return r.text

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
