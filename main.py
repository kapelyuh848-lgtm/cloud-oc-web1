from flask import Flask, request, jsonify, render_template
import pyotp
import json
import os

app = Flask(__name__)

# Файл базы данных
DB_FILE = 'users.json'

# --- Вспомогательные функции (Работа с БД) ---
def load_users():
    """Загружает пользователей из файла. Если файла нет — возвращает пустой словарь."""
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, 'r') as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except Exception as e:
        print(f"Error loading DB: {e}")
        return {}

def save_users(users):
    """Сохраняет пользователей в файл."""
    with open(DB_FILE, 'w') as f:
        json.dump(users, f, indent=4)

# --- Страницы сайта (HTML) ---

@app.route('/')
def index():
    """Главная страница (Форма входа)"""
    return render_template('index.html')

@app.route('/register')
def register_page():
    """Страница регистрации"""
    return render_template('register.html')

# --- API (Логика сервера) ---

@app.route('/api/register', methods=['POST'])
def api_register():
    """Регистрация нового пользователя"""
    # Берем данные либо из JSON (лаунчер), либо из формы (сайт)
    data = request.get_json(silent=True) or request.form
    username = data.get('username')
    
    if not username:
        return jsonify({"status": "error", "message": "Username required"}), 400
    
    users = load_users()
    
    if username in users:
        return jsonify({"status": "error", "message": "User already exists"}), 400
    
    # Генерация секретного ключа для 2FA
    secret = pyotp.random_base32()
    users[username] = {"secret": secret}
    save_users(users)
    
    return jsonify({
        "status": "success", 
        "message": "User created", 
        "secret": secret
    })

@app.route('/api/login', methods=['POST'])
def api_login():
    """Вход пользователя с проверкой 2FA"""
    data = request.get_json(silent=True) or request.form
    
    username = data.get('username')
    code = data.get('code') # Код из Google Authenticator

    if not username or not code:
        return jsonify({"status": "error", "message": "Missing username or code"}), 400

    users = load_users()
    user = users.get(username)

    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    # Проверка кода TOTP
    totp = pyotp.TOTP(user['secret'])
    if totp.verify(code):
        return jsonify({"status": "success", "message": "Logged in successfully!"})
    else:
        return jsonify({"status": "error", "message": "Invalid 2FA code"}), 401

if __name__ == "__main__":
    # Запуск сервера на порту из переменной окружения (нужно для Render)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
