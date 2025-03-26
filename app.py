import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DATABASE = 'database.db'

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS idea (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                username TEXT NOT NULL UNIQUE,
                followed BOOLEAN NOT NULL
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS admin (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        ''')
        # Check if admin user exists
        admin = db.execute('SELECT * FROM admin WHERE username = ?', ('admin',)).fetchone()
        if not admin:
            db.execute('INSERT INTO admin (username, password) VALUES (?, ?)', 
                     ('admin', 'admin123')) 
        db.commit()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/lottery')
def lottery():
    return render_template('lottery.html')

@app.route('/submit_idea', methods=['POST'])
def submit_idea():
    username = request.form.get('username')
    followed = request.form.get('followed') == 'on'
    
    # Validate username starts with @
    if not username.startswith('@'):
        return redirect(url_for('lottery'))
    
    db = get_db()
    try:
        db.execute('INSERT INTO idea (content, username, followed) VALUES (?, ?, ?)',
                  (username, username, followed))
        db.commit()
        return redirect(url_for('lottery', success='true'))
    except sqlite3.IntegrityError:
        # Username already exists
        return redirect(url_for('lottery'))
    finally:
        db.close()

@app.route('/check_username', methods=['POST'])
def check_username():
    username = request.form.get('username')
    db = get_db()
    existing_entry = db.execute('SELECT 1 FROM idea WHERE username = ?', (username,)).fetchone()
    db.close()
    return jsonify({'exists': existing_entry is not None})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        db = get_db()
        admin = db.execute('SELECT * FROM admin WHERE username = ? AND password = ?', 
                          (username, password)).fetchone()
        db.close()
        if admin:
            session['admin'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Lohs esi? Kur parole?')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'admin' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    ideas = db.execute('SELECT * FROM idea').fetchall()
    db.close()
    return render_template('dashboard.html', ideas=ideas)

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
     app.run(debug=False, host='0.0.0.1', port=5000)
