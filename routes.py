from flask import Flask, render_template, request, redirect, url_for, session
from models import User

app = Flask(__name__)
app.secret_key = 'supersecretkey'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.find_by_username(username)
        if user and User.validate_password(user[2], password):
            session['username'] = username
            return redirect(url_for('chat'))
        return "Invalid credentials"
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password == confirm_password:
            User.create_user(username, password)
            session['username'] = username
            return redirect(url_for('chat'))
        return "Passwords do not match"
    return render_template('register.html')

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html', username=session['username'])

