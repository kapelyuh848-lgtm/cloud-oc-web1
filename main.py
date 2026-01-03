from flask import Flask, request, jsonify, render_template, redirect, url_for
import pyotp
import json
import os

app = Flask(__name__)

# Database file logic
DB_FILE = 'users.json'

def load_users():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, 'r') as f:
        try:
            return json.load(f)
        except:
            return {}

def save_users(users):
    with open(DB_FILE, 'w') as f:
        json.dump(users, f, indent=4)

# --- ROUTES ---

@app.route('/')
def index():
    # Главная страница с твоим дизайном входа
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Поддержка и JSON (лаунчер) и Form (сайт)
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        
        if not username:
            return "Username is required", 400
            
        users = load_users()
        if username in users:
            return "User already exists", 400
        
        # Генерируем секрет для Google Authenticator
        secret = pyotp.random_base32()
        users[username] = {"secret": secret}
        save_users(users)
        
        # Если это лаунчер - шлем JSON, если сайт - показываем текст
        if request.is_json:
            return jsonify({"status": "success", "secret": secret})
        
        return f"<h1>Success!</h1><p>Your 2FA Secret: <b>{secret}</b></p><p>Add this to your Authenticator app.</p><a href='/'>Go to Login</a>"

    # Если просто открыли страницу регистрации
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    # Поддержка и JSON (лаунчер) и Form (сайт)
    data = request.get_json() if request.is_json else request.form
    username = data.get('username')
    code = data.get('code')
    
    users = load_users()
    if username not in users:
        return "User not found", 404
        
    # Проверка 6-значного кода
    secret = users[username]['secret']
    totp = pyotp.TOTP(secret)
    
    if totp.verify(code):
        if request.is_json:
            return jsonify({"status": "success", "message": "Logged in"})
        return "<h1>Welcome to CloudOC! Access Granted.</h1>"
    else:
        if request.is_json:
            return jsonify({"status": "error", "message": "Invalid code"}), 401
        return "<h1>Invalid Code! Try again.</h1><a href='/'>Back</a>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
