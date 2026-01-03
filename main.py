from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from google.cloud import firestore
import pyotp
import time
import os

app = Flask(__name__)
# В облаке лучше использовать переменную окружения или сложную строку
app.secret_key = os.environ.get('SECRET_KEY', 'cloud_oc_super_secure_key_99')

# Инициализация клиента базы данных Google Firestore
db = firestore.Client()
USERS_COLLECTION = "users"


# --- ЛОГИКА РАБОТЫ С БАЗОЙ (FIRESTORE) ---

def get_user_data(login):
    """Получает данные пользователя из облака"""
    doc_ref = db.collection(USERS_COLLECTION).document(login)
    doc = doc_ref.get()
    return doc.to_dict() if doc.exists else None


def save_user_data(login, data):
    """Сохраняет данные пользователя в облако"""
    doc_ref = db.collection(USERS_COLLECTION).document(login)
    doc_ref.set(data)


# --- МАРШРУТЫ САЙТА ---

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/register', methods=['POST'])
def register():
    login = request.form.get('login')
    display_name = request.form.get('display_name')
    password = request.form.get('password')

    if get_user_data(login):
        return "Ошибка: Пользователь CloudOC с таким ID уже существует."

    # Секрет для генератора кодов (TOTP)
    totp_secret = pyotp.random_base32()

    user_data = {
        'login': login,
        'display_name': display_name,
        'password': password,
        'totp_secret': totp_secret,
        'created_at': firestore.SERVER_TIMESTAMP
    }

    save_user_data(login, user_data)
    session['user'] = login
    return redirect(url_for('dashboard'))


@app.route('/login', methods=['POST'])
def login():
    login = request.form.get('login')
    password = request.form.get('password')

    user = get_user_data(login)
    if user and user['password'] == password:
        session['user'] = login
        return redirect(url_for('dashboard'))

    return "Ошибка: Неверные данные для входа в CloudOC."


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('index'))

    user = get_user_data(session['user'])
    return render_template('dashboard.html', name=user['display_name'])


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))


# --- API ДЛЯ ЛАУНЧЕРА И JS ---

@app.route('/api/get_code')
def get_code():
    """Для отображения кода на сайте (JS)"""
    if 'user' not in session:
        return jsonify({'error': 'unauthorized'}), 401

    user = get_user_data(session['user'])
    totp = pyotp.TOTP(user['totp_secret'], interval=30)

    return jsonify({
        'code': totp.now(),
        'time_remaining': int(totp.interval - (time.time() % totp.interval))
    })


@app.route('/api/login_check', methods=['POST'])
def login_check():
    """Для проверки входа из Rust Лаунчера"""
    data = request.json
    login = data.get('login')
    password = data.get('password')
    code = data.get('code')

    user = get_user_data(login)

    if not user or user['password'] != password:
        return jsonify({"status": "error", "message": "Ошибка авторизации"})

    # Проверка 2FA кода
    totp = pyotp.TOTP(user['totp_secret'], interval=30)
    if totp.verify(code):
        return jsonify({
            "status": "ok",
            "user_name": user['display_name']
        })
    else:
        return jsonify({"status": "error", "message": "Неверный код безопасности"})


if __name__ == '__main__':
    # Для локальных тестов (в облаке запустится через gunicorn)
    app.run(debug=True, host='0.0.0.0', port=5000)