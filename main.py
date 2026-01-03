from flask import Flask, request, jsonify, render_template, redirect
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Берем данные напрямую из формы (для сайта) или из JSON (для лаунчера)
        username = request.form.get('username') or (request.json.get('username') if request.is_json else None)
        
        if not username:
            return "<h1>Error: Username is required!</h1><a href='/register'>Try again</a>", 400
            
        users = load_users()
        if username in users:
            return "<h1>Error: User already exists!</h1><a href='/register'>Try again</a>", 400
        
        secret = pyotp.random_base32()
        users[username] = {"secret": secret}
        save_users(users)
        
        if request.is_json:
            return jsonify({"status": "success", "secret": secret})
        
        return f"<h1>Success!</h1><p>Your Secret: <b>{secret}</b></p><a href='/'>Login now</a>"

    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    # Проверяем оба варианта получения данных
    username = request.form.get('username') or (request.json.get('username') if request.is_json else None)
    code = request.form.get('code') or (request.json.get('code') if request.is_json else None)
    
    if not username or not code:
        return "<h1>Missing username or code!</h1>", 400

    users = load_users()
    if username not in users:
        return f"<h1>User {username} not found!</h1><a href='/'>Back</a>", 404
        
    secret = users[username]['secret']
    totp = pyotp.TOTP(secret)
    
    if totp.verify(code):
        return "<h1>Welcome to CloudOC! Login Successful.</h1>"
    
    return "<h1>Invalid Code!</h1><a href='/'>Try again</a>", 401

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
