from flask import Flask, request, jsonify, render_template
import pyotp
import json
import os

app = Flask(__name__)

DB_FILE = 'users.json'

def load_users():
    if not os.path.exists(DB_FILE): return {}
    with open(DB_FILE, 'r') as f:
        try: return json.load(f)
        except: return {}

def save_users(users):
    with open(DB_FILE, 'w') as f:
        json.dump(users, f, indent=4)

# --- WEB ROUTES (Для отображения дизайна в браузере) ---

@app.route('/')
def index():
    # Это откроет файл templates/index.html (твой дизайн)
    return render_template('index.html')

@app.route('/gui-register')
def gui_register():
    # Это откроет файл templates/register.html
    return render_template('register.html')

# --- API ROUTES (Для работы твоего Rust лаунчера) ---

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    username = data.get('username')
    users = load_users()
    if username in users:
        return jsonify({"status": "error", "message": "Exists"}), 400
    
    secret = pyotp.random_base32()
    users[username] = {"secret": secret}
    save_users(users)
    return jsonify({"status": "success", "secret": secret})

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username, code = data.get('username'), data.get('code')
    users = load_users()
    if username not in users: return jsonify({"status": "error"}), 404
    
    totp = pyotp.TOTP(users[username]['secret'])
    if totp.verify(code):
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 401

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
