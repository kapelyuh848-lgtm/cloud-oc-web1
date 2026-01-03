import os
import json
import pyotp
from flask import Flask, render_template, request, jsonify

# Указываем Flask, где искать шаблоны, даже если пути кривые
template_dir = os.path.abspath('templates')
app = Flask(__name__, template_folder=template_dir)

DB_FILE = 'users.json'

# --- ФУНКЦИИ БАЗЫ ДАННЫХ (С ЗАЩИТОЙ ОТ ОШИБОК) ---

def init_db():
    """Создает файл базы, если его нет"""
    if not os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'w') as f:
                json.dump({}, f)
        except Exception as e:
            print(f"CRITICAL ERROR: Could not create DB file. {e}")

def load_users():
    init_db() # Сначала проверяем, есть ли файл
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading DB: {e}")
        return {}

def save_users(users):
    try:
        with open(DB_FILE, 'w') as f:
            json.dump(users, f, indent=4)
    except Exception as e:
        print(f"Error saving DB: {e}")

# --- МАРШРУТЫ ---

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        # Если шаблона нет, покажем ошибку прямо на экране, а не 500
        return f"<h1>Error: Template 'index.html' not found!</h1><p>Details: {e}</p><p>Current folder: {os.getcwd()}</p><p>Templates folder: {template_dir}</p>"

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Универсальное получение данных (и от сайта, и от лаунчера)
        username = request.form.get('username')
        
        # Если пусто, пробуем JSON (для лаунчера)
        if not username and request.is_json:
            username = request.json.get('username')

        if not username:
            return "Username required", 400

        users = load_users()
        if username in users:
            return "User already exists", 400

        # Генерация секрета
        secret = pyotp.random_base32()
        users[username] = {"secret": secret}
        save_users(users)

        # Ответ
        if request.is_json:
            return jsonify({"status": "success", "secret": secret})
        else:
            return f"<h1>Success!</h1><p>Secret: {secret}</p><a href='/'>Login</a>"

    # GET запрос - показываем форму
    try:
        return render_template('register.html')
    except Exception as e:
        return f"<h1>Error: Template 'register.html' not found!</h1><p>{e}</p>"

@app.route('/login', methods=['POST'])
def login():
    # Данные из формы ИЛИ из JSON
    username = request.form.get('username')
    code = request.form.get('code')

    if not username and request.is_json:
        data = request.json
        username = data.get('username')
        code = data.get('code')

    users = load_users()
    if username not in users:
        return "User not found", 404

    secret = users[username]['secret']
    totp = pyotp.TOTP(secret)

    if totp.verify(code):
        if request.is_json:
            return jsonify({"status": "success"})
        return "<h1>Login Successful!</h1>"
    else:
        return "Invalid Code", 401

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
