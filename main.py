from flask import Flask, request, jsonify
import pyotp
import json
import os

app = Flask(__name__)

# Путь к файлу базы данных (просто json для начала)
DB_FILE = 'users.json'

def load_users():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_users(users):
    with open(DB_FILE, 'w') as f:
        json.dump(users, f, indent=4)

@app.route('/')
def index():
    return "CloudOC Server is Live! Use your Rust Launcher to connect."

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    
    users = load_users()
    if username in users:
        return jsonify({"status": "error", "message": "User already exists"}), 400
    
    # Генерируем секрет для 2FA (Google Authenticator)
    secret = pyotp.random_base32()
    users[username] = {"secret": secret}
    save_users(users)
    
    # Ссылка, которую можно превратить в QR код (или просто ввести секрет в приложение)
    provisioning_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=username, 
        issuer_name="CloudOC"
    )
    
    return jsonify({
        "status": "success", 
        "secret": secret, 
        "qr_link": provisioning_uri
    })

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    otp_code = data.get('code') # 6 цифр из приложения
    
    users = load_users()
    if username not in users:
        return jsonify({"status": "error", "message": "User not found"}), 404
    
    # Проверка кода
    secret = users[username]['secret']
    totp = pyotp.TOTP(secret)
    
    if totp.verify(otp_code):
        return jsonify({"status": "success", "message": "Logged in!"})
    else:
        return jsonify({"status": "error", "message": "Invalid 2FA code"}), 401

if __name__ == "__main__":
    # Настройка порта для Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
