from flask import Flask, request, jsonify, render_template
import pyotp
import json
import os

app = Flask(__name__)

# Файл базы данных
DB_FILE = 'users.json'

# --- Вспомогательные функции ---
def load_users():
    # Если файла нет, возвращаем пустой словарь (как будто там {})
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, 'r') as f:
            content = f.read().strip()
            # Если файл пустой, возвращаем {}
            if not content: 
                return {}
            return json.loads(content)
    except Exception as e:
        print(f"Error loading DB: {e}")
        return {}

def save_users(users):
    with open(DB_FILE, 'w') as f:
        json.dump(users, f, indent=4)

# --- Страницы сайта (HTML) ---
@app.route('/')
def index():
    # Главная страница
    return render_template('index.html')

@app.route('/register')
def register_page():
    # Страница регистрации
    return render_template('register.html')

# --- API (Логика сервера) ---
@app.route('/api/register', methods=['POST'])
def api_register():
    # САМОЕ ВАЖНОЕ: Читаем данные отовсюду (и JSON, и Форма)
    data = request.get_json(silent=True) or request.form
    
    # Ищем имя пользователя
    username = data.get('username')
    
    # Если имени нет — ругаемся в логах и возвращаем ошибку
    if not username:
        print(f"DEBUG: Data received but no username found. Data: {data}")
        return jsonify({"status": "error", "message": "Username required"}), 400
    
    users = load_users()
    
    if username in users:
        return jsonify({"status": "error", "message": "User already exists"}), 400
    
    # Генерируем секрет
    secret = pyotp.random_base32()
    users[username] = {"secret": secret}
    save_users(users)
    
    # Возвращаем секрет (чтобы юзер мог сохранить его)
    return jsonify({
        "status": "success", 
        "message": "User created", 
        "secret": secret
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

