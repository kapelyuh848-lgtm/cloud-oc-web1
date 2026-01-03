# Измени название этого метода, чтобы сайт его видел
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Если данные пришли из формы на сайте
        username = request.form.get('username')
        users = load_users()
        
        if username in users:
            return "User already exists!"
            
        secret = pyotp.random_base32()
        users[username] = {"secret": secret}
        save_users(users)
        
        # Показываем секретный код прямо на странице
        return f"<h1>Success!</h1><p>Your 2FA Secret: {secret}</p><a href='/'>Back to Login</a>"
    
    # Если просто зашли на страницу регистрации
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    # Метод для входа через сайт
    username = request.form.get('username')
    code = request.form.get('code')
    
    users = load_users()
    if username in users:
        totp = pyotp.TOTP(users[username]['secret'])
        if totp.verify(code):
            return "<h1>Welcome, CloudOC User!</h1>"
            
    return "<h1>Error: Invalid Code or User</h1><a href='/'>Try Again</a>"

